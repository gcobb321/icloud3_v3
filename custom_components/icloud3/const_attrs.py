from .const_general import(HHMMSS_ZERO, DATETIME_ZERO, HIGH_INTEGER, UNKNOWN)

CONF_USERNAME                   = 'username'
CONF_PASSWORD                   = 'password'
CONF_ACCOUNT_NAME               = 'account_name'
CONF_GROUP                      = 'group'
CONF_NAME                       = 'name'
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
CONF_STATIONARY_STILL_TIME      = 'stationary_still_time'
CONF_STATIONARY_INZONE_INTERVAL = 'stationary_inzone_interval'
CONF_STATIONARY_ZONE_OFFSET     = 'stationary_zone_offset'
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
CONF_WAZE_HISTORY_MAX_DISTANCE  = 'waze_history_max_distance'
CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION= 'waze_history_map_track_direction'
CONF_DISTANCE_METHOD            = 'distance_method'
CONF_COMMAND                    = 'command'
CONF_CREATE_SENSORS             = 'create_sensors'
CONF_EXCLUDE_SENSORS            = 'exclude_sensors'
CONF_ENTITY_REGISTRY_FILE       = 'entity_registry_file_name'
CONF_LOG_LEVEL                  = 'log_level'
CONF_CONFIG_IC3_FILE_NAME       = 'config_ic3_file_name'
CONF_LEGACY_MODE                = 'legacy_mode'
CONF_EVENT_LOG_CARD_DIRECTORY   = 'event_log_card_directory'
CONF_DISPLAY_TEXT_AS            = 'display_text_as'
CONF_TEST_PARAMETER             = 'test_parameter'
CONF_ZONE                       = 'zone'

#devices_schema parameters
CONF_DEVICENAME                 = 'device_name'
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

DEFAULT_USERNAME                         = ''
DEFAULT_PASSWORD                         = ''
DEFAULT_DEVICES                          = []
DEFAULT_TRACK_DEVICES                    = []
DEFAULT_TRACKING_METHOD                  = ''

DEFAULT_ENTITY_REGISTRY_FILE             = ''
DEFAULT_EVENT_LOG_CARD_DIRECTORY         = 'www/custom_cards'
DEFAULT_CREATE_SENSORS                   = []
DEFAULT_EXCLUDE_SENSORS                  = []

DEFAULT_UNIT_OF_MEASUREMENT              = 'mi'
DEFAULT_DISPLAY_TEXT_AS                  = []
DEFAULT_TIME_FORMAT                      = 12
DEFAULT_DISTANCE_METHOD                  = 'waze'
DEFAULT_INZONE_INTERVAL                  = '2 hrs'
DEFAULT_INZONE_INTERVALS                 = []
DEFAULT_DISPLAY_ZONE_FORMAT              = CONF_NAME
DEFAULT_CENTER_IN_ZONE                   = False
DEFAULT_MAX_INTERVAL                     = '4 hrs'
DEFAULT_TRAVEL_TIME_FACTOR               = .60
DEFAULT_GPS_ACCURACY_THRESHOLD           = 100
DEFAULT_OLD_LOCATION_THRESHOLD           = '3 min'
DEFAULT_IGNORE_GPS_ACC_INZONE            = ''
DEFAULT_DISCARD_POOR_GPS_INZONE          = True
DEFAULT_CHECK_GPS_ACC_INZONE             = True
DEFAULT_HIDE_GPS_COORDINATES             = False

DEFAULT_WAZE_REGION                      = 'US'
DEFAULT_WAZE_MAX_DISTANCE                = 1000
DEFAULT_WAZE_MIN_DISTANCE                = 1
DEFAULT_WAZE_REALTIME                    = False
DEFAULT_WAZE_HISTORY_MAX_DISTANCE        = 20
DEFAULT_WAZE_HISTORY_MAP_TRACK_DIRECTION = 'north-south'

DEFAULT_STATIONARY_STILL_TIME            = '8 min'
DEFAULT_STATIONARY_ZONE_OFFSET           = '1, 0'
DEFAULT_STATIONARY_INZONE_INTERVAL       = '30 min'

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
    CONF_WAZE_HISTORY_MAX_DISTANCE: DEFAULT_WAZE_HISTORY_MAX_DISTANCE,
    CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION: DEFAULT_WAZE_HISTORY_MAP_TRACK_DIRECTION,
    CONF_STATIONARY_STILL_TIME: DEFAULT_STATIONARY_STILL_TIME,
    CONF_STATIONARY_ZONE_OFFSET: DEFAULT_STATIONARY_ZONE_OFFSET,
    CONF_STATIONARY_INZONE_INTERVAL: DEFAULT_STATIONARY_INZONE_INTERVAL,

    CONF_LOG_LEVEL: '',
    CONF_EVENT_LOG_CARD_DIRECTORY: 'www/custom_cards',
    CONF_DISPLAY_TEXT_AS: [],
    }

