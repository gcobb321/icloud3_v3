

from ..globals           import GlobalVariables as Gb
from ..const_general     import (HOME, VALID_TIME_TYPES, APPLE_DEVICE_TYPES, DEVICE_TYPE_FNAME, ICLOUD,
                                NEW_LINE, CRLF, CRLF_DOT, CRLF_CHK, UNKNOWN,
                                WAZE, CALC, NEW_LINE, EVLOG_ERROR, EVLOG_NOTICE, EVLOG_ALERT, EVLOG_DEBUG,
                                CONFIG_IC3, DEFAULT_CONFIG_IC3_FILE_NAME, )
from ..const_attrs       import *

from ..helpers.base      import (instr, isnumber,
                                post_event, post_error_msg, post_log_info_msg, post_monitor_msg, post_startup_event,
                                log_debug_msg, log_exception, _trace, _traceha, )
from ..helpers.time      import (secs_to_time_str, time_str_to_secs, )


import os
import shutil
from re import match
import homeassistant.util.dt as dt_util
from   homeassistant.util    import slugify
import homeassistant.util.yaml.loader as yaml_loader


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>


#######################################################################
#
#   EXTRACT ICLOUD3 PARAMETERS FROM THE CONFIG_IC3.YAML PARAMETER FILE.
#
#   The ic3 parameters are specified in the HA configuration.yaml file and
#   processed when HA starts. The 'config_ic3.yaml' file lets you specify
#   parameters at HA startup time or when iCloud3 is restarted using the
#   Restart-iC3 command on the Event Log screen. When iC3 is restarted,
#   the parameters will override those specified at HA startup time.
#
#   1. You can, for example, add new tracked devices without restarting HA.
#   2. You can specify the username, password and tracking method in this
#      file but these items are onlyu processed when iC3 initially loads.
#      A restart will discard these items
#
#   Default file is config/custom_components/icloud3/config-ic3.yaml
#   if no '/' on the config_ic3_filename parameter:
#       check the default directory
#       if not found, check the /config directory
#
#######################################################################
def get_config_ic3_parameters():

    if Gb.config_ic3_filename:
        log_success_msg, log_error_msg = \
                _get_recds_from_config_ic3(Gb.config_ic3_filename)

        if log_error_msg != "":
            event_msg =(f"iCloud3 Error processing '{Gb.config_ic3_filename}` parameters. "
                        f"The following parameters are invalid >{log_error_msg}")
            post_error_msg(event_msg)

    return

#-------------------------------------------------------------------------
def _get_recds_from_config_ic3(config_filename):
    '''
    OrderedDict([('devices', [OrderedDict([('device_name', 'Gary-iPhone'),
    ('name', 'Gary'), ('email', 'gcobb321@gmail.com'),
    ('picture', 'gary.png'), ('track_from_zone', 'warehouse')]), OrderedDict([('device_name', 'lillian_iphone'),
    ('name', 'Lillian'), ('picture', 'lillian.png'), ('email', 'lilliancobb321@gmail.com')])]),
    ('display_text_as', ['gcobb321@gmail.com > gary_2fa@email.com', 'lilliancobb321@gmail.com > lillian_2fa@email.com',
    'twitter:@lillianhc > twitter:@lillian_twitter_handle', 'gary-real-email@gmail.com > gary_secret@email.com',
    'lillian-real-email@gmail.com > lillian_secret@email.com']),
    ('inzone_interval', '30 min'),
    ('display_zone_format', FNAME)])
    '''
    try:
        log_success_msg = ""
        log_error_msg   = ""
        success_msg     = ""
        error_msg       = ""
        devices_list    = []

        Gb.config_track_devices_fields = []
        Gb.config_ic3_track_devices_fields = []

        try:
            config_yaml_recds = yaml_loader.load_yaml(config_filename)
        except Exception as err:
            #log_exception(err)

            #A missing quote mark gives the following error:
            #while parsing a block mapping in "/config/config_ic3.yaml", line 18, column 1
            #expected <block end>, but found '<scalar>' in "/config/config_ic3.yaml", line 47, column 31
            err_text = str(err)
            err_parts = err_text.split(', ')
            error_msg = (f"iCloud3 Error > Invalid configuration parameter > "
                    f"{CRLF_DOT}File-{config_filename}, {err_parts[4]}"
                    f"{CRLF_DOT}A mismatched quote (`) was found. Can not continue. Setup will be aborted.")
            post_error_msg(error_msg)
            return log_success_msg, log_error_msg

        for pname, pvalue in config_yaml_recds.items():
            if pname == CONF_DEVICES:
                Gb.config_ic3_track_devices_fields.extend(\
                        _get_devices_list_from_config_devices_parm(pvalue, CONFIG_IC3))

            else:
                success_msg, error_msg = \
                        _set_non_device_parm_in_config_parameter_dictionary(pname, pvalue)

                log_success_msg += success_msg
                log_error_msg   += error_msg


    except Exception as err:
        log_exception(err)
        pass

    post_event("Config Parameters > Loaded Other Parameters")
    return log_success_msg, log_error_msg

