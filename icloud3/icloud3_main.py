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

# try:
from .global_variables  import GlobalVariables as Gb
from .const             import *
from .const_sensor      import SENSOR_LIST_DEVICE, SENSOR_LIST_TRACKING, SENSOR_LIST_ZONE

# from .support           import event_log
# from .support           import sensor_legacy
# from .                  import sensor
from .support           import start_ic3
from .support           import restore_state
from .support           import iosapp_data_handler
from .support           import iosapp_interface
from .support           import pyicloud_ic3_interface
from .support           import pyicloud_ic3_data_handler
from .support           import service_handler
from .support           import determine_interval as det_interval

from .helpers.base      import (instr, round_to_zero, isnumber, is_inzone_zone, is_statzone, isnot_inzone_zone,
                                signal_create_device_tracker_entities, signal_create_sensor_entities,
                                broadcast_info_msg,
                                post_event, post_error_msg, log_info_msg, log_error_msg,
                                post_monitor_msg, post_startup_event, post_internal_error,
                                log_debug_msg, log_info_msg, log_exception, log_rawdata,
                                _trace, _traceha, )
from .helpers.time      import (time_now_secs, secs_to_time, datetime_to_12hrtime, secs_to, secs_since,
                                secs_to_12hrtime, time_str_to_secs, timestamp_to_time_utcsecs,
                                secs_to_dhms_str, datetime_now, time_now, calculate_time_zone_offset,
                                secs_to_12hrtime_age_str, )
from .helpers.distance  import (m_to_ft_str, calc_distance_km, )
from .helpers.format    import (format_gps, format_dist, format_dist_m, format_list, )
from .helpers.entity_io import (get_attributes, )

# TEST_DETERMINE_INTERVAL_FLAG = True
# TEST_DETERMINE_INTERVAL_AFTER_ERROR_FLAG = False

from .support.pyicloud_ic3  import PyiCloudService
from .support.pyicloud_ic3  import (
        PyiCloudAPIResponseException,
        PyiCloud2SARequiredException, )




#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3:
    """iCloud3 Device Tracker Platform"""

    def __init__(self):

        # Gb.see = None
        Gb.hass_configurator_request_id = {}
        Gb.version                = VERSION
        Gb.attrs[ICLOUD3_VERSION] = VERSION

        Gb.start_icloud3_request_flag   = False
        Gb.start_icloud3_inprocess_flag = False

        Gb.polling_5_sec_loop_running  = False
        self.update_in_process_flag      = False
        self.pyicloud_refresh_time         = {}     # Last time Pyicloud was refreshed for the trk method
        self.pyicloud_refresh_time[FMF]    = 0
        self.pyicloud_refresh_time[FAMSHR] = 0

        Gb.authenticated_time            = 0
        Gb.icloud_no_data_error_cnt      = 0
        Gb.authentication_error_retry_secs = HIGH_INTEGER

        Gb.evlog_trk_monitors_flag       = False
        Gb.log_debug_flag                = False
        Gb.log_rawdata_flag              = False
        Gb.log_debug_flag_restart        = None
        Gb.log_rawdata_flag_restart      = None

        self.start_icloud3_inprocess_flag    = False
        self.start_icloud3_request_flag      = False
        self.any_device_being_updated_flag   = False
        self.update_in_process               = False

        self.attributes_initialized_flag = False
        self.e_seconds_local_offset_secs = 0

        #initialize variables configuration.yaml parameters
        start_ic3.set_global_variables_from_conf_parameters(evlog_msg=False)

    def __repr__(self):
        return (f"<iCloud3: {Gb.version}>")

