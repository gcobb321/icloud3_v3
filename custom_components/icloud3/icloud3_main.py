"""
Platform that supports scanning iCloud.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.icloud/


Special Note: I want to thank Walt Howd, (iCloud2 fame) who inspired me to
    tackle this project. I also want to give a shout out to Kovács Bálint,
    Budapest, Hungary who wrote the Python WazeRouteCalculator and some
    awesome HA guys (Petro31, scop, tsvi, troykellt, balloob, Myrddyn1,
    mountainsandcode,  diraimondo, fabaff, squirtbrnr, and mhhbob) who
    gave me the idea of using Waze in iCloud3.
                ...Gary Cobb aka GeeksterGary, Vero Beach, Florida, USA

Thanks to all
"""

VERSION = '3.0.0'


import os
import time
import traceback
from re import match
import voluptuous as vol
from   homeassistant.util                   import slugify
import homeassistant.util.yaml.loader       as yaml_loader
import homeassistant.util.dt                as dt_util
from   homeassistant.util.location          import distance
import homeassistant.helpers.config_validation as cv
from   homeassistant.helpers.event          import track_utc_time_change
from   homeassistant.components.device_tracker import PLATFORM_SCHEMA
from   homeassistant.helpers.dispatcher     import dispatcher_send
from homeassistant import config_entries

# =================================================================

from .global_variables  import GlobalVariables as Gb
from .const             import (VERSION,
                                HOME, NOT_HOME, NOT_SET, HIGH_INTEGER, RARROW,
                                STATIONARY, TOWARDS,
                                ICLOUD_FNAME,
                                TRACKING_NORMAL,
                                CMD_RESET_PYICLOUD_SESSION, NEAR_DEVICE_DISTANCE,
                                STAT_ZONE_MOVE_DEVICE_INTO, STAT_ZONE_MOVE_TO_BASE,
                                OLD_LOC_POOR_GPS_CNT, AUTH_ERROR_CNT,
                                IOSAPP_UPDATE, ICLOUD_UPDATE,
                                EVLOG_IC3_STAGE_HDR, EVLOG_UPDATE_START, EVLOG_UPDATE_END, EVLOG_ALERT,
                                FMF, FAMSHR, IOSAPP, IOSAPP_FNAME,
                                ENTER_ZONE,
                                LATITUDE, LONGITUDE, BATTERY_SOURCE,
                                GPS, INTERVAL, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
                                NEXT_UPDATE,
                                )

from .support           import start_ic3
from .support           import start_ic3_control
from .support           import restore_state
from .support           import iosapp_data_handler
from .support           import iosapp_interface
from .support           import pyicloud_ic3_interface
from .support           import icloud_data_handler
from .support           import service_handler
from .support           import determine_interval as det_interval

from .helpers.common    import (instr, is_inzone_zone, is_statzone, isnot_inzone_zone, )
from .helpers.messaging import (broadcast_info_msg,
                                post_event, post_error_msg, post_monitor_msg, post_internal_error,
                                log_info_msg, log_exception, log_start_finish_update_banner,
                                log_debug_msg, _trace, _traceha, )
from .helpers.time_util import (time_now_secs, secs_to_time,  secs_to, secs_since,
                                secs_to_time, secs_to_time_str,
                                datetime_now,  calculate_time_zone_offset,
                                secs_to_time_age_str, )
from .helpers.dist_util import (m_to_ft_str, calc_distance_km, format_dist_km, format_dist_m, )


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3:
    """iCloud3 Device Tracker Platform"""

    def __init__(self):

        Gb.hass_configurator_request_id = {}
        Gb.version                         = VERSION

        Gb.polling_5_sec_loop_running      = False
        self.pyicloud_refresh_time         = {}     # Last time Pyicloud was refreshed for the trk method
        self.pyicloud_refresh_time[FMF]    = 0
        self.pyicloud_refresh_time[FAMSHR] = 0

        Gb.authenticated_time              = 0
        Gb.icloud_acct_error_cnt           = 0
        Gb.authentication_error_retry_secs = HIGH_INTEGER

        Gb.evlog_trk_monitors_flag       = False
        Gb.log_debug_flag                = False
        Gb.log_rawdata_flag              = False
        Gb.log_debug_flag_restart        = None
        Gb.log_rawdata_flag_restart      = None

        Gb.start_icloud3_inprocess_flag    = False
        Gb.start_icloud3_request_flag      = False
        Gb.device_update_in_process_flag = False
        Gb.any_device_was_updated_reason = ''
        Gb.master_update_in_process_flag = False

        self.attributes_initialized_flag = False
        self.e_seconds_local_offset_secs = 0

        #initialize variables configuration.yaml parameters
        start_ic3.set_global_variables_from_conf_parameters()


    def __repr__(self):
        return (f"<iCloud3: {Gb.version}>")

#--------------------------------------------------------------------
    def start_icloud3(self):

        try:
            if Gb.start_icloud3_inprocess_flag:
                return False

            service_handler.issue_ha_notification()

            self.start_timer = time_now_secs()
            Gb.initial_locate_complete_flag = False
            self.startup_log_msgs           = ''
            self.startup_log_msgs_prefix    = ''

            start_ic3_control.stage_1_setup_variables()
            start_ic3_control.stage_2_prepare_configuration()

            if Gb.polling_5_sec_loop_running is False:
                broadcast_info_msg("Set Up 5-sec Polling Cycle")
                Gb.polling_5_sec_loop_running = True
                track_utc_time_change(Gb.hass, self._polling_loop_5_sec_device,
                        second=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])

            start_ic3_control.stage_3_setup_configured_devices()
            if start_ic3_control.stage_4_setup_tracking_methods() is False:
                start_ic3_control.stage_4_setup_tracking_methods(retry=True)

            start_ic3_control.stage_5_configure_tracked_devices()
            start_ic3_control.stage_6_initialization_complete()
            start_ic3_control.stage_7_initial_locate()

            Gb.trace_prefix = ''
            Gb.initial_locate_complete_flag = False
            Gb.EvLog.display_user_message('', clear_alert=True)
            Gb.initial_icloud3_loading_flag = False
            Gb.start_icloud3_inprocess_flag = False
            Gb.broadcast_info_msg = None

            return True

        except Exception as err:
            log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This function is called every 5 seconds by HA. Cycle through all
