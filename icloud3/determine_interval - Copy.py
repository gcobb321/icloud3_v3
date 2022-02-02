#####################################################################
#
#   This module handles all tracking activities for a device. It contains
#   the following modules:
#       TrackFromZones - iCloud3 creates an object for each device/zone
#           with the tracking data fields.
#
#   The primary methods are:
#       determine_interval - Determines the polling interval, update times,
#           location data, etc for the device based on the distance from
#           the zone.
#       determine_interval_after_error - Determines the interval when the
#           location data is to be discarded due to poor GPS, it is old or
#           some other error occurs.
#
#
#
#####################################################################


from .global_variables  import GlobalVariables as Gb
from .const             import (NOT_SET, HOME, NOT_HOME, ERROR, VALID_DATA, AWAY_FROM, TOWARDS, PAUSED,
                                DATETIME_ZERO, HIGH_INTEGER, EVLOG_NOTICE, EVLOG_TIME_RECD, CRLF_DOT, CRLF, RARROW,
                                WAZE_USED, WAZE_NOT_USED, WAZE_NO_DATA, WAZE_OUT_OF_RANGE,
                                WAZE_PAUSED, WAZE, STATIONARY, OLD_LOC_POOR_GPS_CNT,
                                NEAR_ZONE, EXIT_ZONE, IOSAPP_FNAME,
                                RETRY_INTERVAL_RANGE_1, RETRY_INTERVAL_RANGE_2, AUTH_ERROR_CNT, IOSAPP_REQUEST_LOC_CNT,
                                ZONE, ZONE_DISTANCE, INTERVAL, LAST_UPDATE_TIME,
                                NEXT_UPDATE_TIME, CALC_DISTANCE, TRAVEL_DISTANCE, DIR_OF_TRAVEL,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, WAZE_DISTANCE, LATITUDE, LONGITUDE, LOCATED_DATETIME, )

from .support           import iosapp_interface as iosapp_interface
from .helpers.base      import (instr, round_to_zero, is_inzone_zone, is_statzone, isnot_inzone_zone,
                                post_event, post_error_msg, post_log_info_msg,
                                post_internal_error, post_monitor_msg,
                                log_info_msg, log_error_msg, log_exception, _trace, _traceha, )
from .helpers.time      import (time_now_secs, secs_to_time, secs_to_time_str, mins_to_time_str,
                                secs_since, time_to_12hrtime, time_str_to_secs, secs_to_datetime, )
from .helpers.distance  import (km_to_mi, calc_distance_km, )
from .helpers.format    import (format_dist, format_cnt, )


import homeassistant.util.dt as dt_util
import traceback

# location_data fields
LD_STATUS    = 0
LD_ZONE_DIST = 1
LD_MOVED     = 2
LD_WAZE_DIST = 3
LD_CALC_DIST = 4
LD_WAZE_TIME = 5
LD_DIRECTION = 6

