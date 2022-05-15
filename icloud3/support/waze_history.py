from ..global_variables import GlobalVariables as Gb
from ..const            import (DATETIME_ZERO, HIGH_INTEGER, EVLOG_ALERT, EVLOG_NOTICE,
                                CRLF_DOT, RARROW, RARROW2, CHECK_MARK, HDOT, HDOT2, CRLF_CHK,
                                LATITUDE, LONGITUDE, FRIENDLY_NAME,
                                WAZE_LOCATION_HISTORY_DATABASE, )
from ..helpers.base     import (broadcast_info_msg, post_event, post_internal_error, post_monitor_msg, log_info_msg,
                                log_error_msg, log_exception, _trace, _traceha, )
from ..helpers.time     import (datetime_now, secs_to_time_str, mins_to_time_str, )
from ..helpers.format   import (format_dist, )
from ..helpers.entity_io import (set_state_attributes, set_state_attributes, )
from ..helpers.distance import (mi_to_km, )
from ..support.waze_route_calc_ic3 import WRCError
import homeassistant.util.dt as dt_util

import traceback
import time
import sqlite3
from sqlite3 import Error


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
# Create the zones table
CREATE_ZONES_TABLE = '''
    CREATE TABLE IF NOT EXISTS zones (
        zone_id         integer PRIMARY KEY,
        zone            text NOT NULL,
        latitude        real,
        longitude       real
    );'''
ZON_ID   = 0
ZON_ZONE = 1
ZON_LAT  = 2
ZON_LONG = 3

# Add zone record - [zone, latitude, longitude]
ADD_ZONE_RECORD = '''
    INSERT INTO zones(
        zone, latitude, longitude)
    VALUES(?,?,?)
    '''

# Update zones table, zone_data - [zone, latitude, longitude, id]
UPDATE_ZONES_TABLE = '''
    UPDATE zones
        SET latitude = ? ,
            longitude = ?
        WHERE zone_id = ?
    '''

#----------------------------------------------------------------------
# Create the locations table
CREATE_LOCATIONS_TABLE = '''
    CREATE TABLE IF NOT EXISTS locations (
        loc_id       INTEGER PRIMARY KEY,
        zone_id      INTEGER DEFAULT (0),
        lat_long_key TEXT    NOT NULL
                             DEFAULT ('0:0'),
        latitude     DECIMAL (8, 4) DEFAULT (0.0),
        longitude    DECIMAL (8, 4) DEFAULT (0.0),
        time         DECIMAL (6, 2) DEFAULT (0),
        distance     DECIMAL (8, 2) DEFAULT (0),
        added        TEXT,
        last_used    TEXT,
        usage_cnt    INTEGER DEFAULT (1)
    );'''
LOC_ID           = 0
LOC_ZONE_ID      = 1
LOC_LAT_LONG_KEY = 2
LOC_LAT          = 3
LOC_LONG         = 4
LOC_TIME         = 5
LOC_DIST         = 6
LOC_ADDED        = 7
LOC_LAST_USED    = 8
LOC_USAGE_CNT    = 9

# Add location record - [zone_id, lat_long_key, distance, travel_time, added,
#                        last_used, usage_cnt]
ADD_LOCATION_RECORD = '''
    INSERT INTO locations(
        zone_id, lat_long_key, latitude, longitude,
        time, distance, added, last_used, usage_cnt)
    VALUES(?,?,?,?,?,?,?,?,?)
    '''

# Update locations table, location_data [last_used, usage_cnt, id]
UPDATE_LOCATION_USED = '''
    UPDATE locations
        SET last_used = ? ,
            usage_cnt = ?
        WHERE loc_id = ?
    '''

# DB Maintenance - Update locations table time & distance
UPDATE_LOCATION_TIME_DISTANCE = '''
    UPDATE locations
        SET time = ? ,
            distance = ?
        WHERE loc_id = ?
    '''


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class WazeRouteHistory(object):
    def __init__(self, wazehist_used, max_distance, track_direction):

        # Flags to control db maintenance
        self.wazehist_recalculate_time_dist_abort_flag = False
        self.wazehist_recalculate_time_dist_running_flag = False

        self.use_wazehist_flag = wazehist_used
        self.max_distance = mi_to_km(max_distance)
        self.track_direction_north_south_flag = \
                track_direction in ['north-south', 'north_south']
        self.track_latitude  = 0      # used to update the icloud3_wazeist_track_gps sensor
        self.track_longitude = 0

        self.connection = None
        wazehist_database = Gb.wazehist_database_filename
        post_event(f"Waze Location History Database > {wazehist_database}")

        self._create_connection(wazehist_database)

