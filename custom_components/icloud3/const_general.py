#####################################################################
#
#   Define the iCloud3 General Constants
#
#####################################################################
#Symbols = ▪•●▬⊗⊘✓×ø¦ ▶◀ ►◄▲▼ ∙▪ »« oPhone=►▶

DEBUG_TRACE_CONTROL_FLAG = False

HA_ENTITY_REGISTRY_FILE_NAME    = '/config/.storage/core.entity_registry'
ENTITY_REGISTRY_FILE_KEY        = 'core.entity_registry'
DEFAULT_CONFIG_IC3_FILE_NAME    = '/config/config_ic3.yaml'
CONFIG_IC3                      = 'config_ic3'
ICLOUD_EVENT_LOG_CARD_JS        = 'icloud3-event-log-card.js'
STORAGE_KEY_ICLOUD              = 'icloud'
STORAGE_VERSION                 = 1
STORAGE_DIR                     = ".storage"
STORAGE_KEY_ENTITY_REGISTRY     = 'core.entity_registry'
SENSOR_EVENT_LOG_ENTITY         = 'sensor.icloud3_event_log'

DOMAIN                          = 'device_tracker'
DEVICE_TRACKER                  = 'device_tracker.'
PLATFORM                        = 'platform'
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
AWAY_FROM                       = 'AwayFrom'
AWAY                            = 'Away'
PAUSED                          = 'PAUSED'
PAUSED_CAPS                     = 'PAUSED'
RESUMING                        = 'RESUMING'
RESUMING_CAPS                   = 'RESUMING'
NEVER                           = 'Never'
ERROR                           = 0
VALID_DATA                      = 1
UTC_TIME                        = True
LOCAL_TIME                      = False
NUMERIC                         = True
NEW_LINE                        = '\n'
WAZE                            = 'waze'
CALC                            = 'calc'
DIST                            = 'dist'

IPHONE                          = 'iphone'
IPAD                            = 'ipad'
IPOD                            = 'ipod'
WATCH                           = 'watch'
IPHONE_FNAME                    = 'iPhone'
IPAD_FNAME                      = 'iPad'
IPOD_FNAME                      = 'iPod'
WATCH_FNAME                     = 'Watch'
ICLOUD_FNAME                    = 'iCloud'

APPLE_DEVICE_TYPES = [
        IPHONE, IPAD, IPOD, WATCH, ICLOUD_FNAME,
        IPHONE_FNAME, IPAD_FNAME, IPOD_FNAME, WATCH_FNAME, ICLOUD_FNAME]

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
RETRY_INTERVAL_RANGE_1 = {4:.25, 4:1, 8:5,  12:30, 16:60, 20:120, 22:240, 24:-240}
#request iosapp location retry cnt
IOSAPP_REQUEST_LOC_CNT = 2.1
RETRY_INTERVAL_RANGE_2 = {4:.5,  4:2, 8:30, 12:60, 14:120, 16:180, 18:240, 20:-240}

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
CRLF              = 'CRLF'
CRLF_DOT          = 'CRLF• '
# CRLF_DOT          = 'CRLF ▪ '
CRLF_CHK          = 'CRLF✓ '
CRLF_X            = 'CRLF⊗ '
DOT               = '• '
RARROW            = '→' #'→'
LARROW            = '←'


#tracking_method config parameter being used
ICLOUD            = 'icloud'    #iCloud Location Services (FmF & FamShr)
ICLOUD_FNAME      = 'iCloud'
FMF               = 'fmf'       #Find My Friends
FAMSHR            = 'famshr'    #Family Sharing
IOSAPP            = 'iosapp'    #HA IOS App v1.5x or v2.x
IOSAPP_FNAME      = 'iOSApp'
FMF_FNAME         = 'FmF'
FAMSHR_FNAME      = 'FamShr'
FAMSHR_FMF        = 'famshr_fmf'
FAMSHR_FMF_FNAME  = 'FamShr-FmF'
TRACKING_METHOD_FNAME = {FMF: FMF_FNAME, FAMSHR: FAMSHR_FNAME, FAMSHR_FMF: FAMSHR_FMF_FNAME,
                        IOSAPP: IOSAPP_FNAME, ICLOUD: ICLOUD_FNAME}

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
        IPOD: IPOD_FNAME, }

#iOS App Triggers defined in \iOS/Shared/Location/LocatioTrigger.swift
BACKGROUND_FETCH          = 'Background Fetch'
BKGND_FETCH               = 'Bkgnd Fetch'
GEOGRAPHIC_REGION_ENTERED = 'Geographic Region Entered'
GEOGRAPHIC_REGION_EXITED  = 'Geographic Region Exited'
IBEACON_REGION_ENTERED    = 'iBeacon Region Entered'
IBEACON_REGION_EXITED     = 'iBeacon Region Exited'
REGION_ENTERED            = 'Region Entered'
REGION_EXITED             = 'Region Exited'
INITIAL                   = 'Initial'
MANUAL                    = 'Manual'
LAUNCH                    = "Launch",
SIGNIFICANT_LOC_CHANGE    = 'Significant Location Change'
SIGNIFICANT_LOC_UPDATE    = 'Significant Location Update'
SIG_LOC_CHANGE            = 'Sig Loc Change'
PUSH_NOTIFICATION         = 'Push Notification'
REQUEST_IOSAPP_LOC        = 'Request iOSApp Loc'
IOSAPP_LOC_CHANGE         = "iOSApp Loc Change"

#Trigger is converted to abbreviation after getting last_update_trigger
IOS_TRIGGER_ABBREVIATIONS = {
        GEOGRAPHIC_REGION_ENTERED: REGION_ENTERED,
        GEOGRAPHIC_REGION_EXITED: REGION_EXITED,
        IBEACON_REGION_ENTERED: REGION_ENTERED,
        IBEACON_REGION_EXITED: REGION_EXITED,
        SIGNIFICANT_LOC_CHANGE: SIG_LOC_CHANGE,
        SIGNIFICANT_LOC_UPDATE: SIG_LOC_CHANGE,
        PUSH_NOTIFICATION: REQUEST_IOSAPP_LOC,
        BACKGROUND_FETCH: BKGND_FETCH,
        }
IOS_TRIGGERS_VERIFY_LOCATION = [
        INITIAL,
        LAUNCH,
        MANUAL,
        IOSAPP_LOC_CHANGE,
        BKGND_FETCH,
        SIG_LOC_CHANGE,
        REQUEST_IOSAPP_LOC,
        ]
IOS_TRIGGERS_ENTER = [
        REGION_ENTERED,
        ]
IOS_TRIGGERS_EXIT = [
        REGION_EXITED,
        ]
IOS_TRIGGERS_ENTER_EXIT = [
        REGION_ENTERED,
        REGION_EXITED,
        ]

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