#waze_from_zone fields
WAZ_STATUS   = 0
WAZ_TIME     = 1
WAZ_DISTANCE = 2
WAZ_MOVED    = 3

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
def determine_interval(Device, DeviceFmZone):
    '''
    Calculate new interval. Return location based attributes.
    The durrent location:   Device.loc_data_latitude/longitude.
    The last location:      Device.attrs[LATITUDE]/[LONGITUDE]
    '''

    devicename = Device.devicename
    Device.DeviceFmZoneCurrent = DeviceFmZone

    try:
        Device.display_sensor_field(LOCATED_DATETIME, Device.loc_data_datetime)

        location_data = _get_distance_data(Device, DeviceFmZone)

        # If an error occurred, the [1] entry contains an attribute that can be passed to
        # display_info_code to display an error message
        if (location_data[LD_STATUS] == ERROR):
            return location_data[LD_ZONE_DIST]

        status_code             = location_data[LD_STATUS]
        dist_from_zone_km       = location_data[LD_ZONE_DIST]
        dist_moved_km           = location_data[LD_MOVED]
        waze_dist_from_zone_km  = location_data[LD_WAZE_DIST]
        calc_dist_from_zone_km  = location_data[LD_CALC_DIST]
        waze_time_from_zone     = location_data[LD_WAZE_TIME]
        dir_of_travel           = location_data[LD_DIRECTION]

    except:
        attrs_msg = post_internal_error('Get Distance Data', traceback.format_exc)
        return attrs_msg

    try:
        # The following checks the distance from home and assigns a
        # polling interval in minutes.  It assumes a varying speed and
        # is generally set so it will poll one or twice for each distance
        # group. When it gets real close to home, it switches to once
        # each 15 seconds so the distance from home will be calculated
        # more often and can then be used for triggering automations
        # when you are real close to home. When home is reached,
        # the distance will be 0.

        Device.display_info_msg( f"Determine Interval-{DeviceFmZone.info_status_msg}")

        waze_time_msg = "N/A"
        calc_interval = round(km_to_mi(dist_from_zone_km) / 1.5) * 60
        if Gb.Waze.waze_status == WAZE_USED:
            waze_interval = round(waze_time_from_zone * 60 * Gb.travel_time_factor , 0)
        else:
            waze_interval = 0
        interval = 15
        interval_multiplier = 1
        interval_str = ''

        battery10_flag       = (0 > Device.dev_data_battery_level >= 10)
        battery5_flag        = (0 > Device.dev_data_battery_level >= 5)
        inzone_flag          = (is_inzone_zone(Device.loc_data_zone))
        not_inzone_flag      = (isnot_inzone_zone(Device.loc_data_zone))
        was_inzone_flag      = (Device.was_inzone)
        wasnot_inzone_flag   = (Device.wasnot_inzone)
        inzone_home_flag     = (Device.loc_data_zone == HOME)     #Gb.trk_fm_zone)
        was_inzone_home_flag = (Device.attrs_zone == HOME)  #Gb.trk_fm_zone) #
        # near_zone_flag       = (instr(Device.loc_data_zone, NEAR_ZONE))

        interval_method       = ''

    except Exception as err:
        attrs_msg = post_internal_error('Set Zone Flags', traceback.format_exc)
        return attrs_msg

    try:
        if inzone_flag:
            #Reset got zone exit trigger since now in a zone for next
            #exit distance check. Also reset Stat Zone timer and dist moved.
            Device.got_exit_trigger_flag = False
            Device.StatZone.clear_timer

        #Note: If state is NEAR_ZONE, it is reset to NOT_HOME when
        #updating the device_tracker state so it will not trigger a state chng
        if Device.state_change_flag:
            if inzone_flag:
                if (is_statzone(Device.loc_data_zone)):
                    interval        = Device.StatZone.inzone_interval_secs
                    interval_method = "1.StatZone"

                #inzone & old location
                # elif Device.old_loc_poor_gps_flag and battery10_flag is False:
                elif (Device.is_location_old_or_gps_poor and battery10_flag is False):
                    interval        = _get_interval_for_error_retry_cnt(Device, OLD_LOC_POOR_GPS_CNT)
                    interval_method = '1.OldLocPoorGPS'

                else:
                    interval        = Device.inzone_interval_secs
                    interval_method = "1.EnterZone"

            #battery < 5% and near zone
            elif (battery5_flag and dist_from_zone_km <= 1):
                interval        = 15
                dir_of_travel   = 'Battery 5%'
                interval_method = "2.Battery5%"

            #battery < 10%
            elif (battery10_flag):
                interval        = Device.StatZone.inzone_interval_secs
                dir_of_travel   = 'Battery <10%'
                interval_method = "2.Battery10%"

            #entered NEAR_ZONE zone if close to HOME and last is NOT_HOME
            # elif (near_zone_flag and wasnot_inzone_flag and
            #         calc_dist_from_zone_km < 2):
            #     interval        = 15
            #     dir_of_travel   = 'NearZone'
            #     interval_method = "2.EnterNearZone"

            #entered NEAR_ZONE zone if close to HOME and last is NOT_HOME
            # elif (near_zone_flag and was_inzone_flag
            #         and calc_dist_from_zone_km < 2):
            #     interval        = 15
            #     dir_of_travel   = 'NearZone'
            #     interval_method = "2.EnterNearZone"

            #exited HOME zone
            elif (not_inzone_flag and was_inzone_home_flag):
                interval        = 240
                dir_of_travel   = AWAY_FROM
                interval_method = "2.ExitHomeZone"

            #exited 'other' zone
            elif (not_inzone_flag and was_inzone_flag):
                interval        = 120
                dir_of_travel   = 'left_zone'
                interval_method = "2.ExitZone"

            #entered 'other' zone
            else:
                interval        = 240
                interval_method = "2.ZoneChanged"

        # Exit_Zone trigger & away & exited less than 1 min ago
        elif (instr(Device.trigger, EXIT_ZONE)
                and not_inzone_flag
                and secs_since(Device.iosapp_zone_exit_secs) < 60):
            interval        = 240
            interval_method = '3.ExitTrigger'

        #inzone & poor gps & check gps accuracy when inzone
        elif (Device.is_gps_poor
                and inzone_flag
                # and Gb.check_gps_accuracy_inzone_flag):
                and Gb.discard_poor_gps_inzone_flag is False):
            interval = _get_interval_for_error_retry_cnt(Device, OLD_LOC_POOR_GPS_CNT)
            interval_method = '3.PoorGPSinZone'

        elif Device.is_gps_poor:
            interval        = _get_interval_for_error_retry_cnt(Device, OLD_LOC_POOR_GPS_CNT)
            interval_method = '3.PoorGPS'

        # elif Device.old_loc_poor_gps_flag:
        elif Device.is_location_old_or_gps_poor:
            interval        = _get_interval_for_error_retry_cnt(Device, OLD_LOC_POOR_GPS_CNT)
            interval_method = '3.OldLocPoorGPS'

        elif Device.override_interval_secs > 0:
            interval        = Device.override_interval_secs
            interval_method = '3.Override'

        elif (is_statzone(Device.loc_data_zone)):
            interval        = Device.StatZone.inzone_interval_secs
            interval_method = "3.StatZone"
            dir_of_travel   = STATIONARY

        #battery <= 10% and not near home ==> stationary time
        elif (battery10_flag and dist_from_zone_km > 1):
            interval        = Device.StatZone.inzone_interval_secs
            interval_method = "3.Battery10%"
            dir_of_travel   = "Battery <10%"

        elif (inzone_home_flag
                or (dist_from_zone_km < .05
                and dir_of_travel == TOWARDS)):
            interval        = Device.inzone_interval_secs
            interval_method = '3.InHomeZone'

        # elif near_zone_flag:
        #     interval        = 15
        #     interval_method = '3.NearZone'

        #in another zone and inzone time > travel time
        elif (inzone_flag
                and Device.inzone_interval_secs > waze_interval):
            interval        = Device.inzone_interval_secs
            interval_method = '3.InZone'

        elif dir_of_travel in ('left_zone', NOT_SET):
            interval = 150
            if inzone_home_flag:
                dir_of_travel = AWAY_FROM
            else:
                dir_of_travel = NOT_SET
            interval_method = '3.NeedInfo'

        elif dist_from_zone_km < 2.5 and Device.went_3km:
            interval        = 15             #1.5 mi = real close and driving
            interval_method = '<2.5km'

        elif dist_from_zone_km < 3.5:      #2 mi=30 sec
            interval        = 30
            interval_method = '<3.5km'

        elif waze_time_from_zone > 5 and waze_interval > 0:
            interval        = waze_interval
            interval_method = '3.WazeTime'

        elif dist_from_zone_km < 5:        #3 mi=1 min
            interval        = 60
            interval_method = '<5km'

        elif dist_from_zone_km < 8:        #5 mi=2 min
            interval        = 120
            interval_method = '<8km'

        elif dist_from_zone_km < 12:       #7.5 mi=3 min
            interval        = 180
            interval_method = '<12km'

        elif dist_from_zone_km < 20:       #12 mi=10 min
            interval        = 600
            interval_method = '<20km'

        elif dist_from_zone_km < 40:       #25 mi=15 min
            interval        = 900
            interval_method = '<40km'

        elif dist_from_zone_km > 150:      #90 mi=1 hr
            interval        = 3600
            interval_method = '>150km'

        else:
            interval        = calc_interval
            interval_method = '3.Calculated'

        if (dir_of_travel in ('', AWAY_FROM)
                and interval < 180
                and interval > 30):
            interval = 180
            interval_method += ', 6.Away(<3min)'

        elif (dir_of_travel == AWAY_FROM
                and not Gb.Waze.distance_method_waze_flag):
            interval_multiplier = 2    #calc-increase timer
            interval_method += ', 6.Away(Calc)'

        elif (dir_of_travel == NOT_SET
                and interval > 180):
            interval = 180
            interval_method += ', >180s'

        #15-sec interval (close to zone) and may be going into a stationary zone,
        #increase the interval
        elif (interval == 15
                and Gb.this_update_secs >= Device.StatZone.timer+45):
            interval = 30
            interval_method += ', 6.StatTimer+45'

        #Turn off waze close to zone flag to use waze after leaving zone or getting more than 1km from it
        if Gb.Waze.waze_close_to_zone_pause_flag:
            if (inzone_flag
                    or calc_dist_from_zone_km >= 1):
                Gb.Waze.waze_close_to_zone_pause_flag = False
                _trace(f'{DeviceFmZone.devicename_zone} Reset WazeCloseToZonePauseFlag {calc_dist_from_zone_km=} {dir_of_travel=} {Gb.Waze.waze_status=}')

        #if triggered by ios app (Zone Enter/Exit, Manual, Fetch, etc.)
        #and interval < 3 min, set to 3 min. Leave alone if > 3 min.
        if (Device.iosapp_update_flag
                and interval < 180
                and interval > 30
                and Device.override_interval_secs == 0):
            interval   = 180
            interval_method += ', 7.iosAppTrigger'

        #if changed zones on this poll reset multiplier
        if Device.state_change_flag:
            interval_multiplier = 1

        #Check accuracy again to make sure nothing changed, update counter
        if Device.is_gps_poor:
            interval_multiplier = 1

    except Exception as err:
        attrs_msg = post_internal_error('Set Interval', traceback.format_exc)
        return attrs_msg

    try:
        #Real close, final check to make sure interval is not adjusted
        if (interval <= 60
                or ((0 > Device.dev_data_battery_level >= 33) and interval >= 120)):
            interval_multiplier = 1

        interval     = interval * interval_multiplier
        interval, x  = divmod(interval, 15)
        interval     = interval * 15

        #check for max interval
        if interval > Gb.max_interval_secs and not_inzone_flag:
            interval_str = (f"{secs_to_time_str(Gb.max_interval_secs)} (max)")
            interval = Gb.max_interval_secs
            interval_method += (f", 7.Max")
        else:
            interval_str = secs_to_time_str(interval)

        if interval_multiplier > 1:
            interval_method += (f"x{interval_multiplier}")

        #check if next update is past midnight (next day), if so, adjust it
        next_poll = round((Gb.this_update_secs + interval)/5, 0) * 5

        # Update all dates and other fields
        DeviceFmZone.next_update_secs = next_poll
        DeviceFmZone.next_update_time = secs_to_time(next_poll)
        DeviceFmZone.interval_secs    = interval
        DeviceFmZone.interval_str     = interval_str
        DeviceFmZone.last_update_secs = Gb.this_update_secs
        DeviceFmZone.last_update_time = time_to_12hrtime(Gb.this_update_time)
        DeviceFmZone.interval_method  = interval_method
        DeviceFmZone.dir_of_travel    = dir_of_travel

    #--------------------------------------------------------------------------------
        #if more than 3km(1.8mi) then assume driving, used later above
        if dist_from_zone_km > 3:                # 1.8 mi
            Device.went_3km = True
        elif dist_from_zone_km < .03:            # home, reset flag
            Device.went_3km = False

    except Exception as err:
        attrs_msg = post_internal_error('Update DeviceFmZone Times', traceback.format_exc)

    #--------------------------------------------------------------------------------
    try:
        #if 'NearZone' zone, do not change the state
        # if near_zone_flag:
        #     zone = NOT_HOME

        #if poor gps and moved less than 1km, redisplay last distances
        if (Device.state_change_flag is False
                and Device.is_gps_poor
                and dist_moved_km < 1):
            dist_from_zone_km      = DeviceFmZone.zone_dist
            waze_dist_from_zone_km = DeviceFmZone.waze_dist
            calc_dist_from_zone_km = DeviceFmZone.calc_dist
            waze_time_from_zone    = DeviceFmZone.waze_time

        else:

            #save for next poll if poor gps
            DeviceFmZone.zone_dist = dist_from_zone_km
            DeviceFmZone.waze_dist = waze_dist_from_zone_km
            DeviceFmZone.waze_time = waze_time_from_zone
            DeviceFmZone.calc_dist = calc_dist_from_zone_km

        waze_time_msg = Gb.Waze.format_waze_time_msg(waze_time_from_zone)

    except Exception as err:
        attrs_msg = post_internal_error('Set DeviceFmZone Distance', traceback.format_exc)

    #--------------------------------------------------------------------------------
    try:
        #Make sure the new 'last state' value is the internal value for
        #the state (e.g., Away-->not_home) to reduce state change triggers later.
        attrs                   = {}
        attrs[INTERVAL]         = interval
        attrs[LAST_UPDATE_TIME] = secs_to_datetime(Gb.this_update_secs)
        attrs[NEXT_UPDATE_TIME] = secs_to_datetime(next_poll)
        attrs[TRAVEL_TIME]      = waze_time_from_zone
        attrs[TRAVEL_TIME_MIN]  = waze_time_from_zone

        if Gb.Waze.waze_status == WAZE_USED:
            attrs[WAZE_DISTANCE] = km_to_mi(waze_dist_from_zone_km)
        elif Gb.Waze.waze_status == WAZE_NOT_USED:
            attrs[WAZE_DISTANCE] = 'NotUsed'
        elif Gb.Waze.waze_status == WAZE_NO_DATA:
            attrs[WAZE_DISTANCE] = 'NoData'
        elif Gb.Waze.waze_status == WAZE_OUT_OF_RANGE:
            if waze_dist_from_zone_km < 1:
                attrs[WAZE_DISTANCE] = ''
            elif waze_dist_from_zone_km < Gb.Waze.waze_min_distance:
                attrs[WAZE_DISTANCE] = 'DistLow'
            else:
                attrs[WAZE_DISTANCE] = 'DistHigh'
        elif dir_of_travel == 'in_zone':
            attrs[WAZE_DISTANCE] = ''
        elif Gb.Waze.waze_status == WAZE_PAUSED:
            attrs[WAZE_DISTANCE] = PAUSED
        elif waze_dist_from_zone_km > 0:
            attrs[WAZE_DISTANCE] = km_to_mi(waze_dist_from_zone_km)
        else:
            attrs[WAZE_DISTANCE] = ''
        attrs[ZONE_DISTANCE]   = km_to_mi(dist_from_zone_km)
        attrs[CALC_DISTANCE]   = km_to_mi(calc_dist_from_zone_km)
        attrs[DIR_OF_TRAVEL]   = dir_of_travel
        attrs[TRAVEL_DISTANCE] = km_to_mi(dist_moved_km)


        #save for event log
        # dir_of_travel_msg = (f" ({dir_of_travel})") if dir_of_travel else ''
        if type(waze_time_msg) != str: waze_time_msg = ''
        DeviceFmZone.last_tavel_time   = (f"{waze_time_msg}")
        # DeviceFmZone.last_tavel_time   = (f"{waze_time_msg}{dir_of_travel_msg}")
        DeviceFmZone.last_distance_str = (f"{km_to_mi(dist_from_zone_km)} {Gb.um}")

        if Device.is_location_gps_good:
            Device.old_loc_poor_gps_cnt = 0


        Device.display_info_msg(Device.format_info_text)
        post_results_message_to_event_log(Device, DeviceFmZone)
        post_zone_time_dist_event_msg(Device, DeviceFmZone)

        DeviceFmZone.attrs = attrs.copy()

        return attrs

    except Exception as err:
        attrs_msg = post_internal_error('Set Final Results', traceback.format_exc)
        return attrs_msg

