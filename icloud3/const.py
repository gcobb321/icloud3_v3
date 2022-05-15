#####################################################################
#
#   Define the iCloud3 General Constants
#
#####################################################################


#from ast import Interactive
#from imp import SEARCH_ERROR
#from turtle import distance


DOMAIN                          = 'icloud3'
MODE_PLATFORM                   = -1
MODE_INTEGRATION                = 1
DEBUG_TRACE_CONTROL_FLAG        = False
STORAGE_KEY                     = DOMAIN
STORAGE_VERSION                 = 1

HA_ENTITY_REGISTRY_FILE_NAME    = 'config/.storage/core.entity_registry'
ENTITY_REGISTRY_FILE_KEY        = 'core.entity_registry'
DEFAULT_CONFIG_IC3_FILE_NAME    = 'config/config_ic3.yaml'

STORAGE_DIR                     = ".storage"
STORAGE_KEY_ENTITY_REGISTRY     = 'core.entity_registry'
# SENSOR_EVENT_LOG_ENTITY         = 'sensor.icloud3_event_log'
SENSOR_EVENT_LOG_NAME           = 'icloud3_event_log'
EVENT_LOG_CARD_WWW_DIRECTORY    = 'custom_cards'
EVENT_LOG_CARD_WWW_JS_PROG      = 'icloud3-event-log-card.js'
WAZE_LOCATION_HISTORY_DATABASE  = 'icloud3.waze_location_history.db'
SENSOR_WAZEHIST_TRACK_NAME      = 'icloud3_wazehist_track'

DEVICE_TRACKER                  = 'device_tracker'
DEVICE_TRACKER_DOT              = 'device_tracker.'
PLATFORMS                       = ['sensor', 'device_tracker']
PLATFORM                        = 'device_tracker'
SENSOR                          = 'sensor'
ATTRIBUTES                      = 'attributes'
ENTITY_ID                       = 'entity_id'
HA_DEVICE_TRACKER_LEGACY_MODE   = False
MOBILE_APP                      = 'mobile_app_'
NOTIFY                          = 'notify'

# General constants
HOME                            = 'home'
HOME_FNAME                      = 'Home'
NOT_HOME                        = 'not_home'
NOT_HOME_FNAME                  = 'Not Home'
NOT_SET                         = 'not_set'
NOT_SET_FNAME                   = 'Not Set'
UNKNOWN                         = 'Unknown'
STATIONARY                      = 'stationary'
STATIONARY_FNAME                = 'Stationary'
NEAR_ZONE                       = 'near_zone'
NEAR_ZONE_FNAME                 = 'Near Zone'
AWAY_FROM                       = 'Away From'
AWAY                            = 'Away'
TOWARDS                         = 'To-'
PAUSED                          = 'PAUSED'
PAUSED_CAPS                     = 'PAUSED'
RESUMING                        = 'RESUMING'
RESUMING_CAPS                   = 'RESUMING'
NEVER                           = 'Never'
ERROR                           = 0
#NONE                            = 'none'
#NONE_CAPS                       = 'None'
#SEARCH                          = 'search'
#SEARCH_CAPS                     = 'Search'
VALID_DATA                      = 1
UTC_TIME                        = True
LOCAL_TIME                      = False
NUMERIC                         = True
NEW_LINE                        = '\n'
WAZE                            = 'waze'
CALC                            = 'calc'
DIST                            = 'dist'

IPHONE_FNAME                    = 'iPhone'
IPHONE                          = 'iphone'
IPAD_FNAME                      = 'iPad'
IPAD                            = 'ipad'
IPOD_FNAME                      = 'iPod'
IPOD                            = 'ipod'
WATCH_FNAME                     = 'Watch'
WATCH                           = 'watch'
AIRPODS_FNAME                   = 'AirPods'
AIRPODS                         = 'airpods'
ICLOUD_FNAME                    = 'iCloud'
ICLOUD                          = 'icloud'
OTHER_FNAME                     = 'Other'
OTHER                           = 'other'

APPLE_DEVICE_TYPES = [
        IPHONE, IPAD, IPOD, WATCH, ICLOUD_FNAME, AIRPODS,
        IPHONE_FNAME, IPAD_FNAME, IPOD_FNAME, WATCH_FNAME, ICLOUD_FNAME, AIRPODS_FNAME,]

APPLE_DEVICE_TYPES_FNAME = [
        IPHONE_FNAME, IPAD_FNAME, WATCH_FNAME, IPOD_FNAME, AIRPODS_FNAME, OTHER_FNAME]

APPLE_DEVICE_TYPE_TO_FNAME = {
        IPHONE: IPHONE_FNAME,
        IPAD: IPAD_FNAME,
        IPOD: IPOD_FNAME,
        WATCH: WATCH_FNAME,
        AIRPODS: AIRPODS_FNAME,
        OTHER: OTHER_FNAME,
}
APPLE_FNAME_TO_DEVICE_TYPE = {
        IPHONE_FNAME: IPHONE,
        IPAD_FNAME: IPAD,
        IPOD_FNAME: IPOD,
        WATCH_FNAME: WATCH,
        AIRPODS_FNAME: AIRPODS,
        OTHER_FNAME: OTHER,
}

# DATETIME_FORMAT                 = '%Y-%m-%d %H:%M:%S.%f'
DATETIME_FORMAT                 = '%Y-%m-%d %H:%M:%S'
DATETIME_ZERO                   = '0000-00-00 00:00:00'
HHMMSS_ZERO                     = '00:00:00'
HIGH_INTEGER                    = 9999999999

# Device Tracking Status
TRACKING_NORMAL            = 0
TRACKING_PAUSED            = 1
TRACKING_RESUMED           = 2

#Other constants
IOSAPP_DT_ENTITY = True
ICLOUD_DT_ENTITY = False
ICLOUD_LOCATION_DATA_ERROR = False
CMD_RESET_PYICLOUD_SESSION = 'reset_session'
NEAR_DEVICE_DISTANCE       = 20
PASS_THRU_ZONE_INTERVAL_SECS = 60       # Delay time before moving into a non-tracked zone to see if if just passing thru

# used by the Gb.stationary_zone_update_control field to indicate the
# Stat Zone should be updated when the Device location info is updated
STAT_ZONE_NO_UPDATE        = 0
STAT_ZONE_MOVE_DEVICE_INTO = 100
STAT_ZONE_MOVE_TO_BASE     = 1

EVLOG_RECDS_PER_DEVICE  = 2000          #Used to calculate the max recds to store
EVENT_LOG_CLEAR_SECS    = 6000  #600           #Clear event log data interval
EVENT_LOG_CLEAR_CNT     = 15            #Number of recds to display when clearing event log
EVLOG_RECDS_PER_DEVICE_ZONE   = 500           #Used to calculate the max recds to store
ICLOUD3_ERROR_MSG       = "ICLOUD3 ERROR-SEE EVENT LOG"

