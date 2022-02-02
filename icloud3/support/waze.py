#########################################################
#
#   WAZE ROUTINES
#
#########################################################

from ..global_variables import GlobalVariables as Gb
from ..const            import (EVLOG_ALERT, WAZE_REGIONS, WAZE_USED, WAZE_NOT_USED, WAZE_PAUSED,
                                WAZE_OUT_OF_RANGE, WAZE_NO_DATA,
                                LATITUDE, LONGITUDE,ZONE)

from ..helpers.base     import (instr, round_to_zero, is_inzone_zone, is_statzone, isnot_inzone_zone,
                                post_event, post_internal_error, post_log_info_msg, internal_error_msg, post_monitor_msg,
                                log_info_msg, log_error_msg, log_exception, _trace, _traceha, )
from ..helpers.time     import (time_now_secs, datetime_now, secs_since, secs_to_time_str, mins_to_time_str, )
from ..helpers.format   import (format_gps, format_dist, )
from ..helpers.distance import (mi_to_km, )
from ..support.waze_history import WazeRouteHistory as WazeHist
from ..support.waze_route_calc_ic3 import WazeRouteCalculator, WRCError

import traceback
# import logging
import time
#_LOGGER = logging.getLogger(__name__)

MODULE_NAME = 'waze'

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class Waze(object):
    def __init__(self, distance_method_waze_flag, waze_min_distance, waze_max_distance,
                    waze_realtime, waze_region):

        self.waze_status                = WAZE_USED
        self.distance_method_waze_flag  = distance_method_waze_flag
        self.waze_realtime              = waze_realtime
        self.waze_region                = waze_region.upper()
        self.waze_min_distance          = mi_to_km(waze_min_distance)
        self.waze_max_distance          = mi_to_km(waze_max_distance)

        self.waze_manual_pause_flag        = False  #If Paused via iCloud command
        self.waze_close_to_zone_pause_flag = False  #pause if dist from zone < 1 flag
        self.count_waze_locates            = {}
        self.WazeRouteCalc                 = None

        try:
            self.WazeRouteCalc = WazeRouteCalculator(self.waze_region, self.waze_realtime)

        except Exception as err:
            post_internal_error('Waze Route Info', traceback.format_exc)
            self.distance_method_waze_flag = False

        if self.distance_method_waze_flag:
            self.waze_status = WAZE_USED

            event_msg = (f"Set Up Waze > Region-{self.waze_region}, "
                        f"MinDist-{self.waze_min_distance} {Gb.um}, "
                        f"MaxDist-{self.waze_max_distance} {Gb.um}, "
                        f"Realtime-{self.waze_realtime}, "
                        f"HistoryDatabaseUsed-{Gb.waze_history_database_used}")
        else:
            self.waze_status = WAZE_NOT_USED
            event_msg = ("Waze Route Service is not being used")
        post_event(event_msg)