#--------------------------------------------------------------------
    def start_icloud3(self):
        """
        Start iCloud3, Define all variables & tables, Initialize devices
        """
        broadcast_info_msg(f"Stage 0 > Define Variables, Tables, etc.")
        #check to see if restart is in process
        if Gb.start_icloud3_inprocess_flag:
            return

        try:
            self.start_timer = time_now_secs()
            if Gb.start_icloud3_initial_load_flag is False:
                Gb.EvLog.update_event_log_display("")
                start_ic3.reinitialize_config_parameters()
                start_ic3.initialize_global_variables()

            Gb.this_update_secs             = time_now_secs()
            Gb.start_icloud3_inprocess_flag = True
            Gb.start_icloud3_request_flag   = False
            Gb.config_track_devices_change_flag = False

            self.initial_locate_complete_flag = False
            self.startup_log_msgs             = ''
            self.startup_log_msgs_prefix      = ''

            start_ic3.define_tracking_control_fields()

            event_msg =(f"{EVLOG_INIT_HDR}Initializing iCloud3 v{VERSION} > "
                        f"{dt_util.now().strftime('%A, %b %d')}")
            post_event(event_msg)

            post_event(f"iCloud3 Directory > {Gb.icloud3_directory}")
            if Gb.conf_profile[CONF_VERSION] == 0:
                post_event(f"iCloud3 Configuration File > {Gb.config_ic3_yaml_filename}")
            else:
                post_event(f"iCloud3 Configuration File > {Gb.icloud3_config_filename}")

            start_ic3.display_platform_operating_mode_msg()
            start_ic3.check_ic3_event_log_file_version()

        except Exception as err:
            log_exception(err)

        #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        try:
            post_event(f"{EVLOG_INIT_HDR}Stage 1 > Prepare iCloud3 Configuration")
            broadcast_info_msg('Stage 1 > Prepare iCloud3 Configuration')

            start_ic3.set_global_variables_from_conf_parameters()
            calculate_time_zone_offset()

            start_ic3.create_Zones_object()
            start_ic3.create_Waze_object()

            if Gb.polling_5_sec_loop_running is False:
                broadcast_info_msg("Set Up 5-sec Polling Cycle")
                Gb.polling_5_sec_loop_running = True
                track_utc_time_change(Gb.hass, self._polling_loop_5_sec_device,
                        second=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])

        except Exception as err:
            log_exception(err)

        #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        try:
            post_event(f"{EVLOG_INIT_HDR}Stage 2 > Set up iCloud3 Devices")
            broadcast_info_msg('Stage 2 > Set up iCloud3 Devices')

            Gb.EvLog.update_event_log_display("")

            # Make sure a full restart is done if all of the devices were not found in the iCloud data
            if Gb.config_track_devices_change_flag:
                pass
            elif (Gb.tracking_method_FMF
                    and Gb.fmf_device_verified_cnt < len(Gb.Devices)):
                Gb.config_track_devices_change_flag = True
            elif (Gb.tracking_method_FAMSHR
                    and Gb.famshr_device_verified_cnt < len(Gb.Devices)):
                Gb.config_track_devices_change_flag = True
            elif Gb.log_debug_flag:
                Gb.config_track_devices_change_flag = True

            start_ic3.create_Devices_object()

            Gb.WazeHist.load_track_from_zone_table()

        except Exception as err:
            log_exception(err)

        #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        try:
            post_event(f"{EVLOG_INIT_HDR}Stage 3 > Set up Tracking Methods")
            Gb.EvLog.update_event_log_display("")

            broadcast_info_msg(f"Stage 3 > Set up Tracking Methods")
            if Gb.data_source_use_icloud:
                if Gb.username and Gb.password:
                    pyicloud_ic3_interface.pyicloud_initialize_device_api()
                else:
                    event_msg =(f"iCloud3 Alert > The iCloud username or password has not been "
                                f"configured. iCloud location tracking will not be done. ")
                    post_event(event_msg)

                if Gb.PyiCloud:
                    start_ic3.setup_tracked_devices_for_famshr()
                    start_ic3.setup_tracked_devices_for_fmf()
                    start_ic3.set_device_tracking_method_famshr_fmf()
                    start_ic3.tune_device_tracking_method_famshr_fmf()
            else:
                event_msg = 'iCloud Location Services is not being used to locate devices'
                post_event(event_msg)

            if Gb.data_source_use_iosapp:
                start_ic3.setup_tracked_devices_for_iosapp()
            else:
                event_msg = 'iOS App is not being used to locate devices'
                post_event(event_msg)

        except Exception as err:
            log_exception(err)

        #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        try:
            post_event(f"{EVLOG_INIT_HDR}Stage 4 > Configure Tracked Devices")
            broadcast_info_msg(f"Stage 4 > Configure Tracked Devices")

            start_ic3.remove_unverified_untrackable_devices()
            Gb.EvLog.setup_event_log_trackable_device_info()
            Gb.EvLog.update_event_log_display("")

            # Nothing to do if no devices to track
            # if len(Gb.Devices_by_devicename) == 0:
            if Gb.Devices_by_devicename:
                start_ic3.setup_trackable_devices()
                start_ic3.display_object_lists()
            else:
                event_msg =("iCloud3 Error > Setup aborted, no devices to track. "
                            "CRLFNo devices have been configured for tracking using the iCloud3 "
                            "configurator or the `Tracking Mode` for all of the devices "
                            "is set to Inactive. "
                            "CRLFReview the current configuration below. "
                            "CRLF1. Select `HA Sidebar > Configuration`"
                            "CRLF2. Select `Devices and Services`, then select `Integrations`"
                            "CRLF4. Select `iCloud3 > Configure`. Then setup the iCloud3 "
                            "configuration using the various setup forms")
                post_event(event_msg)

                Gb.EvLog.update_event_log_display("")
                Gb.start_icloud3_inprocess_flag = False
                # return False

        except Exception as err:
            log_exception(err)

        start_ic3.display_platform_operating_mode_msg()
        start_ic3.post_restart_icloud3_complete_msg()
        broadcast_info_msg("Inialization Complete")

        #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

        if Gb.log_debug_flag is False:
            Gb.startup_log_msgs = (NEW_LINE + '-'*55 +
                                    Gb.startup_log_msgs.replace(CRLF, NEW_LINE) +
                                    NEW_LINE + '-'*55)
            log_info_msg(Gb.startup_log_msgs)
        Gb.startup_log_msgs = ''

        broadcast_info_msg("Initial Locate")
        self._polling_loop_5_sec_device(-1)
        Gb.EvLog.update_event_log_display("")
        Gb.start_icloud3_inprocess_flag = False
        Gb.broadcast_info_msg = None

        # if Gb.polling_5_sec_loop_running is False:
        #     broadcast_info_msg("Set Up 5-sec Polling Cycle")
        #     Gb.polling_5_sec_loop_running = True
        #     track_utc_time_change(Gb.hass, self._polling_loop_5_sec_device,
        #             second=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])

        return True

