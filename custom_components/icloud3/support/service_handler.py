#########################################################
#
#   ICLOUD SERVICE HANDLER MODULE
#
#########################################################
from ..globals          import GlobalVariables as Gb
from ..const_general    import (HHMMSS_ZERO,
                                WAZE, WAZE_NOT_USED, WAZE_USED, WAZE_PAUSED, )
                                # CMD_PAUSE, CMD_RESUME, CMD_REQUEST_LOCATION, CMD_ERROR, CMD_INTERVAL, CMD_WAZE,
                                # CMD_RESET_PYICLOUD_SESSION,
                                # CMD_EXPORT_EVENT_LOG, CMD_DISPLAY_STARTUP_EVENTS, CMD_RESET_PYICLOUD_SESSION,
                                # CMD_LOG_LEVEL, CMD_REFRESH_EVENT_LOG, CMD_RESTART, CMD_LOG_LEVEL, CMD_FIND_DEVICE_ALERT,
                                # CMD_WAZEHIST_DB_MAINTENANCE, CMD_WAZEHIST_DB_GPS_SENSOR_FOR_MAP, )
from ..const_attrs      import (LOCATION, HIGH_INTEGER, CONF_ZONE, NEXT_UPDATE_TIME, )

from ..helpers.base     import (instr,
                                post_event, post_error_msg, post_log_info_msg, post_monitor_msg,
                                log_debug_msg, log_exception, _trace, _traceha, )
from ..helpers.time     import (time_to_secs, time_str_to_secs, )
from ..support          import iosapp as iosapp

import homeassistant.util.dt as dt_util

# EvLog Action Commands
CMD_ERROR                  = 'error'
CMD_INTERVAL               = 'interval'
CMD_PAUSE                  = 'pause'
CMD_RESUME                 = 'resume'
CMD_WAZE                   = 'waze'
CMD_REQUEST_LOCATION       = 'location'
CMD_EXPORT_EVENT_LOG       = 'export_event_log'
CMD_WAZEHIST_DB_MAINTENANCE= 'wazehist_maint'
CMD_WAZEHIST_DB_MAP_GPS_SENSOR = 'wazehist_map_gps_sensor'
CMD_DISPLAY_STARTUP_EVENTS = 'startuplog'
CMD_RESET_PYICLOUD_SESSION = 'reset_session'
CMD_LOG_LEVEL              = 'log_level'
CMD_REFRESH_EVENT_LOG      = 'refresh_event_log'
CMD_RESTART                = 'restart'
CMD_FIND_DEVICE_ALERT      = 'find_alert'


GLOBAL_ACTIONS =  [CMD_EXPORT_EVENT_LOG,
                    CMD_DISPLAY_STARTUP_EVENTS,
                    CMD_RESET_PYICLOUD_SESSION,
                    CMD_WAZE,
                    CMD_REFRESH_EVENT_LOG,
                    CMD_RESTART,
                    CMD_LOG_LEVEL,
                    CMD_WAZEHIST_DB_MAINTENANCE,
                    CMD_WAZEHIST_DB_MAP_GPS_SENSOR, ]
DEVICE_ACTIONS =  [CMD_REQUEST_LOCATION,
                    CMD_PAUSE,
                    CMD_RESUME,
                    CMD_FIND_DEVICE_ALERT, ]

from   homeassistant.util.location import distance

#--------------------------------------------------------------------
def update_service_handler(devicename=None, action=None):
    """
    Authenticate against iCloud and scan for devices.


    Actions:
    - waze reset range = reset the min-max range to defaults (1-1000)
    - waze toggle      = toggle waze on or off
    - pause            = stop polling for the devicename or all devices
    - resume           = resume polling devicename or all devices, reset
                            the interval override to normal interval
                            calculations
    - pause-resume     = same as above but toggles between pause and resume
    - zone xxxx        = updates the devie state to xxxx and updates all
                            of the iloud3 attributes. This does the see
                            service call and then an update.
    - reset            = reset everything and rescans all of the devices
    - debug interval   = displays the interval formula being used
    - debug gps        = simulates bad gps accuracy
    - debug old        = simulates that the location informaiton is old
    - info xxx         = the same as 'debug'
    - location         = request location update from ios app
    """

    post_monitor_msg(f"Service Call Action Received > {devicename}, Action-{action}")

    action        = action.replace(f"{CONF_ZONE} ", f"{CONF_ZONE}:")
    action        = action.replace(f"{WAZE} ", f"{WAZE}:")
    action        = action.replace(' ', '')
    action_parts  = action.split(':')
    action        = action_parts[0]
    try:
        action_option = action_parts[1]
    except:
        action_option = ''

    msg_devicename = (f", Device-{devicename}") if devicename else ""
    event_msg =(f"iCloud3 Action Handler > Command-{action}:{action_option}{msg_devicename}")
    post_event(event_msg)

    if action in GLOBAL_ACTIONS:
        _handle_global_action(action, action_option)

    else:
        for Device in Gb.Devices_by_devicename.values():   #
            if devicename and Device.devicename != devicename:
                continue

            info_msg = None
            if action == CMD_PAUSE:
                Device.pause_tracking

            elif action == CMD_RESUME:
                Device.resume_tracking
                # _handle_action_device_resume(Device)

            elif action == LOCATION:
                _handle_action_device_location(Device)

            else:
                info_msg = (f"INVALID ACTION > {action}")
                Device.display_info_msg( info_msg)

    Gb.EvLog.update_event_log_display(devicename)