#-------------------------------------------------------------------------
def _get_devices_list_from_config_devices_parm(conf_devices_parameter, source_file):
    '''
    Process the CONF_DEVICES parameter. This is the general routine for parsing
    the parameter and creating a dictionary (devices_list) containing values
    associated with each device_name.

    Input:      The CONF_DEVICES parameter
    Returns:    The dictionary with the fields associated with all of the devices
    '''
    devices_list = []

    for device in conf_devices_parameter:
        device_fields = {}
        for pname, pvalue in device.items():
            if pname in VALID_CONF_DEVICES_ITEMS:
                if pname == CONF_DEVICENAME:
                    devicename        = slugify(pvalue)
                    name, device_type = _extract_name_device_type(pvalue)
                    device_fields[CONF_DEVICENAME]  = devicename
                    device_fields[CONF_DEVICE_TYPE] = device_type
                    device_fields[CONF_NAME]        = name
                    device_fields[CONF_CONFIG]      = source_file
                    device_fields[CONF_SOURCE]      = 'Config Devices Parameter'

                #You can track from multiple zones, cycle through zones and check each one
                #The value can be zone name or zone friendly name. Change to zone name.
                elif pname == CONF_TRACK_FROM_ZONE:
                    device_fields[CONF_TRACK_FROM_ZONE] = ''
                    pzones = pvalue.replace('zone.', '').replace(HOME, '')
                    pzones = pzones.split(',')
                    pvalue = ''
                    zone_list = str(Gb.Zones_by_zone).replace(': ', '').replace("'", "")
                    for pzone in pzones:
                        for Zone in Gb.Zones:
                            if pzone == Zone.zone or pzone == Zone.fname:
                                pvalue += (f"{Zone.zone},")
                                break
                        else:
                            _display_config_parameter_error_msg(CONF_TRACK_FROM_ZONE, pzone,
                                    zone_list, '(Invalid Zone Name)')
                    if pvalue:
                        device_fields[CONF_TRACK_FROM_ZONE] = pvalue[:-1]

                elif pname == CONF_IOSAPP_SUFFIX:
                        device_fields[CONF_IOSAPP_SUFFIX] = pvalue
                        device_fields.pop(CONF_IOSAPP_ENTITY, None)
                elif pname == CONF_IOSAPP_ENTITY:
                        device_fields[CONF_IOSAPP_ENTITY] = pvalue
                        device_fields.pop(CONF_IOSAPP_SUFFIX, None)

                elif pname == CONF_INZONE_INTERVAL:
                    device_fields[CONF_INZONE_INTERVAL] = time_str_to_secs(pvalue)

                elif pname in [CONF_NOIOSAPP, CONF_NO_IOSAPP] and pvalue:
                    device_fields[CONF_IOSAPP_INSTALLED] = not pvalue

                elif pname == CONF_TRACKING_METHOD:
                    pvalue = '' if pvalue == ICLOUD else pvalue
                    device_fields[CONF_TRACKING_METHOD] = pvalue

                else:
                    device_fields[pname] = pvalue
            else:
                _display_config_parameter_error_msg(
                            pname, pvalue, VALID_CONF_DEVICES_ITEMS)

        devices_list.append(device_fields)

    post_event(f"Config Parameters > Loaded tracked devices ({source_file})")
    return devices_list

