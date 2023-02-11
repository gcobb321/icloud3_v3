

from ..global_variables import GlobalVariables as Gb
from ..const            import (DOT, ICLOUD3_ERROR_MSG, EVLOG_DEBUG, EVLOG_ERROR, EVLOG_INIT_HDR, EVLOG_MONITOR,
                                EVLOG_TIME_RECD, EVLOG_UPDATE_HDR, EVLOG_UPDATE_START, EVLOG_UPDATE_END,
                                EVLOG_ALERT, EVLOG_WARNING, EVLOG_HIGHLIGHT, EVLOG_IC3_STARTING,EVLOG_IC3_STAGE_HDR,
                                IC3LOGGER_FILENAME, EVLOG_TIME_RECD,
                                CRLF, CRLF_DOT, NBSP, NBSP2, NBSP3, NBSP4, NBSP5, NBSP6,
                                DATETIME_FORMAT, DATETIME_ZERO,
                                NEXT_UPDATE_TIME, INTERVAL,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_LOG_LEVEL, CONF_PASSWORD, CONF_USERNAME,
                                LATITUDE,  LONGITUDE, LOCATION_SOURCE, TRACKING_METHOD,
                                ZONE, ZONE_DATETIME, INTO_ZONE_DATETIME, LAST_ZONE,
                                TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
                                TRIGGER, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
                                INTERVAL, ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, MOVED_DISTANCE,
                                DEVICE_STATUS, LOW_POWER_MODE,
                                AUTHENTICATED,
                                LAST_UPDATE_TIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_TIME, LAST_LOCATED_DATETIME, LAST_LOCATED_TIME,
                                INFO, GPS_ACCURACY, GPS, POLL_COUNT, VERT_ACCURACY, ALTITUDE,
                                ICLOUD3_VERSION,
                                BADGE,
                                )

import homeassistant.util.dt as dt_util

import os
import time
from inspect import getframeinfo, stack
import traceback
from .common import obscure_field

FILTER_DATA_DICTS = ['data', 'userInfo', 'dsid', 'dsInfo', 'webservices', 'locations',]
FILTER_DATA_LISTS = ['devices', 'content', 'followers', 'following', 'contactDetails',]
FILTER_FIELDS = [
        ICLOUD3_VERSION, AUTHENTICATED,
        LATITUDE,  LONGITUDE, LOCATION_SOURCE, TRACKING_METHOD,
        ZONE, ZONE_DATETIME, INTO_ZONE_DATETIME, LAST_ZONE,
        TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
        TRIGGER, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
        INTERVAL, ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
        TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, MOVED_DISTANCE,
        DEVICE_STATUS, LOW_POWER_MODE, BADGE,
        LAST_UPDATE_TIME, LAST_UPDATE_DATETIME,
        NEXT_UPDATE_TIME, NEXT_UPDATE_TIME,
        LAST_LOCATED_TIME, LAST_LOCATED_DATETIME,
        INFO, GPS_ACCURACY, GPS, POLL_COUNT, VERT_ACCURACY, ALTITUDE,
        'ResponseCode', 'reason',
        'id', 'firstName', 'lastName', 'name', 'fullName', 'appleId', 'emails', 'phones',
        'deviceStatus', 'batteryStatus', 'batteryLevel', 'membersInfo',
        'deviceModel', 'rawDeviceModel', 'deviceDisplayName', 'modelDisplayName', 'deviceClass',
        'isOld', 'isInaccurate', 'timeStamp', 'altitude', 'location', 'latitude', 'longitude',
        'horizontalAccuracy', 'verticalAccuracy',
        'hsaVersion', 'hsaEnabled', 'hsaTrustedBrowser', 'locale', 'appleIdEntries', 'statusCode',
        'familyEligible', 'findme', 'requestInfo',
        'invitationSentToEmail', 'invitationAcceptedByEmail', 'invitationFromHandles',
        'invitationFromEmail', 'invitationAcceptedHandles',
        'data', 'userInfo', 'dsid', 'dsInfo', 'webservices', 'locations',
        'devices', 'content', 'followers', 'following', 'contactDetails', ]


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   MISCELLANEOUS MESSAGING ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def broadcast_info_msg(info_msg):
    '''
    Display a message in the info sensor for all devices
    '''
    if INFO not in Gb.conf_sensors['device']:
        return


    Gb.broadcast_info_msg = f"{DOT}{info_msg}"

    try:
        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            InfoSensor = Gb.Sensors_by_devicename[devicename][INFO]
            InfoSensor.write_ha_sensor_state()

    # Catch error if the Info sensor has not been set up yet during startup
    # or if the info sensor has not been selected in config_vlow > sensors
    except KeyError:
        pass


    return

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   EVENT LOG POST ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def post_event(devicename, event_msg='+'):
    '''
    Add records to the Event Log table. This does not change
    the info displayed on the Event Log screen. Use the
    '_update_event_log_display' function to display the changes.
    '''

    devicename, event_msg = resolve_system_event_msg(devicename, event_msg)

    try:
        if event_msg.endswith(', '):
            event_msg = event_msg[:-2]
    except:
        Gb.HALogger.info(event_msg)
        pass

    Gb.EvLog.post_event(devicename, event_msg)

    if (Gb.log_debug_flag
            and event_msg.startswith(EVLOG_TIME_RECD) is False):
        event_msg = (f"{Gb.trace_prefix}{devicename} > {str(event_msg)}")
        write_ic3_debug_log_recd(event_msg)

    # Starting up, update event msg to print all messages together
    elif (Gb.start_icloud3_inprocess_flag
            and event_msg.startswith(EVLOG_DEBUG) is False):

        if event_msg.startswith('^'):
            Gb.startup_log_msgs += f"\n\n{event_msg[3:].upper()}"
        else:
            event_msg = event_msg.replace(NBSP6, '    ')
            event_msg = event_msg.replace('• ', '•').replace('•', '  • ')
            event_msg = event_msg.replace('✓', '  ✓ ')
            Gb.startup_log_msgs += f"\n{event_msg}"

