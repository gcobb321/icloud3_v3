#########################################################
#
#   WAZE ROUTINES
#
#########################################################

from ..globals          import GlobalVariables as Gb
from ..const_general    import (WAZE_REGIONS, WAZE_USED, WAZE_NOT_USED, WAZE_PAUSED ,
                                WAZE_OUT_OF_RANGE, WAZE_NO_DATA)

from ..const_attrs      import (LATITUDE, LONGITUDE,ZONE)

from ..helpers.base     import (instr, round_to_zero, is_inzone_zone, is_statzone, isnot_inzone_zone,
                                post_event, post_internal_error, post_log_info_msg, internal_error_msg, post_monitor_msg,
                                log_info_msg, log_error_msg, _trace, _traceha, )
from ..helpers.time     import (time_now_secs, datetime_now, secs_since, secs_to_time_str, mins_to_time_str, )
from ..helpers.format   import (format_dist, )
from ..helpers.distance import (mi_to_km, )
from ..support.waze_history import WazeRouteHistory as WazeHist

import WazeRouteCalculator
import traceback
import logging
_LOGGER = logging.getLogger(__name__)

#waze_from_zone fields
WAZ_STATUS   = 0
WAZ_TIME     = 1
WAZ_DISTANCE = 2
WAZ_MOVED    = 3

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class Waze(object):
    def __init__(self, distance_method_waze_flag, waze_min_distance, waze_max_distance,
                    waze_realtime, waze_region):

        self.waze_status               = WAZE_USED
        self.distance_method_waze_flag = distance_method_waze_flag
        self.waze_min_distance         = waze_min_distance
        self.waze_max_distance         = waze_max_distance
        self.waze_realtime             = waze_realtime
        self.waze_region               = waze_region.upper()

        self.waze_manual_pause_flag        = False  #If Paused via iCloud command
        self.waze_close_to_zone_pause_flag = False  #pause if dist from zone < 1 flag
        self.count_waze_locates            = {}

        if Gb.um == 'mi':
            self.waze_min_distance = mi_to_km(self.waze_min_distance)
            self.waze_max_distance = mi_to_km(self.waze_max_distance)

        if self.distance_method_waze_flag:
            self.waze_status = WAZE_USED

            event_msg = (f"Set Up Waze > Region-{self.waze_region}, "
                        f"MinDist-{self.waze_min_distance} {Gb.um}, "
                        f"MaxDist-{self.waze_max_distance} {Gb.um}, "
                        f"Realtime-{self.waze_realtime}")
        else:
            self.waze_status = WAZE_NOT_USED
            event_msg = ("Waze Route Service not available")
        post_event(event_msg)


########################################################
#
#   WAZE ROUTINES
#
#########################################################
    def get_waze_data(self, Device, DeviceFmZone):

        try:
            if not self.distance_method_waze_flag:
                return (WAZE_NOT_USED, 0, 0, 0)
            # elif Device.loc_data_zone == DeviceFmZone.zone:
            #     return (WAZE_USED, 0, 0, 0)
            elif self.waze_status == WAZE_PAUSED:
                return (WAZE_PAUSED, 0, 0, 0)

            try:
                waze_start_timer = time_now_secs()

                location_id = 0
                from_history_msg = ""
                route_time, route_distance, location_id  = \
                                Gb.WazeHist.get_location_time_dist(
                                                DeviceFmZone.Zone,
                                                Device.loc_data_latitude,
                                                Device.loc_data_longitude)

                if route_distance > 0:
                    waze_from_zone = [WAZE_USED, route_time, route_distance]
                    Gb.WazeHist.update_usage_cnt(location_id)
                    from_history_msg = "From History "

                else:
                    waze_from_zone = self._get_waze_distance(
                                                Device,
                                                DeviceFmZone,
                                                Device.loc_data_latitude,
                                                Device.loc_data_longitude,
                                                DeviceFmZone.Zone.latitude,
                                                DeviceFmZone.Zone.longitude,
                                                ZONE)

                waze_status = waze_from_zone[WAZ_STATUS]

                if waze_status == WAZE_NO_DATA:
                    event_msg = (f"Waze Route Failure > No Response from Waze Servers, "
                                f"Calc distance will be used")
                    post_event(Device.devicename, event_msg)

                    return (WAZE_NO_DATA, 0, 0, 0)

                # Add a time/distance record to the waze history database
                if location_id == 0:
                    location_id = Gb.WazeHist.add_location_record(
                                                DeviceFmZone.Zone,
                                                Device.loc_data_latitude,
                                                Device.loc_data_longitude,
                                                waze_from_zone[WAZ_TIME],
                                                waze_from_zone[WAZ_DISTANCE])

                    event_msg =(f"Waze History Database > Saved Route Info > "
                                f"TravTime-{mins_to_time_str(waze_from_zone[WAZ_TIME])}, "
                                f"Distance-{format_dist(waze_from_zone[WAZ_DISTANCE])}, "
                                f"Id-{location_id}")
                    post_event(Device.devicename, event_msg)

                waze_from_last_poll = self._get_waze_distance(
                                                Device, DeviceFmZone,
                                                Device.attrs[LATITUDE],
                                                Device.attrs[LONGITUDE],
                                                Device.loc_data_latitude,
                                                Device.loc_data_longitude,
                                                "moved")

            except Exception as err:
                _LOGGER.exception(err)

                if err == "Name 'WazeRouteCalculator' is not defined":
                    self.distance_method_waze_flag = False
                    return (WAZE_NOT_USED, 0, 0, 0)

                return (WAZE_NO_DATA, 0, 0, 0)

            try:
                waze_dist_from_zone_km = round_to_zero(waze_from_zone[WAZ_DISTANCE])
                waze_dist_moved_km     = round_to_zero(waze_from_last_poll[WAZ_DISTANCE])
                # waze_time_from_zone    = round_to_zero(waze_from_zone[WAZ_TIME])

                if waze_dist_from_zone_km > 0:
                    waze_time_from_zone = round_to_zero(waze_from_zone[WAZ_TIME])
                else:
                    waze_time_from_zone = 0

                if ((waze_dist_from_zone_km > self.waze_max_distance)
                        or (waze_dist_from_zone_km < self.waze_min_distance)):
                    waze_status = WAZE_OUT_OF_RANGE

            except Exception as err:
                log_msg = (f"►INTERNAL ERROR (ProcWazeData)-{err})")
                log_error_msg(log_msg)

            event_msg = (f"Waze Route Info {from_history_msg}> "
                        f"TravTime-{mins_to_time_str(waze_time_from_zone)}, "
                        f"Distance-{format_dist(waze_dist_from_zone_km)}, "
                        f"DistMoved-{format_dist(waze_dist_moved_km)}, "
                        f"Took-{secs_to_time_str(secs_since(waze_start_timer))}")
            post_event(Device.devicename, event_msg)

            return (waze_status, waze_time_from_zone, waze_dist_from_zone_km,
                    waze_dist_moved_km)

        except Exception as err:
            self._set_waze_not_available_error(err)

            return (WAZE_NO_DATA, 0, 0, 0)

