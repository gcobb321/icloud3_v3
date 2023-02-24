#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   WAZE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from ..global_variables     import GlobalVariables as Gb
from ..const                import (WAZE_USED, WAZE_NOT_USED, WAZE_PAUSED, WAZE_OUT_OF_RANGE, WAZE_NO_DATA,
                                    EVLOG_ALERT,
                                    WAZE_SERVERS_FNAME,
                                    LATITUDE, LONGITUDE, ZONE, )
from ..support.waze_history         import WazeRouteHistory as WazeHist
from ..support.waze_route_calc_ic3  import WazeRouteCalculator, WRCError

from ..helpers.common       import (instr, format_gps, )
from ..helpers.messaging    import (post_event, post_internal_error, log_info_msg, _trace, _traceha, )
from ..helpers.time_util    import (time_now_secs, datetime_now, secs_since, secs_to_time_str, mins_to_time_str, )
from ..helpers.dist_util    import (mi_to_km,  format_dist_km, )

import traceback
import time

WAZE_STATUS_FNAME ={WAZE_USED: 'Waze-Used',
                    WAZE_NOT_USED: 'Waze-Not Used',
                    WAZE_PAUSED: 'Waze-Paused',
                    WAZE_OUT_OF_RANGE: 'Waze-Out of Range',
                    WAZE_NO_DATA: 'Waze-No Data'}

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Waze(object):
    def __init__(self, distance_method_waze_flag, waze_min_distance, waze_max_distance,
                    waze_realtime, waze_region):

        self.waze_status                = WAZE_USED
        self.distance_method_waze_flag  = distance_method_waze_flag
        self.waze_realtime              = waze_realtime
        self.waze_region                = waze_region.upper()
        self.waze_min_distance          = waze_min_distance
        self.waze_max_distance          = waze_max_distance

        self.waze_manual_pause_flag        = False  #If Paused via iCloud command
        self.waze_close_to_zone_pause_flag = False  #pause if dist from zone < 1 flag
        self.count_waze_locates            = {}
        self.WazeRouteCalc                 = None

        try:
            if self.WazeRouteCalc is None:
                self.WazeRouteCalc = WazeRouteCalculator(self.waze_region, self.waze_realtime)

        except Exception as err:
            post_internal_error('Waze Route Info', traceback.format_exc)
            self.distance_method_waze_flag = False

        if self.distance_method_waze_flag:
            self.waze_status = WAZE_USED
            config_server_fname = WAZE_SERVERS_FNAME.get(self.waze_region.lower(), self.waze_region.lower())
            event_msg = (f"Set Up Waze > Server-{config_server_fname} ({self.waze_region.upper()}), "
                        f"CountryCode-{Gb.country_code.upper()}, "
                        f"MinDist-{self.waze_min_distance}km, "
                        f"MaxDist-{self.waze_max_distance}km, "
                        f"Realtime-{self.waze_realtime}, "
                        f"HistoryDatabaseUsed-{Gb.waze_history_database_used}")
        else:
            self.waze_status = WAZE_NOT_USED
            event_msg = ("Waze Route Service is not being used")
        post_event(event_msg)

    @property
    def is_status_USED(self):
        return (self.waze_status == WAZE_USED
                and Gb.Waze.distance_method_waze_flag)

    @property
    def is_status_NOT_USED(self):
        return self.waze_status == WAZE_NOT_USED

    @property
    def is_status_PAUSED(self):
        return self.waze_status == WAZE_PAUSED

    @property
    def is_status_NO_DATA(self):
        return self.waze_status == WAZE_NO_DATA

    @property
    def is_status_OUT_OF_RANGE(self):
        return self.waze_status == WAZE_OUT_OF_RANGE

    @property
    def waze_status_fname(self):
        return WAZE_STATUS_FNAME.get(self.waze_status, 'Waze-Unknown')