#-------------------------------------------------------------------------
def _set_non_device_parm_in_config_parameter_dictionary(pname, pvalue):
    '''
    Set the config_parameters[key] master parameter dictionary from the
    config_ic3 parameter file

    Input:      parameter name & value
    Output:     Valid parameters are added to the config_parameter[pname] dictionary
    '''
    try:
        success_msg = ""
        error_msg   = ""
        if pname == "":
            return ("", "")

        #These parameters can not be changed
        if pname in [CONF_GROUP, CONF_USERNAME, CONF_PASSWORD,
                    CONF_CREATE_SENSORS, CONF_EXCLUDE_SENSORS,
                    CONF_ENTITY_REGISTRY_FILE, CONF_CONFIG_IC3_FILE_NAME]:
            return ("", "")
        log_msg = (f"config_ic3 Parameter > {pname}: {pvalue}")
        post_monitor_msg(log_msg)

        if pname in Gb.config_parm:
            Gb.config_parm[pname] = pvalue

        else:
            error_msg = (f"{CRLF_DOT}{pname}: {pvalue}")
            log_msg = (f"Invalid parameter-{pname}: {pvalue}")
            log_debug_msg(log_msg)

    except Exception as err:
        log_exception(err)
        error_msg = (f"{CRLF_DOT}{err}")

    if error_msg == "":
        success_msg = (f"{CRLF_DOT}{pname}: {pvalue}")

    return (success_msg, error_msg)


#######################################################################
#
#   GET DEVICES FROM HA CONFIGURATION.YAML devices parameter
#
#######################################################################
def get_devices_list_from_ha_config_yaml_file():

    try:
        # Extract device fields from ha config file 'devices:' parameter
        Gb.config_track_devices_fields.extend(
                _get_devices_list_from_config_devices_parm(\
                        Gb.config_devices_schema, 'HA config'))

        # Get device fields from iCloud3 config_ic3 file
        Gb.config_track_devices_fields.extend(Gb.config_ic3_track_devices_fields)

        # See if there are any changes to the devices parameter on a restart. If nothing
        # changed, only change parameter values and bypass Stages 2, 3 & 4.
        Gb.config_track_devices_change_flag = False
        if Gb.config_track_devices_fields != Gb.config_track_devices_fields_last_restart:
            Gb.config_track_devices_fields_last_restart = []
            Gb.config_track_devices_fields_last_restart.extend(Gb.config_track_devices_fields)
            Gb.config_track_devices_change_flag = True

        # Changes to toe tracking method require a full iCloud3 restart
        if Gb.tracking_method_config != Gb.tracking_method_config_last_restart:
            Gb.tracking_method_config_last_restart = Gb.tracking_method_config
            Gb.config_track_devices_change_flag = True

    except Exception as err:
        log_exception(err)

#######################################################################
#
#   VALIDATE THE CONFIGURATION PARMATERS
#
#######################################################################
def validate_config_parameters():
    '''
    Cycle through the each of the validate_parameters_type lists and
    validate the parameter values for each list type.

    If the value is invalid, display an error message in the event log
    and reset the config_parameter[xxx] value to it's default value.
    '''

    #validate list parameters: CONF_UNIT_OF_MEASUREMENT: ['mi', 'km']
    for pname in VALIDATE_PARAMETER_LIST:
        pvalue       = Gb.config_parm.get(pname)
        valid_values = VALIDATE_PARAMETER_LIST.get(pname)
        if pvalue not in valid_values:
            _display_config_parameter_error_msg(pname, pvalue, valid_values)

    #validate true/false parameters: CONF_CENTER_IN_ZONE (center_in_zone: false)
    for pname in VALIDATE_PARAMETER_TRUE_FALSE:
        pvalue       = Gb.config_parm.get(pname)
        valid_values = [True, False]
        if pvalue not in valid_values:
            _display_config_parameter_error_msg(pname, pvalue, valid_values)

    #validate number parameters: CONF_TRAVEL_TIME_FACTOR (travel_time_factor: .6)
    for pname in VALIDATE_PARAMETER_NUMBER:
        pvalue       = Gb.config_parm.get(pname)
        valid_values = 'Number'
        if pvalue and isnumber(str(pvalue)) is False:
            _display_config_parameter_error_msg(pname, pvalue, valid_values)

    #validate time parameters: CONF_INZONE_INTERVAL (inzone_interval: 30 min)
    for pname in VALIDATE_PARAMETER_TIME:
        pvalue       = Gb.config_parm.get(pname)
        valid_values = VALID_TIME_TYPES
        time_parts   = (f"{pvalue} min").split(' ')
        if (time_parts[0] and time_parts[1] in valid_values
                and isnumber(str(time_parts[0]))) is False:
            _display_config_parameter_error_msg(pname, pvalue, valid_values)

