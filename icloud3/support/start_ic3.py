

from ..global_variables import GlobalVariables as Gb
from ..const            import (DOMAIN, PLATFORMS, STORAGE_VERSION, STORAGE_KEY, STORAGE_KEY_ENTITY_REGISTRY,
                                MODE_PLATFORM,
                                CF_DEFAULT_IC3_CONF_FILE, CF_DATA_TRACKING, CF_DATA,
                                CF_DATA_GENERAL, CF_DATA_SENSORS, CF_PROFILE,
                                CONF_UPDATE_DATE, CONF_VERSION,
                                EVENT_LOG_CARD_WWW_JS_PROG, CONF_DEVICES,

                                DEFAULT_CONFIG_VALUES, DEFAULT_GENERAL_CONF, DEFAULT_TRACKING_CONF,
                                DEFAULT_PROFILE_CONF, DEFAULT_DEVICE_CONF, DEFAULT_SENSORS_CONF,
                                CF_DEFAULT_IC3_CONF_FILE, DEFAULT_DEVICE_CONF,

                                CONF_LOG_LEVEL,

                                HOME, HOME_FNAME, ERROR, NOT_SET, NON_ZONE_ITEM_LIST, CRLF_DOT, UNKNOWN,
                                EVLOG_NOTICE, EVLOG_ALERT, EVLOG_ERROR, LARROW, RARROW, CRLF_NBSP6_DOT, INFO_SEPARATOR,
                                STATIONARY,
                                NAME, TITLE, FNAME, RADIUS, STATE_TO_ZONE_BASE, HIGH_INTEGER, NOT_SET_FNAME,
                                FMF, FAMSHR, FAMSHR_FMF, IOSAPP, ICLOUD, DEVICE_TRACKER, DEVICE_TRACKER_DOT,
                                IPHONE, IPAD, IPOD, WATCH, AIRPODS, NO_IOSAPP,
                                ICLOUD3_ERROR_MSG, CRLF, CRLF_DOT, CRLF_CHK, CRLF_X, DOT, HDOT, NEW_LINE,
                                NBSP2, NBSP4, NBSP6, CRLF_NBSP6_DOT, DASH_20,
                                TRACKING_METHOD_FNAME, CALC, NORMAL, MONITOR, INACTIVE,
                                EVENT_LOG_CARD_WWW_JS_PROG, EVLOG_DEBUG, EVLOG_INIT_HDR,
                                STORAGE_DIR,  DEBUG_TRACE_CONTROL_FLAG,
                                ENTITY_ID, NOTIFY, MOBILE_APP, STORAGE_KEY_ENTITY_REGISTRY,
                                MODE_PLATFORM,

                                CF_PROFILE, CF_DATA, CF_DATA_TRACKING, CF_DATA_DEVICES, CF_DATA_GENERAL,
                                CF_DATA_SENSORS, CONF_UPDATE_DATE,

                                LOCATION, ICLOUD_DEVICE_CLASS,
                                CONF_VERSION,
                                CONF_IC3_DEVICENAME, CONF_FAMSHR_DEVICENAME, CONF_FMF_EMAIL,
                                CONF_DEVICE_TYPE, CONF_TRACKING_MODE, CONF_IOSAPP_DEVICE,

                                CONF_ZONE, CONF_NAME, CONF_DEVICENAME, ZONE, LATITUDE, DEVICE_ID,
                                CONF_DEVICENAME, CONF_SOURCE, CONF_FNAME, CONF_PICTURE, CONF_EMAIL,

                                CONF_EVENT_LOG_CARD_DIRECTORY, CONF_EVENT_LOG_CARD_PROGRAM,

                                CONF_USERNAME, CONF_PASSWORD,
                                CONF_DATA_SOURCE,
                                CONF_UNIT_OF_MEASUREMENT,
                                CONF_DISPLAY_TEXT_AS,

                                CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_MAX_INTERVAL, CONF_TRAVEL_TIME_FACTOR,
                                CONF_STAT_ZONE_FNAME,
                                CONF_STAT_ZONE_BASE_LATITUDE, CONF_STAT_ZONE_BASE_LONGITUDE,

                                CONF_DISPLAY_ZONE_FORMAT, CONF_CENTER_IN_ZONE,
                                CONF_TIME_FORMAT, CONF_INZONE_INTERVAL, CONF_INZONE_INTERVALS,
                                CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD,
                                CONF_DISCARD_POOR_GPS_INZONE, CONF_DISTANCE_METHOD,

                                CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE,CONF_WAZE_MIN_DISTANCE,
                                CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED,
                                CONF_WAZE_HISTORY_MAX_DISTANCE, CONF_WAZE_HISTORY_TRACK_DIRECTION,

                                CONF_LOG_LEVEL, CONF_NO_IOSAPP,

                                DEFAULT_CONFIG_IC3_FILE_NAME,
                                DEFAULT_UNIT_OF_MEASUREMENT, DEFAULT_DISPLAY_TEXT_AS, DEFAULT_TIME_FORMAT,
                                DEFAULT_DISTANCE_METHOD, DEFAULT_INZONE_INTERVAL, DEFAULT_INZONE_INTERVALS,
                                DEFAULT_DISPLAY_ZONE_FORMAT, DEFAULT_CENTER_IN_ZONE, DEFAULT_MAX_INTERVAL,
                                DEFAULT_TRAVEL_TIME_FACTOR, DEFAULT_GPS_ACCURACY_THRESHOLD,
                                DEFAULT_OLD_LOCATION_THRESHOLD, DEFAULT_IGNORE_GPS_ACC_INZONE,
                                DEFAULT_CHECK_GPS_ACC_INZONE, DEFAULT_HIDE_GPS_COORDINATES,
                                DEFAULT_WAZE_REGION, DEFAULT_WAZE_MAX_DISTANCE, DEFAULT_WAZE_MIN_DISTANCE,
                                DEFAULT_WAZE_REALTIME,
                                DEFAULT_WAZE_HISTORY_DATABASE_USED, DEFAULT_WAZE_HISTORY_MAX_DISTANCE ,
                                DEFAULT_WAZE_HISTORY_TRACK_DIRECTION,
                                DEFAULT_STATIONARY_STILL_TIME, DEFAULT_STATIONARY_ZONE_OFFSET,
                                DEFAULT_STATIONARY_INZONE_INTERVAL, DEFAULT_LOG_LEVEL,
                                DEFAULT_IOSAPP_REQUEST_LOC_MAX_CNT,
                                WAZE_LOCATION_HISTORY_DATABASE, )

from ..device               import iCloud3Device
from ..zone                 import iCloud3Zone, iCloud3StationaryZone
from ..support.waze         import Waze
from ..support.waze_history import WazeRouteHistory as WazeHist
from ..support              import iosapp_interface
from ..support              import iosapp_data_handler
from ..helpers.base         import (instr, broadcast_info_msg, ordereddict_to_dict,
                                    post_event, post_error_msg, post_monitor_msg, post_startup_event,
                                    log_info_msg, log_debug_msg, log_rawdata, log_exception,
                                    _trace, _traceha, )
from ..helpers.time         import (secs_to_time_str, hhmmss_to_secs, datetime_now, )
from ..helpers              import entity_io
from ..helpers.format       import (format_gps, format_dist, format_dist_m, )

import os
import json
import shutil
from collections import OrderedDict
from   homeassistant.util    import slugify
from re import match

import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- INITIALIZATION
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
def initialize_directory_filenames(base_directory):
    """ Set up common directories and file names """

    Gb.ha_storage_icloud3      = Gb.hass.helpers.storage.Store(STORAGE_VERSION, DOMAIN).path
    Gb.ha_storage_directory    = Gb.ha_storage_icloud3.replace(f"/{DOMAIN}", "")
    Gb.ha_config_directory     = Gb.ha_storage_directory.replace('.storage', '')
    Gb.icloud3_config_filename = f"{Gb.ha_storage_icloud3}.configuration"
    Gb.icloud3_restore_state_filename = f"{Gb.ha_storage_icloud3}.restore_state"
    Gb.wazehist_database_filename = f"{Gb.ha_storage_directory}/{WAZE_LOCATION_HISTORY_DATABASE}"

    Gb.icloud3_directory       = base_directory
    Gb.icloud3_filename        = Gb.icloud3_directory.split("/custom_components/")[1]
    Gb.HALogger                = logging.getLogger(f"icloud3")

    Gb.entity_registry_file    = Gb.hass.config.path(Gb.ha_storage_directory, STORAGE_KEY_ENTITY_REGISTRY)
    if Gb.entity_registry_file.startswith('/workspaces'):
        Gb.entity_registry_file = Gb.entity_registry_file.replace('.storage/core.', '.storage/test.')

#-------------------------------------------------------------------------------------------
def load_storage_icloud3_configuration_file():

    if os.path.exists(Gb.icloud3_config_filename) is False:
        _LOGGER.info(f"Creating Configuration File-{Gb.icloud3_config_filename}")

        Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
        build_initial_config_file_structure()
        write_storage_icloud3_configuration_file()

    success = read_storage_icloud3_configuration_file()

    if success is False:
        _LOGGER.info(f"Invalid Configuration File-{Gb.icloud3_config_filename}")
        _LOGGER.info(f"Recreating Configuration File-{Gb.icloud3_config_filename}")

        build_initial_config_file_structure()
        Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
        write_storage_icloud3_configuration_file()
        read_storage_icloud3_configuration_file()

    if CONF_LOG_LEVEL in Gb.conf_general:
        set_log_level(Gb.conf_general[CONF_LOG_LEVEL])
        return True

    return