#Devicename config parameter file extraction
DI_DEVICENAME           = 0
DI_DEVICE_TYPE          = 1
DI_NAME                 = 2
DI_EMAIL                = 3
DI_BADGE_PICTURE        = 4
DI_IOSAPP_ENTITY        = 5
DI_IOSAPP_SUFFIX        = 6
DI_ZONES                = 7

#Waze status codes
WAZE_REGIONS      = ['US', 'NA', 'EU', 'IL', 'AU']
WAZE_USED         = 0
WAZE_NOT_USED     = 1
WAZE_PAUSED       = 2
WAZE_OUT_OF_RANGE = 3
WAZE_NO_DATA      = 4

#Interval range table used for setting the interval based on a retry count
#The key is starting retry count range, the value is the interval (in minutes)
#poor_location_gps cnt, icloud_authentication cnt (default)
OLD_LOC_POOR_GPS_CNT   = 1.1
AUTH_ERROR_CNT         = 1.2
RETRY_INTERVAL_RANGE_1 = {4:.25, 4:1, 8:5, 12:30, 16:60, 20:120, 22:240, 24:-240}
#request iosapp location retry cnt
IOSAPP_REQUEST_LOC_CNT = 2.1
RETRY_INTERVAL_RANGE_2 = {4:.5, 4:2, 8:30, 12:60, 14:120, 16:180, 18:240, 20:-240}

#Used by the 'update_method' in the polling_5_sec loop
IOSAPP_UPDATE     = "IOSAPP"
ICLOUD_UPDATE     = "ICLOUD"

#The event_log lovelace card will display the event in a special color if
#the text starts with a special character:
#^1^ - LightSeaGreen
#^2^ - BlueViolet
#^3^ - OrangeRed
#^4^ - DeepPink
#^5^ - MediumVioletRed
#^6^ - --dark-primary-color
EVLOG_TIME_RECD   = '^t^'       # iosState, ic3Zone, interval, travel time, distance event
EVLOG_INIT_HDR    = '^i^'       # iC3 initialization start/complete event
EVLOG_UPDATE_START= '^s^'       # update start-to-complete highlight and edge bar block
EVLOG_UPDATE_END  = '^c^'       # update start-to-complete highlight and edge bar block
EVLOG_NOTICE      = '^2^'
EVLOG_ERROR       = '^5^'
EVLOG_ALERT       = '^5^'
EVLOG_TRACE       = '^6^'
EVLOG_DEBUG       = '^6^'

#Symbols = ▪•●▬⊗⊘✓×ø¦ ▶◀ ►◄▲▼ ∙▪ »« oPhone=►▶→⟾➤➟➜➔➤🡆🡪🡺⟹🡆➔ᐅ
# — – ⁃ » ━▶━➤🡺 —> > > ❯↦ … 🡪ᗕ ᗒ ᐳ ─🡢 ──ᗒ 🡢 ─ᐅ ↣ ➙ →
CRLF              = 'CRLF'
CRLF_DOT          = 'CRLF•'
# CRLF_DOT          = 'CRLF ▪ '
CRLF_CHK          = 'CRLF✓'
CRLF_X            = 'CRLF⊗ '
CHECK_MARK        = '✓ '
CIRCLE_X          = '⊗ '
NBSP2             = 'NBSP2'
NBSP4             = 'NBSP4'
NBSP6             = 'NBSP6'
DOT               = '• '
DOT2              = '•'
HDOT              = '◦ '
HDOT2             = '◦'
# DOT               = 'DOT'
RARROW            = ' → '       #U+27F6 (Long Arrow Right)  ⟹ ⟾
RARROW2           = '→'       #U+27F6 (Long Arrow Right)  ⟹ ⟾
LARROW            = ' <-- '       #U+27F5 (Long Arrow Left) ⟸ ⟽
LARROW2           = '<--'       #U+27F5 (Long Arrow Left) ⟸ ⟽
# RARROW            = ' 🡪 '       #U+27F6 (Long Arrow Right)  ⟹ ⟾
# RARROW2           = '🡪'       #U+27F6 (Long Arrow Right)  ⟹ ⟾
# LARROW            = ' ⟵ '       #U+27F5 (Long Arrow Left) ⟸ ⟽
# LARROW2           = '⟵'       #U+27F5 (Long Arrow Left) ⟸ ⟽
INFO_SEPARATOR    = '/' #'∻'
CRLF_NBSP6_DOT    = f"{CRLF}{NBSP6}{HDOT}"

#tracking_method config parameter being used
ICLOUD            = 'icloud'    #iCloud Location Services (FmF & FamShr)
ICLOUD_FNAME      = 'iCloud'
FMF               = 'fmf'       #Find My Friends
FAMSHR            = 'famshr'    #Family Sharing
IOSAPP            = 'iosapp'    #HA IOS App v1.5x or v2.x
IOSAPP_FNAME      = 'iOSApp'
NO_IOSAPP         = 'no_iosapp'
FMF_FNAME         = 'FmF'
FAMSHR_FNAME      = 'FamShr'
FAMSHR_FMF        = 'famshr_fmf'
FAMSHR_FMF_FNAME  = 'FamShr-FmF'
TRACKING_METHOD_FNAME = {FMF: FMF_FNAME, FAMSHR: FAMSHR_FNAME, FAMSHR_FMF: FAMSHR_FMF_FNAME,
                        IOSAPP: IOSAPP_FNAME, ICLOUD: ICLOUD_FNAME}

# Device tracking modes
NORMAL            = 'normal'
MONITOR           = 'monitor'
INACTIVE          = 'inactive'

#Zone field names
NAME              = 'name'
FNAME             = 'fname'
TITLE             = 'title'
RADIUS            = 'radius'
NON_ZONE_ITEM_LIST = {
        NOT_HOME: AWAY,
        NOT_SET: NOT_SET_FNAME,
        NEAR_ZONE: NEAR_ZONE_FNAME,
        STATIONARY: STATIONARY_FNAME, }

#config_ic3.yaml parameter validation items
LIST = 1
TIME = 2
NUMBER = 3
TRUE_FALSE = 4
VALID_TIME_TYPES = ['sec', 'secs', 'min', 'mins', 'hr', 'hrs']

TRK_METHOD_SHORT_NAME = {
        FMF: FMF_FNAME,
        FAMSHR: FAMSHR_FNAME,
        IOSAPP: IOSAPP_FNAME, }
DEVICE_TYPE_FNAME = {
        IPHONE: IPHONE_FNAME,
        'phone': IPHONE_FNAME,
        IPAD: IPAD_FNAME,
        WATCH: WATCH_FNAME,
        AIRPODS: AIRPODS_FNAME,
        IPOD: IPOD_FNAME, }

