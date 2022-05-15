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

from .global_variables  import GlobalVariables as Gb
from .const             import (NOT_SET, NOT_SET_FNAME, DATETIME_ZERO, HHMMSS_ZERO, PAUSED_CAPS, HIGH_INTEGER, RARROW2,
                                DOMAIN, MODE_PLATFORM, HOME, DOT,
                                STATIONARY, STATIONARY_FNAME,

                                CONF_UNIT_OF_MEASUREMENT, FRIENDLY_NAME, ICON, BADGE, NOT_HOME,
                                NAME, ZONE, LAST_ZONE, ZONE_DISTANCE,
                                LAST_UPDATE_DATETIME, LAST_UPDATE_TIME, LAST_UPDATE,
                                NEXT_UPDATE_DATETIME, NEXT_UPDATE_TIME, NEXT_UPDATE,
                                LAST_LOCATED_DATETIME, LAST_LOCATED_TIME, LAST_LOCATED,
                                CALC_DISTANCE, TRAVEL_DISTANCE, DIR_OF_TRAVEL,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, WAZE_DISTANCE,
                                INTERVAL,  INFO, ALTITUDE, TRAVEL_TIME_MIN,
                                TRAVEL_DISTANCE, TRIGGER, BATTERY, BATTERY_STATUS, GPS_ACCURACY, VERT_ACCURACY,

                                SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME,
                                CONF_IC3_DEVICENAME, FNAME, CONF_DEVICE_TYPE, CONF_PICTURE,
                                CONF_TRACK_FROM_ZONES,

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
from .const_sensor      import (SENSOR_DEFINITION,
                                SENSOR_ENTITY, SENSOR_FNAME, SENSOR_TYPE, SENSOR_ICON,
                                SENSOR_ATTRS, SENSOR_DEFAULT, )


from homeassistant.const        import DEVICE_CLASS_BATTERY, PERCENTAGE

from .helpers.base                      import (instr, post_event, post_error_msg, post_log_info_msg, post_monitor_msg,
                                                signal_device_update, broadcast_info_msg,
                                                log_info_msg, log_error_msg, log_exception, _trace, _traceha, )
from .helpers.time                      import (time_to_12hrtime, datetime_to_time, secs_to_time_str, mins_to_time_str, )
from .helpers.entity_io                 import (set_state_attributes, set_state_attributes, )
from .support                       import start_ic3

from homeassistant.components.sensor    import SensorEntity
from homeassistant.config_entries       import ConfigEntry
from homeassistant.core                 import HomeAssistant, callback
from homeassistant.helpers.dispatcher   import async_dispatcher_connect
# from homeassistant.helpers.entity       import DeviceInfo
from homeassistant.helpers.icon         import icon_for_battery_level
from homeassistant.helpers              import entity_registry as er, device_registry as dr

import homeassistant.util.dt as dt_util
from homeassistant.helpers.entity       import Entity

import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    '''Set up iCloud3 sensors'''

    # Save the hass `add_entities` call object for use in config_flow for adding new sensors
    Gb.async_add_entities_sensor = async_add_entities

    try:
        if Gb.conf_file_data == {}:
            Gb.hass = hass
            start_ic3.initialize_directory_filenames()
            start_ic3.load_storage_icloud3_configuration_file()

        NewSensors = []
        if Gb.EvLogSensor is None:
            Gb.EvLogSensor = SensorEventLog('iCloud3 Event Log', SENSOR_EVENT_LOG_NAME)
            if Gb.EvLogSensor:
                NewSensors.append(Gb.EvLogSensor)
            else:
                log_error_msg("Error setting up Event Log Sensor")

        if Gb.WazeHistTrackSensor is None:
            Gb.WazeHistTrackSensor = SensorWazeHistTrack('iCloud3 Waze History Track', SENSOR_WAZEHIST_TRACK_NAME)
            if Gb.WazeHistTrackSensor:
                NewSensors.append(Gb.WazeHistTrackSensor)
            else:
                log_error_msg("Error setting up Waze History Track Sensor")

        # Create the selected sensors for each devicename
        # Cycle through each device being tracked or monitored and create it's sensors
        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            DeviceSensors = create_sensors(devicename, conf_device, Gb.conf_sensors_list)

            if DeviceSensors:
                NewSensors.extend(DeviceSensors)

        if NewSensors != []:
            async_add_entities(NewSensors, True)

        log_info_msg(f"Set up {len(NewSensors)} iCloud3 Sensors")

    except Exception as err:
        log_exception(err)
        log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
        log_error_msg(log_msg)

#--------------------------------------------------------------------
def create_sensors(devicename, conf_device, new_sensors_list=None, ):
    '''
        Add icloud3 sensors that have been selected via config_flow and
        arein the Gb.conf_sensors for each device
    '''

    try:
        NewSensors = []
        # if devicename_list is None:  devicename_list = []
        if new_sensors_list is None:
            new_sensors_list = Gb.conf_sensors_list

        # Cycle through each device being tracked or monitored and create it's sensors
        # for conf_device in Gb.conf_devices:
        #     devicename = conf_device[CONF_IC3_DEVICENAME]

            # if devicename_list and devicename not in devicename_list:
            #     continue

        devicename_sensors = Gb.Sensors_by_devicename.get(devicename, {})
        devicename_from_zone_sensors = Gb.Sensors_by_devicename_from_zone.get(devicename, {})
        # Cycle through the sensor definition names in the list of selected sensors,
        # Get the sensor entity name and create the sensor.[ic3_devicename]_[sensor_name] entity
        # The sensor_def name is the conf_sensor name set up in the Sensor_definition table.
        # The table contains the actual ha sensor entity name. That permits support for track-from-zone
        # suffixes.
        for sensor_def in new_sensors_list:
            Sensor      = None
            sensor      = SENSOR_DEFINITION[sensor_def][SENSOR_ENTITY]
            sensor_type = SENSOR_DEFINITION[sensor_def][SENSOR_TYPE]

            if sensor in devicename_sensors:
                # Sensor object might exist, use it to recreate the sensor entity
                _Sensor = devicename_sensors[sensor]
                if _Sensor.entity_removed_flag:
                    Sensor = _Sensor
                    log_info_msg(f"Reused Existing sensor.icloud3 entity: {Sensor.entity_id}")
                    Sensor.entity_removed_flag = False

            elif sensor_type.startswith('text'):
                Sensor = SensorText(devicename, sensor_def, conf_device)
            elif sensor_type.startswith('timestamp'):
                Sensor = SensorTimestamp(devicename, sensor_def, conf_device)
            elif sensor_type.startswith('timer'):
                Sensor = SensorTimer(devicename, sensor_def, conf_device)
            elif sensor_type.startswith('distance'):
                Sensor = SensorDistance(devicename, sensor_def, conf_device)
            elif sensor_type.startswith('zone'):
                Sensor = SensorZone(devicename, sensor_def, conf_device)
            elif sensor_type.startswith('info'):
                Sensor = SensorInfo(devicename, sensor_def, conf_device)
            elif sensor_type.startswith('battery'):
                Sensor = SensorBattery(devicename, sensor_def, conf_device)
            elif sensor_type.startswith('badge'):
                Sensor = SensorBadge(devicename, sensor_def, conf_device)

            if Sensor:
                devicename_sensors[sensor] = Sensor
                NewSensors.append(Sensor)
                continue

            # Track_from_zone related sensors
            for from_zone in conf_device[CONF_TRACK_FROM_ZONES]:
                Sensor = None
                sensor_zone = f"{sensor}_{from_zone}"

                # Sensor object might exist, use it to recreate the sensor entity
                if sensor_zone in devicename_from_zone_sensors:
                    _Sensor = devicename_from_zone_sensors[sensor_zone]
                    if _Sensor.entity_removed_flag:
                        Sensor = _Sensor
                        log_info_msg(f"Reused Existing sensor.icloud3 entity: {Sensor.entity_id}")
                        Sensor.entity_removed_flag = False

                elif instr(sensor_type ,'tfz_zoneinfo'):
                    Sensor = SensorTfzZoneInfo(devicename, sensor_def, conf_device, from_zone)
                elif sensor_type.startswith('tfz_text'):
                    Sensor = SensorText(devicename, sensor_def, conf_device, from_zone)
                elif sensor_type.startswith('tfz_timer'):
                    Sensor = SensorTimer(devicename, sensor_def, conf_device, from_zone)
                elif sensor_type.startswith('tfz_distance'):
                    Sensor = SensorDistance(devicename, sensor_def, conf_device, from_zone)

                if Sensor:
                    devicename_from_zone_sensors[sensor_zone] = Sensor
                    NewSensors.append(Sensor)

            Gb.Sensors_by_devicename[devicename] = devicename_sensors
            Gb.Sensors_by_devicename_from_zone[devicename] = devicename_from_zone_sensors

        return NewSensors

    except Exception as err:
        log_exception(err)
        log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
        log_error_msg(log_msg)



#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3SensorBase(SensorEntity):
    '''Representation of a iCloud device battery sensor.'''

    def __init__(self, devicename, sensor_def, conf_device, from_zone=None):
        '''Initialize the battery sensor.'''
        try:
            self.hass        = Gb.hass
            self.devicename  = devicename
            self.sensor_def  = sensor_def
            self.sensor_base = SENSOR_DEFINITION[sensor_def][SENSOR_ENTITY]
            self.from_zone   = from_zone
            if from_zone:
                self.from_zone_fname = f" ({from_zone.title().replace('_', '').replace(' ', '')})"
                self.sensor          = f"{self.sensor_base}_{self.from_zone}"
                restore_file_datagrp = f'from_zone_{self.from_zone}'
            else:
                self.from_zone_fname = ''
                self.sensor          = self.sensor_base
                restore_file_datagrp    = 'sensors'

            self.entity_name     = f"{devicename}_{self.sensor}"
            self.entity_id       = f"sensor.{self.entity_name}"
            self.device_id       = f"{DOMAIN}_{devicename}"

            self.Device          = Gb.Devices_by_devicename.get(devicename)
            if self.Device and from_zone:
                self.DeviceFmZone = Gb.Device.DeviceFmZones_by_zone.get(from_zone)
            else:
                self.DeviceFmZone = None

            self._attr_force_update = True
            self._unsub_dispatcher  = None
            self._on_remove         = [self.after_removal_cleanup]
            self.entity_removed_flag = False


            self.sensor_type     = self._get_sensor_definition(self.sensor_def, SENSOR_TYPE)
            self.sensor_type     = self.sensor_type.replace(' ', '')
            self.sensor_fname    = (f"{conf_device[FNAME]} "
                                    f"{self._get_sensor_definition(self.sensor_def, SENSOR_FNAME)}"
                                    f"{self.from_zone_fname}")
            self._attr_native_unit_of_measurement = ''

            self.default_value = self._get_sensor_definition(self.sensor_def, SENSOR_DEFAULT)
            try:
                self.default_value = Gb.restore_state_devices[self.devicename][restore_file_datagrp][self.sensor_base]
            except:
                pass


            self._state = self.default_value

        except Exception as err:
            log_exception(err)
            log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
            log_error_msg(log_msg)

#-------------------------------------------------------------------------------------------
    @property
    def unique_id(self):
        return f"{DOMAIN}_{self.entity_name}"

    @property
    def name(self):
        ''' Sensor friendly name '''
        return self.sensor_fname

    @property
    def devicename_sensor(self):
        '''Sensor friendly name.'''
        return f"{self.entity_id}_{self.sensor}"

    @property
    def icon(self):
        return self._get_sensor_definition(self.sensor_def, SENSOR_ICON)

    @property
    def device_info(self):
        return None

#-------------------------------------------------------------------------------------------
    @property
    def sensor_value(self):
        return self._get_sensor_value(self.sensor)

#-------------------------------------------------------------------------------------------
    def _get_extra_attributes(self, sensor_def):
        '''
        Get the extra attributes for the sensor defined in the
        SENSOR_DEFINITION dictionary
        '''
        # Resolve sensor definition table sensor name for tfz sensors where 'tfz_' was stripped off
        sensors = self._get_sensor_definition(sensor_def, SENSOR_ATTRS)
        extra_attrs = {}
        for sensor in sensors:
            sensor_value = self._get_sensor_value(sensor)

            # Interval sensor may end in -5s or -15s. if so, strip it off attr value
            if (sensor == INTERVAL and sensor_value.endswith('s')):
                datetime_parts = sensor_value.split('-')

            extra_attrs[sensor] = sensor_value

        return extra_attrs

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _get_sensor_definition(sensor_def, field):
        try:
            return SENSOR_DEFINITION[sensor_def][field]

        except:
            if field == SENSOR_ATTRS:
                return []
            else:
                return ''

#-------------------------------------------------------------------------------------------
    @property
    def sensor_not_set(self):
        sensor_value = self._get_sensor_value(self.sensor)

        if self.Device is None:
            return True

        if (type(sensor_value) is str
                and (sensor_value.startswith('___')
                    or sensor_value.strip() == ''
                    or sensor_value == HHMMSS_ZERO
                    or sensor_value == DATETIME_ZERO
                    or sensor_value == NOT_SET
                    or sensor_value == NOT_SET_FNAME)):
            return True
        else:
            return False

#-------------------------------------------------------------------------------------------
    def _get_sensor_value(self, sensor):
        '''
        Get the sensor value from:
            - Device's attributes/sensor
            - Device's DeviceFmZone attributes/sensors for a zone
        '''

        if self.from_zone:
            return self._get_tfz_sensor_value(sensor)
        else:
            return self._get_device_sensor_value(sensor)

#-------------------------------------------------------------------------------------------
    def _get_device_sensor_value(self, sensor):
        '''
        Get the sensor value from:
            - Device's attributes/sensor
            - Device's DeviceFmZone attributes/sensors for a zone
        '''

        try:
            if self.Device is None:
                return self.default_value

            sensor_value = self.Device.sensors.get(sensor, None)

            if (sensor_value is None
                    or sensor_value == NOT_SET
                    or type(sensor_value) is str and sensor_value.strip() == ''):
                return self.default_value

            return sensor_value

        except Exception as err:
            log_exception(err)
            return self.default_value

#-------------------------------------------------------------------------------------------
    def _get_tfz_sensor_value(self, sensor):
        '''
        Get the sensor value from:
            - Device's DeviceFmZone attributes/sensors for a zone
        '''
        try:
            if (self.Device is None
                    or self.DeviceFmZone is None):
                return self.default_value

            # Strip off zone to get the actual tfz dictionary item
            tfz_sensor   = sensor.replace(f"_{self.from_zone}", "")
            sensor_value = self.DeviceFmZone.sensors.get(tfz_sensor, None)

            if (sensor_value is None
                    or sensor_value == NOT_SET
                    or (type(sensor_value) is str and sensor_value.strip() == '')):
                return self.default_value

            return sensor_value

        except Exception as err:
            log_exception(err)
            return self.default_value

#-------------------------------------------------------------------------------------------
    def _get_sensor_value_um(self, sensor, value_and_um=True):
        '''
            Get the sensor value and determine if it has a value and unit_of_measurement.

            Return:
                um specified:
                    [sensor_value, um]
                um not specified (value only):
                    [sensor_value, None]
        '''
        sensor_value = self._get_sensor_value(sensor)

        try:
            if instr(sensor_value, ' '):
                value_um_parts = sensor_value.split(' ')
                return float(value_um_parts[0]), value_um_parts[1]

            elif self.sensor_not_set:
                return sensor_value, None

            else:
                return float(sensor_value), None

        except ValueError:
            return sensor_value, None

        except Exception as err:
            log_exception(err)
            return sensor_value, None

#-------------------------------------------------------------------------------------------
    def _get_sensor_um(self, sensor):
        '''
        Get the sensor's special um override value from:
            - Device's sensors_um dictionary
            - Device's DeviceFmZone sensors_um dictionary for a zone
        '''
        try:
            if self.Device is None:
                return None

            if self.from_zone and self.DeviceFmZone is None:
                return None

            elif self.from_zone is None:
                sensor_um = self.Device.sensors_um.get(sensor, None)

            elif self.from_zone and self.DeviceFmZone:
                sensor_um = self.DeviceFmZone.sensors_um.get(sensor, None)

        except:
            sensor_um = None

        return sensor_um

#-------------------------------------------------------------------------------------------
    @property
    def should_poll(self):
        ''' Do not poll to update the sensor '''
        return False

#-------------------------------------------------------------------------------------------
    def update_entity_attribute(self, new_fname=None):
        """ Update entity definition attributes """

        if new_fname is None:
            return

        entity_registry   = er.async_get(Gb.hass)
        self.sensor_fname = (f"{new_fname} "
                            f"{self._get_sensor_definition(self.sensor_def, SENSOR_FNAME)}"
                            f"{self.from_zone_fname}")

        kwargs = {}
        kwargs['original_name'] = self.sensor_fname
        entity_registry.async_update_entity(self.entity_id, **kwargs)


        """
            Typically used:
                name: str | None | UndefinedType = UNDEFINED,
                new_entity_id: str | UndefinedType = UNDEFINED,
                device_id: str | None | UndefinedType = UNDEFINED,
                original_name: str | None | UndefinedType = UNDEFINED,

            Not used:
                area_id: str | None | UndefinedType = UNDEFINED,
                capabilities: Mapping[str, Any] | None | UndefinedType = UNDEFINED,
                config_entry_id: str | None | UndefinedType = UNDEFINED,
                device_class: str | None | UndefinedType = UNDEFINED,
                disabled_by: RegistryEntryDisabler | None | UndefinedType = UNDEFINED,
                entity_category: EntityCategory | None | UndefinedType = UNDEFINED,
                hidden_by: RegistryEntryHider | None | UndefinedType = UNDEFINED,
                icon: str | None | UndefinedType = UNDEFINED,
                new_unique_id: str | UndefinedType = UNDEFINED,
                original_device_class: str | None | UndefinedType = UNDEFINED,
                original_icon: str | None | UndefinedType = UNDEFINED,
                supported_features: int | UndefinedType = UNDEFINED,
                unit_of_measurement: str | None | UndefinedType = UNDEFINED,
    """

#-------------------------------------------------------------------------------------------
    def remove_entity(self):
        try:
            Gb.hass.async_create_task(self.async_remove(force_remove=True))

        except Exception as err:
            _LOGGER.exception(err)

#-------------------------------------------------------------------------------------------
    def after_removal_cleanup(self):
        """ Cleanup sensor after removal

        Passed in the `self._on_remove` parameter during initialization
        and called by HA after processing the async_remove request
        """

        log_info_msg(f"Registered sensor.icloud3 entity removed: {self.entity_id}")

        self._remove_from_registries()
        self.entity_removed_flag = True

        if self.Device is None:
            return

        if self.Device.Sensors_from_zone and self.sensor in self.Device.Sensors_from_zone:
            self.Device.Sensors_from_zone.pop(self.sensor)

        if self.Device.Sensors and self.sensor in self.Device.Sensors:
            self.Device.Sensors.pop(self.sensor)

#-------------------------------------------------------------------------------------------
    def _remove_from_registries(self) -> None:
        """ Remove entity/device from registry """

        if not self.registry_entry:
            return

        # if self.entity_id == self.registry_entry.entity_id:
        if entity_id := self.registry_entry.entity_id:
            entity_registry = er.async_get(Gb.hass)
            if entity_id in entity_registry.entities:
                entity_registry.async_remove(self.entity_id)

#-------------------------------------------------------------------------------------------
    def __repr__(self):
        return (f"<Sensor: {self.entity_name}>")

#-------------------------------------------------------------------------------------------
    def async_update_sensor(self):
        """Update the entity's state."""
        try:
            self.async_write_ha_state()

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def async_update_info_sensor(self):
        """Update the info sensor entity's state."""
        try:
            self.async_write_ha_state()

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    async def async_added_to_hass(self):
        '''Register state update callback.'''
        self._unsub_dispatcher = async_dispatcher_connect(
                                        self.hass,
                                        signal_device_update,
                                        self.async_write_ha_state)

#-------------------------------------------------------------------------------------------
    async def async_will_remove_from_hass(self):
        '''Clean up after entity before removal.'''
        self._unsub_dispatcher()


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorBadge(iCloud3SensorBase):
    '''  Sensor for displaying the device badge items '''

    @property
    def native_value(self):

        return  self._get_sensor_value(BADGE)

    @property
    def extra_state_attributes(self):
        if self.Device:
            return self.Device.sensor_badge_attrs.copy()
        else:
            return None


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorTfzZoneInfo(iCloud3SensorBase):
    '''  Sensor for displaying the device zone time/distance items '''

    @property
    def native_value(self):
        self._attr_unit_of_measurement = None

        if (self.Device is None
                or self.DeviceFmZone is None):
            return self.default_value

        if self.Device.is_inzone:
            if self.Device.sensors[ZONE] != self.from_zone:
                zone = self.Device.sensors[ZONE]
                return Gb.Zones_by_zone[zone].display_as
            else:
                return 'In Zone'

        else:
            self._attr_unit_of_measurement = Gb.um
            return self.DeviceFmZone.sensors[ZONE_DISTANCE]

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor_def)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorText(iCloud3SensorBase):
    '''  Sensor for handling text items '''

    @property
    def native_value(self):
        sensor_value = self._get_sensor_value(self.sensor)

        if instr(self.sensor_type, 'title'):
            sensor_value = sensor_value.title().replace('_', ' ')

        elif instr(self.sensor_type, 'time'):
            if instr(sensor_value, ' '):
                text_um_parts = sensor_value.split(' ')
                sensor_value = text_um_parts[0]
                self._attr_unit_of_measurement = text_um_parts[1]
            else:
                self._attr_unit_of_measurement = None

        # Set to space if empty
        if sensor_value.strip() == '':
            sensor_value = ' '

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor_def)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorInfo(iCloud3SensorBase):
    '''
        Sensor for handling info sensor messages.
            1.  This will update a specific Device's info sensor using the
                Device.update_info_message('msg') function.
                broadcase_info_msg('msg') function in base.py by entering the
                message into the 'Gb.broadcast_info_msg' field. This lets you display
                an info message during startup before the devices have been created
                or to everyone as a general notification.
    '''

    @property
    def native_value(self):
        self._attr_unit_of_measurement = None

        if Gb.broadcast_info_msg and Gb.broadcast_info_msg != '•  ':
            return Gb.broadcast_info_msg

        elif self.sensor_not_set:
            return f"{DOT} Starting iCloud3 Device Tracker"

        else:
            return self.sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor_def)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorTimestamp(iCloud3SensorBase):
    '''
    Sensor for handling timestamp (mm/dd/yy hh:mm:ss) items
    Sensors: last_update_time, next_update_time, last_located
    '''

    @property
    def native_value(self):
        sensor_value = self._get_sensor_value(f"{self.sensor}")
        sensor_um    = self._get_sensor_um(f"{self.sensor}")
        self._attr_unit_of_measurement = sensor_um
        sensor_value = time_to_12hrtime(sensor_value)

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor_def)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorTimer(iCloud3SensorBase):
    '''
    Sensor for handling timer items (30 secs, 1.5 hrs, 30 mins)
    Sensors: inteval, travel_time, travel_time_mins
    '''

    @property
    def native_value(self):

        if instr(self.sensor_type, ','):
            sensor_type_um = self.sensor_type.split(',')[1]
        else:
            sensor_type_um = ''

        sensor_value, unit_of_measurement = self._get_sensor_value_um(self.sensor)

        if unit_of_measurement:
            self._attr_native_unit_of_measurement = unit_of_measurement

        elif sensor_type_um == 'min':
            time_str = mins_to_time_str(sensor_value)
            if time_str and instr(time_str, 'd') is False:         # Make sure it is not a 4d2h34m12s item
                time_min_hrs = time_str.split(' ')
                sensor_value = time_min_hrs[0]
                self._attr_native_unit_of_measurement = time_min_hrs[1]

        elif sensor_type_um == 'sec':
            time_str = secs_to_time_str(sensor_value)
            if time_str and instr(time_str, 'd') is False:       # Make sure it is not a 4d2h34m12s item
                time_secs_min_hrs = time_str.split(' ')
                sensor_value = time_secs_min_hrs[0]
                self._attr_native_unit_of_measurement = time_secs_min_hrs[1]

        else:
            self._attr_native_unit_of_measurement = 'min'

        try:
            # Try to convert sensor_value to integer. Just return it if it fails.
            if sensor_value != '___':
                if sensor_value == int(sensor_value):
                    sensor_value = int(sensor_value)
        except Exception as err:
            log_exception(err)
            pass

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor_def)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorDistance(iCloud3SensorBase):
    '''
    Sensor for handling timer items (30 secs, 1.5 hrs, 30 mins)
    Sensors: inteval, travel_time, travel_time_mins
    '''

    @property
    def native_value(self):
        if instr(self.sensor_type, ','):
            sensor_type_um = self.sensor_type.split(',')[1]

        sensor_value, unit_of_measurement = self._get_sensor_value_um(self.sensor)

        if unit_of_measurement:
            self._attr_native_unit_of_measurement = unit_of_measurement
        elif sensor_type_um == 'm-ft':
            self._attr_native_unit_of_measurement = Gb.um_m_ft
        elif sensor_type_um == 'km-mi':
            self._attr_native_unit_of_measurement = Gb.um
        elif sensor_type_um == 'm':
            self._attr_native_unit_of_measurement = 'm'
        else:
            self._attr_native_unit_of_measurement = Gb.um

        from_zone_msg = self._get_sensor_um(self.sensor)
        if from_zone_msg:
            self._attr_native_unit_of_measurement += f"{from_zone_msg}"

        try:
            if sensor_value == int(sensor_value):
                sensor_value = int(sensor_value)
        except:
            pass

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor_def)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorBattery(iCloud3SensorBase):
    '''
    Sensor for handling battery items (30s)
    Sensors: battery
    '''

    @property
    def native_value(self):
        return self._get_sensor_value(f"{self.sensor}")

    @property
    def extra_state_attributes(self):
        extra_attrs = {}
        if self.Device:
            extra_attrs[ICON] = icon_for_battery_level(
                            battery_level = self.Device.sensors[BATTERY],
                            charging      = (self.Device.sensors[BATTERY_STATUS] == "Charging"))
        else:
            extra_attrs[ICON] = 'mdi:battery-outline'

        return extra_attrs


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorZone(iCloud3SensorBase):
    '''
    Sensor for handling zone items
    Sensors:
        zone, zone_name, zone_fname,
        last_zone, last_zone_name, last_zone_fname

    zone or last_zone sensor:
        Attributes = zone_name & zone_fname
    zone_name, zone_fname, last_zone_name, last_zone_fname:
        Attributes = zone
    '''

    @property
    def native_value(self):
        sensor_value = self._get_sensor_value(f"{self.sensor}")

        if self.sensor.endswith(ZONE):
            return sensor_value

        zone = self._get_sensor_value(ZONE)
        Zone = Gb.Zones_by_zone.get(zone, None)
        if Zone is None:
            pass
        elif self.sensor.endswith(FNAME):
            sensor_value = Zone.fname
        else:
            sensor_value = Zone.name

        return sensor_value

    @property
    def extra_state_attributes(self):
        extra_attrs = {}
        zone = self._get_sensor_value(ZONE)
        Zone = Gb.Zones_by_zone.get(zone, None)

        if Zone is None:
            pass
        elif self.sensor.endswith(ZONE):
            extra_attrs[NAME]  = Zone.name
            extra_attrs[FNAME] = Zone.fname
        else:
            extra_attrs[ZONE] = Zone.zone

        return extra_attrs

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3SupportiCloud3SensorBase(SensorEntity):
    ''' iCloud Support Sensor Base
        - Event Log
        - Waze History Track
    '''

    def __init__(self, fname, entity_name):
        '''Initialize the Event Log sensor (icloud3_event_log).'''
        self.fname             = fname
        self.sensor            = entity_name
        self.entity_name       = entity_name
        self.entity_id         = f"sensor.{self.entity_name}"
        self._unsub_dispatcher = None

    @property
    def name(self):
        '''Sensor friendly name.'''
        return self.fname

    @property
    def unique_id(self):
        return self.entity_name

    @property
    def device_info(self):
        return None