#--------------------------------------------------------------------
def post_error_msg(devicename, event_msg="+"):
    '''
    Always display log_msg in Event Log; always add to HA log
    '''
    devicename, event_msg = resolve_system_event_msg(devicename, event_msg)
    if event_msg.find("iCloud3 Error") >= 0:
        for td_devicename, Device in Gb.Devices_by_devicename.items():   #
            Device.display_info_msg(ICLOUD3_ERROR_MSG)

    post_event(devicename, event_msg)

    log_msg = (f"{devicename} {event_msg}")
    log_msg = str(log_msg).replace(CRLF, ". ")

    if Gb.start_icloud3_inprocess_flag and not Gb.log_debug_flag:
        Gb.startup_log_msgs       += (f"{Gb.startup_log_msgs_prefix}\n {log_msg}")
        Gb.startup_log_msgs_prefix = ""

    log_error_msg(log_msg)

#--------------------------------------------------------------------
def post_monitor_msg(devicename, event_msg='+'):
    '''
    Post the event message and display it in Event Log and HA log
    when the config parameter "log_level: eventlog" is specified or
    the Show Tracking Monitors was selected in Event Log > Actions
    '''
    devicename, event_msg = resolve_system_event_msg(devicename, event_msg)
    post_event(devicename, f"{EVLOG_MONITOR}{event_msg}")

    # write_ic3_debug_log_recd(f"{devicename} >{event_msg}")

#-------------------------------------------------------------------------------------------
def resolve_system_event_msg(devicename, event_msg):
    if event_msg == '+':
        return ("*", devicename)
    else:
        return (devicename, event_msg)

#--------------------------------------------------------------------
def resolve_log_msg_module_name(module_name, log_msg):
    if log_msg == "+":
        return (module_name.replace(NBSP, ''))
    else:
        return (f"[{module_name}] {log_msg.replace(NBSP, '')}")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3-DEBUG.LOG FILE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
