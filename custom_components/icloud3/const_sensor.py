
#   Constant file for device_tracker and sensors


from .const     import (DISTANCE_TO_DEVICES,
                        BLANK_SENSOR_FIELD,
                        NAME,
                        BADGE,
                        TRIGGER,
                        ZONE, ZONE_DATETIME, LAST_ZONE, FROM_ZONE, ZONE_INFO,
                        ZONE_NAME, ZONE_FNAME, LAST_ZONE_NAME, LAST_ZONE_FNAME,
                        INTERVAL,
                        BATTERY_SOURCE, BATTERY, BATTERY_STATUS,
                        DISTANCE, ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD, HOME_DISTANCE,
                        MAX_DISTANCE, TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, MOVED_DISTANCE,
                        DEVICE_STATUS,
                        LAST_UPDATE, LAST_UPDATE_DATETIME,
                        NEXT_UPDATE, NEXT_UPDATE_DATETIME,
                        LAST_LOCATED, LAST_LOCATED_DATETIME,
                        INFO, GPS_ACCURACY, ALTITUDE, VERTICAL_ACCURACY,
                        TFZ_ZONE_INFO, TFZ_DISTANCE, TFZ_ZONE_DISTANCE, TFZ_TRAVEL_TIME,
                        TFZ_TRAVEL_TIME_MIN, TFZ_DIR_OF_TRAVEL,
                        )

SENSOR_LIST_DEVICE =    [NAME, BADGE, BATTERY, BATTERY_STATUS,
                        TRIGGER, INTERVAL, LAST_LOCATED,
                        INFO,
                        GPS_ACCURACY, ALTITUDE, VERTICAL_ACCURACY,
                        ]