#########################################################
#
#   This function is called every 5 seconds by HA. Cycle through all
#   of the iCloud devices to see if any of the ones being tracked need
#   to be updated. If so, we might as well update the information for
#   all of the devices being tracked since PyiCloud gets data for
#   every device in the account
#
#########################################################
    def _polling_loop_5_sec_device(self, ha_timer_secs):
        try:
            if Gb.config_flow_parameters_updated != {''}:
                start_ic3.process_conf_flow_parameter_updates()

            if Gb.start_icloud3_request_flag:    #via service call
                self.start_icloud3()
                Gb.start_icloud3_request_flag = False

            # Exit 5-sec loop if no devices, updating a device now, or restarting iCloud3
            if (Gb.any_device_being_updated_flag
                    or Gb.conf_devices == []
                    or Gb.start_icloud3_inprocess_flag):

                # Authentication may take a long time, Display a status message before exiting loop
                if (Gb.pyicloud_auth_started_secs > 0):
                        # and Gb.this_update_time[:-2] in ['00', '15', '30', '45']):
                    info_msg = ("iCloud Account Authentication Requested at "
                                f"{secs_to_time(Gb.pyicloud_auth_started_secs)} "
                                f"({secs_to_dhms_str(secs_since(Gb.pyicloud_auth_started_secs))} ago)")
                    for devicename, Device in Gb.Devices_by_devicename.items():
                        Device.display_info_msg(info_msg)
                return

            # Handle any EvLog > Actions requested by the 'service_handler' module.
            if Gb.evlog_action_request == '':
                pass

            elif Gb.evlog_action_request == CMD_RESET_PYICLOUD_SESSION:
                pyicloud_ic3_interface.pyicloud_reset_session()
                Gb.evlog_action_request = ''

        except Exception as err:
            log_exception(err)
            return

        Gb.this_update_secs   = time_now_secs()
        Gb.this_update_time   = dt_util.now().strftime('%H:%M:%S')
        Gb.update_restore_state_file_flag = False
        #Reset counts on new day, check for daylight saving time new offset
        if Gb.this_update_time.endswith(':00:00'):
            self._timer_tasks_every_hour()

        if Gb.this_update_time == HHMMSS_ZERO:
            self._timer_tasks_midnight()

        elif Gb.this_update_time == '01:00:00':
            calculate_time_zone_offset()

        #Test code to check ios monitor, display it every minute
        try:
            if (Gb.this_update_secs >= Gb.EvLog.clear_secs
                    and Gb.log_debug_flag is False):
                Gb.EvLog.update_event_log_display('clear_log_items')
        except:
            pass

        try:

            if Gb.this_update_secs >= Gb.authentication_error_retry_secs:
                post_event(f"Retry authentication > "
                            f"Timer={secs_to_time(Gb.authentication_error_retry_secs)}")
                pyicloud_ic3_interface.pyicloud_authenticate_account()

            if Gb.this_update_time.endswith(':00'):
                for devicename, Device in Gb.Devices_by_devicename.items():
                    Device.display_info_msg(Device.format_info_msg)

            #-----------------------------------------------------------------------------
            # iOSApp Device loop
            #-----------------------------------------------------------------------------
            for devicename, Device in Gb.Devices_by_devicename.items():
                if Gb.data_source_use_iosapp is False:
                    break
                if Device.iosapp_monitor_flag is False:
                    continue
                elif Device.is_tracking_paused:
                    continue

                #iosapp uses the device_tracker.<devicename>_# entity for
                #location info and sensor.<devicename>_last_update_trigger entity
                #for trigger info. Get location data and trigger.
                #Use the trigger/timestamp if timestamp is newer than current
                #location timestamp.
                update_reason = ''

                iosapp_data_handler.check_iosapp_state_trigger_change(Device)

                # Turn off monitoring the iOSApp if excessive errors
                if Device.iosapp_data_invalid_error_cnt > 50:
                    Device.iosapp_data_invalid_error_cnt = 0
                    Device.iosapp_monitor_flag = False
                    event_msg =("iCloud3 Error > iOSApp entity error cnt exceeded, "
                                "iOSApp monitoring stopped. iCloud monitoring will be used.")
                    post_event(Device.devicename, event_msg)
                    continue

                # iOSApp has process a non-tracked zone change (enter zone, sig loc update, etc).
                # Delay the zone enter from being processed for 1-min (PASS_THRU_ZONE_INTERVAL_SECS)
                # to see if just passing thru a zone. If still in the zone after 1-minute, it
                # will be handled normally.
                if Device.passthru_zone_expire_secs > 0:
                    det_interval.pass_thru_zone_delay(Device)
                    continue

                # The iosapp may be entering or exiting another Device's Stat Zone. If so,
                # reset the iosapp information to this Device's Stat Zone and continue.
                if Device.iosapp_data_updated_flag:
                    Device.iosapp_data_invalid_error_cnt = 0

                    event_msg =(f"Trigger > {Device.iosapp_data_change_reason}")
                    post_event(Device.devicename, event_msg)

                    iosapp_data_handler.check_enter_exit_stationary_zone(Device)

                    self._process_new_iosapp_data(Device, Device.iosapp_data_change_reason)

                # Send a location request every 2-hours
                iosapp_data_handler.check_if_iosapp_is_alive(Device)

                # Refresh the EvLog if this is an initial locate
                if self.initial_locate_complete_flag == False:
                    if devicename == Gb.Devices[0].devicename:
                        Gb.EvLog.update_event_log_display(devicename)

            #-----------------------------------------------------------------------------
            # iCloud Device Loop
            #-----------------------------------------------------------------------------
            for devicename, Device in Gb.Devices_by_devicename.items():
                # save_device_icloud_initial_locate_done = Device.icloud_initial_locate_done
                if Device.any_reason_to_update_ic3_device_and_sensors() is False:
                    continue
                elif Device.is_tracking_paused:
                    continue

                # if Device.icloud_update_needed_flag is False:
                #     continue

                Device.calculate_old_location_threshold()
                if Device.should_ic3_device_and_sensors_be_updated() is False:
                    continue

                                # if Device.icloud_update_needed_flag is False:
                #     continue

                # Updating device info. Get data from FmF or FamShr
                pyicloud_ic3_data_handler.request_icloud_data_update(Device)

                if Device.icloud_data_updated_flag:
                    Gb.icloud_no_data_error_cnt = 0

                # iOSApp has process a non-tracked zone change (enterzone, sig loc update, etc).
                # Delay the zone enter from being processed for 1-min (PASS_THRU_ZONE_INTERVAL_SECS)
                # to see if just passing thru a zone. If still in the zone after 1-minute, it
                # will be handled normally.
                elif Device.passthru_zone_expire_secs > 0:
                    det_interval.pass_thru_zone_delay(Device)
                    continue

                else:
                    # An error ocurred accessing the iCloud account. This can be a
                    # Authentication error or an error retrieving the loction data
                    Gb.icloud_no_data_error_cnt += 1

                    if Device.icloud_initial_locate_done is False:
                        Device.update_sensors_error_msg = "Retrying Initial Locate"
                    else:
                        Device.update_sensors_error_msg = "iCloud is Offline (Authentication or Location Error)"

                    det_interval.determine_interval_after_error(
                                                Device,
                                                counter=AUTH_ERROR_CNT)

                    if Gb.icloud_no_data_error_cnt > 20:
                        start_ic3.set_tracking_method(IOSAPP)
                        Device.tracking_method = IOSAPP
                        log_msg = ("iCloud3 Error > More than 20 iCloud Authentication "
                                    "errors. Resetting to use tracking_method <iosapp>. "
                                    "Restart iCloud3 at a later time to see if iCloud "
                                    "Loction Services is available.")
                        post_error_msg(log_msg)

                    return

                self._post_before_update_monitor_msg(Device)

                # Update the Device tracking information
                update_reason = Device.icloud_update_reason.split('>')[0]

                self._process_new_icloud_data(Device, update_reason)

                self._post_after_update_monitor_msg(Device)

                Device.device_being_updated_flag = False
                self.update_in_process_flag      = False

                # Refresh the EvLog if this is an initial locate
                if self.initial_locate_complete_flag == False:
                    if devicename == Gb.Devices[0].devicename:
                        Gb.EvLog.update_event_log_display(devicename)

            if Gb.update_restore_state_file_flag:
                restore_state.write_storage_icloud3_restore_state_file()

            Gb.any_device_being_updated_flag = False

            #If less than 90 secs to the next update for any devicename:zone, display time to
            #the next update in the NextUpdt time field, e.g, 1m05s or 0m15s.
            self._display_secs_to_next_update_info_msg()

            #End devicename in self.tracked_devices loop

        except Exception as err:
            log_exception(err)
            log_msg = (f"Device Update Error, Error-{ValueError}")
            post_error_msg(log_msg)

        self.update_in_process_flag = False

        # if (Gb.Devices_by_devicename
                # and self.initial_locate_complete_flag == False):
        if self.initial_locate_complete_flag == False:
            self.initial_locate_complete_flag = True


