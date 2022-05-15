"""Support for tracking for iCloud devices."""

from .global_variables  import GlobalVariables as Gb
from .const             import (NOT_SET, NOT_SET_FNAME, DATETIME_ZERO, HHMMSS_ZERO, PAUSED_CAPS, HIGH_INTEGER, RARROW2,
                                DOMAIN, MODE_PLATFORM, HOME,
                                TRAVEL_DISTANCE, TRIGGER, BATTERY, BATTERY_STATUS, GPS_ACCURACY, VERT_ACCURACY,

                                CONF_IC3_DEVICENAME, FNAME, CONF_DEVICE_TYPE, CONF_PICTURE,
                                CONF_TRACK_FROM_ZONES,

                                ICLOUD3_EVENT_LOG,
                                LATITUDE, LONGITUDE, DEVTRK_STATE_VALUE,
                                NAME, BADGE, BATTERY, DATA_SOURCE, PICTURE,
                                TRIGGER, INTERVAL, LOCATION_SOURCE,
                                ZONE_DATETIME,
                                LAST_UPDATE_DATETIME, LAST_UPDATE_TIME, LAST_UPDATE,
                                NEXT_UPDATE_DATETIME, NEXT_UPDATE_TIME, NEXT_UPDATE,
                                LAST_LOCATED_DATETIME, LAST_LOCATED_TIME, LAST_LOCATED,
                                TRAVEL_TIME, TRAVEL_TIME_MIN,
                                DISTANCE, ZONE_DISTANCE, HOME_DISTANCE, WAZE_DISTANCE,
                                CALC_DISTANCE, TRAVEL_DISTANCE, GPS_ACCURACY,
                                DIR_OF_TRAVEL, ZONE, ZONE_FNAME,
                                ZONE_NAME, ZONE_DATETIME, FROM_ZONE,
                                POLL_COUNT, INFO, LAST_ZONE, LAST_ZONE_FNAME,
                                LAST_ZONE_NAME,
                                BATTERY_STATUS, ALTITUDE, VERTICAL_ACCURACY,
                                )

from .helpers.base      import (instr, isnumber, post_event, post_error_msg, post_log_info_msg, post_monitor_msg,
                                signal_device_update,
                                log_info_msg, log_error_msg, log_exception, _trace, _traceha, )
from .support           import start_ic3

# from __future__ import annotations

from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries       import ConfigEntry
from homeassistant.core                 import HomeAssistant, callback
from homeassistant.helpers.dispatcher   import async_dispatcher_connect
from homeassistant.helpers              import entity_registry as er, device_registry as dr

import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

