
from ..global_variables     import GlobalVariables as Gb
from ..const                import (
                                    APPLE_SPECIAL_ICLOUD_SERVER_COUNTRY_CODE,
                                    RARROW,
                                    CONF_IC3_VERSION, VERSION, CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_CARD_PROGRAM,
                                    CONF_UPDATE_DATE, CONF_PASSWORD, CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX,
                                    CONF_DEVICES, CONF_SETUP_ICLOUD_SESSION_EARLY,
                                    CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT, CONF_LOG_LEVEL,
                                    CONF_FAMSHR_DEVICENAME2, CONF_FAMSHR_DEVICE_ID2,
                                    CONF_RAW_MODEL2, CONF_MODEL2, CONF_MODEL_DISPLAY_NAME2, CONF_IOSAPP_DEVICE2,
                                    CF_DEFAULT_IC3_CONF_FILE,
                                    DEFAULT_PROFILE_CONF, DEFAULT_TRACKING_CONF, DEFAULT_GENERAL_CONF,
                                    DEFAULT_SENSORS_CONF,
                                    HOME_DISTANCE, CONF_SENSORS_TRACKING_DISTANCE,
                                    CONF_SENSORS_DEVICE, BATTERY_STATUS,
                                    CONF_WAZE_USED, CONF_WAZE_REGION, CONF_DISTANCE_METHOD,
                                    )

from ..support              import start_ic3
from ..support              import waze
from ..helpers.common       import (instr, ordereddict_to_dict, )
from ..helpers.messaging    import (log_exception, _trace, _traceha, close_reopen_ic3_debug_log_file, )
from ..helpers.time_util    import (datetime_now, )

import os
import json
import base64

import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")


#-------------------------------------------------------------------------------------------
def load_storage_icloud3_configuration_file():

    if os.path.exists(Gb.ha_storage_icloud3) is False:
        os.makedirs(Gb.ha_storage_icloud3)

    if os.path.exists(Gb.icloud3_config_filename) is False:
        _LOGGER.info(f"Creating Configuration File-{Gb.icloud3_config_filename}")

        Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
        build_initial_config_file_structure()
        write_storage_icloud3_configuration_file()

    success = read_storage_icloud3_configuration_file()

    if success:
        write_storage_icloud3_configuration_file('_backup')

    else:
        success = read_storage_icloud3_configuration_file('_backup')

        if success:
            _LOGGER.warning(f"iCloud3{RARROW}Restore from backup config file successful")

            write_storage_icloud3_configuration_file()

        else:
            _LOGGER.error(f"iCloud3{RARROW}Restore config file from backup failed")
            _LOGGER.error(f"iCloud3{RARROW}Recreating config file with default parameters-"
                            f"{Gb.icloud3_config_filename}")

            build_initial_config_file_structure()
            Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
            write_storage_icloud3_configuration_file()
            read_storage_icloud3_configuration_file()

    if CONF_LOG_LEVEL in Gb.conf_general:
        start_ic3.set_log_level(Gb.conf_general[CONF_LOG_LEVEL])

    update_icloud3_configuration_file = False
    if HOME_DISTANCE not in Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE]:
        Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)
        update_icloud3_configuration_file = True
    if Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY].startswith('www/') is False:
        Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY] = f"www/{Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]}"
        update_icloud3_configuration_file = True

    if update_icloud3_configuration_file:
        write_storage_icloud3_configuration_file()

    Gb.www_evlog_js_directory = Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]
    Gb.www_evlog_js_filename  = f"{Gb.www_evlog_js_directory}/{Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]}"

    return

#-------------------------------------------------------------------------------------------
def load_icloud3_ha_config_yaml(ha_config_yaml):


    Gb.ha_config_yaml_icloud3_platform = {}
    # _traceha(f"{ha_config_yaml=} ")
    if ha_config_yaml == '':
        return

    ha_config_yaml_devtrkr_platforms = ordereddict_to_dict(ha_config_yaml)['device_tracker']

    ic3_ha_config_yaml = {}
    for ha_config_yaml_platform in ha_config_yaml_devtrkr_platforms:
        if ha_config_yaml_platform['platform'] == 'icloud3':
            ic3_ha_config_yaml = ha_config_yaml_platform.copy()
            break

    Gb.ha_config_yaml_icloud3_platform = ordereddict_to_dict(ic3_ha_config_yaml)
    # _traceha(f"{ic3_ha_config_yaml=} ")
    # _traceha(f"{Gb.ha_config_yaml_icloud3_platform=} ")