#-------------------------------------------------------------------------------------------
def load_icloud3_ha_config_yaml(config):

    log_info_msg("__init__ async_setup {config=}")
    Gb.config_parm_ha_config_yaml = None

    ha_config_yaml_platforms = ordereddict_to_dict(config)['device_tracker']

    ic3_ha_config_yaml = {}
    for ha_config_yaml_platform in ha_config_yaml_platforms:
        if ha_config_yaml_platform['platform'] == 'icloud3':
            ic3_ha_config_yaml = ha_config_yaml_platform.copy()
            break

    Gb.config_parm_ha_config_yaml = ordereddict_to_dict(ic3_ha_config_yaml)

#--------------------------------------------------------------------
def build_initial_config_file_structure():
    '''
    Create the initial data structure of the ic3 config file

    |---profile
    |---data
        |---tracking
            |---devices
        |---general
            |---parameters
        |---sensors

    '''

    Gb.conf_profile   = DEFAULT_PROFILE_CONF.copy()
    Gb.conf_tracking  = DEFAULT_TRACKING_CONF.copy()
    Gb.conf_devices   = []
    Gb.conf_general   = DEFAULT_GENERAL_CONF.copy()
    Gb.conf_sensors   = DEFAULT_SENSORS_CONF.copy()
    Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()

    Gb.conf_data['tracking']        = Gb.conf_tracking
    Gb.conf_data['tracking']['devices'] = Gb.conf_devices
    Gb.conf_data['general']         = Gb.conf_general
    Gb.conf_data['sensors']         = Gb.conf_sensors

    Gb.conf_file_data['profile']    = Gb.conf_profile
    Gb.conf_file_data['data']       = Gb.conf_data

#-------------------------------------------------------------------------------------------
def read_storage_icloud3_configuration_file():
    '''
    Read the config/.storage/.icloud3.configuration file and extract the
    data into the Global Variables
    '''

    try:
        with open(Gb.icloud3_config_filename, 'r') as f:
            Gb.conf_file_data = json.load(f)

            Gb.conf_profile   = Gb.conf_file_data['profile']
            Gb.conf_data      = Gb.conf_file_data['data']

            Gb.conf_tracking  = Gb.conf_data['tracking']
            Gb.conf_devices   = Gb.conf_data['tracking']['devices']
            Gb.conf_general   = Gb.conf_data['general']
            Gb.conf_sensors   = Gb.conf_data['sensors']

            # Build a single list from the selected sensors in all sensor groups
            Gb.conf_sensors_list = []

            for sensor_group, sensor_list in Gb.conf_sensors.items():
                Gb.conf_sensors_list.extend(sensor_list)

            # Adjust sensors_list for last_zone items based on selected zone items
            if 'last_zone' in Gb.conf_sensors_list:
                if 'zone' not in Gb.conf_sensors_list:
                    Gb.conf_sensors_list.pop('last_zone')
                if 'zone_name' in Gb.conf_sensors_list:
                    Gb.conf_sensors_list.append('last_zone_name')
                if 'zone_fname' in Gb.conf_sensors_list:
                    Gb.conf_sensors_list.append('last_zone_fname')
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
            Gb.conf_profile[CONF_UPDATE_DATE] = datetime_now()

            Gb.conf_data['tracking']['devices'] = Gb.conf_devices
            Gb.conf_data['tracking']        = Gb.conf_tracking
            Gb.conf_data['general']         = Gb.conf_general
            Gb.conf_data['sensors']         = Gb.conf_sensors

            Gb.conf_file_data['profile']    = Gb.conf_profile
            Gb.conf_file_data['data']       = Gb.conf_data

            json.dump(Gb.conf_file_data, f, indent=4)

        return True

    except Exception as err:
        log_exception(err)

    return False



#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 0
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>


#------------------------------------------------------------------------------
#
#   VARIABLE DEFINITION & INITIALIZATION FUNCTIONS
#
#------------------------------------------------------------------------------
def define_tracking_control_fields():
    Gb.any_device_being_updated_flag   = False
    Gb.trigger                         = {}       #device update trigger
    Gb.info_notification               = ''
    Gb.broadcast_msg                   = ''

#------------------------------------------------------------------------------
#
#   SET GLOBAL VARIABLES BACK TO THEIR INITIAL CONDITION
#
#------------------------------------------------------------------------------
def initialize_global_variables():

    # Configuration parameters that can be changed in config_ic3.yaml
    Gb.um                               = DEFAULT_UNIT_OF_MEASUREMENT
    # Gb.time_format                      = 12
    Gb.time_format_12_hour              = True
    Gb.um_km_mi_factor                  = .62137
    Gb.um_m_ft                          = 'ft'
    Gb.um_kph_mph                       = 'mph'
    Gb.um_time_strfmt                   = '%I:%M:%S'
    Gb.um_time_strfmt_ampm              = '%I:%M:%S%P'
    Gb.um_date_time_strfmt              = '%Y-%m-%d %H:%M:%S'

    # Configuration parameters
    Gb.center_in_zone_flag             = DEFAULT_CENTER_IN_ZONE
    Gb.display_zone_format             = DEFAULT_DISPLAY_ZONE_FORMAT
    Gb.max_interval_secs               = 240
    Gb.travel_time_factor              = DEFAULT_TRAVEL_TIME_FACTOR
    Gb.gps_accuracy_threshold          = DEFAULT_GPS_ACCURACY_THRESHOLD
    Gb.old_location_threshold          = 180
    Gb.distance_method_waze_flag       = True
    Gb.log_level                       = DEFAULT_LOG_LEVEL

    Gb.waze_region                     = DEFAULT_WAZE_REGION
    Gb.waze_max_distance               = DEFAULT_WAZE_MAX_DISTANCE
    Gb.waze_min_distance               = DEFAULT_WAZE_MIN_DISTANCE
    Gb.waze_realtime                   = DEFAULT_WAZE_REALTIME
    Gb.waze_history_database_used      = DEFAULT_WAZE_HISTORY_DATABASE_USED
    Gb.waze_history_max_distance       = DEFAULT_WAZE_HISTORY_MAX_DISTANCE
    Gb.waze_history_track_direction= DEFAULT_WAZE_HISTORY_TRACK_DIRECTION

    # Tracking method control vaiables
    # Used to reset Gb.tracking_method  after pyicloud/icloud account successful reset
    # Will be changed to IOSAPP if pyicloud errors
    Gb.tracking_method_FAMSHR           = False
    Gb.tracking_method_FMF              = False
    Gb.tracking_method_IOSAPP           = False
    Gb.tracking_method_FMF_used         = False
    Gb.tracking_method_FAMSHR_used      = False
    Gb.tracking_method_IOSAPP_used      = False

#------------------------------------------------------------------------------
#
#   INITIALIZE THE GLOBAL VARIABLES WITH THE CONFIGURATION FILE PARAMETER
#   VALUES
#
#------------------------------------------------------------------------------
def set_global_variables_from_conf_parameters(evlog_msg=True):
    '''
    Set the iCloud3 variables from the configuration parameters
    '''
    try:
        config_event_msg = "Configure iCloud3 Operations >"
        config_event_msg += f"{CRLF_DOT}Load configuration parameters"

        set_icloud_username_password()

        Gb.event_log_card_directory     = Gb.conf_profile[CONF_EVENT_LOG_CARD_DIRECTORY]
        Gb.event_log_card_program       = Gb.conf_profile[CONF_EVENT_LOG_CARD_PROGRAM]

        Gb.um                           = Gb.conf_general[CONF_UNIT_OF_MEASUREMENT]
        Gb.time_format_12_hour          = (Gb.conf_general[CONF_TIME_FORMAT] == '12_hour')
        Gb.display_zone_format          = Gb.conf_general[CONF_DISPLAY_ZONE_FORMAT]

        Gb.center_in_zone_flag          = Gb.conf_general[CONF_CENTER_IN_ZONE]
        Gb.max_interval_secs            = hhmmss_to_secs(Gb.conf_general[CONF_MAX_INTERVAL])
        Gb.travel_time_factor           = Gb.conf_general[CONF_TRAVEL_TIME_FACTOR]
        Gb.gps_accuracy_threshold       = Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]
        Gb.old_location_threshold       = hhmmss_to_secs(Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD])
        Gb.discard_poor_gps_inzone_flag = Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]

        Gb.distance_method_waze_flag    = (Gb.conf_general[CONF_DISTANCE_METHOD] != CALC)
        Gb.waze_region                  = Gb.conf_general[CONF_WAZE_REGION]
        Gb.waze_max_distance            = Gb.conf_general[CONF_WAZE_MAX_DISTANCE]
        Gb.waze_min_distance            = Gb.conf_general[CONF_WAZE_MIN_DISTANCE]
        Gb.waze_realtime                = Gb.conf_general[CONF_WAZE_REALTIME]
        Gb.waze_history_database_used   = Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED]
        Gb.waze_history_max_distance    = Gb.conf_general[CONF_WAZE_HISTORY_MAX_DISTANCE]
        Gb.waze_history_track_direction = Gb.conf_general[CONF_WAZE_HISTORY_TRACK_DIRECTION]

        # Setup the Stationary Zone location and times
        # The stat_zone_base_lat/long will be adjusted after the Home zone is set up
        Gb.stat_zone_fname              = Gb.conf_general[CONF_STAT_ZONE_FNAME]
        Gb.stat_zone_base_latitude      = Gb.conf_general[CONF_STAT_ZONE_BASE_LATITUDE]
        Gb.stat_zone_base_longitude     = Gb.conf_general[CONF_STAT_ZONE_BASE_LONGITUDE]
        Gb.stat_zone_still_time_secs      = hhmmss_to_secs(Gb.conf_general[CONF_STAT_ZONE_STILL_TIME])
        Gb.stat_zone_inzone_interval_secs = hhmmss_to_secs(Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL])

        Gb.log_level = Gb.conf_general[CONF_LOG_LEVEL]

        # update the interval time for each of the interval types (i.e., ipad: 2 hrs, no_iosapp: 15 min)
        inzone_intervals = Gb.conf_general[CONF_INZONE_INTERVALS]
        Gb.inzone_interval_secs = {}
        Gb.inzone_interval_secs[IPHONE]     = hhmmss_to_secs(inzone_intervals[IPHONE])
        Gb.inzone_interval_secs[IPAD]       = hhmmss_to_secs(inzone_intervals[IPAD])
        Gb.inzone_interval_secs[WATCH]      = hhmmss_to_secs(inzone_intervals[WATCH])
        Gb.inzone_interval_secs[IPOD]       = hhmmss_to_secs(inzone_intervals[IPHONE])
        Gb.inzone_interval_secs[AIRPODS]    = hhmmss_to_secs(inzone_intervals[AIRPODS])
        Gb.inzone_interval_secs[NO_IOSAPP]  = hhmmss_to_secs(inzone_intervals[NO_IOSAPP])
        Gb.inzone_interval_secs[CONF_INZONE_INTERVAL] = hhmmss_to_secs(inzone_intervals['other'])

        config_event_msg += f"{CRLF_DOT}Set Display Text As fields"
        Gb.EvLog.display_text_as = {}
        for display_text_as in Gb.conf_general[CONF_DISPLAY_TEXT_AS]:
            if instr(display_text_as, '>'):
                from_to_text = display_text_as.split('>')
                Gb.EvLog.display_text_as[from_to_text[0].strip()] = from_to_text[1].strip()

        # Set other fields and flags based on configuration parameters
        config_event_msg += f"{CRLF_DOT}Set Tracking Method"
        set_tracking_method(Gb.tracking_method)

        config_event_msg += f"{CRLF_DOT}Initialize debug control"
        set_log_level(Gb.log_level)

        config_event_msg += f"{CRLF_DOT}Set Unit of Measure Formats"
        set_um_formats()

        if evlog_msg:
            post_event(config_event_msg)

    except Exception as err:
        log_exception(err)