#--------------------------------------------------------------------
def setinterval_service_handler(arg_interval=None, arg_devicename=None):

    """
    Set the interval or process the action action of the given devices.
        'interval' has the following options:
            - 15               = 15 minutes
            - 15 min           = 15 minutes
            - 15 sec           = 15 seconds
            - 5 hrs            = 5 hours
            - Pause            = Pause polling for all devices
                                    (or specific device if devicename
                                    is specified)
            - Resume            = Resume polling for all devices
                                    (or specific device if devicename
                                    is specified)
            - Waze              = Toggle Waze on/off
    """
    argDevice = Gb.DeviceByDevicename[arg_devicename]
    if arg_devicename and Gb.tracking_method_IOSAPP:
        if argDevice.iosapp_request_loc_cnt > Gb.iosapp_request_loc_max_cnt:
            event_msg =(f"Can not Set Interval, location request cnt "
                        f"exceeded ({argDevice.iosapp_request_location_cnt} "
                        f"of {Gb.iosapp_request_loc_max_cnt})")
            post_event(arg_devicename, event_msg)
            return

    if arg_interval is None:
        #if arg_devicename is not None:
        if arg_devicename:
            post_event(arg_devicename, "Set Interval Action Error, "
                    "no new interval specified")
        return

    cmd_type = CMD_INTERVAL
    new_interval = arg_interval.lower().replace('_', ' ')

#       loop through all devices being tracked and
#       update the attributes. Set various flags if pausing or resuming
#       that will be processed by the next poll in '_polling_loop_15_sec_icloud'
    device_time_adj = 0
    for devicename, Device in Gb.Devices_by_devicename.items():   #
        if arg_devicename and devicename != arg_devicename:
            continue

        device_time_adj += 3
        # devicename_zone = self._format_devicename_zone(devicename, HOME)
        # device_zone, DeviceFmZone = self._get_DeviceFmZone(Device, HOME)
        # DeviceFmZone = Device.DeviceFmZone[HOME]

        # self._wait_if_update_in_process()

        log_msg = (f"SET INTERVAL ACTION Start {devicename}, "
                    f"ArgDevname-{arg_devicename}, ArgInterval-{arg_interval}, "
                    f"New Interval-{new_interval}")
        log_debug_msg(devicename, log_msg)
        event_msg =(f"Set Interval Action handled, New interval {arg_interval}")
        post_event(devicename, event_msg)

        Device.DeviceFmZoneHome.next_update_time = HHMMSS_ZERO
        Device.DeviceFmZoneHome.next_update_secs = 0
        Device.DeviceFmZoneHome.interval_str     = new_interval
        Device.override_interval_seconds = time_str_to_secs(new_interval)

        now_seconds = time_to_secs(dt_util.now().strftime('%X'))
        x, update_in_secs = divmod(now_seconds, 15)
        time_suffix = 15 - update_in_secs + device_time_adj

        info_msg = 'Updating'
        Device.display_info_msg( info_msg)

        log_msg = (f"SET INTERVAL ACTION END {devicename}")
        log_debug_msg(devicename, log_msg)

#--------------------------------------------------------------------
def edit_configuration_service_handler():
    post_event("Edit Configuration handler called")

#--------------------------------------------------------------------
def find_iphone_alert_service_handler(devicename):
    """
    Call the lost iPhone function if using th e FamShr tracking method.
    Otherwise, send a notification to the iOS App
    """
    Device = Gb.Devices_by_devicename[devicename]
    if Device.tracking_method_FAMSHR:
        device_id = Device.device_id_famshr
        if device_id and Gb.PyiCloud:
            Gb.PyiCloud.play_sound(device_id)

            post_event(devicename, "iCloud Find My iPhone Alert sent")
            return
        else:
            event_msg =("iCloud Device not available, the alert will be "
                        "sent to the iOS App")
            post_event(devicename, event_msg)

    message =   {"message": "Find My iPhone Alert",
                    "data": {
                        "push": {
                            "sound": {
                            "name": "alarm.caf",
                            "critical": 1,
                            "volume": 1
                            }
                        }
                    }
                }
    iosapp.send_message_to_device(Device, message)