#-------------------------------------------------------------------------
def _display_config_parameter_error_msg(pname, pvalue, valid_values, msg=''):
    '''
    Display an invalid parameter error in the Event Log
    '''
    try:
        if valid_values == [True, False]:
            valid_values = 'true, false'

        elif type(valid_values) is list:
            if type(pvalue) is not int:
                valid_values = ', '.join(valid_values)

    except Exception as err:
        log_exception(err)
        pass

    default_value = DEFAULT_CONFIG_VALUES.get(pname, '')
    Gb.config_parm[pname] = default_value

    error_msg = (f"iCloud3 Error > Invalid configuration parameter > "
                f"{CRLF_DOT}Parameter .. - {pname}: {pvalue} {msg}"
                f"{CRLF_DOT}Valid values - {valid_values}"
                f"{CRLF_DOT}Resetting to - {default_value}")
    post_error_msg(error_msg)

#######################################################################
#
#   INITIALIZE THE GLOBAL VARIABLES WITH THE CONFIGURATION FILE PARAMETER
#   VALUES
#
#######################################################################
def set_data_fields_from_config_parameter_dictionary():
    '''
    Set the iCloud3 variables from the configuration parameters
    '''
    Gb.username                     = Gb.config_parm[CONF_USERNAME]
    Gb.username_base                = Gb.username.split('@')[0]
    Gb.password                     = Gb.config_parm[CONF_PASSWORD]
    Gb.entity_registry_file         = Gb.config_parm[CONF_ENTITY_REGISTRY_FILE]
    Gb.config_ic3_filename          = Gb.config_parm[CONF_CONFIG_IC3_FILE_NAME]
    Gb.event_log_card_directory     = Gb.config_parm[CONF_EVENT_LOG_CARD_DIRECTORY]
    Gb.config_devices_schema        = Gb.config_parm[CONF_DEVICES]
    Gb.tracking_method_config       = Gb.config_parm[CONF_TRACKING_METHOD]

    Gb.um                           = Gb.config_parm[CONF_UNIT_OF_MEASUREMENT]
    Gb.time_format                  = Gb.config_parm[CONF_TIME_FORMAT]
    Gb.display_zone_format          = Gb.config_parm[CONF_DISPLAY_ZONE_FORMAT]

    Gb.center_in_zone_flag          = Gb.config_parm[CONF_CENTER_IN_ZONE]
    Gb.max_interval_secs            = time_str_to_secs(Gb.config_parm[CONF_MAX_INTERVAL])
    Gb.travel_time_factor           = Gb.config_parm[CONF_TRAVEL_TIME_FACTOR]
    Gb.gps_accuracy_threshold       = Gb.config_parm[CONF_GPS_ACCURACY_THRESHOLD]
    Gb.old_location_threshold       = time_str_to_secs(Gb.config_parm[CONF_OLD_LOCATION_THRESHOLD])
    Gb.discard_poor_gps_inzone_flag = Gb.config_parm[CONF_DISCARD_POOR_GPS_INZONE]

    if Gb.config_parm[CONF_IGNORE_GPS_ACC_INZONE] == 'true':
        Gb.discard_poor_gps_inzone_flag = False

    # Gb.ignore_gps_accuracy_inzone_flag = Gb.config_parm[CONF_IGNORE_GPS_ACC_INZONE]
    # Gb.check_gps_accuracy_inzone_flag  = not Gb.ignore_gps_accuracy_inzone_flag
    Gb.hide_gps_coordinates         = Gb.config_parm[CONF_HIDE_GPS_COORDINATES]
    Gb.legacy_mode_flag             = Gb.config_parm[CONF_LEGACY_MODE]

    Gb.distance_method_waze_flag    = (Gb.config_parm[CONF_DISTANCE_METHOD].lower() != CALC)
    Gb.waze_region                  = Gb.config_parm[CONF_WAZE_REGION]
    Gb.waze_max_distance            = Gb.config_parm[CONF_WAZE_MAX_DISTANCE]
    Gb.waze_min_distance            = Gb.config_parm[CONF_WAZE_MIN_DISTANCE]
    Gb.waze_realtime                = Gb.config_parm[CONF_WAZE_REALTIME]
    Gb.waze_history_max_distance    = Gb.config_parm[CONF_WAZE_HISTORY_MAX_DISTANCE]
    Gb.waze_history_map_track_direction = Gb.config_parm[CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION]

    Gb.stationary_still_time_str    = Gb.config_parm[CONF_STATIONARY_STILL_TIME]
    Gb.stationary_zone_offset       = Gb.config_parm[CONF_STATIONARY_ZONE_OFFSET]
    Gb.stationary_inzone_interval_str = Gb.config_parm[CONF_STATIONARY_INZONE_INTERVAL]
    Gb.log_level                    = Gb.config_parm[CONF_LOG_LEVEL]
    Gb.iosapp_request_loc_max_cnt   = Gb.config_parm[CONF_IOSAPP_REQUEST_LOC_MAX_CNT]

    #update the interval time for each of the interval types (i.e., ipad: 2 hrs, noiosapp: 15 min)
    Gb.config_inzone_interval_secs = {}
    Gb.config_inzone_interval_secs[CONF_INZONE_INTERVAL] = \
            time_str_to_secs(Gb.config_parm[CONF_INZONE_INTERVAL])
    Gb.inzone_interval_secs = {}
    Gb.inzone_interval_secs[CONF_INZONE_INTERVAL] = \
            time_str_to_secs(Gb.config_parm[CONF_INZONE_INTERVAL])

    try:
        for itype_itime in Gb.config_parm[CONF_INZONE_INTERVALS]:
            for itype, itime in itype_itime.items():
                Gb.config_inzone_interval_secs[itype] = time_str_to_secs(itime)
                Gb.inzone_interval_secs[itype] = time_str_to_secs(itime)
    except:
        pass

    Gb.EvLog.display_text_as = {}
    for item in Gb.config_parm[CONF_DISPLAY_TEXT_AS]:
        if instr(item, '>'):
            from_to_text = item.split(">")
            Gb.EvLog.display_text_as[from_to_text[0].strip()] = from_to_text[1].strip()

    # Initalize inzone_intervals for specified device types
    if Gb.start_icloud3_inprocess_flag:
        event_msg =(f"inZone Intervals > ")
        for itype, itime in Gb.inzone_interval_secs.items():
            event_msg += (f"{itype}-{secs_to_time_str(itime)}, ")
        post_event(event_msg)

#--------------------------------------------------------------------
def _extract_name_device_type(devicename):
    '''Extract the name and device type from the devicename'''

    try:
        fname       = devicename.lower()
        device_type = ""
        for ic3dev_type in APPLE_DEVICE_TYPES:
            if devicename == ic3dev_type:
                return (devicename, devicename)

            elif instr(devicename, ic3dev_type):
                fnamew = devicename.replace(ic3dev_type, "")
                fname  = fnamew.replace("_", "").replace("-", "").title().strip()
                device_type = DEVICE_TYPE_FNAME.get(ic3dev_type, ic3dev_type)
                break

        if device_type == "":
            fname  = fname.replace("_", "").replace("-", "").title().strip()

    except Exception as err:
        log_exception(err)

    return (fname, device_type)