#--------------------------------------------------------------------
    def _get_waze_distance(self, Device, DeviceFmZone, from_lat, from_long,
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
                return (WAZE_NO_DATA, 0, 0)

            from_loc = f"{from_lat},{from_long}"
            to_loc   = f"{to_lat},{to_long}"

            retry_cnt = 0
            while retry_cnt < 3:
                try:
                    retry_msg = '' if retry_cnt == 0 else (f" (#{retry_cnt})")
                    if route_from == ZONE:
                        Device.display_info_msg( f"GetWazeInfoFrom-{DeviceFmZone.zone_display_as}{retry_msg}")
                    else:
                        Device.display_info_msg( f"GetWazeMovedFrom-LastLocation{retry_msg}")
                    Device.count_waze_locates += 1
                    waze_call_start_time = time_now_secs()
                    route = WazeRouteCalculator.WazeRouteCalculator(
                            from_loc, to_loc, self.waze_region)

                    route_time, route_distance = route.calc_route_info(self.waze_realtime)

                    Device.time_waze_calls += (time_now_secs() - waze_call_start_time)

                    route_time     = round(route_time, 2)
                    route_distance = round(route_distance, 2)

                    return (WAZE_USED, route_time, route_distance)

                except WazeRouteCalculator.WRCError as err:
                    retry_cnt += 1
                    log_msg = (f"Waze Server Error (#{retry_cnt}), Retrying, Type-{err}")
                    log_info_msg(log_msg)

        except Exception as err:
            self._set_waze_not_available_error(err)

        return (WAZE_NO_DATA, 0, 0)

#--------------------------------------------------------------------
    def _set_waze_not_available_error(self, err):
        ''' Turn Waze off if connection error '''

        if (instr(err, "www.waze.com")
                and instr(err, "HTTPSConnectionPool")
                and instr(err, "Max retries exceeded")
                and instr(err, "TIMEOUT")):
            self.waze_status = WAZE_NOT_USED
            event_msg = ("iCloud3 Error > Waze Server Error > Connection error accessing www.waze.com, "
                        "Waze is not available, Will use `distance_method: calc`")
            post_event(event_msg)

        else:
            log_msg = (f"iCloud3 Error > Waze Error > {err}")
            post_event(log_msg)

#--------------------------------------------------------------------
    def _get_wazehist_location_records(self, Device, DeviceFmZone):

        zone_id = Gb.wazehist_db_zone_id[DeviceFmZone.zone]

        records = Gb.WazeHist._get_wazehist_location_records(
                                                DeviceFmZone.zone,
                                                Device.loc_data_latitude,
                                                Device.loc_data_longitude)

        if records:
            post_event(records)
        else:
            post_event("No location records")

    def get_waze_from_data_history(self, Device, curr_dist_from_zone_km):
        return None

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