#   of the iCloud devices to see if any of the ones being tracked need
#   to be updated. If so, we might as well update the information for
#   all of the devices being tracked since PyiCloud gets data for
#   every device in the account
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _polling_loop_5_sec_device(self, ha_timer_secs):
        Gb.this_update_secs   = time_now_secs()
        Gb.this_update_time   = dt_util.now().strftime('%H:%M:%S')

        if Gb.config_flow_updated_parms != {''}:
            start_ic3.process_conf_flow_parameter_updates()

        # Restart iCloud via service call from EvLog or config_flow
        if Gb.start_icloud3_request_flag:
            self.start_icloud3()
            Gb.start_icloud3_request_flag = False

        # Exit 5-sec loop if no devices, updating a device now, or restarting iCloud3
        if (Gb.master_update_in_process_flag
                or Gb.conf_devices == []
                or Gb.start_icloud3_inprocess_flag):

            # Authentication may take a long time, Display a status message before exiting loop
            if (Gb.pyicloud_auth_started_secs > 0):
                info_msg = ("Waiting for iCloud Account Authentication, Requested at "
                            f"{secs_to_time_age_str(Gb.pyicloud_auth_started_secs)} ")
                for Device in Gb.Devices_by_devicename.values():
                    Device.display_info_msg(info_msg)
                if Gb.this_update_time[-2:] in ['00', '15', '30', '45']:
                    log_info_msg(info_msg)
            return

        # Handle any EvLog > Actions requested by the 'service_handler' module.
        if Gb.evlog_action_request == '':
            pass

        elif Gb.evlog_action_request == CMD_RESET_PYICLOUD_SESSION:
            pyicloud_ic3_interface.pyicloud_reset_session()
            Gb.evlog_action_request = ''


        #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
        #   CHECK TIMERS
        #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
        self._main_5sec_loop_special_time_control()

        if Gb.all_tracking_paused_flag:
            return


        #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
        #   UPDATE TRACKED DEVICES
        #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
        Gb.master_update_in_process_flag = True
        self._main_5sec_loop_icloud_prefetch_control()

        for Device in Gb.Devices_by_devicename_tracked.values():
            if Gb.device_update_in_process_flag:
                break

            self._main_5sec_loop_update_tracked_devices_iosapp(Device)
            self._main_5sec_loop_update_tracked_devices_icloud(Device)

            self._display_secs_to_next_update_info_msg(Device)


        #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
        #   UPDATE MONITORED DEVICES
        #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
        for Device in Gb.Devices_by_devicename_monitored.values():
            if Gb.device_update_in_process_flag:
                break

            if Device.isnot_data_source_NOT_SET:
                self._main_5sec_loop_update_monitored_devices(Device)


        Gb.trace_prefix = ''
        Gb.any_device_was_updated_reason = ''
        Gb.device_update_in_process_flag = False
        Gb.master_update_in_process_flag = False
        Gb.initial_locate_complete_flag  = True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   MAIN 5-SEC LOOP PROCESSING CONTROLLERS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _main_5sec_loop_update_tracked_devices_iosapp(self, Device):
        '''
        Update the device based on iOS App data
        '''
        if (Device.iosapp_monitor_flag is False
                or Device.is_tracking_paused
                or Gb.data_source_use_iosapp is False):
            return


        Gb.trace_prefix = 'IOSAPP > '
        Gb.device_update_in_process_flag = True
        devicename = Device.devicename

        self._main_5sec_loop_update_battery(Device)
        iosapp_data_handler.check_iosapp_state_trigger_change(Device)

        # Turn off monitoring the iOSApp if excessive errors
        if Device.iosapp_data_invalid_error_cnt > 50:
            Device.iosapp_data_invalid_error_cnt = 0
            Device.iosapp_monitor_flag = False
            event_msg =("iCloud3 Error > iOSApp entity error cnt exceeded, "
                        "iOSApp monitoring stopped. iCloud monitoring will be used.")
            post_event(devicename, event_msg)
            return

        # iOSApp has process a non-tracked zone change (enter zone, sig loc update, etc).
        # Delay the zone enter from being processed for 1-min (Gb.passthru_zone_interval_secs)
        # to see if just passing thru a zone. If still in the zone after 1-minute, it
        # will be handled normally.
        if det_interval.is_passthru_zone_delay_active(Device):
            return

        # The iosapp may be entering or exiting another Device's Stat Zone. If so,
        # reset the iosapp information to this Device's Stat Zone and continue.
        if Device.iosapp_data_updated_flag:
            Device.iosapp_data_invalid_error_cnt = 0
            if Device.isnot_set is False:
                Device.moved_since_last_update = \
                        Device.distance_km(Device.iosapp_data_latitude, Device.iosapp_data_longitude)

            event_msg = f"Trigger > {Device.iosapp_data_change_reason}"
            post_event(devicename, event_msg)

            iosapp_data_handler.check_enter_exit_stationary_zone(Device)

            self._validate_new_iosapp_data(Device)
            self.process_updated_location_data(Device, IOSAPP_FNAME)

            Device.update_in_process_flag = False
            Gb.device_update_in_process_flag = False

        Gb.device_update_in_process_flag = False

        # Send a location request to device if needed
        iosapp_data_handler.check_if_iosapp_is_alive(Device)

        # Refresh the EvLog if this is an initial locate
        if Gb.initial_locate_complete_flag == False:
            if devicename == Gb.Devices[0].devicename:
                Gb.EvLog.update_event_log_display(devicename)

#----------------------------------------------------------------------------
    def _main_5sec_loop_update_tracked_devices_icloud(self, Device):
        '''
        Update the device based on iCloud data
        '''

        if Gb.PyiCloud is None:
            return

        Gb.trace_prefix = 'ICLOUD > '
        if (icloud_data_handler.any_reason_to_update_ic3_device_and_sensors(Device) is False
                or Device.is_tracking_paused):
            return

        Gb.device_update_in_process_flag = True
        devicename = Device.devicename

        Device.calculate_old_location_threshold()
        if icloud_data_handler.should_ic3_device_and_sensors_be_updated(Device) is False:
            return

        # Update device info. Get data from FmF or FamShr
        icloud_data_handler.request_icloud_data_update(Device)

        # Do not redisplay update reason if in error retries. It has already been displayed.
        if (Device.icloud_devdata_useable_flag
                or Device.icloud_update_reason == 'Stationary Timer Reached'):
            Device.display_info_msg(Device.icloud_update_reason)

            event_msg = f"Trigger > {Device.icloud_update_reason}"
            post_event(devicename, event_msg)

        if icloud_data_handler.update_device_with_latest_raw_data(Device) is False:
            Device.icloud_acct_error_flag = True

        # iOSApp has processed a non-tracked zone change (enterzone, sig loc
        # update, etc).  Delay the zone enter from being processed for 1-min
        # (Gb.passthru_zone_interval_secs) to see if just passing thru a zone.
        # If still in the zone after 1-minute, it will be handled normally.
        if det_interval.is_passthru_zone_delay_active(Device):
            return

        if Device.icloud_acct_error_flag:
            self._display_icloud_acct_error_msg(Device)
            Device.icloud_acct_error_flag = False
            return

        Gb.icloud_acct_error_cnt = 0

        self._validate_new_icloud_data(Device)
        self._post_before_update_monitor_msg(Device)
        self.process_updated_location_data(Device, ICLOUD_FNAME)

        Device.tracking_status             = TRACKING_NORMAL
        Device.icloud_initial_locate_done  = True
        Device.update_in_process_flag      = False
        Gb.device_update_in_process_flag = False

        # Refresh the EvLog if this is an initial locate
        if Gb.initial_locate_complete_flag == False:
            if devicename == Gb.Devices[0].devicename:
                Gb.EvLog.update_event_log_display(devicename)

#---------------------------------------------------------------------
    def _main_5sec_loop_update_monitored_devices(self, Device):
        '''
        Update the monitored device with new location and battery info
        '''

        Gb.trace_prefix = 'MONITOR > '
        if (Device.iosapp_data_secs > Device.last_update_loc_secs
                or Device.loc_data_secs > Device.last_update_loc_secs
                or Device.last_update_loc_secs == 0):
            Gb.device_update_in_process_flag = True
            self._update_monitored_devices(Device)

            #restore_state.write_storage_icloud3_restore_state_file()
            Device.update_in_process_flag  = False
            Gb.device_update_in_process_flag = False

        self._main_5sec_loop_update_battery(Device)