#--------------------------------------------------------------------
def build_initial_config_file_structure():
    '''
    Create the initial data structure of the ic3 config file

    |---profile
    |---data
        |---tracking
            |---devices
        |---general
            |---parameters
        |---sensors

    '''

    Gb.conf_profile   = DEFAULT_PROFILE_CONF.copy()
    Gb.conf_tracking  = DEFAULT_TRACKING_CONF.copy()
    Gb.conf_devices   = []
    Gb.conf_general   = DEFAULT_GENERAL_CONF.copy()
    Gb.conf_sensors   = DEFAULT_SENSORS_CONF.copy()
    Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()

    Gb.conf_data['tracking']        = Gb.conf_tracking
    Gb.conf_data['tracking']['devices'] = Gb.conf_devices
    Gb.conf_data['general']         = Gb.conf_general
    Gb.conf_data['sensors']         = Gb.conf_sensors

    Gb.conf_file_data['profile']    = Gb.conf_profile
    Gb.conf_file_data['data']       = Gb.conf_data


    # Verify general parameters and make any necessary corrections
    try:
        if Gb.location_info['country_code'].lower() in APPLE_SPECIAL_ICLOUD_SERVER_COUNTRY_CODE:
            Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX] = Gb.location_info['country_code'].lower()

        if Gb.config and Gb.config.units['name'] != 'Imperial':
            Gb.conf_general[CONF_UNIT_OF_MEASUREMENT] = 'km'
            Gb.conf_general[CONF_TIME_FORMAT] = '24-hour'

        elif Gb.location_info['use_metric']:
            Gb.conf_general[CONF_UNIT_OF_MEASUREMENT] = 'km'
            Gb.conf_general[CONF_TIME_FORMAT] = '24-hour'

        waze_region_code = waze.waze_region_by_country_code()
        Gb.conf_general[CONF_WAZE_REGION] = waze_region_code.lower()
        Gb.conf_general[CONF_WAZE_USED]   = (waze_region_code != '??')

    except:
        pass


#-------------------------------------------------------------------------------------------
def read_storage_icloud3_configuration_file(filename_suffix=''):
    '''
    Read the config/.storage/.icloud3.configuration file and extract the
    data into the Global Variables

    Parameters:
        filename_suffix: A suffix added to the filename that allows saving multiple copies of
                            the configuration file
    '''

    try:
        filename = f"{Gb.icloud3_config_filename}{filename_suffix}"
        with open(filename, 'r') as f:
            Gb.conf_file_data = json.load(f)

            Gb.conf_profile   = Gb.conf_file_data['profile']
            Gb.conf_data      = Gb.conf_file_data['data']

            Gb.conf_tracking  = Gb.conf_data['tracking']
            Gb.conf_devices   = Gb.conf_data['tracking']['devices']
            Gb.conf_general   = Gb.conf_data['general']
            Gb.conf_sensors   = Gb.conf_data['sensors']
            Gb.log_level      = Gb.conf_general[CONF_LOG_LEVEL]

            Gb.conf_tracking[CONF_PASSWORD] = decode_password(Gb.conf_tracking[CONF_PASSWORD])

            config_file_special_maintenance()

        return True

    except Exception as err:
        log_exception(err)

    return False

#--------------------------------------------------------------------
def config_file_special_maintenance():
    '''
    Fix configuration file errors or add any new fields
    '''

    update_config_file_flag = False

    # v3.0.0 beta 1 - Fix time format from migration
    if instr(Gb.conf_data['general'][CONF_TIME_FORMAT], '-hour-hour'):
        Gb.conf_data['general'][CONF_TIME_FORMAT].replace('-hour-hour', '-hour')
        update_config_file_flag = True

    # v3.0.0 beta 3 - remove tracking_from_zone item from sensors list which shouldn't have been added
    if BATTERY_STATUS in Gb.conf_sensors[CONF_SENSORS_DEVICE]:
        Gb.conf_sensors[CONF_SENSORS_DEVICE].pop(BATTERY_STATUS, None)
        update_config_file_flag = True

    if 'tracking_by_zones' in Gb.conf_sensors:
        Gb.conf_sensors.pop('tracking_by_zones', None)
        update_config_file_flag = True

    for conf_device in Gb.conf_devices:
        if CONF_FAMSHR_DEVICENAME2 in conf_device:
            conf_device.pop(CONF_FAMSHR_DEVICENAME2, None)
            conf_device.pop(CONF_FAMSHR_DEVICE_ID2, None)
            conf_device.pop(CONF_RAW_MODEL2, None)
            conf_device.pop(CONF_MODEL2, None)
            conf_device.pop(CONF_MODEL_DISPLAY_NAME2, None)
            conf_device.pop(CONF_IOSAPP_DEVICE2, None)
            update_config_file_flag = True

    if (CONF_IC3_VERSION not in Gb.conf_profile
            or Gb.conf_profile[CONF_IC3_VERSION] == VERSION):
        Gb.conf_profile[CONF_IC3_VERSION] = VERSION
        update_config_file_flag = True

    if CONF_SETUP_ICLOUD_SESSION_EARLY not in Gb.conf_tracking:
        _insert_into_conf_tracking(CONF_SETUP_ICLOUD_SESSION_EARLY, True)
        update_config_file_flag = True
        # Gb.conf_tracking.insert(3, [CONF_SETUP_ICLOUD_SESSION_EARLY]) = True

    if update_config_file_flag:
        write_storage_icloud3_configuration_file()