#########################################################
#
#   Update the device on a state or trigger change was received from the ios app
#
#########################################################
    def _process_new_iosapp_data(self, Device, update_reason):
        """
        Update the devices location using data from the iOS App
        """
        if Gb.start_icloud3_inprocess_flag:
            return ''
        elif Device.iosapp_monitor_flag is False:
            return ''

        devicename = Device.devicename
        Device.iosapp_request_loc_retry_cnt = 0
        Device.iosapp_request_loc_sent_secs = 0
        Device.iosapp_request_loc_sent_flag = False

        try:
            if Device.is_tracking_paused:
                return ''
            elif Device.iosapp_data_latitude == 0  or Device.iosapp_data_longitude == 0:
                return ''

            Gb.any_device_being_updated_flag = True
            return_code = IOSAPP_UPDATE

            self._log_start_finish_update_banner('↓↓', devicename, IOSAPP_FNAME, update_reason)

            event_msg =(f"{EVLOG_UPDATE_START}iOSApp update started > {update_reason.split('@')[0]}")
            post_event(devicename, event_msg)

            det_interval.post_zone_time_dist_event_msg(Device, Device.DeviceFmZoneHome)

            try:
                # Check to see if the location is outside the zone without an exit trigger

                for from_zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
                    if is_inzone_zone(from_zone):
                        info_msg = self._is_outside_zone_no_exit(
                                                Device,
                                                from_zone,
                                                '',
                                                Device.iosapp_data_latitude,
                                                Device.iosapp_data_longitude)

                        if Device.outside_no_exit_trigger_flag:
                            post_event(devicename, info_msg)
                            # Set located time to trigger time so it won't fire as trigger change again
                            Device.loc_data_secs = Device.iosapp_data_trigger_secs + 10
                            return ''

            except Exception as err:
                post_internal_error('Outside Zone Check', traceback.format_exc)

            try:
                Device.update_sensors_flag = True
                if (Device.iosapp_data_isold
                        and Device.next_update_time_reached):
                    Device.old_loc_poor_gps_cnt += 1
                    iosapp_interface.request_location(Device)

                    Device.update_sensors_error_msg =  (f"OldLocation (#{Device.old_loc_poor_gps_cnt})")
                    Device.update_sensors_flag = False

                if Device.update_sensors_flag:
                    Device.update_dev_loc_data_from_raw_data(IOSAPP)

                self._process_updated_location_data(Device, update_reason)

            except Exception as err:
                log_exception(err)

        except Exception as err:
            post_internal_error('iOSApp Update', traceback.format_exc)
            return_code = ICLOUD_UPDATE

        Gb.any_device_being_updated_flag = False

        return return_code

#########################################################
#
#   Cycle through all iCloud devices and update the information for the devices
#   being tracked
#
#########################################################
    def _process_new_icloud_data(self, Device, update_reason='Check iCloud'):

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

        Gb.any_device_being_updated_flag = True

        try:
            devicename = Device.devicename
            Device.icloud_update_retry_flag = False
            zone = Device.loc_data_zone

            event_msg =(f"{EVLOG_UPDATE_START}{Device.tracking_method_fname} update started > "
                        f"{update_reason.split('@')[0]}")
            post_event(devicename, event_msg)

            self._log_start_finish_update_banner('↓↓',
                                                devicename,
                                                "iCloud",
                                                update_reason)

            Device.update_timer = time_now_secs()
            Device.iosapp_request_loc_sent_secs = 0

            det_interval.post_zone_time_dist_event_msg(Device, Device.DeviceFmZoneHome)

            Device.calculate_old_location_threshold()

            #icloud data overrules device data which may be stale
            latitude     = Device.loc_data_latitude
            longitude    = Device.loc_data_longitude
            gps_accuracy = Device.loc_data_gps_accuracy   #0  db 5/12/2022

            if latitude != 0 and longitude != 0:
                self._check_old_loc_poor_gps(Device)

            #Discard if no location coordinates
            Device.update_sensors_flag = True
            if latitude == 0 or longitude == 0:
                Device.update_sensors_flag = False

            #Check to see if currently in a zone. If so, check the zone distance.
            #If new location is outside of the zone and inside radius*4, discard
            #by treating it as poor GPS
            elif (isnot_inzone_zone(zone)
                    or Device.sensor_zone == NOT_SET):
                Device.outside_no_exit_trigger_flag = False
                Device.update_sensors_error_msg= ''

            else:
                Device.update_sensors_error_msg = self._is_outside_zone_no_exit(Device, zone, '', latitude, longitude)

            #Ignore old location when in a zone and discard=False
            #let normal next time update check process
            if (Device.is_location_old_or_gps_poor
                    and Device.is_inzone
                    and Device.next_update_time_reached is False
                    and Device.outside_no_exit_trigger_flag is False
                    and Gb.discard_poor_gps_inzone_flag is False):
                Device.old_loc_poor_gps_cnt -= 1
                Device.old_loc_poor_gps_msg = ''

                event_msg =(f"Old Loc/Poor GPS exception (will use location data) > "
                            f"DiscardPoorGPSinZone-False, inZone-True, "
                            f"NextUpdate-{Device.DeviceFmZoneHome.next_update_time} "
                            f"(not reached), "
                            f"GPS-{format_gps(latitude, longitude, gps_accuracy)}, "
                            f"LocationTime-{Device.loc_data_time_age}")
                post_event(devicename, event_msg)

            elif Device.is_offline:
                Device.update_sensors_flag = False
                Device.update_sensors_error_msg = "Device Offline"

                event_msg =(f"Device Status Exception, Tracking may be delayed > {devicename} "
                            f"Status-{Device.dev_data_device_status}")
                post_event(devicename, event_msg)

            # Outside zone, no exit trigger check. This is valid for location less than 2-minutes old
            # **changed 4/24 - added 2-min check so it wouldn't hang with old iosapp data
            elif (Device.iosapp_monitor_flag
                    and Device.outside_no_exit_trigger_flag
                    and secs_since(Device.iosapp_data_secs) < 120):
                Device.update_sensors_error_msg = "Outside of zone without iOSApp `Exit Zone` Trigger"
                Device.update_sensors_flag = False

            # Discard if location is old and next update time has been reached
            # **changed 4/24 - Will check for old loc after other checks (was)
            if (Device.is_location_old_or_gps_poor
                    and Device.next_update_time_reached):
                Device.update_sensors_error_msg = (f"{Device.old_loc_poor_gps_msg}")
                Device.update_sensors_flag = False

            self._process_updated_location_data(Device, update_reason)

            Device.icloud_initial_locate_done = True
            Device.tracking_status = TRACKING_NORMAL

        except Exception as err:
            post_internal_error('iCloud Update', traceback.format_exc)
            Device.device_being_updated_flag = False

        Gb.any_device_being_updated_flag = False

