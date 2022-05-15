
#   Constant file for device_tracker and sensors

from .const             import (NOT_SET, TITLE, DATETIME_ZERO, DIST, PAUSED_CAPS, HIGH_INTEGER,
                                DOMAIN, MODE_PLATFORM, HOME,
                                STATIONARY, STATIONARY_FNAME,

                                CONF_UNIT_OF_MEASUREMENT, FRIENDLY_NAME, ICON, BADGE, NOT_HOME,
                                NAME, ZONE, LAST_ZONE, ZONE_DISTANCE,
                                LAST_UPDATE_DATETIME, LAST_UPDATE_TIME, LAST_UPDATE,
                                NEXT_UPDATE_DATETIME, NEXT_UPDATE_TIME, NEXT_UPDATE,
                                LAST_LOCATED_DATETIME, LAST_LOCATED_TIME, LAST_LOCATED,
                                CALC_DISTANCE, TRAVEL_DISTANCE, DIR_OF_TRAVEL,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, WAZE_DISTANCE, DISTANCE,
                                INTERVAL,  INFO, ALTITUDE,
                                TRAVEL_DISTANCE, TRIGGER, BATTERY, BATTERY_STATUS, GPS_ACCURACY, VERT_ACCURACY,

                                ICLOUD3_EVENT_LOG,
                                NAME, BADGE, BATTERY,
                                TRIGGER, INTERVAL,
                                TRAVEL_TIME,
                                TRAVEL_TIME_MIN, ZONE_DISTANCE, HOME_DISTANCE, WAZE_DISTANCE,
                                CALC_DISTANCE, TRAVEL_DISTANCE, GPS_ACCURACY,
                                DIR_OF_TRAVEL, ZONE, ZONE_FNAME,
                                ZONE_NAME, ZONE_DATETIME, FROM_ZONE,
                                POLL_COUNT, INFO, LAST_ZONE, LAST_ZONE_FNAME,
                                LAST_ZONE_NAME,
                                BATTERY_STATUS, ALTITUDE, VERTICAL_ACCURACY,
                                TFZ_ZONEINFO, TFZ_DISTANCE,
                                TFZ_TRAVEL_TIME, TFZ_TRAVEL_TIME_MIN,
                                TFZ_DIR_OF_TRAVEL,
                                DEVTRKR_ONLY_MONITOR,
                                )

X_SENSOR_DEVICE_ATTRS = [
        ZONE,
        LAST_ZONE,
        ZONE_DATETIME,
        ZONE_DISTANCE,
        CALC_DISTANCE,
        WAZE_DISTANCE,
        TRAVEL_TIME,
        TRAVEL_TIME_MIN,
        DIR_OF_TRAVEL,
        INTERVAL,
        INFO,
        LAST_LOCATED_DATETIME,
        LAST_UPDATE_TIME,
        NEXT_UPDATE_TIME,
        POLL_COUNT,
        TRAVEL_DISTANCE,
        TRIGGER,
        BATTERY,
        BATTERY_STATUS,
        GPS_ACCURACY,
        VERT_ACCURACY,
        BADGE,
        NAME,
        ]

SENSOR_LIST_DEVICE =    [NAME, BADGE, BATTERY, BATTERY_STATUS,
                        TRIGGER, INTERVAL, LAST_LOCATED,
                        INFO,
                        GPS_ACCURACY, ALTITUDE, VERTICAL_ACCURACY,
                        ]
SENSOR_LIST_TRACKING =  [NEXT_UPDATE, LAST_UPDATE, LAST_LOCATED,
                        TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_DISTANCE, DIR_OF_TRAVEL,
                        WAZE_DISTANCE, CALC_DISTANCE, ZONE_DISTANCE, HOME_DISTANCE,
                        ZONE, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME,
                        LAST_ZONE, LAST_ZONE_FNAME, LAST_ZONE_NAME,
                        ]
SENSOR_LIST_TRACK_FROM_ZONE = [INFO, LAST_UPDATE, NEXT_UPDATE,
                        TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL,
                        ]
SENSOR_LIST_LOC_UPDATE =[TRIGGER, INTERVAL,
                        NEXT_UPDATE, LAST_UPDATE, LAST_LOCATED,
                        TRAVEL_TIME, TRAVEL_TIME_MIN,
                        ]
