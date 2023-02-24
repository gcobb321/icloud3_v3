#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD SERVICE HANDLER MODULE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from ..global_variables     import GlobalVariables as Gb
from ..const                import (DOMAIN,
                                    HHMMSS_ZERO, HIGH_INTEGER,
                                    WAZE,
                                    CMD_RESET_PYICLOUD_SESSION,
                                    LOCATION, NEXT_UPDATE_TIME, NEXT_UPDATE, INTERVAL,
                                    CONF_DEVICENAME, CONF_ZONE, CONF_COMMAND, CONF_LOG_LEVEL,
                                    )

from ..support              import iosapp_interface
from ..support              import config_file
from ..support              import determine_interval as det_interval
from ..helpers.common       import (instr, )
from ..helpers.messaging    import (post_event, post_error_msg, post_monitor_msg,
                                    write_ic3_debug_log_recd,
                                    log_info_msg, log_debug_msg, log_exception,
                                    open_ic3_debug_log_file, close_ic3_debug_log_file,
                                    close_reopen_ic3_debug_log_file,
                                    _trace, _traceha, )
from ..helpers.time_util    import (secs_to_time, time_str_to_secs, datetime_now, secs_since, time_now, )

# EvLog Action Commands
CMD_ERROR                  = 'error'
CMD_PAUSE                  = 'pause'
CMD_RESUME                 = 'resume'
CMD_WAZE                   = 'waze'
CMD_REQUEST_LOCATION       = 'location'
CMD_EXPORT_EVENT_LOG       = 'export_event_log'
CMD_WAZEHIST_MAINTENANCE   = 'wazehist_maint'
CMD_WAZEHIST_TRACK         = 'wazehist_track'
CMD_DISPLAY_STARTUP_EVENTS = 'startuplog'
CMD_RESET_PYICLOUD_SESSION = 'reset_session'
CMD_LOG_LEVEL              = 'log_level'
CMD_REFRESH_EVENT_LOG      = 'refresh_event_log'
CMD_RESTART                = 'restart'
CMD_FIND_DEVICE_ALERT      = 'find_alert'
CMD_LOCATE                 = 'locate'

REFRESH_EVLOG_FNAME             = 'Refresh Event Log'
HIDE_TRACKING_MONITORS_FNAME    = 'Hide Tracking Monitors'
SHOW_TRACKING_MONITORS_FNAME    = 'Show Tracking Monitors'


GLOBAL_ACTIONS =  [CMD_EXPORT_EVENT_LOG,
                    CMD_DISPLAY_STARTUP_EVENTS,
                    CMD_RESET_PYICLOUD_SESSION,
                    CMD_WAZE,
                    CMD_REFRESH_EVENT_LOG,
                    CMD_RESTART,
                    CMD_LOG_LEVEL,
                    CMD_WAZEHIST_MAINTENANCE,
                    CMD_WAZEHIST_TRACK, ]
DEVICE_ACTIONS =  [CMD_REQUEST_LOCATION,
                    CMD_PAUSE,
                    CMD_RESUME,
                    CMD_FIND_DEVICE_ALERT,
                    CMD_LOCATE, ]

NO_EVLOG_ACTION_POST_EVENT = [
                    'Show Startup Log, Errors & Alerts',
                    REFRESH_EVLOG_FNAME,
                    HIDE_TRACKING_MONITORS_FNAME,
                    SHOW_TRACKING_MONITORS_FNAME,
                    CMD_DISPLAY_STARTUP_EVENTS, ]

SERVICE_SCHEMA = vol.Schema({
    vol.Optional('command'): cv.string,
    vol.Optional('action'): cv.string,
    vol.Optional(CONF_DEVICENAME): cv.slugify,
    vol.Optional('action_fname'): cv.string,
})

from   homeassistant.util.location import distance

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEFINE THE PROCESS INVOKED BY THE HASS.SERVICES.REGISTER FOR EACH SERVICE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def process_update_service_request(call):
    """ icloud3.update service call request """

    action       = call.data.get('command') or call.data.get('action')
    action_fname = call.data.get('action_fname')
    devicename   = call.data.get(CONF_DEVICENAME)

    update_service_handler(action, action_fname, devicename)

