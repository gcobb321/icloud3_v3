#####################################################################
#
#   Global Variables Class Object
#
#   Global Variables is a general class to allow access to iCloud3 shared variables from
#   multiple classes. The variable to be referenced is defined in the __init__
#   function with it's default value.
#
#   Usage:
#       The following code is added to the module.py file containing another class
#       that needs access to the shared global variables.
#
#       Add the following code before the class statement:
#           from .globals import GlobalVariables as GbObj
#
#       Add the following code in the __init__ function:
#           def __init(self, var1, var2, ...):
#               global Gb
#               Gb = GbObj.MasterGbObject
#
#       The shared variables can then be shared using the Gb object:
#           Gb.time_format
#           Gb.Zones_by_zone
#####################################################################

from .const          import (NOT_SET, HOME_FNAME, HOME, STORAGE_DIR, WAZE_USED, FAMSHR, FMF, FAMSHR_FMF, ICLOUD,
                            HIGH_INTEGER,

                            AUTHENTICATED, TRACKING, ICLOUD3_VERSION,
                            DEFAULT_GENERAL_CONF,

                            CONF_UNIT_OF_MEASUREMENT,
                            CONF_DISPLAY_ZONE_FORMAT, CONF_CENTER_IN_ZONE,
                            CONF_TRAVEL_TIME_FACTOR, CONF_GPS_ACCURACY_THRESHOLD,
                            CONF_DISCARD_POOR_GPS_INZONE, CONF_MAX_INTERVAL,
                            CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                            CONF_WAZE_REALTIME,
                            CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE ,
                            CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION,
                            CONF_STAT_ZONE_STILL_TIME,
                            CONF_STAT_ZONE_BASE_LATITUDE, CONF_STAT_ZONE_BASE_LONGITUDE,
                            CONF_STAT_ZONE_INZONE_INTERVAL, CONF_LOG_LEVEL,
                            CONF_IOSAPP_REQUEST_LOC_MAX_CNT,

                            DEFAULT_MAX_INTERVAL_SECS, DEFAULT_STAT_ZONE_STILL_TIME_SECS,
                            DEFAULT_STAT_ZONE_INZONE_INTERVAL_SECS,
                            )


import logging
_LOGGER = logging.getLogger("icloud3_cf")