#iOS App Triggers defined in /iOS/Shared/Location/LocatioTrigger.swift
BACKGROUND_FETCH          = 'Background Fetch'
BKGND_FETCH               = 'Bkgnd Fetch'
GEOGRAPHIC_REGION_ENTERED = 'Geographic Region Entered'
GEOGRAPHIC_REGION_EXITED  = 'Geographic Region Exited'
IBEACON_REGION_ENTERED    = 'iBeacon Region Entered'
IBEACON_REGION_EXITED     = 'iBeacon Region Exited'
REGION_ENTERED            = 'Region Entered'
REGION_EXITED             = 'Region Exited'
ENTER_ZONE                = 'Enter Zone'
EXIT_ZONE                 = 'Exit Zone'
INITIAL                   = 'Initial'
MANUAL                    = 'Manual'
LAUNCH                    = "Launch",
SIGNIFICANT_LOC_CHANGE    = 'Significant Location Change'
SIGNIFICANT_LOC_UPDATE    = 'Significant Location Update'
SIG_LOC_CHANGE            = 'Sig Loc Change'
PUSH_NOTIFICATION         = 'Push Notification'
REQUEST_IOSAPP_LOC        = 'Request iOSApp Loc'
IOSAPP_LOC_CHANGE         = 'iOSApp Loc Change'
SIGNALED                  = 'Signaled'

#Trigger is converted to abbreviation after getting last_update_trigger
IOS_TRIGGER_ABBREVIATIONS = {
        GEOGRAPHIC_REGION_ENTERED: ENTER_ZONE,
        GEOGRAPHIC_REGION_EXITED: EXIT_ZONE,
        IBEACON_REGION_ENTERED: ENTER_ZONE,
        IBEACON_REGION_EXITED: EXIT_ZONE,
        SIGNIFICANT_LOC_CHANGE: SIG_LOC_CHANGE,
        SIGNIFICANT_LOC_UPDATE: SIG_LOC_CHANGE,
        PUSH_NOTIFICATION: REQUEST_IOSAPP_LOC,
        BACKGROUND_FETCH: BKGND_FETCH,
        }
IOS_TRIGGERS_VERIFY_LOCATION = [
        INITIAL,
        LAUNCH,
        SIGNALED,
        MANUAL,
        IOSAPP_LOC_CHANGE,
        BKGND_FETCH,
        SIG_LOC_CHANGE,
        REQUEST_IOSAPP_LOC,
        ]
IOS_TRIGGERS_ENTER      = [ENTER_ZONE, ]
IOS_TRIGGERS_EXIT       = [EXIT_ZONE, ]
IOS_TRIGGERS_ENTER_EXIT = [ENTER_ZONE, EXIT_ZONE, ]

#Convert state non-fname value to internal zone/state value
STATE_TO_ZONE_BASE = {
        NOT_SET_FNAME: NOT_SET,
        AWAY: NOT_HOME,
        "away": NOT_HOME,
        NOT_HOME_FNAME: NOT_HOME,
        "nothome": NOT_HOME,
        STATIONARY_FNAME: STATIONARY,
        STATIONARY: STATIONARY,
        "NearZone": "nearzone",
        NEAR_ZONE: NEAR_ZONE,
        }

#Lists to hold the group names, group objects and iCloud device configuration
#The ICLOUD3_GROUPS is filled in on each platform load, the GROUP_OBJS is
#filled in after the polling timer is setup.
ICLOUD3_GROUPS     = []
ICLOUD3_GROUP_OBJS = {}
ICLOUD3_TRACKED_DEVICES = {}

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#       CONFIGURATION FILE AND ENTITY ATTRIBUTE CONSTANTS
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
CONF_ENTITY_REGISTRY_FILE       = 'entity_registry_file_name'
CONFIG_IC3                      = 'config_ic3'

CONF_USERNAME                   = 'username'
CONF_PASSWORD                   = 'password'
CONF_ACCOUNT_NAME               = 'account_name'
CONF_GROUP                      = 'group'
CONF_FNAME                       = 'fname'
CONF_TRACKING_METHOD            = 'tracking_method'
CONF_IOSAPP_REQUEST_LOC_MAX_CNT = 'iosapp_request_loc_max_cnt'
CONF_TRACK_DEVICES              = 'track_devices'
CONF_DEVICES                    = 'devices'
CONF_UNIT_OF_MEASUREMENT        = 'unit_of_measurement'
CONF_TIME_FORMAT                = 'time_format'
CONF_INTERVAL                   = 'interval'
CONF_BASE_ZONE                  = 'base_zone'
CONF_INZONE_INTERVAL            = 'inzone_interval'
CONF_INZONE_INTERVALS           = 'inzone_intervals'
CONF_DISPLAY_ZONE_FORMAT        = 'display_zone_format'
CONF_CENTER_IN_ZONE             = 'center_in_zone'

CONF_STAT_ZONE_STILL_TIME      = 'stat_zone_still_time'
CONF_STAT_ZONE_INZONE_INTERVAL = 'stat_zone_inzone_interval'
# CONF_STATIONARY_ZONE_OFFSET     = 'stat_zone_zone_offset'

CONF_MAX_INTERVAL               = 'max_interval'
CONF_TRAVEL_TIME_FACTOR         = 'travel_time_factor'
CONF_GPS_ACCURACY_THRESHOLD     = 'gps_accuracy_threshold'
CONF_OLD_LOCATION_THRESHOLD     = 'old_location_threshold'
CONF_IGNORE_GPS_ACC_INZONE      = 'ignore_gps_accuracy_inzone'
CONF_DISCARD_POOR_GPS_INZONE    = 'discard_poor_gps_inzone'
CONF_HIDE_GPS_COORDINATES       = 'hide_gps_coordinates'

CONF_WAZE_REGION                = 'waze_region'
CONF_WAZE_MAX_DISTANCE          = 'waze_max_distance'
CONF_WAZE_MIN_DISTANCE          = 'waze_min_distance'
CONF_WAZE_REALTIME              = 'waze_realtime'
CONF_WAZE_HISTORY_DATABASE_USED = 'waze_history_database_used'
CONF_WAZE_HISTORY_MAX_DISTANCE  = 'waze_history_max_distance'
CONF_WAZE_HISTORY_TRACK_DIRECTION = 'waze_history_track_direction'
# CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION = 'waze_history_track_direction'
CONF_DISTANCE_METHOD            = 'distance_method'