#--------------------------------------------------------------------
def _insert_into_conf_tracking(new_item, initial_value):
    '''
    Add item to conf_travking before the devices element
    '''
    pos = list(Gb.conf_tracking.keys()).index(CONF_DEVICES) - 1
    items = list(Gb.conf_tracking.items())
    items.insert(pos, (new_item, initial_value ))
    Gb.conf_tracking = dict(items)

#--------------------------------------------------------------------
def write_storage_icloud3_configuration_file(filename_suffix=''):
    '''
    Update the config/.storage/.icloud3.configuration file

    Parameters:
        filename_suffix: A suffix added to the filename that allows saving multiple copies of
                            the configuration file
    '''

    try:
        filename = f"{Gb.icloud3_config_filename}{filename_suffix}"
        with open(filename, 'w', encoding='utf8') as f:
            Gb.conf_profile[CONF_UPDATE_DATE] = datetime_now()

            Gb.conf_data['tracking']['devices'] = Gb.conf_devices
            Gb.conf_data['tracking']        = Gb.conf_tracking
            Gb.conf_data['general']         = Gb.conf_general
            Gb.conf_data['sensors']         = Gb.conf_sensors

            Gb.conf_file_data['profile']    = Gb.conf_profile
            Gb.conf_file_data['data']       = Gb.conf_data

            decoded_password = Gb.conf_tracking[CONF_PASSWORD]
            Gb.conf_tracking[CONF_PASSWORD] = encode_password(Gb.conf_tracking[CONF_PASSWORD])

            json.dump(Gb.conf_file_data, f, indent=4, ensure_ascii=False)

            Gb.conf_tracking[CONF_PASSWORD] = decoded_password

        if Gb.iC3DebugLogFile:
            close_reopen_ic3_debug_log_file()

        return True

    except Exception as err:
        log_exception(err)

    return False

#--------------------------------------------------------------------
def encode_password(password):
    '''
    Determine if the password is encoded.

    Return:
        Decoded password
    '''
    try:
        if (password == ''
                or Gb.encode_password_flag is False):
            return password

        return f"««{base64_encode(password)}»»"

    except Exception as err:
        log_exception(err)
        password = password.replace('««', '').replace('»»', '')
        return password

def base64_encode(string):
    """
    Encode the string via base64 encoder
    """
    # encoded = base64.urlsafe_b64encode(string)
    # return encoded.rstrip("=")

    string_bytes = string.encode('ascii')
    base64_bytes = base64.b64encode(string_bytes)
    return base64_bytes.decode('ascii')

#--------------------------------------------------------------------
def decode_password(password):
    '''
    Determine if the password is encoded.

    Return:
        Decoded password
    '''
    try:
        if (password.startswith('««') or password.endswith('»»')):
            password = password.replace('««', '').replace('»»', '')
            return base64_decode(password)

    except Exception as err:
        log_exception(err)
        password = password.replace('««', '').replace('»»', '')

    return password

def base64_decode(string):
    """
    Decode the string via base64 decoder
    """
    # padding = 4 - (len(string) % 4)
    # string = string + ("=" * padding)
    # return base64.urlsafe_b64decode(string)

    base64_bytes = string.encode('ascii')
    string_bytes = base64.b64decode(base64_bytes)
    return string_bytes.decode('ascii')

#--------------------------------------------------------------------:)