#########################################################
#
#   HANDLER THE VARIOUS ACTION ACTION REQUESTS
#
#########################################################
#--------------------------------------------------------------------
def _handle_global_action(global_action, action_option):

    if global_action == CMD_RESTART:
        #preserve debug & rawdata across restarts
        Gb.log_debug_flag_restart     = Gb.log_debug_flag
        Gb.log_rawdata_flag_restart   = Gb.log_rawdata_flag
        Gb.start_icloud3_request_flag = True

        return

    elif global_action == CMD_EXPORT_EVENT_LOG:
        Gb.EvLog.export_event_log()
        return

    elif global_action == CMD_REFRESH_EVENT_LOG:
        return

    elif global_action == CMD_DISPLAY_STARTUP_EVENTS:
        Gb.EvLog.update_event_log_display("*")
        return

    elif global_action == CMD_RESET_PYICLOUD_SESSION:
        Gb.evlog_action_request = CMD_RESET_PYICLOUD_SESSION
        return

    elif global_action == CMD_LOG_LEVEL:
        _handle_action_log_level(action_option)
        return

    elif global_action == CMD_WAZEHIST_DB_MAINTENANCE:
        Gb.WazeHist.wazehist_db_maintenance(all_zones_flag=True)

    elif global_action == CMD_WAZEHIST_DB_MAP_GPS_SENSOR:
        Gb.WazeHist.wazehist_db_update_map_gps_sensor()
        return

    #Location level actions
    elif global_action == WAZE:
        if Gb.waze_status == WAZE_USED:
            _handle_action_waze(global_action, '')
        return

#--------------------------------------------------------------------
def _handle_action_device_resume(Device):

    Device.resume_tracking
    return

#--------------------------------------------------------------------
def _handle_action_log_level(action_option):
    if instr(action_option, 'debug'):
        Gb.log_debug_flag = (not Gb.log_debug_flag)

    if instr(action_option, 'rawdata'):
        Gb.log_rawdata_flag = (not Gb.log_rawdata_flag)
        if Gb.log_rawdata_flag:
            Gb.log_rawdata_flag_restart = True

    if instr(action_option, 'eventlog'):
        Gb.evlog_trk_monitors_flag = (not Gb.evlog_trk_monitors_flag)

    event_msg = ""
    if Gb.evlog_trk_monitors_flag:     event_msg += "Event Log Details: On, "
    if Gb.log_debug_flag:              event_msg += "Debug: On, "
    if Gb.log_rawdata_flag:            event_msg += "Rawdata: On, "

    event_msg = "Logging: Off" if event_msg == "" else event_msg
    event_msg =(f"Log Level State > {event_msg}")
    post_log_info_msg(event_msg)

#--------------------------------------------------------------------
def _handle_action_waze(global_action):
    attrs = {}

    if instr(global_action, 'toggle'):
        if Gb.waze_status == WAZE_USED:
            global_action += 'off'
        else:
            global_action += 'on'

    if instr(global_action, 'on'):
        Gb.waze_manual_pause_flag = False
        Gb.waze_status == WAZE_USED

    elif instr(global_action, 'off'):
        Gb.waze_manual_pause_flag = True
        Gb.waze_status == WAZE_NOT_USED

    elif instr(global_action, 'reset_range'):
        Gb.waze_min_distance      = 0
        Gb.waze_max_distance      = HIGH_INTEGER
        Gb.waze_manual_pause_flag = False
        Gb.waze_status            = WAZE_USED

    elif instr(global_action, 'pause'):
        if Gb.waze_manual_pause_flag:
            Gb.waze_manual_pause_flag = False
            Gb.waze_status = WAZE_PAUSED
        else:
            Gb.waze_manual_pause_flag = True
            Gb.waze_status = WAZE_USED

#--------------------------------------------------------------------
def _handle_action_device_location(Device):

    Device.display_info_msg( 'locating')
    if Device.iosapp_monitor_flag:
        iosapp.request_location(Device)
    else:
        Device.DeviceFmZoneHome.next_update_time = HHMMSS_ZERO
        Device.DeviceFmZoneHome.next_update_secs = 0
        Device.override_interval_seconds         = 0

    Gb.EvLog.update_event_log_display(Device.devicename)