CONF_COMMAND                    = 'command'
CONF_CREATE_SENSORS             = 'create_sensors'
CONF_EXCLUDE_SENSORS            = 'exclude_sensors'
CONF_ENTITY_REGISTRY_FILE       = 'entity_registry_file_name'
CONF_LOG_LEVEL                  = 'log_level'
CONF_CONFIG_IC3_FILE_NAME       = 'config_ic3_file_name'
CONF_LEGACY_MODE                = 'legacy_mode'
CONF_DISPLAY_TEXT_AS            = 'display_text_as'
CONF_TEST_PARAMETER             = 'test_parameter'
CONF_ZONE                       = 'zone'



DEFAULT_USERNAME                         = ''
DEFAULT_PASSWORD                         = ''
DEFAULT_DEVICES                          = []
DEFAULT_TRACK_DEVICES                    = []
DEFAULT_DATA_SOURCE                      = 'icloud,iosapp'

DEFAULT_ENTITY_REGISTRY_FILE             = ''
DEFAULT_EVENT_LOG_CARD_DIRECTORY         = 'www/custom_cards'
DEFAULT_EVENT_LOG_CARD_PROGRAM           = 'icloud3_event_log_card'
DEFAULT_CREATE_SENSORS                   = []
DEFAULT_EXCLUDE_SENSORS                  = []

DEFAULT_UNIT_OF_MEASUREMENT              = 'mi'
DEFAULT_DISPLAY_TEXT_AS                  = []
DEFAULT_TIME_FORMAT                      = 12
DEFAULT_DISTANCE_METHOD                  = 'waze'
DEFAULT_INZONE_INTERVAL                  = '02:00:00',
DEFAULT_INZONE_INTERVAL_SECS             = 120
DEFAULT_INZONE_INTERVALS                 = []
DEFAULT_DISPLAY_ZONE_FORMAT              = 'name'
DEFAULT_CENTER_IN_ZONE                   = False
DEFAULT_MAX_INTERVAL                     = '04:00:00',
DEFAULT_MAX_INTERVAL_SECS                = 240
DEFAULT_TRAVEL_TIME_FACTOR               = .60
DEFAULT_GPS_ACCURACY_THRESHOLD           = 100
DEFAULT_OLD_LOCATION_THRESHOLD           = '00:02:00',
DEFAULT_IGNORE_GPS_ACC_INZONE            = ''
DEFAULT_DISCARD_POOR_GPS_INZONE          = True
DEFAULT_CHECK_GPS_ACC_INZONE             = True
DEFAULT_HIDE_GPS_COORDINATES             = False

DEFAULT_WAZE_REGION                      = 'US'
DEFAULT_WAZE_MAX_DISTANCE                = 1000
DEFAULT_WAZE_MIN_DISTANCE                = 1
DEFAULT_WAZE_REALTIME                    = False
DEFAULT_WAZE_HISTORY_DATABASE_USED              = True
DEFAULT_WAZE_HISTORY_MAX_DISTANCE        = 20
DEFAULT_WAZE_HISTORY_TRACK_DIRECTION = 'north-south'

DEFAULT_STATIONARY_STILL_TIME            = '00:08:00',
DEFAULT_STAT_ZONE_STILL_TIME_SECS       = 480
DEFAULT_STAT_BASE_OFFSET_LATITUDE        = 1
DEFAULT_STAT_BASE_OFFSET_LONGITUDE       = 0
DEFAULT_STATIONARY_INZONE_INTERVAL       = '00:30:00',
DEFAULT_STAT_ZONE_INZONE_INTERVAL_SECS  = 180
DEFAULT_STATIONARY_ZONE_OFFSET = "1,0"

DEFAULT_LOG_LEVEL                        = ''
DEFAULT_IOSAPP_REQUEST_LOC_MAX_CNT       = HIGH_INTEGER
DEFAULT_LEGACY_MODE                      = False
DEFAULT_COMMAND = ''

DEFAULT_CONFIG_VALUES = {
    CONF_UNIT_OF_MEASUREMENT: DEFAULT_UNIT_OF_MEASUREMENT,
    CONF_TIME_FORMAT: DEFAULT_TIME_FORMAT,
    CONF_INZONE_INTERVAL: DEFAULT_INZONE_INTERVAL,
    CONF_INZONE_INTERVALS : DEFAULT_INZONE_INTERVALS,
    CONF_DISPLAY_ZONE_FORMAT: DEFAULT_DISPLAY_ZONE_FORMAT,
    CONF_CENTER_IN_ZONE: DEFAULT_CENTER_IN_ZONE,
    CONF_MAX_INTERVAL: DEFAULT_MAX_INTERVAL,
    CONF_TRAVEL_TIME_FACTOR: DEFAULT_TRAVEL_TIME_FACTOR,
    CONF_GPS_ACCURACY_THRESHOLD: DEFAULT_GPS_ACCURACY_THRESHOLD,
    CONF_OLD_LOCATION_THRESHOLD: DEFAULT_OLD_LOCATION_THRESHOLD,
    CONF_DISCARD_POOR_GPS_INZONE: DEFAULT_DISCARD_POOR_GPS_INZONE,
    CONF_IGNORE_GPS_ACC_INZONE: DEFAULT_IGNORE_GPS_ACC_INZONE,
    CONF_HIDE_GPS_COORDINATES: DEFAULT_HIDE_GPS_COORDINATES,
    CONF_TRACK_DEVICES: DEFAULT_TRACK_DEVICES,
    CONF_DEVICES: DEFAULT_DEVICES,
    CONF_DISTANCE_METHOD: DEFAULT_DISTANCE_METHOD,
    CONF_LEGACY_MODE: DEFAULT_LEGACY_MODE,
    CONF_WAZE_REGION: DEFAULT_WAZE_REGION,
    CONF_WAZE_MAX_DISTANCE: DEFAULT_WAZE_MAX_DISTANCE,
    CONF_WAZE_MIN_DISTANCE: DEFAULT_WAZE_MIN_DISTANCE,
    CONF_WAZE_REALTIME: DEFAULT_WAZE_REALTIME,
    CONF_WAZE_HISTORY_DATABASE_USED: DEFAULT_WAZE_HISTORY_DATABASE_USED,
    CONF_WAZE_HISTORY_MAX_DISTANCE: DEFAULT_WAZE_HISTORY_MAX_DISTANCE,
    CONF_WAZE_HISTORY_TRACK_DIRECTION: DEFAULT_WAZE_HISTORY_TRACK_DIRECTION,
    CONF_STAT_ZONE_STILL_TIME: DEFAULT_STATIONARY_STILL_TIME,
    CONF_STAT_ZONE_INZONE_INTERVAL: DEFAULT_STATIONARY_INZONE_INTERVAL,

    CONF_LOG_LEVEL: '',
    CONF_DISPLAY_TEXT_AS: [],
    }