#TODO
# 1. Change Version
# 2. Change constants_general.EVENT_LOG_CLEAR_SECS

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class GlobalVariables(object):
    '''
    Define global variables used in the various iCloud3 modules
    '''
    # Fixed variables set during iCloud3 loading that will not change
    version         = '3.0.0'
    iCloud3         = None      # iCloud3 Platform object
    hass            = None      # hass: HomeAssistant set in __init__
    config_entry    = None      # hass.config_entry set in __init__
    OptionsFlowHandler = None   # config_flow OptionsFlowHandler
    see             = None
    EvLog           = None
    HALogger        = None
    Sensors         = None
    iC3EntityPlatform = None    # iCloud3 Entity Platform (homeassistant.helpers.entity_component)
    PyiCloud        = None
    Waze            = None
    WazeHist        = None
    attrs           = {}
    operating_mode  = 0        # Platform (Legacy using configuration.yaml) or Integration
    icloud3_v2_to_v3_parameters_converted = False

    add_entities = None

    # iCloud3 Directory & File Names
    ha_config_directory       = ''
    ha_storage_directory      = ''      # 'config/.storage' directory
    ha_storage_icloud3        = ''      # 'config/.storage/icloud'
    icloud3_config_filename   = ''      # '.storage/icloud3.configuration' - iC3 Configuration File
    config_ic3_yaml_filename  = ''      # 'conf/config_ic3.yaml' (v2 config file name)
    icloud3_directory         = ''
    icloud3_filename          = ''
    # icloud3_evlog_js_filename = ''
    ha_config_www_directory   = ''
    www_evlog_js_directory    = ''
    www_evlog_js_filename     = ''

    # Platform and iCloud account parameters
    username                     = ''
    username_base                = ''
    password                     = ''
    all_famshr_devices           = True
    entity_registry_file         = ''
    event_log_card_directory     = ''
    event_log_card_program       = ''
    # event_log_card_js_file_name  = ''
    devices                      = ''

    # Global Object Dictionaries
    Devices                           = []  # Devices objects list
    Devices_by_devicename             = {}  # All Devices by devicename
    Devices_by_icloud_device_id       = {}  # FmF/FamShr Device Configuration
    Zones                             = []  # Zones object list
    Zones_by_zone                     = {}  # Zone object by zone name
    TrackedZones_by_zone              = {HOME, None}  # Tracked zones object by zone name set up with Devices.DeviceFmZones object
    StatZones                         = []  # Stationary Zone objects
    StatZones_by_devicename           = {}  # Stationary Zone objects by devicename
    HomeZone                          = None # Home Zone object

    PyiCloud_FamilySharing            = None # PyiCloud_ic3 object for FamilySharig used to refresh the device's location
    PyiCloud_FindMyFriends            = None # PyiCloud_ic3 object for FindMyFriends used to refresh the device's location
    PyiCloud_DevData_by_device_id     = {}   # Device data for tracked devices, updated in Pyicloud famshr.refresh_client
    PyiCloud_DevData_by_device_id_famshr = {}
    PyiCloud_DevData_by_device_id_fmf = {}

    # System Wide variables control iCloud3 start/restart procedures
    start_icloud3_inprocess_flag    = False
    start_icloud3_request_flag      = False
    start_icloud3_initial_load_flag = False
    any_device_being_updated_flag   = False
    update_in_process               = False
    evlog_action_request            = ''

    # Debug and trace flags
    log_debug_flag               = False
    log_rawdata_flag             = False
    log_rawdata_flag_unfiltered  = False
    log_debug_flag_restart       = None
    log_rawdata_flag_restart     = None
    evlog_trk_monitors_flag      = False
    info_notification            = ''
    trace_text_change_1          = ''
    trace_text_change_2          = ''

    # Startup variables
    startup_log_msgs          = ''
    startup_log_msgs_prefix   = ''
    iosapp_entities           = ''
    iosapp_notify_devicenames = ''


    # Configuration parameters that can be changed in config_ic3.yaml
    um                     = DEFAULT_GENERAL_CONF[CONF_UNIT_OF_MEASUREMENT]
    time_format            = 12
    um_km_mi_factor        = .62137
    um_m_ft                = 'ft'
    um_kph_mph             = 'mph'
    um_time_strfmt         = '%I:%M:%S'
    um_time_strfmt_ampm    = '%I:%M:%S%P'
    um_date_time_strfmt    = '%Y-%m-%d %H:%M:%S'

    # Time conversion variables used in global_utilities
    time_zone_offset_seconds    = 0
    timestamp_local_offset_secs = 0

    # Configuration parameters
    config_parm                     = {}        # Config parms from HA config.yaml and config_ic3.yaml
    config_parm_initial_load        = {}        # Config parms from HA config.yaml used to reset eveerything on restart
    config_parm_ha_config_yaml      = {}        # Config parms from HA config.yaml used during initial conversion to config_flow

    conf_file_data    = {}
    conf_profile      = {}
    conf_data         = {}
    conf_tracking     = {}
    conf_devices      = []
    conf_general      = {}
    conf_sensors      = {}

    # This stores the type of configuration parameter change done in the config_flow module
    # It indicates the type of change and if a restart is required to load device or sensor changes.
    # Items in the set are 'tracking', 'devices', 'profile', 'sensors', 'general', 'restart'
    config_flow_update_control = {''}

    distance_method_waze_flag       = True
    max_interval_secs               = DEFAULT_MAX_INTERVAL_SECS
    gps_accuracy_threshold          = DEFAULT_GENERAL_CONF[CONF_GPS_ACCURACY_THRESHOLD]
    travel_time_factor              = DEFAULT_GENERAL_CONF[CONF_TRAVEL_TIME_FACTOR]
    old_location_threshold          = 180
    log_level                       = DEFAULT_GENERAL_CONF[CONF_LOG_LEVEL]

    # iosapp_request_loc_max_cnt      = DEFAULT_GENERAL_CONF[CONF_IOSAPP_REQUEST_LOC_MAX_CNT]
    center_in_zone_flag             = DEFAULT_GENERAL_CONF[CONF_CENTER_IN_ZONE]
    display_zone_format             = DEFAULT_GENERAL_CONF[CONF_DISPLAY_ZONE_FORMAT]
    discard_poor_gps_inzone_flag    = DEFAULT_GENERAL_CONF[CONF_DISCARD_POOR_GPS_INZONE]

    waze_region                     = DEFAULT_GENERAL_CONF[CONF_WAZE_REGION]
    waze_max_distance               = DEFAULT_GENERAL_CONF[CONF_WAZE_MAX_DISTANCE]
    waze_min_distance               = DEFAULT_GENERAL_CONF[CONF_WAZE_MIN_DISTANCE]
    waze_realtime                   = DEFAULT_GENERAL_CONF[CONF_WAZE_REALTIME]
    waze_history_database_used      = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_DATABASE_USED]
    waze_history_max_distance       = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_MAX_DISTANCE]
    waze_history_map_track_direction= DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION]

    # stationary_still_time_str       = DEFAULT_GENERAL_CONF[CONF_STATIONARY_STILL_TIME]
    stat_zone_still_time_secs        = DEFAULT_STAT_ZONE_STILL_TIME_SECS
    # stationary_zone_offset          = DEFAULT_GENERAL_CONF[CONF_STATIONARY_ZONE_OFFSET]
    stat_zone_base_latitude  = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_BASE_LATITUDE]
    stat_zone_base_longitude = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_BASE_LONGITUDE]
    # stationary_inzone_interval_str  = DEFAULT_GENERAL_CONF[CONF_STATIONARY_INZONE_INTERVAL]
    stat_zone_inzone_interval_secs       = DEFAULT_STAT_ZONE_INZONE_INTERVAL_SECS
    # Variables used to config the device variables when setting up
    # intervals and determining the tracking method
    inzone_interval_secs = {}
    # config_inzone_interval_secs = {}

    # Tracking method control vaiables
    # Used to reset Gb.tracking_method after pyicloud/icloud account successful reset
    tracking_method_use_icloud   = True     # Master icloud tracking method flag (set in config_flow icloud)
    tracking_method_use_iosapp   = True     # Master iosapp tracking method flag (set in config_flow icloud)
    tracking_method_config_last_restart = NOT_SET
    tracking_method_config       = ''   #NOT_SET
    tracking_method              = ''    #NOT_SET   # Will be changed to IOSAPP if pyicloud errors
    tracking_method_FMF          = False
    tracking_method_FAMSHR       = False
    tracking_method_IOSAPP       = False
    tracking_method_FMF_used     = False
    tracking_method_FAMSHR_used  = False
    tracking_method_IOSAPP_used  = False

    # iCloud account authorization variables
    icloud_no_data_error_cnt        = 0
    authenticated_time              = 0
    authentication_error_cnt        = 0
    authentication_error_retry_secs = HIGH_INTEGER
    pyicloud_refresh_time         = {}     # Last time Pyicloud was refreshed for the trk method
    pyicloud_refresh_time[FMF]    = 0
    pyicloud_refresh_time[FAMSHR] = 0

    # Pyicloud counts, times and common variables
    pyicloud_authentications_cnt = 0
    pyicloud_location_update_cnt = 0
    pyicloud_calls_time          = 0.0
    trusted_device               = None
    verification_code            = None
    icloud_cookies_dir           = ''
    icloud_cookies_file          = ''
    fmf_device_verified_cnt      = 0
    famshr_device_verified_cnt   = 0
    iosapp_device_verified_cnt   = 0

    # Waze History for DeviceFmZone
    wazehist_db_zone_id         = {}
    waze_status                 = WAZE_USED
    waze_manual_pause_flag      = False         # Paused using service call
    waze_close_to_zone_pause_flag = False         # Close to home pauses Waze

    # Variables to be moved to Device object when available
    # iosapp entity data
    last_iosapp_state                = {}
    last_iosapp_state_changed_time   = {}
    last_iosapp_state_changed_secs   = {}
    last_iosapp_trigger              = {}
    last_iosapp_trigger_changed_time = {}
    last_iosapp_trigger_changed_secs = {}
    iosapp_monitor_error_cnt         = {}

    # Device state, zone data from icloud and iosapp
    state_to_zone     = {}
    this_update_secs  = 0
    this_update_time  = ''
    state_this_poll   = {}
    state_last_poll   = {}
    zone_last         = {}
    zone_current      = {}
    zone_timestamp    = {}
    state_change_flag = {}

    # Device status and tracking fields
    # config_track_devices_fields     = []            # Device parameter dict for all devices
    # config_track_devices_fields_last_restart = []   # Saved copy used to see if devices parameters were changed on reload
    config_track_devices_change_flag = True         # Set in config_handler when parms are loaded. Do Stave 1 only if no device changes
    # config_ic3_track_devices_fields = []
    device_tracker_entity_ic3      = {}
    trigger                        = {}
    got_exit_trigger_flag          = {}
    device_being_updated_flag      = {}
    device_being_updated_retry_cnt = {}
    iosapp_update_flag             = {}
    attr_tracking_msg              = '' # tracking msg on attributes

    # Miscellenous variables
    broadcast_msg                  = ''

    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

    # def __init__():
    #     attrs                     = {}
    #     attrs[AUTHENTICATED]      = ''
    #     attrs[TRACKING]           = ''
    #     attrs[ICLOUD3_VERSION]    = ''

    config_flow_flag = False