#------------------------------------------------------------------------------
#
#   SET THE GLOBAL TRACKING METHOD
#
#   This is used during the startup routines and in other routines when errors occur.
#
#------------------------------------------------------------------------------
def set_icloud_username_password():
    '''
    Set up icloud username/password and devices from the configuration parameters
    '''
    Gb.username                     = Gb.conf_tracking[CONF_USERNAME]
    Gb.username_base                = Gb.username.split('@')[0]
    Gb.password                     = Gb.conf_tracking[CONF_PASSWORD]
    Gb.data_source_use_icloud       = instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD)
    Gb.data_source_use_iosapp       = instr(Gb.conf_tracking[CONF_DATA_SOURCE], IOSAPP)
    Gb.devices                      = Gb.conf_devices

#------------------------------------------------------------------------------
def set_tracking_method(tracking_method):
    '''
    Set up tracking method. These fields will be reset based on the device_id's available
    for the Device once the famshr and fmf tracking methods are set up.
    '''

    # If the tracking_method is in OPT_TRACK_METHOD, we are processing one from the
    # config parameters. If not, it is the actual tracking method to assign
    if Gb.data_source_use_icloud:
        tracking_method = FAMSHR
    elif Gb.data_source_use_iosapp:
        tracking_method = IOSAPP

    if Gb.data_source_use_icloud and Gb.password == '':
        error_msg =("iCloud3 Error > The password is required for the "
                    f"iCloud Location Services tracking method. "
                    f"The iOS App tracking_method will be used.")
        post_error_msg(error_msg)
        tracking_method = IOSAPP

    # If the tracking method changes, the complete initialization must be done
    if Gb.data_source_use_icloud:
        Gb.tracking_method = FAMSHR if tracking_method == '' else tracking_method
        Gb.tracking_method_FAMSHR     = (tracking_method == FAMSHR)
        Gb.tracking_method_FMF        = (tracking_method == FMF)

    if Gb.data_source_use_iosapp:
        Gb.tracking_method_IOSAPP     = (tracking_method == IOSAPP)

#------------------------------------------------------------------------------
#
#   INITIALIZE THE UNIT_OF_MEASURE FIELDS
#
#------------------------------------------------------------------------------
def set_um_formats():
    #Define variables, lists & tables
    if Gb.um == 'mi':
        Gb.um_km_mi_factor          = 0.62137
        Gb.um_m_ft                  = 'ft'
        Gb.um_kph_mph               = 'mph'
    else:
        Gb.um_km_mi_factor          = 1
        Gb.um_m_ft                  = 'm'
        Gb.um_kph_mph               = 'kph'

    if Gb.time_format_12_hour:
        Gb.um_time_strfmt       = '%I:%M:%S'
        Gb.um_time_strfmt_ampm  = '%I:%M:%S%P'
        Gb.um_date_time_strfmt  = '%Y-%m-%d %I:%M:%S'
    else:
        Gb.um_time_strfmt       = '%H:%M:%S'
        Gb.um_time_strfmt_ampm  = '%H:%M:%S'
        Gb.um_date_time_strfmt  = '%Y-%m-%d %H:%M:%S'

#------------------------------------------------------------------------------
#
#   INITIALIZE THE DEBUG CONTROL FLAGS
#
#   Decode the log_level: debug parameter
#      debug            - log 'debug' messages to the log file under the 'info' type
#      debug_rawdata    - log data read from records to the log file
#      eventlog         - Add debug items to ic3 event log
#      debug+eventlog   - Add debug items to HA log file and ic3 event log
#
#------------------------------------------------------------------------------
def set_log_level(log_level):

    log_level = log_level.lower()
    #Save log_level flags across restarts via Event Log > Actions
    if Gb.log_debug_flag_restart is not None or Gb.log_rawdata_flag_restart is not None:
        if Gb.log_debug_flag_restart is not None:
            Gb.log_debug_flag         = Gb.log_debug_flag_restart
            Gb.log_debug_flag_restart = None

        if Gb.log_rawdata_flag_restart is not None:
            Gb.log_rawdata_flag         = Gb.log_rawdata_flag_restart
            Gb.log_rawdata_flag_restart = None
    else:
        Gb.log_debug_flag   = instr(log_level, 'debug') or DEBUG_TRACE_CONTROL_FLAG
        Gb.log_rawdata_flag = instr(log_level, 'rawdata')
        Gb.log_rawdata_flag_unfiltered = instr(log_level, 'unfiltered')

    if Gb.log_rawdata_flag: Gb.log_debug_flag = True
    Gb.evlog_trk_monitors_flag = Gb.evlog_trk_monitors_flag or instr(log_level, 'eventlog')

#------------------------------------------------------------------------------
#
#   ICLOUD3 CONFIGURATION PARAMETERS WERE UPDATED VIA CONFIG_FLOW
#
#   Determine the type of parameters that were updated and reset the variables or
#   devices based on the type of changes.
#
#------------------------------------------------------------------------------
def process_conf_flow_parameter_updates():

    if 'restart' in Gb.config_flow_parameters_updated:
        set_icloud_username_password()
        Gb.start_icloud3_request_flag = True

    elif 'general' in Gb.config_flow_parameters_updated:
        set_global_variables_from_conf_parameters()

    if 'tracking' in Gb.config_flow_parameters_updated:
        set_icloud_username_password()
        pass
    elif 'devices' in Gb.config_flow_parameters_updated:
        set_icloud_username_password()
        pass

    Gb.config_flow_parameters_updated = {''}
#------------------------------------------------------------------------------
#
#   LOAD HA CONFIGURATION.YAML FILE
#
#   Load the configuration.yaml file and save it's contents. This contains the default
#   parameter values used to reset the configuration when iCloud3 is restarted.
#
#   'load_ha_config_parameters' is run in device_tracker.__init__ when iCloud3 starts
#   'reinitialize_config_parameters' is run in device_tracker.start_icloud3 when iCloud3
#   starts or is restarted before the config_ic3.yaml parameter file is processed
#
#------------------------------------------------------------------------------
def load_ha_config_parameters(ha_config_yaml_and_defaults):
    Gb.config_parm_initial_load = {k:v for k, v in ha_config_yaml_and_defaults.items()}
    reinitialize_config_parameters()

def reinitialize_config_parameters():
    Gb.config_parm = Gb.config_parm_initial_load.copy()

#------------------------------------------------------------------------------
#
#   GET FILE AND DIRECTORY NAMES FOR ICLOUD3, CONFIG_IC3.YAML AND
#   ICLOUD3_EVENT_LOG_CARD.JS
#
#------------------------------------------------------------------------------
def get_icloud3_directory_and_file_names():
    post_event(f"iCloud3 Directory > {Gb.icloud3_directory}")
    post_event(f"iCloud3 Configuration File > {Gb.icloud3_config_filename}")