########################################################
#
#   WAZE ROUTINES
#
#########################################################
    def get_waze_data(self, Device, DeviceFmZone):
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
            elif self.waze_status == WAZE_PAUSED:
                return (WAZE_PAUSED, 0, 0, 0)
            elif Device.loc_data_zone == DeviceFmZone.zone:
                return (WAZE_NOT_USED, 0, 0, 0)

            try:
                from_zone         = DeviceFmZone.zone
                waze_status       = WAZE_USED
                route_time        = 0
                route_dist_km = 0
                dist_moved_km     = 0
                wazehist_save_msg = ''

                waze_all_timer = time.perf_counter()
                waze_hist_timer = time.perf_counter()
                waze_hist_timer_took = 9.99
                waze_moved_timer_took = 9.99
                waze_dist_timer_took = 9.99
                waze_addhist_timer_took = 9.99
                waze_source_msg = ""
                location_id = 0

                if (Device.is_location_gps_good
                        and Device.loc_data_distance_moved == 0
                        and DeviceFmZone.waze_results):

                    # If haven't move and accuracte location, use waze data
                    # from last time
                    waze_status, route_time, route_dist_km, dist_moved_km = \
                                    DeviceFmZone.waze_results

                    location_id = -2
                    waze_source_msg = "> From Previous Waze Location Info "

                elif (Gb.waze_history_database_used
                        and Gb.wazehist_db_zone_id.get(from_zone, 0) > 0
                        and Gb.waze_history_max_distance > 0):
                    # Get waze data from Waze History and update usage counter
                    # for that location. (location id is 0 if not in history)
                    route_time, route_dist_km, location_id  = \
                                    Gb.WazeHist.get_location_time_dist(
                                                    Gb.wazehist_db_zone_id[from_zone],
                                                    Device.loc_data_latitude,
                                                    Device.loc_data_longitude)

                    if location_id > 0:
                        waze_hist_timer_took = time.perf_counter() - waze_hist_timer
                        waze_addhist_timer = time.perf_counter()
                        Gb.WazeHist.update_usage_cnt(location_id)
                        waze_source_msg = (f"> From WazeHistory Database "
                                            f"({Gb.wazehist_db_zone_id[from_zone]}:"
                                            f"{location_id})")
                        waze_addhist_timer_took =  time.perf_counter() - waze_addhist_timer

                    else:
                        # Zone's location changed in WazeHist or  issue. Get from Waze,
                        location_id = 0

                waze_dist_timer = time.perf_counter()
                # Get data from Waze if not in history and not being reused
                if location_id == 0:
                    waze_status, route_time, route_dist_km = \
                                    self.get_waze_distance(
                                                Device,
                                                DeviceFmZone,
                                                Device.loc_data_latitude,
                                                Device.loc_data_longitude,
                                                DeviceFmZone.Zone.latitude,
                                                DeviceFmZone.Zone.longitude,
                                                ZONE)
                    waze_dist_timer_took =  time.perf_counter() - waze_dist_timer
                    if waze_status == WAZE_NO_DATA:
                        event_msg = (f"Waze Route Failure > No Response from Waze Servers, "
                                    f"Calc distance will be used")
                        post_event(Device.devicename, event_msg)

                        return (WAZE_NO_DATA, 0, 0, 0)

                    # Add a time/distance record to the waze history database
                    if (Gb.waze_history_database_used
                            and DeviceFmZone.distance_km <= Gb.WazeHist.max_distance
                            and route_time > .25
                            and Gb.wazehist_db_zone_id[from_zone] > 0):
                        location_id = Gb.WazeHist.add_location_record(
                                                    Gb.wazehist_db_zone_id[from_zone],
                                                    Device.loc_data_latitude,
                                                    Device.loc_data_longitude,
                                                    route_time,
                                                    route_dist_km)
                        wazehist_save_msg =(f", Saved to WazeHistory Database "
                                            f"({Gb.wazehist_db_zone_id[from_zone]}:"
                                            f"{location_id})")

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
                                                    Device.attrs[LATITUDE],
                                                    Device.attrs[LONGITUDE],
                                                    Device.loc_data_latitude,
                                                    Device.loc_data_longitude,
                                                    "moved")
                    # dist_moved_km = round_to_zero(waze_from_last_poll[WAZ_DISTANCE])
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

            event_msg =(f"HistTook-{waze_hist_timer_took:0.2f} secs, "
                        f"UsageHistTook-{waze_addhist_timer_took:0.2f} secs, "
                        f"WazeDistTook-{waze_dist_timer_took:0.2f} secs, "
                        f"WazeMovedTook-{waze_moved_timer_took:0.2f} secs")
            #post_event(Device.devicename, event_msg)
            waze_all_timer_took = time.perf_counter() - waze_all_timer

            event_msg =(f"Waze Route Info {waze_source_msg}")
            if waze_source_msg == "":
                event_msg += (  f"> TravTime-{self.format_waze_time_msg(route_time)}, "
                                f"Dist-{format_dist(route_dist_km)}, "
                                f"WazeMoved-{format_dist(dist_moved_km)}, "
                                f"CalcMoved-{format_dist(Device.loc_data_distance_moved)}, "
                                f"Took-{waze_all_timer_took:0.2f} secs"
                                f"{wazehist_save_msg}")
            post_event(Device.devicename, event_msg)

            DeviceFmZone.waze_results = (   WAZE_USED,
                                            route_time,
                                            route_dist_km,
                                            dist_moved_km)
            return DeviceFmZone.waze_results

        except Exception as err:
            self._set_waze_not_available_error(err)

            return (WAZE_NO_DATA, 0, 0, 0)

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
                log_msg = (f"Waze request error, No location coordinates, "
                            f"GPS-{format_gps(from_lat, from_long, 0, to_lat, to_long)}")
                log_info_msg(MODULE_NAME, log_msg)
                return (WAZE_NO_DATA, 0, 0)

            elif self.WazeRouteCalc is None:
                log_msg = "Waze Route Calculator module is not set up"
                log_info_msg(MODULE_NAME, log_msg)
                return (WAZE_NO_DATA, 0, 0)

            retry_cnt = 0
            while retry_cnt < 3:
                try:
                    retry_msg = '' if retry_cnt == 0 else (f" (#{retry_cnt})")
                    if route_from == ZONE:
                        Device.display_info_msg( f"GetWazeInfoFrom-{DeviceFmZone.zone_display_as}{retry_msg}")
                    elif route_from == 'moved':
                        Device.display_info_msg( f"GetWazeMovedFrom-LastLocation{retry_msg}")
                    waze_call_start_time = time_now_secs()

                    route_time, route_dist_km = \
                            self.WazeRouteCalc.calc_route_info(from_lat, from_long, to_lat, to_long)

                    if route_time < 0:
                        continue
                        # self._set_waze_not_available_error("No Waze data returned")
                        # return (WAZE_NO_DATA, 0, 0)

                    route_time    = round(route_time, 2)
                    route_dist_km = round(route_dist_km, 2)

                    Device.count_waze_locates += 1
                    Device.time_waze_calls += (time_now_secs() - waze_call_start_time)

                    return (WAZE_USED, route_time, route_dist_km)


                except WRCError as err:
                    retry_cnt += 1
                    log_msg = (f"Waze Server Error (#{retry_cnt}), Retrying, Type-{err}")
                    log_info_msg(MODULE_NAME, log_msg)

        except Exception as err:
            # log_exception(err)
            self._set_waze_not_available_error(err)

        self._set_waze_not_available_error("No Waze data returned")

        return (WAZE_NO_DATA, 0, 0)

