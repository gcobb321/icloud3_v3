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


from .support.event_log import EventLog
from .support.sensor    import UpdateiCloud3Sensors
from .support           import start_ic3
from .support           import iosapp_data_handler
from .support           import iosapp_interface
from .support           import pyicloud_ic3_interface
from .support           import pyicloud_ic3_data_handler
from .support           import service_handler
from .                  import determine_interval as det_interval

from .helpers.base      import (instr, round_to_zero, is_inzone_zone, is_statzone, isnot_inzone_zone,
                                post_event, post_error_msg, log_info_msg, log_error_msg,
                                post_monitor_msg, post_startup_event, post_internal_error,
                                log_debug_msg, log_info_msg, log_exception, log_rawdata,
                                _trace, _traceha, )
from .helpers.time      import (time_now_secs, secs_to_time, datetime_to_12hrtime, secs_to,
                                time_to_12hrtime, time_str_to_secs, timestamp_to_time_utcsecs,
                                secs_to_datetime, datetime_now, calculate_time_zone_offset, )
from .helpers.distance  import (calc_distance_m, calc_distance_km, )
from .helpers.format    import (format_gps, format_dist, format_dist_m, format_list,
                                format_time_age, format_age, )
from .helpers.entity_io import (get_attributes, )

TEST_DETERMINE_INTERVAL_FLAG = True
TEST_DETERMINE_INTERVAL_AFTER_ERROR_FLAG = False

from .support.pyicloud_ic3  import PyiCloudService
from .support.pyicloud_ic3  import (
        PyiCloudAPIResponseException,
        PyiCloud2SARequiredException, )


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
SERVICE_SCHEMA = vol.Schema({
    vol.Optional(CONF_COMMAND): cv.string,
    vol.Optional(CONF_DEVICENAME): cv.slugify,
    })

#Parameters for devices to be tracked
DEVICES_SCHEMA = vol.Schema({
    vol.Optional(CONF_DEVICENAME): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_EMAIL): cv.string,
    vol.Optional(CONF_TRACKING_METHOD, default=''): cv.string,
    vol.Optional(CONF_TRACK_FROM_ZONES): cv.string,
    vol.Optional(CONF_PICTURE): cv.string,
    vol.Optional(CONF_INZONE_INTERVAL): cv.string,
    vol.Optional(CONF_IOSAPP_ENTITY): cv.string,
    vol.Optional(CONF_IOSAPP_SUFFIX): cv.string,
    vol.Optional(CONF_IOSAPP_INSTALLED): cv.boolean,
    vol.Optional(CONF_DEVICE_TYPE): cv.string,
    })
    # vol.Optional(CONF_NOIOSAPP): cv.boolean,
    # vol.Optional(CONF_NO_IOSAPP): cv.boolean,