VALIDATE_PARAMETER_LIST = {
    CONF_UNIT_OF_MEASUREMENT: ['mi', 'km'],
    CONF_TIME_FORMAT: [12, 24],
    CONF_DISPLAY_ZONE_FORMAT: ['zone', 'name', 'fname', 'title'],
    CONF_DISTANCE_METHOD: ['waze', 'calc'],
    CONF_WAZE_REGION: ['US', 'NA', 'EU', 'IS', 'AU', 'us', 'na', 'eu', 'is', 'au'],
    CONF_DISPLAY_ZONE_FORMAT: ['zone', 'name', 'fname', 'title'],
    CONF_WAZE_HISTORY_TRACK_DIRECTION: ['north-south', 'east-west', 'north_south', 'east_west']
}
VALIDATE_PARAMETER_TRUE_FALSE = [
    CONF_CENTER_IN_ZONE,
    CONF_DISCARD_POOR_GPS_INZONE,
    CONF_HIDE_GPS_COORDINATES,
    CONF_WAZE_HISTORY_DATABASE_USED,
    CONF_WAZE_REALTIME,
    CONF_LEGACY_MODE,
]
VALIDATE_PARAMETER_NUMBER = [
    CONF_TRAVEL_TIME_FACTOR,
    CONF_GPS_ACCURACY_THRESHOLD,
    CONF_WAZE_MAX_DISTANCE,
    CONF_WAZE_MIN_DISTANCE,
]
VALIDATE_PARAMETER_TIME = [
    CONF_INZONE_INTERVAL,
    CONF_MAX_INTERVAL,
    CONF_STAT_ZONE_STILL_TIME,
    CONF_STAT_ZONE_INZONE_INTERVAL,
    CONF_OLD_LOCATION_THRESHOLD,
]


# entity attributes (iCloud FmF & FamShr)
ICLOUD_TIMESTAMP           = 'timeStamp'
ICLOUD_HORIZONTAL_ACCURACY = 'horizontalAccuracy'
ICLOUD_VERTICAL_ACCURACY   = 'verticalAccuracy'
ICLOUD_BATTERY_STATUS      = 'batteryStatus'
ICLOUD_BATTERY_LEVEL       = 'batteryLevel'
ICLOUD_DEVICE_CLASS        = 'deviceClass'
ICLOUD_DEVICE_STATUS       = 'deviceStatus'
ICLOUD_LOW_POWER_MODE      = 'lowPowerMode'
ID                         = 'id'

# device data attributes
DEVTRK_STATE_VALUE         = 'location_name'
LOCATION                   = 'location'
ATTRIBUTES                 = 'attributes'
RADIUS                     = 'radius'
NAME                       = 'name'
FRIENDLY_NAME              = 'friendly_name'
LATITUDE                   = 'latitude'
LONGITUDE                  = 'longitude'
DEVICE_CLASS               = 'device_class'
DEVICE_ID                  = 'device_id'
PASSIVE                    = 'passive'

# entity attributes
LOCATION_SOURCE            = 'location_source'
ZONE                       = 'zone'
ZONE_DATETIME              = 'zone_timestamp'
INTO_ZONE_DATETIME         = 'into_zone'
LAST_ZONE                  = 'last_zone'
FROM_ZONE                  = 'from_zone'
GROUP                      = 'group'
TIMESTAMP                  = 'timestamp'
TIMESTAMP_SECS             = 'timestamp_secs'
TIMESTAMP_TIME             = 'timestamp_time'
LOCATION_TIME              = 'location_time'
TRACKING_METHOD            = 'tracking_method'
DATA_SOURCE                = 'data_source'
DATETIME                   = 'date_time'
AGE                        = 'age'
TRIGGER                    = 'trigger'
BATTERY                    = 'battery'
BATTERY_LEVEL              = 'battery_level'
BATTERY_STATUS             = 'battery_status'
INTERVAL                   = 'interval'
ZONE_DISTANCE              = 'zone_distance'
CALC_DISTANCE              = 'calc_distance'
WAZE_DISTANCE              = 'waze_distance'
TRAVEL_TIME                = 'travel_time'
TRAVEL_TIME_MIN            = 'travel_time_min'
DIR_OF_TRAVEL              = 'dir_of_travel'
TRAVEL_DISTANCE            = 'travel_distance'
DEVICE_STATUS              = 'device_status'
LOW_POWER_MODE             = 'low_power_mode'
TRACKING                   = 'tracking'
DEVICENAME_IOSAPP          = 'iosapp_device'
AUTHENTICATED              = 'authenticated'

LAST_UPDATE                = 'last_update'
LAST_UPDATE_TIME           = 'last_update_time'
LAST_UPDATE_DATETIME       = 'last_update_date/time'
NEXT_UPDATE                = 'next_update'
NEXT_UPDATE_TIME           = 'next_update_time'
NEXT_UPDATE_DATETIME       = 'next_update_date/time'
LAST_LOCATED               = 'last_located'
LAST_LOCATED_TIME          = 'last_located_time'
LAST_LOCATED_DATETIME      = 'last_locate_date/time'

INFO                       = 'info'
GPS_ACCURACY               = 'gps_accuracy'
GPS                        = 'gps'
POLL_COUNT                 = 'poll_count'
ICLOUD3_VERSION            = 'icloud3_version'
VERT_ACCURACY              = 'vertical_accuracy'
ALTITUDE                   = 'altitude'
BADGE                      = 'badge'
EVENT_LOG                  = 'event_log'
PICTURE                    = 'entity_picture'
ICON                       = 'icon'

DEVICE_ATTRS_BASE = {
         LATITUDE: 0,
         LONGITUDE: 0,
         BATTERY: 0,
         BATTERY_LEVEL: 0,
         BATTERY_STATUS: '',
         GPS_ACCURACY: 0,
         VERT_ACCURACY: 0,
         TIMESTAMP: DATETIME_ZERO,
         ICLOUD_TIMESTAMP: HHMMSS_ZERO,
         TRIGGER: '',
         DEVICE_STATUS: UNKNOWN,
         LOW_POWER_MODE: '',
         }

INITIAL_LOCATION_DATA  = {
        NAME: '',
        DEVICE_CLASS: 'iPhone',
        BATTERY_LEVEL: 0,
        BATTERY_STATUS: UNKNOWN,
        DEVICE_STATUS: UNKNOWN,
        LOW_POWER_MODE: False,
        TIMESTAMP_SECS: 0,
        TIMESTAMP_TIME: HHMMSS_ZERO,
        AGE: HIGH_INTEGER,
        LATITUDE: 0.0,
        LONGITUDE: 0.0,
        ALTITUDE: 0.0,
        GPS_ACCURACY: 0,
        VERT_ACCURACY: 0,
        }
        #ISOLD: False,