########################################################
#
#   WAZE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def get_route_time_distance(self, Device, DeviceFmZone, check_hist_db=True):
        '''
        Get the travel time and distance for the Device's current location from the
        track from zone (DeviceFmZone) using the Waze History Database, the Waze Route
        Service or the direct calculation. Also determine the distance moved from the
        last location.

        Returns:
            Waze Status - Used, Paused, Not Used, Error, etc.
            Travel Time from the zone to the device
            Distance from the zone to the device
            Distance moved from the last device's location
        '''

        try:
            if not self.distance_method_waze_flag:
                return (WAZE_NOT_USED, 0, 0, 0)
            elif self.is_status_PAUSED:
                return (WAZE_PAUSED, 0, 0, 0)
            elif Device.loc_data_zone == DeviceFmZone.from_zone:
                return (WAZE_NOT_USED, 0, 0, 0)

            try:
                from_zone         = DeviceFmZone.from_zone
                waze_status       = WAZE_USED
                route_time        = 0
                route_dist_km     = 0
                dist_moved_km     = 0
                wazehist_save_msg = ''

                waze_all_timer    = time.perf_counter()
                waze_source_msg   = ""
                location_id       = 0

                waze_status, route_time, route_dist_km, dist_moved_km, \
                        location_id, waze_source_msg = \
                        self.get_history_time_distance(Device, DeviceFmZone, check_hist_db=True)

                # Get data from Waze if not in history and not being reused
                if location_id == 0:
                    waze_status, route_time, route_dist_km = \
                                    self.get_waze_distance(
                                                Device,
                                                DeviceFmZone,
                                                Device.loc_data_latitude,
                                                Device.loc_data_longitude,
                                                DeviceFmZone.FromZone.latitude,
                                                DeviceFmZone.FromZone.longitude,
                                                ZONE)

                    if waze_status == WAZE_NO_DATA:
                        event_msg = (f"Waze Route Error > Problem connecting to Waze Servers. "
                                    f"Distance will be  calculated, Travel Time not available")
                        post_event(Device.devicename, event_msg)

                        return (WAZE_NO_DATA, 0, 0, 0)

                    # Add a time/distance record to the waze history database
                    try:
                        if (Gb.waze_history_database_used
                                and Gb.wazehist_zone_id
                                and DeviceFmZone.distance_km < Gb.WazeHist.max_distance
                                and route_time > .25
                                and Gb.wazehist_zone_id.get(from_zone, 0) > 0):
                            location_id = Gb.WazeHist.add_location_record(
                                                        Gb.wazehist_zone_id[from_zone],
                                                        Device.loc_data_latitude,
                                                        Device.loc_data_longitude,
                                                        route_time,
                                                        route_dist_km)
                            wazehist_save_msg =f"(Saved)"
                    except:
                        pass

                if route_dist_km == 0:
                    route_time = 0

                # Get distance moved since last update
                waze_moved_timer = time.perf_counter()
                if Device.loc_data_distance_moved < .5:
                    dist_moved_km = Device.loc_data_distance_moved
                else:
                    last_status, last_time, dist_moved_km = \
                                    self.get_waze_distance(
                                                    Device, DeviceFmZone,
                                                    Device.sensors[LATITUDE],
                                                    Device.sensors[LONGITUDE],
                                                    Device.loc_data_latitude,
                                                    Device.loc_data_longitude,
                                                    "moved")

                waze_moved_timer_took = time.perf_counter() - waze_moved_timer

            except Exception as err:
                post_internal_error('Waze Route Info', traceback.format_exc)
                if err == "Name 'WazeRouteCalculator' is not defined":
                    self.distance_method_waze_flag = False
                    return (WAZE_NOT_USED, 0, 0, 0)

                return (WAZE_NO_DATA, 0, 0, 0)

            try:

                if ((route_dist_km > self.waze_max_distance)
                        or (route_dist_km < self.waze_min_distance)):
                    waze_status = WAZE_OUT_OF_RANGE

            except Exception as err:
                post_internal_error('Waze Route Info', traceback.format_exc)
                route_dist_km = 0
                dist_moved_km     = 0
                route_time        = 0
                waze_source_msg   = 'Error'

            waze_all_timer_took = time.perf_counter() - waze_all_timer

            event_msg =(f"Waze Route Info > {waze_source_msg}")
            if waze_source_msg == "":
                event_msg += (  f"TravTime-{self.waze_mins_to_time_str(route_time)}, "
                                f"Dist-{format_dist_km(route_dist_km)}, "
                                f"WazeMoved-{format_dist_km(dist_moved_km)}, "
                                f"CalcMoved-{format_dist_km(Device.loc_data_distance_moved)}, "
                                f"Took-{waze_all_timer_took:0.2f} secs "
                                f"{wazehist_save_msg}")
            post_event(Device.devicename, event_msg)

            DeviceFmZone.waze_results = (WAZE_USED, route_time, route_dist_km, dist_moved_km)

            return DeviceFmZone.waze_results

        except Exception as err:
            self._set_waze_not_available_error(err)

            return (WAZE_NO_DATA, 0, 0, 0)