DEBUG_LOG_LINE_TABS = "\t\t\t\t\t\t\t\t\t\t"
def open_ic3_debug_log_file(new_debug_log=False):
    '''
    Open the icloud3-debug.log file

    args:
        reopen  True - Open the file in append mode
                False - Create a new file
    '''

    if new_debug_log:
        filemode = 'w'
        Gb.ic3_debug_log_new_file_secs = int(time.time())

    elif Gb.iC3DebugLogFile:
        write_ic3_debug_log_recd(f"{'-'*25} Debug Log File Already Open {'-'*25}")
        return

    else:
        filemode = 'a'

    ic3_debug_log_filename = Gb.hass.config.path(IC3LOGGER_FILENAME)
    Gb.iC3DebugLogFile = open(ic3_debug_log_filename, filemode, encoding='utf8')
    Gb.ic3_debug_log_file_last_write_secs = 0
    Gb.ic3_debug_log_update_flag = False

    # write_ic3_debug_log_recd(f"\n{'-'*25} Opened by Event Log  {'-'*25}")

    if new_debug_log is False:
        return

    write_ic3_debug_log_recd(f"iCloud3 v{Gb.version}, "
                            f"Debug Log File: {dt_util.now().strftime(DATETIME_FORMAT)[0:19]}\n")

    # Write the ic3 configuration (general & devices) to the debug log file
    write_ic3_debug_log_recd(f"Profile:\n{DEBUG_LOG_LINE_TABS}{Gb.conf_profile}")
    write_ic3_debug_log_recd(f"General Configuration:\n{DEBUG_LOG_LINE_TABS}{Gb.conf_general}")
    write_ic3_debug_log_recd(f"{DEBUG_LOG_LINE_TABS}{Gb.ha_location_info}")
    write_ic3_debug_log_recd("")

    for conf_device in Gb.conf_devices:
        write_ic3_debug_log_recd(   f"{conf_device[CONF_FNAME]}, {conf_device[CONF_IC3_DEVICENAME]}:\n"
                                    f"{DEBUG_LOG_LINE_TABS}{conf_device}")
    write_ic3_debug_log_recd("")

#------------------------------------------------------------------------------
def close_ic3_debug_log_file(new_debug_log=False):
    '''
    Close the icloud3-debug.log file is it is open
    '''
    if Gb.iC3DebugLogFile is None:
        return

    if new_debug_log:
        write_ic3_debug_log_recd(f"\n")
        write_ic3_debug_log_recd(f"iCloud3 v{Gb.version}, Closing Debug Log File, "
                                f"ConfigLogLevel-{Gb.conf_general[CONF_LOG_LEVEL]}, "
                                f"CurrentLogLevel-{Gb.log_level}")

    Gb.iC3DebugLogFile.close()
    Gb.iC3DebugLogFile = None
    Gb.ic3_debug_log_update_flag = False

#------------------------------------------------------------------------------
def close_reopen_ic3_debug_log_file(closed_by=None):
    '''
    Close and reopen the debug log file to commit the newly written records
    '''
    if Gb.ic3_debug_log_update_flag is False:
        return

    if closed_by:
        write_ic3_debug_log_recd(f"Commit Log File Records, RequestedBy-{closed_by}")

    close_ic3_debug_log_file()
    open_ic3_debug_log_file()

#------------------------------------------------------------------------------
def write_ic3_debug_log_recd(recd, force_write=False):

    if Gb.log_debug_flag is False and force_write is False:
        return

    if Gb.iC3DebugLogFile is None:
        open_ic3_debug_log_file()

    date_time_now = dt_util.now().strftime(DATETIME_FORMAT)[0:19]
    recd = _debug_recd_filter(recd)

    Gb.iC3DebugLogFile.write(f"{date_time_now} {_called_from()} {recd}\n")

    Gb.ic3_debug_log_file_last_write_secs = int(time.time())
    Gb.ic3_debug_log_update_flag = True