#--------------------------------------------------------------------
    # def call_waze_route_calculator(self, from_lat, from_long, to_lat, to_long):
    #     '''
    #     Get the Waze time & distance between the two gps locations
    #     '''

    #     retry_cnt = 0
    #     while retry_cnt < 3:
    #         try:
    #             route_time, route_dist_km = \
    #                         self.WazeRouteCalc.calc_route_info(from_lat, from_long, to_lat, to_long)

    #             route_time    = round(route_time, 2)
    #             route_dist_km = round(route_dist_km, 3)

    #             return (route_time, route_dist_km)

    #         except WRCError as err:
    #             retry_cnt += 1

    #     return (0, 0)

#--------------------------------------------------------------------
    def _set_waze_not_available_error(self, err):
        ''' Turn Waze off if connection error '''

        error_msg = f"Waze Server Connection Error-{err}"
        # log_error_msg(MODULE_NAME, error_msg)

        if (instr(err, "www.waze.com")
                and instr(err, "HTTPSConnectionPool")
                and instr(err, "Max retries exceeded")
                and instr(err, "TIMEOUT")):
            self.waze_status = WAZE_NOT_USED
            err = "Connection error accessing www.waze.com. Waze is not available at this time. "
        else:
            log_msg = (f"{EVLOG_ALERT}iCloud3 Alert > Waze Error > {err} "
                        "Distance to zone will be calculated.")
        post_event(log_msg)

#--------------------------------------------------------------------
    def format_waze_time_msg(self, waze_time_from_zone):
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
            waze_time_msg = 'N/A'

        return waze_time_msg