#Parameters for devices to be tracked
INZONE_INTERVALS_SCHEMA = vol.Schema({
    vol.Optional(CONF_INZONE_INTERVAL): cv.string,
    vol.Optional(IPHONE): cv.string,
    vol.Optional(IPAD): cv.string,
    vol.Optional(IPOD): cv.string,
    vol.Optional(WATCH): cv.string,
    vol.Optional(CONF_NO_IOSAPP): cv.string,
    })


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): cv.string,
    vol.Optional(CONF_TRACKING_METHOD, default=DEFAULT_TRACKING_METHOD): cv.string,
    vol.Optional(CONF_IOSAPP_REQUEST_LOC_MAX_CNT, default=DEFAULT_IOSAPP_REQUEST_LOC_MAX_CNT): cv.string,
    vol.Optional(CONF_ENTITY_REGISTRY_FILE, default=DEFAULT_ENTITY_REGISTRY_FILE): cv.string,
    vol.Optional(CONF_CONFIG_IC3_FILE_NAME, default=DEFAULT_CONFIG_IC3_FILE_NAME): cv.string,
    vol.Optional(CONF_EVENT_LOG_CARD_DIRECTORY, default=DEFAULT_EVENT_LOG_CARD_DIRECTORY): cv.string,
    vol.Optional(CONF_LEGACY_MODE, default=DEFAULT_LEGACY_MODE): cv.boolean,
    vol.Optional(CONF_DISPLAY_TEXT_AS, default=DEFAULT_DISPLAY_TEXT_AS): vol.All(cv.ensure_list, [cv.string]),

    #-----►►General Attributes ----------
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): cv.slugify,
    vol.Optional(CONF_TIME_FORMAT, default=DEFAULT_TIME_FORMAT): cv.positive_int,
    vol.Optional(CONF_INZONE_INTERVAL, default=DEFAULT_INZONE_INTERVAL): cv.string,
    vol.Optional(CONF_INZONE_INTERVALS, default=DEFAULT_INZONE_INTERVALS): vol.All(cv.ensure_list, [INZONE_INTERVALS_SCHEMA]),
    vol.Optional(CONF_DISPLAY_ZONE_FORMAT, default=DEFAULT_DISPLAY_ZONE_FORMAT): cv.string,
    vol.Optional(CONF_CENTER_IN_ZONE, default=DEFAULT_CENTER_IN_ZONE): cv.boolean,
    vol.Optional(CONF_MAX_INTERVAL, default=DEFAULT_MAX_INTERVAL): cv.string,
    vol.Optional(CONF_TRAVEL_TIME_FACTOR, default=DEFAULT_TRAVEL_TIME_FACTOR): cv.small_float,
    vol.Optional(CONF_GPS_ACCURACY_THRESHOLD, default=DEFAULT_GPS_ACCURACY_THRESHOLD): cv.positive_int,
    vol.Optional(CONF_OLD_LOCATION_THRESHOLD, default=DEFAULT_OLD_LOCATION_THRESHOLD): cv.string,
    vol.Optional(CONF_IGNORE_GPS_ACC_INZONE, default=DEFAULT_IGNORE_GPS_ACC_INZONE): cv.string,
    vol.Optional(CONF_DISCARD_POOR_GPS_INZONE, default=DEFAULT_DISCARD_POOR_GPS_INZONE): cv.boolean,
    vol.Optional(CONF_HIDE_GPS_COORDINATES, default=DEFAULT_HIDE_GPS_COORDINATES): cv.boolean,
    vol.Optional(CONF_LOG_LEVEL, default=DEFAULT_LOG_LEVEL): cv.string,

    #-----►►Filter, Include, Exclude Devices ----------
    vol.Optional(CONF_DEVICES, default=DEFAULT_DEVICES): vol.All(cv.ensure_list, [DEVICES_SCHEMA]),

    #-----►►Waze Attributes ----------
    vol.Optional(CONF_DISTANCE_METHOD, default=DEFAULT_DISTANCE_METHOD): cv.string,
    vol.Optional(CONF_WAZE_REGION, default=DEFAULT_WAZE_REGION): cv.string,
    vol.Optional(CONF_WAZE_MAX_DISTANCE, default=DEFAULT_WAZE_MAX_DISTANCE): cv.positive_int,
    vol.Optional(CONF_WAZE_MIN_DISTANCE, default=DEFAULT_WAZE_MIN_DISTANCE): cv.positive_int,
    vol.Optional(CONF_WAZE_REALTIME, default=DEFAULT_WAZE_REALTIME): cv.boolean,
    vol.Optional(CONF_WAZE_HISTORY_MAX_DISTANCE, default=DEFAULT_WAZE_HISTORY_MAX_DISTANCE): cv.positive_int,
    vol.Optional(CONF_WAZE_HISTORY_DATABASE_USED, default=DEFAULT_WAZE_HISTORY_DATABASE_USED): cv.boolean,
    vol.Optional(CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION, default=DEFAULT_WAZE_HISTORY_MAP_TRACK_DIRECTION): cv.string,

    #-----►►Other Attributes ----------
    vol.Optional('stationary_inzone_interval', default=DEFAULT_STATIONARY_INZONE_INTERVAL): cv.string,
    vol.Optional('stationary_still_time', default=DEFAULT_STATIONARY_STILL_TIME): cv.string,
    vol.Optional('stationary_zone_offset', default=DEFAULT_STATIONARY_ZONE_OFFSET): cv.string,
    vol.Optional(CONF_CREATE_SENSORS, default=DEFAULT_CREATE_SENSORS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_EXCLUDE_SENSORS, default=DEFAULT_EXCLUDE_SENSORS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_COMMAND, default=DEFAULT_COMMAND): cv.string,
})

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   CREATE THE ICLOUD3 DEVICE TRACKER PLATFORM
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
def setup_scanner(hass, config: dict, see, discovery_info=None):

    Gb.version = VERSION

    log_msg =(f"Setting up iCloud3 v{VERSION} device tracker")
    log_info_msg(log_msg)

    Gb.iCloud3 = iCloud3(hass, see, config)

    Gb.hass.services.register(DOMAIN, 'action',
                service_handler.process_update_service_request, schema=SERVICE_SCHEMA)
    Gb.hass.services.register(DOMAIN, 'config',
                # iCloud3.update_configuration_parameters_handler())
                service_handler.process_update_icloud3_configuration_request)
    Gb.hass.services.register(DOMAIN, 'restart',
                service_handler.process_restart_icloud3_service_request, schema=SERVICE_SCHEMA)
    Gb.hass.services.register(DOMAIN, 'find_iphone_alert',
                service_handler.process_find_iphone_alert_service_request, schema=SERVICE_SCHEMA)

    # Tells the bootstrapper that the component was successfully initialized
    return True


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3:
    """Representation of an iCloud3 platform"""

    def __init__(self, hass, see, ha_config_yaml_parms):

        """Initialize the iCloud3 device tracker."""
        # Gb.hass = hass
        Gb.see  = see

        start_ic3.load_ha_config_parameters(ha_config_yaml_parms)

        Gb.hass_configurator_request_id = {}
        Gb.version                = VERSION
        Gb.attrs[ICLOUD3_VERSION] = VERSION

        # Initialize Global Variables
        Gb.EvLog    = EventLog(Gb.hass)
        Gb.PyiCloud = None
        Gb.Sensors  = UpdateiCloud3Sensors()

        Gb.start_icloud3_request_flag   = False
        Gb.start_icloud3_inprocess_flag = False

        self.polling_5_sec_loop_running  = False
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
        self.start_icloud3_initial_load_flag = False
        self.any_device_being_updated_flag   = False
        self.update_in_process               = False

        self.attributes_initialized_flag = False
        self.e_seconds_local_offset_secs = 0

        #initialize variables configuration.yaml parameters
        start_ic3.set_global_variables_from_conf_parameters(evlog_msg=False)

        Gb.start_icloud3_initial_load_flag = True

        self._start_icloud3()

        Gb.start_icloud3_initial_load_flag = False