#--------------------------------------------------------------------
    def _create_connection(self, wazehist_database):
        """
        Create a database connection to the SQLite database
            specified by db_file

        :param      db_file: database file
        :return:    Connection object or None
        """
        self.connection = None
        self.cursor     = None

        try:
            self.connection = sqlite3.connect(wazehist_database, check_same_thread=False)
            self.cursor     = self.connection.cursor()

            self._sql(CREATE_ZONES_TABLE)
            self._sql(CREATE_LOCATIONS_TABLE)

        except:
            post_internal_error(traceback.format_exc)

        return self.connection

#--------------------------------------------------------------------
    def _sql(self, sql):
        try:
            self.cursor.execute(sql)
        except:
            post_internal_error(traceback.format_exc)

#--------------------------------------------------------------------
    def _sql_data(self, sql, data):
        self.cursor.execute(sql, data)

#--------------------------------------------------------------------
    def _add_record(self, sql, data):
        '''
        General function that adds a record to a table
        :param      sql     - sql statement that will add the data
                    data    - list containing the data to be added that matches the sql stmt
        :return     rowid   - id of the added row
        '''
        try:
            self.cursor.execute(sql, data)
            self.connection.commit()

            return self.cursor.lastrowid

        except:
            post_internal_error(traceback.format_exc)

#--------------------------------------------------------------------
    def _update_record(self, sql, data):
        '''
        Update a record in a table
        :param      sql     - sql statement that will update the data
                    data    - list containing the data to be added that matches the sql stmt
        '''
        try:
            self.cursor.execute(sql, data)
            self.connection.commit()
            return True

        except:
            error_msg = f"Error updating Waze History Database, {sql}, {data}"
            log_error_msg(error_msg)
            # post_internal_error(traceback.format_exc)
            return False
#--------------------------------------------------------------------
    def _delete_record(self, table, criteria=''):
        '''
        Select a record from a table
        :param      sql     - sql statement that will select the record
                    criteria- sql select stmt WHERE clause
        '''
        sql = (f"DELETE FROM {table}")
        if criteria:
            sql += (f" WHERE {criteria}")

        self.cursor.execute(sql)

#--------------------------------------------------------------------
    def _get_record(self, table, criteria=''):
        '''
        Select a record from a table
        :param      sql     - sql statement that will select the record
                    criteria- sql select stmt WHERE clause
                                ("lat_long_key='27.3023:-80.9738'", "location_id=342")
        '''
        try:

            sql = (f"SELECT * FROM {table}")
            if criteria:
                sql += (f" WHERE {criteria}")


            self.cursor.execute(sql)
            record = self.cursor.fetchone()

            post_monitor_msg(f"Waze Hist Database > Get Record > "
                            f"Request-{sql}, "
                            f"Record-{record}")
            return record

        except:
            post_internal_error(traceback.format_exc)
            return []

#--------------------------------------------------------------------
    def _get_all_records(self, table, criteria='', orderby=''):
        '''
        Select a record from a table
        :param      sql     - sql statement that will select the record
                    criteria- sql select stmt WHERE clause
                                ("lat_long_key='27.3023:-80.9738'", "location_id=342")
        '''
        try:

            sql = (f"SELECT * FROM {table} ")
            if criteria:
                sql += (f"WHERE {criteria} ")
            if orderby:
                sql += (f"ORDER BY {orderby} ")

            post_monitor_msg(f"Waze Hist Database > Get All Records > "
                            f"Request-{sql}")

            self.cursor.execute(sql)
            records = self.cursor.fetchall()

            return records

        except:
            post_internal_error(traceback.format_exc)
            return []