#--------------------------------------------------------------------------------
def post_results_message_to_event_log(Device, DeviceFmZone):
    # Zone = Gb.Zones_by_zone[Device.loc_data_zone]
    # event_msg = (f"Results ")
    # if Device.track_from_other_zone_flag:
    event_msg = (f"Results: From-{DeviceFmZone.zone_display_as} > "
                f"NextUpdate-{DeviceFmZone.next_update_time}, "
                f"Interval-{DeviceFmZone.interval_str}, "
                f"TravTime-{DeviceFmZone.last_tavel_time}, "
                f"Distance-{km_to_mi(DeviceFmZone.zone_dist)} {Gb.um}, "
                f"Method-{DeviceFmZone.interval_method}, "
                f"Direction-{DeviceFmZone.dir_of_travel}")

    if Device.StatZone.timer > 0:
        event_msg +=(f", IntoStatZoneAfter-{secs_to_time(Device.StatZone.timer)}")
    if Device.StatZone.moved_dist > 0:
        event_msg +=(f", Moved-{format_dist(Device.StatZone.moved_dist)}")
    post_event(Device.devicename, event_msg)

#--------------------------------------------------------------------------------
def copy_near_device_results(Device, DeviceFmZone, NearDevice, NearDeviceFmZone):
    '''
    The Device is near the NearDevice for the DeviceFmZone zone results. Copy the NearDevice
    variables to Device since everything is the same.
    '''

    DeviceFmZone.attrs             = NearDeviceFmZone.attrs.copy()

    DeviceFmZone.zone_dist         = NearDeviceFmZone.zone_dist
    DeviceFmZone.waze_dist         = NearDeviceFmZone.waze_dist
    DeviceFmZone.waze_time         = NearDeviceFmZone.waze_time
    DeviceFmZone.calc_dist         = NearDeviceFmZone.calc_dist
    DeviceFmZone.next_update_secs  = NearDeviceFmZone.next_update_secs
    DeviceFmZone.next_update_time  = NearDeviceFmZone.next_update_time
    DeviceFmZone.interval_secs     = NearDeviceFmZone.interval_secs
    DeviceFmZone.interval_str      = NearDeviceFmZone.interval_str
    DeviceFmZone.interval_method   = NearDeviceFmZone.interval_method
    DeviceFmZone.last_update_secs  = NearDeviceFmZone.last_update_secs
    DeviceFmZone.last_update_time  = NearDeviceFmZone.last_update_time
    DeviceFmZone.last_tavel_time   = NearDeviceFmZone.last_tavel_time
    DeviceFmZone.last_distance_str = NearDeviceFmZone.last_distance_str
    DeviceFmZone.dir_of_travel     = NearDeviceFmZone.dir_of_travel
    Device.StatZone.timer          = NearDevice.StatZone.timer
    Device.StatZone.moved_dist     = NearDevice.StatZone.moved_dist


    Device.display_info_msg(Device.format_info_text)
    post_results_message_to_event_log(Device, DeviceFmZone)
    post_zone_time_dist_event_msg(Device, DeviceFmZone)

    return DeviceFmZone.attrs