#########################################################
#
#   Determine the update interval, Update the sensors and device_tracker entity
#
#   1. Cycle through each trackFromZone zone for the Device and determint the interval,
#   next_update_time, distance from the zones, etc. Then update all of the TrackFromZone
#   sensors for the Device (this is normally just the Home zone).
#   2. Update the sensors for the device.
#   3. Update the device_tracker entity for the device.
#
#########################################################
    def _process_updated_location_data(self, Device, update_reason):
        try:
            devicename  = Device.devicename

            # Location data is good. Determine next update time and update interval,
            # next_update_time values and sensors with the good data
            if Device.update_sensors_flag:
                self._calculate_interval_and_next_update(Device)

                self._update_sensors_values_from_data_fields(Device)
                Device.update_sensors()
                Device.update_device_from_zone_sensors()
                Device.update_device_tracker_entity()
                self._update_restore_state_values(Device)

                event_msg =(f"{EVLOG_UPDATE_END}{Device.tracking_method_fname} update completed")
                if Device.tracking_method_fname != Device.dev_data_source:
                    event_msg += (f" > Used {Device.dev_data_source} Data")
                post_event(devicename, event_msg)

            else:
                # Old location, poor gps etc. Determine the next update time to request new location info
                # with good data (hopefully). Update interval, next_update_time values and sensors with the time
                det_interval.determine_interval_after_error(Device, counter=OLD_LOC_POOR_GPS_CNT)

            #**db 5/3 stop looping
            # if (Gb.EvLog.last_devicename in ["", devicename]):
            #     Gb.EvLog.update_event_log_display(devicename)
            # Refresh the EvLog if this is an initial locate
            if self.initial_locate_complete_flag == False:
                if devicename == Gb.Devices[0].devicename:
                        Gb.EvLog.update_event_log_display(devicename)

            self._log_start_finish_update_banner('↑↑',
                                                devicename,
                                                f"{Device.tracking_method_fname}/{Device.dev_data_source}",
                                                "gen update")

        except Exception as err:
            post_internal_error('iCloud Update', traceback.format_exc)
            Device.device_being_updated_flag = False

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
        try:
            devicename = Device.devicename

            Device.post_location_data_event_msg()

            if Device.device_being_updated_flag:
                info_msg  = "Retrying > Last update not completed"
                event_msg = info_msg
                post_event(devicename, event_msg)

            #set device being updated flag. This is checked in the
            #'_polling_loop_15_sec_icloud' loop to make sure the last update
            #completed successfully (Waze has a compile error bug that will
            #kill update and everything will sit there until the next poll.
            #if this is still set in '_polling_loop_15_sec_icloud', repoll
            #immediately!!!
            Device.device_being_updated_flag = True

        except Exception as err:
            post_internal_error('Update Attributes', traceback.format_exc)

        try:
            if Device.dev_data_source == IOSAPP_FNAME:
                Device.trigger = (f"{Device.iosapp_data_trigger}@{Device.iosapp_data_trigger_time}")
            else:
                Device.trigger = (f"{Device.dev_data_source}@{Device.loc_data_datetime[11:19]}")

            # Update the device's zone/away status
            self._get_zone(Device, display_zone_msg=True)

            calc_dist_last_poll_moved_km = calc_distance_km(
                                        Device.sensors[LATITUDE],
                                        Device.sensors[LONGITUDE],
                                        Device.loc_data_latitude,
                                        Device.loc_data_longitude)
            Device.StatZone.update_distance_moved(calc_dist_last_poll_moved_km)

            #See if moved less than the stationary zone movement limit
            #If updating via the ios app and the current state is stationary,
            #make sure it is kept in the stationary zone
            if Device.StatZone.timer_expired:
                if Device.StatZone.moved_dist > Device.StatZone.dist_move_limit:
                    Device.StatZone.reset_timer_time

                elif (Device.StatZone.not_inzone
                        or (is_statzone(Device.iosapp_data_state)
                            and Device.loc_data_zone == NOT_SET)):
                    Device.stationary_zone_update_control = STAT_ZONE_MOVE_DEVICE_INTO
                    Device.StatZone.update_stationary_zone_location()

                    self._get_zone(Device, display_zone_msg=True)

        except Exception as err:
            post_internal_error('Update Stat Zone', traceback.format_exc)

        try:
            # Update the devices that are near each other
            self._update_devices_in_same_location()

            # Cycle thru each Track From Zone get the interval and all other data
            devicename = Device.devicename

            # This is used to determine the zone with the soonest update
            Device.DeviceFmZoneTracked = Device.DeviceFmZoneHome

            for from_zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
                self._log_start_finish_update_banner('↓↓', devicename, Device.tracking_method_fname, from_zone)

                # See if this Device is near another Device. If it is, use the near Device's
                # determine_interval results instead of recalculating everything.
                near_device_results_copied_flag = False
                if Device.is_near_another_device:
                    NearDevice = Device.NearDevice

                    # Make sure this Device is tracking from the same zone as the NearDevice
                    if from_zone in NearDevice.DeviceFmZones_by_zone:
                        NearDeviceFmZone            = NearDevice.DeviceFmZones_by_zone[from_zone]
                        Device.DeviceFmZoneCurrent  = DeviceFmZone
                        near_device_results_copied_flag = True
                        event_msg =(f"Using Nearby Device > "
                                    f"{NearDevice.fname_devicename}/"
                                    f"{format_dist_m(Device.near_device_distance)}, "
                                    f"Zone-{NearDeviceFmZone.FromZone.display_as}")
                        post_event(Device.devicename, event_msg)

                        det_interval.copy_near_device_results(Device, DeviceFmZone, NearDevice, NearDeviceFmZone)


                # Determine the interval and update times for the track_from_zones for this Device
                if near_device_results_copied_flag is False:
                    det_interval.determine_interval(Device, DeviceFmZone)

                # The DeviceFmZone tracking sensors have the results i.e., zone distance, interval, next update time
                # and direction calculations, etc. The TrackFmZone sensor data that is closest to the Device's
                # location are copied to the Device sensors if the Device is within the TrackFmZone tracking
                # radius (8km). The Home tracking results are used when outside this radius.
                if (Device.DeviceFmZoneTracked.zone_dist < 8
                        and DeviceFmZone.zone_dist < Device.DeviceFmZoneTracked.zone_dist):
                    Device.DeviceFmZoneTracked = DeviceFmZone

                self._log_start_finish_update_banner('↑↑', devicename, Device.tracking_method_fname, from_zone)


        except Exception as err:
            log_exception(err)
            post_internal_error('Det IntervalLoop', traceback.format_exc)
            return False

        Device.device_being_updated_flag = False

#----------------------------------------------------------------------------
    def xx_check_reset_zone_name_change(self, Device):
        """ Check to see if the zone name change needs to be overridden based on
            enter/exit conditions or stationary zone changes.
        """

        # If a non-tracked from zone was entered (not_home --> zone), and the
        # enter zone secs is less than 1-minute ago, cancel the zone enter name
        # change in case the Device is just passing thru the zone
        if (Device.is_inzone
                and Device.loc_data_zone not in Device.DeviceFmZones_by_zone
                and Device.wasnot_inzone
                and secs_since(Device.zone_change_secs) < 60
                and Device.DeviceFmZoneTracked.interval_secs == PASS_THRU_ZONE_INTERVAL_SECS):

            monitor_msg = (f"Zone Enter Delayed > May be just passing thru zone, "
                            f"Zone-{Device.loc_data_zone}, "
                            f"Delayed-{PASS_THRU_ZONE_INTERVAL_SECS} secs")
            post_monitor_msg(Device.devicename, monitor_msg)
            _trace(monitor_msg)

            Device.loc_data_zone = NOT_HOME