#--------------------------------------------------------------------
    @property
    def signal_device_new(self) -> str:
        """Event specific per Freebox entry to signal new device."""
        return f"{DOMAIN}-device-new"

    @property
    def signal_device_update(self) -> str:
        """Event specific per Freebox entry to signal updates in devices."""
        return f"{DOMAIN}-device-update"

#--------------------------------------------------------------------
    def _start_icloud3(self):
        """
        Start iCloud3, Define all variables & tables, Initialize devices
        """
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

            if Gb.devices == []:
                log_error_msg("iCloud3 Aborted > No Devices have been specified in the "
                                "iCloud3 configuration parameters.")
                return False

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

            start_ic3.set_global_variables_from_conf_parameters()
            calculate_time_zone_offset()

            start_ic3.create_Zones_object()
            start_ic3.create_Waze_object()

        except Exception as err:
            log_exception(err)

        #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        try:
            post_event(f"{EVLOG_INIT_HDR}Stage 2 > Set up Tracked Devices")
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
            # dispatcher_send(Gb.hass, self.signal_device_update)
            # dispatcher_send(Gb.hass, self.signal_device_new)
            Gb.WazeHist.load_track_from_zone_table()

        except Exception as err:
            log_exception(err)

        #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        try:
            post_event(f"{EVLOG_INIT_HDR}Stage 3 > Set up Tracking Methods")
            Gb.EvLog.update_event_log_display("")

            if Gb.tracking_method_use_icloud:
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

            if Gb.tracking_method_use_iosapp:
                start_ic3.setup_tracked_devices_for_iosapp()
            else:
                event_msg = 'iOS App is not being used to locate devices'
                post_event(event_msg)

        except Exception as err:
            log_exception(err)

        #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        try:
            post_event(f"{EVLOG_INIT_HDR}Stage 4 > Configure Tracked Devices")
            Gb.EvLog.update_event_log_display("")

            # Finish setting up the Event Log Sensor now that the devices have been set up
            start_ic3.remove_unverified_untrackable_devices()
            Gb.EvLog.setup_event_log()

            # Nothing to do if no devices to track
            if len(Gb.Devices_by_devicename) == 0:
                event_msg =(f"iCloud3 Error > Setup aborted, no devices to track. "
                    f"Verify the devicename on the `devices/device_name: [devicename]` parameters. "
                    f"They must be the same as `Settings > General > About > Name` "
                    f"on the phones being tracked.")
                post_event(event_msg)

                Gb.EvLog.update_event_log_display("")
                Gb.start_icloud3_inprocess_flag = False
                return False

            start_ic3.setup_trackable_devices()

            for devicename, Device in Gb.Devices_by_devicename.items():
                try:
                    self._update_device_trkr_entity_attrs(Device)

                    Gb.Sensors.update_device_sensors(Device, Device.kwargs)
                    Gb.Sensors.update_device_sensors(Device, Device.attrs)
                    Gb.Sensors.update_device_sensors(Device, Device.DeviceFmZoneHome.attrs)

                except:
                    pass

            start_ic3.display_object_lists()

        except Exception as err:
            log_exception(err)

        start_ic3.display_platform_operating_mode_msg()
        start_ic3.post_restart_icloud3_complete_msg()

        #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

        if Gb.log_debug_flag is False:
            Gb.startup_log_msgs = (NEW_LINE + '-'*55 +
                                    Gb.startup_log_msgs.replace(CRLF, NEW_LINE) +
                                    NEW_LINE + '-'*55)
            log_info_msg(Gb.startup_log_msgs)
        Gb.startup_log_msgs = ''

        if self.polling_5_sec_loop_running is False:
            self.polling_5_sec_loop_running = True
            track_utc_time_change(Gb.hass, self._polling_loop_5_sec_device,
                    second=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])

        Gb.start_icloud3_inprocess_flag = False
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
    def _polling_loop_5_sec_device(self, now):
        try:
            if Gb.config_flow_update_control != {''}:
                start_ic3.process_conf_flow_parameter_updates()

            if Gb.start_icloud3_request_flag:    #via service call
                self._start_icloud3()
                Gb.start_icloud3_request_flag = False

            if (Gb.any_device_being_updated_flag
                    or Gb.start_icloud3_inprocess_flag):
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

            #-----------------------------------------------------------------------------
            # iOSApp Device loop
            #-----------------------------------------------------------------------------
            for devicename, Device in Gb.Devices_by_devicename.items():
                if Gb.tracking_method_use_iosapp is False:
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
                _traceha(f"512 iosloop {devicename} {Device.iosapp_data_updated_flag=}")
                # Turn off monitoring the iOSApp if excessive errors
                if Device.iosapp_data_invalid_error_cnt > 120:
                    _trace(f"iosapp errCnt-exceeded/reset {devicename}, {Device.iosapp_data_invalid_error_cnt}")
                    Device.iosapp_data_invalid_error_cnt = 0
                    Device.iosapp_monitor_flag = False
                    event_msg =("iCloud3 Error > iOSApp entity error cnt exceeded, "
                                "iOSApp monitoring stopped. iCloud monitoring will be used.")
                    post_event(Device.devicename, event_msg)
                    continue

                # The iosapp may be entering or exiting another Device's Stat Zone. If so,
                # reset the iosapp information to this Device's Stat Zone and continue.
                if Device.iosapp_data_updated_flag:
                    Device.iosapp_data_invalid_error_cnt = 0

                    event_msg =(f"Trigger > {Device.iosapp_data_change_reason}")
                    post_event(Device.devicename, event_msg)

                    iosapp_data_handler.check_enter_exit_stationary_zone(Device)

                    self._update_device_iosapp(Device, Device.iosapp_data_change_reason)

                # Send a location request every 6-hours
                iosapp_data_handler.check_if_iosapp_is_alive(Device)

            #-----------------------------------------------------------------------------
            # iCloud Device Loop
            #-----------------------------------------------------------------------------
            for devicename, Device in Gb.Devices_by_devicename.items():
                save_device_icloud_initial_locate_done = Device.icloud_initial_locate_done
                Device.check_device_update_qualification()
                _traceha(f"544 iclloop {devicename} {Device.icloud_update_flag=}")
                if Device.icloud_update_flag is False:
                    continue

                Device.calculate_old_location_threshold()
                Device.check_icloud_loc_data_change_needed()
                _traceha(f"550 iclloop {devicename} {Device.icloud_update_flag=}")

                if Device.icloud_update_flag is False:
                    continue

                # Updating device info. Get data from FmF or FamShr
                pyicloud_ic3_data_handler.request_icloud_data_update(Device)
                _traceha(f"557 iclloop {devicename} {Device.icloud_update_flag=}")

                if Device.icloud_update_flag:
                    Gb.icloud_no_data_error_cnt = 0

                else:
                    # An error ocurred accessing the iCloud account. This can be a
                    # Authentication error or an error retrieving the loction data
                    Gb.icloud_no_data_error_cnt += 1

                    if Device.icloud_initial_locate_done is False:
                        error_msg = "Retrying Initial Locate"
                    else:
                        error_msg = "iCloud is Offline (Authentication or Location Error)"

                    det_interval.determine_interval_after_error(
                                                Device,
                                                error_msg,
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

            #-----------------------------------------------------------------------------
            # Update Location data and post results loop
            #-----------------------------------------------------------------------------
            for devicename, Device in Gb.Devices_by_devicename.items():
                _traceha(f"592 updateloop {devicename} {Device.icloud_update_flag=} {Device.iosapp_data_updated_flag=}")
                if (Device.icloud_update_flag is False
                        and Device.iosapp_data_updated_flag is False):
                    continue
                # _traceha(f"593 devloop{devicename} {Device.icloud_update_flag=} {Device.iosapp_data_updated_flag=}")
                # Post a monitor msg for all other devices with this device's update reason
                event_msg =(f"Trigger > {Device.icloud_update_reason}")
                for _Device in Gb.Devices:
                    if _Device is Device:
                        post_event(devicename, event_msg)
                    else:
                        event_msg += (f", Device-{devicename}")
                        post_monitor_msg(_Device.devicename, event_msg)

                update_reason = Device.icloud_update_reason.split('>')[0]

                # Update the Device tracking information
                self._update_device_icloud(update_reason, Device)

                device_monitor_msg = (f"Device Monitor > {Device.tracking_method}, "
                                    f"{Device.icloud_update_reason}, "
                                    f"AttrsZone-{Device.attrs_zone}, "
                                    f"LocDataZone-{Device.loc_data_zone}, "
                                    f"Located-%tage, "
                                    f"iOSAppGPS-{format_gps(Device.iosapp_data_latitude, Device.iosapp_data_longitude, Device.iosapp_data_gps_accuracy)}, "
                                    f"iOSAppState-{Device.iosapp_data_state})")

                if Device.last_device_monitor_msg != device_monitor_msg:
                    Device.last_device_monitor_msg = device_monitor_msg
                    device_monitor_msg = device_monitor_msg.\
                                replace('%tage', Device.loc_data_time_age)
                    post_monitor_msg(devicename, device_monitor_msg)

                Device.device_being_updated_flag = False
                self.update_in_process_flag      = False

            Gb.any_device_being_updated_flag = False

            #If less than 90 secs to the next update for any devicename:zone, display time to
            #the next update in the NextUpdt time field, e.g, 1m05s or 0m15s.
            self._display_secs_to_next_update_info_msg()

            #End devicename in self.tracked_devices loop

        except Exception as err:
            log_exception(err)
            log_msg = (f"Device Update Error, Error-{ValueError}")
            post_error_msg(log_msg)

        self.update_in_process_flag     = False

        if (Gb.Devices_by_devicename
                and self.initial_locate_complete_flag == False):
            self.initial_locate_complete_flag = True


#########################################################
#
#   Update the device on a state or trigger change was received from the ios app
#
#########################################################
    def _update_device_iosapp(self, Device, update_reason):
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
                do_not_update_flag = False
                if (Device.iosapp_data_isold
                        and Device.next_update_time_reached):
                    Device.old_loc_poor_gps_cnt += 1
                    info_msg =  (f"OldLocation (#{Device.old_loc_poor_gps_cnt})")
                                # f"-{format_time_age(Device.iosapp_data_secs)}")
                    do_not_update_flag = True

                if do_not_update_flag:
                    iosapp_interface.request_location(Device)
                    # Do not update Device attrs and sensors if old location, poor gps etc.
                    # Update interval & next_update_time values and sensors only to retry getting
                    # good data.
                    det_interval.determine_interval_after_error(
                                                Device,
                                                info_msg,
                                                counter=OLD_LOC_POOR_GPS_CNT)

                else:
                    Device.update_dev_loc_data_from_raw_data(IOSAPP)

                    # Update the device's tracking information, attributes and sensors
                    self._update_device_tracker_and_sensors(Device)

                event_msg =(f"{EVLOG_UPDATE_END}iOSApp update completed")
                post_event(devicename, event_msg)

                if (Gb.EvLog.last_devicename in ["", devicename]):
                        # and (Device.count_update_iosapp == 0
                    Gb.EvLog.update_event_log_display(devicename)

                self._log_start_finish_update_banner('↑↑', devicename, "iOSApp", "gen update")

                if Device.is_location_gps_good:
                    Device.count_update_iosapp += 1

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
    def _update_device_icloud(self, update_reason='Check iCloud', Device=None):

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

            self._log_start_finish_update_banner('↓↓', devicename, "iCloud", update_reason)

            Device.update_timer = time_now_secs()
            Device.iosapp_request_loc_sent_secs = 0

            det_interval.post_zone_time_dist_event_msg(Device, Device.DeviceFmZoneHome)

            Device.calculate_old_location_threshold()

            #icloud data overrules device data which may be stale
            latitude     = Device.loc_data_latitude
            longitude    = Device.loc_data_longitude
            gps_accuracy = 0

            if latitude != 0 and longitude != 0:
                self._check_old_loc_poor_gps(Device)

            #Discard if no location coordinates
            do_not_update_flag = False
            if latitude == 0 or longitude == 0:
                do_not_update_flag = True

            #Check to see if currently in a zone. If so, check the zone distance.
            #If new location is outside of the zone and inside radius*4, discard
            #by treating it as poor GPS
            elif (isnot_inzone_zone(zone)
                    or Device.attrs_zone == NOT_SET):
                Device.outside_no_exit_trigger_flag = False
                info_msg= ''

            else:
                info_msg = self._is_outside_zone_no_exit(Device, zone, '', latitude, longitude)

            #Ignore old location when in a zone and discard=False
            #let normal next time update check process
            if (Device.is_location_old_or_gps_poor
                    and Device.is_inzone
                    and Device.outside_no_exit_trigger_flag is False
                    and Gb.discard_poor_gps_inzone_flag is False):
                    # and Gb.ignore_gps_accuracy_inzone_flag):
                Device.old_loc_poor_gps_cnt -= 1
                Device.old_loc_poor_gps_msg = ''

                event_msg =(f"Old Loc/Poor GPS exception (will process) > "
                            f"DiscardPoorGPSinZone=False, inZone=True, "
                            f"NextUpdate-{Device.DeviceFmZoneHome.next_update_time}, "
                            f"(Not reached), "
                            f"GPS-{format_gps(latitude, longitude, gps_accuracy)}, "
                            f"LocationTime-{Device.loc_data_time_age}")
                post_event(devicename, event_msg)

            elif Device.is_offline:
                do_not_update_flag = True
                info_msg = "Device Offline"

                event_msg =(f"Device Status Exception, Tracking may be delayed > {devicename} "
                            f"Status-{Device.dev_data_device_status}")
                post_event(devicename, event_msg)

            #Outside zone, no exit trigger check
            elif (Device.iosapp_monitor_flag
                    and Device.outside_no_exit_trigger_flag):
                # Device.loc_data_ispoorgps = True
                info_msg = "Outside of zone without iOSApp `Exit Zone` Trigger"
                do_not_update_flag = True

            #Discard if location is old and next update time has been reached
            elif (Device.is_location_old_or_gps_poor
                    and Device.next_update_time_reached):
                info_msg = (f"{Device.old_loc_poor_gps_msg}")
                do_not_update_flag = True

            if do_not_update_flag:
                # Do not update Device attrs and sensors if old location, poor gps etc.
                # Update interval & next_update_time values and sensors only to retry getting
                # good data.
                det_interval.determine_interval_after_error(
                                                Device,
                                                info_msg,
                                                counter=OLD_LOC_POOR_GPS_CNT)

                self._log_start_finish_update_banner('↓↓', devicename, "iCloud", update_reason)
            else:
                # Update all tracking attributes for the device
                self._update_device_tracker_and_sensors(Device)

                event_msg =(f"{EVLOG_UPDATE_END}{Device.tracking_method_fname} update completed")
                if Device.tracking_method_fname != Device.dev_data_source:
                    event_msg += (f" > Used {Device.dev_data_source} Data")
                post_event(devicename, event_msg)

            if (Gb.EvLog.last_devicename in ["", devicename]):
                    # and (Device.count_update_icloud == 0
                Gb.EvLog.update_event_log_display(devicename)

            self._log_start_finish_update_banner('↑↑', devicename, "iCloud", "gen update")

            if Device.is_location_gps_good:
                Device.count_update_icloud += 1

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
    def _update_device_tracker_and_sensors(self, Device):
        try:
            devicename  = Device.devicename

            Device.post_location_data_event_msg('Location Data')

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
            # Update the device's zone/away status
            Device.get_zone(display_zone_msg=True)

            calc_dist_last_poll_moved_km = calc_distance_km(
                                        Device.attrs[LATITUDE],
                                        Device.attrs[LONGITUDE],
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
                    Device.get_zone(display_zone_msg=True)

        except Exception as err:
            post_internal_error('Update Stat Zone', traceback.format_exc)

        try:
            # Update the devices that are near each other
            self._update_devices_in_same_location()

            # Cycle thru each Track From Zone get the interval and all other data
            devicename = Device.devicename
            for from_zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
                self._log_start_finish_update_banner('↓↓', devicename,
                                Device.tracking_method_fname, from_zone)

                # See if this Device is near another Device. If it is, use the near Device's
                # determine_interval results instead of recalculating everything.
                near_device_attrs_used_flag = False
                if Device.is_near_another_device:
                    NearDevice = Device.NearDevice
                    if from_zone in NearDevice.DeviceFmZones_by_zone:
                        NearDeviceFmZone            = NearDevice.DeviceFmZones_by_zone[from_zone]
                        Device.DeviceFmZoneCurrent  = DeviceFmZone
                        near_device_attrs_used_flag = True
                        event_msg =(f"Using Nearby Device > "
                                    f"{NearDevice.fname_devicename}/"
                                    f"{format_dist_m(Device.near_device_distance)}")
                        post_event(Device.devicename, event_msg)

                        attrs = det_interval.copy_near_device_results(Device, DeviceFmZone, NearDevice, NearDeviceFmZone)

                # Determine the interval and update times e for the track_from_zones for this Device
                if near_device_attrs_used_flag is False:
                    attrs = det_interval.determine_interval(Device, DeviceFmZone)

                # Update all the sensors with the interval and times for this track_from_zone.
                if attrs != {}:
                    Gb.Sensors.update_device_sensors(Device, attrs, DeviceFmZone)

                self._log_start_finish_update_banner('↑↑', devicename,
                            Device.tracking_method_fname, from_zone)

        except Exception as err:
            post_internal_error('Det IntervalLoop', traceback.format_exc)
            return False

        try:
            #Note: Final prep and update device attributes via
            #device_tracker.see. The gps location, battery, and
            #gps accuracy are not part of the attrs variable and are
            #reformatted into device attributes by 'See'. The gps
            #location goes to 'See' as a "(latitude, longitude)" pair.
            #'See' converts them to LATITUDE and LONGITUDE
            #and discards the 'gps' item.

            Device.StatZone.update_stationary_zone_location()

            if Device.loc_data_zone != Device.attrs_zone:
                Device.attrs[LAST_ZONE]      = Device.attrs[ZONE]
                Device.attrs[INTO_ZONE_DATETIME] = Device.into_zone_datetime

            Device.attrs[LOCATION_SOURCE]    = Device.dev_data_source
            Device.attrs[BATTERY]            = Device.dev_data_battery_level
            Device.attrs[BATTERY_STATUS]     = Device.dev_data_battery_status
            Device.attrs[DEVICE_STATUS]      = Device.dev_data_device_status
            Device.attrs[LOW_POWER_MODE]     = Device.dev_data_low_power_mode
            Device.attrs[POLL_COUNT]         = Device.poll_count

            Device.attrs[ZONE]               = Device.loc_data_zone
            Device.attrs[LATITUDE]           = Device.loc_data_latitude
            Device.attrs[LONGITUDE]          = Device.loc_data_longitude
            Device.attrs[GPS_ACCURACY]       = Device.loc_data_gps_accuracy
            Device.attrs[LOCATED_DATETIME]   = Device.loc_data_datetime
            Device.attrs[ALTITUDE]           = Device.loc_data_altitude
            Device.attrs[VERT_ACCURACY]      = Device.loc_data_vert_accuracy

            Device.attrs_located_secs   = Device.loc_data_secs

            Gb.Sensors.update_device_sensors(Device, Device.attrs)

        except Exception as err:
            post_internal_error('Set Attributes', traceback.format_exc)

        try:
            Device.kwargs[BATTERY]        = Device.dev_data_battery_level
            Device.kwargs[GPS_ACCURACY]   = Device.loc_data_gps_accuracy

            self._setup_base_kwargs(Device,
                                    Device.attrs[LATITUDE],
                                    Device.attrs[LONGITUDE])
            self._update_device_trkr_entity_attrs(Device)

            Device.device_being_updated_flag = False

        except Exception as err:
            log_msg = (f"{self._format_fname_devtype(devicename)} Error Updating Device, {err}")
            post_error_msg(log_msg)

            log_exception(err)

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
    def _update_device_trkr_entity_attrs(self, Device, attrs=None):
        """
        The Device attributes now contain the device's location, update times, zone
        information, distances, etc. Use the HA 'see' platform function to update
        the device_tracker.[devicename] entity and all it's attributes.
        """
        try:
            zone = Device.loc_data_zone
            Zone = Gb.Zones_by_zone[zone]
            ZoneAttrs = Gb.Zones_by_zone[Device.attrs_zone]

            #The current zone is based on location of the device after it is looked
            #up in the zone tables.
            #The ic3dev_state is from the original trigger value when the poll started.
            #If the device went from one zone to another zone, an enter/exit trigger
            #may not have been issued. If the trigger was the next update time
            #reached, the ic3dev_state and zone many now not match. (v2.0.2)
            if Device.attrs_zone == NOT_SET and Device.attrs[LATITUDE] == 0:
                pass
            elif zone == NOT_SET or zone == '':
                pass
            elif Device.attrs_zone == STATIONARY and is_statzone(zone):
                pass

            #If state is 'stationary' and in another zone, reset the state to the
            #current zone that was based on the device location.
            #If the state is in a zone but not the current zone, change the state
            #to the current zone that was based on the device location.
            elif ((Device.attrs_zone == STATIONARY
                        and is_inzone_zone(zone))
                    or (is_inzone_zone(Device.attrs_zone)
                        and is_inzone_zone(zone)
                        and Device.attrs_zone != zone)):
                if (self._is_overlapping_zone(Device.attrs_zone, zone) is False
                        and Device.attrs_zone != NOT_SET):

                    event_msg =(f"Stationary Zone mismatch > "
                                f"Resetting Zone, ({ZoneAttrs.display_as})"
                                f"{RARROW}({Zone.display_as})")
                    post_event(Device.devicename, event_msg)
                Device.attrs[ZONE] = zone

            #Calculate and display how long the update took
            if Device.dev_data_source == IOSAPP_FNAME:
                new_trigger = (f"{Device.iosapp_data_trigger}@{Device.iosapp_data_trigger_time}")
            else:
                new_trigger = (f"{Device.dev_data_source}@{Device.loc_data_datetime[11:19]}")

            Device.trigger                  = new_trigger
            Device.attrs[TRIGGER]           = new_trigger
            Device.attrs[UPDATE_DATETIME]   = datetime_now()
            if attrs is None:
                attrs = dict(Device.attrs, **Gb.attrs)

            # Update sensor.<devicename>_last_update_trigger if IOS App detected
            # and iCloud3 has been running for at least 10 secs to let HA &
            # mobile_app start up to avoid error if iC3 loads before the mobile_app
            kwargs                     = dict(Device.kwargs)
            kwargs[ATTRIBUTES]         = attrs
            kwargs[DEVTRK_STATE_VALUE] = self._zone_display_as(Device.attrs_zone)

            if Gb.log_rawdata_flag:
                log_rawdata(f"Update HA Device Tracker Entity - <{Device.devicename}>", kwargs)
                log_rawdata(f"Update HA Device Tracker Entity - <{Device.devicename}>", attrs)

            Gb.see(**kwargs)

            if Device.attrs[UPDATE_DATETIME] == DATETIME_ZERO:   #Bypass if not initialized
                return

            retry_cnt = 1
            update_datetime = Device.attrs[UPDATE_DATETIME]      # Time only, Strip off date

            #Quite often, the attribute update has not actually taken
            #before other code is executed and errors occur.
            #Reread the attributes of the ones just updated to make sure they
            #were updated corectly. Verify by comparing the timestamps. If
            #differet, retry the attribute update. HA runs in multiple threads.
            try:
                entity_id = Device.device_tracker_entity_ic3
                while retry_cnt < 99:
                    chk_see_attrs  = get_attributes(entity_id)
                    try:
                        chk_update_datetime = chk_see_attrs[UPDATE_DATETIME]
                        if update_datetime == chk_update_datetime:
                            break
                    except Exception as err:
                        pass

                    if (retry_cnt % 10) == 0:
                        time.sleep(1)
                    retry_cnt += 1

                    Gb.see(**kwargs)

            except Exception as err:
                #pass
                log_exception(err)

        except Exception as err:
            #pass
            log_exception(err)

        return

#--------------------------------------------------------------------
    def _setup_base_kwargs(self, Device, latitude, longitude):

        devicename = Device.devicename
        zone_name    = Device.loc_data_zone

        #if in zone, replace lat/long with zone center lat/long
        if is_inzone_zone(Device.attrs_zone):
            zone_name = self._format_zone_name(devicename, Device.attrs_zone)

        Zone = Gb.Zones_by_zone[zone_name]

        # debug_msg=(f"SETUP BASE KWARGS zone_name-{zone_name}, "
        #             f"inzone-state-{is_inzone_zone(Device.attrs_zone)}")
        # log_debug_msg(devicename, debug_msg)

        if zone_name and is_inzone_zone(Device.attrs_zone):
            zone_lat  = Zone.latitude
            zone_long = Zone.longitude
            zone_dist = Zone.distance_m(latitude, longitude)

            # debug_msg=(f"zone_lat/long=({zone_lat}, {zone_long}), "
            #         f"lat-long=({latitude}, {longitude}), "
            #         f"zone_dist-{zone_dist}, "
            #         f"zone-radius-{Zone.radius_km}")
            # log_debug_msg(devicename, debug_msg)

            #Move center of stationary zone to new location if more than 10m from old loc
            if (is_statzone(zone_name)
                    and Zone.radius == 1
                    and zone_dist > 10):
                Device.stat_zone_update_control = STAT_ZONE_MOVE_DEVICE_INTO

            #inside zone, move to center
            elif (Gb.center_in_zone_flag
                    and zone_dist <= Zone.radius
                    and (latitude != zone_lat or longitude != zone_long)):
                event_msg =(f"Moving to zone center > {zone_name}, "
                            f"GPS-{format_gps(latitude, longitude, Device.loc_data_gps_accuracy, zone_lat, zone_long)}, "
                            f"Distance-{format_dist_m(zone_dist)}")
                post_event(devicename, event_msg)
                log_debug_msg(devicename, event_msg)

                latitude  = zone_lat
                longitude = zone_long
                Device.loc_data_latitude  = zone_lat
                Device.loc_data_longitude = zone_long

        gps_lat_long              = (latitude, longitude)
        kwargs                    = {}
        kwargs['gps']             = gps_lat_long
        kwargs[BATTERY]           = Device.dev_data_battery_level
        kwargs[GPS_ACCURACY]      = Device.loc_data_gps_accuracy

        Device.kwargs[GPS]        = (latitude, longitude)
        Device.attrs[LATITUDE]   = latitude
        Device.attrs[LONGITUDE]  = longitude

        return kwargs

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
                attrs = {}
                attrs[INTERVAL] = (f"WAIT-{wait_cnt}")
                Gb.Sensors.update_device_sensors(Device, attrs)

            time.sleep(2)

#--------------------------------------------------------------------
    def _update_device_sensors(self, Device, attrs:dict, DeviceFmZone=None):
        '''
        Update/Create sensor for the device attributes.

        Input:
            Device.       Device or DeviceFmZone ifupdatine non-Home zone info
            attrs:        attributes to be updated

            sensor_device_attrs = ['distance', 'calc_distance', 'waze_distance',
                        'travel_time', 'dir_of_travel', 'interval', 'info',
                        'last_located', 'last_update', 'next_update',
                        'poll_count', 'trigger', 'battery', 'battery_state',
                        'gps_accuracy', 'zone', LAST_ZONE, 'travel_distance']

            sensor_attrs_format = {'distance': 'dist', 'calc_distance': 'dist',
                        'travel_distance': 'dist', 'battery': '%',
                        'dir_of_travel': 'title'}
        '''

        Gb.Sensors.update_device_sensors(Device, attrs, DeviceFmZone)

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

            post_event(devicename, "Verifying Waze History Data Base")
            Gb.WazeHist.wazehist_db_maintenance()
            Gb.WazeHist.wazehist_db_update_map_gps_sensor()


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
                or Device.attrs_zone == NOT_SET
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
                for zone, DeviceFmZone in Device.DeviceFmZones_by_zone.items():
                    age_secs = secs_to(DeviceFmZone.next_update_secs)
                    info_msg = (f"{secs_to_datetime(DeviceFmZone.next_update_secs)}")

                    if  -90 <= age_secs <= 90:
                        info_msg += (f"-{age_secs}s")

                    if -120 < age_secs <= 90:
                        attrs = {}
                        attrs[NEXT_UPDATE_TIME] = info_msg
                        Gb.Sensors.update_device_sensors(Device, attrs)

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
                    f"From-{Device.attrs_zone}, {update_reason} ^")

        log_msg2 = log_msg.replace('^', start_finish_chars).upper()
        log_debug_msg(devicename, log_msg2)

#--------------------------------------------------------------------
    def update_configuration_parameters_handler(self):
        post_event("Edit Configuration handler called")

        try:
            _traceha(f"to OFH {Gb.config_entry.data=} {Gb.config_entry.unique_id=}")
            # Gb.OptionsFlowHandler.async_step_init()
            # OFH = Gb.hass.async_add_executor_job(Gb.OptionsFlowHandler)
            # return OFH.__init__()
            # _traceha(f"fm OFH {Gb.OptionsFlowHandler=}")


            # Gb.hass.add_job(Gb.OptionsFlowHandler.async_step_init())

            Gb.hass.add_job(
                Gb.hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={"source": 'init'},
                        data={
                            **Gb.config_entry.data,
                            "unique_id": Gb.config_entry.unique_id,
                        },
                    )
                )

        except Exception as err:
            log_exception(err)

############ LAST LINE ###########