#########################################################
#
#   iCloud FmF or FamShr authentication returned an error or no location
#   data is available. Update counter and device attributes and set
#   retry intervals based on current retry count.
#
#########################################################
def determine_interval_after_error(Device, info_msg, counter=OLD_LOC_POOR_GPS_CNT):
    '''
    Handle errors where the device can not be or should not be updated with
    the current data. The update will be retried 4 times on a 15 sec interval.
    If the error continues, the interval will increased based on the retry
    count using the following cycles:
        1-4   - 15 sec
        5-8   - 1 min
        9-12  - 5min
        13-16 - 15min
        >16   - 30min

    The following errors use this routine:
        - iCloud Authentication errors
        - FmF location data not available
        - Old location
        - Poor GPS Acuracy
    '''
    devicename   = Device.devicename
    Device.post_location_data_event_msg('Location Data (Old)')

    try:
        interval = 0
        if counter == OLD_LOC_POOR_GPS_CNT:
            error_cnt = Device.old_loc_poor_gps_cnt
            range_tbl = RETRY_INTERVAL_RANGE_1

        elif counter == AUTH_ERROR_CNT:
            error_cnt = Gb.icloud_no_data_error_cnt
            range_tbl = RETRY_INTERVAL_RANGE_1

        elif counter == IOSAPP_REQUEST_LOC_CNT:
            error_cnt = Device.iosapp_request_loc_retry_cnt
            range_tbl = RETRY_INTERVAL_RANGE_2
        else:
            interval = 60

        # Retry in 10-secs if this is the first time retried
        if error_cnt == 1:
            interval = 10

        elif interval == 0:
            interval = .25
            for cnt, cnt_time in range_tbl.items():
                if cnt <= error_cnt:
                    interval = cnt_time

            interval = interval * 60

        if interval < 0:
            Device.pause_tracking

            message = {
                "title": "iCloud3 Tracking Exception",
                "message": (f"Old Location or Poor GPS Accuracy Error "
                            f"Count exceeded (#{error_cnt}). Event Log > Actions > "
                            f"Resume to restart tracking."),
                "data": {"subtitle": "Tracking has been Paused"}}
            iosapp_interface.send_message_to_device(Device, message)
            return

        # If the interval is chnging and the data source is from the iOS App
        # send a location request to the phone
        if (interval > Device.DeviceFmZoneHome.interval_secs
                and interval >= 60
                and counter == OLD_LOC_POOR_GPS_CNT
                and Device.dev_data_source == IOSAPP_FNAME
                and Device.iosapp_monitor_flag):
            iosapp_interface.request_location(Device)

        next_poll     = Gb.this_update_secs + interval
        next_updt_str = secs_to_time(next_poll)

        attrs = {}
        attrs[INTERVAL]         = interval  #secs_to_time_str(interval)
        attrs[NEXT_UPDATE_TIME] = secs_to_datetime(next_poll)
        attrs[LAST_UPDATE_TIME] = secs_to_datetime(Gb.this_update_secs)

        # Set all track from zone intervals. This prevents one zone from triggering an update
        # when the location data was poor.
        for from_zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
            DeviceFmZone.interval_secs    = interval
            DeviceFmZone.next_update_secs = next_poll
            DeviceFmZone.next_update_time = next_updt_str
            DeviceFmZone.last_update_secs = Gb.this_update_secs
            DeviceFmZone.last_update_time = time_to_12hrtime(Gb.this_update_time)
            DeviceFmZone.interval_str     = secs_to_time_str(interval)

            # Move Stationary Zone timer if it is set and expired so it does not trigger an update
            if Device.StatZone.timer_expired:
                Device.StatZone.timer = next_poll

            Gb.Sensors.update_device_sensors(Device, attrs, DeviceFmZone)

        Device.device_being_updated_flag = False

        # Often, iCloud does not actually locate the device but just returns the last
        # location it has. A second call is needed after a 5-sec delay. This also
        # happens after a reauthentication. If so, do not display an error on the
        # first retry.
        Device.display_info_msg(info_msg)
        if (Device.outside_no_exit_trigger_flag
            or (Device.old_loc_poor_gps_cnt > 0
                and secs_since(DeviceFmZone.next_update_secs) < \
                            (DeviceFmZone.interval_secs + 10))):
            Device.count_discarded_update += 1
            event_msg =(f"Discarded > {info_msg}, "
                        f"Retry In {DeviceFmZone.interval_str} at {next_updt_str}")
            if Device.is_offline:
                event_msg += (f", DeviceStatus-{Device.dev_data_device_status}")
            post_event(devicename, event_msg)

        elif counter == AUTH_ERROR_CNT:
            event_msg = (f"Results > RetryCounter-{Gb.icloud_no_data_error_cnt}, "
                        f"Retry In {DeviceFmZone.interval_str} at {next_updt_str}")

    except Exception as err:
        log_exception(err)


