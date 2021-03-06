#########################################################
#
#   ICLOUD SERVICE HANDLER MODULE
#
#########################################################
# import homeassistant.util.dt as dt_util
# from homeassistant import config_entries, data_entry_flow
# from homeassistant.data_entry_flow import FlowManager
# from homeassistant.helpers import discovery_flow
# import homeassistant.helpers.httpx_client as client
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

# import requests
# import webbrowser
# import asyncio

from ..global_variables import GlobalVariables as Gb
from ..const            import (DOMAIN, HHMMSS_ZERO,
                                WAZE, WAZE_NOT_USED, WAZE_USED, WAZE_PAUSED,
                                LOCATION, HIGH_INTEGER, CONF_ZONE, NEXT_UPDATE_TIME,
                                CONF_DEVICENAME, CONF_COMMAND, )

from ..helpers.base     import (instr,
                                post_event, post_error_msg, post_log_info_msg, post_monitor_msg,
                                log_debug_msg, log_exception, _trace, _traceha, )
from ..helpers.time     import (time_to_secs, time_str_to_secs, )
from ..support          import iosapp_interface
from ..config_flow      import iCloud3ConfigFlow, OptionsFlowHandler
# import asyncio

# EvLog Action Commands
CMD_ERROR                  = 'error'
CMD_INTERVAL               = 'interval'
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
                    CMD_FIND_DEVICE_ALERT, ]

SERVICE_SCHEMA = vol.Schema({
    vol.Optional(CONF_COMMAND): cv.string,
    vol.Optional(CONF_DEVICENAME): cv.slugify,
})

from   homeassistant.util.location import distance

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   DEFINE THE PROCESS INVOKED BY THE HASS.SERVICES.REGISTER FOR EACH SERVICE
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
def process_update_service_request(call):
    """ icloud3.update service call request """

    devicename = call.data.get(CONF_DEVICENAME)
    command    = call.data.get(CONF_COMMAND)

    update_service_handler(devicename, command)

#--------------------------------------------------------------------
def process_update_icloud3_configuration_request(call):
    """
    Call the Icloud3 edit configuration service_request function
    that initiates a config_flow update
    """
    update_configuration_parameters_handler()

#--------------------------------------------------------------------
def process_restart_icloud3_service_request(call):
    """ icloud3.restart service call request  """

    Gb.start_icloud3_request_flag = True

#--------------------------------------------------------------------
def process_find_iphone_alert_service_request(call):
    """Call the find_iphone_alert to play a sound on the phone"""

    devicename = call.data.get(CONF_DEVICENAME)

    find_iphone_alert_service_handler(devicename)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   DEFINE THE PROCESS INVOKED BY THE HASS.SERVICES.REGISTER FOR EACH SERVICE
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
def register_icloud3_services():
    ''' Register iCloud3 Service Call Handlers '''

    try:
        Gb.hass.services.register(DOMAIN, 'action',
                    process_update_service_request, schema=SERVICE_SCHEMA)
        # Gb.hass.services.register(DOMAIN, 'config',
        #             process_update_icloud3_configuration_request)
        Gb.hass.services.register(DOMAIN, 'restart',
                    process_restart_icloud3_service_request, schema=SERVICE_SCHEMA)
        Gb.hass.services.register(DOMAIN, 'find_iphone_alert',
                    process_find_iphone_alert_service_request, schema=SERVICE_SCHEMA)

        return True

    except Exception as err:
        log_exception(err)

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ROUTINES THAT HANDLE THE INDIVIDUAL SERVICE REQUESTS
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
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
    # Ignore Action requests during startup. They are caused by the devicename changes
    # to the EvLog attributes indicating the startup stage.
    if Gb.start_icloud3_inprocess_flag:
        return

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

            elif action == LOCATION:
                _handle_action_device_location(Device)

            else:
                info_msg = (f"INVALID ACTION > {action}")
                Device.display_info_msg( info_msg)

    Gb.EvLog.update_event_log_display(devicename)


#--------------------------------------------------------------------
def update_configuration_parameters_handler():
    post_event("Edit Configuration handler called")

    try:

        Gb.hass.add_job(
            Gb.hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={'source': 'reauth'},
                    data={
                        'icloud3_service_call': True,
                        'step_id': 'reauth',
                    },
                )
            )
        # _traceha(f"200 ### aft {Gb.OptionsFlowHandler=}")

        # options_flow = iCloud3ConfigFlow.async_get_options_flow()
        # _traceha(f"203 {options_flow=}")

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
    iosapp_interface.send_message_to_device(Device, message)

#########################################################
#
#   HANDLER THE VARIOUS ACTION ACTION REQUESTS
#
#########################################################
def _handle_global_action(global_action, action_option):

    # _traceha(f'{global_action=}'')
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

    elif global_action == CMD_WAZEHIST_MAINTENANCE:
        Gb.WazeHist.wazehist_recalculate_time_dist(all_zones_flag=True)

    elif global_action == CMD_WAZEHIST_TRACK:
        Gb.WazeHist.wazehist_update_track_sensor()
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
        iosapp_interface.request_location(Device)
    else:
        Device.DeviceFmZoneHome.next_update_time = HHMMSS_ZERO
        Device.DeviceFmZoneHome.next_update_secs = 0
        Device.override_interval_seconds         = 0

    Gb.EvLog.update_event_log_display(Device.devicename)