TRACE_ATTRS_BASE = {
        NAME: '',
        ZONE: '',
        LAST_ZONE: '',
        INTO_ZONE_DATETIME: '',
        LATITUDE: 0,
        LONGITUDE: 0,
        TRIGGER: '',
        TIMESTAMP: DATETIME_ZERO,
        ZONE_DISTANCE: 0,
        INTERVAL: 0,
        DIR_OF_TRAVEL: '',
        TRAVEL_DISTANCE: 0,
        WAZE_DISTANCE: '',
        CALC_DISTANCE: 0,
        LAST_LOCATED_DATETIME: '',
        LAST_UPDATE_TIME: '',
        NEXT_UPDATE_TIME: '',
        POLL_COUNT: '',
        INFO: '',
        BATTERY: 0,
        BATTERY_LEVEL: 0,
        GPS: 0,
        GPS_ACCURACY: 0,
        VERT_ACCURACY: 0,
        }

TRACE_ICLOUD_ATTRS_BASE = {
        'name': '',
        ICLOUD_DEVICE_STATUS: '',
        LATITUDE: 0,
        LONGITUDE: 0,
        ICLOUD_TIMESTAMP: 0,
        ICLOUD_HORIZONTAL_ACCURACY: 0,
        ICLOUD_VERTICAL_ACCURACY: 0,
        'positionType': 'Wifi',
        }
        #ISOLD: False,


DEVICE_STATUS_SET = [
        ICLOUD_DEVICE_CLASS,
        ICLOUD_BATTERY_STATUS,
        ICLOUD_LOW_POWER_MODE,
        LOCATION
        ]
DEVICE_STATUS_CODES = {
        '200': 'Online',
        '201': 'Offline',
        '203': 'Pending',
        '204': 'Unregistered',
        '0': ''
        }
DEVICE_STATUS_ONLINE = ['Online', 'Pending', UNKNOWN, 'unknown', '']

FMF_FAMSHR_LOCATION_FIELDS = [
        ALTITUDE,
        LATITUDE,
        LONGITUDE,
        TIMESTAMP,
        ICLOUD_HORIZONTAL_ACCURACY,
        ICLOUD_VERTICAL_ACCURACY,
        ICLOUD_BATTERY_STATUS, ]

LOG_RAWDATA_FIELDS = [
        LATITUDE,  LONGITUDE, LOCATION_SOURCE, TRACKING_METHOD, DATA_SOURCE,
        ZONE, ZONE_DATETIME, INTO_ZONE_DATETIME, LAST_ZONE,
        TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
        TRIGGER, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
        INTERVAL, ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
        TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, TRAVEL_DISTANCE,
        DEVICE_STATUS, LOW_POWER_MODE,
        TRACKING, DEVICENAME_IOSAPP,
        AUTHENTICATED,
        LAST_UPDATE_TIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_TIME, LAST_LOCATED_DATETIME,
        INFO, GPS_ACCURACY, GPS, POLL_COUNT, VERT_ACCURACY, ALTITUDE,
        ICLOUD3_VERSION,
        BADGE,
        DEVICE_ID, ID,
        ICLOUD_HORIZONTAL_ACCURACY, ICLOUD_VERTICAL_ACCURACY,
        ICLOUD_BATTERY_LEVEL, ICLOUD_BATTERY_STATUS,
        ICLOUD_DEVICE_CLASS, ICLOUD_DEVICE_STATUS, ICLOUD_LOW_POWER_MODE, ICLOUD_TIMESTAMP,
        NAME, 'emails', 'firstName', 'laststName',
        'prsId', 'batteryLevel', 'isOld', 'isInaccurate', 'phones',
        'invitationAcceptedByEmail', 'invitationFromEmail', 'invitationSentToEmail', 'data',
        ]


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           CONFIG_FLOW CONSTANTS - CONFIGURATION PARAMETERS IN .storage/icloud.configuration FILE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# to store the cookie
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

# Platform
CONF_VERSION                    = 'version'
CONF_UPDATE_DATE                = 'config_update_date'
CONF_EVENT_LOG_CARD_DIRECTORY   = 'event_log_card_directory'
CONF_EVENT_LOG_CARD_PROGRAM     = 'event_log_card_program'

# Account, Devices, Tracking Parameters
CONF_USERNAME                   = 'username'
CONF_PASSWORD                   = 'password'
CONF_DEVICES                    = 'devices'
CONF_TRACKING_METHOD            = 'tracking_method'
CONF_DATA_SOURCE                = 'data_source'
CONF_VERIFICATION_CODE          = 'verification_code'

#devices_schema parameters
CONF_DEVICENAME                 = 'device_name'
CONF_TRACK_FROM_ZONES           = 'track_from_zones'
CONF_TRACK_FROM_ZONE            = 'track_from_zone'
CONF_IOSAPP_SUFFIX              = 'iosapp_suffix'
CONF_IOSAPP_ENTITY              = 'iosapp_entity'
CONF_NOIOSAPP                   = 'noiosapp'
CONF_NO_IOSAPP                  = 'no_iosapp'
CONF_IOSAPP_INSTALLED           = 'iosapp_installed'
CONF_PICTURE                    = 'picture'
CONF_EMAIL                      = 'email'
CONF_CONFIG                     = 'config'
CONF_SOURCE                     = 'source'
CONF_DEVICE_TYPE                = 'device_type'


# General Parameters
CONF_UNIT_OF_MEASUREMENT        = 'unit_of_measurement'
CONF_TIME_FORMAT                = 'time_format'
CONF_MAX_INTERVAL               = 'max_interval'
CONF_GPS_ACCURACY_THRESHOLD     = 'gps_accuracy_threshold'
CONF_OLD_LOCATION_THRESHOLD     = 'old_location_threshold'
CONF_TRAVEL_TIME_FACTOR         = 'travel_time_factor'
CONF_LOG_LEVEL                  = 'log_level'

# inZone Parameters
CONF_DISPLAY_ZONE_FORMAT        = 'display_zone_format'
CONF_CENTER_IN_ZONE             = 'center_in_zone'
CONF_DISCARD_POOR_GPS_INZONE    = 'discard_poor_gps_inzone'
CONF_INZONE_INTERVALS           = 'inzone_intervals'

# Waze Parameters
CONF_DISTANCE_METHOD            = 'distance_method'
CONF_WAZE_REGION                = 'waze_region'
CONF_WAZE_MAX_DISTANCE          = 'waze_max_distance'
CONF_WAZE_MIN_DISTANCE          = 'waze_min_distance'
CONF_WAZE_REALTIME              = 'waze_realtime'
CONF_WAZE_HISTORY_DATABASE_USED = 'waze_history_database_used'
CONF_WAZE_HISTORY_MAX_DISTANCE  = 'waze_history_max_distance'
CONF_WAZE_HISTORY_TRACK_DIRECTION= 'waze_history_track_direction'

