
import logging

from ..globals          import GlobalVariables as Gb
from ..const_general    import (UNKNOWN, HIGH_INTEGER, HHMMSS_ZERO, DATETIME_ZERO, CRLF_DOT, CRLF,
                                NOT_HOME, NOT_SET, PAUSED, PAUSED_CAPS, ICLOUD3_ERROR_MSG, EVLOG_DEBUG,
                                IOSAPP, ICLOUD, EVLOG_NOTICE, )
from ..const_attrs      import (NEXT_UPDATE_TIME, INFO, TRACE_ICLOUD_ATTRS_BASE, TRACE_ATTRS_BASE,
                                LOCATION, ATTRIBUTES, TRIGGER, )
# from .base              import (post_event, display_info_msg, )


_LOGGER = logging.getLogger(__name__)

#####################################################################
#
#   Event & Log functions
#
#####################################################################
# def post_event(devicename, event_msg='+'):
#     '''
#     Add records to the Event Log table. This does not change
#     the info displayed on the Event Log screen. Use the
#     '_update_event_log_display' function to display the changes.
#     '''
#     if event_msg == '+':
#         event_msg = devicename
#         devicename = '*'

#     Gb.EvLog.post_event(devicename, event_msg)

#     if Gb.log_debug_flag:
#         event_msg = (f"◆{devicename}--{str(event_msg).replace(CRLF, '. ')}")
#         _LOGGER.info(event_msg)


# #--------------------------------------------------------------------
# def post_error_event(devicename, event_msg="+"):
#     '''
#     Always display log_msg in Event Log; always add to HA log
#     '''
#     if event_msg.find("iCloud3 Error") >= 0:
#         # self.info_notification = ICLOUD3_ERROR_MSG
#         for td_devicename, Device in Gb.Devices_by_devicename.items():   #
#             display_info_msg(Device, ICLOUD3_ERROR_MSG)

#     post_event(devicename, event_msg)

#     event_msg = (f"{devicename} {event_msg}")
#     event_msg = str(event_msg).replace(CRLF, ". ")

#     if Gb.start_icloud3_inprocess_flag and not Gb.log_debug_flag:
#         Gb.startup_log_msgs       += (f"{Gb.startup_log_msgs_prefix}\n {event_msg}")
#         Gb.startup_log_msgs_prefix = ""

#     log_error_msg(event_msg)

# #--------------------------------------------------------------------
# def post_info_event(devicename, event_msg='+'):
#     ''' Always add log_msg to HA log '''
#     if event_msg == '+':
#         event_msg = devicename
#         devicename = '*'

#     post_event(devicename, event_msg)

#     event_msg = (f"◆{devicename}--◆{str(event_msg).replace(CRLF, '. ')}")
#     _LOGGER.info(event_msg)

# #--------------------------------------------------------------------
# def post_debug_event(devicename, event_msg='+'):
#     '''
#     Post the event message and display it in Event Log and HA log
#     when the config parameter "log_level: eventlog" is specified or
#     the Show Tracking Monitors was selected in Event Log > Actions
#     '''
#     if event_msg == '+':
#         event_msg = devicename
#         devicename = '*'

#     post_event(devicename, f"{EVLOG_DEBUG}{event_msg}")

#     if Gb.evlog_trk_monitors_flag:
#         log_debug_msg(devicename, event_msg)

#--------------------------------------------------------------------
def log_debug_msg(devicename, log_msg='+', log_title=''):
    '''
    Add a debug log message to the HA Log file
    '''
    if log_msg == '+':
        log_msg = devicename
        devicename = '*'

    log_msg = (f"◆{devicename}--{log_title}◆{str(log_msg).replace(CRLF, '. ')}")
    if Gb.log_debug_flag:
        _LOGGER.info(log_msg)
    else:
        _LOGGER.debug(log_msg)

# #--------------------------------------------------------------------
# def display_info_msg(Device, info_msg):
#     '''
#     Display a status message in the Device's info sensor.
#     '''
#     try:
#         if Gb.Devices_by_devicename == {}:
#             return ""

#         attrs = {}
#         attrs[INFO] = (f"● {info_msg} ●")
#         Gb.Sensors.update_device_sensors(Device, attrs)

#         return (f"{CRLF_DOT}{info_msg}")

#     # Catch any errors before the Device or info sensor is set up
#     except Exception as err:
#         #_LOGGER.exception(err)
#         return ""


#--------------------------------------------------------------------
def log_info_msg(log_msg):
    ''' Always add log_msg to HA log '''
    _LOGGER.info(log_msg)

#--------------------------------------------------------------------
def log_warning_msg(log_msg):
    _LOGGER.warning(log_msg)

#--------------------------------------------------------------------
def log_error_msg(log_msg):
    _LOGGER.error(log_msg)

#--------------------------------------------------------------------
def log_rawdata(log_msg):
    _LOGGER.error(log_msg)