#--------------------------------------------------------------------
# def process_update_icloud3_configuration_request(call):
#     """
#     Call the Icloud3 edit configuration service_request function
#     that initiates a config_flow update
#     """
#     update_configuration_parameters_handler()

#--------------------------------------------------------------------
def process_restart_icloud3_service_request(call):
    """ icloud3.restart service call request  """

    Gb.start_icloud3_request_flag = True

#--------------------------------------------------------------------
def process_find_iphone_alert_service_request(call):
    """Call the find_iphone_alert to play a sound on the phone"""

    devicename = call.data.get(CONF_DEVICENAME)

    find_iphone_alert_service_handler(devicename)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEFINE THE PROCESS INVOKED BY THE HASS.SERVICES.REGISTER FOR EACH SERVICE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def register_icloud3_services():
    ''' Register iCloud3 Service Call Handlers '''

    try:
        Gb.hass.services.register(DOMAIN, 'action',
                    process_update_service_request, schema=SERVICE_SCHEMA)
        Gb.hass.services.register(DOMAIN, 'update',
                    process_update_service_request, schema=SERVICE_SCHEMA)
        Gb.hass.services.register(DOMAIN, 'restart',
                    process_restart_icloud3_service_request, schema=SERVICE_SCHEMA)
        Gb.hass.services.register(DOMAIN, 'find_iphone_alert',
                    process_find_iphone_alert_service_request, schema=SERVICE_SCHEMA)

        return True

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ROUTINES THAT HANDLE THE INDIVIDUAL SERVICE REQUESTS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def update_service_handler(action_entry=None, action_fname=None, devicename=None):
    """
    Authenticate against iCloud and scan for devices.


    Actions:
    - pause             - stop polling for the devicename or all devices
    - resume            - resume polling devicename or all devices, reset
                            the interval override to normal interval
                            calculations
    - pause-resume      - same as above but toggles between pause and resume
    - zone xxxx         - updates the devie state to xxxx and updates all
                            of the iloud3 attributes. This does the see
                            service call and then an update.
    - reset             - reset everything and rescans all of the devices
    - location          - request location update from ios app
    - locate x mins     - locate in x minutes
    """
    # Ignore Action requests during startup. They are caused by the devicename changes
    # to the EvLog attributes indicating the startup stage.
    if Gb.start_icloud3_inprocess_flag:
        return

    action = action_entry
    if action == f"{CMD_REFRESH_EVENT_LOG}+clear_alerts":
        action = CMD_REFRESH_EVENT_LOG
        Gb.EvLog.clear_alert_events()

    if (action == CMD_REFRESH_EVENT_LOG
            and Gb.EvLog.secs_since_refresh <= 2
            and Gb.EvLog.last_refresh_devicename == devicename):
        post_monitor_msg(f"Service Action Ignored > {action_fname}, Action-{action_entry}, {devicename}")
        return

    if action_fname not in NO_EVLOG_ACTION_POST_EVENT:
        post_monitor_msg(f"Service Action Received > Action-{action_entry}, {devicename}")

    action_entry  = action_entry.replace('eventlog', 'monitor')
    action_entry  = action_entry.replace(':', '')
    action        = action_entry.split(' ')[0]
    action_option = action_entry.replace(action, '').strip()

    devicename_msg = (f", Device-{devicename}") if devicename else ""
    action_msg     = action_fname if action_fname else f"{action.title()}"
    action_option_msg = f", Option-{action_option}" if action_option else ""
    event_msg =(f"Service Action Handler > Action-{action_msg}{action_option_msg}{devicename_msg}")
    if action_fname not in NO_EVLOG_ACTION_POST_EVENT:
        post_event(event_msg)

    if action in GLOBAL_ACTIONS:
        _handle_global_action(action, action_option)

    elif devicename == 'startup_log':
        pass

    elif action in DEVICE_ACTIONS:
        if devicename:
            Devices = [Gb.Devices_by_devicename[devicename]]
        else:
            Devices = [Device for Device in Gb.Devices_by_devicename_tracked.values()]

        if action == CMD_PAUSE:
            if devicename is None:
                Gb.all_tracking_paused_flag = True
                Gb.EvLog.display_user_message('Tracking is Paused', alert=True)
            for Device in Devices:
                Device.pause_tracking

        elif action == CMD_RESUME:
            Gb.all_tracking_paused_flag = False
            Gb.EvLog.display_user_message('', clear_alert=True)
            for Device in Devices:
                Device.resume_tracking

        elif action == CMD_LOCATE:
            for Device in Devices:
                _handle_action_device_locate(Device, action_option)

        elif action == CMD_REQUEST_LOCATION:
            for Device in Devices:
                _handle_action_device_location(Device)

    if devicename == 'startup_log':
        pass
    elif (Gb.EvLog.evlog_attrs['fname'] == 'Startup Events'
            and action == 'log_level'
            and action_option == 'monitor'):
        devicename = 'startup_log'

    Gb.EvLog.update_event_log_display(devicename)