#------------------------------------------------------------------------------
#
#   CHECK THE IC3 EVENT LOG VERSION BEING USED
#
#   Read the icloud3-event-log-card.js file in the iCloud3 directory and the
#   Lovelace Custom Card directory (default=www/custom_cards) and extract
#   the current version (Version=x.x.x (mm.dd.yyyy)) comment entry before
#   the first 'class' statement. If the version in the ic3 directory is
#   newer than the www/custom_cards directory, copy the ic3 version
#   to the www/custom_cards directory.
#
#   The custom_cards directory can be changed using the event_log_card_directory
#   parameter.
#
#------------------------------------------------------------------------------
def check_ic3_event_log_file_version():
    try:
        ic3_evlog_filename    = f"{Gb.icloud3_directory}/{Gb.conf_profile[CONF_EVENT_LOG_CARD_PROGRAM]}"
        www_evlog_directory   = f"{Gb.ha_config_directory}www/{Gb.conf_profile[CONF_EVENT_LOG_CARD_DIRECTORY]}"
        www_evlog_js_filename = f"{www_evlog_directory}/{Gb.conf_profile[CONF_EVENT_LOG_CARD_PROGRAM]}"
        ic3_version, ic3_beta_version, ic3_version_text = _read_event_log_card_js_file(ic3_evlog_filename)
        www_version, www_beta_version, www_version_text = _read_event_log_card_js_file(www_evlog_js_filename)
        Gb.version_evlog = www_version_text

        # Event log card is not in iCloud3 directory. Nothing to do.
        if ic3_version == 0:
            return

        # Event Log card does not exist in www directory. Copy it from iCloud3 directory
        if www_version == 0:
            try:
                os.mkdir(www_evlog_directory)
            except FileExistsError:
                pass
            except Exception as err:
                log_exception(err)
                pass
        current_version_installed_flag = True
        if ic3_version > www_version:
            current_version_installed_flag = False
        elif ic3_version == www_version:
            if ic3_beta_version == 0:
                pass
            elif ic3_beta_version > www_beta_version:
                current_version_installed_flag = False

        if current_version_installed_flag:
            event_msg =(f"iCloud3 Event Log > "
                        f"Current Version Installed (v{www_version_text}), "
                        f"{www_evlog_js_filename}")
            post_event(event_msg)

        else:
            shutil.copy(ic3_evlog_filename, www_evlog_js_filename)
            event_msg =(f"{EVLOG_ALERT}"
                        f"Event Log Alert > iCloud3 Event Log was updated:"
                        f"CRLFThe Event Log Card was updated to v{ic3_version_text}. "
                        "Refresh your browser and do the following on every tracked "
                        "devices running the iOS App to load the new version."
                        "CRLF1. Select `HA Sidebar > Configuration`"
                        "CRLF2. Select `Companion App` near the bottom of the HA Configuration screen"
                        "CRLF3. Select `Debugging` near the bottom of the `Settings` screen"
                        "CRLF4. Select `Reset frontend cache`. The cache on the phone/device will be cleared"
                        "CRLF5. Select `Settings`, then Select `Done`, then Close the `HA Configuration` screen"
                        "CRLF6. Display the iCloud3 Event Log, then pull down to refresh the page. "
                        "You should see the busy spinning wheel as the new version is loaded")
            post_event(event_msg)

            event_msg =(f"{EVLOG_ALERT}"
                        f"Event Log Alert > iCloud3 Event Log was updated:"
                        f"{CRLF_DOT}Old Version.. - v{www_version_text}"
                        f"{CRLF_DOT}New Version - v{ic3_version_text}"
                        f"{CRLF_DOT}Copied From - {ic3_evlog_filename}"
                        f"{CRLF_DOT}Copied To..... - {www_evlog_js_filename}")
            post_event(event_msg)

            Gb.info_notification = (f"Event Log Card updated to v{ic3_version_text}. "
                        "See Event Log for more info.")
            title       = (f"iCloud3 Event Log Card updated to v{ic3_version_text}")
            message     = ("Refresh the iOS App to load the new version. "
                        "Select HA Sidebar > APP Configuration. Scroll down. Select Refresh "
                        "Frontend Cache. Select Done. Pull down to refresh App.")
            Gb.broadcast_msg = {
                        "title": title,
                        "message": message,
                        "data": {"subtitle": "Event Log needs to be refreshed"}}

    except Exception as err:
        log_exception(err)
        return

#------------------------------------------------------------------------------
def _read_event_log_card_js_file(evlog_filename):
    '''
    Read the records in the the evlog_filename up to the 'class' statement and
    extract the version and date.
    Return the Version number and the Version text (#.#.#b## (m/d/yyy))
    Return 0, 0, "Unknown" if the Version number was not found
    '''
    try:
        if os.path.exists(evlog_filename) == False:
            return (0, 0, 'Not Installed')

        #Cycle thru the file looking for the Version
        evlog_file = open(evlog_filename)

        for evlog_recd in evlog_file:
            if instr(evlog_recd.lower().replace(' ', ''), 'version='):
                break

            #exit if find 'class' recd before 'version' recd
            elif instr(evlog_recd, "class"):
                return (0, 0, 'Unknown')

        evlog_recd          = evlog_recd.replace("("," (").replace("  "," ")
        version_line        = evlog_recd.split("=")[1].replace('\n', '')
        version_number_date = f"{version_line} ".split(' ')

        version_number_text = version_number_date[0]
        version_beta_number = 0

        if instr(version_number_text, 'b'):
            version_number_beta = (f"{version_number_text}").split('b')
            version_number_text = version_number_beta[0]
            version_beta_number = int(version_number_beta[1])

        version_parts = (f"{version_number_text}.0.0").split('.')
        version  = 0
        version += int(version_parts[0])*10000
        version += int(version_parts[1])*100
        version += int(version_parts[2])*1

    except FileNotFoundError:
        return (0, 0, 'Not Installed')

    except Exception as err:
        log_exception(err)
        return (0, 0, ERROR)

    evlog_file.close()

    return (version, version_beta_number, version_number_text)

#------------------------------------------------------------------------------
#
#   LOAD THE ZONE DATA FROM HA
#
#   Retrieve the zone entity attributes from HA and initialize Zone object
#   that is used when a Device is located
#
#------------------------------------------------------------------------------
def create_Zones_object():
    '''
    Get the zone names from HA, fill the zone tables
    '''

    try:
        if Gb.start_icloud3_initial_load_flag is False:
            Gb.hass.services.call(ZONE, "reload")
    except:
        pass

    #log_msg = (f"Reloading Zone.yaml config file")
    #log_debug_msg(log_msg)

    # zone_entities = Gb.hass.states.entity_ids(ZONE)
    zone_entity_ids, zone_entity_data = entity_io.get_entity_registry_data(platform=ZONE)
    log_debug_msg(f"ZONES - {zone_entity_ids}")

    Gb.state_to_zone = STATE_TO_ZONE_BASE.copy()
    OldZones_by_zone = Gb.Zones_by_zone.copy()

    Gb.Zones = []
    Gb.Zones_by_zone = {}

    # Add away, not_set, not_home, stationary, etc. so display_name is set
    # for these zones/states. Radius=0 is used to ypass normal zone processing.
    for zone, display_as in NON_ZONE_ITEM_LIST.items():
        if zone in OldZones_by_zone:
            Zone = OldZones_by_zone[zone]
        else:
            Zone = iCloud3Zone(zone, {NAME: display_as, TITLE: display_as, FNAME: display_as, RADIUS: 0})
            Zone.display_as = display_as
        Gb.Zones.append(Zone)
        Gb.Zones_by_zone[zone] = Zone

    zone_msg = ''
    for zone_entity in zone_entity_ids:
        try:
            zone_data = entity_io.get_attributes(zone_entity)
            zone      = zone_entity.replace('zone.', '')

            #log_debug_msg(f"ZONE.DATA - [zone.{zone}--{zone_data}]")

            if LATITUDE not in zone_data: continue

            # Update Zone data if it already exists, else add a new one
            if zone in OldZones_by_zone:
                if instr(zone, STATIONARY):
                    continue
                Zone = OldZones_by_zone[zone]
                Zone.__init__(zone, zone_data)
                post_monitor_msg(f"INITIALIZED Zone-{zone}")

            else:
                Zone = iCloud3Zone(zone, zone_data)
                post_monitor_msg(f"ADDED Zone-{zone}")

            Gb.Zones.append(Zone)
            Gb.Zones_by_zone[zone] = Zone

            zfname = Zone.fname
            ztitle = Zone.title

            Gb.state_to_zone[zfname] = zone
            if ztitle not in Gb.state_to_zone:
                Gb.state_to_zone[ztitle] = zone
            ztitle_w = ztitle.replace(' ', '')
            if ztitle_w not in Gb.state_to_zone:
                Gb.state_to_zone[ztitle_w] = zone

            if Zone.radius > 0:
                if Gb.display_zone_format   == CONF_ZONE: Zone.display_as = Zone.zone
                elif Gb.display_zone_format == CONF_NAME: Zone.display_as = Zone.name
                elif Gb.display_zone_format == TITLE:     Zone.display_as = Zone.title
                elif Gb.display_zone_format == FNAME:     Zone.display_as = Zone.fname

                zone_msg += (f"{CRLF_DOT}{Zone.zone}/{Zone.display_as} "
                        f"(r{Zone.radius}m)")

            if zone == HOME:
                Gb.HomeZone = Zone

                if (float(Gb.stat_zone_base_latitude) == int(Gb.stat_zone_base_latitude)
                    or Gb.stat_zone_base_latitude < 25):
                    offset_lat          = float(Gb.stat_zone_base_latitude) * 0.008983
                    offset_long         = float(Gb.stat_zone_base_longitude) * 0.010094
                    Gb.stat_zone_base_latitude  = Gb.HomeZone.latitude  + offset_lat
                    Gb.stat_zone_base_longitude = Gb.HomeZone.longitude + offset_long

        except Exception as err:
            log_exception(err)

    log_msg = (f"Set up Zones (zone/{Gb.display_zone_format}) > {zone_msg}")
    post_event("*", log_msg)

    dist = Gb.HomeZone.distance_km(Gb.stat_zone_base_latitude, Gb.stat_zone_base_longitude)
    home_zone_radius_km   = Gb.HomeZone.radius_km
    min_dist_from_zone_km = round(home_zone_radius_km * 2, 2)
    dist_move_limit       = round(home_zone_radius_km * 1.5, 2)

    event_msg =(f"Stationary Zone Base Information > "
                f"BaseLocation-{format_gps(Gb.stat_zone_base_latitude, Gb.stat_zone_base_longitude, 0)}, "
                f"Radius-{Gb.HomeZone.radius * 2}m, "
                f"DistFromHome-{format_dist(dist)}, "
                f"MinDistFromZone-{format_dist(min_dist_from_zone_km)}, "
                f"DistMoveLimit-{format_dist(dist_move_limit)}")
    post_event(event_msg)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 1
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>