#---------------------------------------------------------------------
    def _main_5sec_loop_update_battery(self, Device):
        '''
        Update the Device's battery info
        '''
        try:
            if Gb.this_update_time[-5:] not in ['00:00', '15:00', '30:00', '45:00']:
                return

            if Device.update_battery_information():
                event_msg = (f"Battery Status > "
                            f"Level-{Device.dev_data_battery_level_last}%{RARROW}{Device.dev_data_battery_level}%, "
                            f"{Device.dev_data_battery_status} "
                            f"({Device.dev_data_battery_source})")
                post_event(Device.devicename, event_msg)
                log_debug_msg(Device.devicename, event_msg)

        except Exception as err:
            log_exception(err)


#----------------------------------------------------------------------------
    def _main_5sec_loop_icloud_prefetch_control(self):
        '''
        Update the iCloud location data if it the next_update_time will be reached
        in the next 10-seconds
        '''
        if Gb.PyiCloud is None:
            return

        if Device := self._get_icloud_data_prefetch_device():
            Gb.trace_prefix = 'PREFETCH > '
            log_start_finish_update_banner('start', Device.devicename, 'icloud prefetch', '')
            post_monitor_msg(Device.devicename, "iCloud Location Requested (prefetch)")

            Device.icloud_devdata_useable_flag = \
                icloud_data_handler.update_PyiCloud_RawData_data(Device,
                        results_msg_flag=Device.is_location_old_or_gps_poor)

            log_start_finish_update_banner('finish', Device.devicename, 'icloud prefetch', '')
            Gb.trace_prefix = ''

#----------------------------------------------------------------------------
    def _main_5sec_loop_special_time_control(self):
        '''
        Various functions that are run based on the time-of-day
        '''

        # Every hour
        if Gb.this_update_time.endswith(':00:00'):
            self._timer_tasks_every_hour()

        # At midnight
        if Gb.this_update_time == '00:00:00':
            self._timer_tasks_midnight()

        # At 1am
        elif Gb.this_update_time == '01:00:00':
            calculate_time_zone_offset()

        if (Gb.this_update_secs >= Gb.EvLog.clear_secs):
                # and Gb.log_debug_flag is False):
            #_trace uncomment the above line after testing
            #db
            Gb.EvLog.update_event_log_display('clear_log_items')

        # Every minute
        if Gb.this_update_time.endswith(':00'):
            for Device in Gb.Devices_by_devicename.values():
                Device.display_info_msg(Device.format_info_msg)

        # Every 1/2-hour
        if (Gb.this_update_time.endswith('00:00')
                or Gb.this_update_time.endswith('30:00')):
            for devicename, Device in Gb.Devices_by_devicename.items():
                if Device.dist_apart_msg:
                    event_msg = f"Nearby Devices (<{NEAR_DEVICE_DISTANCE}m) > {Device.dist_apart_msg}"
                    post_event(devicename, event_msg)

        if (Gb.PyiCloud is not None
                and Gb.this_update_secs >= Gb.authentication_error_retry_secs):
            post_event(f"Retry authentication > "
                        f"Timer={secs_to_time(Gb.authentication_error_retry_secs)}")
            pyicloud_ic3_interface.authenticate_icloud_account()

        service_handler.issue_ha_notification()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE THE DEVICE IF A STATE OR TRIGGER CHANGE WAS RECIEVED FROM THE IOSAPP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _validate_new_iosapp_data(self, Device):
        """
        Update the devices location using data from the iOS App
        """
        if Gb.start_icloud3_inprocess_flag:
            return ''
        elif Device.iosapp_monitor_flag is False:
            return ''

        update_reason = Device.iosapp_data_change_reason
        devicename    = Device.devicename

        Device.update_sensors_flag           = False
        Device.iosapp_request_loc_first_secs = 0
        Device.iosapp_request_loc_last_secs  = 0

        Device.DeviceFmZoneCurrent = Device.DeviceFmZoneHome
        if Device.next_update_DeviceFmZone is None:
            Device.next_update_DeviceFmZone = Device.DeviceFmZoneHome

        if (Device.is_tracking_paused
                or Device.iosapp_data_latitude == 0
                or Device.iosapp_data_longitude == 0):
            return

        if Gb.any_device_was_updated_reason == '':
            Gb.any_device_was_updated_reason = f'{Device.iosapp_data_change_reason}, {Device.fname_devtype}'
        return_code = IOSAPP_UPDATE

        # Check to see if the location is outside the zone without an exit trigger
        for from_zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
            if is_inzone_zone(from_zone):
                info_msg = self._is_outside_zone_no_exit( Device, from_zone, '',
                                        Device.iosapp_data_latitude,
                                        Device.iosapp_data_longitude)

                if Device.outside_no_exit_trigger_flag:
                    post_event(devicename, info_msg)

                    # Set located time to trigger time so it won't fire as trigger change again
                    Device.loc_data_secs = Device.iosapp_data_secs + 10
                    return

        try:
            log_start_finish_update_banner('start', devicename, IOSAPP_FNAME, update_reason)
            Device.update_sensors_flag = True

            # Request the iosapp location if iosapp location is old and the next update
            # time is reached and less than 1km from the zone
            if (Device.is_iosapp_data_old
                    and Device.next_update_time_reached
                    and Device.next_update_DeviceFmZone.zone_dist < 1
                    and Device.next_update_DeviceFmZone.dir_of_travel == TOWARDS
                    and Device.isnot_inzone):

                iosapp_interface.request_location(Device)

                Device.update_sensors_flag = False

            if Device.update_sensors_flag:
                Device.update_dev_loc_data_from_raw_data_IOSAPP()

        except Exception as err:
            post_internal_error('iOSApp Update', traceback.format_exc)
            return_code = ICLOUD_UPDATE

        return

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Cycle through all iCloud devices and update the information for the devices
#   being tracked
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _validate_new_icloud_data(self, Device):

        """
        Request device information from iCloud (if needed) and update
        device_tracker information.

        _Device -
                None     =  Update all devices
                Not None =  Update specified device
        arg_other-devicename -
                None     =  Update all devices
                Not None =  One device in the list reached the next update time.
                            Do not update another device that now has poor location
                            gps after all the results have been determined if
                            their update time has not been reached.

        """

        update_reason = Device.icloud_update_reason
        devicename    = Device.devicename
        zone          = Device.loc_data_zone

        if Gb.any_device_was_updated_reason == '':
            Gb.any_device_was_updated_reason = f'{Device.icloud_update_reason}, {Device.fname_devtype}'

        Device.update_timer                 = time_now_secs()
        Device.icloud_update_retry_flag     = False
        Device.iosapp_request_loc_last_secs = 0

        Device.DeviceFmZoneCurrent = Device.DeviceFmZoneHome
        if Device.next_update_DeviceFmZone is None:
            Device.next_update_DeviceFmZone = Device.DeviceFmZoneHome

        log_start_finish_update_banner('start', devicename, ICLOUD_FNAME, update_reason)

        try:
            Device.update_sensors_flag = True
            Device.calculate_old_location_threshold()

            #icloud data overrules device data which may be stale
            latitude     = Device.loc_data_latitude
            longitude    = Device.loc_data_longitude

            if latitude != 0 and longitude != 0:
                self._check_old_loc_poor_gps(Device)

            #Discard if no location coordinates
            if latitude == 0 or longitude == 0:
                Device.update_sensors_flag = False

            # Update the device if it is monitored
            elif Device.is_monitored:
                pass

            # Check to see if currently in a zone. If so, check the zone distance.
            # If new location is outside of the zone and inside radius*4, discard
            # by treating it as poor GPS
            elif (isnot_inzone_zone(zone)
                    or Device.sensor_zone == NOT_SET):
                Device.outside_no_exit_trigger_flag = False
                Device.update_sensors_error_msg= ''

            else:
                Device.update_sensors_error_msg = \
                            self._is_outside_zone_no_exit(Device, zone, '', latitude, longitude)

            if Device.is_offline or Device.is_pending:
                offline_msg = ( f"{Device.fname_devtype} not Online > "
                                f"DeviceStatus-{Device.device_status_msg}")
                if instr(Device.update_sensors_error_msg, 'Offline') is False:
                    log_info_msg(Device.devicename, offline_msg)
                    post_event(Device.devicename, offline_msg)
                Device.update_sensors_flag = False
                Device.update_sensors_error_msg = offline_msg

            # 'Verify Location' update reason overrides all other checks and forces an iCloud update
            elif Device.icloud_update_reason == 'Verify Location':
                pass

            # Ignore old location when in a zone and discard=False
            # let normal next time update check process
            elif (Device.is_gps_poor
                    and Gb.discard_poor_gps_inzone_flag
                    and Device.is_inzone
                    and Device.outside_no_exit_trigger_flag is False):
                Device.old_loc_poor_gps_cnt -= 1
                Device.old_loc_poor_gps_msg = ''

                if Device.next_update_time_reached is False:
                    Device.update_sensors_flag = False

            # Outside zone, no exit trigger check. This is valid for location less than 2-minutes old
            # added 2-min check so it wouldn't hang with old iosapp data. Force a location update
            elif (Device.outside_no_exit_trigger_flag
                    and secs_since(Device.iosapp_data_secs) < 120):
                pass

            # Discard if location is old and next update time has been reached
            # Will check for old loc after other checks (was)
            if (Device.is_location_old_or_gps_poor
                    and Device.is_tracked
                    and Device.is_offline is False
                    and Device.next_update_time_reached):
                Device.update_sensors_error_msg = (f"{Device.old_loc_poor_gps_msg}")
                Device.update_sensors_flag = False

        except Exception as err:
            post_internal_error('iCloud Update', traceback.format_exc)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Determine the update interval, Update the sensors and device_tracker entity
