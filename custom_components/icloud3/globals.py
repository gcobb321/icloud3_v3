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

from .const_general import (NOT_SET, HOME_FNAME, HOME, WAZE_USED, FAMSHR, FMF, FAMSHR_FMF, ICLOUD,
                            HIGH_INTEGER, )
from .const_attrs   import (AUTHENTICATED, TRACKING, ICLOUD3_VERSION,
                            DEFAULT_UNIT_OF_MEASUREMENT, DEFAULT_DISPLAY_TEXT_AS, DEFAULT_TIME_FORMAT,
                            DEFAULT_DISTANCE_METHOD, DEFAULT_INZONE_INTERVAL, DEFAULT_INZONE_INTERVALS,
                            DEFAULT_DISPLAY_ZONE_FORMAT, DEFAULT_CENTER_IN_ZONE, DEFAULT_MAX_INTERVAL,
                            DEFAULT_TRAVEL_TIME_FACTOR, DEFAULT_GPS_ACCURACY_THRESHOLD,
                            DEFAULT_OLD_LOCATION_THRESHOLD, DEFAULT_IGNORE_GPS_ACC_INZONE,
                            DEFAULT_CHECK_GPS_ACC_INZONE, DEFAULT_HIDE_GPS_COORDINATES,
                            DEFAULT_WAZE_REGION, DEFAULT_WAZE_MAX_DISTANCE, DEFAULT_WAZE_MIN_DISTANCE,
                            DEFAULT_WAZE_REALTIME, DEFAULT_WAZE_HISTORY_MAX_DISTANCE ,
                            DEFAULT_WAZE_HISTORY_MAP_TRACK_DIRECTION,
                            DEFAULT_STATIONARY_STILL_TIME, DEFAULT_STATIONARY_ZONE_OFFSET,
                            DEFAULT_STATIONARY_INZONE_INTERVAL, DEFAULT_LOG_LEVEL,
                            DEFAULT_IOSAPP_REQUEST_LOC_MAX_CNT,
                            DEFAULT_LEGACY_MODE, )


import logging
_LOGGER = logging.getLogger("icloud3")

#TODO
# 1. Change Version
# 2. Change constants_general.EVENT_LOG_CLEAR_SECS

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class GlobalVariables(object):
    '''
    Define global variables used in the various iCloud3 modules
    '''
    # Fixed variables set during iCloud3 loading that will not change
    version         = '3.0.0b1'
    Icloud3Platform = None
    hass            = None
    see             = None
    EvLog           = None
    HALog           = None
    Sensors         = None
    PyiCloud        = None
    Waze            = None
    WazeHist        = None
    attrs           = {}

    # iCloud3 Directory & File Names
    icloud3_dir               = ''
    icloud3_filename          = ''
    icloud3_evlog_js_filename = ''
    www_evlog_js_dir          = ''
    www_evlog_js_filename     = ''
    config_ic3_filename       = ''
    # config_ic3_file_name         = ''

    # Platform and iCloud account parameters
    username                     = ''
    username_base                = ''
    password                     = ''
    entity_registry_file         = ''
    event_log_card_directory     = ''
    config_devices_schema        = ''

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
    um                     = DEFAULT_UNIT_OF_MEASUREMENT
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
    center_in_zone_flag             = DEFAULT_CENTER_IN_ZONE
    display_zone_format             = DEFAULT_DISPLAY_ZONE_FORMAT
    max_interval_secs               = 240
    travel_time_factor              = DEFAULT_TRAVEL_TIME_FACTOR
    gps_accuracy_threshold          = DEFAULT_GPS_ACCURACY_THRESHOLD
    old_location_threshold          = 180
    ignore_gps_accuracy_inzone_flag = DEFAULT_IGNORE_GPS_ACC_INZONE
    check_gps_accuracy_inzone_flag  = DEFAULT_CHECK_GPS_ACC_INZONE
    hide_gps_coordinates            = DEFAULT_HIDE_GPS_COORDINATES
    distance_method_waze_flag       = True
    legacy_mode_flag                = DEFAULT_LEGACY_MODE
    log_level                       = DEFAULT_LOG_LEVEL
    iosapp_request_loc_max_cnt      = DEFAULT_IOSAPP_REQUEST_LOC_MAX_CNT

    waze_region                     = DEFAULT_WAZE_REGION
    waze_max_distance               = DEFAULT_WAZE_MAX_DISTANCE
    waze_min_distance               = DEFAULT_WAZE_MIN_DISTANCE
    waze_realtime                   = DEFAULT_WAZE_REALTIME
    waze_history_max_distance       = DEFAULT_WAZE_HISTORY_MAX_DISTANCE
    waze_history_map_track_direction= DEFAULT_WAZE_HISTORY_MAP_TRACK_DIRECTION

    stationary_still_time_str       = DEFAULT_STATIONARY_STILL_TIME
    stationary_zone_offset          = DEFAULT_STATIONARY_ZONE_OFFSET
    stationary_inzone_interval_str  = DEFAULT_STATIONARY_INZONE_INTERVAL

    # Variables used to config the device variables when setting up
    # intervals and determining the tracking method
    inzone_interval_secs = {}       # Probably not needed
    config_inzone_interval_secs = {}

    # Tracking method control vaiables
    # Used to reset Gb.tracking_method after pyicloud/icloud account successful reset
    tracking_method_config_last_restart = ''    #NOT_SET
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

    # Pyicloud counts, times and common variables
    pyicloud_authentications_cnt = 0
    pyicloud_location_update_cnt = 0
    pyicloud_calls_time          = 0.0
    trusted_device               = None
    verification_code            = None
    icloud_cookies_dir           = ''
    icloud_cookies_file          = ''

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
    config_track_devices_fields     = []            # Device parameter dict for all devices
    config_track_devices_fields_last_restart = []   # Saved copy used to see if devices parameters were changed on reload
    config_track_devices_change_flag = True         # Set in ic3_config when parms are loaded. Do Stave 1 only if no device changes
    config_ic3_track_devices_fields = []
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

    def __init__():
        attrs                     = {}
        attrs[AUTHENTICATED]      = ''
        attrs[TRACKING]           = ''
        attrs[ICLOUD3_VERSION]    = ''