#------------------------------------------------------------------------------
#
#   INITIALIZE THE WAZE FIELDS
#
#------------------------------------------------------------------------------
def create_Waze_object():
    '''
    Create the Waze object even if Waze is not used.
    Also st up the WazeHist object here to keep object creation together
    '''
    try:
        if Gb.Waze:
            Gb.Waze.__init__(   Gb.distance_method_waze_flag,
                                Gb.waze_min_distance,
                                Gb.waze_max_distance,
                                Gb.waze_realtime,
                                Gb.waze_region)
            Gb.WazeHist.__init__(
                                Gb.waze_history_database_used,
                                Gb.waze_history_max_distance,
                                Gb.waze_history_track_direction)
        else:
            Gb.Waze = Waze(     Gb.distance_method_waze_flag,
                                Gb.waze_min_distance,
                                Gb.waze_max_distance,
                                Gb.waze_realtime,
                                Gb.waze_region)
            Gb.WazeHist = WazeHist(
                                Gb.waze_history_database_used,
                                Gb.waze_history_max_distance,
                                Gb.waze_history_track_direction)

    except Exception as err:
        log_exception(err)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 2
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>


#------------------------------------------------------------------------------
#
#   CREATE THE DEVICES OBJECT FROM THE DEVICE PARAMETERS IN THE
#   CONFIGURATION FILE
#
#   Set up the devices to be tracked and it's associated information
#   for the configuration line entry. This will fill in the following
#   fields based on the extracted devicename:
#       device_type
#       friendly_name
#       fmf email address
#       sensor.picture name
#       device tracking flags
#       tracked_devices list
#   These fields may be overridden by the routines associated with the
#   operating mode (fmf, icloud, iosapp)
#
#------------------------------------------------------------------------------
def create_Devices_object():

    try:
        old_Devices_by_devicename = Gb.Devices_by_devicename.copy()
        Gb.Devices               = []
        Gb.Devices_by_devicename = {}
        Gb.TrackedZones_by_zone  = {}
        Gb.TrackedZones_by_zone[HOME] = Gb.HomeZone
        inactive_device_cnt = 0

        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            broadcast_info_msg(f"Set up Device > {devicename}")

            if conf_device[CONF_TRACKING_MODE] ==  INACTIVE:
                event_msg = (f"{DOT}{devicename} > INACTIVE"
                            f"{CRLF_NBSP6_DOT}FamShr Device-{conf_device[CONF_FAMSHR_DEVICENAME]}"
                            f"{CRLF_NBSP6_DOT}FmF Device-{conf_device[CONF_FMF_EMAIL]}"
                            f"{CRLF_NBSP6_DOT}iOSApp Entity-{conf_device[CONF_IOSAPP_DEVICE]}")
                post_event(event_msg)
                continue

            # Reinitialize or add device, preserve the Sensor object if reinitializing
            if devicename in old_Devices_by_devicename:
                Device = old_Devices_by_devicename[devicename]
                Device.__init__(devicename, conf_device)
                post_monitor_msg(f"INITIALIZED Device-{devicename}")
            else:
                Device = iCloud3Device(devicename, conf_device)
                post_monitor_msg(f"ADDED Device-{devicename}")

            Gb.Devices.append(Device)
            Gb.Devices_by_devicename[devicename] = Device

            famshr_dev_msg = Device.conf_famshr_name if Device.conf_famshr_name else 'None'
            fmf_dev_msg    = Device.conf_fmf_email if Device.conf_fmf_email else 'None'
            iosapp_dev_msg = Device.iosapp_device_trkr_entity_id if Device.iosapp_device_trkr_entity_id else 'NotMonitored'

            event_msg = (f"{DOT}{devicename} > {Device.fname_devtype}"
                            f"{CRLF_NBSP6_DOT}FamShr Device-{famshr_dev_msg}"
                            f"{CRLF_NBSP6_DOT}FmF Device-{fmf_dev_msg}"
                            f"{CRLF_NBSP6_DOT}iOSApp Entity-{iosapp_dev_msg}")
            post_event(event_msg)

        event_msg = "Setting up iCloud3 Tracked Devices > "
        post_event(event_msg)

    except Exception as err:
        log_exception(err)

    return

#########################################################
#
#   INITIALIZE PYICLOUD DEVICE API
#   DEVICE SETUP SUPPORT FUNCTIONS FOR MODES FMF, FAMSHR, IOSAPP
#
#########################################################

def setup_tracked_devices_for_famshr():
    '''
    The Family Share device data is available from PyiCloud when logging into the iCloud
    account. This routine will get all the available FamShr devices from this data.
    The raw data devices are then cycled through and matched with the conf tracked devices.
    Their status is displayed on the Event Log. The device is also marked as verified.
    '''
    broadcast_info_msg(f"Stage 3 > Set up Family Share Devices")

    devices_desc = get_famshr_devices()
    device_id_by_device_fname   = devices_desc[0]
    device_fname_by_device_id   = devices_desc[1]
    device_info_by_device_fname = devices_desc[2]

    Gb.famshr_device_verified_cnt = 0
    event_msg = "Family Sharing List devices that can be tracked > "
    if device_fname_by_device_id == {}:
        event_msg += "No devices found"
        post_event(event_msg)
        return

    try:
        # Cycle thru the devices from those found in the iCloud data. We are not cycling
        # through the PyiCloud_DevData so we get devices without location info
        update_conf_file_flag = False
        for famshr_device_fname, device_id in device_id_by_device_fname.items():
            device_fname     = device_info_by_device_fname[famshr_device_fname].split(',')[0]
            broadcast_info_msg(f"Set up FamShr Device > {device_fname}")

            PyiCloud_DevData = None
            exception_msg    = ''

            # Cycle through the config tracked devices and find the matching device.
            for device in Gb.conf_devices:
                conf_famshr_device_fname = device[CONF_FAMSHR_DEVICENAME].split(" >")[0].strip()

                # The device's famshr config devicename will be the ic3 devicename when the parameters
                # are converted from the config_ic3.yaml file the first time iC3 is loaded. Chack for
                # this and change the famshr config parameter to the Device's fname.
                if (conf_famshr_device_fname != famshr_device_fname
                        and conf_famshr_device_fname == slugify(famshr_device_fname)):
                    device[CONF_FAMSHR_DEVICENAME] = famshr_device_fname
                    conf_famshr_device_fname = famshr_device_fname
                    update_conf_file_flag = True

                if conf_famshr_device_fname == famshr_device_fname:
                    devicename   = device[CONF_IC3_DEVICENAME]
                    device_fname = device[CONF_FNAME]
                    device_type  = device[CONF_DEVICE_TYPE]
                    PyiCloud_DevData = Gb.PyiCloud_DevData_by_device_id_famshr[device_id]
                    break

            if update_conf_file_flag:
                write_storage_icloud3_configuration_file()

            if PyiCloud_DevData is None:
                exception_msg = 'Not tracked'

            elif device[CONF_TRACKING_MODE] == INACTIVE:
                exception_msg = 'INACTIVE, Not tracked'
                PyiCloud_DevData.locatable_flag = False

            if exception_msg:
                event_msg += (f"{CRLF_DOT}{famshr_device_fname}{RARROW}{exception_msg}, {device_fname}")
                continue

            # If no location info in pyiCloud data but tracked device is matched, refresh the
            # data and see if it is locatable now. If so, all is OK. If not, set to verified but
            # display no location exception msg in EvLog
            if (LOCATION not in PyiCloud_DevData.device_data
                    or PyiCloud_DevData.device_data[LOCATION] is None
                    or PyiCloud_DevData.locatable_flag is False):
                exception_msg = f", No Location Info"
                Gb.PyiCloud_FamilySharing.refresh_client()
                if PyiCloud_DevData.locatable_flag:
                    exception_msg = ''

            if PyiCloud_DevData and Gb.log_rawdata_flag:
                log_title = (f"FamShr PyiCloud Data (device_data -- {famshr_device_fname}{INFO_SEPARATOR}{devicename}/{famshr_device_fname})")
                log_rawdata(log_title, {'data': PyiCloud_DevData.device_data})

            device_type = ''
            if devicename in Gb.Devices_by_devicename:
                Device                  = Gb.Devices_by_devicename[devicename]
                device_type             = Device.device_type
                Device.verified_flag    = True
                Device.device_id_famshr = device_id
                Gb.Devices_by_icloud_device_id[device_id] = Device
                Gb.famshr_device_verified_cnt += 1

                crlf_mark = CRLF_CHK
            else:
                crlf_mark = CRLF_DOT
            event_msg += (f"{crlf_mark}{famshr_device_fname}{RARROW}{devicename}, "
                            f"{device_fname}{INFO_SEPARATOR}{device_type}{exception_msg}")

        post_event(event_msg)

        return

    except Exception as err:
        log_exception(err)

        event_msg =(f"iCloud3 Error from iCloud Loc Svcs > "
            "Error Authenticating account or no data was returned from "
            "iCloud Location Services. iCloud access may be down or the "
            "Username/Password may be invalid.")
        post_error_msg(event_msg)

    return