SENSOR_LIST_ZONE =      [ZONE_DISTANCE, HOME_DISTANCE,
                        ZONE, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME,
                        LAST_ZONE, LAST_ZONE_FNAME, LAST_ZONE_NAME,
                        ]

'''
The Sensor Definition dictionary defines all sensors created by iCloud3.
    Key:
        Sensor id used in config_flow and in the en.json file (Ex: 'name', 'tfz_zone_distance')
    Item definition:
        Field 0:
            HA base sensor entity_id name.
                Prefix: [devicename]
                Suffix: [Track_from_zone name]
                Examples:   'sensor.gary_iphone_battery', 'sensor.gary_iphone_zone_distance_home',
                            'sensor.bary_iphone_travel_time_home'
        Index 1:
            Sensor Friendly Name.
                Prefix: [device fridndly name]/[device type]
                Examples:   'Gary/iPhone Name', 'Gary/iPhone Distance Warhouse'
        Index 2:
            Sensor type used to determine the format of sensor and the Class object that should be used
        Index 3:
            mdi Icon for the sensor
        Index 4:
            List of attributes that should be added to the sensor
'''

SENSOR_SUFFIX = ''
SENSOR_ENTITY = 0
SENSOR_FNAME  = 1
SENSOR_TYPE   = 2
SENSOR_ICON   = 3
SENSOR_ATTRS  = 4
SENSOR_DEFAULT= 5

