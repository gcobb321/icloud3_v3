

from ..globals          import GlobalVariables as Gb
from ..const_general    import (NOT_HOME, ICLOUD3_ERROR_MSG, EVLOG_DEBUG, EVLOG_ERROR,
                                STATIONARY, NEW_LINE, CRLF, CRLF_DOT, DATETIME_ZERO, RARROW, )
from ..const_attrs      import (NEXT_UPDATE_TIME, INTERVAL, LOCATION, ID,
                                LOG_RAWDATA_FIELDS, )


import os, sys
import traceback
from inspect import getframeinfo, stack
import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

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

#####################################################################
#
#   iOS App Device utilities
#
#####################################################################
def resolve_system_event_msg(devicename, event_msg):
    if event_msg == '+':
        return ("*", devicename)
    else:
        return (devicename, event_msg)

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
def display_info_msg(Device, info_msg):
    '''
    Display a status message in the Device's info sensor.
    '''
    Device.display_info_msg(info_msg)
    return

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
            Device.display_info_msg(Device, ICLOUD3_ERROR_MSG)

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
def log_info_msg(log_msg):
    _LOGGER.info(log_filter(log_msg))

#--------------------------------------------------------------------
def log_warning_msg(log_msg):
    _LOGGER.warning(log_filter(log_msg))

#--------------------------------------------------------------------
def log_error_msg(log_msg):
    _LOGGER.error(log_filter(log_msg))

#--------------------------------------------------------------------
def log_exception(err):
    _LOGGER.exception(err)

#--------------------------------------------------------------------
def log_debug_msg(devicename, log_msg="+"):
    devicename, log_msg = resolve_system_event_msg(devicename, log_msg)
    dn_str = '' if devicename == '*' else (f"{devicename} > ")
    log_msg = (f"{dn_str}{str(log_msg).replace(CRLF, ', ')}")
    log_info_msg(log_msg)

#--------------------------------------------------------------------
def log_rawdata(title, raw_data, log_rawdata=False):
        ''' Add log_msg to HA log only when "log_level: rawdata" '''
        display_title = title.replace(" ",".").upper()

        if ((Gb.log_rawdata_flag or log_rawdata) and Gb.log_rawdata_flag_unfiltered):
            _LOGGER.info(f"{'┬─┬'*8}─ {display_title} ─{'┬─┬'*8}")
            _LOGGER.info(f"{raw_data}")
            _LOGGER.info("-"*80)
            return

        filtered_data = {k: v for k, v in raw_data.items() if k in LOG_RAWDATA_FIELDS}

        if ID in filtered_data:
            filtered_data[ID] = filtered_data[ID][:10]

        for friends_list in ['following', 'followers', 'contactDetails']:
            if friends_list in raw_data:
                try:
                    friends_filtered_data = []
                    for friend in raw_data[friends_list]:
                        friend_data = {k: v for k, v in friend.items() if k in LOG_RAWDATA_FIELDS}
                        if ID in friend:
                            friend_data[ID] = friend_data[ID][:10]

                        friends_filtered_data.append(friend_data)

                    filtered_data[friends_list] = friends_filtered_data
                except:
                    pass

        if 'locations' in raw_data:
            locations_filtered_data = []
            for location in raw_data['locations']:
                loc_filtered_data = {k: v for k, v in location.items() if k in LOG_RAWDATA_FIELDS}
                if location['location']:
                    loc_filtered_data['location'] = {k: v for k, v in location['location'].items() if k in LOG_RAWDATA_FIELDS}
                    locations_filtered_data.append(loc_filtered_data)

            filtered_data['locations'] = locations_filtered_data

        if LOCATION in raw_data:
            location_data = {k: v for k, v in raw_data[LOCATION].items() if k in LOG_RAWDATA_FIELDS}
            filtered_data[LOCATION] = location_data

        if Gb.log_rawdata_flag or log_rawdata:
            _LOGGER.info(f"{'┬─┬'*8}{display_title}{'┬─┬'*8}")
            _LOGGER.info(f"{filtered_data}")

            _LOGGER.info("-"*80)
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
        err_line_f = err_line.strip(' ').replace(Gb.icloud3_dir, '')
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