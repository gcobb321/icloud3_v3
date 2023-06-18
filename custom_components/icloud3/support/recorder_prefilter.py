#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   HA RECORDER - EXCLUDE SENSORS FROM BEING ADDED TO HISTORY DATABASE
#
#
#   The HA Recorder module was modified in HA 2023.6.0 to no longer allow a custom
#   component to insert sensor entity names in the '_exclude_e' list that defined
#   sensor entities to not be added to the History database (home_assistant_v2.db).
#
#   This module fixes that problem by using a code injection process to provide a
#   local prefilter to determine if an entity should be added before the Recorder filter.
#
#   Generally, it does the following:
#       1. Define the filter to be injected into the Recorder (entity_prefilter)
#       2. Get the Recorder instance from the ha data.
#       3. Get the entity_filter and _event_listener functions.
#       4. Inject the local filter function (entity_prefilter) into the Recorder.
#       5. Remove the Recorder that listener for event/state changes.
#       6. Reinitialize the Recorder listener to link to the local prefilter.
#
#   Entity id checking is done using the 'entity_prefilter' function.
#       If it should be filtered:
#           - return False
#       It it is not in the local filter list,
#           - return using the original Recorder entity filter
#
#   This injection should be done at the beginining of the  '__init__.py/def async_setup'
#   function before the filtered sensors have been initialized and set up.
#
#   Example Setup Code in __init__.py:
#       import recorder_prefilter
#
#       async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
#           ....
#
#           Other Code
#
#           ....
#
#           recorder_prefilter.add_prefilter(hass, sensors)
#           - or -
#           recorder_prefilter.add_prefilter(hass, ['new_sensor1', 'new_sensor2', '*_sensor_glob1'])
#
#   Sensors can be added to the filtered list at a later time using the update_filter
#   function.
#
#   Examples:
#       recorder_prefilter.update_prefilter(sensorargument)
#       recorder_prefilter.update_prefilter(['new_sensor3', 'new_sensor4', '*_sensor_glob2'])
#       recorder_prefilter.update_prefilter('new_sensor5')
#
#   Arguments:
#       hass     - hass: HomeAssistant
#       sensors  - A list of sensor entities or sensor globs to be excluded
#                         (['gary_last_update', 'lillian_last_update', '*_last_update'])
#                       - A single sensor entity to be excluded
#                         ('gary_last_zone')
#
#   Gary Cobb, iCloud3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entityfilter
import logging
_LOGGER = logging.getLogger(__name__)

# Recorder Prefilter Global Variables
exclude_entities = set()
exclude_globs    = set()
exclude_globs_re = None


def update_prefilter(exclude_items):
    """ Update the filtered entity/globs list """
    global exclude_entities, exclude_globs, exclude_globs_re

    try:
        items = [exclude_items] if type(exclude_items) is str else exclude_items

        for item in items:
            if item.find('*') >= 0:
                exclude_globs.add(item)
            else:
                if item.startswith('sensor.') is False: item = f"sensor.{item}"
                exclude_entities.add(item)

        if exclude_entities != set():
            _LOGGER.info(f"Prefiltering Entities: {sorted(exclude_entities)}")

        if exclude_globs != set():
            exclude_globs_re = entityfilter._convert_globs_to_pattern(exclude_globs)
            _LOGGER.info(f"Prefiltering Globs: {sorted(exclude_globs)}")
    #        _LOGGER.info(f"Prefiltering Globs: >>{exclude_globs_re}<<")

    except Exception as err:
        _LOGGER.info(f"Recorder Entity Filter Injection Failed ({err}), "
                        f"Entities-{exclude_entities}")
        #_LOGGER.exception(err)


def add_prefilter(hass: HomeAssistant, exclude_items: dict[str, list[str]]):
    '''
    Inject the entity prefilter into the Recorder, remove Recorder listeners,
    reinitialize the Recorder

    Arguments:
        hass - HomeAssistant
        exclude_items - A list of sensor entities or sensor globs
                        (['gary_last_update', 'lillian_last_update', '*_next_update'])
                      - A single sensor entity ('gary_last_zone')

    Returns:
        True - The injection was successful
        False - The injection was not successful
    '''

    _LOGGER.info(f"Recorder Entity Prefilter Injection Started")

    ha_recorder = hass.data['recorder_instance']
    if ha_recorder is None:
        return False

    recorder_entity_filter   = ha_recorder.entity_filter
    recorder_remove_listener = ha_recorder._event_listener

    update_prefilter(exclude_items)

    try:
        def entity_prefilter(entity_id):
            global exclude_entities, exclude_globs, exclude_globs_re

            if (entity_id
                    and entity_id.startswith('sensor.')
                    and (entity_id in exclude_entities
                        or (bool(exclude_globs_re
                            and exclude_globs_re.match(entity_id))))):
                #_LOGGER.debug(f"Excluding Sensor {entity_id=}")
                return False
            #_LOGGER.debug(f"--------- Sensor {entity_id=} {entity_id in exclude_entities} {bool(exclude_globs_re and exclude_globs_re.match(entity_id))}")

            return recorder_entity_filter(entity_id)

        _LOGGER.info(f"Injecting Custom Exclude Entity Prefilter into Recorder")
        ha_recorder.entity_filter = entity_prefilter

        _LOGGER.info(f"Removing Recorder Event Listener")
        recorder_remove_listener()

        _LOGGER.info(f"Reinitializing Recorder Event Listener")
        hass.add_job(ha_recorder.async_initialize)

        _LOGGER.info(f"Recorder Entity Prefilter Injection Completed")

        return True

    except Exception as err:
        _LOGGER.info(f"Recorder Entity Filter Injection Failed ({err})")
        # _LOGGER.exception(err)

    return False