####################################################################################
    def get_location_time_dist(self, zone_id, latitude, longitude):
        '''
        Get the waze time & distance from the wacehist data base.

        Return: time        Waze route time
                distance    Waze route distance
                location_id 0 ==>   No history for this lat/long, get from Waze and add it
                            > 0 ==> The id of the recd used to update the last_used date & count
                            -1 ==>  This zone's base location is different than the base location
                                    in the zones table and the zone time/dist values need to be
                                    recalculated. Get the info from Waze and do not update the db.
        '''

        try:
            if zone_id < 1:
                return (0, 0, -1)

            lat_long_key = (f"{latitude:.04f}:{longitude:.04f}")
            criteria     = (f"zone_id={zone_id} AND lat_long_key='{lat_long_key}';")

            record       = self._get_record('locations', criteria)

            if record:
                return (record[LOC_TIME], record[LOC_DIST], record[LOC_ID])

            else:
                return (0, 0, 0)

        except:
            post_internal_error(traceback.format_exc)
            return (0, 0, 0)

#--------------------------------------------------------------------
    def add_location_record(self, zone_id, latitude, longitude, time, distance):

        try:
            if zone_id < 1:
                return

            lat_long_key = (f"{latitude:.04f}:{longitude:.04f}")
            latitude     = round(latitude, 6)
            longitude    = round(longitude, 6)
            datetime     = datetime_now()

            location_data = [zone_id, lat_long_key, latitude, longitude,
                             time, distance, datetime, datetime, 1]

            location_id = self._add_record(ADD_LOCATION_RECORD, location_data)

            self._update_sensor_ic3_wazehist_track(latitude, longitude)

            return location_id

        except:
            post_internal_error(traceback.format_exc)
            return -1

#--------------------------------------------------------------------
    def update_usage_cnt(self, location_id):
        '''
        Update the location record's last_used date & update the usage counter
        '''

        try:
            if location_id < 1:
                return

            sql = (f"SELECT * FROM locations WHERE loc_id={location_id}")

            self.cursor.execute(sql)
            record = self.cursor.fetchone()

            cnt = record[LOC_USAGE_CNT] + 1
            usage_data = [datetime_now(), cnt, location_id]

            self._update_record(UPDATE_LOCATION_USED, usage_data)

            self.cursor.execute(sql)
            record = self.cursor.fetchone()

            post_monitor_msg(   f"Waze Hist Database > Update Record > "
                                f"Table-`locations`, Criteria-`loc_id={location_id}`, "
                                f"record-{record}")

        except:
            post_internal_error(traceback.format_exc)

#--------------------------------------------------------------------
    def compress_wazehist_database(self):
        """ Compress the WazeHist Database """
        self._sql("VACUUM;")
        post_event("Waze Location History Database Compressed")

####################################################################################
#
#   WAZE HISTORY DATABASE MAINTENANCE SETUP
#
####################################################################################
    def load_track_from_zone_table(self):
        '''
        Cycle through the tracked from zones and see if the zone and it's location is in the
        zones table. Save the zone_id that will be used to access the data in locations table.
        - If not, add it.
        - If it is there, check the location to see if it is different than the one used to
          get the waze route distances & times.
          - If it has been changed, the zone's locations need to be updated with new distances
            & times or deleted.
        '''

        try:
            # Check to see if all tracked from zones are in the zones table
            Gb.wazehist_zone_id = {}
            for from_zone, Zone in Gb.TrackedZones_by_zone.items():
                criteria = (f"zone='{from_zone}'")
                wazehist_zone_recd = self._get_record('zones', criteria)

                if wazehist_zone_recd:
                    Gb.wazehist_zone_id[from_zone] = wazehist_zone_recd[ZON_ID]

                    # If the zone location was changed by more than 5m, all waze distances/times
                    # need to be updated to the new location during the midnight maintenance check
                    if (abs(wazehist_zone_recd[ZON_LAT] - Zone.latitude) > 5
                            or abs(wazehist_zone_recd[ZON_LONG] - Zone.longitude) > 5):
                        Gb.wazehist_zone_id[from_zone] = wazehist_zone_recd[ZON_ID] * -1

                        event_msg =(f"{EVLOG_ALERT}Waze Location History Database > "
                                    f"Zone Location Changed-{Zone.display_as} > "
                                    f"The zone location has changed by more than 5m. "
                                    f"The Waze Location History will not be used for this zone "
                                    f"until the history for this zone has been recalculated. "
                                    f"(zoneId- {Gb.wazehist_zone_id[from_zone]})"
                                    f"{CRLF_DOT}Select `Event Log > Action > WazeHistory-"
                                    f"Recalculate Route Time/Dist` to do this now or,"
                                    f"{CRLF_DOT}This will be done automatically tonight "
                                    f"at midnight.")
                        post_event(event_msg)

                else:
                    zone_data = [from_zone, Zone.latitude, Zone.longitude]
                    zone_id   = self._add_record(ADD_ZONE_RECORD, zone_data)
                    Gb.wazehist_zone_id[from_zone] = zone_id

                    post_monitor_msg(   f"Waze Location History Database > Added zone > "
                                        f"{from_zone}, zoneId-{zone_id}")

                self._update_sensor_ic3_wazehist_track(Zone.latitude5, Zone.longitude5)

        except:
            post_internal_error(traceback.format_exc)