#--------------------------------------------------------------------
def _debug_recd_filter(recd):
    '''
    Filter out EVLOG_XXX control fields
    '''

    if recd.startswith('^'): recd = recd[3:]
    extra_tabs = '\t\t\t   ' #if recd.startswith('STAGE') else ''
    recd = recd.replace(EVLOG_MONITOR, '')
    recd = recd.replace(NBSP, ' ')
    recd = recd.replace(NBSP2, ' ')
    recd = recd.replace(NBSP3, ' ')
    recd = recd.replace(NBSP4, ' ')
    recd = recd.replace(NBSP5, ' ')
    recd = recd.replace(NBSP6, ' ')
    recd = recd.strip()
    recd = recd.replace(CRLF, f"\n{DEBUG_LOG_LINE_TABS}{extra_tabs}")
    recd = recd.replace('* >', '')

    if recd.find('^') == -1: return recd.strip()

    recd = recd.replace(EVLOG_TIME_RECD , '')
    recd = recd.replace(EVLOG_UPDATE_HDR, '')
    recd = recd.replace(EVLOG_UPDATE_START, '')
    recd = recd.replace(EVLOG_UPDATE_END  , '')
    recd = recd.replace(EVLOG_ERROR, '')
    recd = recd.replace(EVLOG_ALERT, '')
    recd = recd.replace(EVLOG_WARNING, '')
    recd = recd.replace(EVLOG_INIT_HDR, '')
    recd = recd.replace(EVLOG_HIGHLIGHT, '')
    recd = recd.replace(EVLOG_IC3_STARTING, '')
    recd = recd.replace(EVLOG_IC3_STAGE_HDR, '')

    recd = recd.replace('^1^', '').replace('^2^', '').replace('^3^', '')
    recd = recd.replace('^4^', '').replace('^5^', '')

    return recd.strip()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   LOG MESSAGE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def log_filter(log_msg):
    try:
        if type(log_msg) is str:
            p = log_msg.find('^')
            if p >= 0:
                log_msg = log_msg[:p] + log_msg[p+3:]

            log_msg = log_msg.replace('* > ', '')
    except:
        pass

    return log_msg

#--------------------------------------------------------------------
def log_info_msg(module_name, log_msg='+'):
    log_msg = resolve_log_msg_module_name(module_name, log_msg)

    if type(log_msg) is str and log_msg.startswith('^'): log_msg = log_msg[3:]

    Gb.HALogger.info(log_filter(log_msg))

    if Gb.iC3DebugLogFile is not None:
        write_ic3_debug_log_recd(log_filter(log_msg))

#--------------------------------------------------------------------
def log_warning_msg(module_name, log_msg='+'):
    log_msg = resolve_log_msg_module_name(module_name, log_msg)
    log_msg = log_filter(log_msg)
    Gb.HALogger.warning(log_msg)
    write_ic3_debug_log_recd(log_msg)

#--------------------------------------------------------------------
def log_error_msg(module_name, log_msg='+'):
    log_msg = resolve_log_msg_module_name(module_name, log_msg)
    log_msg = log_filter(log_msg)
    Gb.HALogger.error(log_msg)
    write_ic3_debug_log_recd(log_msg)

#--------------------------------------------------------------------
def log_exception(err):
    Gb.HALogger.exception(err)
    write_ic3_debug_log_recd(traceback.format_exc())

#--------------------------------------------------------------------
def log_debug_msg(devicename, log_msg="+"):
    if Gb.log_debug_flag is False:
        return

    devicename, log_msg = resolve_system_event_msg(devicename, log_msg)
    dn_str = '' if devicename == '*' else (f"{devicename} > ")
    log_msg = (f"{Gb.trace_prefix}{dn_str}{str(log_msg).replace(CRLF, ', ')}")

    write_ic3_debug_log_recd(log_filter(log_msg))

#--------------------------------------------------------------------
def log_start_finish_update_banner(start_finish_char, devicename,
            method, update_reason):
    '''
    Display a banner in the log file at the start and finish of a
    device update cycle
    '''

    if Gb.log_debug_flag is False and Gb.log_rawdata_flag is False:
        return

    start_finish_char = '▼─▽─▼' if start_finish_char.startswith('s') else '▲─△─▲'
    start_finish_chars = (f"────{start_finish_char}────")
    Device = Gb.Devices_by_devicename[devicename]
    log_msg =   (f"{start_finish_chars} ▷▷ {method} ◁◁ {devicename}, "
                f"CurrZone-{Device.sensor_zone}, {update_reason} "
                f"{start_finish_chars}").upper()

    log_debug_msg(devicename, log_msg)