VALIDATE_PARAMETER_LIST = {
    CONF_UNIT_OF_MEASUREMENT: ['mi', 'km'],
    CONF_TIME_FORMAT: [12, 24],
    CONF_DISPLAY_ZONE_FORMAT: ['zone', 'name', 'fname', 'title'],
    CONF_DISTANCE_METHOD: ['waze', 'calc'],
    CONF_WAZE_REGION: ['US', 'NA', 'EU', 'IS', 'AU', 'us', 'na', 'eu', 'is', 'au'],
    CONF_DISPLAY_ZONE_FORMAT: ['zone', 'name', 'fname', 'title'],
    CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION: ['north-south', 'east-west', 'north_south', 'east_west']
}
VALIDATE_PARAMETER_TRUE_FALSE = [
    CONF_CENTER_IN_ZONE,
    CONF_DISCARD_POOR_GPS_INZONE,
    CONF_HIDE_GPS_COORDINATES,
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
    CONF_STATIONARY_STILL_TIME,
    CONF_STATIONARY_INZONE_INTERVAL,
    CONF_OLD_LOCATION_THRESHOLD,
]

#-----►►Test configuration parameters ----------
VALID_CONF_DEVICES_ITEMS = [CONF_DEVICENAME, CONF_EMAIL, CONF_PICTURE, CONF_NAME,
                            CONF_INZONE_INTERVAL, CONF_TRACK_FROM_ZONE, CONF_IOSAPP_SUFFIX,
                            CONF_IOSAPP_ENTITY, CONF_IOSAPP_INSTALLED, CONF_NOIOSAPP,
                            CONF_NO_IOSAPP, CONF_TRACKING_METHOD, ]

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
ZONE_DATETIME              = 'zone_time'
INTO_ZONE_DATETIME         = 'into_zone'
LAST_ZONE                  = 'last_zone'
GROUP                      = 'group'
TIMESTAMP                  = 'timestamp'
TIMESTAMP_SECS             = 'timestamp_secs'
TIMESTAMP_TIME             = 'timestamp_time'
LOCATION_TIME              = 'location_time'
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
LAST_UPDATE_TIME           = 'last_update'
UPDATE_DATETIME            = 'updated'
NEXT_UPDATE_TIME           = 'next_update'
LOCATED_DATETIME           = 'last_located'
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
        LOCATED_DATETIME: '',
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
        CONF_NAME: '',
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
        LOCATION_SOURCE,
        ZONE,
        ZONE_DATETIME,
        INTO_ZONE_DATETIME,
        LAST_ZONE,
        TIMESTAMP,
        TIMESTAMP_SECS,
        TIMESTAMP_TIME,
        LOCATION_TIME,
        DATETIME,
        AGE,
        TRIGGER,
        BATTERY,
        BATTERY_LEVEL,
        BATTERY_STATUS,
        INTERVAL,
        ZONE_DISTANCE,
        CALC_DISTANCE,
        WAZE_DISTANCE,
        TRAVEL_TIME,
        TRAVEL_TIME_MIN,
        DIR_OF_TRAVEL,
        TRAVEL_DISTANCE,
        DEVICE_STATUS,
        LOW_POWER_MODE,
        TRACKING,
        DEVICENAME_IOSAPP,
        AUTHENTICATED,
        LAST_UPDATE_TIME,
        UPDATE_DATETIME,
        NEXT_UPDATE_TIME,
        LOCATED_DATETIME,
        INFO,
        GPS_ACCURACY,
        GPS,
        POLL_COUNT,
        ICLOUD3_VERSION,
        VERT_ACCURACY,
        ALTITUDE,
        BADGE,
        DEVICE_ID,
        ID,
        ICLOUD_HORIZONTAL_ACCURACY,
        ICLOUD_VERTICAL_ACCURACY,
        ICLOUD_BATTERY_LEVEL,
        ICLOUD_BATTERY_STATUS,
        ICLOUD_DEVICE_CLASS,
        ICLOUD_DEVICE_STATUS,
        ICLOUD_LOW_POWER_MODE,
        ICLOUD_TIMESTAMP,
        'emails',
        NAME,
        'firstName',
        'laststName',
        'prsId',
        'batteryLevel',
        'isOld',
        'isInaccurate',
        'phones',
        'invitationAcceptedByEmail',
        'invitationFromEmail',
        'invitationSentToEmail',
        ]