####################################################################################
#
#   WAZE HISTORY DATABASE MAINTENANCE - UPDATE TIME/DISTANCE VALUES, COMPRESS DATABASE
#   NOTE: RUNS EACH NIGHT AT MIDNIGHT
#
####################################################################################
    def wazehist_recalculate_time_dist_all_zones(self):
        self.wazehist_recalculate_time_dist(all_zones_flag=True)

    def wazehist_recalculate_time_dist(self, all_zones_flag=False):
        '''
        Various maintenance functions:
            1.  Recalculate the one time/distance values based on the current zone location for
                zones that have been moved since they were added.
        '''

        # Cycle through the zones. If the location change flag is set, cycle through the
        # waze history database for those zones and recalculate the time & distance.
        try:
            Device = Gb.Devices[0]
            records = self._get_all_records('locations')
            total_cnt = len(records)

            if self.use_wazehist_flag is False:
                event_msg = (f"{EVLOG_NOTICE}Waze Location History is disabled in the "
                            "iCloud3 configuration.")
                post_event(event_msg)

            # Set the Abort Flag which is picked up in the update routine that is running
            # in another thread or as an asyncio task
            if self.wazehist_recalculate_time_dist_running_flag:
                self.wazehist_recalculate_time_dist_abort_flag = True
                Device.display_info_msg("Waze Location History Update stopped")
                return

            self.wazehist_recalculate_time_dist_running_flag = True
            for zone, zone_id in Gb.wazehist_zone_id.items():
                if self.wazehist_recalculate_time_dist_abort_flag:
                    break
                elif all_zones_flag:
                    pass
                elif zone_id > 0:       # zone_id whose location changed will be negative
                    continue

                Zone            = Gb.Zones_by_zone[zone]
                zone_display_as = Zone.display_as
                zone_from_loc   = f"{Zone.latitude},{Zone.longitude}"
                zone_id         = abs(zone_id)

                maint_time = time.perf_counter()

                recd_cnt, total_cnt, update_cnt, deleted_cnt = \
                        self._cycle_through_wazehist_records(zone_id, zone_display_as, zone_from_loc)

                zone_data = [Zone.latitude5, Zone.longitude5, zone_id]

                self._update_record(UPDATE_ZONES_TABLE, zone_data)

                maint_time_took = time.perf_counter() - maint_time

                event_msg =(f"{EVLOG_NOTICE}Waze Location History > Recalculate Time/Distance > Complete, "
                            f"TrackFmZone-{zone_display_as}, "
                            f"Records-{total_cnt}, "
                            f"Updated-{update_cnt}, "
                            f"Deleted-{deleted_cnt}, "
                            f"Took-{secs_to_time_str(maint_time_took)}")

                if self.wazehist_recalculate_time_dist_abort_flag:
                    event_msg = event_msg.replace('Complete', f'Stopped at #{recd_cnt}')
                    post_event(event_msg)
                    break

                post_event(event_msg)

        except:
            post_internal_error(traceback.format_exc)

        self.compress_wazehist_database()

        broadcast_info_msg(f"Waze History Time & Distance Update Complete")

        self.wazehist_recalculate_time_dist_running_flag = False
        self.wazehist_recalculate_time_dist_abort_flag   = False

