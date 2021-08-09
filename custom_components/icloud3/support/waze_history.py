from ..globals          import GlobalVariables as Gb
from ..const_general    import (DATETIME_ZERO, HIGH_INTEGER, EVLOG_ALERT, CRLF_DOT, RARROW, )
from ..const_attrs      import (LATITUDE, LONGITUDE, FRIENDLY_NAME,)
from ..helpers.base     import (post_event, post_internal_error, post_monitor_msg,
                                _trace, _traceha, )
from ..helpers.time     import (datetime_now, secs_to_time_str, mins_to_time_str, )
from ..helpers.format   import (format_dist, )
from ..helpers.entity_io import (set_state_attributes, set_state_attributes, )
from ..helpers.distance import (mi_to_km, )

import homeassistant.util.dt as dt_util
import traceback
import time
import sqlite3
from sqlite3 import Error


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
# Create the zones table
CREATE_ZONES_TABLE = '''
    CREATE TABLE IF NOT EXISTS zones (
        id              integer PRIMARY KEY,
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
        WHERE id = ?
    '''

#----------------------------------------------------------------------
# Create the locations table
CREATE_LOCATIONS_TABLE = '''
    CREATE TABLE IF NOT EXISTS locations (
        id           INTEGER PRIMARY KEY,
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
        WHERE id = ?
    '''

# Update locations table, location_data [last_used, usage_cnt, id]
UPDATE_LOCATION_TIME_DISTANCE = '''
    UPDATE locations
        SET latitude = ?,
            longitude = ?,
            time = ? ,
            distance = ?
        WHERE id = ?
    '''
        # SET time = ? ,
        #     distance = ?



#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class WazeRouteHistory(object):
    def __init__(self, max_distance, map_track_direction):

        self.max_distance = mi_to_km(max_distance)
        self.map_track_direction_north_south_flag = \
                map_track_direction in ['north-south', 'north_south']

        self.connection = None
        database = (f"{Gb.icloud3_dir}/waze_route_history.db")

        self._create_connection(database)

    def _create_connection(self, database):
        """
        Create a database connection to the SQLite database
            specified by db_file

        :param      db_file: database file
        :return:    Connection object or None
        """
        self.connection = None
        self.cursor     = None



        try:
            self.connection = sqlite3.connect(database, check_same_thread=False)
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
            post_internal_error(traceback.format_exc)
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
            post_monitor_msg(f"Waze Hist Database > Get Record > "
                            f"Table-{table}, Criteria-{criteria}")

            sql = (f"SELECT * FROM {table}")
            if criteria:
                sql += (f" WHERE {criteria}")

            self.cursor.execute(sql)
            record = self.cursor.fetchone()
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
            post_monitor_msg(f"Waze Hist Database > Get All Records > "
                            f"Table-{table}, Criteria-{criteria}")

            sql = (f"SELECT * FROM {table}")
            if orderby:
                sql += (f" ORDER BY {orderby}")
            if criteria:
                sql += (f" WHERE {criteria}")

            self.cursor.execute(sql)
            records = self.cursor.fetchall()

            return records

        except:
            post_internal_error(traceback.format_exc)
            return []

####################################################################################
    def get_location_time_dist(self, Zone, latitude, longitude):
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
            if Zone.wazehist_db_zone_location_changed_flag:
                return (0, 0, -1)

            zone_id = Zone.wazehist_db_zone_id
            lat_long_key = (f"{latitude:.04f}:{longitude:.04f}")

            record = self._get_record('locations',
                                        (f"zone_id={zone_id} AND lat_long_key='{lat_long_key}';"))
            if record:
                return (record[LOC_TIME], record[LOC_DIST], record[LOC_ID])

            else:
                return (0, 0, 0)

        except:
            post_internal_error(traceback.format_exc)
            return (0, 0, 0)

#--------------------------------------------------------------------
    def get_location_record(self, from_zone, latitude, longitude):

        try:
            zone_id = Gb.wazehist_db_zone_id[from_zone]
            lat_long_key = (f"{latitude:.04f}:{longitude:.04f}")

            record = self._get_record('locations',
                                        (f"zone_id={zone_id} AND lat_long_key='{lat_long_key}';"))

            return record

        except:
            post_internal_error(traceback.format_exc)
            return []