# Stationary Zone Parameters
CONF_STAT_ZONE_FNAME            = 'stat_zone_fname'
CONF_STAT_ZONE_STILL_TIME       = 'stat_zone_still_time'
CONF_STAT_ZONE_INZONE_INTERVAL  = 'stat_zone_inzone_interval'
CONF_STAT_ZONE_BASE_LATITUDE    = 'stat_zone_base_latitude'
CONF_STAT_ZONE_BASE_LONGITUDE   = 'stat_zone_base_longitude'
CONF_SENSORS                    = 'sensors'

# Display Text As Parameter
CONF_DISPLAY_TEXT_AS            = 'display_text_as'

#devices_schema parameters
CONF_IC3_DEVICENAME             = 'ic3_devicename'
CONF_FNAME                      = 'fname'
CONF_FAMSHR_DEVICENAME          = 'famshr_devicename'
CONF_FAMSHR_DEVICENAME2         = 'famshr_devicename2'
CONF_FAMSHR_DEVICE_ID           = 'famshr_device_id'
CONF_FMF_EMAIL                  = 'fmf_email'
CONF_FMF_DEVICE_ID              = 'fmf_device_id'
CONF_IOSAPP_DEVICE              = 'iosapp_device'
CONF_PICTURE                    = 'picture'
CONF_TRACKING_MODE              = 'tracking_mode'
CONF_TRACK_FROM_ZONES           = 'track_from_zones'
CONF_TRACKING_METHOD            = 'tracking_method'
CONF_DEVICE_TYPE                = 'device_type'
CONF_INZONE_INTERVAL            = 'inzone_interval'
CONF_UNIQUE_ID                  = 'unique_id'

CONF_ZONE                       = 'zone'
CONF_COMMAND                    = 'command'
CONF_NAME                       = 'name'
CONF_IOSAPP_REQUEST_LOC_MAX_CNT = 'iosapp_request_loc_max_cnt'
CONF_INTERVAL                   = 'interval'

#TODO Delete this after config_flow
#-----►►Test configuration parameters ----------
VALID_CONF_DEVICES_ITEMS = [
        CONF_DEVICENAME, CONF_EMAIL, CONF_PICTURE, CONF_NAME,
        CONF_INZONE_INTERVAL, CONF_TRACK_FROM_ZONES, CONF_IOSAPP_SUFFIX,
        CONF_IOSAPP_ENTITY, CONF_IOSAPP_INSTALLED, CONF_NO_IOSAPP,
        CONF_NO_IOSAPP, CONF_TRACKING_METHOD, ]

DASH_20  = '━'*20
OPT_NONE = 0

#------------------
CONF_SENSORS_CONTROL             = 'control'
ICLOUD3_EVENT_LOG    = 'icloud3_event_log'
DEVTRKR_ONLY_MONITOR = 'devtrkr_only_monitored_devices'

CONF_SENSORS_DEVICE        = 'device'
NAME           = "name"
BADGE          = "badge"
BATTERY        = "battery"
BATTERY_STATUS = "battery_status"
INFO           = "info"

CONF_SENSORS_TRACKING_UPDATE = 'tracking_update'
INTERVAL         = "interval"
LAST_LOCATED     = "last_located"
LAST_UPDATE      = "last_update"
NEXT_UPDATE      = "next_update"

CONF_SENSORS_TRACKING_TIME  = 'tracking_time'
TRAVEL_TIME     = "travel_time"
TRAVEL_TIME_MIN = "travel_time_min"

CONF_SENSORS_TRACKING_DISTANCE = 'tracking_distance'
ZONE_DISTANCE      = "zone_distance"
HOME_DISTANCE      = "home_distance"
DIR_OF_TRAVEL      = "dir_of_travel"
TRAVEL_DISTANCE    = "travel_distance"

CONF_SENSORS_TRACK_FROM_ZONES = 'track_from_zones'
TFZ_ZONEINFO        = 'tfz_zoneinfo'
TFZ_DISTANCE        = 'tfz_distance'
TFZ_TRAVEL_TIME     = 'tfz_travel_time'
TFZ_TRAVEL_TIME_MIN = 'tfz_travel_time_min'
TFZ_DIR_OF_TRAVEL   = 'tfz_dir_of_travel'

CONF_SENSORS_TRACKING_OTHER = 'tracking_other'
TRIGGER         = "trigger"
WAZE_DISTANCE   = "waze_distance"
CALC_DISTANCE   = "calc_distance"

DISTANCE           = 'distance'
CONF_SENSORS_ZONE  = 'zone'
ZONE               = "zone"
ZONE_FNAME         = "zone_fname"
ZONE_NAME          = "zone_name"
# ZONE_DATETIME      = "zone_datetime"
ZONE_DATETIME      = "zone_changed"
LAST_ZONE          = "last_zone"
LAST_ZONE_FNAME    = "last_zone_fname"
LAST_ZONE_NAME     = "last_zone_name"
# LAST_ZONE_DATETIME = "last_zone_datetime"
LAST_ZONE_DATETIME = "last_zone_changed"

CONF_SENSORS_OTHER = 'other'
GPS_ACCURACY      = "gps_accuracy"
ALTITUDE          = "altitude"
VERTICAL_ACCURACY = "vertical_accuracy"

# SENSOR_LIST_DEVICE =    [NAME, BADGE, BATTERY, BATTERY_STATUS,
#                         TRIGGER, INTERVAL, LAST_LOCATED,
#                         INFO,
#                         GPS_ACCURACY, ALTITUDE, VERTICAL_ACCURACY]

# SENSOR_LIST_TRACKING =  [NEXT_UPDATE, LAST_UPDATE, LAST_LOCATED,
#                         TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_DISTANCE, DIR_OF_TRAVEL,
#                         WAZE_DISTANCE, CALC_DISTANCE, ZONE_DISTANCE, HOME_DISTANCE,
#                         ZONE, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME,
#                         LAST_ZONE, LAST_ZONE_FNAME, LAST_ZONE_NAME,]
# SENSOR_LIST_TRACK_FROM_ZONE = [INFO, LAST_UPDATE, NEXT_UPDATE,
#                         TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, ]
# SENSOR_LIST_LOC_UPDATE =[TRIGGER, INTERVAL,
#                         NEXT_UPDATE, LAST_UPDATE, LAST_LOCATED,
#                         TRAVEL_TIME, TRAVEL_TIME_MIN, ]
# SENSOR_LIST_ZONE =      [ZONE_DISTANCE, HOME_DISTANCE,
#                         ZONE, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME,
#                         LAST_ZONE, LAST_ZONE_FNAME, LAST_ZONE_NAME, ]
#--------------------------------------------------------
# '.storage/icloud3.configuration' json file 'data' branch categories
CF_PROFILE       = 'profile'
CF_DATA          = 'data'
CF_DATA_TRACKING = 'tracking'
CF_DATA_DEVICES  = 'devices'
CF_DATA_GENERAL  = 'general'
CF_DATA_SENSORS  = 'sensors'