#
#   1. Cycle through each trackFromZone zone for the Device and determint the interval,
#   next_update_time, distance from the zones, etc. Then update all of the TrackFromZone
#   sensors for the Device (this is normally just the Home zone).
#   2. Update the sensors for the device.
#   3. Update the device_tracker entity for the device.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def process_updated_location_data(self, Device, update_requested_by):
        try:
            devicename = Gb.devicename = Device.devicename

            # See if the Stat Zone timer has expired or if the Device has moved a lot. Do this
            # even if the sensors are not updated to make sure the Stat Zone is set up and be
            # seleted for the Device
            self._check_statzone_timer_expired(Device)

            # Location is good. Determine next update time and update interval,
            # next_update_time values and sensors with the good data
            if Device.update_sensors_flag:
                update_reason = Device.iosapp_data_change_reason \
                                    if update_requested_by == IOSAPP_FNAME \
                                    else Device.icloud_update_reason

                if Gb.PyiCloud:
                    icloud_data_handler.update_device_with_latest_raw_data(Device)
                else:
                    Device.update_dev_loc_data_from_raw_data_IOSAPP()

                if Device.is_location_data_rejected():
                    if Device.is_data_source_FAMSHR_FMF:
                        det_interval.determine_interval_after_error(Device, counter=OLD_LOC_POOR_GPS_CNT)

                else:
                    event_msg =(f"{EVLOG_UPDATE_START}{update_requested_by} update started > "
                                f"{update_reason.split(' (')[0]}")
                    post_event(devicename, event_msg)

                    self._post_before_update_monitor_msg(Device)
                    if self._calculate_interval_and_next_update(Device):
                        Device.update_sensor_values_from_data_fields()

                    event_msg =(f"{EVLOG_UPDATE_END}{update_requested_by} update completed > "
                                f"Date source - {Device.dev_data_source}")
                    post_event(devicename, event_msg)

                #self._update_restore_state_values(Device)
                Device.write_ha_sensors_state()
                Device.write_ha_device_from_zone_sensors_state()
                Device.write_ha_device_tracker_state()
                #restore_state.write_storage_icloud3_restore_state_file()
                #self._update_restore_state_values(Device)

                self._post_after_update_monitor_msg(Device)

                if Gb.PyiCloud is None:
                    pass
                elif (update_requested_by == ICLOUD_FNAME and Gb.PyiCloud.requires_2fa):
                    alert_msg = f"{EVLOG_ALERT}Alert > iCloud account authentication is needed"
                    post_event(devicename, alert_msg)
                    Gb.EvLog.clear_alert_events()
                    Gb.EvLog.display_user_message('iCloud Account authentication is needed')
                elif (Gb.PyiCloud.requires_2fa is False
                        and update_requested_by == ICLOUD_FNAME
                        and Gb.EvLog.user_message == 'iCloud Account authentication is needed'):
                    Gb.EvLog.display_user_message('', clear_alert=True)

            else:
                # Old location, poor gps etc. Determine the next update time to request new location info
                # with good data (hopefully). Update interval, next_update_time values and sensors with the time
                det_interval.determine_interval_after_error(Device, counter=OLD_LOC_POOR_GPS_CNT)

                #self._update_restore_state_values(Device)
                Device.write_ha_sensors_state()
                Device.write_ha_device_from_zone_sensors_state()
                Device.write_ha_device_tracker_state()
                #restore_state.write_storage_icloud3_restore_state_file()

            # Refresh the EvLog if this is an initial locate
            if (Gb.initial_locate_complete_flag == False
                    and devicename == Gb.Devices[0].devicename):
                Gb.EvLog.update_event_log_display(devicename)

            log_start_finish_update_banner('finish',  devicename,
                                    f"{Device.tracking_method_fname}/{Device.dev_data_source}",
                                    "gen update")

        except Exception as err:
            log_exception(err)
            post_internal_error('iCloud Update', traceback.format_exc)
            Device.update_in_process_flag = False