#--------------------------------------------------------------------
    def add_location_record(self, Zone, latitude, longitude, time, distance):

        try:
            zone_id      = Zone.wazehist_db_zone_id
            lat_long_key = (f"{latitude:.04f}:{longitude:.04f}")
            datetime     = datetime_now()

            location_data = [zone_id, lat_long_key, latitude, longitude,
                             time, distance, datetime, datetime, 1]

            location_id = self._add_record(ADD_LOCATION_RECORD, location_data)

            self._update_ic3_wazehist_gps(latitude, longitude)

            post_monitor_msg(f"Waze History Database > Saved Route Info > "
                            f"TravTime-{mins_to_time_str(time)}, "
                            f"Distance-{format_dist(distance)}")

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

            record = self._get_record('locations', (f"id={location_id}"))

            cnt = record[LOC_USAGE_CNT] + 1
            usage_data = [datetime_now(), cnt, location_id]

            self._update_record(UPDATE_LOCATION_USED, usage_data)

        except:
            post_internal_error(traceback.format_exc)

#--------------------------------------------------------------------
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
            for from_zone, Zone in Gb.TrackedZones_by_zone.items():
                wazehist_zone_recd = self._get_record('zones', (f"zone='{from_zone}'"))
                if wazehist_zone_recd:
                    Zone.wazehist_db_zone_id = wazehist_zone_recd[ZON_ID]

                    # If the zone location was changed, all waze distances/times need to be updated
                    # to the new location during the midnight maintenance check
                    if (wazehist_zone_recd[ZON_LAT] != Zone.latitude
                            or wazehist_zone_recd[ZON_LONG] != Zone.longitude):
                        Zone.wazehist_db_zone_location_changed_flag = True

                        event_msg =(f"{EVLOG_ALERT}Waze History Database > "
                                    f"Zone Location Changed-{Zone.display_as} > "
                                    f"The zone location has changed. The Waze History "
                                    f"will not be used for this zone until the "
                                    f"history for this zone has been recalculated. "
                                    f"ZoneId-#{Zone.wazehist_db_zone_id}"
                                    f"{CRLF_DOT}Select Event Log > Action > WazeHistory-DB "
                                    f"Maintenance to do this now or,"
                                    f"{CRLF_DOT}This will be done automatically tonight "
                                    f"at midnight.")
                        post_event(event_msg)

                else:
                    zone_data = [from_zone, Zone.latitude, Zone.longitude]

                    zone_id = self._add_record(ADD_ZONE_RECORD, zone_data)

                    Zone.wazehist_db_zone_id = zone_id

                    event_msg = (f"Waze History Database > Added zone > {from_zone}, Id-#{zone_id}")
                    post_monitor_msg(event_msg)

                self._update_ic3_wazehist_gps(Zone.latitude, Zone.longitude)

        except:
            post_internal_error(traceback.format_exc)

