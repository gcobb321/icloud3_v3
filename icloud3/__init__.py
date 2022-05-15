"""GitHub Custom Component."""
import asyncio


from homeassistant.config_entries   import ConfigEntry
from homeassistant.core             import CoreState, HomeAssistant
from homeassistant.helpers.typing   import ConfigType
from homeassistant.const            import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.entity_platform import EntityPlatform
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import os

from .const import (DOMAIN, PLATFORMS, STORAGE_VERSION, STORAGE_KEY_ENTITY_REGISTRY,
                    MODE_PLATFORM, MODE_INTEGRATION,CONF_VERSION,
                    WAZE_LOCATION_HISTORY_DATABASE, )

from .global_variables              import GlobalVariables as Gb
from .helpers.base                  import (_traceha, log_info_msg, log_warning_msg, log_error_msg, )
from .support.ic3v3_conf_converter  import iCloud3V3ConfigurationConverter
from .support                       import start_ic3
from .support                       import restore_state
from .support                       import service_handler
from .icloud3_main                  import iCloud3
from .support                       import event_log

import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")
successful_startup = True

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   PLATFORM MODE - STARTED FROM CONFIGURATION.YAML 'DEVICE_TRACKER/PLATFORM: ICLOUD3 STATEMENT
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    if 'device_tracker' not in config:
        return True

    hass.data.setdefault(DOMAIN, {})

    Gb.hass = hass
    Gb.operating_mode = MODE_PLATFORM
    _LOGGER.info(f"Initializing iCloud3 {Gb.version} - Using Platform method")

    current_directory = os.path.abspath(os.path.dirname(__file__)).replace("//", "/")
    start_ic3.initialize_directory_filenames(current_directory)
    start_ic3.load_storage_icloud3_configuration_file()

    # Convert or Reconvert the .storage/icloud3.configuration file if it is at a default
    # state or has never been updated via config_flow using 'HA Integrations > iCloud3'
    if Gb.conf_profile[CONF_VERSION] == 0:
        start_ic3.load_icloud3_ha_config_yaml(config)

        ic3v3_conf_converter = iCloud3V3ConfigurationConverter()
        ic3v3_conf_converter.convert_v2_config_files_to_v3()
        Gb.icloud3_v2_to_v3_parameters_converted = True

    return True


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   INTEGRATION MODE - STARTED FROM CONFIGURATION > INTEGRATIONS ENTRY
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """ Set up the iCloud3 integration from a ConfigEntry integration """

    try:
        if entry.unique_id is None:
            hass.config_entries.async_update_entry(entry, unique_id=DOMAIN)

        Gb.hass = hass
        current_directory = os.path.abspath(os.path.dirname(__file__)).replace("//", "/")
        start_ic3.initialize_directory_filenames(current_directory)
        start_ic3.load_storage_icloud3_configuration_file()
        restore_state.load_storage_icloud3_restore_state_file()

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.unique_id] = DOMAIN
        hass_data = dict(entry.data)

        hass.config_entries.async_setup_platforms(entry, PLATFORMS)

        Gb.config_entry = entry
        Gb.operating_mode = MODE_INTEGRATION
        Gb.start_icloud3_inprocess_flag = True

        _LOGGER.info(f"Initializing iCloud3 {Gb.version} - Using Integration method")
        # log_info_msg(f"{hass.data.get('frontend_extra_module_js','NO EXTRA MODULE js')}")

        # Do not start if loading/initialization failed
        if successful_startup is False:
            _LOGGER.error(f"iCloud3 Initialization Failed, configuration file "
                            f"{Gb.icloud3_config_filename} failed to load.")
            _LOGGER.error("Verify the configuration file and delete it manually if necessary")
            return False

        # Registers update listener to update config entry when options are updated.
        unsub_options_update_listener = entry.add_update_listener(options_update_listener)

        # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
        hass_data["unsub_options_update_listener"] = unsub_options_update_listener
        hass.data[DOMAIN][entry.entry_id] = hass_data

    except Exception as err:
        _LOGGER.exception(err)
        return False

    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
    #
    #   SETUP PROCESS TO START ICLOUD3
    #
    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
    def start_icloud3(event=None):
        """Start iCloud3 after HA starts."""

        service_handler.register_icloud3_services()

        log_info_msg(f"HA Startup Complete, Starting iCloud3 {Gb.version}")
        Gb.EvLog    = event_log.EventLog(Gb.hass)
        Gb.PyiCloud = None
        Gb.iCloud3 = iCloud3()
        Gb.start_icloud3_initial_load_flag = True

        icloud3_started = Gb.iCloud3.start_icloud3()
        if icloud3_started:
            log_info_msg(f"iCloud3 {Gb.version} loaded, Waiting for HA to finish starting")
        else:
            log_error_msg(f"iCloud3 {Gb.version} Initialization Failed")


    # If Home Assistant is already in a running state, start iCloud3
    # immediately, else trigger it after Home Assistant has finished starting.
    if hass.state == CoreState.running:
        start_icloud3()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_icloud3)

    return True

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
async def options_update_listener(  hass: HomeAssistant,
                                    config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

#-------------------------------------------------------------------------------------------
async def async_unload_entry(       hass: HomeAssistant,
                                    entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]))

    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

#-------------------------------------------------------------------------------------------
# async def async_setup(hass: core.HomeAssistant, config: dict):
#     """Set up the GitHub Custom component from yaml configuration."""
#     hass.data.setdefault(DOMAIN, {})
#     return True