#----------------------------------------------------------------------------
    def _calculate_interval_and_next_update(self, Device):
        '''
        Determine the update interval, Update the sensors and device_tracker entity:
            1. Cycle through each trackFromZone zone for the Device and determint the interval,
            next_update_time, distance from the zones, etc. Then update all of the TrackFromZone
            sensors for the Device (this is normally just the Home zone).
            2. Update the sensors for the device.
            3. Update the device_tracker entity for the device.
        '''
        devicename = Device.devicename

        if Device.update_in_process_flag:
            info_msg  = "Retrying > Last update not completed"
            event_msg = info_msg
            post_event(devicename, event_msg)
        Device.update_in_process_flag = True

        try:
            if Device.is_data_source_IOSAPP:
                Device.trigger = (f"{Device.iosapp_data_trigger}@{Device.iosapp_data_time}")
            else:
                Device.trigger = (f"{Device.dev_data_source}@{Device.loc_data_datetime[11:19]}")

            self._get_zone(Device, display_zone_msg=True)

            if (Device.passthru_zone_expire_secs > 0
                    and Device.loc_data_secs < \
                            Device.passthru_zone_expire_secs - Gb.passthru_zone_interval_secs):
                return False

        except Exception as err:
            post_internal_error('Update Stat Zone', traceback.format_exc)

        try:
            # Update the devices that are near each other
            # See if a device updated updated earlier in this 5-sec loop was just updated and is
            # near the device being updated now
            self._identify_nearby_devices(Device)

            # Cycle thru each Track From Zone get the interval and all other data
            devicename = Device.devicename

            for from_zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
                log_start_finish_update_banner('start', devicename, Device.dev_data_source, from_zone)

                det_interval.determine_interval(Device, DeviceFmZone)

            self._set_tracked_devicefmzone_to_dislpay(Device)

            log_start_finish_update_banner('finish', devicename, Device.dev_data_source, from_zone)

        except Exception as err:
            log_exception(err)
            post_internal_error('Det IntervalLoop', traceback.format_exc)

        return True

#----------------------------------------------------------------------------
    def _set_tracked_devicefmzone_to_dislpay(self, Device):
        '''
        The DeviceFmZone tracking sensors have the results i.e., zone distance, interval, next update time
        and direction calculations, etc. The TrackFmZone sensor data that is closest to the Device's
        location are copied to the Device sensors if the Device is < 100km from home and 8km of the TrackFmZone
        or > 100km from Home
        '''
        Device.DeviceFmZoneTracked = Device.TrackFromBaseZone       #Device.DeviceFmZoneHome
        if len(Device.DeviceFmZones_by_zone) == 1:
            return

        # track_fm_zone_radius is the distance from the trackFm zone before it's results are displayed
        # track_fm_zone_home_radius is the max home zone distance before the closest trackFm results are dsplayed

        # TrackFromBaseZone
        for from_zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
            if DeviceFmZone.next_update_secs <= Device.DeviceFmZoneTracked.next_update_secs:
                # If within tfz tracking dist, display this tfz results
                # Then see if another trackFmZone is closer to the device
                if (DeviceFmZone.zone_dist <= Gb.tfz_tracking_max_distance
                        and DeviceFmZone.zone_dist < Device.DeviceFmZoneTracked.zone_dist):
                    Device.DeviceFmZoneTracked = DeviceFmZone

##<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Determine the update interval, Update the sensors and device_tracker entity
#
#   1. Cycle through each trackFromZone zone for the Device and determint the interval,
#   next_update_time, distance from the zones, etc. Then update all of the TrackFromZone
#   sensors for the Device (this is normally just the Home zone).
#   2. Update the sensors for the device.
#   3. Update the device_tracker entity for the device.
#
##<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _update_monitored_devices(self, Device):

        Device.icloud_update_reason = 'Monitored Device Update'    #Gb.any_device_was_updated_reason

        event_msg =(f"Trigger > {Gb.any_device_was_updated_reason}")
        post_event(Device.devicename, event_msg)

        Device.DeviceFmZoneTracked = Device.DeviceFmZoneHome
        Device.update_sensors_flag = True

        self.process_updated_location_data(Device, ICLOUD_FNAME)

        Device.update_sensor_values_from_data_fields()


#------------------------------------------------------------------------------
#
#   DETERMINE THE ZONE THE DEVICE IS CURRENTLY IN
#
#------------------------------------------------------------------------------
    def _get_zone(self, Device, display_zone_msg=True):

        '''
        Get current zone of the device based on the location

        Returns:
            zone    zone name or not_home if not in a zone
            Zone    Zone object

        NOTE: This is the same code as (active_zone/async_active_zone) in zone.py
        but inserted here to use zone table loaded at startup rather than
        calling hass on all polls
        '''

        zone_selected_dist_m = HIGH_INTEGER
        ZoneSelected         = None
        zone_selected        = None
        zones_distance_list  = []

        # iOSApp will trigger Enter Region when the edge of the devices's location area (100m)
        # touches or is inside the zones radius. If enterina a zone, increase the zone's radius
        # so the device will be in the zone when it is actually just outside of it.
        # But don't do this for a Stationary Zone.

        # if Close to zone, add 50m for iOS App Extra area
        zone_radius_iosapp_enter_adjustment_m = 0
        if (Device.is_data_source_IOSAPP
                and instr(Device.trigger.lower(), 'exit') is False):
            zone_radius_iosapp_enter_adjustment_m = 50

        for Zone in Gb.Zones:
            zone          = Zone.zone
            zone_radius_m = Zone.radius_m
            zone_dist_m   = Zone.distance_m(Device.loc_data_latitude, Device.loc_data_longitude)

            if (.100 < zone_dist_m <= .150
                    and zone_radius_iosapp_enter_adjustment_m > 0):
                zone_radius_m += zone_radius_iosapp_enter_adjustment_m

            #Skip another device's stationary zone or if at base location
            if (is_statzone(zone) and instr(zone, Device.devicename) is False):
                continue

            #Bypass stationary zone at base and Pseudo Zones (not_home, not_set, etc)
            elif zone_radius_m <= 1:
                continue

            #Do not check Stat Zone if radius=1 (at base loc) but include in log_msg
            in_zone_flag      = zone_dist_m <= zone_radius_m
            closer_zone_flag  = zone_selected is None or zone_dist_m < zone_selected_dist_m
            smaller_zone_flag = zone_dist_m == zone_selected_dist_m and zone_radius_m <= zone_selected_radius_m
            if in_zone_flag and (closer_zone_flag or smaller_zone_flag):
                ZoneSelected         = Zone
                zone_selected        = zone
                zone_selected_dist_m = zone_dist_m
                zone_selected_radius_m = ZoneSelected.radius_m + zone_radius_iosapp_enter_adjustment_m

            ThisZone = Device.StatZone if is_statzone(zone) else Zone
            zones_distance_list.append(f"{int(zone_dist_m):08}| {ThisZone.display_as}-{format_dist_m(zone_dist_m)}")

        if ZoneSelected is None:
            ZoneSelected         = Gb.Zones_by_zone[NOT_HOME]
            zone_selected        = NOT_HOME
            zone_selected_dist_m = 0

        # In a zone but if not in a track from zone and was in a Stationary Zone,
        # reset the stationary zone
        # elif Device.StatZone.inzone is False and Device.StatZone.radius_m > 1:
        elif is_statzone(zone_selected) is False and Device.StatZone.is_at_base is False:
            Device.stationary_zone_update_control = STAT_ZONE_MOVE_TO_BASE

        if ZoneSelected and is_statzone(zone_selected) is False:
            zones_distance_msg = ''
        else:
            zones_distance_list.sort()
            zones_distance_list = ', '.join([v.split('|')[1] for v in zones_distance_list])
            zones_distance_msg  = (f" > {zones_distance_list}")

        if display_zone_msg:
            distance_msg = f"-{format_dist_m(zone_selected_dist_m)}/r{ZoneSelected.radius_m:.0f}m" \
                                if ZoneSelected.radius_m > 0 else ''
            zones_msg = (f"Zone > "
                        f"{ZoneSelected.display_as}"
                        f"{distance_msg}"
                        f"{zones_distance_msg}, "
                        f"GPS-{Device.loc_data_fgps}")
            post_event(Device.devicename, zones_msg)

        # Get distance between zone selected and current zone to see if they overlap.
        # If so, keep the current zone
        if (zone_selected != NOT_HOME
                and self._is_overlapping_zone(Device.loc_data_zone, zone_selected)):
            zone_selected = Device.loc_data_zone
            ZoneSelected  = Gb.Zones_by_zone[Device.loc_data_zone]

        # Going from Away-->inZone, set passthru delay if not going to tracked zone
        if (Device.loc_data_zone == NOT_HOME
                and is_statzone(zone_selected) is False
                and zone_selected != NOT_HOME
                and zone_selected != HOME
                and zone_selected not in Device.DeviceFmZones_by_zone
                and Device.passthru_zone_expire_secs == 0
                and Gb.passthru_zone_interval_secs > 0):
            Device.passthru_zone = zone_selected
            zone_selected = Device.loc_data_zone
            ZoneSelected  = Gb.Zones_by_zone[zone_selected]

            det_interval.set_passthru_zone_delay(Device)

        elif Device.passthru_zone_expire_secs > 0:
            zone_selected = Device.loc_data_zone
            ZoneSelected  = Gb.Zones_by_zone[zone_selected]

        # The zone changed
        elif Device.loc_data_zone != zone_selected:
            Device.loc_data_zone        = zone_selected
            Device.zone_change_datetime = datetime_now()
            Device.zone_change_secs     = time_now_secs()

        return (zone_selected, ZoneSelected)

