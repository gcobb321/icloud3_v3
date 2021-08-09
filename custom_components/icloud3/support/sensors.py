#####################################################################
#
#   This module handles all activities related to updating a device's sensors. It contains
#   the following modules:
#       TrackFromZones - iCloud3 creates an object for each device/zone
#           with the tracking data fields.
#
#   The primary methods are:
#       determine_interval - Determines the polling interval, update times,
#           location data, etc for the device based on the distance from
#           the zone.
#       determine_interval_after_error - Determines the interval when the
#           location data is to be discarded due to poor GPS, it is old or
#           some other error occurs.
#
#####################################################################

from ..globals           import GlobalVariables as Gb
from ..const_general     import (NOT_SET, TITLE, DATETIME_ZERO, DIST, PAUSED_CAPS, HIGH_INTEGER, )
from ..const_attrs       import (CONF_UNIT_OF_MEASUREMENT, FRIENDLY_NAME, ICON, BADGE,
                                NAME, ZONE, LAST_ZONE, ZONE_DISTANCE, LAST_UPDATE_TIME, LOCATED_DATETIME,
                                NEXT_UPDATE_TIME,
                                CALC_DISTANCE, WAZE_DISTANCE, TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL,
                                INTERVAL,  INFO, POLL_COUNT, ALTITUDE,
                                TRAVEL_DISTANCE, TRIGGER, BATTERY, BATTERY_STATUS, GPS_ACCURACY, VERT_ACCURACY,)

from ..helpers.base      import (instr, post_event, post_error_msg, post_log_info_msg, post_monitor_msg,
                                log_error_msg, log_exception, _trace, _traceha, )
from ..helpers.time      import (time_to_12hrtime, datetime_to_time, secs_to_time_str, mins_to_time_str, )
from ..helpers.entity_io import (set_state_attributes, set_state_attributes, )


import homeassistant.util.dt as dt_util


ZONE_NAME       = 'zone_name'
ZONE_TITLE      = 'zone_title'
ZONE_FNAME      = 'zone_fname'
LAST_ZONE_NAME  = 'last_zone_name'
LAST_ZONE_TITLE = 'last_zone_title'
LAST_ZONE_FNAME = 'last_zone_fname'
ZONE_TIMESTAMP  = 'zone_timestamp'
BASE_ZONE       = 'base_zone'