#--------------------------------------------------------------------
    def wazehist_db_maintenance(self, all_zones_flag=False):
        '''
        Various maintenance functions:
            1.  Recalculate the one time/distance values based on the current zone location for
                zones that have been moved since they were added.
        '''

        # Cycle through the zones. If the location change flag is set, cycle through the
        # waze history database for those zones and recalculate the time & distance.
        try:
            Device = Gb.Devices[0]
            for Zone in Gb.TrackedZones_by_zone.values():
                if all_zones_flag:
                    pass
                elif Zone.wazehist_db_zone_location_changed_flag is False:
                    continue

                criteria = (f"zone_id={Zone.wazehist_db_zone_id}")
                records = self._get_all_records('locations', criteria=criteria)

                total_cnt = len(records)
                event_msg=(f"Waze History Maintenance Started > {Zone.display_as} > "
                            f"Update Route Time & Distance, "
                            f"Records-{total_cnt}")
                post_event(event_msg)

                maint_time = time.perf_counter()
                recd_cnt = 0
                update_cnt = 0
                for record in records:
                    recd_cnt += 1
                    # if recd_cnt == 15:
                    #     break
                    lat_long_key = record[LOC_LAT_LONG_KEY].split(':')

                    latitude  = lat_long_key[0]
                    longitude = lat_long_key[1]
                    old_time  = record[LOC_TIME]
                    old_dist  = record[LOC_DIST]

                    new_time, new_dist = Gb.Waze.call_waze_route_calculator(
                                                    Zone.latitude,
                                                    Zone.longitude,
                                                    latitude,
                                                    longitude)

                    new_time = round(new_time, 2)
                    new_dist = round(new_dist, 2)

                    update_time_flag = ' ' if abs(new_time - old_time) > .25 else '✓'
                    update_dist_flag = ' ' if abs(new_dist - old_dist) > .25 else '✓'


                    if abs(new_time - old_time) > .25 or abs(new_dist - old_dist) > .25:
                        update_cnt += 1
                        route_data = [latitude, longitude, new_time, new_dist, record[LOC_ID]]

                        self._update_record(UPDATE_LOCATION_TIME_DISTANCE, route_data)

                    Device.display_info_msg(f"Waze History > {Zone.display_as[:10]}, "
                                            f"Recd-{recd_cnt}/{total_cnt}, Updt-{update_cnt}, "
                                            f"{update_time_flag}({old_time:0.2f}{RARROW}{new_time:0.2f}min), "
                                            f"{update_dist_flag}({old_dist:0.2f}{RARROW}{new_dist:0.2f}km)")
                                            # f"{record[LOC_LAT_LONG_KEY]}, "
                                            # f"{record[LOC_LAT]:0.4f}, {record[LOC_LONG]:0.4f}, "
                                            # f"({old_time:0.2f}min, {old_dist:0.2f}km){RARROW}"
                                            # f"({new_time:0.2f}min, {new_dist:0.2f}km)")

                Zone.wazehist_db_zone_location_changed_flag = False
                zone_data = [Zone.latitude, Zone.longitude, Zone.wazehist_db_zone_id]
                self._update_record(UPDATE_ZONES_TABLE, zone_data)

                maint_time_took = time.perf_counter() - maint_time
                event_msg=(f"Waze History Maintenance Complete > {Zone.display_as} > "
                            f"Update Route Time & Distance, "
                            f"Records-{total_cnt}, Updated-{update_cnt}, "
                            f"Took-{secs_to_time_str(maint_time_took)}")
                post_event(event_msg)
        except:
            post_internal_error(traceback.format_exc)

        Device.display_info_msg(f"Waze History Maintenance Complete")

#--------------------------------------------------------------------
    def wazehist_db_update_map_gps_sensor(self):
        '''
        Cycle through all recds in the locations table and fill in the latitude/longitude
        of the sensor.icloud3_wazehist_map_gps entity. This lets you see all the locations
        in the wazehist database on a lovelace map.
        '''
        Device = Gb.Devices[0]

        if self.map_track_direction_north_south_flag:
            orderby = 'latitude, longitude'
        else:
            orderby = 'longitude, latitude'

        records = self._get_all_records('locations', orderby=orderby)

        total_cnt = len(records)
        recd_cnt = 0
        for record in records:
            recd_cnt += 1
            # if recd_cnt == 30:
            #     break
            Device.display_info_msg(f"Waze History Maintenance > Update Map Sensor > "
                                    f"Records-{recd_cnt}/{total_cnt}, "
                                    f"GPS-{record[LOC_LAT_LONG_KEY]}")

            self._update_ic3_wazehist_gps(record[LOC_LAT], record[LOC_LONG])

        Device.display_info_msg(Device.format_info_text)

#--------------------------------------------------------------------
    def _update_ic3_wazehist_gps(self, latitude, longitude):
        '''
        Update the sensor with the latitude/longitude locations
        '''
        sensor_entity = 'sensor.icloud3_wazehist_map_gps'
        sensor_attrs = {}
        sensor_attrs[LATITUDE]  = latitude
        sensor_attrs[LONGITUDE] = longitude
        sensor_attrs[FRIENDLY_NAME] = 'WazeHist'

        state_value = (f"{latitude}:{longitude}")

        set_state_attributes(sensor_entity, state_value, sensor_attrs)