SENSOR_DEFINITION = {
        DEVTRKR_ONLY_MONITOR: [
                'monitor',
                'monitor',
                'control',
                'mdi:cellphone-information',
                [NAME, ZONE_NAME, BATTERY, BATTERY_STATUS,
                HOME_DISTANCE, TRAVEL_TIME, TRAVEL_TIME_MIN, ],
                '___'],

        # CONF_SENSORS_DEVICE
        NAME: [
                'name',
                'Name',
                'text',
                'mdi:account',
                [],
                '___'],
        BADGE: [
                'badge',
                'Badge',
                'badge',
                'mdi:shield-account',
                [],
                '___'],
        BATTERY: [
                'battery',
                'Battery',
                'battery',
                'mdi:battery-outline',
                [BATTERY_STATUS],
                0],
        BATTERY_STATUS: [
                'battery_status',
                'BatteryStatus',
                'text, title',
                'mdi:battery-outline',
                [BATTERY],
                '___'],
        INFO: [
                'info',
                'Info',
                'info',
                'mdi:information-outline',
                [],
                '___'],

        # CONF_SENSORS_TRACKING_UPDATE
        INTERVAL: [
                'interval',
                'Interval',
                'timer, secs',
                'mdi:clock-start',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                '___'],
        LAST_LOCATED: [
                'last_located',
                'LastLocated',
                'timestamp',
                'mdi:history',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                '___'],
        LAST_UPDATE: [
                'last_update',
                'LastUpdate',
                'timestamp',
                'mdi:history',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                '___'],
        NEXT_UPDATE: [
                'next_update',
                'NextUpdate',
                'timestamp',
                'mdi:update',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                '___'],

        # CONF_SENSORS_TRACKING_TIME
        TRAVEL_TIME: [
                'travel_time',
                'TravelTime',
                'timer, min',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, 
                WAZE_DISTANCE, CALC_DISTANCE],
                0],
        TRAVEL_TIME_MIN: [
                'travel_time_min',
                'TravelTimeMin',
                'timer',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, 
                WAZE_DISTANCE, CALC_DISTANCE],
                0],

        # CONF_SENSORS_TRACKING_DISTANCE
        ZONE_DISTANCE: [
                'zone_distance',
                'ZoneDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, 
                WAZE_DISTANCE, CALC_DISTANCE],
                0],
        HOME_DISTANCE: [
                'home_distance',
                'HomeDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, 
                WAZE_DISTANCE, CALC_DISTANCE],
                '0'],
        DIR_OF_TRAVEL: [
                'dir_of_travel',
                'Direction',
                'text, title',
                'mdi:compass-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, 
                WAZE_DISTANCE, CALC_DISTANCE],
                '___'],
        TRAVEL_DISTANCE: [
                'travel_distance',
                'TravelDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, 
                WAZE_DISTANCE, CALC_DISTANCE],
                0],

        # CONF_SENSORS_TRACK_FROM_ZONES
        TFZ_ZONEINFO: [
                'zoneinfo',
                'ZoneInfo',
                'tfz_zoneinfo',
                'mdi:map-marker-radius-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN,
                DIR_OF_TRAVEL, DISTANCE, WAZE_DISTANCE, CALC_DISTANCE],
                '___'],
        TFZ_TRAVEL_TIME: [
                'travel_time',
                'TravelTime',
                'tfz_timer, mins',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN,
                DIR_OF_TRAVEL, DISTANCE, WAZE_DISTANCE, CALC_DISTANCE],
                '___'],
        TFZ_TRAVEL_TIME_MIN: [
                'travel_time_min',
                'TravelTimeMin',
                'tfz_timer',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN,
                DIR_OF_TRAVEL, DISTANCE, WAZE_DISTANCE, CALC_DISTANCE],
                '___'],
        TFZ_DISTANCE: [
                'distance',
                'ZoneDistance',
                'tfz_distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN,
                DIR_OF_TRAVEL, DISTANCE, WAZE_DISTANCE, CALC_DISTANCE],
                '0 mi'],
        TFZ_DIR_OF_TRAVEL: [
                'dir_of_travel',
                'Direction',
                'tfz_text, title',
                'mdi:compass-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN,
                DIR_OF_TRAVEL, DISTANCE, WAZE_DISTANCE, CALC_DISTANCE],
                '___'],

        # CONF_SENSORS_TRACKING_OTHER
        TRIGGER: [
                'trigger',
                'Trigger',
                'text',
                'mdi:flash-outline',
                [],
                '___'],
        WAZE_DISTANCE: [
                'waze_distance',
                'WazeDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, DISTANCE, WAZE_DISTANCE, CALC_DISTANCE],
                0],
        CALC_DISTANCE: [
                'calc_distance',
                'CalcDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, DISTANCE, WAZE_DISTANCE, CALC_DISTANCE],
                0],

        # CONF_SENSORS_ZONE
        ZONE: [
                'zone',
                'Zone',
                'zone',
                'mdi:map-home-import-outline',
                [ZONE, ZONE_FNAME, ZONE_NAME],
                '___'],
        ZONE_FNAME: [
                'zone_fname',
                'ZoneFriendlyName',
                'zone',
                'mdi:map-home-import-outline',
                [ZONE, ZONE_FNAME, ZONE_NAME],
                '___'],
        ZONE_NAME: [
                'zone_name',
                'ZoneName',
                'zone',
                'mdi:map-home-import-outline',
                [ZONE, ZONE_FNAME, ZONE_NAME],
                '___'],
        ZONE_DATETIME: [
                'zone_datetime',
                'ZoneChanged',
                'timestamp',
                'mdi:clock-in',
                [],
                '___'],
        LAST_ZONE: [
                'last_zone',
                'LastZone',
                'zone',
                'mdi:map-home-import-outline',
                [LAST_ZONE_FNAME, LAST_ZONE_NAME],
                '___'],
        LAST_ZONE_FNAME: [
                'last_zone_fname',
                'LastZone',
                'zone',
                'mdi:map-home-import-outline',
                [LAST_ZONE],
                '___'],
        LAST_ZONE_NAME: [
                'last_zone_name',
                'LastZone',
                'zone',
                'mdi:map-home-import-outline',
                [LAST_ZONE],
                '___'],

        # CONF_SENSORS_OTHER
        GPS_ACCURACY: [
                'gps_accuracy',
                'GPSAccuracy',
                'distance, m',
                'mdi:map-marker-radius',
                [],
                0],
        ALTITUDE: [
                'altitude',
                'Altitude',
                'distance, m-ft',
                'mdi:arrow-compress-up',
                [VERTICAL_ACCURACY],
                0],
        VERTICAL_ACCURACY: [
                'vertical_accuracy',
                'VerticalAccuracy',
                'distance, m',
                'mdi:map-marker-radius',
                [],
                0],
}