#--------------------------------------------------------------------
def log_rawdata(title, rawdata, log_rawdata_flag=False):
    '''
    Add raw data records to the HA log file for debugging purposes.

    This is used in Pyicloud_ic3 to log all data requests and responses,
    and in other routines in iCloud3 when device_tracker or other entities
    are read from or updated in HA.

    A filter is applied to the raw data and dictionaries and lists in the
    data to eliminate displaying uninteresting fields. The fields, dictionaries,
    and list are defined in the FILTER_FIELDS, FILTER_DATA_DICTS and
    FILTER_DATA_LISTS.
    '''

    if Gb.log_rawdata_flag is False or rawdata is None:
        return

    filtered_data = {}
    rawdata_data = {}

    try:
        if 'raw' in rawdata or log_rawdata_flag:
            log_debug_msg(f"{'─'*8} {title.upper()} {'─'*8}")
            log_debug_msg(rawdata)
            return

        rawdata_data['filter'] = {k: v for k, v in rawdata['filter'].items()
                                        if k in FILTER_FIELDS}
    except:
        rawdata_data['filter'] = {k: v for k, v in rawdata.items()
                                        if k in FILTER_FIELDS}

    if rawdata_data['filter']:
        for data_dict in FILTER_DATA_DICTS:
            filter_results = _filter_data_dict(rawdata_data['filter'], data_dict)
            if filter_results:
                filtered_data[f"◤{data_dict.upper()}◥ ({data_dict})"] = filter_results

        for data_list in FILTER_DATA_LISTS:
            if data_list in rawdata_data['filter']:
                filter_results = _filter_data_list(rawdata_data['filter'][data_list])
                if filter_results:
                    filtered_data[f"◤{data_list.upper()}◥ ({data_list})"] = filter_results

    try:
        log_msg = None
        if filtered_data:
            log_msg = f"{filtered_data}"
        else:
            if 'id' in rawdata_data and len(rawdata_data['id']) > 10:
                rawdata_data['id'] = f"{rawdata_data['id'][:10]}..."
            elif 'id' in rawdata_data['filter'] and len(rawdata_data['filter']['id']) > 10:
                rawdata_data['filter']['id'] = f"{rawdata_data['filter']['id'][:10]}..."

            if rawdata_data:
                log_msg = f"{rawdata_data}"
            else:
                log_msg = f"{rawdata[:15]}"

    except:
        pass

    if log_msg != {}:
        log_debug_msg(f"{'─'*8} {title.upper()} {'─'*8}")
        log_debug_msg(log_msg)

    return

#--------------------------------------------------------------------
def _filter_data_dict(rawdata_data, data_dict_items):
    try:
        filter_results = {k: v for k, v in rawdata_data[data_dict_items].items()
                                    if k in FILTER_FIELDS}

        if 'id' in filter_results and len(filter_results['id']) > 10:
            filter_results['id'] = f"{filter_results['id'][:10]}..."

        return filter_results

    except Exception as err:
        return {}

#--------------------------------------------------------------------
def _filter_data_list(rawdata_data_list):

    try:
        filtered_list = []
        for list_item in rawdata_data_list:
            filter_results = {k: v for k, v in list_item.items()
                                    if k in FILTER_FIELDS}
            if id := filter_results.get('id'):
                if id in Gb.Devices_by_icloud_device_id:
                    filtered_list.append(f"◉◉ <{filter_results['name']}> ◉◉")
                    continue

            if 'id' in filter_results:
                if len(filter_results['id']) > 10:
                    filter_results['id'] = f"{filter_results['id'][:10]}..."

            if 'location' in filter_results and filter_results['location']:
                filter_results['location'] = {k: v for k, v in filter_results['location'].items()
                                                    if k in FILTER_FIELDS}
                filter_results['location'].pop('address', None)

            if filter_results:
                filtered_list.append(f"◉◉ <{filter_results['name']}> ⭑⭑ {filter_results} ◉◉")
                #filtered_list.append('◉◉◉◉◉')

        return filtered_list

    except:
        return []


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ERROR MESSAGE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def internal_error_msg(err_text, msg_text=''):

    caller   = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename).split('.')[0][:12]
    try:
        parent = getframeinfo(stack()[2][0])
        parent_lineno = parent.lineno
    except:
        parent_lineno = ''

    if msg_text:
        msg_text = (f", {msg_text}")

    log_msg =  (f"INTERNAL ERROR-RETRYING ({parent_lineno}>{caller.lineno}{msg_text} -- "
                f"{filename}»{caller.function[:20]} -- {err_text})")
    post_error_msg(log_msg)

    attrs = {}
    attrs[INTERVAL]         = 0
    attrs[NEXT_UPDATE_TIME] = DATETIME_ZERO

    return attrs