#--------------------------------------------------------------------
    def _check_statzone_timer_expired(self, Device):
        '''
        Check the Device's Stationary Zone expired timer and distance moved:
            Udate the Device's Stat Zone distance moved
            Reset the timer if the Device has moved further than the distance limit
            Move Device into the Stat Zone if it has not moved further than the limit
        '''
        calc_dist_last_poll_moved_km = calc_distance_km(Device.sensors[GPS], Device.loc_data_gps)
        Device.StatZone.update_distance_moved(calc_dist_last_poll_moved_km)

        # See if moved less than the stationary zone movement limit
        # If updating via the ios app and the current state is stationary,
        # make sure it is kept in the stationary zone
        if Device.StatZone.timer_expired:
            if Device.StatZone.move_limit_exceeded:
                Device.StatZone.reset_timer_time

            # elif (Device.StatZone.not_inzone
            elif (Device.isnot_inzone_stationary
                    or (is_statzone(Device.iosapp_data_state)
                        and Device.loc_data_zone == NOT_SET)):
                Device.stationary_zone_update_control = STAT_ZONE_MOVE_DEVICE_INTO
                Device.StatZone.update_stationary_zone_location()

#--------------------------------------------------------------------
    def _is_overlapping_zone(self, current_zone, new_zone):
        '''
        Check to see if two zones overlap each other. The current_zone and
        new_zone overlap if their distance between centers is less than 2m.

        Return:
            True    They overlap
            False   They do not oerlap, ic3 is starting
        '''
        try:
            if current_zone == NOT_SET:
                return False
            elif current_zone == new_zone:
                return True

            if current_zone == "": current_zone = HOME
            CurrentZone = Gb.Zones_by_zone[current_zone]
            NewZone     = Gb.Zones_by_zone[new_zone]

            zone_dist = CurrentZone.distance_m(NewZone.latitude, NewZone.longitude)

            return (zone_dist <= 2)

        except:
            return False

#----------------------------------------------------------------------------
    def _identify_nearby_devices(self, Device):
        '''
        Cycle through the devices and see if this device is in the same location as
        another device updated earlier in this 5-sec polling loop.

        Return: The closest device
        '''
        try:
            if len(Gb.Devices) == 1:
                return

            closest_device_distance     = HIGH_INTEGER
            Device.dist_apart_msg  = ''
            Device.NearDevice           = None
            Device.near_device_distance = 0

            for _Device in Gb.Devices:
                can_use_nearby_device = False
                nearby_symbol = ''

                # If the device being updated has been reached and the data is iCloud, a nearby device
                # cannot be used and must be calculated. Otherwise, there is a circular reference and
                # this device will be set to another device's previous results
                if _Device is Device:
                    can_use_nearby_device = _Device.is_using_iosapp_data
                    continue

                distance_apart       = _Device.distance_m(Device.loc_data_latitude, Device.loc_data_longitude)
                gps_accuracy_factor  = min(Device.loc_data_gps_accuracy, _Device.loc_data_gps_accuracy) * distance_apart / NEAR_DEVICE_DISTANCE
                location_age_ok_flag = (secs_since(_Device.loc_data_secs) < _Device.old_loc_threshold_secs)
                if Device.sensor_zone == _Device.sensor_zone and Device.is_inzone:
                    location_age_ok_flag = True

                # if (distance_apart > NEAR_DEVICE_DISTANCE - gps_accuracy_adjustment
                if (distance_apart > NEAR_DEVICE_DISTANCE
                        or gps_accuracy_factor > NEAR_DEVICE_DISTANCE
                        # or min(Device.loc_data_gps_accuracy, _Device.loc_data_gps_accuracy) > NEAR_DEVICE_DISTANCE
                        or Device.is_inzone_stationary
                        or _Device.is_inzone_stationary):
                    nearby_symbol = '⊗'

                # dist_apart_msg = (f"{format_dist_m(distance_apart)}±{format_dist_m(gps_accuracy_adjustment)}"
                dist_apart_msg = (f"{format_dist_m(distance_apart)}/±"
                                    f"{min(Device.loc_data_gps_accuracy, _Device.loc_data_gps_accuracy)}m")

                # Update the other Device with this Device's distance
                if location_age_ok_flag:
                    Device.dist_apart_msg_by_devicename[_Device.devicename] = dist_apart_msg
                    _Device.dist_apart_msg_by_devicename[Device.devicename] = dist_apart_msg

                Device.dist_apart_msg += f"{nearby_symbol}{_Device.fname_devtype}-{dist_apart_msg}, "

                # The nearby devices can not point to each other and other criteria
                if (_Device.NearDevice is not Device
                        and ((Device.is_tracked and _Device.is_tracked) or Device.is_monitored)
                        and location_age_ok_flag
                        and nearby_symbol == ''
                        and _Device.DeviceFmZoneHome.interval_secs > 0
                        and _Device.old_loc_poor_gps_cnt == 0
                        and _Device.is_online):
                    can_use_nearby_device = True

                if can_use_nearby_device and distance_apart < closest_device_distance:
                    closest_device_distance = distance_apart
                    Device.NearDevice = _Device
                    Device.near_device_distance = distance_apart

            monitor_msg = f"Nearby Devices (<{NEAR_DEVICE_DISTANCE}m) > {Device.dist_apart_msg}"
            post_monitor_msg(Device.devicename, monitor_msg)

            return

        except Exception as err:
            post_internal_error('Get nearby device', traceback.format_exc)