#----------------------------------------------------------------------------
    def _update_sensors_values_from_data_fields(self, Device):
        #Note: Final prep and update device attributes via
        #device_tracker.see. The gps location, battery, and
        #gps accuracy are not part of the attrs variable and are
        #reformatted into device attributes by 'See'. The gps
        #location goes to 'See' as a "(latitude, longitude)" pair.
        #'See' converts them to LATITUDE and LONGITUDE
        #and discards the 'gps' item.

        # Determine the soonest DeviceFmZone to update, then get the sensor values to be displayed with
        # the Device sensors

        try:
            # Device related sensors
            Device.sensors[INFO]                 = Device.format_info_msg
            Device.sensors[BATTERY]              = Device.dev_data_battery_level
            Device.sensors[BATTERY_STATUS]       = Device.dev_data_battery_status
            Device.sensors[DEVICE_STATUS]        = Device.dev_data_device_status
            Device.sensors[LOW_POWER_MODE]       = Device.dev_data_low_power_mode
            Device.sensors[BADGE]                = Device.badge_sensor_value

            # Location related items
            Device.sensors[GPS]                  = (Device.loc_data_latitude, Device.loc_data_longitude)
            Device.sensors[LATITUDE]             = Device.loc_data_latitude
            Device.sensors[LONGITUDE]            = Device.loc_data_longitude
            Device.sensors[GPS_ACCURACY]         = m_to_ft_str(Device.loc_data_gps_accuracy)
            Device.sensors[ALTITUDE]             = m_to_ft_str(Device.loc_data_altitude)
            Device.sensors[VERT_ACCURACY]        = m_to_ft_str(Device.loc_data_vert_accuracy)
            Device.sensors[LOCATION_SOURCE]      = Device.dev_data_source
            Device.sensors[TRIGGER]              = Device.trigger
            Device.sensors[LAST_LOCATED_DATETIME] = Device.loc_data_datetime
            Device.sensors[LAST_LOCATED_TIME]    = Device.loc_data_time
            Device.sensors[LAST_LOCATED]         = Device.loc_data_time

            Device.sensors[FROM_ZONE]            = Device.DeviceFmZoneTracked.from_zone
            Device.sensors[INTERVAL]             = Device.DeviceFmZoneTracked.sensors[INTERVAL]
            Device.sensors[NEXT_UPDATE_DATETIME] = Device.DeviceFmZoneTracked.sensors[NEXT_UPDATE_DATETIME]
            Device.sensors[NEXT_UPDATE_TIME]     = Device.DeviceFmZoneTracked.sensors[NEXT_UPDATE_TIME]
            Device.sensors[NEXT_UPDATE]          = Device.DeviceFmZoneTracked.sensors[NEXT_UPDATE]
            Device.sensors[LAST_UPDATE_DATETIME] = Device.DeviceFmZoneTracked.sensors[LAST_UPDATE_DATETIME]
            Device.sensors[LAST_UPDATE_TIME]     = Device.DeviceFmZoneTracked.sensors[LAST_UPDATE_TIME]
            Device.sensors[LAST_UPDATE]          = Device.DeviceFmZoneTracked.sensors[LAST_UPDATE]
            Device.sensors[TRAVEL_TIME_MIN]      = Device.DeviceFmZoneTracked.sensors[TRAVEL_TIME_MIN]
            Device.sensors[TRAVEL_TIME]          = Device.DeviceFmZoneTracked.sensors[TRAVEL_TIME]
            Device.sensors[ZONE_DISTANCE]        = Device.DeviceFmZoneTracked.sensors[ZONE_DISTANCE]
            Device.sensors[HOME_DISTANCE]        = Device.DeviceFmZoneHome.sensors[ZONE_DISTANCE]
            Device.sensors[WAZE_DISTANCE]        = Device.DeviceFmZoneTracked.sensors[WAZE_DISTANCE]
            Device.sensors[CALC_DISTANCE]        = Device.DeviceFmZoneTracked.sensors[CALC_DISTANCE]
            Device.sensors[TRAVEL_DISTANCE]      = Device.DeviceFmZoneTracked.sensors[TRAVEL_DISTANCE]

            # If moving towards a tracked from zone, change the direction to 'To-[zonename]'
            if Device.DeviceFmZoneTracked.sensors[DIR_OF_TRAVEL].startswith(TOWARDS):
                Device.sensors[DIR_OF_TRAVEL] = f"{TOWARDS}{Device.DeviceFmZoneTracked.from_zone_display_as}"
            else:
                Device.sensors[DIR_OF_TRAVEL] = Device.DeviceFmZoneTracked.sensors[DIR_OF_TRAVEL]

            # Zone related sensors
            if Device.loc_data_zone != Device.sensor_zone:
                Device.sensors[LAST_ZONE]      = Device.sensors[ZONE]
                Device.sensors[ZONE_DATETIME]  = Device.zone_change_datetime
            Device.sensors[ZONE]               = Device.loc_data_zone
            Device.sensors[DEVTRK_STATE_VALUE] = Device.loc_data_zone_fname

            # If TrackFromZone is not Home and there is a '.' in the number, remove it so
            # there is room for the zone name
            if Device.sensors[FROM_ZONE] != HOME:
                from_zone = Device.DeviceFmZoneTracked.from_zone
                Zone = Gb.Zones_by_zone[from_zone]
                if instr(Device.sensors[ZONE_DISTANCE], '.'):
                    int_dec_um_parts = Device.sensors[ZONE_DISTANCE].split('.')
                    Device.sensors[ZONE_DISTANCE] = f"{int_dec_um_parts[0]} {Gb.um}"

                Device.sensors_um[ZONE_DISTANCE] = f"-{Zone.display_as[:5]}"

            Device.StatZone.update_stationary_zone_location()

            Device.last_attrs_update_loc_secs = Device.loc_data_secs

            # Reset any special um message fields after update
            Device.sensors_um = {}

        except Exception as err:
            post_internal_error('Set Attributes', traceback.format_exc)

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

        zone_selected_dist_km = HIGH_INTEGER
        ZoneSelected          = None
        zone_selected         = None
        zones_msg             = ""
        iosapp_zone_msg       = ""

        # zone_iosapp = self.iosapp_data_state if is_inzone_zone(self.iosapp_data_state) else None
        # iOSApp will trigger Enter Region when the edge of the devices's location area (100m)
        # touches or is inside the zones radius. If enterina a zone, increase the zone's radius
        # so the device will be in the zone when it is actually just outside of it.
        # But don't do this for a Stationary Zone.
        # if (self.isnot_set or (instr(self.iosapp_data_trigger, REGION_ENTERED))
        #         and is_statzone(self.iosapp_data_state) is False):
        #     zone_radius_iosapp_enter_adjustment_km = .100
        # else:
        zone_radius_iosapp_enter_adjustment_km = 0
        if instr(Device.trigger.lower(), 'exit') is False:
            zone_radius_iosapp_enter_adjustment_km = .05    # if Close to zone, add 100m for iOS App Extra area

        for Zone in Gb.Zones:
            zone           = Zone.zone
            zone_radius_km = Zone.radius_km
            zone_dist_km   = Zone.distance_km(Device.loc_data_latitude, Device.loc_data_longitude)

            if (.100 < zone_dist_km <= .150
                    and zone_radius_iosapp_enter_adjustment_km > 0):
                zone_radius_km += zone_radius_iosapp_enter_adjustment_km
                zone_radius_iosapp_enter_adjustment_msg = '+50m'
            else:
                zone_radius_iosapp_enter_adjustment_msg = ''

            #Skip another device's stationary zone or if at base location
            if (is_statzone(zone) and instr(zone, Device.devicename) is False):
                continue

            #Bypass stationary zone at base and Pseudo Zones (not_home, not_set, etc)
            elif Zone.radius <= 1:
                continue

            #Do not check Stat Zone if radius=1 (at base loc) but include in log_msg
            in_zone_flag      = zone_dist_km <= zone_radius_km
            closer_zone_flag  = zone_selected is None or zone_dist_km < zone_selected_dist_km
            smaller_zone_flag = (zone_dist_km == zone_selected_dist_km
                                     and zone_radius_km <= zone_selected_radius_km)

            if in_zone_flag and (closer_zone_flag or smaller_zone_flag):
                ZoneSelected          = Zone
                zone_selected         = zone
                zone_selected_dist_km = zone_dist_km
                iosapp_zone_msg       = ""
                zone_selected_radius_km = ZoneSelected.radius_km + zone_radius_iosapp_enter_adjustment_km

            if is_statzone(zone):
                zones_msg += Device.StatZone.display_as
            else:
                zones_msg += Zone.display_as
            zones_msg +=   (f"-{format_dist(zone_dist_km)}/"
                            f"r{Zone.radius:.0f}m"
                            f"{zone_radius_iosapp_enter_adjustment_msg}, ")

        # _trace(f'{zone_selected=} {Device.iosapp_data_trigger_time=} {secs_since(Device.iosapp_data_trigger_secs)=} {Device.iosapp_data_trigger=} ')
        # if ZoneSelected is not None:
            # _trace(f'{zone_selected=} {Device.iosapp_zone_enter_time=} {secs_since(Device.iosapp_zone_enter_secs)=} ')

        if ZoneSelected is None:
            ZoneSelected       = Gb.Zones_by_zone[NOT_HOME]
            zone_selected      = NOT_HOME
            zone_selected_dist_km = 0
            # _trace(f'{zone_selected=} {Device.iosapp_zone_exit_time=} {secs_since(Device.iosapp_zone_exit_secs)=} ')

            #If not in a zone and was in a Stationary Zone, Exit the zone and reset everything
            if Device.StatZone.inzone:
                Device.stationary_zone_update_control = STAT_ZONE_MOVE_TO_BASE

        zones_msg = (f"Selected Zone > {ZoneSelected.display_as} > "
                    f"{zones_msg[:-2]}{iosapp_zone_msg}"#)
                    f", Trigger-{Device.trigger}")

        if display_zone_msg:
            post_event(Device.devicename, zones_msg)

        # Get distance between zone selected and current zone to see if they overlap.
        # If so, keep the current zone
        if (zone_selected != NOT_HOME
                and self._is_overlapping_zone(Device.loc_data_zone, zone_selected)):
            zone_selected = Device.loc_data_zone
            ZoneSelected  = Gb.Zones_by_zone[Device.loc_data_zone]

        if Device.loc_data_zone != zone_selected:
            Device.loc_data_zone        = zone_selected
            Device.zone_change_datetime = datetime_now()
            Device.zone_change_secs     = time_now_secs()

        return (zone_selected, ZoneSelected)

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
    def _update_devices_in_same_location(self):
        '''
        Cycle through the devices and see if one device is in the same location as
        another device. If so, when the interval is determined, use one device's
        interval attributes for another rather than recalculating everything. Do this
        in the Gb.Device's order so the device later in the list will use the data
        of a device earlier in the list. The later Device will have the earlier Device
        in it's 'same_location' table.
        '''
        try:
            for NearDevice in Gb.Devices:
                if (NearDevice.NearDevice is not None
                        or NearDevice.isnot_set
                        or NearDevice.is_location_old_or_gps_poor):
                    continue

                for Device in Gb.Devices:
                    if Device is NearDevice:
                        continue

                    Device.NearDevice = None
                    distance_apart =  Device.distance_m(
                                            NearDevice.loc_data_latitude,
                                            NearDevice.loc_data_longitude)
                    if distance_apart <= NEAR_DEVICE_DISTANCE:
                        Device.NearDevice = NearDevice

                    monitor_msg = ( f"Check Nearby Devices > "
                                    f"{NearDevice.fname_devicename}/"
                                    f"{format_dist_m(Device.near_device_distance)}")
                    post_monitor_msg(Device.devicename, monitor_msg)

        except Exception as err:
            post_internal_error('Update Dev in Same Loc', traceback.format_exc)


