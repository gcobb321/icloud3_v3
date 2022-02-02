

from ..global_variables import GlobalVariables as Gb
from ..const            import (NOT_HOME, ICLOUD3_ERROR_MSG, EVLOG_DEBUG, EVLOG_ERROR, EVLOG_INIT_HDR,
                                STATIONARY, NEW_LINE, CRLF, CRLF_DOT, DATETIME_ZERO, RARROW,
                                NEXT_UPDATE_TIME, INTERVAL, LOCATION, ID,
                                LOG_RAWDATA_FIELDS, LOCATION,
                                CONF_UPDATE_DATE,
                                CF_PROFILE, CF_DATA, CF_DATA_TRACKING, CF_DATA_DEVICES, CF_DATA_GENERAL,
                                CF_DATA_SENSORS,
                                LATITUDE,  LONGITUDE, LOCATION_SOURCE, TRACKING_METHOD,
                                ZONE, ZONE_DATETIME, INTO_ZONE_DATETIME, LAST_ZONE,
                                TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
                                TRIGGER, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
                                INTERVAL, ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, TRAVEL_DISTANCE,
                                DEVICE_STATUS, LOW_POWER_MODE,
                                TRACKING, DEVICENAME_IOSAPP,
                                AUTHENTICATED,
                                LAST_UPDATE_TIME, UPDATE_DATETIME, NEXT_UPDATE_TIME, LOCATED_DATETIME,
                                INFO, GPS_ACCURACY, GPS, POLL_COUNT, VERT_ACCURACY, ALTITUDE,
                                ICLOUD3_VERSION,
                                BADGE,
                                )


import os
import json
import traceback
from inspect import getframeinfo, stack
from collections import OrderedDict
# import logging
# # _LOGGER = logging.getLogger(__name__)
# _LOGGER = logging.getLogger(f"icloud3")

FILTER_DATA_DICTS = ['data', 'userInfo', 'dsid', 'dsInfo', 'webservices', 'locations',]
                    #  'devices', 'content', 'followers', 'following', 'contactDetails',]
FILTER_DATA_LISTS = ['devices', 'content', 'followers', 'following', 'contactDetails',]
FILTER_FIELDS = [
        ICLOUD3_VERSION, AUTHENTICATED,
        LATITUDE,  LONGITUDE, LOCATION_SOURCE, TRACKING_METHOD,
        ZONE, ZONE_DATETIME, INTO_ZONE_DATETIME, LAST_ZONE,
        TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
        TRIGGER, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
        INTERVAL, ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
        TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, TRAVEL_DISTANCE,
        DEVICE_STATUS, LOW_POWER_MODE, BADGE,
        LAST_UPDATE_TIME, UPDATE_DATETIME, NEXT_UPDATE_TIME, LOCATED_DATETIME,
        INFO, GPS_ACCURACY, GPS, POLL_COUNT, VERT_ACCURACY, ALTITUDE,
        'ResponseCode',
        'id', 'firstName', 'lastName', 'name', 'fullName', 'appleId', 'emails', 'phones',
        'deviceStatus', 'batteryLevel', 'membersInfo',
        'batteryStatus', 'deviceDisplayName', 'modelDisplayName', 'deviceClass',
        'isOld', 'isInaccurate', 'timeStamp', 'altitude', 'location', 'latitude', 'longitude',
        'horizontalAccuracy', 'verticalAccuracy',
        'hsaVersion', 'hsaEnabled', 'hsaTrustedBrowser', 'locale', 'appleIdEntries', 'statusCode',
        'familyEligible', 'findme', 'requestInfo',
        'invitationSentToEmail', 'invitationAcceptedByEmail', 'invitationFromHandles',
        'invitationFromEmail', 'invitationAcceptedHandles',
        'data', 'userInfo', 'dsid', 'dsInfo', 'webservices', 'locations',
        'devices', 'content', 'followers', 'following', 'contactDetails', ]

#####################################################################
#
#   Data verification functions
#
#####################################################################
def combine_lists(parm_lists):
    '''
    Take a list of lists and return a single list of all of the items.
        [['a,b,c'],['d,e,f']] --> ['a','b','c','d','e','f']
    '''
    new_list = []
    for lists in parm_lists:
        lists_items = lists.split(',')
        for lists_item in lists_items:
            new_list.append(lists_item)

    return new_list

#--------------------------------------------------------------------
def instr(string, find_string):
    if find_string is None:
        return False
    else:
        return (str(string).find(find_string) >= 0)

#--------------------------------------------------------------------
def is_statzone(string):
        return (str(string).find(STATIONARY) >= 0)

#--------------------------------------------------------------------
def isnumber(string):

    try:
        test_number = float(string)

        return True
    except:
        return False