SENSOR_LIST_TRACKING =  [NEXT_UPDATE, LAST_UPDATE, LAST_LOCATED,
                        TRAVEL_TIME, TRAVEL_TIME_MIN, MOVED_DISTANCE, DIR_OF_TRAVEL,
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
SENSOR_LIST_DISTANCE =  [DISTANCE, ZONE_DISTANCE, HOME_DISTANCE,
                        ]
SENSOR_GROUPS = {
        'battery': [BATTERY, BATTERY_STATUS],
        'md_badge': [BADGE],
        'md_battery': [BATTERY, BATTERY_STATUS],
        'md_location_sensors': [
                        NAME,
                        ZONE, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME,
                        HOME_DISTANCE,
                        TRAVEL_TIME, TRAVEL_TIME_MIN,
                        LAST_LOCATED,
                        LAST_UPDATE,
                        ],
}
'''
The Sensor Definition dictionary defines all sensors created by iCloud3.
        Key:
                Sensor id used in config_flow and in the en.json file (Ex: 'name', 'tfz_zone_distance')
        Item definition:
                Field 0:
                HA base sensor entity_id name.
                        Prefix: [devicename]
                        Suffix: [Track_from_zone name]
                        Examples:   'sensor.gary_iphone_battery', 'sensor.gary_iphone_zone_HOME_DISTANCE',
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
SENSOR_FNAME  = 0
SENSOR_TYPE   = 1
SENSOR_ICON   = 2
SENSOR_ATTRS  = 3
SENSOR_DEFAULT= 4

SENSOR_DEFINITION = {
        # SENSOR_FIELD_ITEMS: [
        #         'Sensor Friendly Name',
        #         'Sensor Type-battery, text, info, distance, time, timer, timestamp, zone',
        #         'icon-mdi:xxx,
        #         [attributes from sensors[sensorname1, sensorname2, ...]],
        #         default value to display at startup,
        #       ]
        NAME: [
                'Name',
                'text',
                'mdi:account',
                [],
                BLANK_SENSOR_FIELD],
        BADGE: [
                'Badge',
                'badge',
                'mdi:shield-account',
                [NAME, BATTERY, ZONE, ZONE_FNAME, ZONE_NAME,
                HOME_DISTANCE, DISTANCE_TO_DEVICES,
                MAX_DISTANCE, TRAVEL_TIME, DIR_OF_TRAVEL, INTERVAL,
                ZONE_DATETIME,
                LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME,
                DEVICE_STATUS, ],
                BLANK_SENSOR_FIELD],
        BATTERY: [
                'Battery',
                'battery',
                'mdi:battery-outline',
                [BATTERY_STATUS, BATTERY_SOURCE],
                0],
        BATTERY_STATUS: [
                'BatteryStatus',
                'text, title',
                'mdi:battery-outline',
                [BATTERY, BATTERY_SOURCE],
                ''],
        INFO: [
                'Info',
                'info, ha_history_exclude',
                'mdi:information-outline',
                [],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_TRACKING_UPDATE
        INTERVAL: [
                'Interval',
                'timer, secs',
                'mdi:clock-start',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                BLANK_SENSOR_FIELD],
        LAST_LOCATED: [
                'LastLocated',
                'timestamp, ha_history_exclude',
                'mdi:history',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                BLANK_SENSOR_FIELD],
        LAST_UPDATE: [
                'LastUpdate',
                'timestamp, ha_history_exclude',
                'mdi:history',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                BLANK_SENSOR_FIELD],
        NEXT_UPDATE: [
                'NextUpdate',
                'timestamp, ha_history_exclude',
                'mdi:update',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_TRACKING_TIME
        TRAVEL_TIME: [
                'TravelTime',
                'timer, min',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN],
                0],
        TRAVEL_TIME_MIN: [
                'TravelTimeMin',
                'timer',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN],
                0],

        # CONF_SENSORS_TRACKING_DISTANCE
        ZONE_DISTANCE: [
                'ZoneDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD],
                0],
        DISTANCE: [
                'Distance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD],
                0],
        HOME_DISTANCE: [
                'HomeDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD],
                '0'],
        DIR_OF_TRAVEL: [
                'Direction',
                'text, title',
                'mdi:compass-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, DISTANCE, MAX_DISTANCE],
                BLANK_SENSOR_FIELD],
        MOVED_DISTANCE: [
                'MovedDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, MAX_DISTANCE],
                0],
        ZONE_INFO: [
                'ZoneInfo',
                'zone_info',
                'mdi:map-marker-radius-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN,
                DISTANCE, MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD, DIR_OF_TRAVEL],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_TRACK_FROM_ZONES
        TFZ_ZONE_INFO: [
                'ZoneInfo',
                'zone_info',
                'mdi:map-marker-radius-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN,
                DISTANCE, MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD, DIR_OF_TRAVEL],
                BLANK_SENSOR_FIELD],
        TFZ_TRAVEL_TIME: [
                'TravelTime',
                'timer, mins',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN],
                BLANK_SENSOR_FIELD],
        TFZ_TRAVEL_TIME_MIN: [
                'TravelTimeMin',
                'timer',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN],
                BLANK_SENSOR_FIELD],
        TFZ_DISTANCE: [
                'ZoneDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, DISTANCE, MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD],
                '0 mi'],
        TFZ_ZONE_DISTANCE: [
                'ZoneDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, DISTANCE, MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD],
                '0 mi'],
        TFZ_DIR_OF_TRAVEL: [
                'Direction',
                'text, title',
                'mdi:compass-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, DISTANCE, MAX_DISTANCE],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_TRACKING_OTHER
        TRIGGER: [
                'Trigger',
                'text, ha_history_exclude',
                'mdi:flash-outline',
                [],
                BLANK_SENSOR_FIELD],
        WAZE_DISTANCE: [
                'WazeDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, MAX_DISTANCE, DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD],
                0],
        CALC_DISTANCE: [
                'CalcDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, MAX_DISTANCE, DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD],
                0],

        # CONF_SENSORS_ZONE
        ZONE: [
                'Zone',
                'zone',
                'mdi:map-home-import-outline',
                [ZONE, ZONE_FNAME, ZONE_NAME],
                BLANK_SENSOR_FIELD],
        ZONE_FNAME: [
                'ZoneFriendlyName',
                'zone',
                'mdi:map-home-import-outline',
                [ZONE, ZONE_FNAME, ZONE_NAME],
                BLANK_SENSOR_FIELD],
        ZONE_NAME: [
                'ZoneName',
                'zone',
                'mdi:map-home-import-outline',
                [ZONE, ZONE_FNAME, ZONE_NAME],
                BLANK_SENSOR_FIELD],
        ZONE_DATETIME: [
                'ZoneChanged',
                'timestamp, ha_history_exclude',
                'mdi:clock-in',
                [],
                BLANK_SENSOR_FIELD],
        LAST_ZONE: [
                'LastZone',
                'zone, ha_history_exclude',
                'mdi:map-home-import-outline',
                [LAST_ZONE_FNAME, LAST_ZONE_NAME],
                BLANK_SENSOR_FIELD],
        LAST_ZONE_FNAME: [
                'LastZone',
                'zone, ha_history_exclude',
                'mdi:map-home-import-outline',
                [LAST_ZONE],
                BLANK_SENSOR_FIELD],
        LAST_ZONE_NAME: [
                'LastZone',
                'zone, ha_history_exclude',
                'mdi:map-home-import-outline',
                [LAST_ZONE],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_OTHER
        GPS_ACCURACY: [
                'GPSAccuracy',
                'distance, m',
                'mdi:map-marker-radius',
                [],
                0],
        ALTITUDE: [
                'Altitude',
                'distance, m-ft',
                'mdi:arrow-compress-up',
                [VERTICAL_ACCURACY],
                0],
        VERTICAL_ACCURACY: [
                'VerticalAccuracy',
                'distance, m',
                'mdi:map-marker-radius',
                [],
                0],
}