#--------------------------------------------------------------------
    def get_history_time_distance(self, Device, DeviceFmZone, check_hist_db=True):
        '''
        Get the time & distance from the history database or the previous results

        Return: [route_time, route_dist_km, location_id]
        '''

        from_zone       = DeviceFmZone.from_zone
        waze_status     = WAZE_USED
        route_time      = 0
        route_dist_km   = 0
        dist_moved_km   = 0
        waze_source_msg = ''

        if (Device.is_location_gps_good
                and Device.loc_data_distance_moved == 0
                and DeviceFmZone.waze_results):

            # If haven't move and accuracte location, use waze data
            # from last time
            waze_status, route_time, route_dist_km, dist_moved_km = \
                            DeviceFmZone.waze_results

            location_id = -2
            waze_source_msg = "Using Previous Waze Location Info "

        elif check_hist_db is False or Gb.WazeHist.use_wazehist_flag is False:
            location_id = 0

        else:
            # Get waze data from Waze History and update usage counter
            # for that location. (location id is 0 if not in history)
            route_time, route_dist_km, location_id  = \
                    Gb.WazeHist.get_location_time_dist(
                                            from_zone,
                                            Device.loc_data_latitude,
                                            Device.loc_data_longitude)

            if (location_id > 0
                    and route_time > 0
                    and route_dist_km > 0):
                Gb.WazeHist.update_usage_cnt(location_id)
                waze_source_msg = f"Using Route History Database, Recd-{location_id} "

            else:
                # Zone's location changed in WazeHist or invalid data. Get from Waze later
                location_id = 0

        return waze_status, route_time, route_dist_km, dist_moved_km, location_id, waze_source_msg

#--------------------------------------------------------------------
    def get_waze_distance(self, Device, DeviceFmZone, from_lat, from_long,
                    to_lat, to_long, route_from):
        """
        Example output:
            Time 72.42 minutes, distance 121.33 km.
            (72.41666666666667, 121.325)

        See https://github.com/home-assistant/home-assistant/blob
        /master/homeassistant/components/sensor/waze_travel_time.py
        See https://github.com/kovacsbalu/WazeRouteCalculator
        """

        try:
            if from_lat == 0 or from_long == 0 or to_lat == 0 or to_long == 0:
                log_msg = (f"Waze request error > No location coordinates provided, "
                            f"GPS-{format_gps(from_lat, from_long, 0, to_lat, to_long)}")
                log_info_msg(log_msg)
                return (WAZE_NO_DATA, 0, 0)

            elif self.WazeRouteCalc is None:
                log_msg = "Waze Route Calculator module is not set up"
                log_info_msg(log_msg)
                return (WAZE_NO_DATA, 0, 0)

            retry_cnt = 0
            while retry_cnt < 3:
                try:
                    retry_msg = '' if retry_cnt == 0 else (f" (#{retry_cnt})")
                    # if route_from == ZONE:
                    #     Device.display_info_msg( f"GetWazeInfoFrom-{DeviceFmZone.from_zone_display_as}{retry_msg}")
                    # elif route_from == 'moved':
                    #     Device.display_info_msg( f"GetWazeMovedFrom-LastLocation{retry_msg}")
                    waze_call_start_time = time_now_secs()

                    route_time, route_dist_km = \
                            self.WazeRouteCalc.calc_route_info(from_lat, from_long, to_lat, to_long)

                    retry_cnt += 1
                    if route_time < 0:
                        continue

                    route_time    = round(route_time, 2)
                    route_dist_km = round(route_dist_km, 2)

                    Device.count_waze_locates += 1
                    Device.time_waze_calls += (time_now_secs() - waze_call_start_time)

                    return (WAZE_USED, route_time, route_dist_km)

                except Exception as err:
                    if retry_cnt > 3:
                        log_msg = (f"Waze Server Error (#{retry_cnt}), Retrying, Type-{err}")
                        log_info_msg(log_msg)

        except Exception as err:
            # log_exception(err)
            self._set_waze_not_available_error(err)

        self._set_waze_not_available_error(f"No data returned")

        return (WAZE_NO_DATA, 0, 0)


#--------------------------------------------------------------------
    def _set_waze_not_available_error(self, err):
        ''' Turn Waze off if connection error '''

        error_msg = f"Waze Server Connection Error-{err}"
        # log_error_msg(error_msg)

        if (instr(err, "www.waze.com")
                and instr(err, "HTTPSConnectionPool")
                and instr(err, "Max retries exceeded")
                and instr(err, "TIMEOUT")):
            self.waze_status = WAZE_NOT_USED
            err = "A problem occurred connecting to `www.waze.com`. Waze is not available at this time"

        log_msg = (f"{EVLOG_ALERT}Alert > Waze Connection Error, Region-{self.waze_region} > {err}. "
                    "The route distance will be calculated, Travel Time is not available.")
        post_event(log_msg)

#--------------------------------------------------------------------
    def waze_mins_to_time_str(self, waze_time_from_zone):
        '''
        Return the message displayed in the waze time field ►►
        '''

        #Display time to the nearest minute if more than 3 min away
        if self.waze_status == WAZE_USED:
            t = waze_time_from_zone * 60
            r = 0
            if t > 180:
                t, r = divmod(t, 60)
                t = t + 1 if r > 30 else t
                t = t * 60

            waze_time_msg = secs_to_time_str(t)

        else:
            waze_time_msg = ''

        return waze_time_msg

    def __repr__(self):
        return (f"<Waze>")