async def async_setup_scanner(hass: HomeAssistant, config, see, discovery_info=None):
    """Old way of setting up the iCloud tracker."""
    _LOGGER.warning("Device Tracker PLATFORM async_setup_scanner")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up iCloud3 device tracker component."""
    # Save the hass `add_entities` call object for use in config_flow for adding devices
    Gb.async_add_entities_device_tracker = async_add_entities

    try:
        if Gb.conf_file_data == {}:
            Gb.hass = hass
            start_ic3.initialize_directory_filenames()
            start_ic3.load_storage_icloud3_configuration_file()

        NewDeviceTrackers = []
        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]

            if devicename in Gb.DeviceTrackers_by_devicename:
                continue

            DeviceTracker = iCloud3DeviceTracker(devicename, conf_device)

            if DeviceTracker:
                Gb.DeviceTrackers_by_devicename[devicename] = DeviceTracker
                NewDeviceTrackers.append(DeviceTracker)

        if NewDeviceTrackers is not []:
            async_add_entities(NewDeviceTrackers, True)

        log_info_msg(f"Set up {len(NewDeviceTrackers)} iCloud3 device_trackers > {NewDeviceTrackers}")

    except Exception as err:
        _LOGGER.exception(err)
        log_exception(err)
        log_msg = f"►INTERNAL ERROR (Create device_tracker loop-{err})"
        log_error_msg(log_msg)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3DeviceTracker(TrackerEntity):
    """iCloud3 device_tracker entity definition."""

    def __init__(self, devicename, conf_device):
        """Set up the iCloud3 device_tracker entity."""

        try:
            self.hass         = Gb.hass
            self.devicename   = devicename
            self.entity_id    = f"device_tracker.{devicename}"
            self.device_id    = f"{DOMAIN}_{devicename}"
            self.device_fname = conf_device[FNAME]
            self.device_type  = conf_device[CONF_DEVICE_TYPE]


            self.Device = None
            try:
                self.default_value = Gb.restore_state_devices[devicename]['sensors'][ZONE]
            except:
                self.default_value = '___'
            self._state = self.default_value

            self._attr_force_update = True
            self._unsub_dispatcher  = None
            self._on_remove         = [self.after_removal_cleanup]
            self.entity_removed_flag = False


        except Exception as err:
            log_exception(err)
            log_msg = f"►INTERNAL ERROR (Create device_tracker object-{err})"
            log_error_msg(log_msg)

#-------------------------------------------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{DOMAIN}_{self.devicename}"

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self.device_fname

    @property
    def location_name(self):
        """Return the location name of the device."""
        try:
            if self.state_value_not_set:
                return self.default_value

            return self._get_sensor_value(DEVTRK_STATE_VALUE)
        except:
            return self.default_value

    @property
    def location_accuracy(self):
        """Return the location accuracy of the device."""
        return self._get_sensor_value(GPS_ACCURACY, number=True)

    @property
    def latitude(self):
        """Return latitude value of the device."""
        return self._get_sensor_value(LATITUDE, number=True)

    @property
    def longitude(self):
        """Return longitude value of the device."""
        return self._get_sensor_value(LONGITUDE, number=True)

    @property
    def battery_level(self):
        """Return the battery level of the device."""
        return self._get_sensor_value(BATTERY, number=True)

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return f"{SOURCE_TYPE_GPS}/{self._get_sensor_value(LOCATION_SOURCE)}"

    @property
    def icon(self):
        """Return an icon based on the type of the device."""
        device_type_icons = {
            "iphone": "mdi:cellphone",
            "ipad": "mdi:tablet",
            "ipod": "mdi:ipod",
            "airpods": "mdi:earbuds",
            "watch": "mdi:watch-variant",
        }
        return device_type_icons.get(self.device_type, "mdi:cellphone")

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        return self._get_extra_attributes()

    @property
    def device_info(self):
        """Return the device information."""
        device_fname_type = f"{self.device_fname}/{self.device_type}"
        return {
            "identifiers":  {(DOMAIN, device_fname_type)},
            "name": self.devicename,
            "manufacturer": "Apple",
            "model": self.device_type,
            "id": self.devicename}

#-------------------------------------------------------------------------------------------
    def _get_extra_attributes(self):
        '''
        Get the extra attributes for the device_tracker
        '''
        try:
            extra_attrs = {}

            extra_attrs[NAME]                  = self._get_sensor_value(NAME)
            extra_attrs[PICTURE]               = self._get_sensor_value(PICTURE)
            extra_attrs[ZONE]                  = self._get_sensor_value(ZONE)
            extra_attrs[LAST_ZONE]             = self._get_sensor_value(LAST_ZONE)
            extra_attrs[ZONE_DATETIME]         = self._get_sensor_value(ZONE_DATETIME)
            extra_attrs[LAST_LOCATED_DATETIME] = self._get_sensor_value(LAST_LOCATED_DATETIME)
            extra_attrs[LAST_UPDATE_DATETIME]  = self._get_sensor_value(LAST_UPDATE_DATETIME)
            extra_attrs[NEXT_UPDATE_DATETIME]  = self._get_sensor_value(NEXT_UPDATE_DATETIME)
            extra_attrs[TRIGGER]               = self._get_sensor_value(TRIGGER)
            extra_attrs[FROM_ZONE]             = self._get_sensor_value(FROM_ZONE)
            extra_attrs[WAZE_DISTANCE]         = self._get_sensor_value(WAZE_DISTANCE)
            extra_attrs[CALC_DISTANCE]         = self._get_sensor_value(CALC_DISTANCE)
            extra_attrs[HOME_DISTANCE]         = self._get_sensor_value(HOME_DISTANCE)

            extra_attrs['icloud3_version']     = Gb.version
            extra_attrs['event_log_version']   = Gb.version_evlog
            extra_attrs['tracking']            = ', '.join(Gb.Devices_by_devicename.keys())
            extra_attrs['icloud3_directory']   = Gb.icloud3_directory

            return extra_attrs

        except Exception as err:
            log_exception(err)
            log_error_msg(f"►INTERNAL ERROR (Create device_tracker object-{err})")

#-------------------------------------------------------------------------------------------
    def _get_sensor_value(self, sensor, number=False):
        '''
        Get the sensor value from Device's /sensor
        '''
        try:
            not_set_value = 0 if number else '___'

            if self.Device is None:
                return not_set_value

            sensor_value = self.Device.sensors.get(sensor, None)
            number = isnumber(sensor_value)
            if number is False:
                if sensor_value is None or sensor_value.strip() == '' or sensor_value == NOT_SET:
                    sensor_value = '___'

        except Exception as err:
            log_exception(err)
            log_error_msg(f"►INTERNAL ERROR (Create device_tracker object-{err})")
            sensor_value = not_set_value

        return sensor_value

#-------------------------------------------------------------------------------------------
    def _get_attribute_value(self, attribute):
        '''
        Get the attribute value from Device's attributes
        '''
        try:
            if self.Device is None:
                return 0

            attr_value = self.Device.attrs.get(attribute, None)

            if attr_value is None or attr_value.strip() == '' or attr_value == NOT_SET:
                attr_value = 0

        except:
            attr_value = 0

        return attr_value

#-------------------------------------------------------------------------------------------
    @property
    def state_value_not_set(self):
        state_value = self._get_sensor_value(DEVTRK_STATE_VALUE)

        if self.Device is None:
            return True

        if (type(state_value) is str
                and (state_value.startswith('___')
                    or state_value.strip() == ''
                    or state_value == NOT_SET
                    or state_value == NOT_SET_FNAME)):
            return True
        else:
            return False

#-------------------------------------------------------------------------------------------
    def update_entity_attribute(self, new_fname=None):
        """ Update entity definition attributes """

        if new_fname is None:
            return

        entity_registry   = er.async_get(Gb.hass)
        self.device_fname = new_fname

        kwargs = {}
        kwargs['original_name'] = self.device_fname

        entity_registry.async_update_entity(self.entity_id, **kwargs)

        """
            Typically used:
                original_name: str | None | UndefinedType = UNDEFINED,

            Not used:
                area_id: str | None | UndefinedType = UNDEFINED,
                capabilities: Mapping[str, Any] | None | UndefinedType = UNDEFINED,
                config_entry_id: str | None | UndefinedType = UNDEFINED,
                device_class: str | None | UndefinedType = UNDEFINED,
                device_id: str | None | UndefinedType = UNDEFINED,
                disabled_by: RegistryEntryDisabler | None | UndefinedType = UNDEFINED,
                entity_category: EntityCategory | None | UndefinedType = UNDEFINED,
                hidden_by: RegistryEntryHider | None | UndefinedType = UNDEFINED,
                icon: str | None | UndefinedType = UNDEFINED,
                name: str | None | UndefinedType = UNDEFINED,
                new_entity_id: str | UndefinedType = UNDEFINED,
                new_unique_id: str | UndefinedType = UNDEFINED,
                original_device_class: str | None | UndefinedType = UNDEFINED,
                original_icon: str | None | UndefinedType = UNDEFINED,
                supported_features: int | UndefinedType = UNDEFINED,
                unit_of_measurement: str | None | UndefinedType = UNDEFINED,
    """

#-------------------------------------------------------------------------------------------
    def remove_device_tracker(self):
        try:
            Gb.hass.async_create_task(self.async_remove(force_remove=True))

        except Exception as err:
            _LOGGER.exception(err)

#-------------------------------------------------------------------------------------------
    def after_removal_cleanup(self):
        """ Cleanup device_tracker after removal

        Passed in the `self._on_remove` parameter during initialization
        and called by HA after processing the async_remove request
        """

        log_info_msg(f"Registered device_tracker.icloud3 entity removed: {self.entity_id}")

        self._remove_from_registries()
        self.entity_removed_flag = True

        if self.Device is None:
            return

        if self.Device.Sensors_from_zone and self.devicename in self.Device.Sensors_from_zone:
            self.Device.Sensors_from_zone.pop(self.devicename)

        if self.Device.Sensors and self.devicename in self.Device.Sensors:
            self.Device.Sensors.pop(self.devicename)

#-------------------------------------------------------------------------------------------
    def _remove_from_registries(self) -> None:
        """ Remove entity/device from registry """

        if not self.registry_entry:
            return

        if device_id := self.registry_entry.device_id:
            # Remove from device registry.
            device_registry = dr.async_get(self.hass)
            if device_id in device_registry.devices:
                device_registry.async_remove_device(device_id)

        if entity_id := self.registry_entry.entity_id:
            entity_registry = er.async_get(Gb.hass)
            if entity_id in entity_registry.entities:
                entity_registry.async_remove(entity_id)

#-------------------------------------------------------------------------------------------
    def __repr__(self):
        return (f"<DeviceTracker: {self.devicename}/{self.device_type}>")

#-------------------------------------------------------------------------------------------
    def async_update_device_tracker(self):
        """Update the entity's state."""
        try:
            self.async_write_ha_state()

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    async def async_added_to_hass(self):
        """Register state update callback."""
        self._unsub_dispatcher = async_dispatcher_connect(
                                        self.hass,
                                        signal_device_update,
                                        self.async_write_ha_state)

#-------------------------------------------------------------------------------------------
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        self._unsub_dispatcher()