#--------------------------------------------------------
DEFAULT_PROFILE_CONF = {
        CONF_VERSION: 0,
        CONF_UPDATE_DATE: '',
        CONF_EVENT_LOG_CARD_DIRECTORY: EVENT_LOG_CARD_WWW_DIRECTORY,
        CONF_EVENT_LOG_CARD_PROGRAM: EVENT_LOG_CARD_WWW_JS_PROG,
}

DEFAULT_TRACKING_CONF = {
        CONF_USERNAME: '',
        CONF_PASSWORD: '',
        CONF_DATA_SOURCE: 'icloud,iosapp',
        CONF_DEVICES: [],
}

DEFAULT_DEVICE_CONF = {
        CONF_IC3_DEVICENAME: ' ',
        CONF_FNAME: '',
        CONF_TRACKING_MODE: 'normal',
        CONF_FAMSHR_DEVICENAME: 'None',
        CONF_FAMSHR_DEVICENAME2: 'None',
        CONF_FMF_EMAIL: 'None',
        CONF_IOSAPP_DEVICE: 'Search',
        CONF_TRACK_FROM_ZONES: ['home'],
        CONF_PICTURE: 'None',
        CONF_DEVICE_TYPE: 'iPhone',
        CONF_INZONE_INTERVAL: '02:00:00',
        CONF_UNIQUE_ID: '',
}

DEFAULT_GENERAL_CONF = {
        # General Configuration Parameters
        CONF_UNIT_OF_MEASUREMENT: 'mi',
        CONF_TIME_FORMAT: '12-hour',
        CONF_DISPLAY_ZONE_FORMAT: 'name',
        CONF_MAX_INTERVAL: '04:00:00',
        CONF_GPS_ACCURACY_THRESHOLD: 100,
        CONF_OLD_LOCATION_THRESHOLD: '00:03:00',
        CONF_TRAVEL_TIME_FACTOR: .6,

        # inZone Configuration Parameters
        CONF_CENTER_IN_ZONE: False,
        CONF_DISCARD_POOR_GPS_INZONE: False,
        CONF_INZONE_INTERVALS: {
                IPHONE: '02:00:00',
                IPAD: '02:00:00',
                WATCH: '00:15:00',
                AIRPODS: '00:15:00',
                NO_IOSAPP: '00:15:00',
                OTHER: '02:00:00',
                },

        # Waze Configuration Parameters
        CONF_DISTANCE_METHOD: 'waze',
        CONF_WAZE_REGION: 'us',
        CONF_WAZE_MIN_DISTANCE: 1,
        CONF_WAZE_MAX_DISTANCE: 1000,
        CONF_WAZE_REALTIME: False,
        CONF_WAZE_HISTORY_DATABASE_USED: True,
        CONF_WAZE_HISTORY_MAX_DISTANCE: 20,
        CONF_WAZE_HISTORY_TRACK_DIRECTION: 'north_south',

        # Stationary Zone Configuration Parameters
        CONF_STAT_ZONE_FNAME: 'Stationary',
        CONF_STAT_ZONE_STILL_TIME: '00:08:00',
        CONF_STAT_ZONE_INZONE_INTERVAL: '00:30:00',
        CONF_STAT_ZONE_BASE_LATITUDE: 1,
        CONF_STAT_ZONE_BASE_LONGITUDE: 0,

        CONF_DISPLAY_TEXT_AS: ['#1', '#2', '#3', '#4', '#5', '#6', '#7', '#8', '#9', '#10'],

        # Other Parameters
        CONF_LOG_LEVEL: 'info',
}

# Default Create Sensor Field Parameter
DEFAULT_SENSORS_CONF = {
        CONF_SENSORS_CONTROL: [
                DEVTRKR_ONLY_MONITOR, ],
        CONF_SENSORS_DEVICE: [
                NAME,
                BADGE,
                BATTERY,
                INFO, ],
        CONF_SENSORS_TRACKING_UPDATE: [
                INTERVAL,
                LAST_LOCATED,
                LAST_UPDATE,
                NEXT_UPDATE, ],
        CONF_SENSORS_TRACKING_TIME: [
                TRAVEL_TIME, ],
        CONF_SENSORS_TRACKING_DISTANCE: [
                ZONE_DISTANCE,
                DIR_OF_TRAVEL, ],
        CONF_SENSORS_TRACK_FROM_ZONES: [
                TFZ_ZONEINFO, ],
        CONF_SENSORS_TRACKING_OTHER: [],
        CONF_SENSORS_ZONE:
                [ZONE_NAME],
        CONF_SENSORS_OTHER: [],
}

DEFAULT_DATA_CONF =  {
        CF_DATA_TRACKING: DEFAULT_TRACKING_CONF,
        CF_DATA_GENERAL: DEFAULT_GENERAL_CONF,
        CF_DATA_SENSORS: DEFAULT_SENSORS_CONF,
}

CF_DEFAULT_IC3_CONF_FILE = {
        CF_PROFILE: {
                CONF_VERSION: 0,
                CONF_UPDATE_DATE: '',
                CONF_EVENT_LOG_CARD_DIRECTORY: EVENT_LOG_CARD_WWW_DIRECTORY,
                CONF_EVENT_LOG_CARD_PROGRAM: EVENT_LOG_CARD_WWW_JS_PROG,
        },
        CF_DATA: {
                CF_DATA_TRACKING: DEFAULT_TRACKING_CONF,
                CF_DATA_GENERAL: DEFAULT_GENERAL_CONF,
                CF_DATA_SENSORS: DEFAULT_SENSORS_CONF,
        }
}

CONF_PARAMETER_TIME_STR = [
        CONF_INZONE_INTERVAL,
        CONF_MAX_INTERVAL,
        CONF_STAT_ZONE_STILL_TIME,
        CONF_STAT_ZONE_INZONE_INTERVAL,
        CONF_OLD_LOCATION_THRESHOLD,
        IPHONE,
        IPAD,
        WATCH,
        AIRPODS,
        NO_IOSAPP,
        OTHER,
]

CONF_PARAMETER_FLOAT = [
        CONF_TRAVEL_TIME_FACTOR,
        CONF_STAT_ZONE_BASE_LATITUDE,
        CONF_STAT_ZONE_BASE_LONGITUDE,
]

CONF_ALL_FAMSHR_DEVICES = "all_famshr_devices"
DEFAULT_ALL_FAMSHR_DEVICES = True

# .storage/icloud3.restore_state file used to resore the device_trackers
# and sensors state during start up
RESTORE_STATE_FILE = {
        'profile': {
                CONF_VERSION: 0,
                LAST_UPDATE: DATETIME_ZERO, },
        'devices': {}
}