#--------------------------------------------------------------------
    def _cycle_through_wazehist_records(self, zone_id, zone_display_as, zone_from_loc):
        '''

        '''
        Device = Gb.Devices[0]
        criteria = (f"zone_id={abs(zone_id)}")
        orderby  = "lat_long_key"
        records  = self._get_all_records('locations', criteria=criteria, orderby=orderby)

        total_cnt = len(records)
        event_msg =(f"{EVLOG_NOTICE}Waze Location History > Recalculate Time/Distance Started, "
                    f"TrackFmZone-{zone_display_as}, "
                    f"Records-{total_cnt}")
        post_event(event_msg)

        recd_cnt   = 0
        update_cnt = 0
        deleted_cnt = 0
        last_recd_lat_long_key = ''
        last_recd_loc_id       = 0

        for record in records:
            if self.wazehist_recalculate_time_dist_abort_flag:
                break

            recd_cnt += 1

            try:
                # If this record's location key is the same as the last one,
                # increase the usage count of the last recd and delete this recd
                if record[LOC_LAT_LONG_KEY] == last_recd_lat_long_key:
                    self.update_usage_cnt(last_recd_loc_id)
                    criteria = (f"loc_id={record[LOC_ID]};")
                    self._delete_record('locations', criteria)
                    log_msg = (f"Waze Location History updated, (#{recd_cnt}), "
                                f"deleted duplicate record, "
                                f"LocationKey-{record[LOC_LAT_LONG_KEY]}, "
                                f"id-{record[LOC_ID]}")
                    log_info_msg(log_msg)
                    deleted_cnt += 1

                # Get new waze time & distance and update the location record
                else:
                    last_recd_lat_long_key = record[LOC_LAT_LONG_KEY]
                    last_recd_loc_id       = record[LOC_ID]

                    update_time_flag, update_dist_flag, new_time, new_dist = \
                                self._update_wazehist_record(
                                                        recd_cnt,
                                                        zone_from_loc,
                                                        record[LOC_LAT_LONG_KEY],
                                                        record[LOC_ID],
                                                        record[LOC_TIME],
                                                        record[LOC_DIST])

                    # There was an error getting the new Waze time/dist info
                    if new_time == -1 or new_dist == -1:
                        continue

                    if update_time_flag or update_dist_flag:
                        update_cnt += 1
                        update_msg = f"✓.."
                    else:
                        update_msg = f"⊗.."

                info_msg = (f"Recalc Time/Dist > {zone_display_as[:6]}, "
                            f"{recd_cnt} of {total_cnt}, ChgCnt-{update_cnt}, "
                            f"{update_msg}"
                            f"Time-({record[LOC_TIME]:0.1f}{RARROW2}{new_time:0.1f}min), "
                            f"Dist-({record[LOC_DIST]:0.1f}{RARROW2}{new_dist:0.1f}km) "
                            "Note: Select `EventLog > Action > Recalculate Route Time/Dist` again "
                            "to cancel")
                Device.display_info_msg(info_msg)

                if (recd_cnt % 25) == 0:
                    log_msg = (f"Waze Location History, Zone-{zone_display_as}, Recds-{total_cnt}, "
                                f"Processed-{recd_cnt}, Updated-{update_cnt}")
                    log_info_msg(log_msg)

            except:
                post_internal_error(traceback.format_exc)

            if self.wazehist_recalculate_time_dist_abort_flag:
                break

            #** 5/15/2022 Delete all records with invalid times or distances
            self._delete_record('locations', 'time < 0 or distance < 0')

        log_msg = (f"Waze Location History, Zone-{zone_display_as}, Recds-{total_cnt}, "
                    f"Processed-{recd_cnt}, Updated-{update_cnt}")
        log_info_msg(log_msg)

        return recd_cnt, total_cnt, update_cnt, deleted_cnt