#--------------------------------------------------------------------
def internal_error_msg2(err_text, traceback_format_exec_obj):
    post_internal_error(err_text, traceback_format_exec_obj)

def post_internal_error(err_text, traceback_format_exec_obj='+'):

    '''
    Display an internal error message in the Event Log and the in the HA log file.

    Parameters:
    - traceback_format_exc  = traceback.format_exec_obj object with the error information

    Example traceback_format_exec_obj():
        Traceback (most recent call last):
        File "/config/custom_components/icloud3_v3/determine_interval.py", line 74, in determine_interval
        distance = location_data[76]
        IndexError: list index out of range
    '''
    if traceback_format_exec_obj == '+':
        traceback_format_exec_obj = err_text
        err_text = ''

    tb_err_msg = traceback_format_exec_obj()
    log_error_msg(tb_err_msg)

    err_lines = tb_err_msg.split('\n')
    err_lines_f = []
    for err_line in err_lines:
        err_line_f = err_line.strip(' ').replace(Gb.icloud3_directory, '')
        err_line_f = err_line_f.replace('File ', '').replace(', line ', f"{CRLF_DOT}Line.. > ")
        if err_line_f:
            err_lines_f.append(err_line_f)

    err_msg = (f"{EVLOG_ERROR}INTERNAL ERROR > {err_text}")
    try:
        n = len(err_lines_f) - 1

        if n >= 5:
            err_msg += (f"{CRLF_DOT}File... > {err_lines_f[n-4]}(...)"
                        f"{CRLF_DOT}Code > {err_lines_f[n-3]}")
        err_msg += (f"{CRLF_DOT}File... > {err_lines_f[n-2]}(...)"
                    f"{CRLF_DOT}Code > {err_lines_f[n-1]}"
                    f"{CRLF_DOT}Error. > {err_lines_f[n]}")
    except Exception as err:
        err_msg += (f"{CRLF_DOT}Error > Unknown")
        pass

    post_event(err_msg)

    attrs = {}
    attrs[INTERVAL]         = '0 sec'
    attrs[NEXT_UPDATE_TIME] = DATETIME_ZERO

    return attrs

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEBUG TRACE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def _trace(devicename, log_text='+'):

    devicename, log_text = resolve_system_event_msg(devicename, log_text)

    header_msg = _called_from()
    post_event(devicename, f"^3^{header_msg} {log_text}")

#--------------------------------------------------------------------
def _traceha(log_text, v1='+++', v2='', v3='', v4='', v5=''):
    '''
    Display a message or variable in the HA log file
    '''
    try:
        if v1 == '+++':
            log_msg = ''
        else:
            log_msg = (f"|{v1}|-|{v2}|-|{v3}|-|{v4}|-|{v5}|")

        if log_text in Gb.Devices_by_devicename:
            trace_msg = (f"{Gb.trace_prefix}{log_text} ::: TRACE ::: {log_msg}")
        else:
            trace_msg = (f"{Gb.trace_prefix} ::: TRACE ::: {log_text}, {log_msg}")

        Gb.HALogger.info(trace_msg)
        # if Gb.iC3DebugLogFile:
        write_ic3_debug_log_recd(trace_msg, force_write=True)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _called_from():

    #if Gb.log_debug_flag is False and Gb.log_rawdata_flag is False:
    #    return ''

    caller = None
    level = 0
    while level < 5:
        level += 1
        caller = getframeinfo(stack()[level][0])
        if caller.filename.endswith('messaging.py') is False:
            break

    if caller is None:
        return ''

    caller_path = caller.filename.replace('.py','')
    caller_filename = f"{caller_path.split('/')[-1]}........"
    caller_lineno = caller.lineno

    return f"[{caller_filename[:12]}:{caller_lineno:04}] "