#--------------------------------------------------------------------
def inlist(string, list_items):
    for item in list_items:
        if str(string).find(item) >= 0:
            return True

    return False

#--------------------------------------------------------------------
def round_to_zero(value):
    if abs(value) < .05: value = 0
    return round(value, 2)

#--------------------------------------------------------------------
def is_inzone_zone(zone):
    return (zone != NOT_HOME)

#--------------------------------------------------------------------
def isnot_inzone_zone(zone):
    return (zone == NOT_HOME)

#--------------------------------------------------------------------
def ordereddict_to_dict(odict_item):
    if isinstance(odict_item, OrderedDict):
        dict_item = dict(odict_item)
    else:
        dict_item = odict_item
    try:
        for key, value in dict_item.items():
            dict_item[key] = ordereddict_to_dict(value)
            if isinstance(value, list):
                new_value = []
                for item in value:
                    if isinstance(item, OrderedDict):
                        item = ordereddict_to_dict(item)
                    new_value.append(item)
                dict_item[key] = new_value
    except AttributeError:
        pass

    return dict_item

#####################################################################
#
#   Common Utilities
#
#####################################################################
def read_storage_icloud3_configuration_file():
    '''
    Read the config/.storage/.icloud3.configuration file and extract the
    data into the Global Variables
    '''

    try:
        with open(Gb.icloud3_config_filename, 'r') as f:
            Gb.conf_file_data = json.load(f)
            Gb.conf_profile   = Gb.conf_file_data[CF_PROFILE]
            Gb.conf_data      = Gb.conf_file_data[CF_DATA]

            Gb.conf_tracking  = Gb.conf_data[CF_DATA_TRACKING]
            Gb.conf_devices   = Gb.conf_data[CF_DATA_TRACKING][CF_DATA_DEVICES]
            Gb.conf_general   = Gb.conf_data[CF_DATA_GENERAL]
            Gb.conf_sensors   = Gb.conf_data[CF_DATA_SENSORS]

        return True

    except Exception as err:
        log_exception(err)

    return False

#--------------------------------------------------------------------
def write_storage_icloud3_configuration_file():
    '''
    Update the config/.storage/.icloud3.configuration file
    '''

    try:
        with open(Gb.icloud3_config_filename, 'w', encoding='utf8') as f:
            Gb.conf_profile[CONF_UPDATE_DATE] = ''
            json.dump(Gb.conf_file_data, f, indent=4)

        return True

    except Exception as err:
        log_exception(err)

    return False

#--------------------------------------------------------------------
def resolve_system_event_msg(devicename, event_msg):
    if event_msg == '+':
        return ("*", devicename)
    else:
        return (devicename, event_msg)

#--------------------------------------------------------------------
def resolve_log_msg_module_name(module_name, log_msg):
    if log_msg == "+":
        return (module_name)
    else:
        return (f"[{module_name}] {log_msg}")

#--------------------------------------------------------------------
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
# def display_info_msg(Device, info_msg):
#     '''
#     Display a status message in the Device's info sensor.
#     '''
#     Device.display_info_msg(info_msg)
#     return

#--------------------------------------------------------------------
def post_event(devicename, event_msg='+'):
    '''
    Add records to the Event Log table. This does not change
    the info displayed on the Event Log screen. Use the
    '_update_event_log_display' function to display the changes.
    '''
    devicename, event_msg = resolve_system_event_msg(devicename, event_msg)
    Gb.EvLog.post_event(devicename, event_msg)

    if Gb.log_debug_flag:
        event_msg = (f"{devicename} > {str(event_msg).replace(CRLF, '. ')}")
        log_info_msg(event_msg)
    elif (Gb.start_icloud3_inprocess_flag
            and event_msg.startswith(EVLOG_DEBUG) is False):
        if event_msg.startswith(EVLOG_INIT_HDR):
            Gb.startup_log_msgs += f"\n\n{event_msg[3:].upper()}"
        else:
            Gb.startup_log_msgs += f"\n{event_msg}"


#--------------------------------------------------------------------
def post_startup_event(devicename, event_msg="+"):
    '''
    Post the start event and add it to the HA log file
    '''
    devicename, event_msg = resolve_system_event_msg(devicename, event_msg)

    if event_msg != NEW_LINE:
        post_event(devicename, event_msg)

    if Gb.log_debug_flag:
        log_info_msg(event_msg)
    else:
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
def post_log_info_msg(devicename, event_msg='+'):
    ''' Always add log_msg to HA log '''

    devicename, event_msg = resolve_system_event_msg(devicename, event_msg)
    post_event(devicename, event_msg)

    log_msg = (f"{devicename} > {str(event_msg).replace(CRLF, '. ')}")
    log_info_msg(log_msg)