#--------------------------------------------------------------------
    def _get_icloud_data_prefetch_device(self):
        '''
        Get the time (secs) until the next update for any device. This is used to determine
        when icloud data should be prefetched before it is needed.

        Return:
            Device that will be updated in 5-secs
        '''
        # At least 10-secs between prefetch refreshes
        if (secs_since(Gb.pyicloud_refresh_time[FAMSHR]) < 10
                and secs_since(Gb.pyicloud_refresh_time[FMF]) < 10):
            return None

        prefetch_before_update_secs = 5
        for Device in Gb.Devices_by_devicename_tracked.values():
            if Device.icloud_initial_locate_done is False:
                return Device

            if (Device.is_tracking_method_IOSAPP
                    or Device.is_tracking_paused
                    or Device.is_offline
                    or Device.NearDevice):
                continue

            secs_to_next_update = secs_to(Device.next_update_secs)

            if Device.inzone_interval_secs < -15 or Device.inzone_interval_secs > 15:
                continue

            # If going towards a TrackFmZone and the next update is in 15-secs or less and distance < 1km
            # and current location is older than 15-secs, prefetch data now
            if (Device.DeviceFmZoneTracked.is_going_towards
                    and Device.DeviceFmZoneTracked.zone_dist < 1
                    and secs_since(Device.loc_data_secs > 15)):
                Device.old_loc_threshold_secs = 15
                return Device

            if Device.is_location_gps_good:
                continue

            # Updating the device in the next 10-secs
            Device.display_info_msg(f"Requesting iCloud Location, Next Update in {secs_to_time_str(secs_to_next_update)} secs")
            return Device

        return None

#--------------------------------------------------------------------
    def _display_icloud_acct_error_msg(self, Device):
        '''
        An error ocurred accessing the iCloud account. This can be a
        Authentication error or an error retrieving the loction data. Update the error
        count and turn iCloud tracking off when the error count is exceeded.
        '''
        Gb.icloud_acct_error_cnt += 1

        if Device.icloud_initial_locate_done is False:
            Device.update_sensors_error_msg = "Retrying Initial Locate"
        else:
            Device.update_sensors_error_msg = "iCloud Authentication or Location Error (may be Offline)"

        det_interval.determine_interval_after_error(Device, counter=AUTH_ERROR_CNT)

        if Gb.icloud_acct_error_cnt > 20:
            start_ic3.set_tracking_method(IOSAPP)
            Device.tracking_method = IOSAPP
            log_msg = ("iCloud3 Error > More than 20 iCloud Authentication "
                        "or Location errors. iCloud may be down. "
                        "The iOSApp tracking_method will be used. "
                        "Restart iCloud3 at a later time to see if iCloud "
                        "Loction Services is available.")
            post_error_msg(log_msg)

#--------------------------------------------------------------------
    def _format_fname_devtype(self, Device):
        try:
            return f"{Device.fname_devtype}"
        except:
            return ''

#--------------------------------------------------------------------
    def _is_overlapping_zone(self, zone1, zone2):
        '''
        zone1 and zone2 overlap if their distance between centers is less than 2m
        '''
        try:
            if zone1 == zone2:
                return True

            if zone1 == "": zone1 = HOME
            Zone1 = Gb.Zones_by_zone[zone1]
            Zone2 = Gb.Zones_by_zone[zone2]

            zone_dist = Zone1.distance(Zone2.latitude, Zone2.longitude)

            return (zone_dist <= 2)

        except:
            return False

#--------------------------------------------------------------------
    @staticmethod
    def _format_zone_name(devicename, zone):
        '''
        The Stationary zone info is kept by 'devicename_stationary'. Other zones
        are kept as 'zone'. Format the name based on the zone.
        '''
        return f"{devicename}_stationary" if zone == STATIONARY else zone

#--------------------------------------------------------------------
    def _wait_if_update_in_process(self, Device=None):
        # An update is in process, must wait until done

        wait_cnt = 0
        while Gb.master_update_in_process_flag:
            wait_cnt += 1
            if Device:
                Device.write_ha_sensor_state(INTERVAL, (f"WAIT-{wait_cnt}"))

            time.sleep(2)

#--------------------------------------------------------------------
    def _post_before_update_monitor_msg(self, Device):
        """ Post a monitor msg for all other devices with this device's update reason """
        return

#--------------------------------------------------------------------
    def _post_after_update_monitor_msg(self, Device):
        """ Post a monitor event after the update with the result """
        device_monitor_msg = (f"Device Monitor > {Device.tracking_method}, "
                            f"{Device.icloud_update_reason}, "
                            f"AttrsZone-{Device.sensor_zone}, "
                            f"LocDataZone-{Device.loc_data_zone}, "
                            f"Located-%tage, "
                            f"iOSAppGPS-{Device.iosapp_data_fgps}, "
                            f"iOSAppState-{Device.iosapp_data_state}), "
                            f"GPS-{Device.loc_data_fgps}")

        if Device.last_device_monitor_msg != device_monitor_msg:
            Device.last_device_monitor_msg = device_monitor_msg
            device_monitor_msg = device_monitor_msg.\
                        replace('%tage', Device.loc_data_time_age)
            post_monitor_msg(Device.devicename, device_monitor_msg)


#--------------------------------------------------------------------
    def _display_usage_counts(self, Device, force_display=False):
        try:
            total_count =   Device.count_update_icloud + \
                            Device.count_update_iosapp + \
                            Device.count_discarded_update + \
                            Device.count_state_changed + \
                            Device.count_trigger_changed + \
                            Device.iosapp_request_loc_cnt

            pyi_avg_time_per_call = 0
            if Gb.pyicloud_location_update_cnt > 0:
                pyi_avg_time_per_call = Gb.pyicloud_calls_time / \
                    (Gb.pyicloud_authentication_cnt + Gb.pyicloud_location_update_cnt)

            # Verify average and counts, reset counts if average time > 1 min
            if pyi_avg_time_per_call > 60:
                pyi_avg_time_per_call           = 0
                Gb.pyicloud_calls_time          = 0
                Gb.pyicloud_authentication_cnt  = 0
                Gb.pyicloud_location_update_cnt = 0

            # If updating the devicename's info_msg, only add to the event log
            # and info_msg if the counter total is divisible by 5.
            hour = int(dt_util.now().strftime('%H'))
            if force_display:
                pass
            elif (hour % 3) != 0:
                return
            elif total_count == 0:
                return

            #    ¤s=<table>                         Table start, Row start
            #    ¤e=</table>                        Row end, Table end
            #    §=</tr><tr>                        Row end, next row start
            #    »   =</td></tr>
            #    «LT- =<tr><td style='width: 28%'>    Col start, 40% width
            #    ¦LC-=</td><td style='width: 8%'>   Col end, next col start-width 40%
            #    ¦RT-=</td><td style='width: 28%'>   Col end, next col start-width 10%
            #    ¦RC-=</td><td style='width: 8%'>   Col end, next col start-width 40%

            count_msg =  (f"¤s")
            state_trig_count = Device.count_state_changed + Device.count_trigger_changed

            if Device.is_tracking_method_FAMSHR_FMF:
                count_msg +=(f"«HS¦LH-Device Counts¦RH-iCloud Counts»HE"
                            f"«LT-State/Trigger Chgs¦LC-{state_trig_count}¦"
                            f"RT-Authentications¦RC-{Gb.pyicloud_authentication_cnt}»"
                            f"«LT-iCloud Updates¦LC-{Device.count_update_icloud}¦"
                            f"RT-Total iCloud Loc Rqsts¦RC-{Gb.pyicloud_location_update_cnt}»"
                            f"«LT-iOS App Updates¦LC-{Device.count_update_iosapp}¦"
                            f"RT-Time/Locate (secs)¦RC-{round(pyi_avg_time_per_call, 2)}»")
            else:
                count_msg +=(f"«HS¦LH-Device Counts¦RH-iOS App Counts»HE"
                            f"«LT-State/Triggers Chgs¦LC-{state_trig_count}¦"
                            f"RT-iOS Locate Requests¦RC-{Device.iosapp_request_loc_cnt}»"
                            f"«LT-iCloud Updates¦LC-{Device.count_update_icloud}¦"
                            f"RT-iOS App Updates¦RC-{Device.count_update_iosapp}»")

            count_msg     +=(f"«LT-Discarded¦LC-{Device.count_discarded_update}¦"
                            f"RT-Waze Routes¦RC-{Device.count_waze_locates}»"
                            f"¤e")

            post_event(Device.devicename, f"{count_msg}")

        except Exception as err:
            log_exception(err)

        return

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Perform tasks on a regular time schedule
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _timer_tasks_every_hour(self):
        for Device in Gb.Devices_by_devicename.values():
            self._display_usage_counts(Device)