#--------------------------------------------------------------------
def update_configuration_parameters_handler():
    post_event("Edit Configuration handler called")

    try:

        Gb.hass.add_job(Gb.hass.config_entries.flow.async_init(
                                DOMAIN,
                                context={'source': 'reauth'},
                                data={'icloud3_service_call': True, 'step_id': 'reauth',},)
                        )

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def find_iphone_alert_service_handler(devicename):
    """
    Call the lost iPhone function if using th e FamShr tracking method.
    Otherwise, send a notification to the iOS App
    """
    Device = Gb.Devices_by_devicename[devicename]
    if Device.tracking_method_FAMSHR:
        device_id = Device.device_id_famshr
        if device_id and Gb.PyiCloud and Gb.PyiCloud.FamilySharing:
            Gb.PyiCloud.FamilySharing.play_sound(device_id, subject="Find My iPhone Alert")
            # Gb.PyiCloud.play_sound(device_id, subject="Find My iPhone Alert")

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
    iosapp_interface.send_message_to_device(Device, message)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   HANDLER THE VARIOUS ACTION ACTION REQUESTS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def _handle_global_action(global_action, action_option):

    if global_action == CMD_RESTART:
        Gb.log_debug_flag_restart     = Gb.log_debug_flag
        Gb.log_rawdata_flag_restart   = Gb.log_rawdata_flag
        Gb.start_icloud3_request_flag = True
        Gb.EvLog.display_user_message('iCloud3 is Restarting', clear_alert=True)
        if Gb.log_debug_flag:
            close_ic3_debug_log_file()
            open_ic3_debug_log_file(new_debug_log=True)
            write_ic3_debug_log_recd(f"\n{'-'*25} Opened by Event Log > Actions > Restart {'-'*25}")
        return

    elif global_action == CMD_EXPORT_EVENT_LOG:
        Gb.EvLog.export_event_log()
        return

    elif global_action == CMD_REFRESH_EVENT_LOG:
        return

    elif global_action == CMD_DISPLAY_STARTUP_EVENTS:
        return

    elif global_action == CMD_RESET_PYICLOUD_SESSION:
        # This will be handled in the 5-second ic3 loop
        Gb.evlog_action_request = CMD_RESET_PYICLOUD_SESSION
        return

    elif global_action == CMD_LOG_LEVEL:
        handle_action_log_level(action_option)
        return

    elif global_action == CMD_WAZEHIST_MAINTENANCE:
        event_msg = "Waze History > Recalculate Route Time/Distance "
        if Gb.wazehist_recalculate_time_dist_flag:
            event_msg += "Starting Immediately"
            post_event(event_msg)
            Gb.WazeHist.wazehist_recalculate_time_dist_all_zones()
        else:
            Gb.wazehist_recalculate_time_dist_flag = True
            event_msg += "Scheduled to run tonight at Midnight"
            post_event(event_msg)

    elif global_action == CMD_WAZEHIST_TRACK:
        event_msg = ("Waze History > Update Location Map Display Points "
                    "Scheduled for Midnight")
        post_event(event_msg)
        Gb.WazeHist.wazehist_update_track_sensor()
        return