SENSOR_DEVICE_ATTRS = [
        ZONE,
        LAST_ZONE,
        BASE_ZONE,
        ZONE_NAME,
        ZONE_TITLE,
        ZONE_FNAME,
        LAST_ZONE_NAME,
        LAST_ZONE_TITLE,
        LAST_ZONE_FNAME,
        ZONE_TIMESTAMP,
        ZONE_DISTANCE,
        CALC_DISTANCE,
        WAZE_DISTANCE,
        TRAVEL_TIME,
        TRAVEL_TIME_MIN,
        DIR_OF_TRAVEL,
        INTERVAL,
        INFO,
        LOCATED_DATETIME,
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

SENSOR_FORMAT = {
        ZONE_DISTANCE: 'dist',
        CALC_DISTANCE: 'dist',
        WAZE_DISTANCE: 'diststr',
        TRAVEL_DISTANCE: 'dist',
        BATTERY: '%',
        DIR_OF_TRAVEL: 'title',
        ALTITUDE: 'm-ft',
        BADGE: BADGE,
        LOCATED_DATETIME: 'timestamp-time',
        LAST_UPDATE_TIME: 'timestamp-time',
        NEXT_UPDATE_TIME: 'timestamp-time',
        INTERVAL: 'time_str_secs',
        TRAVEL_TIME: 'time_str_mins',
        TRAVEL_TIME_MIN: 'min',
        }

#---- iPhone Device Tracker Attribute Templates -----
SENSOR_FNAME = {
        ZONE: 'Zone',
        LAST_ZONE: 'Last Zone',
        ZONE_NAME: 'Zone Name',
        ZONE_TITLE: 'Zone Title',
        ZONE_FNAME: 'Zone Fname',
        LAST_ZONE_NAME: 'Last Zone Name',
        LAST_ZONE_TITLE: 'Last Zone Title',
        LAST_ZONE_FNAME: 'Last Zone Fname',
        ZONE_TIMESTAMP: 'Zone Timestamp',
        BASE_ZONE: 'Base Zone',
        ZONE_DISTANCE: 'Zone Distance',
        CALC_DISTANCE: 'Calc Dist',
        WAZE_DISTANCE: 'Waze Dist',
        TRAVEL_TIME: 'Travel Time',
        TRAVEL_TIME_MIN: 'Travel Time',
        DIR_OF_TRAVEL: 'Direction',
        INTERVAL: 'Interval',
        INFO: 'Info',
        LOCATED_DATETIME: 'Last Located',
        LAST_UPDATE_TIME: 'Last Update',
        NEXT_UPDATE_TIME: 'Next Update',
        POLL_COUNT: 'Poll Count',
        TRAVEL_DISTANCE: 'Travel Dist',
        TRIGGER: 'Trigger',
        BATTERY: 'Battery',
        BATTERY_STATUS: 'Battery Status',
        GPS_ACCURACY: 'GPS Accuracy',
        VERT_ACCURACY: 'Vertical Accuracy',
        BADGE: 'Badge',
        NAME: 'Name',
        }
SENSOR_ZONE_FNAME = {
        ZONE_NAME: 'Zone Name',
        ZONE_TITLE: 'Zone Title',
        ZONE_FNAME: 'Zone Fname',
        LAST_ZONE_NAME: 'Last Zone Name',
        LAST_ZONE_TITLE: 'Last Zone Title',
        LAST_ZONE_FNAME: 'Last Zone Fname',
}

SENSOR_ICON = {
        ZONE: 'mdi:cellphone-iphone',
        LAST_ZONE: 'mdi:map-clock-outline',
        BASE_ZONE: 'mdi:map-clock',
        ZONE_TIMESTAMP: 'mdi:clock-in',
        ZONE_DISTANCE: 'mdi:map-marker-distance',
        CALC_DISTANCE: 'mdi:map-marker-distance',
        WAZE_DISTANCE: 'mdi:map-marker-distance',
        TRAVEL_TIME: 'mdi:clock-outline',
        TRAVEL_TIME_MIN: 'mdi:clock-outline',
        DIR_OF_TRAVEL: 'mdi:compass-outline',
        INTERVAL: 'mdi:clock-start',
        INFO: 'mdi:information-outline',
        LOCATED_DATETIME: 'mdi:history',
        LAST_UPDATE_TIME: 'mdi:history',
        NEXT_UPDATE_TIME: 'mdi:update',
        POLL_COUNT: 'mdi:counter',
        TRAVEL_DISTANCE: 'mdi:map-marker-distance',
        TRIGGER: 'mdi:flash-outline',
        BATTERY: 'mdi:battery-outline',
        BATTERY_STATUS: 'mdi:battery-outline',
        GPS_ACCURACY: 'mdi:map-marker-radius',
        ALTITUDE: 'mdi:image-filter-hdr',
        VERT_ACCURACY: 'mdi:map-marker-radius',
        BADGE: 'mdi:shield-account',
        NAME: 'mdi:account',
        'entity_log': 'mdi:format-list-checkbox',
        }

SENSOR_ID_NAME_LIST = {
        'zon': ZONE,
        'lzon': LAST_ZONE,
        'bzon': BASE_ZONE,
        'zonn': ZONE_NAME,
        'zont': ZONE_TITLE,
        'zonfn': ZONE_FNAME,
        'lzonn': LAST_ZONE_NAME,
        'lzont': LAST_ZONE_TITLE,
        'lzonfn': LAST_ZONE_FNAME,
        'zonts': ZONE_TIMESTAMP,
        'zdis': ZONE_DISTANCE,
        'cdis': CALC_DISTANCE,
        'wdis': WAZE_DISTANCE,
        'tdis': TRAVEL_DISTANCE,
        'ttim': TRAVEL_TIME,
        'mtim': TRAVEL_TIME_MIN,
        'dir': DIR_OF_TRAVEL,
        'intvl':  INTERVAL,
        'lloc': LOCATED_DATETIME,
        'lupdt': LAST_UPDATE_TIME,
        'nupdt': NEXT_UPDATE_TIME,
        'cnt': POLL_COUNT,
        INFO: INFO,
        'trig': TRIGGER,
        'bat': BATTERY,
        'batstat': BATTERY_STATUS,
        'alt': ALTITUDE,
        'gpsacc': GPS_ACCURACY,
        'vacc': VERT_ACCURACY,
        BADGE: BADGE,
        NAME: NAME,
        }

class iCloud3Sensors(object):

    def __init__(self, hass, create_sensor_ids, exclude_sensor_ids):
        self.hass                = hass
        self.create_sensor_ids   = create_sensor_ids
        self.exclude_sensor_ids  = exclude_sensor_ids
        self.sensors_custom_list = []

        #--------------------------------------------------------------------
        # This will process the 'sensors' and 'exclude_sensors' config
        # parameters if 'sensors' exists, only those sensors wil be displayed.
        # if 'exclude_sensors' eists, those sensors will not be displayed.
        #'sensors' takes ppresidence over 'exclude_sensors'.

        try:
            # if initial_load_flag is False:
            #     return

            if self.create_sensor_ids != []:
                for sensor_id in self.create_sensor_ids[0].split(','):
                    id = sensor_id.lower().strip()
                    if id in SENSOR_ID_NAME_LIST:
                        self.sensors_custom_list.append(SENSOR_ID_NAME_LIST.get(id))

            elif self.exclude_sensor_ids != []:
                self.sensors_custom_list.extend(SENSOR_DEVICE_ATTRS)
                for sensor_id in self.exclude_sensor_ids[0].split(','):
                    id = sensor_id.lower().strip()
                    if id in SENSOR_ID_NAME_LIST:
                        if SENSOR_ID_NAME_LIST.get(id) in self.sensors_custom_list:
                            self.sensors_custom_list.remove(SENSOR_ID_NAME_LIST.get(id))
            else:
                self.sensors_custom_list.extend(SENSOR_DEVICE_ATTRS)

        except Exception as err:
            log_exception(err)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><
    def update_device_sensors(self, Device, attrs:dict, DeviceFmZone=None):
        '''
        Update/Create sensor for the device attributes.

        Input:
            Device.       Device or DeviceFmZone ifupdatine non-Home zone info
            attrs:        attributes to be updated

            sensor_device_attrs = ['distance', CALC_DISTANCE, WAZE_DISTANCE,
                        TRAVEL_TIME, DIR_OF_TRAVEL, INTERVAL, INFO,
                        LOCATED_DATETIME, LAST_UPDATE_TIME, NEXT_UPDATE_TIME,
                        POLL_COUNT, TRIGGER, BATTERY, 'battery_state',
                        GPS_ACCURACY, ZONE, LAST_ZONE, TRAVEL_DISTANCE]

            sensor_attrs_format = {'distance': 'dist', CALC_DISTANCE: 'dist',
                        TRAVEL_DISTANCE: 'dist', BATTERY: '%',
                        DIR_OF_TRAVEL: 'title'}
        '''
        try:
            if not attrs:
                return

            badge_state = None
            badge_zone  = None
            badge_dist  = None

            if DeviceFmZone:
                sensor_prefix = DeviceFmZone.sensor_prefix
            else:
                sensor_prefix = Device.sensor_prefix

            for attr_name in SENSOR_DEVICE_ATTRS:
                sensor_entity = (f"{sensor_prefix}{attr_name}")
                sensor_attrs = {}
                format_type  = ''

                if Gb.start_icloud3_inprocess_flag and attr_name != INFO:
                    state_value = '──' if attr_name != LAST_UPDATE_TIME else 'Never'
                    sensor_attrs[CONF_UNIT_OF_MEASUREMENT] = ''
                elif attr_name in attrs:
                    state_value = attrs[attr_name]
                else:
                    continue

                if Gb.start_icloud3_inprocess_flag:
                    pass
                elif attr_name in SENSOR_FORMAT:
                    format_type = SENSOR_FORMAT[attr_name]
                    # _trace(Device.devicename, f"{attr_name} {format_type=} {state_value=}")
                    if format_type in ['%', 'sec', 'min', 'hr']:
                        sensor_attrs[CONF_UNIT_OF_MEASUREMENT] = format_type
                    elif format_type == DIST:
                        sensor_attrs[CONF_UNIT_OF_MEASUREMENT] = Gb.um
                    elif format_type == 'diststr':
                        try:
                            sensor_attrs[CONF_UNIT_OF_MEASUREMENT] = Gb.um
                        except:
                            sensor_attrs[CONF_UNIT_OF_MEASUREMENT] = ''
                    elif format_type == TITLE:
                        state_value = state_value.title().replace('_', ' ')
                    elif format_type == 'kph-mph':
                        sensor_attrs[CONF_UNIT_OF_MEASUREMENT] = Gb.um_kph_mph
                    elif format_type == 'm-ft':
                        sensor_attrs[CONF_UNIT_OF_MEASUREMENT] = Gb.um_m_ft
                    elif format_type == 'time_str_mins':
                        if state_value == '': state_value = 0
                        time_str = mins_to_time_str(state_value)
                        if time_str and instr(time_str, 'd') is False:         # Make sure it is not a 4d2h34m12s item
                            time_min_hrs = time_str.split(' ')
                            state_value = time_min_hrs[0]
                            sensor_attrs[CONF_UNIT_OF_MEASUREMENT] = time_min_hrs[1]
                    elif format_type == 'time_str_secs':
                        if state_value == '': state_value = 0
                        time_str = secs_to_time_str(state_value)
                        if time_str and instr(time_str, 'd') is False:       # Make sure it is not a 4d2h34m12s item
                            time_secs_min_hrs = time_str.split(' ')
                            # _trace(f"{attr_name=} {state_value=} {time_str=} {time_secs_min_hrs=}")
                            state_value = time_secs_min_hrs[0]
                            sensor_attrs[CONF_UNIT_OF_MEASUREMENT] = time_secs_min_hrs[1]

                    elif format_type == 'timestamp-time':
                        if state_value == DATETIME_ZERO:
                            state_value = ''
                        else:
                            state_value = datetime_to_time(state_value)
                            state_value = time_to_12hrtime(state_value)

                if attr_name in SENSOR_ICON:
                    sensor_attrs[ICON] = SENSOR_ICON[attr_name]

                if attr_name in SENSOR_FNAME:
                    sensor_attrs[FRIENDLY_NAME] = (f"{Device.fname}{SENSOR_FNAME[attr_name]}")

                self._update_device_sensors_hass(sensor_prefix, attr_name, state_value, sensor_attrs)

                # if Device.attrs_zone == NOT_SET:
                if Gb.start_icloud3_inprocess_flag:
                    pass

                elif attr_name == ZONE:
                    Zone = Gb.Zones_by_zone[state_value]

                    zone_attrs = {}
                    zone_attrs[ICON] = SENSOR_ICON[attr_name]
                    if badge_state is None: badge_state = Zone.name
                    zone_sensor_prefix = Zone.sensor_prefix

                    sensor_attrs = dict(zone_attrs)
                    sensor_attrs[FRIENDLY_NAME] = (f"{zone_sensor_prefix} Zone Name")
                    self._update_device_sensors_hass(sensor_prefix, "zone_name", Zone.name, sensor_attrs)
                    sensor_attrs = dict(zone_attrs)
                    sensor_attrs[FRIENDLY_NAME] = (f"{zone_sensor_prefix} Zone Title")
                    self._update_device_sensors_hass(sensor_prefix, "zone_title", Zone.title, sensor_attrs)
                    sensor_attrs = dict(zone_attrs)
                    sensor_attrs[FRIENDLY_NAME] = (f"{zone_sensor_prefix} Zone Fname")
                    self._update_device_sensors_hass(sensor_prefix, "zone_fname", Zone.fname, sensor_attrs)

                elif attr_name == LAST_ZONE:
                    Zone = Gb.Zones_by_zone[state_value]
                    zone_attrs = {}
                    zone_attrs[ICON] = SENSOR_ICON[attr_name]
                    zone_sensor_prefix = Zone.sensor_prefix

                    sensor_attrs = dict(zone_attrs)
                    sensor_attrs[FRIENDLY_NAME] = (f"{zone_sensor_prefix} Last Zone Name")
                    self._update_device_sensors_hass(sensor_prefix, "last_zone_name", Zone.name, sensor_attrs)
                    sensor_attrs = dict(zone_attrs)
                    sensor_attrs[FRIENDLY_NAME] = (f"{zone_sensor_prefix} Last Zone Title")
                    self._update_device_sensors_hass(sensor_prefix,  "last_zone_title", Zone.title, sensor_attrs)
                    sensor_attrs = dict(zone_attrs)
                    sensor_attrs[FRIENDLY_NAME] = (f"{zone_sensor_prefix} Last Zone Fname")
                    self._update_device_sensors_hass(sensor_prefix,  "last_zone_fname", Zone.fname, sensor_attrs)

                elif attr_name == ZONE_DISTANCE:
                    if state_value and float(state_value) > 0:
                        badge_state = (f"{state_value} {Gb.um}")

            if Device.is_tracking_paused: badge_state = PAUSED_CAPS

            if badge_state:
                self._update_device_sensors_hass(sensor_prefix, BADGE, badge_state, Device.sensor_badge_attrs)
            return True

        except Exception as err:
            log_exception(err)
            log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
            log_error_msg(log_msg)

            return False

#--------------------------------------------------------------------
    def _update_device_sensors_hass(self, sensor_prefix, attr_name, state_value, sensor_attrs):

        try:
            state_value = state_value[0:250]
        except:
            pass

        if attr_name in self.sensors_custom_list:
            sensor_entity = (f"{sensor_prefix}{attr_name}")

            set_state_attributes(sensor_entity, state_value, sensor_attrs)

#--------------------------------------------------------------------