#--------------------------------------------------------------------
    def _update_restore_state_values(self, Device):
        """ Save the Device's updated sensors in the icloud3.restore_state file """

        Gb.restore_state_devices[Device.devicename] = {}
        Gb.restore_state_devices[Device.devicename]['last_update'] = datetime_now()
        Gb.restore_state_devices[Device.devicename]['sensors'] = Device.sensors
        for from_zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
            Gb.restore_state_devices[Device.devicename][f"from_zone_{from_zone}"] = DeviceFmZone.sensors

        Gb.update_restore_state_file_flag = True

#--------------------------------------------------------------------
    def _format_fname_devtype(self, Device):
        try:
            return f"{Device.fname_devtype}"
        except:
            return ''

#--------------------------------------------------------------------
    def _zone_display_as(self, zone):
        if zone in Gb.Zones_by_zone:
            Zone = Gb.Zones_by_zone[zone]
            return Zone.display_as
        else:
            return zone.title()

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
        #An update is in process, must wait until done

        wait_cnt = 0
        while self.update_in_process_flag:
            wait_cnt += 1
            if Device:
                Device.update_sensor_value(INTERVAL, (f"WAIT-{wait_cnt}"))

            time.sleep(2)

#--------------------------------------------------------------------
    def _post_before_update_monitor_msg(self, Device):
        """ Post a monitor msg for all other devices with this device's update reason """
        event_msg =(f"Trigger > {Device.icloud_update_reason}")
        for _Device in Gb.Devices:
            if _Device is Device:
                post_event(Device.devicename, event_msg)
            else:
                event_msg += (f", Device-{Device.devicename}")
                post_monitor_msg(_Device.devicename, event_msg)