#--------------------------------------------------------------------
def setup_tracked_devices_for_fmf():
    '''
    The Find-my-Friends device data is available from PyiCloud when logging into the iCloud
    account. This routine will get all the available FmF devices from the email contacts/following/
    followed data. The devices are then cycled through to be matched with the tracked devices
    and their status is displayed on the Event Log. The device is also marked as verified.
    '''
    broadcast_info_msg(f"Stage 3 > Set up Find-my-Friends Devices")

    devices_desc = get_fmf_devices()

    device_id_by_fmf_email   = devices_desc[0]
    fmf_email_by_device_id   = devices_desc[1]
    device_info_by_fmf_email = devices_desc[2]

    event_msg = "Find-My-Friends devices that can be tracked > "
    if device_id_by_fmf_email == {}:
        event_msg += "No devices found"
        post_event(event_msg)
        return

    try:
        Gb.fmf_device_verified_cnt = 0

        # Cycle through all the FmF devices in the iCloud account
        exception_event_msg = ''
        device_fname_by_device_id = {}
        for fmf_email, device_id in device_id_by_fmf_email.items():
            broadcast_info_msg(f"Set up FmF Device > {fmf_email}")
            devicename       = ''
            device_fname     = ''
            PyiCloud_DevData = None
            exception_msg    = ''

            # Cycle througn the tracked devices and find the matching device
            # Verify the device_id in the configuration with the found
            # device and display a configuration error msg later if something
            # doesn't match
            for device in Gb.conf_devices:
                conf_fmf_email = device[CONF_FMF_EMAIL].split(" >")[0].strip()

                if conf_fmf_email == fmf_email:
                    devicename   = device[CONF_IC3_DEVICENAME]
                    device_fname = device[CONF_FNAME]
                    device_type  = device[CONF_DEVICE_TYPE]
                    PyiCloud_DevData = Gb.PyiCloud_DevData_by_device_id_fmf[device_id]
                    break

            if PyiCloud_DevData is None:
                exception_msg = 'Not tracked'

            elif device[CONF_TRACKING_MODE] == INACTIVE:
                exception_msg = 'TRACKING DISABLED-Inactive Device'
                PyiCloud_DevData.locatable_flag = False

            if exception_msg:
                exception_event_msg += (f"{CRLF_DOT}{fmf_email}{RARROW}{exception_msg}")
                continue

            # If no location info in pyiCloud data but tracked device is matched, refresh the
            # data and see if it is locatable now. If so, all is OK. If not, set to verified but
            # display no location exception msg in EvLog
            if (LOCATION not in PyiCloud_DevData.device_data
                    or PyiCloud_DevData.device_data[LOCATION] is None
                    or PyiCloud_DevData.locatable_flag is False):
                exception_msg = f", No Location Info"
                Gb.PyiCloud_FindMyFriends.refresh_client()
                if PyiCloud_DevData.locatable_flag:
                    exception_msg = ''

            if PyiCloud_DevData and Gb.log_rawdata_flag:
                log_title = (f"FmF PyiCloud Data (device_data -- {devicename}/{fmf_email})")
                log_rawdata(log_title, {'data': PyiCloud_DevData.device_data})

            device_type = ''
            # The tracked device has been matched with available devices, mark it as verified.
            if devicename in Gb.Devices_by_devicename:
                Device               = Gb.Devices_by_devicename[devicename]
                device_fname_by_device_id[device_id] = Device.fname
                device_type          = Device.device_type
                Device.verified_flag = True
                Device.device_id_fmf = device_id
                Gb.Devices_by_icloud_device_id[device_id] = Device
                Gb.fmf_device_verified_cnt += 1

                event_msg += (f"{CRLF_CHK}{fmf_email}{RARROW}{devicename}, "
                                f"{device_fname}{INFO_SEPARATOR}{device_type}{exception_msg}")
            else:
                event_msg += (f"{CRLF_DOT}{fmf_email}{RARROW}{devicename}, "
                                f"{device_fname}{INFO_SEPARATOR}{device_type}{exception_msg}")

        # Replace known device_ids whith the actual name
        for device_id, device_fname in device_fname_by_device_id.items():
            exception_event_msg = exception_event_msg.replace(f"({device_id})", \
                                                                f"({device_fname_by_device_id[device_id]})")

        # Remove any unknown device_ids
        for device_id, fmf_email in fmf_email_by_device_id.items():
            exception_event_msg = exception_event_msg.replace(f"({device_id})", "")

        event_msg += exception_event_msg
        post_event(event_msg)

        return

    except Exception as err:
        log_exception(err)

        event_msg =(f"iCloud3 Error from iCloud Loc Svcs > "
            "Error Authenticating account or no data was returned from "
            "iCloud Location Services. iCloud access may be down or the "
            "Username/Password may be invalid.")
        post_error_msg(event_msg)

    return
#----------------------------------------------------------------------
def get_famshr_devices():
    '''
    Cycle through famshr data and get devices that can be tracked for the
    icloud device selection list
    '''
    device_id_by_device_fname = {}
    device_fname_by_device_id = {}
    device_info_device_fname  = {}
    if Gb.PyiCloud_DevData_by_device_id is None:
        return device_id_by_device_fname, device_fname_by_device_id, device_info_device_fname

    for device_id, PyiCloud_DevData in Gb.PyiCloud_DevData_by_device_id.items():
        if PyiCloud_DevData.tracking_method_FAMSHR:
            device_fname = PyiCloud_DevData.name
            device_fname = device_fname.replace("\xa0", " ")        # non-breakable space
            device_fname = device_fname.replace("’", "'")           # right quote mark

            try:
                if device_fname:
                    device_id_by_device_fname[device_fname] = device_id
                    device_fname_by_device_id[device_id]  = device_fname
                    desc = PyiCloud_DevData.device_identifier.replace("’", "'")
                    device_info_device_fname[device_fname]  = f"{device_fname} > {desc}"

            except:
                pass

    return device_id_by_device_fname, device_fname_by_device_id, device_info_device_fname

#----------------------------------------------------------------------
def get_fmf_devices():
    '''
    Cycle through fmf following, followers and contact details data and get
    devices that can be tracked for the icloud device selection list
    '''
    device_id_by_fmf_email      = {}
    fmf_email_by_device_id      = {}
    device_info_by_fmf_email    = {}
    device_form_icloud_fmf_list = []

    if Gb.PyiCloud_FindMyFriends is None:
        return device_id_by_fmf_email, fmf_email_by_device_id, device_info_by_fmf_email

    fmf_friends_data = {'emails': Gb.PyiCloud_FindMyFriends.contact_details,
                        'invitationFromHandles': Gb.PyiCloud_FindMyFriends.followers,
                        'invitationAcceptedHandles': Gb.PyiCloud_FindMyFriends.following}

    for fmf_email_field, Pyicloud_FmF_data in fmf_friends_data.items():
        if Pyicloud_FmF_data is None:
            continue

        for friend in Pyicloud_FmF_data:
            friend_emails = friend.get(fmf_email_field)
            full_name     = (f"{friend.get('firstName', '')} {friend.get('lastName', '')}")
            full_name     = full_name.strip()
            device_id     = friend.get('id')

            # extracted_fmf_devices.append((device_id, friend_emails))
            for friend_email in friend_emails:
                device_id_by_fmf_email[friend_email] = device_id
                fmf_email_by_device_id[device_id]    = friend_email
                friend_email_full_name = f"{friend_email} > {full_name}" if full_name else friend_email
                if (friend_email not in device_info_by_fmf_email  or full_name):
                    device_info_by_fmf_email[friend_email] = f"{friend_email_full_name}"

    return device_id_by_fmf_email, fmf_email_by_device_id, device_info_by_fmf_email

#--------------------------------------------------------------------
def set_device_tracking_method_iosapp():
    '''
    The Global tracking method is iosapp so set all Device's tracking method
    to iosapp
    '''
    if Gb.data_source_use_iosapp is False:
        return

    for Device in Gb.Devices:
        Device.tracking_method = 'iosapp'

#--------------------------------------------------------------------
def set_device_tracking_method_famshr_fmf():
    '''
    The goal is to get either all fmf or all famshr to minimize the number of
    calls to iCloud Web Services by pyicloud_ic3. Look at the fmf and famshr
    devices to see if:
    1. If all devices are fmf or all devices are famshr:
            Do not make any changes
    2. If set to fmf but it also has a famshr id, change to famshr.
    2. If set to fmf and no famshr id, leave as fmf.
    '''
    broadcast_info_msg(f"Stage 3 > Set up device data source")

    try:
        if Gb.Devices_by_devicename == {}:
            return

        Gb.Devices_by_icloud_device_id = {}
        devicename_not_tracked = {}
        for devicename, Device in Gb.Devices_by_devicename.items():
            tracking_method = None
            broadcast_info_msg(f"Determine Device Tracking Method >{devicename}")

            if Device.device_id_famshr:
                if Device.device_id_famshr in Gb.PyiCloud_DevData_by_device_id:
                    tracking_method = FAMSHR
                    Gb.Devices_by_icloud_device_id[Device.device_id_famshr] = Device
                    Device.PyiCloud_DevData_famshr = Gb.PyiCloud_DevData_by_device_id[Device.device_id_famshr]

            if Device.device_id_fmf:
                if Device.device_id_fmf in Gb.PyiCloud_DevData_by_device_id:
                    if tracking_method is None:
                        tracking_method = FMF
                    Gb.Devices_by_icloud_device_id[Device.device_id_fmf] = Device
                    Device.PyiCloud_DevData_fmf = Gb.PyiCloud_DevData_by_device_id[Device.device_id_fmf]

            if (Device.iosapp_monitor_flag
                    and tracking_method is None):
                tracking_method = IOSAPP

            if tracking_method != IOSAPP:
                if Device.device_id_famshr and Device.device_id_fmf is None:
                    Device.PyiCloud_DevData = Device.PyiCloud_DevData_famshr
                elif Device.device_id_fmf and Device.device_id_famshr is None:
                    Device.PyiCloud_DevData = Device.PyiCloud_DevData_fmf

                info_msg = (f"Set PyiCloud Device Id > {Device.devicename}, "
                            f"TrkMethod-{tracking_method}, "
                            f"{CRLF}FamShr-({Device.device_id8_famshr}), "
                            f"FmF-({Device.device_id8_fmf})")
                post_monitor_msg(info_msg)

            Device.tracking_method = tracking_method

        info_msg = (f"PyiCloud Devices > ")
        for _device_id, _PyiCloud_DevData in Gb.PyiCloud_DevData_by_device_id.items():
            info_msg += (f"{_PyiCloud_DevData.tracking_method}, ({_device_id[:8]}), ")
        post_monitor_msg(info_msg)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def tune_device_tracking_method_famshr_fmf():
    '''
    The goal is to get either all fmf or all famshr to minimize the number of
    calls to iCloud Web Services by pyicloud_ic3. Look at the fmf and famshr
    devices to see if:
    1. If all devices are fmf or all devices are famshr:
            Do not make any changes
    2. If set to fmf but it also has a famshr id, change to famshr.
    2. If set to fmf and no famshr id, leave as fmf.
    '''
    broadcast_info_msg(f"Stage 3 > Tune Tracking Method")

    try:
        # Global tracking_method specified, nothing to do
        if Gb.data_source_use_icloud is False:
            return
        elif Gb.Devices_by_devicename == {}:
            return

        cnt_famshr = 0     # famshr is specified as the tracking_method for the device in config
        cnt_fmf    = 0     # fmf is specified as the tracking_method for the device in config
        cnt_famshr_to_fmf = 0
        cnt_fmf_to_famshr = 0

        for devicename, Device in Gb.Devices_by_devicename.items():
            broadcast_info_msg(f"Tune Device Tracking Method > {devicename}")

            if Device.tracking_method_FAMSHR:
                cnt_famshr += 1
            elif Device.tracking_method_FMF:
                cnt_fmf += 1

            # Only count those with no tracking_method config parm
            Devices_famshr_to_fmf = []
            Devices_fmf_to_famshr = []
            if Device.tracking_method_config == '':
                if Device.tracking_method_FAMSHR and Device.device_id_fmf:
                    Devices_fmf_to_famshr.append(Device)
                    cnt_famshr_to_fmf += 1
                elif Device.tracking_method_FMF and Device.device_id_famshr:
                    Devices_famshr_to_fmf.append(Device)
                    cnt_fmf_to_famshr += 1

        if cnt_famshr == 0 or cnt_fmf == 0:
            pass
        elif cnt_famshr_to_fmf == 0 or cnt_fmf_to_famshr == 0:
            pass
        elif cnt_famshr >= cnt_fmf:
            for Device in Devices_fmf_to_famshr:
                Device.tracking_method = FAMSHR
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_fmf)
                Gb.Devices_by_icloud_device_id[Device.device_id_famshr] = Device
        else:
            for Device in Devices_famshr_to_fmf:
                Device.tracking_method = FMF
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_famshr)
                Gb.Devices_by_icloud_device_id[Device.device_id_fmf] = Device
    except:
        pass