#-------------------------------------------------------------------------------------------
    def __repr__(self):
        return (f"<DeviceSensor: {self.entity_name}>")

    @property
    def should_poll(self):
        ''' Do not poll to update the sensor '''
        return False

#-------------------------------------------------------------------------------------------
    def async_update_sensor(self):
        """Update the entity's state."""
        try:
            self.async_write_ha_state()
        except Exception as err:
            log_exception(err)

    async def async_added_to_hass(self):
        '''Register state update callback.'''
        self._unsub_dispatcher = async_dispatcher_connect(
                                        self.hass,
                                        signal_device_update,
                                        self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        '''Clean up after entity before removal.'''
        self._unsub_dispatcher()


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorEventLog(iCloud3SupportiCloud3SensorBase):

    @property
    def icon(self):
        return 'mdi:message-text-clock-outline'

    @property
    def native_value(self):
        '''State value - (devicename_time)'''
        try:
            return Gb.EvLog.evlog_state_attr
        except:
            return 'unavailable'

    @property
    def extra_state_attributes(self):
        '''Return default attributes for the iCloud device entity.'''
        log_update_time = ( f"{dt_util.now().strftime('%a, %m/%d')}, "
                            f"{dt_util.now().strftime(Gb.um_time_strfmt)}")

        if Gb.EvLog:
            return Gb.EvLog.log_attrs

        return {'log_level_debug': '',
                'filtername': 'Initialize',
                'update_time': log_update_time,
                'names': {'Loading': 'Initializing iCloud3'},
                'logs': '',
                'platform': Gb.operating_mode}


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class SensorWazeHistTrack(iCloud3SupportiCloud3SensorBase):
    '''iCloud Waze History Track GPS Values Sensor.'''

    @property
    def icon(self):
        return 'mdi:map-check-outline'

    @property
    def native_value(self):
        '''State value - (latitude, longitude)'''
        if Gb.WazeHist is None:
            return None

        return f"{Gb.WazeHist.track_latitude}, {Gb.WazeHist.track_longitude}"

    @property
    def extra_state_attributes(self):
        '''Return default attributes for the iCloud device entity.'''
        if Gb.WazeHist is None:
            return None

        return {'latitude': Gb.WazeHist.track_latitude,
                'longitude': Gb.WazeHist.track_longitude,
                'friendly_name': 'WazeHist'}


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><