#--------------------------------------------------------------------
    def _post_after_update_monitor_msg(self, Device):
        """ Post a monitor event after the update with the result """
        device_monitor_msg = (f"Device Monitor > {Device.tracking_method}, "
                            f"{Device.icloud_update_reason}, "
                            f"AttrsZone-{Device.sensor_zone}, "
                            f"LocDataZone-{Device.loc_data_zone}, "
                            f"Located-%tage, "
                            f"iOSAppGPS-{format_gps(Device.iosapp_data_latitude, Device.iosapp_data_longitude, Device.iosapp_data_gps_accuracy)}, "
                            f"iOSAppState-{Device.iosapp_data_state})")

        if Device.last_device_monitor_msg != device_monitor_msg:
            Device.last_device_monitor_msg = device_monitor_msg
            device_monitor_msg = device_monitor_msg.\
                        replace('%tage', Device.loc_data_time_age)
            post_monitor_msg(Device.devicename, device_monitor_msg)


#--------------------------------------------------------------------
    def _display_usage_counts(self, Device, force_display=False):
        try:
            total_count = Device.count_update_icloud + \
                          Device.count_update_iosapp + \
                          Device.count_discarded_update + \
                          Device.count_state_changed + \
                          Device.count_trigger_changed + \
                          Device.iosapp_request_loc_cnt

            pyi_avg_time_per_call = 0
            if Gb.pyicloud_location_update_cnt > 0:
                pyi_avg_time_per_call = Gb.pyicloud_calls_time / \
                    (Gb.pyicloud_authentication_cnt + Gb.pyicloud_location_update_cnt)

            #Verify average and counts, reset counts if average time > 1 min
            if pyi_avg_time_per_call > 60:
                pyi_avg_time_per_call           = 0
                Gb.pyicloud_calls_time          = 0
                Gb.pyicloud_authentication_cnt  = 0
                Gb.pyicloud_location_update_cnt = 0

            #If updating the devicename's info_msg, only add to the event log
            #and info_msg if the counter total is divisible by 5.
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

            if Device.tracking_method_FAMSHR_FMF:
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

#########################################################
#
#   Perform tasks on a regular time schedule
#
#########################################################
    def _timer_tasks_every_hour(self):
        for devicename, Device in Gb.Devices_by_devicename.items():
            self._display_usage_counts(Device)

#--------------------------------------------------------------------
    def _timer_tasks_midnight(self):
        for devicename, Device in Gb.Devices_by_devicename.items():
            event_msg =(f"{EVLOG_INIT_HDR}iCloud3 v{VERSION} Daily Summary > "
                        f"{dt_util.now().strftime('%A, %b %d')}")
            post_event(devicename, event_msg)

            Gb.pyicloud_authentication_cnt  = 0
            Gb.pyicloud_location_update_cnt = 0
            Gb.pyicloud_calls_time          = 0.0
            Device.initialize_usage_counters()

            # post_event(devicename, "Verifying Waze History Data Base")
            Gb.WazeHist.compress_wazehist_database()
            Gb.WazeHist.wazehist_update_track_sensor()
            if (Gb.wazehist_recalculate_time_dist_flag
                    and Gb.WazeHist):
                Gb.wazehist_recalculate_time_dist_flag = False
                Gb.WazeHist.wazehist_recalculate_time_dist(all_zones_flag=True)


#########################################################
#
#   DEVICE STATUS SUPPORT FUNCTIONS FOR GPS ACCURACY, OLD LOC DATA, ETC
#
#########################################################
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
                    Device.old_loc_poor_gps_msg = (f"OldLocation/PoorGPS (#{Device.old_loc_poor_gps_cnt})")
                elif Device.is_location_old:
                    Device.old_loc_poor_gps_msg = (f"OldLocation (#{Device.old_loc_poor_gps_cnt})")
                elif Device.is_gps_poor:
                    Device.old_loc_poor_gps_msg = (f"PoorGPS (#{Device.old_loc_poor_gps_cnt})")

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
        zone_radius    = Zone.radius
        zone_radius_accuracy = zone_radius + Gb.gps_accuracy_threshold

        info_msg = ''
        if (dist_fm_zone_m > zone_radius
                and Device.got_exit_trigger_flag is False
                and is_statzone(Zone) is False):
            if (dist_fm_zone_m < zone_radius_accuracy
                    and Device.outside_no_exit_trigger_flag == False):
                Device.outside_no_exit_trigger_flag = True
                Device.old_loc_poor_gps_cnt += 1

                info_msg = ("Outside of Zone without iOSApp `Exit Zone` Trigger, "
                            f"Keeping in Zone-{Zone.display_as} > ")
            else:
                Device.got_exit_trigger_flag = True
                info_msg = ("Outside of Zone without iOSApp `Exit Zone` Trigger "
                            f"but outside threshold, Exiting Zone-{Zone.display_as} > ")

            info_msg += (f"Distance-{format_dist(dist_fm_zone_m)}, "
                        f"RelocateDist-{format_dist(zone_radius)} "
                        f"to {format_dist(zone_radius_accuracy)}, "
                        f"Located-{Device.loc_data_time_age}")

        if Device.got_exit_trigger_flag:
            Device.outside_no_exit_trigger_flag = False

        return info_msg

#--------------------------------------------------------------------
    def _display_secs_to_next_update_info_msg(self):
        '''
        Display the secs until the next update in the next update time field.
        if between 90s to -90s. if between -90s and -120s, resisplay time
        without the age to make sure it goes away. The age may be for a non-Home
        zone but displat it in the Home zone sensor.
        '''
        try:
            for devicename, Device in Gb.Devices_by_devicename.items():
                if Device.is_tracking_paused:
                    continue

                for zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
                    age_secs = secs_to(DeviceFmZone.next_update_secs)
                    if -90 <= age_secs <= 90:
                        Device.sensors_um[NEXT_UPDATE] = f"{age_secs}s"
                        Device.update_sensors([NEXT_UPDATE])

        except Exception as err:
            log_exception(err)
            pass

#--------------------------------------------------------------------
    def _log_start_finish_update_banner(self, start_finish_char, devicename,
                method, update_reason):
        '''
        Display a banner in the log file at the start and finish of a
        device update cycle
        '''

        if Gb.log_debug_flag is False and Gb.log_rawdata_flag is False:
            return

        start_finish_chars = (f"─{start_finish_char}─")*2
        Device = Gb.Devices_by_devicename[devicename]
        log_msg =   (f"^ {method}, {devicename}, "
                    f"From-{Device.sensor_zone}, {update_reason} ^")

        log_msg2 = log_msg.replace('^', start_finish_chars).upper()
        log_debug_msg(devicename, log_msg2)


############ LAST LINE ###########