#--------------------------------------------------------------------
def handle_action_log_level(action_option, change_conf_log_level=True):

    new_log_debug_flag   = Gb.log_debug_flag
    new_log_rawdata_flag = Gb.log_rawdata_flag

    if instr(action_option, 'debug'):
        new_log_debug_flag   = (not Gb.log_debug_flag)
        new_log_rawdata_flag = False

    if instr(action_option, 'rawdata'):
        new_log_rawdata_flag = (not Gb.log_rawdata_flag)
        new_log_debug_flag   = True if new_log_rawdata_flag else new_log_debug_flag

    if instr(action_option, 'monitor'):
        Gb.evlog_trk_monitors_flag = (not Gb.evlog_trk_monitors_flag)

    event_msg = "Debug Logging Status > "
    # event_msg += f"Tracking Monitors-{Gb.evlog_trk_monitors_flag}, "
    event_msg += f"Debug-{new_log_debug_flag}, "
    event_msg += f"Rawdata-{new_log_rawdata_flag}"
    post_event(event_msg)

    # Create a new debug.log file if the current one was created over 24-hours ago
    if new_log_debug_flag:
        new_debug_log_file = (Gb.ic3_debug_log_new_file_secs == 0
                            or secs_since(Gb.ic3_debug_log_new_file_secs) > 80000)

        open_ic3_debug_log_file(new_debug_log=new_debug_log_file)
        write_ic3_debug_log_recd(f"\n{'-'*25} Opened by Event Log > Actions {'-'*25}")
        write_ic3_debug_log_recd(event_msg)

    elif Gb.iC3DebugLogFile is not None:
        write_ic3_debug_log_recd(event_msg)
        write_ic3_debug_log_recd(f"{'-'*25} Closed by Event Log > Actions {'-'*25}\n")
        close_ic3_debug_log_file()

    Gb.log_debug_flag   = new_log_debug_flag
    Gb.log_rawdata_flag = new_log_rawdata_flag

def _on_off_text(condition):
    return 'On' if condition else 'Off'

#--------------------------------------------------------------------
def close_reopen_ic3_debug_log_file():
    close_reopen_ic3_debug_log_file()

#--------------------------------------------------------------------
def _handle_action_device_location(Device):
    '''
    Request ios app location from the EvLog > Actions
    '''

    Device.display_info_msg('Updating Location')

    if Device.iosapp_monitor_flag:
        Device.iosapp_data_change_reason = f"Location Requested@{time_now()}"
        iosapp_interface.request_location(Device, force_request=True)

    Device.resume_tracking
    Device.write_ha_sensor_state(NEXT_UPDATE, 'Locating')

#--------------------------------------------------------------------
def _handle_action_device_locate(Device, minutes):
    '''
    Set the next update time & interval from the Action > locate service call
    '''

    interval = time_str_to_secs(minutes) if minutes != '' else 5
    det_interval.update_all_device_fm_zone_sensors_interval(Device, interval)
    Device.icloud_update_reason = f"Location Requested@{time_now()}"
    post_event(Device.devicename, f"Location will be updated at {Device.sensors[NEXT_UPDATE_TIME]}")
    Device.write_ha_sensors_state([NEXT_UPDATE, INTERVAL])

#--------------------------------------------------------------------
def set_ha_notification(title, message, issue=True):
    '''
    Format an HA Notification
    '''
    Gb.ha_notification = {
        'title': title,
        'message': f'{message}<br><br>*iCloud3 Notification {datetime_now()}*',
        'notification_id': DOMAIN}

    if issue:
        issue_ha_notification()

#--------------------------------------------------------------------
def issue_ha_notification():

    if Gb.ha_notification == {}:
        return

    Gb.hass.services.call("persistent_notification", "create", Gb.ha_notification)
    Gb.ha_notification = {}
