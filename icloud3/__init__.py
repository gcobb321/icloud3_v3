"""GitHub Custom Component."""
import asyncio
import logging
import os
import json
from collections import OrderedDict

from homeassistant.config_entries   import ConfigEntry
from homeassistant.core             import HomeAssistant
from homeassistant.helpers.typing   import ConfigType

from .const import (DOMAIN, STORAGE_VERSION, STORAGE_KEY, STORAGE_KEY_ENTITY_REGISTRY,
                    MODE_PLATFORM, MODE_INTEGRATION,
                    CF_DEFAULT_IC3_CONF_FILE, CF_DATA_TRACKING, CF_DATA,
                    CF_DATA_GENERAL, CF_DATA_SENSORS, CF_PROFILE,
                    CONF_UPDATE_DATE, CONF_VERSION,
                    EVENT_LOG_CARD_WWW_JS_PROG, CONF_DEVICES,
                    DEFAULT_GENERAL_CONF, CONF_DISPLAY_TEXT_AS,
                    CONF_LOG_LEVEL, )

from .global_variables              import GlobalVariables as Gb
from .helpers.base                  import (_traceha, log_info_msg, log_warning_msg, log_error_msg,
                                            read_storage_icloud3_configuration_file,
                                            write_storage_icloud3_configuration_file,
                                            ordereddict_to_dict, )
from .support.ic3v3_conf_converter  import iCloud3V3ConfigurationConverter
from .support.start_ic3             import set_log_level
# from .config_flow                   import OptionsFlowHandler

# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

#-------------------------------------------------------------------------------------------
def initialize_directory_filenames(hass):

    Gb.hass                    = hass
    Gb.ha_storage_icloud3      = Gb.hass.helpers.storage.Store(STORAGE_VERSION, DOMAIN).path
    Gb.ha_storage_directory    = Gb.ha_storage_icloud3.replace(f"/{DOMAIN}", "")
    Gb.ha_config_directory     = Gb.ha_storage_directory.replace('.storage', '')
    Gb.ha_config_www_directory = f"{Gb.ha_config_directory}www"
    Gb.icloud3_config_filename = f"{Gb.ha_storage_icloud3}.configuration"
    Gb.icloud3_directory       = os.path.abspath(os.path.dirname(__file__)).replace("//", "/")
    Gb.icloud3_filename        = Gb.icloud3_directory.split("/custom_components/")[1]
    Gb.www_evlog_js_filename   = (f"{Gb.ha_config_www_directory}/{EVENT_LOG_CARD_WWW_JS_PROG}")
    Gb.HALogger                = logging.getLogger(f"icloud3")
    Gb.entity_registry_file    = Gb.hass.config.path(Gb.ha_storage_directory, STORAGE_KEY_ENTITY_REGISTRY)

    if Gb.entity_registry_file.startswith('/workspaces'):
        Gb.entity_registry_file = Gb.entity_registry_file.replace('.storage/core.', '.storage/test.')


#-------------------------------------------------------------------------------------------
def load_storage_icloud3_configuration_file():

    if os.path.exists(Gb.icloud3_config_filename) is False:
        Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
        write_storage_icloud3_configuration_file()

    read_storage_icloud3_configuration_file()

    _traceha(f"{Gb.conf_general=}")
    set_log_level(Gb.conf_general[CONF_LOG_LEVEL])
    return

#-------------------------------------------------------------------------------------------
def load_icloud3_ha_config_yaml(config):

    log_info_msg("__init__ async_setup {config=}")
    Gb.config_parm_ha_config_yaml = None
    ha_config_yaml_platforms = ordereddict_to_dict(config)['device_tracker']

    ic3_ha_config_yaml = {}
    for ha_config_yaml_platform in ha_config_yaml_platforms:
        if ha_config_yaml_platform['platform'] == 'icloud3':
            ic3_ha_config_yaml = ha_config_yaml_platform.copy()
            break

    Gb.config_parm_ha_config_yaml = ordereddict_to_dict(ic3_ha_config_yaml)

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   PLATFORM MODE - STARTED FROM CONFIGURATION.YAML 'DEVICE_TRACKER/PLATFORM: ICLOUD3 STATEMENT
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    '''
    Set up the iCloud3 from config.yaml platform statement
    '''

    hass.data.setdefault(DOMAIN, {})

    Gb.hass = hass
    Gb.operating_mode = MODE_PLATFORM

    _LOGGER.info(f"Initializing iCloud3 {Gb.version} - Using Platform method")

    initialize_directory_filenames(hass)
    load_storage_icloud3_configuration_file()

    # Convert or Reconvert the .storage/icloud3.configuration file if it is at a default
    # state or has never been updated via config_flow using 'HA Integrations > iCloud3'
    if Gb.conf_profile[CONF_VERSION] == 0:
        load_icloud3_ha_config_yaml(config)

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
    '''
    Set up the iCloud3 integration from a ConfigEntry integration
    '''
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=DOMAIN)

    hass.data[DOMAIN][entry.unique_id] = DOMAIN
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)

    Gb.hass = hass
    Gb.config_entry = entry
    Gb.operating_mode = MODE_INTEGRATION
    # Gb.OptionsFlowHandler = OptionsFlowHandler()

    _LOGGER.info(f"Initializing iCloud3 {Gb.version} - Using Integration method")

    initialize_directory_filenames(hass)
    load_storage_icloud3_configuration_file()


    Gb.HALogger.info(f"Integration {Gb.conf_general=}")
    Gb.HALogger.info(f"Integration {Gb.conf_devices=}")

    # _LOGGER.info(f"25 init {Gb.hass.config('icloud3')=}")
    # Gb.HALogger.info(f"156 {Gb.ha_storage_icloud3=} {STORAGE_KEY=} {STORAGE_VERSION=}")
    # Gb.HALogger.info(f"156 {Gb.entity_registry_file=}")
    # Gb.HALogger.info(f"156 {Gb.ha_storage_directory=}")
    # Gb.HALogger.info(f"156 {Gb.ha_config_directory=}")
    # Gb.HALogger.info(f"156 {Gb.icloud3_filename=}")
    # Gb.HALogger.info(f"156 {Gb.icloud3_config_filename=}")
    # Gb.HALogger.info(f"156 {Gb.www_evlog_js_filename=}")

    # Gb.HALogger.info(f"130 init {hass_data=}")

    # Start iCloud0
    # account = IcloudAccount(
    #     hass,
    #     username,
    #     password,
    #     icloud_dir,
    #     with_family,
    #     max_interval,
    #     gps_accuracy_threshold,
    #     entry,
    # )
    # await hass.async_add_executor_job(account.setup)
    # hass.data[DOMAIN][entry.unique_id] = account
    # hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    # Gb.hass.services.register(DOMAIN, 'action',
    #             service_handler.process_update_service_request,
    #             schema=SERVICE_SCHEMA)
    # Gb.hass.services.register(DOMAIN, 'config',
    #             service_handler.update_icloud3_configuration)
    # Gb.hass.services.register(DOMAIN, 'restart',
    #             service_handler.process_restart_icloud3_service_request,
    #             schema=SERVICE_SCHEMA)
    # Gb.hass.services.register(DOMAIN, 'find_iphone_alert',
    #             service_handler.process_find_iphone_alert_service_request, schema=SERVICE_SCHEMA)


    # Registers update listener to update config entry when options are updated.
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)

    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # Forward the setup to the sensor platform.
    # hass.async_create_task(
    #     hass.config_entries.async_forward_entry_setup(entry, "sensor")
    # )
    return True

#-------------------------------------------------------------------------------------------
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