#########################################################
#
#   UPDATE DEVICE LOCATION & INFORMATION ATTRIBUTE FUNCTIONS
#
#########################################################
def _get_distance_data(Device, DeviceFmZone):
    """
    Determine the location of the device.
        Returns:
            - zone (current zone from lat & long)
                set to HOME if distance < home zone radius
            - dist_from_zone_km (mi or km)
            - dist_traveled (since last poll)
            - dir_of_travel (towards, away_from, stationary, in_zone,
                left_zone, near_home)
    """

    try:
        Device.display_info_msg(f"GetDistancesFrom-{DeviceFmZone.zone_display_as}")

        if Device.loc_data_latitude == 0 or Device.loc_data_longitude == 0:
            event_msg = "No location data available, will retry"
            post_event(Device.devicename, event_msg)
            return (ERROR, {})

        last_dir_of_travel = NOT_SET
        dist_from_zone_km  = -1

        # FromZone  = DeviceFmZone.Zone
        # calc_dist_from_zone_km = calc_distance_km(
        #                                         Device.loc_data_latitude,
        #                                         Device.loc_data_longitude,
        #                                         FromZone.latitude,
        #                                         FromZone.longitude)
        calc_dist_from_zone_km = DeviceFmZone.distance_km

    except Exception as err:
        attrs = post_internal_error('Calc Distance', traceback.format_exc)
        return (ERROR, attrs)

    try:
        #Not available if first time after reset
        if Device.attrs_zone != NOT_SET:
            last_dir_of_travel = DeviceFmZone.dir_of_travel
            # last_dir_of_travel = DeviceFmZone.attrs[DIR_OF_TRAVEL]
            last_dir_of_travel = last_dir_of_travel.replace('*', '')
            last_dir_of_travel = last_dir_of_travel.replace('?', '')

        interval_str = DeviceFmZone.interval_str

    except Exception as err:
        attrs = post_internal_error('Setup Location', traceback.format_exc)
        return (ERROR, attrs)

    try:
        # Determine how Waze should be handled
        if Gb.Waze.distance_method_waze_flag:
            if (Gb.Waze.waze_manual_pause_flag
                    or Gb.Waze.waze_close_to_zone_pause_flag):
                Gb.Waze.waze_status = WAZE_PAUSED
            else:
                Gb.Waze.waze_status = WAZE_USED
        else:
            Gb.Waze.waze_status = WAZE_NOT_USED

        #Make sure distance and zone are correct for tracked from zone, initialize
        if (calc_dist_from_zone_km <= .05
                or Device.loc_data_zone == DeviceFmZone.zone):
            Device.loc_data_zone   = DeviceFmZone.zone
            calc_dist_from_zone_km = 0
            #Gb.Waze.waze_status    = WAZE_PAUSED

        # Pause waze and set close to zone pause flag if nearing a track from zone
        elif (calc_dist_from_zone_km < 1
                and Device.loc_data_zone == DeviceFmZone.zone
                and last_dir_of_travel == TOWARDS):        #in ('towards', NEAR_ZONE)):
            Gb.Waze.waze_status = WAZE_PAUSED
            Gb.Waze.waze_close_to_zone_pause_flag = True
            _trace(f'Set WazeCloseToZonePauseFlag {calc_dist_from_zone_km=} {last_dir_of_travel=} {Gb.Waze.waze_status=}')

        #Determine if Waze should be used based on calculated distance
        elif (calc_dist_from_zone_km > Gb.Waze.waze_max_distance
                or calc_dist_from_zone_km < Gb.Waze.waze_min_distance):
            Gb.Waze.waze_status = WAZE_OUT_OF_RANGE

        #Initialize Waze default fields
        waze_dist_from_zone_km = calc_dist_from_zone_km
        waze_time_from_zone    = 0
        waze_dist_moved_km     = Device.loc_data_distance_moved

    except Exception as err:
        attrs = post_internal_error('Initialize Distances', traceback.format_exc)
        return (ERROR, attrs)

    try:
        if Gb.Waze.waze_status == WAZE_USED:
            waze_time_dist_info = Gb.Waze.get_waze_data(
                                            Device,
                                            DeviceFmZone)

            Gb.Waze.waze_status = waze_time_dist_info[LD_STATUS]
            if Gb.Waze.waze_status == WAZE_USED:
                waze_time_from_zone    = waze_time_dist_info[WAZ_TIME]
                waze_dist_from_zone_km = waze_time_dist_info[WAZ_DISTANCE]
                waze_dist_moved_km     = waze_time_dist_info[WAZ_MOVED]

    except Exception as err:
        attrs = post_internal_error('Waze Error', traceback.format_exc)
        Gb.Waze.waze_status = WAZE_NO_DATA

    try:
        #don't reset data if poor gps, use the best we have
        Device.display_info_msg( f"Finalizing-{DeviceFmZone.info_status_msg}")
        if Device.loc_data_zone == DeviceFmZone.zone:
            distance_method       = 'Home/Calc'
            dist_from_zone_km     = 0
            dist_moved_km         = 0

        elif Gb.Waze.waze_status == WAZE_USED:
            distance_method       = WAZE
            dist_from_zone_km     = waze_dist_from_zone_km
            dist_moved_km         = waze_dist_moved_km

        else:
            distance_method       = 'Calc'
            dist_from_zone_km     = calc_dist_from_zone_km
            dist_moved_km         = Device.loc_data_distance_moved

    except Exception as err:
        attrs = post_internal_error('Calc Distance', traceback.format_exc)
        return (ERROR, attrs)

    try:
        section = "dir_of_trav"
        dir_of_travel = ''
        if DeviceFmZone.attrs[ZONE_DISTANCE]:
            last_zone_distance = DeviceFmZone.attrs[ZONE_DISTANCE]
        else:
            last_zone_distance = 0

        if is_statzone(Device.loc_data_zone):
            dir_of_travel = STATIONARY

        # elif Device.loc_data_zone not in (NOT_HOME, NEAR_ZONE):
        elif Device.loc_data_zone != NOT_HOME:      #not in (NOT_HOME, NEAR_ZONE):
            dir_of_travel = 'in_zone'

        elif last_dir_of_travel == "in_zone":
            dir_of_travel = 'left_zone'

        elif Device.is_gps_poor:
            dir_of_travel = 'Poor.GPS'

        elif Device.attrs[ZONE] == NOT_SET:
            dir_of_travel = ''

        elif dist_from_zone_km > (last_zone_distance + .25):
            dir_of_travel = AWAY_FROM

        elif last_zone_distance > (dist_from_zone_km - .25):
            dir_of_travel = TOWARDS

        else:
            #didn't move far enough to tell current direction
            dir_of_travel = (f"{last_dir_of_travel}?")

        if Device.loc_data_zone == NOT_HOME:
            if Device.StatZone.timer == 0:
                Device.StatZone.reset_timer_time

            # If moved more than stationary zone limit (~.06km(200ft)),
            # reset StatZone still timer
            # Use calc distance rather than waze for better accuracy
            elif (calc_dist_from_zone_km > Device.StatZone.min_dist_from_zone_km
                    and Device.loc_data_distance_moved > Device.StatZone.dist_move_limit):
                event_msg =(f"Stat Zone Timer Reset > "
                            f"MovedTooFar-{format_dist(Device.loc_data_distance_moved)}, "
                            f"Limit-{format_dist(Device.StatZone.dist_move_limit)}, "
                            f"Timer-{secs_to_time(Device.StatZone.timer)}{RARROW}")

                event_msg +=(f"Moved-{format_dist(Device.loc_data_distance_moved)}, "
                            f"Timer-{secs_to_time(Device.StatZone.timer)}, ")

                Device.StatZone.reset_timer_time

                event_msg += (f"{secs_to_time(Device.StatZone.timer)}")
                post_monitor_msg(Device.devicename, event_msg)

        section                = "Finalize"
        dist_from_zone_km      = round_to_zero(dist_from_zone_km)
        dist_moved_km          = round_to_zero(dist_moved_km)
        waze_dist_from_zone_km = round_to_zero(waze_dist_from_zone_km)
        waze_dist_moved_km     = round_to_zero(waze_dist_moved_km)

        distance_data = [VALID_DATA,
                        dist_from_zone_km,
                        dist_moved_km,
                        waze_dist_from_zone_km,
                        calc_dist_from_zone_km,
                        waze_time_from_zone,
                        dir_of_travel]

        # DeviceFmZone.last_get_distance_data_results = distance_data.copy()

        return  distance_data

    except Exception as err:
        attrs = post_internal_error(section, traceback.format_exc)
        return (ERROR, attrs)



