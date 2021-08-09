"""
Allow Home Assistant to save the state of an entity and restore that state after power loss or home assistant restart

For more details about this platform, please refer to the documentation at
https://github.com/gazoscalvertos/HASS-persistence
"""
import asyncio
import logging
import json
import os
import pytz
import time

from datetime                                  import timedelta

import voluptuous                              as vol
import requests

from homeassistant.components.sensor           import PLATFORM_SCHEMA
from homeassistant.const                       import (EVENT_STATE_CHANGED, EVENT_TIME_CHANGED)
from homeassistant.helpers.entity              import Entity
from homeassistant.helpers.event               import async_track_state_change

import homeassistant.helpers.config_validation as cv

#from homeassistant.util import Throttle
#from homeassistant.helpers.event import track_time_interval

_LOGGER = logging.getLogger(__name__)

#-----------------YAML CONFIG OPTIONS----------------------------------
CONF_ENTITIES = 'entities'
CONF_DOMAINS  = 'domains'
#----------------------------------------------------------------------

ICON = 'mdi:save'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
	vol.Optional(CONF_ENTITIES): cv.entity_ids,
    vol.Optional(CONF_DOMAINS):  cv.entity_ids,
})

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the persistense sensor."""
    persistence = PersistenceSensor(hass, config)
    hass.bus.async_listen(EVENT_TIME_CHANGED, persistence.persistence_load)
    hass.bus.async_listen(EVENT_STATE_CHANGED, persistence.state_change_listener)
    async_add_devices([persistence])

class PersistenceSensor(Entity):
    """Implementation of the sensor."""

    def __init__(self, hass, config):
        """Initialize the sensor."""

        self._entities          = set(config.get(CONF_ENTITIES, []))
        self._domains           = set(config.get(CONF_DOMAINS, []))
        self._hass              = hass
        self._initialised       = False

        self._persistence_list  = []
        persistence_path        = hass.config.path()

        if not os.path.isdir(persistence_path):
           _LOGGER.error("[Persistence] path %s does not exist.", persistence_path)
        else:
           self._persistence_final_path = os.path.join(persistence_path, "persistence.json")

    ### LOAD persistence previously saved
    def persistence_load(self, event):
        if self._initialised == False:  #Only run this once
            try:
               if os.path.isfile(self._persistence_final_path):  #Find the persistence JSON file and load. Once found update the entities
                   self._persistence_list = json.load(open(self._persistence_final_path, 'r'))
                   for key,val in self._persistence_list.items():
                       self._hass.states.set(key, val)
                       _LOGGER.debug("%s=>%s", key, val)
               else: #No persistence file found
                   _LOGGER.warning("[Persistence] file doesnt exist")
                   self._persistence_list = json.loads('{}')

            except Exception as e:
               _LOGGER.error("[Persistence] Error occured loading: %s", str(e))
            self._initialised = True

    ### UPDATE persistence
    def persistence_save(self):
        if self._persistence_list is not None: #Check we have something to save
            try:
               with open(self._persistence_final_path, 'w') as fil:
                  fil.write(json.dumps(self._persistence_list, ensure_ascii=False))
            except Exception as e:
               _LOGGER.error("[Persistence] Error occured saving: %s", str(e))

    def state_change_listener(self, event):
        """ Something changed, check to see if our entities changed, if so save the state to file """
        if event.data['entity_id'] in self._entities:
           self._persistence_list[event.data['entity_id']] = event.data.get('new_state', None).state
           self.persistence_save()

    @property
    def name(self):
        """Return the name of the item."""
        return "persistence"

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return ICON

    @property
    def state(self):
        """Return a dummy state."""
        return "enabled"

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {
	        'entities':  self._entities,
	        'domains':   self._domains,
        }
        return attrs