#--------------------------------------------------------------------
def setup_tracked_devices_for_iosapp():
    '''
    Get the iOSApp device_tracker entities from the entity registry. Then cycle through the
    Devices being tracked and match them up. Anything left over at the end is not matched and not monitored.
    '''
    devices_desc = iosapp_interface.get_entity_registry_mobile_app_devices()

    iosapp_id_by_iosapp_devicename      = devices_desc[0]
    iosapp_devicename_by_iosapp_id      = devices_desc[1]
    device_info_iosapp_devicename       = devices_desc[2]
    last_updt_trig_by_iosapp_devicename = devices_desc[3]
    notify_iosapp_devicenames           = devices_desc[4]

    Gb.iosapp_device_verified_cnt = 0

    tracked_msg = "iOS App Devices > "
    for devicename, Device in Gb.Devices_by_devicename.items():
        broadcast_info_msg(f"Set up iOS App Devices > {devicename}")

        monitor_iosapp_device_trkr_entity_ids = []
        search_for_device_trkr_entity_id = ''
        aert_msg = ''

        # Set iosapp devicename to icloud devicename if nothing is specified. Set to not monitored
        # if no icloud famshr name
        if Device.iosapp_device_trkr_entity_id in ['', 'None']:
            Device.iosapp_device_trkr_entity_id = ''
            continue

        # Check if the specified iosapp device tracker is valid and in the entity registry
        elif Device.iosapp_device_trkr_entity_id != 'Search':
            if Device.iosapp_device_trkr_entity_id in iosapp_id_by_iosapp_devicename:
                monitor_iosapp_device_trkr_entity_ids = [Device.iosapp_device_trkr_entity_id]
            else:
                # iosapp config entry was not found, drop the suffix and see if that is found
                suffix_pos = Device.iosapp_device_trkr_entity_id.rfind('_')
                search_for_device_trkr_entity_id = Device.iosapp_device_trkr_entity_id[:suffix_pos]

                alert_msg = (f"{EVLOG_ALERT}iCloud3 Config Alert > {devicename}, iOS App device entity not found. "
                                f"Searching for a matching iOS App device entity."
                                f"{CRLF_DOT}Config Entry - {Device.iosapp_device_trkr_entity_id}"
                                f"{CRLF_DOT}Searching for - {search_for_device_trkr_entity_id}...")
                post_event(alert_msg)

                monitor_iosapp_device_trkr_entity_ids = [k for k in iosapp_id_by_iosapp_devicename.keys()
                                if k.startswith(search_for_device_trkr_entity_id)]

                if monitor_iosapp_device_trkr_entity_ids == []:
                    alert_msg = (f"{EVLOG_ALERT}iCloud3 Config Alert > {devicename}, iOS App device entity not found. "
                                    f"Searching for a matching FamShr devicename."
                                    f"{CRLF_DOT}Config Entry - {Device.iosapp_device_trkr_entity_id}"
                                    f"{CRLF_DOT}Searched for - {search_for_device_trkr_entity_id}..."
                                    f"{CRLF_DOT}Searching for - {Device.conf_famshr_devicename}...")

                    if alert_msg:
                        post_event(alert_msg)

        # Search for iosapp entity starting with famshr devicename
        if monitor_iosapp_device_trkr_entity_ids == []:
            if Device.conf_famshr_devicename:
                search_for_device_trkr_entity_id = Device.conf_famshr_devicename
                monitor_iosapp_device_trkr_entity_ids = [k for k in iosapp_id_by_iosapp_devicename.keys()
                                    if k.startswith(search_for_device_trkr_entity_id)]

            if monitor_iosapp_device_trkr_entity_ids == []:
                alert_msg = (f"{EVLOG_ALERT}iCloud3 Config Alert > {devicename}, iOS App device entity not found. "
                                f"Searched for a matching FamShr entity failed."
                                f"{CRLF_DOT}Config Entry - {Device.iosapp_device_trkr_entity_id}"
                                f"{CRLF_DOT}Searched for - {search_for_device_trkr_entity_id}...")
                post_event(alert_msg)

        Device.iosapp_device_trkr_entity_id = ''
        if len(monitor_iosapp_device_trkr_entity_ids) == 1:
            Device.iosapp_device_trkr_entity_id = monitor_iosapp_device_trkr_entity_ids[0]

        elif len(monitor_iosapp_device_trkr_entity_ids) > 1:
            Device.iosapp_device_trkr_entity_id = monitor_iosapp_device_trkr_entity_ids[-1]
            alert_msg =(f"{EVLOG_ALERT}iCloud3 Error > More than one iOS App device_tracker "
                    f"entities were found for a tracked device. Only one can be monitored"
                    f"{CRLF}{'-'*25}{CRLF}"
                    f"{devicename} > "
                    f"Found-{', '.join(monitor_iosapp_device_trkr_entity_ids)}, "
                    f"Monitored-{Device.iosapp_device_trkr_entity_id}"
                    f"{CRLF}{'-'*25}{CRLF}Do one of the following:"
                    f"{CRLF_DOT}Delete the incorrect device_tracker from the Entity Registry, or"
                    f"{CRLF_DOT}Change the iOSAPP Device Configuration for `{devicename}`, or"
                    f"{CRLF_DOT}Change the device_tracker entity's name of the one that should not "
                    f"be monitored so it does not start with `{devicename}`.")
            post_event(alert_msg)

        if Device.iosapp_device_trkr_entity_id:
            Device.iosapp_sensor_trigger_entity_id = \
                last_updt_trig_by_iosapp_devicename[Device.iosapp_device_trkr_entity_id]
            Device.verified_flag = True
            Device.iosapp_monitor_flag = True
            Gb.iosapp_device_verified_cnt += 1

            Device.iosapp_notify_devices = []
            for notify_iosapp_devicename in notify_iosapp_devicenames:
                if instr(notify_iosapp_devicename, devicename):
                    Device.iosapp_notify_devices.append(notify_iosapp_devicename)

            tracked_msg += (f"{CRLF_CHK}{Device.iosapp_device_trkr_entity_id}{RARROW}{devicename}, "
                            f"{Device.fname_devtype}")
                            # f"{CRLF_NBSP6_DOT}DeviceTracker > {Device.iosapp_device_trkr_entity_id}"
                            # f"{CRLF_NBSP6_DOT}UpdateTrigger > {Device.iosapp_sensor_trigger_entity_id}"
                            # f"{CRLF_NBSP6_DOT}Notifications > {', '.join(Device.iosapp_notify_devices)}")

            Device.iosapp_device_trkr_entity_id = f"device_tracker.{Device.iosapp_device_trkr_entity_id}"
            Device.iosapp_sensor_trigger_entity_id = f"sensor.{Device.iosapp_sensor_trigger_entity_id}"

            if Device.tracking_method_FAMSHR_FMF is False:
                Device.tracking_method = IOSAPP

            # Remove the iosapp device from the list since we know it is tracked
            iosapp_id_by_iosapp_devicename.pop(Device.iosapp_device_trkr_entity_id.replace('device_tracker.', ''))

    # Devices in the list were not matched with an iCloud3 device
    for iosapp_devicename, iosapp_id in iosapp_id_by_iosapp_devicename.items():
        if iosapp_id != 'matched':
            tracked_msg += (f"{CRLF_DOT}{iosapp_devicename}{RARROW}Not Monitored, "
                            f"{device_info_iosapp_devicename[iosapp_devicename]}")
    post_event(tracked_msg)

    return