#--------------------------------------------------------------------------------
def post_zone_time_dist_event_msg(Device, DeviceFmZone):
    '''
    Post the iosapp state, ic3 zone, interval, travel time, distance msg to the
    Event Log
    '''

    if Device.iosapp_monitor_flag:
        iosapp_state = Device.iosapp_data_state
        if iosapp_state in Gb.Zones_by_zone:
            iosapp_state = Gb.Zones_by_zone[iosapp_state].display_as
    else:
        iosapp_state = 'Not Used'

    ic3_zone = Device.loc_data_zone
    if ic3_zone in Gb.Zones_by_zone:
        ic3_zone = Gb.Zones_by_zone[ic3_zone].display_as

    if Device.loc_data_zone == NOT_SET:
        interval = travel_time = distance = '──'
    else:
        interval     = DeviceFmZone.interval_str.split("(")[0]
        travel_time  = DeviceFmZone.last_tavel_time
        travel_time  = '' if travel_time == '0 sec' else travel_time
        distance     = DeviceFmZone.zone_distance_str

    event_msg =(f"{EVLOG_TIME_RECD}{iosapp_state},{ic3_zone},{interval},{travel_time},{distance}")
    post_event(Device.devicename, event_msg)

#--------------------------------------------------------------------------------
def _get_interval_for_error_retry_cnt(Device, counter=OLD_LOC_POOR_GPS_CNT, pause_control_flag=False):
    '''
    Get the interval time based on the retry_cnt.
    retry_cnt   =   poor_location_gps count (default)
                =   iosapp_request_loc_sent_retry_cnt
                =   retry pyicloud authorization count
    pause_control_flag = True if device will be paused (interval is negative)
                = False if just getting interfal and device will not be paused

    Returns     interval in minutes
                (interval is negative if device should be paused)

    Interval range table - key = retry_cnt, value = time in minutes
    - poor_location_gps cnt, icloud_authentication cnt (default):
        interval_range_1 = {0:.25, 4:1, 8:5,  12:30, 16:60, 20:120, 24:240}
    - request iosapp location retry cnt:
        interval_range_2 = {0:.5,  4:2, 8:30, 12:60, 16:120}

    '''
    if counter == OLD_LOC_POOR_GPS_CNT:
        retry_cnt = Device.old_loc_poor_gps_cnt
        range_tbl = RETRY_INTERVAL_RANGE_1

    elif counter == AUTH_ERROR_CNT:
        retry_cnt = Gb.icloud_acct_auth_error_cnt
        range_tbl = RETRY_INTERVAL_RANGE_1

    elif counter == IOSAPP_REQUEST_LOC_CNT:
        retry_cnt = Device.iosapp_request_loc_retry_cnt
        range_tbl = RETRY_INTERVAL_RANGE_2
    else:
        return 60

    interval = .25
    for k, v in range_tbl.items():
        if k <= retry_cnt:
            interval = v

    if pause_control_flag is False: interval = abs(interval)
    interval = interval * 60

    return interval