#--------------------------------------------------------------------
def post_monitor_msg(devicename, event_msg='+'):
    '''
    Post the event message and display it in Event Log and HA log
    when the config parameter "log_level: eventlog" is specified or
    the Show Tracking Monitors was selected in Event Log > Actions
    '''
    devicename, event_msg = resolve_system_event_msg(devicename, event_msg)
    post_event(devicename, f"{EVLOG_DEBUG}{event_msg}")

    if Gb.evlog_trk_monitors_flag or Gb.log_debug_flag:
        log_debug_msg(event_msg)

#--------------------------------------------------------------------
def log_info_msg(module_name, log_msg='+'):
    log_msg = resolve_log_msg_module_name(module_name, log_msg)
    Gb.HALogger.info(log_filter(log_msg))

#--------------------------------------------------------------------
def log_warning_msg(module_name, log_msg='+'):
    log_msg = resolve_log_msg_module_name(module_name, log_msg)
    Gb.HALogger.warning(log_filter(log_msg))

#--------------------------------------------------------------------
def log_error_msg(module_name, log_msg='+'):
    log_msg = resolve_log_msg_module_name(module_name, log_msg)
    Gb.HALogger.error(log_filter(log_msg))

#--------------------------------------------------------------------
def log_exception(err):
    Gb.HALogger.exception(err)

#--------------------------------------------------------------------
def log_debug_msg(devicename, log_msg="+"):
    devicename, log_msg = resolve_system_event_msg(devicename, log_msg)
    dn_str = '' if devicename == '*' else (f"{devicename} > ")
    log_msg = (f"{dn_str}{str(log_msg).replace(CRLF, ', ')}")
    log_info_msg(log_msg)

#--------------------------------------------------------------------
def log_rawdata(title, rawdata):
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

    if rawdata is None:
        return

    log_info_msg(f"{'─'*8} {title.upper()} {'─'*8}")

    filtered_data = {}
    rawdata_data = {}
    try:
        if 'raw' in rawdata:
            log_info_msg(rawdata)
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
                filtered_data[f"◤◤{data_dict.upper()}◥◥ ({data_dict})"] = filter_results

        for data_list in FILTER_DATA_LISTS:
            if data_list in rawdata_data['filter']:
                filter_results = _filter_data_list(rawdata_data['filter'][data_list])
                if filter_results:
                    filtered_data[f"◤◤{data_list.upper()}◥◥ ({data_list})"] = filter_results

    try:
        if filtered_data:
            log_info_msg(f"{filtered_data}")
        else:
            if 'id' in rawdata_data and len(rawdata_data['id']) > 10:
                rawdata_data['id'] = f"{rawdata_data['id'][:10]}..."
            elif 'id' in rawdata_data['filter'] and len(rawdata_data['filter']['id']) > 10:
                rawdata_data['filter']['id'] = f"{rawdata_data['filter']['id'][:10]}..."

            log_info_msg(f"{rawdata_data}")
    except:
        pass

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
            if 'id' in filter_results and len(filter_results['id']) > 10:
                filter_results['id'] = f"{filter_results['id'][:10]}..."

            if 'location' in filter_results and filter_results['location']:
                filter_results['location'] = {k: v for k, v in filter_results['location'].items()
                                                    if k in FILTER_FIELDS}
            if filter_results:
                filtered_list.append(filter_results)
                filtered_list.append('◉')

        return filtered_list

    except:
        return []


#--------------------------------------------------------------------
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
        err_line_f = err_line_f.replace('File ', '').replace(', line ', f"{CRLF_DOT} Line.. > ")
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

#--------------------------------------------------------------------
def _trace(devicename, log_text='+'):
    caller   = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename).split('.')[0][:20]
    try:
        parent = getframeinfo(stack()[2][0])
        parent_lineno = parent.lineno
    except:
        parent_lineno = ''

    devicename, log_text = resolve_system_event_msg(devicename, log_text)
    header_msg = (f"{parent_lineno}->{caller.lineno}, {filename} ({caller.function}) > ")
    post_event(f"^5^{header_msg}{log_text}")

#--------------------------------------------------------------------
def _traceha(log_text, v1='+++', v2='', v3='', v4='', v5=''):
    '''
    Display a message or variable in the HA log file
    '''
    caller = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename).split('.')[0][:20]
    try:
        parent = getframeinfo(stack()[2][0])
        parent_lineno = parent.lineno
    except:
        parent_lineno = ''

    header_msg = (f"{parent_lineno}{RARROW}{caller.lineno}, {filename} ({caller.function[:18]})»»")
    log_msg    = (f"{header_msg}{log_text}")
    if v1 != '+++':
        log_msg += (f" {RARROW} |{v1}|-|{v2}|-|{v3}|-|{v4}|-|{v5}|")

    log_info_msg(log_msg)