#--------------------------------------------------------------------
def _get_entity_registry_item(Device, device_id, desired_entity_name):
    '''
    Scan through the iosapp entities and get the actual ios app entity_id for
    the desired entity
    '''
    for entity in (x for x in Gb.iosapp_entities \
            if x['unique_id'].endswith(desired_entity_name)):

        if (entity[DEVICE_ID] == device_id):
            entity_id = entity[ENTITY_ID]
            log_msg = (f"Matched iOS App {entity_id} with "
                        f"iCloud3 tracked_device {Device.devicename}")
            log_info_msg(log_msg)

            return entity_id

    return ''

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 3
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

def get_mobile_app_entities():
    '''
    Cycle through the HA Entity Registry and get all of the mobile_app entries
    '''
    _get_entity_registry_entities('mobile_app', 'device_tracker')
    if Gb.iosapp_entities != []:
        _get_mobile_app_notify_devicenames()
    else:
        event_msg =(f"iCloud3 Alert > No mobile_app device_tracker entities "
                    f"were found in the HA Entity Registry. The iOSApp "
                    f"will not be monitored for any device.")
        post_event(event_msg)

#------------------------------------------------------------------------------
def _get_entity_registry_entities(platform, domain):
    '''
    Read the /config/.storage/core.entity_registry file and return
    the entities for platform ('mobile_app', 'zone', etc)
    '''

    try:
        domain += '.'
        iosapp_entities, iosapp_entity_data = entity_io.get_entity_registry_data(platform=platform)
        Gb.iosapp_entities = iosapp_entities.copy()

        entity_devicename_list = ""
        for entity in iosapp_entity_data:
            if entity[ENTITY_ID].startswith(domain):
                devicename = slugify(entity['original_name'])
                devicename_iosapp_suffix = entity[ENTITY_ID].replace(domain, '')
                crlf_dot_chk = CRLF_CHK if devicename in Gb.Devices_by_devicename else CRLF_DOT
                entity_devicename_list += (f"{crlf_dot_chk}{devicename_iosapp_suffix}, "
                                            f"{entity['original_name']}")

        event_msg =(f"Entity Registry {platform} {domain[:-1]} entities found >{entity_devicename_list}")
        post_event(event_msg)

    except Exception as err:
        log_exception(err)
        pass

#------------------------------------------------------------------------------
def _get_mobile_app_notify_devicenames():
    '''
    Extract notify services devicenames from hass
    '''
    try:
        Gb.iosapp_notify_devicenames = []
        services = Gb.hass.services
        notify_services = dict(services.__dict__)['_services'][NOTIFY]

        for notify_service in notify_services:
            if notify_service.startswith(MOBILE_APP):
                Gb.iosapp_notify_devicenames.append(notify_service)
    except:
        pass

#------------------------------------------------------------------------------
def display_object_lists():
    '''
    Display the object list values
    '''
    broadcast_info_msg(f"Logging Initial Monitor Info")
    monitor_msg = (f"StatZones-{Gb.StatZones_by_devicename}")
    post_monitor_msg(monitor_msg)

    monitor_msg = (f"Devices-{Gb.Devices_by_devicename}")
    post_monitor_msg(monitor_msg)

    for Device in Gb.Devices:
        monitor_msg = (f"Device-{Device.devicename}, "
                        f"DeviceFmZones-{Device.DeviceFmZones_by_zone}")
        post_monitor_msg(monitor_msg)

    monitor_msg = (f"Zones-{Gb.Zones_by_zone}")
    post_monitor_msg(monitor_msg)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 4
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

def remove_unverified_untrackable_devices():
    _Devices_by_devicename = Gb.Devices_by_devicename.copy()
    device_removed_flag = False
    alert_msg =(f"{EVLOG_ALERT}Untrackable Device Alert > Devices are not being tracked:")
    for devicename, Device in _Devices_by_devicename.items():
        Device.display_info_msg("Verifing Devices")

        # Device not verified as valid FmF, FamShr or iOSApp device. Remove from devices list
        if (Device.tracking_method is None
                or Device.verified_flag is False):
            device_removed_flag = True
            alert_msg +=(f"{CRLF_DOT}{devicename}, {Device.fname_devtype}")

            devicename = Device.devicename
            if Device.device_id_famshr:
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_famshr)
                Gb.PyiCloud_Devices_by_device_id.pop(Device.device_id_famshr)
                Gb.PyiCloud_Devices_by_device_id_famshr.pop(Device.device_id_famshr)
            if Device.device_id_fmf:
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_fmf)
                Gb.PyiCloud_Devices_by_device_id.pop(Device.device_id_fmf)
                Gb.PyiCloud_Devices_by_device_id_fmf.pop(Device.device_id_fmf)

            Gb.Devices_by_devicename.pop(devicename)

    if device_removed_flag:
        alert_msg +=(f"{CRLF}{DASH_20}"
                    f"{CRLF}This can be caused by:"
                    f"{CRLF_DOT}iCloud3 Device configuration error -- No iCloud (FamShr/FmF) device and no iOS App device have been selected, or"
                    f"{CRLF_DOT}This device is no longer in the Family Sharing list or "
                    f"FindMyFriends list, or"
                    f"{CRLF_DOT}iCloud or iOS App are not being used to locate devices and devices have "
                    f"been configured to use them, or "
                    f"{CRLF_DOT}iCloud is not responding to location requests.")
        post_event(alert_msg)

#------------------------------------------------------------------------------
def setup_trackable_devices():

    for devicename, Device in Gb.Devices_by_devicename.items():
        Device.display_info_msg(f"Set Trackable Devices > {devicename}")
        event_msg =(f"Configuring Device > {devicename}, {Device.fname}")

        if Device.tracking_method_FAMSHR:
            Gb.tracking_method_FAMSHR_used = True
        elif Device.tracking_method_FMF:
            Gb.tracking_method_FMF_used = True

        event_msg += (f"{CRLF_DOT}FamShr Device > {Device.conf_famshr_name}"
                        f"{CRLF_DOT}FmF Device > {Device.conf_fmf_email}")
        if Device.device_id_famshr or Device.device_id_fmf:
            event_msg += (f"{CRLF_DOT}iCloud DevIDs > FamShr-({Device.device_id8_famshr}), "
                        f"FmF-({Device.device_id8_fmf})")

        # Initialize iosapp state & location fields
        if Device.iosapp_monitor_flag:
            Gb.tracking_method_IOSAPP_used = True
            iosapp_data_handler.get_iosapp_device_trkr_entity_attrs(Device)

            event_msg += (f"{CRLF_DOT}iOSApp Entity > {Device.iosapp_device_trkr_entity_id}"
                            f"{CRLF_DOT}Update Trigger > "
                            f"{Device.iosapp_sensor_trigger_entity_id.replace('sensor.', '')}"
                            f"{CRLF_DOT}Notifications > {', '.join(Device.iosapp_notify_devices)}")
        else:
            event_msg += (f"{CRLF_DOT}iOSApp Entity > None")

        # Display all sensor entities early. Value displaye will be '---'
        create_Device_StationaryZone_object(Device)
        info_msg = f"{DOT}Initialize Stationary Zone > {Device.stationary_zonename}"
        Device.display_info_msg(info_msg)
        event_msg += f"{CRLF}{info_msg}"

        if Device.track_from_zones != [HOME]:
            track_from_zones = Device.track_from_zones
            track_from_zones = ', '.join(track_from_zones)
            event_msg += (f"{CRLF_DOT}Track from zones > {track_from_zones}")

        Device.initialize_usage_counters()

        post_event(event_msg)

#------------------------------------------------------------------------------
def create_Device_StationaryZone_object(Device):

    devicename = Device.devicename
    old_StatZones_by_devicename = Gb.StatZones_by_devicename.copy()
    Gb.StatZones = []
    Gb.StatZones_by_devicename = {}

    # Setup Stationary zone for the device, set to base location
    if devicename in old_StatZones_by_devicename:
        StatZone = old_StatZones_by_devicename[devicename]
        StatZone.__init__(Device)
        post_monitor_msg(f"INITIALIZED StationaryZone-{devicename}_stationary")
    else:
        StatZone = iCloud3StationaryZone(Device)
        post_monitor_msg(f"ADDED StationaryZone-{devicename}_stationary")

    Device.StatZone = StatZone
    Gb.StatZones.append(StatZone)
    Gb.StatZones_by_devicename[devicename] = StatZone
    Gb.state_to_zone[Device.stationary_zonename] = Device.stationary_zonename

#------------------------------------------------------------------------------
def display_platform_operating_mode_msg():
    if Gb.operating_mode == MODE_PLATFORM:
        alert_msg = (f"{EVLOG_ALERT}iCloud3 Operating Mode > Platform/Legacy Mode"
                f"{CRLF_DOT}iCloud3 was started using the HA configuration.yaml "
                f"file `device_tracker > platform: icloud3` parameter. ")

        if Gb.conf_profile[CONF_VERSION] == 0:
            alert_msg += (f"{CRLF_DOT}iCloud3 v2{RARROW}v3 configuration parameter "
                f"conversion complete."
                f"{CRLF_NBSP6_DOT}Source-{Gb.config_ic3_yaml_filename}"
                f"{CRLF_NBSP6_DOT}Target-{Gb.icloud3_config_filename}")
        alert_msg += (f"{CRLF_DOT}iCloud3 configuration parameters are updated on the "
            f"`Configuration > Integrations > iCloud3 Integration` screen."
            f"{CRLF_DOT}Add the iCloud3 Integration if it is not listed.")

        post_event(alert_msg)

#------------------------------------------------------------------------------
def post_restart_icloud3_complete_msg():
    for devicename, Device in Gb.Devices_by_devicename.items():   #
        Device.display_info_msg("Setup Complete, Locating Device")

    event_msg =(f"{EVLOG_INIT_HDR}Initializing iCloud3 v{Gb.version} > Complete")

    post_event(event_msg)
    Gb.EvLog.update_event_log_display("")