#--------------------------------------------------------------------
    def _update_wazehist_record(self, recd_cnt, zone_from_loc, wazehist_to_loc,
                                            loc_id, current_time, current_dist):
        '''
        Get the waze time & distance and update the wazehist db if:
            - time difference > +- 15-sec
            - distance difference > 50m
        '''
        if self.wazehist_recalculate_time_dist_abort_flag:
            return False, False, 0, 0

        wazehist_to_loc  = wazehist_to_loc.replace(':', ',')

        new_time  = current_time
        new_dist  = current_dist
        retry_cnt = 0
        while retry_cnt < 3:
            try:
                # Gb.Waze.WazeRouteTimeDistObj.__init__(zone_from_loc, wazehist_to_loc, Gb.Waze.waze_region)
                # new_time, new_dist = Gb.Waze.WazeRouteTimeDistObj.calc_route_info(Gb.Waze.waze_realtime)

                from_lat, from_long = zone_from_loc.split(',')
                to_lat  , to_long   = wazehist_to_loc.split(',')

                new_time, new_dist = \
                            Gb.Waze.WazeRouteCalc.calc_route_info   (from_lat, from_long,
                                                                    to_lat, to_long,
                                                                    log_results_flag=False)
                break

            except WRCError as err:
                retry_cnt += 1
            except Exception as err:
                log_exception(err)
                # post_internal_error('Update WazeHist Recd', traceback.format_exc)

        #** 5/15/2022 Make sure values are above 0
        if (new_time < 0
                or new_dist < 0):
            return False, False, 0, 0

        update_time_flag = (abs(new_time - current_time) > .25)
        update_dist_flag = (abs(new_dist - current_dist) > .05)

        if (update_time_flag is False
                and update_dist_flag is False):
            return update_time_flag, update_dist_flag, new_time, new_dist

        new_time = round(new_time, 2)
        new_dist = round(new_dist, 3)

        route_data = [new_time, new_dist, loc_id]

        self._update_record(UPDATE_LOCATION_TIME_DISTANCE, route_data)

        # log_msg = (f"Waze Location History updated (#{recd_cnt}), "
        #             f"Time({current_time:0.1f}{RARROW}{new_time:0.1f}min), "
        #             f"Dist({current_dist:0.1f}{RARROW}{new_dist:0.1f}km), "
        #             f"id={loc_id}")
        # log_info_msg(log_msg)

        return update_time_flag, update_dist_flag, new_time, new_dist

####################################################################################
#
#   WAZE HISTORY TRACK SENSOR UPDATE, RUNS EACH NIGHT AT MIDNIGHT
#
####################################################################################
    def wazehist_update_track_sensor(self):
        '''
        Cycle through all recds in the locations table and fill in the latitude/longitude
        of the sensor.icloud3_wazehist_track entity. This lets you see all the locations
        in the wazehist database on a lovelace map.
        '''

        Device = Gb.Devices[0]

        if self.track_direction_north_south_flag:
            orderby = 'latitude, longitude'
            orderby_text = "North-South"
        else:
            orderby = 'longitude, latitude'
            orderby_text = "East-West"

        records = self._get_all_records('locations', orderby=orderby)
        total_cnt = len(records)

        if self.use_wazehist_flag is False:
            event_msg = (f"{EVLOG_NOTICE}Waze Location History is disabled in the "
                        "iCloud3 configuration.")
            post_event(event_msg)
        event_msg = (f"Waze Location History > Refreshing locations that can be displayed "
                        f"in a HA Map using `sensor.icloud3_wazehist_track`, "
                        f"RecordCnt-{total_cnt}, "
                        f"OrderedBy-{orderby_text}")
        post_event(event_msg)

        try:
            recd_cnt = 0
            for record in records:
                recd_cnt += 1
                # if recd_cnt == 30:
                #     break
                info_msg = (f"Waze Location History > "
                            f"Records-{recd_cnt}/{total_cnt}, "
                            f"GPS-{record[LOC_LAT_LONG_KEY]}")
                Device.display_info_msg(info_msg)

                self._update_sensor_ic3_wazehist_track(record[LOC_LAT], record[LOC_LONG])

            self._update_sensor_ic3_wazehist_track(Gb.HomeZone.latitude, Gb.HomeZone.longitude)

            Device.display_info_msg(Device.format_info_msg)

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def _update_sensor_ic3_wazehist_track(self, latitude, longitude):
        '''
        Update the sensor with the latitude/longitude locations
        '''
        if Gb.WazeHist and Gb.WazeHistTrackSensor:
            self.track_latitude = latitude
            self.track_longitude = longitude
            Gb.WazeHistTrackSensor.async_update_sensor()