#--------------------------------------------------------------------
    def _timer_tasks_midnight(self):
        for devicename, Device in Gb.Devices_by_devicename.items():
            event_msg =(f"{EVLOG_IC3_STAGE_HDR}iCloud3 v{VERSION} Daily Summary > "
                        f"{dt_util.now().strftime('%A, %b %d')}")
            post_event(devicename, event_msg)

            Gb.pyicloud_authentication_cnt  = 0
            Gb.pyicloud_location_update_cnt = 0
            Gb.pyicloud_calls_time          = 0.0
            Device.initialize_usage_counters()


        if Gb.WazeHist is None:
            return
        Gb.WazeHist.wazehist_delete_invalid_rcords()
        Gb.WazeHist.compress_wazehist_database()
        Gb.WazeHist.wazehist_update_track_sensor()
        if Gb.wazehist_recalculate_time_dist_flag:
            Gb.wazehist_recalculate_time_dist_flag = False
            Gb.WazeHist.wazehist_recalculate_time_dist_all_zones()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEVICE STATUS SUPPORT FUNCTIONS FOR GPS ACCURACY, OLD LOC DATA, ETC
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _check_old_loc_poor_gps(self, Device):
        """
        If this is checked in the icloud location cycle,
        check if the location isold flag. Then check to see if
        the current timestamp is the same as the timestamp on the previous
        poll.

        If this is checked in the iosapp cycle,  the trigger transaction has
        already updated the lat/long so
        you don't want to discard the record just because it is old.
        If in a zone, use the trigger but check the distance from the
        zone when updating the device.

        Update the old_loc_poor_gps_cnt if just_check=False
        """

        try:
            if Device.is_location_gps_good:
                Device.old_loc_poor_gps_cnt = 0
                Device.old_loc_poor_gps_msg = ''
            else:
                Device.old_loc_poor_gps_cnt += 1

                if Device.is_location_old_and_gps_poor:
                    Device.old_loc_poor_gps_msg = (f"OldLoc/PoorGPS (#{Device.old_loc_poor_gps_cnt})")
                elif Device.is_location_old:
                    Device.old_loc_poor_gps_msg = (f"OldLocation (#{Device.old_loc_poor_gps_cnt})")
                elif Device.is_gps_poor:
                    Device.old_loc_poor_gps_msg = (f"PoorGPS (#{Device.old_loc_poor_gps_cnt})")

                db_old_by     = (secs_since(Device.loc_data_secs) - Device.old_loc_threshold_secs)
                db_poorgps_by = (Device.loc_data_gps_accuracy - Gb.gps_accuracy_threshold)

        except Exception as err:
            log_exception(err)
            Device.old_loc_poor_gps_cnt = 0
            Device.old_loc_poor_gps_msg = ''

#--------------------------------------------------------------------
    def _is_outside_zone_no_exit(self, Device, zone, trigger, latitude, longitude):
        '''
        If the device is outside of the zone and less than the zone radius + gps_acuracy_threshold
        and no Geographic Zone Exit trigger was received, it has probably wandered due to
        GPS errors. If so, discard the poll and try again later

        Updates:    Set the Device.outside_no_exit_trigger_flag
                    Increase the old_location_poor_gps count when this innitially occurs
        Return:     Reason message
        '''
        if Device.iosapp_monitor_flag is False:
            return ''

        trigger = Device.trigger if trigger == '' else trigger
        if (instr(trigger, ENTER_ZONE)
                or Device.sensor_zone == NOT_SET
                or zone not in Gb.Zones_by_zone
                or Device.icloud_initial_locate_done is False):
            Device.outside_no_exit_trigger_flag = False
            return ''

        Zone           = Gb.Zones_by_zone[zone]
        dist_fm_zone_m = Zone.distance_m(latitude, longitude)
        zone_radius_m    = Zone.radius_m
        zone_radius_accuracy_m = zone_radius_m + Gb.gps_accuracy_threshold

        info_msg = ''
        if (dist_fm_zone_m > zone_radius_m
                and Device.got_exit_trigger_flag is False
                and is_statzone(Zone) is False):
            if (dist_fm_zone_m < zone_radius_accuracy_m
                    and Device.outside_no_exit_trigger_flag == False):
                Device.outside_no_exit_trigger_flag = True
                Device.old_loc_poor_gps_cnt += 1

                info_msg = ("Outside of Zone without iOSApp `Exit Zone` Trigger, "
                            f"Keeping in Zone-{Zone.display_as} > ")
            else:
                Device.got_exit_trigger_flag = True
                info_msg = ("Outside of Zone without iOSApp `Exit Zone` Trigger "
                            f"but outside threshold, Exiting Zone-{Zone.display_as} > ")

            info_msg += (f"Distance-{format_dist_m(dist_fm_zone_m)}, "
                        f"KeepInZoneThreshold-{format_dist_m(zone_radius_m)} "
                        f"to {format_dist_m(zone_radius_accuracy_m)}, "
                        f"Located-{Device.loc_data_time_age}")

        if Device.got_exit_trigger_flag:
            Device.outside_no_exit_trigger_flag = False

        return info_msg

#--------------------------------------------------------------------
    def _display_secs_to_next_update_info_msg(self, Device):
        '''
        Display the secs until the next update in the next update time field.
        if between 90s to -90s. if between -90s and -120s, resisplay time
        without the age to make sure it goes away. The age may be for a non-Home
        zone but displat it in the Home zone sensor.
        '''
        try:
            age_secs = secs_to(Device.next_update_secs)
            if -90 <= age_secs <= 90:
                Device.sensors_um[NEXT_UPDATE] = f"{age_secs}s"
                Device.write_ha_sensors_state([NEXT_UPDATE])

            elif Device.sensors_um.get(NEXT_UPDATE):
                Device.sensors_um[NEXT_UPDATE] = ''
                Device.write_ha_sensors_state([NEXT_UPDATE])

        except Exception as err:
            log_exception(err)
            pass


############ LAST LINE ###########