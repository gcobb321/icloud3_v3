import json
import os
import time
# from copy import deepcopy
# from typing                         import Any, Dict, Optional
from collections                    import OrderedDict

from homeassistant                  import config_entries, data_entry_flow
# from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.config_entries   import ConfigEntry as config_entry
from homeassistant.data_entry_flow  import FlowHandler
from homeassistant.core             import callback
# from homeassistant.core             import HomeAssistant
from homeassistant.util             import slugify
# from homeassistant.helpers.entity_platform import EntityPlatform as entity_platform
# from homeassistant.helpers.entity_registry import (async_entries_for_config_entry, async_get_registry, )

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers          import selector
import voluptuous as vol

import logging
_LOGGER = logging.getLogger(__name__)

from .const import *
from .global_variables      import GlobalVariables as Gb
from .helpers.base          import (instr, isnumber, log_exception, _traceha, _trace,
                                    post_event, )
from .helpers               import entity_io
from .                      import sensor as ic3_sensor
from .                      import device_tracker as ic3_device_tracker
from .support               import start_ic3
from .support               import pyicloud_ic3_interface
from .support.pyicloud_ic3  import (PyiCloudService, PyiCloudException, PyiCloudFailedLoginException,
                                    PyiCloudServiceNotActivatedException, PyiCloudNoDevicesException, )
from .support.ic3v3_conf_converter import iCloud3V3ConfigurationConverter


#-----------------------------------------------------------------------------------------
def option_text_list(opt_key_text, ensure_six_items=False):
    """ Make a drop down list from a list of 5-items or less """

    if type(opt_key_text) is dict:
        opt_text_list = [t for t in opt_key_text.values()]
    else:
        opt_text_list = opt_key_text

    if ensure_six_items:
        for i in range(6 - len(opt_text_list)):
            opt_text_list.append('.')

    return opt_text_list

#-----------------------------------------------------------------------------------------
def vol_in6_list(opt_key_text):
    """ Make a drop down list from a list of 5-items or less """

    if type(opt_key_text) is dict:
        opt_text_list = [t for t in opt_key_text.values()]
    else:
        opt_text_list = opt_key_text

    for i in range(6 - len(opt_text_list)):
        opt_text_list.append('.')

    return opt_text_list

#-----------------------------------------------------------------------------------------
def dict_value_list(key_value_dict):
    """ Make a drop down list from a list  """

    if type(key_value_dict) is dict:
        value_list = [v for v in key_value_dict.values()]
    else:
        value_list = list(key_value_dict)

    return value_list
#-----------------------------------------------------------------------------------------
MENU_KEY_TEXT = {
        'icloud_account': 'ICLOUD ACCOUNT, DATA SOURCE > iCloud Acct Username/password, iCloud/iOS App Data Usage',
        'device_list': 'ICLOUD3 DEVICES > Add, Change and Delete tracked devices',
        'event_log_configuration': 'EVENT LOG CONFIGURATION > Zones Name formats, Time formats, EvLog Card Directory',
        'display_text_as': 'DISPLAY TEXT AS > Event Log text replacement values',
        'other_parms': 'OTHER PARAMETERS > Unit of Measure, Accuracy Thresholds, Log Levels',
        'inzone_intervals': 'INZONE INTERVALS > Default inZone intervals',
        'waze': 'WAZE PARAMETERS > Region, Min/Max Intervals, History Database Controls',
        'stationary_zone': 'STATIONARY ZONE > Friendly Name, inZone Interval, Still Time & Base Location Offsets',
        'sensors': 'SENSORS > Sensors created by iCloud3',
        'next_page_0': 'NEXT PAGE > iCloud Account • iCloud3 Devices • Event Log Configuration \
                        • Text Replacement • Action Commands',
        'next_page_1': 'NEXT PAGE > Inzone Intervals • Waze • Stationary Zone  • Other Parameters • Sensors',
        'select': 'SELECT > Select the parameter update form',
        'action_menu1': 'ACTION COMMANDS > iCloud Verification Code • Restart/Pause/Resume Polling • Export Event Log \
                         • Reset iCloud Interface  • Find My Phone Alerts • Waze Commands',
        'exit': 'EXIT > Exit the iCloud3 Configurator • Restart iCloud3 (if needed)'}

MENU_KEY_TEXT_PAGE_0 = [
    MENU_KEY_TEXT['icloud_account'],
    MENU_KEY_TEXT['device_list'],
    MENU_KEY_TEXT['sensors'],
    MENU_KEY_TEXT['display_text_as'],
    MENU_KEY_TEXT['action_menu1'],
    ]
MENU_KEY_TEXT_PAGE_1 = [
    MENU_KEY_TEXT['event_log_configuration'],
    MENU_KEY_TEXT['waze'],
    MENU_KEY_TEXT['inzone_intervals'],
    MENU_KEY_TEXT['stationary_zone'],
    MENU_KEY_TEXT['other_parms'],
    ]
menu_action = [
    MENU_KEY_TEXT['select'],
    MENU_KEY_TEXT['next_page_1'],
    MENU_KEY_TEXT['exit']
    ]

OPT_ACTION_KEY_TEXT = {
        'select_form': 'SELECT > Select the parameter update form',
        'update_device': 'UPDATE DEVICE > Update the selected device',
        'select_text_as': 'SELECT > Update selected `Display Text As` field',
        'log_in_icloud_acct': 'LOGIN > Log into the iCloud Account',
        'next_page': 'NEXT PAGE > Save changes • Display the next page',
        'next_page_info': 'NEXT PAGE > ^info_field^',
        'next_page_device': 'NEXT PAGE > Friendly Name, Track-from-Zones, Other Setup Fields',
        'next_page_waze': 'NEXT PAGE > Waze History Database parameters',
        'add_device': 'ADD DEVICE > Add a device to be tracked by iCloud3',
        'delete_device': 'DELETE DEVICE > Delete the selected device from the tracked device list',
        'delete_device_yes': 'YES > Delete this device from the iCloud3 tracked devices list',
        'delete_device_no': 'NO > Do not delete this device',
        'clear_text_as': 'CLEAR > Remove `Display Test As` entry',
        'exit': 'EXIT > Exit the iCloud3 Configurator',
        'return': 'RETURN > Return to the Main Menu',
        'save': 'SAVE > Update Configuration File • Return to the menu screen',
        'cancel': 'CANCEL > Discard changes • Return to the Main Menu'}

UPDATE_CONTROL = 'action_item'
UPDATE_CONTROL_BASE = [
    OPT_ACTION_KEY_TEXT['save'],
    OPT_ACTION_KEY_TEXT['cancel']]

OPT_LIST_KEY_TEXT_NONE      = {'None': 'None'}
OPT_PICTURE_TEXT            = ['None']
UNKNOWN_DEVICE_TEXT         = '  >=== UNKNOWN DEVICE ==='

DEVICE_LIST_CONTROL = [
        OPT_ACTION_KEY_TEXT['update_device'],
        OPT_ACTION_KEY_TEXT['add_device'],
        OPT_ACTION_KEY_TEXT['delete_device'],
        OPT_ACTION_KEY_TEXT['return']]
DEVICE_LIST_CONTROL_NO_ADD = [
        OPT_ACTION_KEY_TEXT['update_device'],
        OPT_ACTION_KEY_TEXT['delete_device'],
        OPT_ACTION_KEY_TEXT['return']]
DELETE_DEVICE_CONFIRM_ACTION = [
        OPT_ACTION_KEY_TEXT['delete_device_yes'],
        OPT_ACTION_KEY_TEXT['delete_device_no'],
]

OPT_DATA_SOURCE_KEY_TEXT = {
        'icloud,iosapp': 'ICLOUD & IOSAPP - iCloud account and iOS App are used',
        'icloud': 'ICLOUD ONLY - iOS App is not used',
        'iosapp': 'IOS APP ONLY - iCloud account is not used'}

OPT_IOSAPP_DEVICE_KEY_TEXT = {
        'None': 'None - The iOS App is not used to locate this device',
        'Search': 'Search - Scan the Entity Registry for the FamShr device'}

OPT_TRACKING_MODE_KEY_TEXT = {
        'normal': 'Normal - Request Location and track device',
        'monitor': 'Monitor - Report location when a tracked device is updated',
        'inactive': 'Inactive - Device is inactive and will not be tracked'}

OPT_TRACKING_METHOD_KEY_TEXT = {
        'famshr': 'FamShr - Family Sharing List location datae',
        'fmf': 'FmF - Use the Find-my-Friends location datae',
        'iosapp': 'iOS App Only - Do not request location data from the iCloud Account'}

OPT_UNIT_OF_MEASUREMENT_KEY_TEXT = {
        'mi': 'mi - Imperial',
        'km': 'km - Metric'}

OPT_TIME_FORMAT_KEY_TEXT = {
        '12-hour': '12-hour Time Format',
        '24-hour': '24-hour Time Format'}

OPT_DISPLAY_ZONE_FORMAT_KEY_TEXT = {
        'name': 'Name - Reformatted HA Zone Name (TheShores)',
        'title': 'Title - Reformatted HA Zone Name (The Shores)',
        'fname': 'Friendly Name - HA Zone Friendly Name (The Shores Development)',
        'zone': 'Zone Name - HA Zone Name (the_shores)'}

OPT_RESTART_NOW_LATER_KEY_TEXT = {
        'now': 'RESTART NOW - Restart iCloud3 now and use the updated configuration.',
        'later': 'RESTART LATER - The configuration changes have been saved. Restart at a later time to apply the changes.'}

OPT_LOG_LEVEL_KEY_TEXT = {
        'info': 'Info - Log General Information',
        'debug': 'Debug - Log Tracking Monitors',
        'rawdata': 'Rawdata - Log data from iCloud'}

OPT_DISTANCE_METHOD_KEY_TEXT = {
        'waze': 'Waze - Use the Waze Route Service',
        'calc': 'Calc - Calculate the Distance'}

OPT_WAZE_REGION_KEY_TEXT = {
        'us': 'United States',
        'eu': 'Europe',
        'il': 'Isreal',
        'au': 'Austrailia'}

OPT_WAZE_HISTORY_TRACK_DIRECTION_KEY_TEXT = {
        'north_south': 'North-South',
        'east_west': 'East-West'}

CONF_SENSORS_CONTROL_KEY_TEXT = {
        'devtrkr_only_monitored_devices': 'MONITORED DEVICES > Only create a device tracker entity (with field attributes) for a monitored device. Uncheck to also create individual sensors for each field',
}
CONF_SENSORS_DEVICE_KEY_TEXT = {
        NAME: 'name > iCloud3 Device Name',
        'badge': 'badge > A badge showing the Zone Name or distance from the Home zone',
        'battery': 'battery > Battery Level',
        'battery_status': 'battery_status > Battery Status (Charging, Low, etc)',
        'info': 'info > An information message containing status, alerts and errors related to device location updates, data accuracy, etc',
}
CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT = {
        'interval': 'interval > Time between location requests',
        'last_update': 'last_update > Last time the location was updated',
        'next_update': 'next_update > Next time the location will be updated',
        'last_located': 'last_located > Last time the was located using iCloud or iOS APP location',
}
CONF_SENSORS_TRACKING_TIME_KEY_TEXT = {
        'travel_time': 'travel_time > Waze Travel time to Home or closest Track-from-Zone zone',
        'travel_time_min': 'travel_time_min > Waze Travel time to Home or closest Track-from-Zone zone in minutes',
}
CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT = {
        'zone_distance': 'zone_distance > Distance to the Home or closest Track-from-Zone zone',
        'home_distance': 'home_distance > Distance to the Home zone',
        'dir_of_travel': 'dir_of_travel > Direction of Travel for the Home zone or closest Track-from-Zone zone (Towards, AwayFrom, inZone, etc)',
        'travel_distance': 'travel_distance > Distance moved from the last location',
}
CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT = {
        'tfz_zoneinfo': 'zoneinfo_[zone] > Summary sensor with all zone distance & time attributes',
        'tfz_travel_time': 'travel_time_[zone] > Waze Travel time to a Track-from-Zone',
        'tfz_travel_time_min': 'travel_time_min_[zone] > Waze Travel time to a Track-from-Zone in minutes',
        'tfz_distance': 'distance_[zone] > Distance from the Track-from-Zone ',
        'tfz_dir_of_travel': 'dir_of_travel_[zone] > Direction of Travel from the Track-from-Zone (Towards, AwayFrom, inZone, etc)',
}
CONF_SENSORS_TRACKING_OTHER_KEY_TEXT = {
        'trigger': 'trigger > Last action that triggered a location update',
        'waze_distance': 'waze_distance > Waze distance from a TrackFrom zone',
        'calc_distance': 'calc_distance > Calculated straight line distance from a TrackFrom zone',
}
CONF_SENSORS_ZONE_KEY_TEXT = {
        'zone': 'zone > HA Zone entity_id (Example: `the_shores`, `home`)',
        'zone_fname': 'zone_fname > HA Zone entity_id Friendly Name (customized on HA Entity update form)',
        'zone_name': 'zone_name > Reformatted Zone entity_id (Example: `TheShores`, `Home`)',
        'zone_datetime': 'zone_datetime > The time the Device entered the Zone',
        'last_zone': 'last_zone_[...] > Create the same sensors for the device`s last HA Zone',
}
CONF_SENSORS_OTHER_KEY_TEXT = {
        'gps_accuracy': 'gps_accuracy > GPS acuracy of the last location coordinates',
        'vertical_accuracy': 'vertical_accuracy > Vertical (Elevation) Accuracy',
        'altitude': 'altitude > Altitude/Elevation',
}

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                     ICLOUD3 CONFIG FLOW - INITIAL SETUP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class iCloud3ConfigFlow(config_entries.ConfigFlow, FlowHandler, domain=DOMAIN ):
    '''iCloud3 config flow Handler'''

    VERSION = 1
    def __init__(self):
        self.step_id = ''           # step_id for the window displayed
        self.errors  = {}           # Errors en.json error key

#----------------------------------------------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        '''Get the options flow for this handler'''
        Gb.OptionsFlowHandler = OptionsFlowHandler()
        return Gb.OptionsFlowHandler

#----------------------------------------------------------------------
    async def async_step_user(self, user_input=None):
        '''Invoked when a user initiates a flow via the user interface.'''
        errors = {}
        _LOGGER.info(f"{self.hass.data.get(DOMAIN)=} {user_input=}")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # ic3v3_conf_converter = iCloud3V3ConfigurationConverter()
            # ic3v3_conf_converter.convert_v2_config_files_to_v3()

            return self.async_create_entry(title="iCloud3", data={})

        schema = vol.Schema({
            vol.Required("continue", default=True): bool})

        return self.async_show_form(step_id="user",
                                    data_schema=schema,
                                    errors=errors)

#----------------------------------------------------------------------
    async def async_step_reauth(self, user_input=None, errors=None):
        '''
        Display the Apple ID Verification Code form and reauthenticate
        the iCloud account.
        '''

        if (user_input and 'icloud3_service_call' in user_input):
            await self.async_set_unique_id(DOMAIN)
            user_input = None

        self.step_id = config_entries.SOURCE_REAUTH
        self.errors = errors or {}

        if user_input is not None:
            if user_input[CONF_VERIFICATION_CODE]:
                valid_code = await self.hass.async_add_executor_job(
                                Gb.PyiCloud.validate_2fa_code,
                                user_input[CONF_VERIFICATION_CODE])

                # valid_code = (user_input[CONF_VERIFICATION_CODE] == '111111')

                if valid_code:
                    event_msg =(f"{EVLOG_ALERT}iCloud Alert > iCloud Account Verification completed successfully. {valid_code}")
                    post_event(event_msg)

                    start_ic3.set_tracking_method(ICLOUD)
                    Gb.start_icloud3_request_flag = True
                    Gb.authenticated_time = time.time()

                    return self.async_abort(reason="reauth_successful")

                else:
                    post_event(f"The Apple ID Verification Code is invalid. {valid_code}")
                    self.errors[CONF_VERIFICATION_CODE] = 'invalid_verification_code'
            else:
                return self.async_abort(reason="update_cancelled")

        schema = vol.Schema({vol.Required(CONF_VERIFICATION_CODE):
                                selector.TextSelector(),})

        return self.async_show_form(step_id=config_entries.SOURCE_REAUTH,
                                    data_schema=schema,
                                    errors=self.errors)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                 ICLOUD3 UPDATE CONFIGURATION / OPTIONS HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlowHandler(config_entries.OptionsFlow):
    '''Handles options flow for the component.'''

    def __init__(self):#, config_entry: config_entries.ConfigEntry):
        self.initialize_options_required_flag = True
        self.step_id        = ''       # step_id for the window displayed
        self.errors         = {}       # Errors en.json error key

        self.initialize_options()

    def initialize_options(self):
        self.initialize_options_required_flag = False

        self.errors                = {}       # Errors en.json error key
        self.user_input_multi_form = {}     # Saves the user_input from form #1 on a multi-form update
        self.errors_user_input     = {}       # user_input text for a value with an error
        self.step_id               = ''       # step_id for the window displayed
        self.menu_item_selected    = [MENU_KEY_TEXT_PAGE_0[0], MENU_KEY_TEXT_PAGE_1[0]]
        self.menu_page_no          = 0        # Menu currently displayed
        self.menu_msg              = ''     # Message displayed on menu after update
        self.called_from_step_id   = ''       # Form/Fct to return to when verifying the icloud auth code

        self.opt_actions               = []
        self.config_flow_updated_parms = {''}
        self._description_placeholders = None

        # Variables used for icloud_account update forms
        self.logging_into_icloud_flag = False
        self._existing_entry          = None
        self.username                 = None
        self.password                 = None
        self.all_famshr_devices       = True

        # Variables used for device selection and update on the device_list and device_update forms
        self.form_devices_list_all         = []         # List of the devices in the Gb.conf_tracking[DEVICES] parameter
        self.form_devices_list_displayed   = []   # List of the devices displayed on the device_list form
        self.form_devices_list_devicename  = []  # List of the devicenames in the Gb.conf_tracking[DEVICES] parameter
        self.next_page_devices_list        = []
        self.device_list_page_no           = 0          # Devices List form page number, starting with 0
        self.device_list_page_selected_idx = \
                [idx for idx in range(0, len(Gb.conf_devices)+10, 5)] # Device selected on each display page
        self.ic3_devicename_being_updated  = ''      # Devicename currently being updated
        self.conf_device_selected          = {}
        self.conf_device_selected_idx      = 0
        self.sensor_entity_attrs_changed   = {}          # Contains info regarding update_device and needed entity changes
        self.device_list_control_default   = 'select'     # Select the Return to main menu as the default
        self.add_device_flag               = False
        self.add_device_enter_devicename_form_part_flag = False  # Add device started, True = form top part only displayed

        self.devicename_device_info_famshr       = {}
        self.devicename_device_id_famshr         = {}
        self.devicename_device_info_fmf          = {}
        self.devicename_device_id_fmf            = {}
        self.device_id_devicename_fmf            = {}
        self.device_opt_iosapp_text_by_entity_id = {}         # mobile_app device_tracker info used in devices form for iosapp selection
        self.device_trkr_by_entity_id_all        = {}          # other platform device_tracker used to validate the ic3 entity is not used

        self.device_opt_picture_file_name_list = []
        self.device_opt_famshr_devicename_list = []
        self.device_opt_fmf_email_list         = []
        self.device_opt_iosapp_entity_list     = []
        self.opt_zone_name_key_text            = {}

        self.device_opt_famshr_text_by_fname     = {}
        self.device_opt_fmf_text_by_email        = {}
        self.device_opt_iosapp_text_by_entity_id = {}

        self._verification_code = None

        # Variables used for the display_text_as update
        self.dta_selected_idx      = -1        # Current conf index being updated
        self.dta_selected_idx_page = [0, 5]    # Selected idx to display on each page
        self.dta_page_no           = 0         # Current page being displayed
        self.dta_working_copy      = {0: '', 1: '', 2: '', 3: '', 4: '',
                                               5: '', 6: '', 7: '', 8: '', 9: '',}

        # Variables used for the system_settings s update
        self.opt_www_directory_list         = []

    async def async_step_init(self, user_input=None):
        if self.initialize_options_required_flag:
            self.initialize_options()
        self.errors = {}

        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_step_menu(self, user_input=None, errors=None):
        '''Main Menu displays different screens for parameter entry'''
        Gb.config_flow_flag = True

        user_input = self._check_if_from_svc_call(user_input)

        self.step_id = 'menu'
        self.current_menu_step_id = self.step_id
        self.errors = {}

        if user_input is not None:
            self.menu_item_selected[self.menu_page_no] = user_input['menu_item']
            user_input, menu_item = self._menu_text_to_item(user_input, 'menu_item')
            user_input, menu_action = self._menu_text_to_item(user_input, 'menu_action')

            if menu_action == 'exit':
                Gb.config_flow_flag = False
                self.initialize_options_required_flag = False

                if 'restart' in self.config_flow_updated_parms:
                    self.step_id = 'restart_icloud3'
                    return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors={},
                            last_step=False)
                else:
                    Gb.config_flow_parameters_updated = self.config_flow_updated_parms
                    self.config_flow_updated_parms = {''}
                    return self.async_create_entry(title="iCloud3", data={})

            elif menu_action == 'next_page':
                self.menu_page_no += 1
                if self.menu_page_no > 1: self.menu_page_no = 0

            elif 'menu_item' == '':
                pass
            elif menu_item == 'icloud_account':
                return await self.async_step_icloud_account()
            elif menu_item == 'device_list':
                return await self.async_step_device_list()
            elif menu_item == 'event_log_configuration':
                return await self.async_step_event_log_configuration()
            elif menu_item == 'display_text_as':
                return await self.async_step_display_text_as()
            elif menu_item == 'other_parms':
                return await self.async_step_other_parms()
            elif menu_item == 'inzone_intervals':
                return await self.async_step_inzone_intervals()
            elif menu_item == 'waze':
                return await self.async_step_waze_1()
            elif menu_item == 'stationary_zone':
                return await self.async_step_stationary_zone()
            elif menu_item == 'sensors':
                return await self.async_step_sensors()
            elif menu_item == 'action_menu1':
                return await self.async_step_action_menu1()

        menu_msg = {'base': self.menu_msg} if self.menu_msg else {}
        self.menu_msg = ''

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=menu_msg,
                            last_step=False)

#-------------------------------------------------------------------------------------------
    async def async_step_restart_icloud3(self, user_input=None, errors=None):
        '''
        A restart is required due to tracking, devices or sensors changes. Ask if this
        should be done now or later.
        '''
        self.step_id = 'restart_icloud3'
        self.errors = errors or {}
        self.errors_user_input = {}
        _traceha(f'{user_input=} {self.config_flow_updated_parms=}')
        if user_input is not None:
            if user_input['restart_now_later'].startswith('RESTART LATER'):
                self.config_flow_updated_parms.remove('restart')
                Gb.config_flow_parameters_updated = self.config_flow_updated_parms

            else:
                # If the polling loop has been set up, set the restart flag to trigger a restart when
                # no devices are being updated. Otherwise, there were probably no devices to track
                # when first loaded and a direct restart must be done.
                _traceha(f'{Gb.polling_5_sec_loop_running=}')
                Gb.start_icloud3_request_flag = True
                # if Gb.polling_5_sec_loop_running is False:
                    # Gb.iCloud3.__init__()
                    # Gb.hass.async_create_task()
                    # Gb.iCloud3.start_icloud3()

            self.config_flow_updated_parms = {''}

            return self.async_create_entry(title="iCloud3", data={})

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema('restart_icloud3'),
                        errors=self.errors,
                        last_step=False)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  DISPLAY AND HANDLE USER INPUT FORMS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def common_form_handler(self, user_input=None, action_item=None, errors=None):
        '''
        Handle the data verification, error handling and confguration update of
        normal parameter feenry forms, excluding those dealing with icloud and
        device updates.
        '''
        self.errors = errors or {}
        self.errors_user_input = {}

        if user_input is not None:

            # Validate the user_input, update the config file with valid entries
            if action_item is None:
                user_input, action_item = self._action_text_to_item(user_input)

            if action_item == 'cancel':
                return True
            elif self.step_id == 'icloud_account':
                pass
            elif self.step_id == 'device_list':
                user_input = self._get_conf_device_selected(user_input)
            elif self.step_id == 'event_log_configuration':
                user_input = self._validate_evlog_configuration(user_input)
            elif self.step_id == "display_text_as":
                pass
            elif self.step_id == 'other_parms':
                user_input = self._validate_other_parms(user_input)
            elif self.step_id == 'inzone_intervals':
                user_input = self._validate_inzone_intervals(user_input)
            elif self.step_id == "waze_1":
                user_input = self._validate_waze_1(user_input)
            elif self.step_id == "waze_2":
                user_input = self._validate_waze_2(user_input)
            elif self.step_id == "stationary_zone":
                user_input = self._validate_stationary_zone(user_input)
            elif self.step_id == "sensors":
                self._remove_and_create_sensors(user_input)

            # elif self.step_id == 'system_settings':
            #     user_input = self._validate_system_settings(user_input)

            self._update_configuration_file(user_input)

            # Redisplay the menu if there were no errors
            if not self.errors:
                return True

        # Display the config data entry form, any errors will be redisplayed and highlighted
        return False

#-------------------------------------------------------------------------------------------
    async def async_step_event_log_configuration(self, user_input=None, errors=None):
        self.step_id = 'event_log_configuration'
        user_input, action_item = self._action_text_to_item(user_input)

        www_path = f"{Gb.ha_config_directory}/www"
        self.opt_www_directory_list = [f for f in os.listdir(www_path)
                            if os.path.isfile(os.path.join(www_path, f)) is False]

        # option_text_list(self.opt_www_directory_list, ensure_six_items=True)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_other_parms(self, user_input=None, errors=None):
        self.step_id = 'other_parms'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_inzone_intervals(self, user_input=None, errors=None):
        self.step_id = 'inzone_intervals'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_waze_1(self, user_input=None, errors=None):
        self.step_id = 'waze_1'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            if action_item == 'next_page':
                return await self.async_step_waze_2()
            else:
                return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors,
                            last_step=False)

#-------------------------------------------------------------------------------------------
    async def async_step_waze_2(self, user_input=None, errors=None):
        self.step_id = 'waze_2'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors,
                            last_step=True)

#-------------------------------------------------------------------------------------------
    async def async_step_stationary_zone(self, user_input=None, errors=None):
        self.step_id = 'stationary_zone'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_sensors(self, user_input=None, errors=None):
        self.step_id = 'sensors'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  DISPLAY_TEXT_AS HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_display_text_as(self, user_input=None, errors=None):
        self.step_id = 'display_text_as'
        user_input, action_item = self._action_text_to_item(user_input)

        # Reinitialize everything
        if self.dta_selected_idx == -1:
            self.dta_selected_idx = 0
            self.dta_selected_idx_page = [0, 5]
            self.dta_page_no = 0
            idx = -1
            for dta_text in Gb.conf_general[CONF_DISPLAY_TEXT_AS]:
                idx += 1
                self.dta_working_copy[idx] = dta_text

        if user_input is not None:
            user_input = self._option_text_to_parm(user_input, CONF_DISPLAY_TEXT_AS, self.dta_working_copy)
            self.dta_selected_idx = int(user_input[CONF_DISPLAY_TEXT_AS])
            self.dta_selected_idx_page[self.dta_page_no] = self.dta_selected_idx

            if action_item == 'next_page':
                self.dta_page_no = 1 if self.dta_page_no == 0 else 0

            elif action_item == 'select_text_as':
                return await self.async_step_display_text_as_update(user_input)

            elif action_item == 'cancel':
                self.dta_selected_idx = -1
                return await self.async_step_menu()

            elif action_item == 'save':
                idx = -1
                self.dta_selected_idx = -1
                dta_working_copy_list = DEFAULT_GENERAL_CONF[CONF_DISPLAY_TEXT_AS].copy()
                for temp_dta_text in self.dta_working_copy.values():
                    if instr(temp_dta_text,'>'):
                        idx += 1
                        dta_working_copy_list[idx] = temp_dta_text

                user_input[CONF_DISPLAY_TEXT_AS] = dta_working_copy_list

                self._update_configuration_file(user_input)

                return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_display_text_as_update(self, user_input=None, errors=None):
        self.step_id = 'display_text_as_update'
        user_input, action_item = self._action_text_to_item(user_input)

        if action_item == 'cancel':
            return await self.async_step_display_text_as()

        if action_item == 'save':
            text_from = user_input['text_from'].strip()
            text_to   = user_input['text_to'].strip()
            if  text_from and text_to:
                self.dta_working_copy[self.dta_selected_idx] = f"{text_from} > {text_to}"
            else:
                self.dta_working_copy[self.dta_selected_idx] = f"#{self.dta_selected_idx + 1}"

            return await self.async_step_display_text_as()

        if action_item == 'clear_text_as':
            self.dta_working_copy[self.dta_selected_idx] = f"#{self.dta_selected_idx + 1}"

            return await self.async_step_display_text_as()

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  ACTION MENU HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_action_menu1(self, user_input=None, errors=None):
        self.step_id = 'action_menu1'
        return self.async_show_menu(
                    step_id=self.step_id,
                    menu_options = ['action_divider1', 'action_restart', 'action_pause', 'action_resume',
                                    'action_divider2', 'action_reauth', 'action_reset_icloud',
                                    'action_divider3', 'action_goto_menu2', 'action_exit'],
                    )

#-------------------------------------------------------------------------------------------
    async def async_step_action_menu2(self, user_input=None, errors=None):
        self.step_id = 'action_menu2'
        return self.async_show_menu(
                    step_id=self.step_id,
                    menu_options = ['action_divider1', 'action_waze_db_recalc', 'action_waze_db_track',
                                    'action_evlog_export',
                                    'action_divider3', 'action_goto_menu1', 'action_exit'],
                    )

#-------------------------------------------------------------------------------------------
    async def async_step_action_restart(self, user_input=None, errors=None):
        self.step_id = 'action_restart'
        Gb.start_icloud3_request_flag = True
        self.menu_msg = 'action_completed'
        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_step_action_pause(self, user_input=None, errors=None):
        for Device in Gb.Devices_by_devicename.values():
            Device.pause_tracking
        self.menu_msg = 'action_completed'
        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_step_action_resume(self, user_input=None, errors=None):
        for Device in Gb.Devices_by_devicename.values():
            Device.resume_tracking
        self.menu_msg = 'action_completed'
        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_step_action_reauth(self, user_input=None, errors=None):
        return await self.async_step_reauth()

#-------------------------------------------------------------------------------------------
    async def async_step_action_reset_icloud(self, user_input=None, errors=None):
        pyicloud_ic3_interface.pyicloud_reset_session()
        self.menu_msg = 'action_completed'
        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_step_action_waze_db_recalc(self, user_input=None, errors=None):
        if Gb.WazeHist is None:
            return

        if Gb.wazehist_recalculate_time_dist_flag:
            Gb.wazehist_recalculate_time_dist_flag = False
            self.menu_msg = 'action_cancelled'
        else:
            Gb.wazehist_recalculate_time_dist_flag = True
            self.menu_msg = 'action_completed'

        # await self.hass.async_add_executor_job(
        #                         Gb.WazeHist.wazehist_recalculate_time_dist_all_zones)

            self.menu_msg = 'action_completed'
        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_step_action_waze_db_track(self, user_input=None, errors=None):
        if Gb.WazeHist:
            Gb.WazeHist.wazehist_update_track_sensor()
            self.menu_msg = 'action_completed'
        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_step_action_evlog_export(self, user_input=None, errors=None):
        Gb.EvLog.export_event_log()
        self.menu_msg = 'action_completed'
        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_step_action_divider1(self, user_input=None, errors=None):
        if self.step_id == 'action_menu1':
            return await self.async_step_action_menu1()
        else:
            return await self.async_step_action_menu2()

#-------------------------------------------------------------------------------------------
    async def async_step_action_divider2(self, user_input=None, errors=None):
        if self.step_id == 'action_menu1':
            return await self.async_step_action_menu1()
        else:
            return await self.async_step_action_menu2()

#-------------------------------------------------------------------------------------------
    async def async_step_action_divider3(self, user_input=None, errors=None):
        if self.step_id == 'action_menu1':
            return await self.async_step_action_menu1()
        else:
            return await self.async_step_action_menu2()

#-------------------------------------------------------------------------------------------
    async def async_step_action_goto_menu1(self, user_input=None, errors=None):
        return await self.async_step_action_menu1()

#-------------------------------------------------------------------------------------------
    async def async_step_action_goto_menu2(self, user_input=None, errors=None):
        return await self.async_step_action_menu2()

#-------------------------------------------------------------------------------------------
    async def async_step_action_exit(self, user_input=None, errors=None):
        return await self.async_step_menu()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  VALIDATE DATA AND UPDATE CONFIG FILE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _traceui(self, user_input):
        _traceha(f"{user_input=} {self.errors=} ")

    def _update_configuration_file(self, user_input):
        '''
        Update the configuration parameters and write to the icloud3.configuration file
        '''
        updated_parms = {''}
        for pname, pvalue in user_input.items():
            if type(pvalue) is str:
                pvalue = pvalue.strip()
                if pvalue == '.':
                    continue

            if (pname not in self.errors
                    and pname in CONF_PARAMETER_FLOAT):
               pvalue = float(pvalue)

            if pname in Gb.conf_tracking:
                if Gb.conf_tracking[pname] != pvalue:
                    Gb.conf_tracking[pname] = pvalue
                    updated_parms.update(['tracking', 'restart'])

            if pname in Gb.conf_general:
                if Gb.conf_general[pname] != pvalue:
                    Gb.conf_general[pname] = pvalue
                    updated_parms.update(['general'])
                    if 'waze' in self.step_id:
                        updated_parms.update(['waze'])
                    if pname == CONF_LOG_LEVEL:
                        Gb.conf_general[CONF_LOG_LEVEL] = pvalue
                        start_ic3.set_log_level

            if pname in Gb.conf_sensors:
                if Gb.conf_sensors[pname] != pvalue:
                    Gb.conf_sensors[pname] = pvalue
                    updated_parms.update(['sensors'])

            if pname in Gb.conf_profile:
                if Gb.conf_profile[pname] != pvalue:
                    Gb.conf_profile[pname] = pvalue
                    updated_parms.update(['profile'])

        if updated_parms != {''}:
            # If default or converted file, update version so the
            # ic3 parameters are now handled by config_flow
            if Gb.conf_profile[CONF_VERSION] == 0:
                Gb.conf_profile[CONF_VERSION] = 1

            self.config_flow_updated_parms.update(updated_parms)
            start_ic3.write_storage_icloud3_configuration_file()

            self.menu_msg = 'conf_updated'

        return

#-------------------------------------------------------------------------------------------
    def _validate_evlog_configuration(self, user_input):
        '''
        The display_zone_format may contain '(Example: ...). If so, strip it off.
        '''
        user_input = self._option_text_to_parm(user_input, CONF_DISPLAY_ZONE_FORMAT, OPT_DISPLAY_ZONE_FORMAT_KEY_TEXT)
        user_input = self._option_text_to_parm(user_input, CONF_TIME_FORMAT, OPT_TIME_FORMAT_KEY_TEXT)
        user_input = self._strip_special_text_from_user_input(user_input)

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_other_parms(self, user_input):
        '''
        The display_zone_format may contain '(Example: ...). If so, strip it off.
        '''
        # self._traceui(user_input)

        user_input = self._option_text_to_parm(user_input, CONF_UNIT_OF_MEASUREMENT, OPT_UNIT_OF_MEASUREMENT_KEY_TEXT)
        user_input = self._option_text_to_parm(user_input, CONF_LOG_LEVEL, OPT_LOG_LEVEL_KEY_TEXT)
        user_input = self._duration_to_hhmmss(user_input)

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_inzone_intervals(self, user_input):
        '''
        Cycle through the inzone_interval items, validate them and rebuild the inzone_interval
        list in the config file.

        Return = valid inzone_interval diction item as part of the user_input field

        user_input:
            {'iphone': {'hours': 3, 'minutes': 11, 'seconds': 0},
            'ipad': {'hours': 2, 'minutes': 55, 'seconds': 0},
            'watch': {'hours': 0, 'minutes': 44, 'seconds': 0},
            'airpods': {'hours': 0, 'minutes': 33, 'seconds': 0},
            'no_iosapp': {'hours': 0, 'minutes': 22, 'seconds': 0},
            'center_in_zone': True,
            'discard_poor_gps_inzone': True}
        '''

        user_input = self._duration_to_hhmmss(user_input)

        user_input_copy = user_input.copy()
        config_inzone_interval = Gb.conf_general[CONF_INZONE_INTERVALS].copy()

        for pname, pvalue in user_input_copy.items():
            if (pname not in self.errors
                    and pname in config_inzone_interval):
                config_inzone_interval[pname] = pvalue

                user_input.pop(pname)

        user_input[CONF_INZONE_INTERVALS] = config_inzone_interval

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_waze_1(self, user_input):
        '''
        Validate the Waze numeric fields
        '''
        user_input = self._option_text_to_parm(user_input, CONF_DISTANCE_METHOD, OPT_DISTANCE_METHOD_KEY_TEXT)
        user_input = self._option_text_to_parm(user_input, CONF_WAZE_REGION, OPT_WAZE_REGION_KEY_TEXT)
        user_input = self._validate_numeric_field(user_input)
        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_waze_2(self, user_input):
        '''
        Validate the Waze numeric fields
        '''
        user_input = self._option_text_to_parm(user_input, CONF_WAZE_HISTORY_TRACK_DIRECTION, OPT_WAZE_HISTORY_TRACK_DIRECTION_KEY_TEXT)
        user_input = self._validate_numeric_field(user_input)

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_stationary_zone(self, user_input):
        """ Validate the stationary one fields

        user_input:
            {'stat_zone_fname': 'Stationary',
            'stat_zone_still_time': {'hours': 0, 'minutes': 10, 'seconds': 0},
            'stat_zone_inzone_interval': {'hours': 0, 'minutes': 30, 'seconds': 0},
            'stat_zone_base_latitude': '1',
            'stat_zone_base_longitude': '0'}
        """

        user_input = self._duration_to_hhmmss(user_input)
        user_input = self._validate_numeric_field(user_input)

        if CONF_STAT_ZONE_BASE_LATITUDE not in self.errors:
            sbo_latitude = float(user_input[CONF_STAT_ZONE_BASE_LATITUDE])
            if sbo_latitude < -90 or sbo_latitude > 90:
                self.errors[CONF_STAT_ZONE_BASE_LATITUDE] = "stat_zone_base_lat_range_error"
                self.errors_user_input[CONF_STAT_ZONE_BASE_LATITUDE] = user_input[CONF_STAT_ZONE_BASE_LATITUDE]

        if CONF_STAT_ZONE_BASE_LONGITUDE not in self.errors:
            sbo_longitude = float(user_input[CONF_STAT_ZONE_BASE_LONGITUDE])
            if sbo_longitude < -180 or sbo_longitude > 180:
                self.errors[CONF_STAT_ZONE_BASE_LONGITUDE] = "stat_zone_base_long_range_error"
                self.errors_user_input[CONF_STAT_ZONE_BASE_LONGITUDE] = user_input[CONF_STAT_ZONE_BASE_LONGITUDE]

        return user_input

#-------------------------------------------------------------------------------------------
    def _strip_special_text_from_user_input(self, user_input, fld_name=None):
        '''
        The user_input options may contain a special message'' after the actual parameter
        value. If so, strip it off so the field can be updated in the configuration file.

        Special message types:
            - '(Example: exampletext)'
            - '>'

        Returns:
            user_input  - user_input without the example text
        '''

        for pname, pvalue in user_input.items():
            if (fld_name is None
                    or fld_name is not None and fld_name == pname):
                if instr(pvalue, '(Example:'):
                    user_input[pname] = pvalue.split(' (Example:')[0].strip()
                elif instr(pvalue, '>'):
                    user_input[pname] = pvalue.split('>')[0].strip()

        return user_input


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                        ICLOUD ACCOUNT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_icloud_account(self, user_input=None, errors=None):
        self.step_id = 'icloud_account'
        self.errors = errors or {}
        self.errors_user_input = {}

        if Gb.conf_tracking[CONF_DATA_SOURCE] not in OPT_DATA_SOURCE_KEY_TEXT:
            Gb.conf_tracking[CONF_DATA_SOURCE] = f"{ICLOUD},{IOSAPP}"

        try:
            if user_input is not None:
                user_input, action_item = self._action_text_to_item(user_input)
                user_input = self._option_text_to_parm(user_input, CONF_DATA_SOURCE, OPT_DATA_SOURCE_KEY_TEXT)

                if action_item == 'cancel':
                    return await self.async_step_menu()

                elif not self.errors:
                    if user_input[CONF_DATA_SOURCE] == IOSAPP:
                        self._update_configuration_file(user_input)
                        Gb.PyiCloud = None
                        return await self.async_step_menu()

                    self._validate_icloud_account_conf(user_input)

                    if user_input[CONF_DATA_SOURCE] != Gb.conf_tracking[CONF_DATA_SOURCE]:
                        user_input_tm = {CONF_DATA_SOURCE: user_input[CONF_DATA_SOURCE]}
                        self._update_configuration_file(user_input_tm)

                    if self.errors:
                        self.errors_user_input[CONF_USERNAME] = user_input[CONF_USERNAME]
                        self.errors_user_input[CONF_PASSWORD] = user_input[CONF_PASSWORD]

                    elif (action_item == 'log_in_icloud_acct'
                            or user_input[CONF_USERNAME] != Gb.conf_tracking[CONF_USERNAME]
                            or user_input[CONF_PASSWORD] != Gb.conf_tracking[CONF_PASSWORD]):
                        await self._log_into_icloud_account(user_input, self.step_id)

                        if (Gb.PyiCloud and Gb.PyiCloud.requires_2fa):
                            return await self.async_step_reauth()

                    else:
                        self._update_configuration_file(user_input)
                        return await self.async_step_menu()

        except Exception as err:
            log_exception(err)

        self.step_id = 'icloud_account'
        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _validate_icloud_account_conf(self, user_input):
        '''
        Validate the iCloud Account credentials by logging into the iCloud Account via
        pyicloud_ic3. This will set up the account access in the same manner as starting iCloud3.
        The devices associated with FamShr and FmF are also retrieved so they are available
        for selection in the Devices screen.
        '''

        # Make sure the username and password are entered.
        username = user_input[CONF_USERNAME].strip()
        password = user_input[CONF_PASSWORD].strip()

        if username == '':
            self.errors[CONF_USERNAME] = 'required_field'
            self.errors_user_input[CONF_USERNAME] = ''
        if password == '':
            self.errors[CONF_PASSWORD] = 'required_field'
            self.errors_user_input[CONF_PASSWORD] = ''

        if not self.errors:
            self.username = username
            self.password = user_input[CONF_PASSWORD]

        return True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            ICLOUD UTILITIES - LOG INTO ACCOUNT
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def _log_into_icloud_account(self, user_input, called_from_step_id):
        '''
        Log into the icloud account and check to see if a verification code is needed.
        If so, show the verification form, get the code from the user, verify it and
        return to the 'called_from_step_id' (icloud_account).

        Input:
            user_input  = A dictionary with the username and password, or
                            {username: icloudAccountUsername, password: icloudAccountPassword}
                        = {} to use the username/password in the tracking configuration parameters
            called_from_step_id
                        = The step logging into the iCloud account. This step will be returned
                            to when the login is complete.

        Exception:
            The Gb.PyiCloud.requres_2fa must be checked after a login to see if the account
            access needs to be verified. If so, the verification code entry form must be displayed.
                await self._log_into_icloud_account(user_input, self.step_id)

                    if (Gb.PyiCloud
                            and Gb.PyiCloud.requires_2fa):
                        return await self.async_step_icloud_verification_code()

        Returns:
            Gb.Pyicloud object
            Gb.PyiCloud_FamilySharing object
            Gb.PyiCloud_FindMyFriends object
            self.device_opt_famshr_devicename_list & self.device_form_icloud_famf_list =
                    A dictionary with the devicename and identifiers
                    used in the tracking configuration devices icloud_device parameter
        '''


        if CONF_USERNAME in user_input:
            self.username = user_input[CONF_USERNAME]
            self.password = user_input[CONF_PASSWORD]
        else:
            self.username = Gb.conf_tracking[CONF_USERNAME]
            self.password = Gb.conf_tracking[CONF_PASSWORD]

        self.called_from_step_id = called_from_step_id

        try:
            Gb.PyiCloud = await self.hass.async_add_executor_job(
                                PyiCloudService,
                                self.username,
                                self.password,
                                Gb.ha_storage_icloud3,
                                f"{Gb.ha_storage_icloud3}/session",
                                True)

        except (PyiCloudFailedLoginException) as err:
            _LOGGER.error(f"Error logging into iCloud service: {err}")
            Gb.PyiCloud = None
            self.errors = {'base': 'icloud_invalid_auth'}
            return self.async_show_form(step_id=called_from_step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors)

        if Gb.PyiCloud.requires_2fa:
            return

        try:
            # This will set Gb.PyiCloud_FamilySharing object
            Gb.PyiCloud_FamilySharing = await self.hass.async_add_executor_job(
                                    getattr,
                                    Gb.PyiCloud,
                                    "family_sharing_object")

            # This will set Gb.PyiCloud_Find-my-Friends object
            Gb.PyiCloud_FindMyFriends = await self.hass.async_add_executor_job(
                                    getattr,
                                    Gb.PyiCloud,
                                    "find_my_friends_object")

        except (PyiCloudServiceNotActivatedException, PyiCloudNoDevicesException):
            _LOGGER.error(f"No device found in the iCloud account: {self.username}")
            Gb.PyiCloud = None
            self.errors = {'base': "no_devices"}
            return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors)

        if self.called_from_step_id == 'icloud_account':
            Gb.username = self.username
            Gb.password = self.password
            user_input = {CONF_USERNAME: self.username, CONF_PASSWORD: self.password}
            self._update_configuration_file(user_input)

        self.errors   = {'base': 'icloud_logged_into'}
        self.menu_msg = 'icloud_logged_into'

        self._build_device_form_selection_lists()

        if self.called_from_step_id:
            self.step_id = self.called_from_step_id

            return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)
        else:
            return self.async_create_entry(title="iCloud3", data={})


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            ICLOUD VERIFICATION CODE ENTRY FORM
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_reauth(self, user_input=None, errors=None):
        """Ask the verification code to the user."""
        '''
        The iCloud account needs to be verified. Show the code entry form, get the
        code from the user, send the code back to Apple iCloud via pyicloud and get
        a valid code indicator or invalid code error.

        If the code is valid, either:
            - return to the called_from_step_id (icloud_account form) if in the config_flow configuration routine or,
            - issue a 'create_entry' indicating a successful verification. This will return
            to the function it wass called from. This will be when a validation request was
            needed during the normal tracking.

        If invalid, display an error message and ask for the code again.

        Input:
            - called_from_step_id
                    = the step_id in the config_glow if the icloud3 configuration
                        is being updated
                    = None if the rquest is from another regular function during the normal
                        tracking operation.
        '''

        user_input = self._check_if_from_svc_call(user_input)

        self.step_id = config_entries.SOURCE_REAUTH
        self.errors = errors or {}

        if user_input is not None:
            if user_input[CONF_VERIFICATION_CODE]:
                valid_code = await self.hass.async_add_executor_job(
                                Gb.PyiCloud.validate_2fa_code,
                                user_input[CONF_VERIFICATION_CODE])

                # valid_code = (user_input[CONF_VERIFICATION_CODE] == '111111')

                if valid_code:
                    event_msg =(f"{EVLOG_ALERT}iCloud Alert > iCloud Account Verification completed successfully. {valid_code}")
                    post_event(event_msg)

                    start_ic3.set_tracking_method(ICLOUD)
                    Gb.start_icloud3_request_flag = True
                    Gb.authenticated_time = time.time()

                    self.step_id = (self.called_from_step_id
                                    if self.called_from_step_id else 'icloud_account')

                    return self.async_show_form(step_id=self.step_id,
                                                data_schema=self.form_schema(self.step_id),
                                                errors=self.errors)

                else:
                    post_event(f"The Apple ID Verification Code is invalid. {valid_code}")
                    self.errors[CONF_VERIFICATION_CODE] = 'invalid_verification_code'
            else:
                self.step_id = (self.called_from_step_id
                                if self.called_from_step_id else 'icloud_account')

                return self.async_show_form(step_id=self.step_id,
                                            data_schema=self.form_schema(self.step_id),
                                            errors=self.errors)

        schema = vol.Schema({vol.Required(CONF_VERIFICATION_CODE):
                                selector.TextSelector(),})

        return self.async_show_form(step_id=config_entries.SOURCE_REAUTH,
                                    data_schema=schema,
                                    errors=self.errors)

#----------------------------------------------------------------------
    async def show_verification_code_form(self, user_input=None, errors=None):
        '''
        Show the verification_code form
        '''
        return self.async_show_form(step_id='reauth',
                        data_schema=self.form_schema('reauth'),
                        errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            TRACKED DEVICE MENU - DEVICE LIST, DEVICE UPDATE FORMS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_device_list(self, user_input=None, errors=None):
        '''
        Display the list of devices form and the function to be performed
        (add, update, delete) on the selected device.
        '''
        self.step_id = 'device_list'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.add_device_flag = False
        user_input, action_item = self._action_text_to_item(user_input)

        if (Gb.PyiCloud is None
                and ICLOUD in Gb.conf_tracking[CONF_DATA_SOURCE]
                and Gb.conf_tracking[CONF_USERNAME]
                and Gb.conf_tracking[CONF_PASSWORD]):
            await self._log_into_icloud_account({}, self.step_id)

            if (Gb.PyiCloud
                    and Gb.PyiCloud.requires_2fa):
                return await self.async_step_reauth()

        if user_input is None:
            self._build_device_form_selection_lists()

        device_cnt = len(Gb.conf_devices)
        if device_cnt == 0:
            user_input = {'action_item': 'add_device'}
            action_item = 'add_device'

        if user_input is not None:
            if action_item == 'next_page':
                if device_cnt > 5:
                    self.device_list_page_no += 1
                    if self.device_list_page_no > int(device_cnt/5):
                        self.device_list_page_no = 0
                    self.conf_device_selected_idx = self.device_list_page_no * 5

            elif action_item == 'return':
                self.sensor_entity_attrs_changed = {}
                return await self.async_step_menu()

            elif action_item == 'add_device':
                self.sensor_entity_attrs_changed['add_device'] = True
                self.conf_device_selected = DEFAULT_DEVICE_CONF.copy()
                return await self.async_step_add_device()

            elif action_item == 'delete_device':
                self.sensor_entity_attrs_changed['delete_device'] = True
                self._get_conf_device_selected(user_input)
                return await self.async_step_delete_device()

            elif action_item == 'update_device':
                self.sensor_entity_attrs_changed['update_device'] = True
                self._get_conf_device_selected(user_input)
                return await self.async_step_update_device()

        menu_msg = {'base': self.menu_msg} if self.menu_msg else {}
        self.menu_msg = ''

        self._prepare_device_selection_list()
        self.sensor_entity_attrs_changed = {}

        self.step_id = 'device_list'
        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=menu_msg,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    def _get_conf_device_selected(self, user_input):
        '''
        Cycle through the devices listed on the device_list screen. If one was selected,
        get it's device name and position in the Gb.config_tracking[DEVICES] parameter.

        If it is deleted, pop it from the config parameter and return.
        If it is being added, add a default entry to the config parameter and return that entry.
        If it is being updated, return that entry.

        Returns:
            - True = The device is being added or updated. Display the device update form.
            - False = The device was deleted. Rebuild the list and redisplay the screen.

        '''
        # Displayed info is devicename > Name, FamShr device info, FmF device info,
        # iOSApp device. Get devicename.
        devicename_selected = user_input[CONF_DEVICES]

        first_space_pos = devicename_selected.find(' ')
        if first_space_pos > 0:
            devicename_selected = devicename_selected[:first_space_pos]

        for form_devices_list_index, devicename in enumerate(self.form_devices_list_devicename):

            if devicename_selected == devicename:
                self.conf_device_selected = Gb.conf_devices[form_devices_list_index]
                self.conf_device_selected_idx = form_devices_list_index
                break

        user_input[CONF_DEVICES] = self.conf_device_selected[CONF_IC3_DEVICENAME]

        self.conf_device_selected_idx = form_devices_list_index

        return True

#-------------------------------------------------------------------------------------------
    async def async_step_delete_device(self, user_input=None, errors=None):
        '''
        Delete the device from the tracking devices list and adjust the device index
        if necessary

        Display a confirmation form and then delete the device
        '''
        self.step_id = 'delete_device'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = self._action_text_to_item(user_input)

        if user_input is not None:
            if action_item == 'delete_device_yes':
                self._process_delete_device_request()

                self.config_flow_updated_parms.update(['tracking', 'restart'])

            return await self.async_step_device_list()

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema('delete_device'),
                        errors=self.errors,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    def _process_delete_device_request(self):
        """ Delete the device_tracker entity and associated ic3 configuration """

        devicename = self.conf_device_selected[CONF_IC3_DEVICENAME]
        self._remove_device_tracker_entity(devicename)

        Gb.conf_devices.pop(self.conf_device_selected_idx)
        self.form_devices_list_all.pop(self.conf_device_selected_idx)
        devicename = self.form_devices_list_devicename.pop(self.conf_device_selected_idx)

        start_ic3.write_storage_icloud3_configuration_file()

        device_cnt = len(self.form_devices_list_devicename) - 1
        if self.conf_device_selected_idx > device_cnt:
            self.conf_device_selected_idx = device_cnt
        if self.conf_device_selected_idx < 5:
            self.device_list_page_no = 0

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            TRACKED DEVICE MENU - DEVICE LIST, DEVICE UPDATE FORMS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_add_device(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'add_device'
        self.errors = errors or {}
        self.errors_user_input = {}

        user_input, action_item = self._action_text_to_item(user_input)
        user_input = self._option_text_to_parm(user_input, CONF_TRACKING_MODE, OPT_TRACKING_MODE_KEY_TEXT)
        user_input = self._option_text_to_parm(user_input, CONF_DEVICE_TYPE, APPLE_DEVICE_TYPE_TO_FNAME)

        if user_input is not None:
            if action_item == 'cancel':
                return await self.async_step_device_list()

            self._validate_devicename(user_input)

            if not self.errors:
                self.conf_device_selected.update(user_input)

                if user_input[IOSAPP] is False:
                    self.conf_device_selected[CONF_INZONE_INTERVAL] = DEFAULT_GENERAL_CONF[CONF_INZONE_INTERVALS][CONF_NO_IOSAPP]
                    self.conf_device_selected[CONF_IOSAPP_DEVICE] = 'None'
                else:
                    device_type = user_input[CONF_DEVICE_TYPE]
                    self.conf_device_selected[CONF_INZONE_INTERVAL] = DEFAULT_GENERAL_CONF[CONF_INZONE_INTERVALS][device_type]

                self.conf_device_selected.pop(IOSAPP)

                self.step_id = 'update_device'

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    async def async_step_update_device(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'update_device'
        self.errors = errors or {}
        self.errors_user_input = {}

        user_input, action_item = self._action_text_to_item(user_input)
        user_input = self._option_text_to_parm(user_input, CONF_FAMSHR_DEVICENAME, self.device_opt_famshr_text_by_fname)
        user_input = self._option_text_to_parm(user_input, CONF_FMF_EMAIL, self.device_opt_fmf_text_by_email)
        user_input = self._option_text_to_parm(user_input, CONF_IOSAPP_DEVICE, self.device_opt_iosapp_text_by_entity_id)
        user_input = self._option_text_to_parm(user_input, CONF_DEVICE_TYPE, APPLE_DEVICE_TYPE_TO_FNAME)

        if user_input is not None:
            if action_item == 'cancel':
                return await self.async_step_device_list()

            user_input  = self._duration_to_hhmmss(user_input)
            user_input  = self._validate_devicename(user_input)
            user_input  = self._validate_update_device(user_input)
            change_flag = self._was_device_data_changed(user_input)

            if not self.errors:
                if change_flag:
                    self.conf_device_selected.update(user_input)

                    # Update the configuration file
                    if 'add_device' in self.sensor_entity_attrs_changed:
                        devicename = self.conf_device_selected[CONF_IC3_DEVICENAME]
                        Gb.conf_devices.append(self.conf_device_selected)
                        self.conf_device_selected_idx = len(Gb.conf_devices) - 1

                        # Add the new device to the device_list form and and set it's position index
                        self.form_devices_list_all.append(self._format_device_list_item(self.conf_device_selected))
                        self.form_devices_list_devicename.append(devicename)

                        if self.device_list_page_no < int(self.conf_device_selected_idx/5):
                            self.device_list_page_no += 1
                        self.device_list_page_selected_idx[self.device_list_page_no] = \
                            self.conf_device_selected_idx
                    else:
                        Gb.conf_devices[self.conf_device_selected_idx] = self.conf_device_selected

                    start_ic3.write_storage_icloud3_configuration_file()

                    # Update the device_tracker & sensor entities now that the configuration has been updated
                    if 'add_device' in self.sensor_entity_attrs_changed:
                        self._create_device_tracker_and_sensor_entities(devicename, self.conf_device_selected)
                    else:
                        self._update_changed_sensor_entities()

                    self.menu_msg = 'conf_updated'
                    self.config_flow_updated_parms.update(['tracking', 'restart'])

                return await self.async_step_device_list()

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors,
                        last_step=True)

#-------------------------------------------------------------------------------------------
    def _validate_devicename(self, user_input):
        '''
        Validate the add device parameters
        '''
        self.errors = {}
        user_input = self._option_text_to_parm(user_input, CONF_TRACKING_MODE, OPT_TRACKING_MODE_KEY_TEXT)
        user_input = self._strip_special_text_from_user_input(user_input, CONF_IC3_DEVICENAME)
        devicename = user_input[CONF_IC3_DEVICENAME] = slugify(user_input[CONF_IC3_DEVICENAME])

        if devicename.strip() == '':
            self.errors[CONF_IC3_DEVICENAME] = 'required_field'
            return user_input

        other_ic3_devicename_list = self.form_devices_list_devicename.copy()
        if other_ic3_devicename_list:
            current_ic3_devicename = Gb.conf_devices[self.conf_device_selected_idx][CONF_IC3_DEVICENAME]
            if self.add_device_flag is False:
                other_ic3_devicename_list.remove(current_ic3_devicename)

        # Already used if the new ic3_devicename is in the devicename list
        if devicename in other_ic3_devicename_list:
            self.errors[CONF_IC3_DEVICENAME] = 'duplicate_ic3_devicename'
            self.errors_user_input[CONF_IC3_DEVICENAME] = user_input[CONF_IC3_DEVICENAME]
            # return user_input

        # Already used if the new ic3_devicename is in the ha device_tracker entity list
        elif (devicename in self.device_trkr_by_entity_id_all
                and self.device_trkr_by_entity_id_all[devicename] != DOMAIN):
            self.errors[CONF_IC3_DEVICENAME] = 'duplicate_other_devicename'
            self.errors_user_input[CONF_IC3_DEVICENAME] = (f"{user_input[CONF_IC3_DEVICENAME]} > Used in Integration "
                                                f"{self.device_trkr_by_entity_id_all[devicename]}")
        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_update_device(self, user_input):
        """ Validate the device parameters

            Sets:
                self.error[] for fields that are in error
            Returns:
                user_input
                change_flag: True if a field was changed
                change_fname_flag: True if the fname was changed and the device_tracker entity needs to be updated
                change_tfz_flag: True if the track_fm_zones zone was changed and the sensors need to be updated
        """
        self.errors = {}
        user_input = self._option_text_to_parm(user_input, CONF_TRACKING_MODE, OPT_TRACKING_MODE_KEY_TEXT)

        ic3_devicename = user_input[CONF_IC3_DEVICENAME]
        self.ic3_devicename_being_updated = ic3_devicename

        user_input[CONF_FNAME] = user_input[CONF_FNAME].strip()
        if user_input[CONF_FNAME] == '':
            self.errors[CONF_FNAME] = 'required_field'

        # Check to make sure either the iCloud Device or iosApp device was entered
        # You must have one of them to enable tracking
        if (user_input[CONF_FAMSHR_DEVICENAME].strip() == ''):
            user_input[CONF_FAMSHR_DEVICENAME] = 'None'

        if (user_input[CONF_FMF_EMAIL].strip() == ''):
            user_input[CONF_FMF_EMAIL] = 'None'

        if (user_input[CONF_IOSAPP_DEVICE].strip() == ''):
            user_input[CONF_IOSAPP_DEVICE] = 'None'

        if (user_input[CONF_FAMSHR_DEVICENAME] == 'None'
                and user_input[CONF_FMF_EMAIL] == 'None'
                and user_input[CONF_IOSAPP_DEVICE] == 'None'):
            self.errors['base'] = 'required_field_device'

        if (user_input[CONF_PICTURE].startswith('select')
                or user_input[CONF_PICTURE].startswith('━')):
            user_input[CONF_PICTURE] = ''

        # Handle track_from_zone changes
        track_from_zones = []

        for zone, zone_name in self.opt_zone_name_key_text.items():
            if (zone in user_input[CONF_TRACK_FROM_ZONES]
                    and zone != '.'):
                track_from_zones.append(zone)

        # Put 'home' at the end of the list
        if 'home' in track_from_zones:
            track_from_zones.remove('home')
        track_from_zones.append('home')
        user_input[CONF_TRACK_FROM_ZONES] = track_from_zones

        return user_input

#-------------------------------------------------------------------------------------------
    def _was_device_data_changed(self, user_input):
        """ Cycle thru old and new data and identify changed fields

            Returns:
                True if anything was changed
            Updates:
                sensor_entity_attrs_changed based on changes detected
        """

        change_flag = False
        if not self.errors:
            self.sensor_entity_attrs_changed[CONF_IC3_DEVICENAME]  = self.conf_device_selected[CONF_IC3_DEVICENAME]
            self.sensor_entity_attrs_changed['new_ic3_devicename'] = user_input[CONF_IC3_DEVICENAME]

            for pname, pvalue in self.conf_device_selected.items():
                if pname not in user_input or user_input[pname] != pvalue:
                    change_flag = True

                if pname == CONF_FNAME and user_input[CONF_FNAME] != pvalue:
                    self.sensor_entity_attrs_changed[CONF_FNAME] = user_input[CONF_FNAME]

                if pname == CONF_TRACK_FROM_ZONES and user_input[CONF_TRACK_FROM_ZONES] != pvalue:
                    new_tfz_zones_list, remove_tfz_zones_list = \
                                self._devices_form_identify_new_and_removed_tfz_zones(user_input)

                    self.sensor_entity_attrs_changed['new_tfz_zones']    = new_tfz_zones_list
                    self.sensor_entity_attrs_changed['remove_tfz_zones'] = remove_tfz_zones_list

        return change_flag

#-------------------------------------------------------------------------------------------
    def _update_changed_sensor_entities(self):
        """ Update the track_fm_zone and device_tracker sensors if needed"""

        # Use the current ic3_devicename since that is how the Device & DeviceTracker objects with the
        # device_tracker and sensor entities are stored. If the devicename was also changed, the
        # device_tracker and sensor entity names will be changed later
        devicename = self.sensor_entity_attrs_changed[CONF_IC3_DEVICENAME]
        new_devicename = self.sensor_entity_attrs_changed['new_ic3_devicename']

        # Remove the new track_fm_zone sensors just unchecked
        if 'remove_tfz_zones' in self.sensor_entity_attrs_changed:
            remove_tfz_zones_list = self.sensor_entity_attrs_changed['remove_tfz_zones']
            self._remove_track_fm_zone_sensor_entity(devicename, remove_tfz_zones_list)

        # Create the new track_fm_zone sensors just checked
        if 'new_tfz_zones' in self.sensor_entity_attrs_changed:
            new_tfz_zones_list = self.sensor_entity_attrs_changed['new_tfz_zones']
            self._create_track_fm_zone_sensor_entity(devicename, new_tfz_zones_list)

        # fname was changed - change the fname of device_tracker and all sensors to the new fname
        if (devicename == new_devicename
                and CONF_FNAME in self.sensor_entity_attrs_changed):
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
            DeviceTracker.update_entity_attribute(new_fname=self.conf_device_selected[CONF_FNAME])

            for sensor, Sensor in Gb.Sensors_by_devicename[devicename].items():
                Sensor.update_entity_attribute(new_fname=self.conf_device_selected[CONF_FNAME])

            for sensor, Sensor in Gb.Sensors_by_devicename_from_zone[devicename].items():
                Sensor.update_entity_attribute(new_fname=self.conf_device_selected[CONF_FNAME])

        # devicename was changed - delete device_tracker and all sensors for devicename and add them for new_devicename
        if devicename != new_devicename:
            # if devicename in Gb.restore_state_devices:
            #     Gb.restore_state_devices[new_devicename]           = Gb.restore_state_devices[devicename].copy()
            # Gb.DeviceTrackers_by_devicename[new_devicename]    = Gb.DeviceTrackers_by_devicename[devicename]
            # Gb.Sensors_by_devicename[new_devicename]           = Gb.Sensors_by_devicename[devicename].copy()
            # Gb.Sensors_by_devicename_from_zone[new_devicename] = Gb.Sensors_by_devicename_from_zone[devicename].copy()

            # # self._remove_device_tracker_entity(devicename)

            # DeviceTracker = Gb.DeviceTrackers_by_devicename[new_devicename]

            # for sensor, Sensor in Gb.Sensors_by_devicename[new_devicename].items():
            #     Sensor.devicename    = new_devicename
            #     Sensor.entity_name   = f"{new_devicename}_{Sensor.sensor}"
            #     Sensor.entity_id     = f"sensor.{Sensor.entity_name}"
            #     Sensor.device_id     = f"{DOMAIN}_{new_devicename}"
            #     Sensor.default_value = Gb.restore_state_devices[new_devicename]['sensors'][Sensor.sensor_base]

            # for sensor, Sensor in Gb.Sensors_by_devicename_from_zone[new_devicename].items():
            #     Sensor.devicename    = new_devicename
            #     Sensor.entity_name   = f"{new_devicename}_{Sensor.sensor}"
            #     Sensor.entity_id     = f"sensor.{Sensor.entity_name}"
            #     Sensor.device_id     = f"{DOMAIN}_{new_devicename}"
            #     Sensor.default_value = Gb.restore_state_devices[new_devicename][f'from_zone_{Sensor.from_zone}'][Sensor.sensor_base]

            self.conf_device_selected[CONF_IC3_DEVICENAME] = new_devicename
            Gb.conf_devices[self.conf_device_selected_idx]    = self.conf_device_selected

            start_ic3.write_storage_icloud3_configuration_file()
            self._create_device_tracker_and_sensor_entities(new_devicename, self.conf_device_selected)
            self._remove_device_tracker_entity(devicename)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            DEVICES LIST FORM, DEVICE UPDATE FORM SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _build_device_form_selection_lists(self):
        """ Setup the option lists used to select device parameters """

        self._get_device_opt_picture_file_name_list()
        self._get_device_opt_iosapp_entity_list()
        self._get_zone_list()

        self._get_famshr_devices_list()
        self._get_fmf_devices_list()

#----------------------------------------------------------------------
    def _get_famshr_devices_list(self):
        """ Cycle through famshr data and get devices that can be tracked for the
            icloud device selection list
        """
        self.device_opt_famshr_text_by_fname = OPT_LIST_KEY_TEXT_NONE.copy()

        if Gb.PyiCloud is None:
            return

        devices_desc = start_ic3.get_famshr_devices()
        self.device_opt_famshr_text_by_fname.update(devices_desc[2])

#----------------------------------------------------------------------
    def _get_fmf_devices_list(self):
        '''
        Cycle through fmf following, followers and contact details data and get
        devices that can be tracked for the icloud device selection list
        '''

        self.device_opt_fmf_text_by_email = OPT_LIST_KEY_TEXT_NONE.copy()

        if Gb.PyiCloud is None:
            return

        devices_desc = start_ic3.get_fmf_devices()
        self.device_opt_fmf_text_by_email.update(devices_desc[2])

#----------------------------------------------------------------------
    def _get_device_opt_iosapp_entity_list(self):
        '''
        Cycle through the /config/.storage/core.entity_registry file and return
        the entities for platform ('mobile_app', 'ios', etc)
        '''

        # Build dict of all HA device_tracker entity devicenames ({devicename: platform})
        iosapp_entities, iosapp_entity_data = entity_io.get_entity_registry_data(domain='device_tracker')
        self.device_trkr_by_entity_id_all = {entity_io._base_entity_id(k): v['platform']
                                            for k, v in iosapp_entity_data.items()}

        # Build dict of ios app device_tracker entity devicenames ({devicename: entity_id > fname})
        iosapp_entities, iosapp_entity_data = entity_io.get_entity_registry_data(platform='mobile_app', domain='device_tracker')
        self.device_opt_iosapp_text_by_entity_id = {entity_io._base_entity_id(k): (f"{v[ENTITY_ID]} > {v['original_name']}")
                                                        for k, v in iosapp_entity_data.items()}
        self.device_opt_iosapp_text_by_entity_id.update(OPT_IOSAPP_DEVICE_KEY_TEXT)

        return

#-------------------------------------------------------------------------------------------
    def _prepare_device_selection_list(self):
        '''
        Rebuild the device list for displaying on the devices list form. This is necessary
        since the parameters displayed may have been changed. Update the default values for
        each page for the device selected on each page.
        '''
        self.form_devices_list_all = []
        self.form_devices_list_displayed = []
        self.form_devices_list_devicename = []

        # Format all the device info to be listed on the form
        for conf_device_data in Gb.conf_devices:
            conf_device_data[CONF_IC3_DEVICENAME] = conf_device_data[CONF_IC3_DEVICENAME].replace(' ', '_')
            self.form_devices_list_all.append(self._format_device_list_item(conf_device_data))
            self.form_devices_list_devicename.append(conf_device_data[CONF_IC3_DEVICENAME])

        # No devices in config, reset to initial conditions
        if self.form_devices_list_all == []:
            self.conf_device_selected_idx = 0
            self.device_list_page_no   = 0
            self.device_list_page_selected_idx[0] = 0
            return

        # Build the device-list page items
        device_from_pos = self.device_list_page_no * 5
        self.form_devices_list_displayed = self.form_devices_list_all[device_from_pos:device_from_pos+5]

        # Build list of devices on next page
        device_from_pos = device_from_pos + 5
        if device_from_pos >= len(self.form_devices_list_devicename):
            device_from_pos = 0
        self.next_page_devices_list = ", ".join(self.form_devices_list_devicename[device_from_pos:device_from_pos+5])

        # Save the selected item info just updated to be used in reselecting the same item via the default value
        self.device_list_page_selected_idx[self.device_list_page_no] = self.conf_device_selected_idx

#-------------------------------------------------------------------------------------------
    def _format_device_list_item(self, conf_device_data):
        """ Format the text that is displayed for the device on the device_list form """

        device_info  = (f"{conf_device_data[CONF_IC3_DEVICENAME]}{RARROW}")

        if conf_device_data[CONF_TRACKING_MODE] == 'monitor':
            device_info += "MONITOR, "
        elif conf_device_data[CONF_TRACKING_MODE] == 'inactive':
            device_info += "INACTIVE, "

        device_info += f"{conf_device_data[CONF_FNAME]}"

        if conf_device_data[CONF_FAMSHR_DEVICENAME] != 'None':
            device_info +=  f", FamShr-({conf_device_data[CONF_FAMSHR_DEVICENAME]})"

        if conf_device_data[CONF_FMF_EMAIL] != 'None':
            device_info +=  f", FmF-({conf_device_data[CONF_FMF_EMAIL]})"

        if conf_device_data[CONF_IOSAPP_DEVICE] != 'None':
            device_info +=  f", iOSApp-({conf_device_data[CONF_IOSAPP_DEVICE]})"

        return device_info

#-------------------------------------------------------------------------------------------
    def _get_device_opt_picture_file_name_list(self):

        self.device_opt_picture_file_name_list = ['None']

        try:
            self.device_opt_picture_file_name_list.extend(
                    [x for x in os.listdir(f"{Gb.ha_config_directory}/www")
                            if (x.endswith('.png') or x.endswith('.jpg'))])

        except:
            pass

        # option_text_list(self.device_opt_picture_file_name_list, ensure_six_items=True)

#-------------------------------------------------------------------------------------------
    def _get_zone_list(self):

        self.opt_zone_name_key_text = OrderedDict()
        with open(Gb.entity_registry_file, 'r') as f:
            entity_reg_data     = json.loads(f.read())
            zone_entities = [x for x in entity_reg_data['data']['entities'] if x['platform'] == 'zone']

        for zone_entity in zone_entities:
            zone      = zone_entity['entity_id'].replace('zone.', '')
            if (zone and zone != 'home'):
                zone_name = zone.title().replace('_', '')
                self.opt_zone_name_key_text[zone] = zone_name
        self.opt_zone_name_key_text['home'] = 'Home'

        zone_entity_ids, zone_entity_data = entity_io.get_entity_registry_data(platform=ZONE)
        opt_zone_name_key_text = {k[5:]:f"{k[5:].title().replace('_', '')}" for k in zone_entity_ids}

        dummy_key = ''
        for i in range(6 - len(self.opt_zone_name_key_text)):
            dummy_key += '.'
            self.opt_zone_name_key_text[dummy_key] = '.'

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#      ROUTINES THAT SUPPORT ADD & REMOVE SENSOR AND DEVICE_TRACKER ENTITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _remove_and_create_sensors(self, user_input):
        """ Remove unchecked sensor entities and create newly checked sensor entities """

        new_sensors_list, remove_sensors_list = \
                self._sensor_form_identify_new_and_removed_sensors(user_input)
        self._remove_sensor_entity(remove_sensors_list)

        for conf_device in Gb.conf_devices:
            devicename  = conf_device[CONF_IC3_DEVICENAME]
            self._create_sensor_entity(devicename, conf_device, new_sensors_list)

#-------------------------------------------------------------------------------------------
    def _create_device_tracker_and_sensor_entities(self, devicename, conf_device):
        """ Create a device and all of it's sensors in the ha entity registry

            Create device_tracker.[devicename] and all sensor.[devicename]_[sensor_name]
            associated with the device.
        """

        # devicename = conf_device[CONF_IC3_DEVICENAME]

        NewDeviceTrackers = []
        if devicename in Gb.DeviceTrackers_by_devicename:
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
        else:
            DeviceTracker = ic3_device_tracker.iCloud3DeviceTracker(devicename, conf_device)

        if DeviceTracker is None:
            return

        Gb.DeviceTrackers_by_devicename[devicename] = DeviceTracker
        NewDeviceTrackers.append(DeviceTracker)

        Gb.async_add_entities_device_tracker(NewDeviceTrackers, True)

        sensors_list = self._get_all_sensors_list()
        self._create_sensor_entity(devicename, conf_device, sensors_list)

#-------------------------------------------------------------------------------------------
    def _remove_device_tracker_entity(self, devicename):
        """ Remove a specific device from the ha entity registry

            Remove device_tracker.[devicename] and all sensor.[devicename]_[sensor_name]
            associated with the device.

            devicename:
                devicename to be removed
        """

        DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
        DeviceTracker.remove_device_tracker()

        for sensor, Sensor in Gb.Sensors_by_devicename[devicename].items():
            Sensor.remove_entity()
        for sensor, Sensor in Gb.Sensors_by_devicename_from_zone[devicename].items():
            Sensor.remove_entity()

#-------------------------------------------------------------------------------------------
    def _devices_form_identify_new_and_removed_tfz_zones(self, user_input):
        """ Determine checked/unchecked track_fm_zones """

        new_tfz_zones_list    = []
        remove_tfz_zones_list = []     # base device sensors
        old_tfz_zones_list    = self.conf_device_selected[CONF_TRACK_FROM_ZONES]
        ui_tfz_zones_list     = user_input[CONF_TRACK_FROM_ZONES]

        # Cycle thru the devices tfz zones before the update to get a list of new
        # and removed zones
        for zone in Gb.Zones_by_zone.keys():
            if zone in ui_tfz_zones_list and zone not in old_tfz_zones_list:
                new_tfz_zones_list.append(zone)
            elif zone in old_tfz_zones_list and zone not in ui_tfz_zones_list:
                remove_tfz_zones_list.append(zone)

        return new_tfz_zones_list, remove_tfz_zones_list

#-------------------------------------------------------------------------------------------
    def _remove_track_fm_zone_sensor_entity(self, devicename, remove_tfz_zones_list):
        """ Remove the all tfz sensors for all of the just unchecked zones"""

        if remove_tfz_zones_list == []:
            return

        device_tfz_sensors = Gb.Sensors_by_devicename_from_zone.get(devicename)

        if device_tfz_sensors is None:
            return

        # Cycle through the zones that are no longer tracked from for the device, then cycle
        # through the Device's sensor list and remove all track_from_zone sensors ending with
        # that zone.
        for zone in remove_tfz_zones_list:
            for sensor, Sensor in device_tfz_sensors.items():
                if (sensor.endswith(f"_{zone}")
                        and Sensor.entity_removed_flag is False):
                    Sensor.remove_entity()

#-------------------------------------------------------------------------------------------
    def _create_track_fm_zone_sensor_entity(self, devicename, new_tfz_zones_list):
        """ Add tfz sensors for all zones that were just checked

            This must be done after the devices user_input parameters have been updated
        """

        if new_tfz_zones_list == []:
            return

        # Cycle thru each new zone and then cycle thru the track_from_zone sensors
        # Then add that sensor for the zones just checked
        new_sensors_list = []
        for sensor in Gb.conf_sensors[CONF_TRACK_FROM_ZONES]:
            new_sensors_list.append(sensor)

        # NewZones = ic3_sensor.create_sensors(new_sensor_list, devicename_list=[devicename])
        NewZones = ic3_sensor.create_sensors(devicename, self.conf_device_selected, new_sensors_list)

        if NewZones is not []:
            Gb.async_add_entities_sensor(NewZones, True)

#-------------------------------------------------------------------------------------------
    def _sensor_form_identify_new_and_removed_sensors(self, user_input):
        """ add newly checked/delete newly unchecked ha sensor entities """

        new_sensors_list    = []
        remove_sensors_list = []     # base device sensors
        for sensor_group, sensor_list in user_input.items():
            if sensor_group not in Gb.conf_sensors:
                continue
            if user_input[sensor_group] == Gb.conf_sensors[sensor_group]:
                continue

            # Cycle thru the sensors now in the user_input sensor_group
            # Get list of sensors to be added
            for sensor in sensor_list:
                if sensor not in Gb.conf_sensors[sensor_group]:
                    new_sensors_list.append(sensor)

            # Get list of sensors to be removed
            for sensor in Gb.conf_sensors[sensor_group]:
                if sensor not in sensor_list:
                    remove_sensors_list.append(sensor)

        return new_sensors_list, remove_sensors_list

#-------------------------------------------------------------------------------------------
    def _remove_sensor_entity(self, remove_sensors_list, select_devicename=None):
        """ Delete sensors from the ha entity registry and ic3 dictionaries

            remove_sensors_list:
                    list of the sensors to be deleted
            selected_devicename:
                    specified       - only delete this devicename's sensors
                    not_specified   - delete the sensors in the remove_sensors_list from all devices
        """

        if remove_sensors_list == []:
            return

        for devicename, devicename_sensors in Gb.Sensors_by_devicename.items():
            if select_devicename and select_devicename != devicename:
                continue

            for sensor in remove_sensors_list:

                # Remove non-track_from_zone sensors
                if sensor.startswith('tfz_') is False:
                    if sensor not in devicename_sensors:
                        continue
                    Sensor = devicename_sensors[sensor]
                    if Sensor.entity_removed_flag is False:
                        Sensor.remove_entity()

                    continue

                # Remove track_from_zone sensors for all zones. We have to cycle through
                # all of the sensors to get all of the zones since the track_from_zone list may
                # have changed since the sensors were created
                tfz_Sensors = [v for k, v in Gb.Sensors_by_devicename_from_zone[devicename].items()
                                if sensor.replace('tfz_', '') == k[:k.rfind("_")]]

                for Sensor in tfz_Sensors:
                    if Sensor.entity_removed_flag is False:
                        Sensor.remove_entity()

#-------------------------------------------------------------------------------------------
    def _create_sensor_entity(self, devicename, conf_device, new_sensors_list):
        """ Add sensors that were just checkeds """

        if new_sensors_list == []:
            return

        NewSensors = ic3_sensor.create_sensors(devicename, conf_device, new_sensors_list)

        if NewSensors == []:
            return

        Gb.async_add_entities_sensor(NewSensors, True)

#-------------------------------------------------------------------------------------------
    def _get_all_sensors_list(self):
        """ Get a list of all sensors from the ic3 config file  """

        sensors_list = []
        for sensor_group, sensor_list in Gb.conf_sensors.items():
            for sensor in Gb.conf_sensors[sensor_group]:
                sensors_list.append(sensor)

        return sensors_list


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                      MISCELLANEOUS SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _menu_text_to_item(self, user_input, selection_list):
        '''
        Convert the text of the menu item selected to it's key name.

        selection_list - Field name in user_input to use:
            ''menu_item' 'menu_action'
        '''

        if user_input is None:
            return None, None

        menu_text = None
        if selection_list in user_input:
            menu_text = user_input[selection_list]
            if menu_text.startswith('NEXT PAGE'):
                menu_item = 'next_page'
            else:
                try:
                    menu_item = [k for k, v in MENU_KEY_TEXT.items() if v == menu_text][0]
                except:
                    menu_item = menu_text.split(' -')[0].lower().replace(' ', '_')
            user_input.pop(selection_list)
        else:
            menu_item = self.menu_item_selected

        return user_input, menu_item

#--------------------------------------------------------------------
    def _action_text_to_item(self, user_input):
        '''
        Convert the text of the item selected to it's key name.
        '''

        if user_input is None:
            return None, None

        action_text = None
        if 'opt_action' in user_input:
            action_text = user_input['opt_action']
            if action_text.startswith('NEXT PAGE'):
                action_item = 'next_page'
            else:
                try:
                    action_item = [k for k, v in OPT_ACTION_KEY_TEXT.items() if v == action_text][0]
                except:
                    action_item = action_text.split(' -')[0].lower().replace(' ', '_')
            user_input.pop('opt_action')
        else:
            action_item = None

        if action_item == 'cancel':
            self.menu_msg = ''

        return user_input, action_item

#-------------------------------------------------------------------------------------------
    def _check_if_from_svc_call(self, user_input):
        '''
        See if this entry is directly from iCloud3 Service Call. If so, initialize the
        general fields and prepare for starting an Options Flow Handler.
        '''
        if self.initialize_options_required_flag:
            self.initialize_options()

        if (user_input is not None
            and 'icloud3_service_call' in user_input):
                user_input = None

        return user_input

#-------------------------------------------------------------------------------------------
    def _parm_or_error_msg(self, pname, conf_group=CF_DATA_GENERAL, conf_dict_variable=None):
        '''
        Determine the value that should be displayed in the config_flow parameter entry screen based
        on whether it was entered incorrectly and has an error message.

        Input:
            conf_group
        Return:
            Value in errors if it is in errors
            Value in Gb.conf_general[CONF_pname] if it is valid
        '''
        # pname is in the 'Profile' data fields
        # Example: [profile][version
        if conf_group == CF_PROFILE:
            return self.errors_user_input.get(pname) or Gb.conf_profile[pname]

        # pname is in the 'Tracking' data fields
        # Example: [data][general][tracking][username]
        # Example: [data][general][tracking][devices]
        elif conf_group == CF_DATA_TRACKING:
            return self.errors_user_input.get(pname) or Gb.conf_tracking[pname]

        # pname is in a dictionary variable in the 'General Data' data fields grupo. It is a dictionary variable.
        # Example: [data][general][inzone_intervals][phone]
        elif conf_dict_variable is not None:
            pvalue = self.errors_user_input.get(pname) or Gb.conf_data[conf_group][conf_dict_variable][pname]

        # pname is in a dictionary variable in the 'General Data' data fields group. It is a non-dictionary variable.
        # Example: [data][general][unit_of_measurement]
        else:
            pvalue = self.errors_user_input.get(pname) or Gb.conf_data[conf_group][pname]
            if pname in CONF_PARAMETER_FLOAT:
                pvalue = str(pvalue).replace('.0', '')

        return pvalue

#-------------------------------------------------------------------------------------------
    def _parm_or_device(self, pname, suggested_value=''):
        parm_displayed = self.errors_user_input.get(pname) \
                            or self.user_input_multi_form.get(pname) \
                            or self.conf_device_selected.get(pname) \
                            or suggested_value
        parm_displayed = ' ' if parm_displayed == '' else parm_displayed

        return parm_displayed

#-------------------------------------------------------------------------------------------
    def _option_parm_to_text(self, pname, option_list_key_text):
        '''
        Returns the full text string displayed in the config_flow options list for the parameter
        value in the configuration parameter file for the parameter name.

        pname - The name of the config parameter
        option_list_key_text - The option list displayed

        Example:
            pname = unit_of_measure field in conf record = 'mi'
            um_key_text = {'mi': 'miles', 'km': 'kilometers'}
        Return:
            'miles'
        '''

        try:
            pvalue_key = pname
            if pname in Gb.conf_profile:
                pvalue_key = Gb.conf_profile[pname]

            elif pname in Gb.conf_tracking:
                pvalue_key = Gb.conf_tracking[pname]

            elif pname in self.conf_device_selected:
                pvalue_key = self.conf_device_selected[pname]

            else:
                pvalue_key = Gb.conf_general[pname]

            return option_list_key_text[pvalue_key]

        except:
            # If the parameter value is already the key to the items dict, it is ok.
            if pvalue_key not in option_list_key_text:
                if pname in [CONF_FAMSHR_DEVICENAME, CONF_FMF_EMAIL, CONF_IOSAPP_DEVICE]:
                    self.errors[pname] = 'unknown_devicename'
                else:
                    self.errors[pname] = 'unknown_value'

            return f"{pvalue_key} > Unknown Selection"

#-------------------------------------------------------------------------------------------
    def _option_text_to_parm(self, user_input, pname, option_list_key_text):
        '''
        user_input contains the full text of the option list item selected. Replace it with
        the actual parameter value for the item selected.
        '''
        try:
            if user_input is None:
                return None

            pvalue_text = user_input[pname]

            # Handle special text added to the end of the key_list
            pvalue_text = pvalue_text.replace(UNKNOWN_DEVICE_TEXT, '')

            if pvalue_text in ['', '.']:
                self.errors[pname] = 'required_field'

            pvalue_key = [k for  k, v in option_list_key_text.items() if v == pvalue_text]
            pvalue_key = pvalue_key[0] if pvalue_key else pvalue_text

            user_input[pname] = pvalue_key
        except:
            # If the parameter value is already the key to the items dict, it is ok.
            if pvalue_text not in option_list_key_text:
                self.errors[pname] = 'invalid_value'

        return  user_input

#-------------------------------------------------------------------------------------------
    def _convert_field_str_to_numeric(self, user_input):
        '''
        Config_flow chokes with malformed input errors when a field is numeric. To avoid this,
        the field's default value is always a string. This converts it back to a float.
        '''
        for pname, pvalue in user_input.items():
            if pname in CONF_PARAMETER_FLOAT:
                user_input[pname] = float(pvalue)

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_numeric_field(self, user_input):
        '''
        Cycle through the user_input fields and, if numeric, validate it
        '''
        for pname, pvalue in user_input.items():
            if pname not in CONF_PARAMETER_FLOAT:
                continue

            pvalue = pvalue.strip()

            if pvalue == '':
                self.errors[pname] = "required_field"
            elif isnumber(pvalue) is False:
                self.errors[pname] = "not_numeric"

            if pname in self.errors:
                self.errors_user_input[pname] = pvalue

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_time_str(self, user_input):
        '''
        Cycle through the each of the parameters. If it is a time string, check it's
        value and sec/min/hrs entry
        '''
        new_user_input = {}

        for pname, pvalue in user_input.items():
            if pname in CONF_PARAMETER_TIME_STR:
                time_parts  = (f"{pvalue} mins").split(' ')

                if time_parts[0].strip() == '':
                    self.errors[pname] = "required_field"
                    self.errors_user_input[pname] = ''
                    continue
                elif isnumber(str(time_parts[0])) is False:
                    self.errors[pname] = "not_numeric"
                    self.errors_user_input[pname] = user_input[pname]
                    continue

                if instr(time_parts[1], 'm'):
                    pvalue = f"{time_parts[0]} mins"
                elif instr(time_parts[1], 'h'):
                    pvalue = f"{time_parts[0]} hrs"
                elif instr(time_parts[1], 's'):
                    pvalue = f"{time_parts[0]} secs"
                else:
                    pvalue = f"{time_parts[0]} mins"

                if not self.errors.get(pname):
                    try:
                        if float(time_parts[0]) == 1:
                            pvalue = pvalue.replace('s', '')
                        new_user_input[pname] = pvalue

                    except ValueError:
                        self.errors[pname] = "not_numeric"
                        self.errors_user_input[pname] = user_input[pname]

            else:
                new_user_input[pname] = pvalue

        return new_user_input

#-------------------------------------------------------------------------------------------
    def _duration_to_hhmmss(self, user_input):
        """ Reformat the duration parameters from {'hours', 'minutes' ,'seconds'} to hhh:mm:ss """

        new_user_input = user_input.copy()
        for pname, pvalue in user_input.items():
            # if type(pvalue) is not dict:
            #     continue

            if type(pvalue) is dict and 'hours' in pvalue:
                new_pvalue = f"{int(pvalue['hours']):02}:{int(pvalue['minutes']):02}:{int(pvalue['seconds']):02}"
                new_user_input[pname] = new_pvalue

        return new_user_input

#-------------------------------------------------------------------------------------------
    def _hhmmss_to_duration(self, hhmmss_field_name, conf_group=None):
        """ Reformat hh:mm:ss to {'hours', 'minutes' ,'seconds'} """

        if conf_group == CONF_DEVICES:
            hhmmss = self.conf_device_selected[hhmmss_field_name]
        elif conf_group in Gb.conf_general:
            hhmmss = Gb.conf_general[conf_group][hhmmss_field_name]
        elif hhmmss_field_name in Gb.conf_general:
            hhmmss = Gb.conf_general[hhmmss_field_name]
        else:
            hhmmss = HHMMSS_ZERO

        hhmmss_parts = hhmmss.split(':')
        duration = {
            'hours':   int(hhmmss_parts[0]),
            'minutes': int(hhmmss_parts[1]),
            'seconds': int(hhmmss_parts[2])
        }
        return duration

#-------------------------------------------------------------------------------------------
    def _parm_with_example_text(self, config_parameter, input_select_list_KEY_TEXT):
        '''
        The input_select_list for the parameter has an example text '(Example: exampletext)'
        as part of list of options display for user selection. The exampletext is not part
        of the configuration parameter. Dydle through the input_select_list and determine which
        one should be the default value.

        Return:
            default - The input_select item to be used for the default value
        '''
        for isli_with_example in input_select_list_KEY_TEXT:
            if isli_with_example.startswith(Gb.conf_general[config_parameter]):
                return isli_with_example

        return input_select_list_KEY_TEXT[0]

#--------------------------------------------------------------------
    def _extract_name_device_type(self, devicename):
        '''
        Extract the name and device type from the devicename
        '''

        try:
            fname       = devicename.lower()
            device_type = ""
            for ic3dev_type in APPLE_DEVICE_TYPES:
                if devicename == ic3dev_type:
                    return (devicename, devicename)

                elif instr(devicename, ic3dev_type):
                    fnamew = devicename.replace(ic3dev_type, "")
                    fname  = fnamew.replace("_", "").replace("-", "").title().strip()
                    device_type = DEVICE_TYPE_FNAME.get(ic3dev_type, ic3dev_type)
                    break

            if device_type == "":
                fname  = fname.replace("_", "").replace("-", "").title().strip()
                device_type = IPHONE_FNAME

        except Exception as err:
            log_exception(err)

        return (fname, device_type)

#--------------------------------------------------------------------
    def _action_default_text(self, action_item):
        return OPT_ACTION_KEY_TEXT.get(action_item, 'UNKNOWN ACTION - Unknown Action')

#--------------------------------------------------------------------
    def _discard_changes(self, user_input):
        '''
        See if user_input 'action_item' item has a 'discard_change' option
        selected. Discard changes is the last item in the list.
        '''
        if user_input:
            return (user_input.get(UPDATE_CONTROL) == self._action_default_text('cancel'))
        else:
            return False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                        FORM SCHEMA DEFINITIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def form_schema(self, step_id):
        '''
        Return the step_id form schema for the data entry forms
        '''
        schema = {}
        self.opt_actions = UPDATE_CONTROL_BASE.copy()

        if step_id == 'menu':
            if self.menu_page_no == 0:
                menu_key_text  = MENU_KEY_TEXT_PAGE_0
                menu_action[1] = MENU_KEY_TEXT['next_page_1']
            else:
                menu_key_text  = MENU_KEY_TEXT_PAGE_1
                menu_action[1] = MENU_KEY_TEXT['next_page_0']

            schema = vol.Schema({
                    vol.Required("menu_item",
                                default=self.menu_item_selected[self.menu_page_no]):
                                selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=menu_key_text)),
                    vol.Required("menu_action",
                                default=menu_action[0]):
                                selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=menu_action)),
            })

            return schema

        #------------------------------------------------------------------------
        elif step_id == 'restart_icloud3':
            restart_now_later_option_list = []
            restart_now_later_option_list.extend(OPT_RESTART_NOW_LATER_KEY_TEXT.values())

            return  vol.Schema({
                        vol.Required('restart_now_later',
                                    default=OPT_RESTART_NOW_LATER_KEY_TEXT['now']):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=restart_now_later_option_list)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'icloud_account':
            self.opt_actions = [OPT_ACTION_KEY_TEXT['log_in_icloud_acct']]
            self.opt_actions.extend(UPDATE_CONTROL_BASE)
            return  vol.Schema({
                        vol.Optional(CONF_USERNAME,
                                    default=self._parm_or_error_msg(CONF_USERNAME, CF_DATA_TRACKING)):
                                    selector.TextSelector(),
                        vol.Optional(CONF_PASSWORD,
                                    default=self._parm_or_error_msg(CONF_PASSWORD, CF_DATA_TRACKING)):
                                    selector.TextSelector(),
                        vol.Required(CONF_DATA_SOURCE,
                                    default=self._option_parm_to_text(CONF_DATA_SOURCE, OPT_DATA_SOURCE_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_DATA_SOURCE_KEY_TEXT), mode='dropdown')),
                        vol.Required('opt_action',
                                    default=self._action_default_text('save')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'reauth':
            return  vol.Schema({
                        vol.Required(CONF_VERIFICATION_CODE):
                        selector.TextSelector(),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'device_list':

            idx = self.device_list_page_selected_idx[self.device_list_page_no]
            if len(self.form_devices_list_all) > 0:
                device_list_default = self.form_devices_list_all[idx]

            if len(self.form_devices_list_all) <= 5:
                self.opt_actions = DEVICE_LIST_CONTROL.copy()
            else:
                devices_text = f"iCloud3 Devices: {self.next_page_devices_list}"

                next_page_text = OPT_ACTION_KEY_TEXT['next_page_info']
                next_page_text = next_page_text.replace('^info_field^', devices_text)
                self.opt_actions = [next_page_text]
                self.opt_actions.extend(DEVICE_LIST_CONTROL)

            schema = {}
            schema = vol.Schema({})
            if self.form_devices_list_displayed != []:
                    schema = schema.extend({
                        vol.Required('devices',
                                    default=device_list_default):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=self.form_devices_list_displayed)),
                    })
            schema = schema.extend({
                        vol.Required('opt_action',
                                    default=self._action_default_text('update_device')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                        })
            return schema

        #------------------------------------------------------------------------
        elif step_id == 'add_device':

            schema = vol.Schema({
                        vol.Required(CONF_IC3_DEVICENAME,
                                    default=self._parm_or_device(CONF_IC3_DEVICENAME)):
                                    selector.TextSelector(),
                        vol.Required(CONF_FNAME,
                                    default=self._parm_or_device(CONF_FNAME)):
                                    selector.TextSelector(),
                        vol.Required(CONF_DEVICE_TYPE,
                                    default=IPHONE_FNAME):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(APPLE_DEVICE_TYPE_TO_FNAME), mode='dropdown')),
                        vol.Required(CONF_TRACKING_MODE,
                                    default=self._option_parm_to_text(CONF_TRACKING_MODE, OPT_TRACKING_MODE_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_TRACKING_MODE_KEY_TEXT), mode='dropdown')),
                        vol.Required('iosapp', default=True):
                                    selector.BooleanSelector(),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'update_device':

            # If conf_famshr_devicename is not in available famshr values list, add it
            famshr_devicename = self.conf_device_selected[CONF_FAMSHR_DEVICENAME]
            opt_famshr_text_by_fname   = self.device_opt_famshr_text_by_fname.copy()
            if famshr_devicename not in self.device_opt_famshr_text_by_fname:
                opt_famshr_text_by_fname[famshr_devicename] = f"{famshr_devicename}{UNKNOWN_DEVICE_TEXT}"

            # If conf_fmf_email is not in available fmf emails list, add it
            fmf_email = self.conf_device_selected[CONF_FMF_EMAIL]
            opt_fmf_text_by_email = self.device_opt_fmf_text_by_email.copy()
            if fmf_email not in self.device_opt_fmf_text_by_email:
                opt_fmf_text_by_email[fmf_email] = f"{fmf_email}{UNKNOWN_DEVICE_TEXT}"

            # If conf_iosapp_device is not in available iosapp devices list, add it
            iosapp_device = self.conf_device_selected[CONF_IOSAPP_DEVICE]
            opt_iosapp_text_by_entity_id = self.device_opt_iosapp_text_by_entity_id.copy()
            if iosapp_device not in opt_iosapp_text_by_entity_id:
                opt_iosapp_text_by_entity_id[iosapp_device] = iosapp_device

            schema = vol.Schema({
                        vol.Required(CONF_IC3_DEVICENAME,
                                    default=self._parm_or_device(CONF_IC3_DEVICENAME)):
                                    selector.TextSelector(),
                        vol.Required(CONF_FNAME,
                                    default=self._parm_or_device(CONF_FNAME)):
                                    selector.TextSelector(),
                        vol.Required(CONF_DEVICE_TYPE,
                                    default=self._option_parm_to_text(CONF_DEVICE_TYPE, APPLE_DEVICE_TYPE_TO_FNAME)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(APPLE_DEVICE_TYPE_TO_FNAME), mode='dropdown')),
                        vol.Required(CONF_TRACKING_MODE,
                                    default=self._option_parm_to_text(CONF_TRACKING_MODE, OPT_TRACKING_MODE_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_TRACKING_MODE_KEY_TEXT), mode='dropdown')),
                        vol.Required(CONF_FAMSHR_DEVICENAME,
                                    default=self._option_parm_to_text(CONF_FAMSHR_DEVICENAME, opt_famshr_text_by_fname)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(opt_famshr_text_by_fname), mode='dropdown')),
                        vol.Required(CONF_FMF_EMAIL,
                                    default=self._option_parm_to_text(CONF_FMF_EMAIL, opt_fmf_text_by_email)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                            options=dict_value_list(opt_fmf_text_by_email), mode='dropdown')),
                        vol.Required(CONF_IOSAPP_DEVICE,
                                    default=self._option_parm_to_text(CONF_IOSAPP_DEVICE, opt_iosapp_text_by_entity_id)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(opt_iosapp_text_by_entity_id), mode='dropdown')),
                        vol.Required(CONF_PICTURE,
                                    default=self._parm_or_device(CONF_PICTURE, OPT_PICTURE_TEXT[OPT_NONE])):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(self.device_opt_picture_file_name_list), mode='dropdown')),
                        vol.Required(CONF_INZONE_INTERVAL,
                                    default=self._hhmmss_to_duration(CONF_INZONE_INTERVAL, CONF_DEVICES)):
                                    selector.DurationSelector(),
                        vol.Required(CONF_TRACK_FROM_ZONES,
                                    default=self._parm_or_device(CONF_TRACK_FROM_ZONES)):
                                    cv.multi_select(self.opt_zone_name_key_text),
                        vol.Required('opt_action',
                                    default=self._action_default_text('save')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'delete_device':
            self.opt_actions = DELETE_DEVICE_CONFIRM_ACTION.copy()
            schema = vol.Schema({
                        vol.Required('opt_action',
                                    default=self._action_default_text('delete_device_no')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'event_log_configuration':
            schema = vol.Schema({
                        vol.Required(CONF_DISPLAY_ZONE_FORMAT,
                                    default=self._option_parm_to_text(CONF_DISPLAY_ZONE_FORMAT, OPT_DISPLAY_ZONE_FORMAT_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_DISPLAY_ZONE_FORMAT_KEY_TEXT), mode='dropdown')),
                        vol.Required(CONF_TIME_FORMAT,
                                    default=self._option_parm_to_text(CONF_TIME_FORMAT, OPT_TIME_FORMAT_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_TIME_FORMAT_KEY_TEXT), mode='dropdown')),
                        vol.Required(CONF_EVENT_LOG_CARD_DIRECTORY,
                                    default=self._parm_or_error_msg(CONF_EVENT_LOG_CARD_DIRECTORY, CF_PROFILE)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(self.opt_www_directory_list), mode='dropdown')),
                        vol.Required('opt_action',
                                    default=self._action_default_text('save')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'display_text_as':
            self.dta_selected_idx = self.dta_selected_idx_page[self.dta_page_no]
            if self.dta_selected_idx <= 4:
                dta_page_display_list = [v for k,v in self.dta_working_copy.items()
                                                if k <= 4]
            else:
                dta_page_display_list = [v for k,v in self.dta_working_copy.items()
                                                if k >= 5]

            next_page_text = OPT_ACTION_KEY_TEXT['next_page_info']

            self.opt_actions = [next_page_text]
            self.opt_actions.extend([OPT_ACTION_KEY_TEXT['select_text_as']])
            self.opt_actions.extend(UPDATE_CONTROL_BASE)

            schema = vol.Schema({
                        vol.Required(CONF_DISPLAY_TEXT_AS,
                                default=self.dta_working_copy[self.dta_selected_idx]):
                                selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=dta_page_display_list)),
                        vol.Required('opt_action',
                            default=self._action_default_text('select_text_as')):
                            selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'display_text_as_update':
            self.opt_actions = [OPT_ACTION_KEY_TEXT['clear_text_as']]
            self.opt_actions.extend(UPDATE_CONTROL_BASE)

            if instr(self.dta_working_copy[self.dta_selected_idx], '>'):
                text_from_to_parts = self.dta_working_copy[self.dta_selected_idx].split('>')
                text_from = text_from_to_parts[0].strip()
                text_to   = text_from_to_parts[1].strip()
            else:
                text_from = ''
                text_to   = ''

            schema = vol.Schema({
                            vol.Optional('text_from', default=text_from):
                                    selector.TextSelector(),
                            vol.Optional('text_to'  , default=text_to):
                                    selector.TextSelector(),
                            vol.Required('opt_action',
                                    default=self._action_default_text('save')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'other_parms':
            schema = vol.Schema({
                        vol.Required(CONF_UNIT_OF_MEASUREMENT,
                                    default=self._option_parm_to_text(CONF_UNIT_OF_MEASUREMENT, OPT_UNIT_OF_MEASUREMENT_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_UNIT_OF_MEASUREMENT_KEY_TEXT), mode='dropdown')),
                        vol.Required(CONF_MAX_INTERVAL,
                                    default=self._hhmmss_to_duration(CONF_MAX_INTERVAL)):
                                    selector.DurationSelector(),
                        vol.Required(CONF_GPS_ACCURACY_THRESHOLD,
                                    default=Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]):
                                    selector.NumberSelector(
                                        selector.NumberSelectorConfig(
                                            min=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement='m')),
                        vol.Required(CONF_OLD_LOCATION_THRESHOLD,
                                    default=self._hhmmss_to_duration(CONF_OLD_LOCATION_THRESHOLD)):
                                    selector.DurationSelector(),
                        vol.Required(CONF_TRAVEL_TIME_FACTOR,
                                    default=self._parm_or_error_msg(CONF_TRAVEL_TIME_FACTOR)):
                                    selector.NumberSelector(
                                        selector.NumberSelectorConfig(
                                                min=.1, step=.1, max = 1, mode=selector.NumberSelectorMode.BOX)),
                        vol.Required(CONF_LOG_LEVEL,
                                    default=self._option_parm_to_text(CONF_LOG_LEVEL, OPT_LOG_LEVEL_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_LOG_LEVEL_KEY_TEXT), mode='dropdown')),
                        vol.Required('opt_action',
                                    default=self._action_default_text('save')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'inzone_intervals':
            schema = vol.Schema({
                        vol.Required(IPHONE,
                                    default=self._hhmmss_to_duration(IPHONE, CONF_INZONE_INTERVALS)):
                                    selector.DurationSelector(),
                        vol.Required(IPAD,
                                    default=self._hhmmss_to_duration(IPAD, CONF_INZONE_INTERVALS)):
                                    selector.DurationSelector(),
                        vol.Required(WATCH,
                                    default=self._hhmmss_to_duration(WATCH, CONF_INZONE_INTERVALS)):
                                    selector.DurationSelector(),
                        vol.Required(AIRPODS,
                                    default=self._hhmmss_to_duration(AIRPODS,CONF_INZONE_INTERVALS)):
                                    selector.DurationSelector(),
                        vol.Required(NO_IOSAPP,
                                    default=self._hhmmss_to_duration(NO_IOSAPP, CONF_INZONE_INTERVALS)):
                                    selector.DurationSelector(),
                        vol.Required(NO_IOSAPP,
                                    default=self._hhmmss_to_duration(OTHER, CONF_INZONE_INTERVALS)):
                                    selector.DurationSelector(),
                        vol.Required(CONF_CENTER_IN_ZONE,
                                    default=Gb.conf_general[CONF_CENTER_IN_ZONE]):
                                    selector.BooleanSelector(),
                        vol.Required(CONF_DISCARD_POOR_GPS_INZONE,
                                    default=Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]):
                                    selector.BooleanSelector(),
                        vol.Required('opt_action',
                                    default=self._action_default_text('save')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                     })

        #------------------------------------------------------------------------
        elif step_id == 'waze_1':
            self.opt_actions = [OPT_ACTION_KEY_TEXT['next_page_waze']]
            self.opt_actions.extend([OPT_ACTION_KEY_TEXT['cancel']])
            # self.opt_actions.extend(UPDATE_CONTROL_BASE)
            schema = vol.Schema({
                        vol.Optional(CONF_DISTANCE_METHOD,
                                    default=self._option_parm_to_text(CONF_DISTANCE_METHOD, OPT_DISTANCE_METHOD_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_DISTANCE_METHOD_KEY_TEXT), mode='dropdown')),
                        vol.Optional(CONF_WAZE_REGION,
                                    default=self._option_parm_to_text(CONF_WAZE_REGION, OPT_WAZE_REGION_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_WAZE_REGION_KEY_TEXT), mode='dropdown')),
                        vol.Optional(CONF_WAZE_MIN_DISTANCE,
                                    default=Gb.conf_general[CONF_WAZE_MIN_DISTANCE]):
                                    selector.NumberSelector(
                                        selector.NumberSelectorConfig(
                                            min=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement='km')),
                        vol.Optional(CONF_WAZE_MAX_DISTANCE,
                                    default=Gb.conf_general[CONF_WAZE_MAX_DISTANCE]):
                                    selector.NumberSelector(
                                        selector.NumberSelectorConfig(
                                            min=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement='km')),
                        vol.Optional(CONF_WAZE_REALTIME,
                                    default=Gb.conf_general[CONF_WAZE_REALTIME]):
                                    selector.BooleanSelector(),
                        vol.Optional('opt_action',
                                    default=self._action_default_text('next_page_waze')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'waze_2':
            schema = vol.Schema({
                        vol.Required(CONF_WAZE_HISTORY_DATABASE_USED,
                                    default=Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED]):
                                    selector.BooleanSelector(),
                        vol.Required(CONF_WAZE_HISTORY_MAX_DISTANCE,
                                    default=Gb.conf_general[CONF_WAZE_HISTORY_MAX_DISTANCE]):
                                    selector.NumberSelector(
                                        selector.NumberSelectorConfig(
                                            min=0, mode=selector.NumberSelectorMode.BOX, unit_of_measurement='km')),
                        vol.Required(CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                    default=self._option_parm_to_text(CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                                                        OPT_WAZE_HISTORY_TRACK_DIRECTION_KEY_TEXT)):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                                options=dict_value_list(OPT_WAZE_HISTORY_TRACK_DIRECTION_KEY_TEXT), mode='dropdown')),
                        vol.Required('opt_action',
                                    default=self._action_default_text('save')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'stationary_zone':
            schema = vol.Schema({
                        vol.Required(CONF_STAT_ZONE_FNAME,
                                    default=self._parm_or_error_msg(CONF_STAT_ZONE_FNAME)):
                                    selector.TextSelector(),
                        vol.Required(CONF_STAT_ZONE_STILL_TIME,
                                    default=self._hhmmss_to_duration(CONF_STAT_ZONE_STILL_TIME)):
                                    selector.DurationSelector(),
                        vol.Required(CONF_STAT_ZONE_INZONE_INTERVAL,
                                    default=self._hhmmss_to_duration(CONF_STAT_ZONE_INZONE_INTERVAL)):
                                    selector.DurationSelector(),
                        vol.Required(CONF_STAT_ZONE_BASE_LATITUDE,
                                    default=self._parm_or_error_msg(CONF_STAT_ZONE_BASE_LATITUDE)):
                                    selector.TextSelector(),
                        vol.Required(CONF_STAT_ZONE_BASE_LONGITUDE,
                                    default=self._parm_or_error_msg(CONF_STAT_ZONE_BASE_LONGITUDE)):
                                    selector.TextSelector(),
                        vol.Required('opt_action',
                                    default=self._action_default_text('save')):
                                    selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        #------------------------------------------------------------------------
        elif step_id == 'sensors':
            schema = vol.Schema({

                        # vol.Required(CONF_METER_NET_CONSUMPTION, default=False): selector.BooleanSelector(),
                        vol.Required(CONF_SENSORS_CONTROL,
                                    default=Gb.conf_sensors[CONF_SENSORS_CONTROL]):
                                    cv.multi_select(CONF_SENSORS_CONTROL_KEY_TEXT),
                        vol.Required(CONF_SENSORS_DEVICE,
                                    default=Gb.conf_sensors[CONF_SENSORS_DEVICE]):
                                    cv.multi_select(CONF_SENSORS_DEVICE_KEY_TEXT),
                        vol.Required(CONF_SENSORS_TRACKING_UPDATE,
                                    default=Gb.conf_sensors[CONF_SENSORS_TRACKING_UPDATE]):
                                    cv.multi_select(CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT),
                        vol.Required(CONF_SENSORS_TRACKING_TIME,
                                    default=Gb.conf_sensors[CONF_SENSORS_TRACKING_TIME]):
                                    cv.multi_select(CONF_SENSORS_TRACKING_TIME_KEY_TEXT),
                        vol.Required(CONF_SENSORS_TRACKING_DISTANCE,
                                    default=Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE]):
                                    cv.multi_select(CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT),
                        vol.Required(CONF_SENSORS_TRACK_FROM_ZONES,
                                    default=Gb.conf_sensors[CONF_SENSORS_TRACK_FROM_ZONES]):
                                    cv.multi_select(CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT),
                        vol.Required(CONF_SENSORS_TRACKING_OTHER,
                                    default=Gb.conf_sensors[CONF_SENSORS_TRACKING_OTHER]):
                                    cv.multi_select(CONF_SENSORS_TRACKING_OTHER_KEY_TEXT),
                        vol.Required(CONF_SENSORS_ZONE,
                                    default=Gb.conf_sensors[CONF_SENSORS_ZONE]):
                                    cv.multi_select(CONF_SENSORS_ZONE_KEY_TEXT),
                        vol.Required(CONF_SENSORS_OTHER,
                                    default=Gb.conf_sensors[CONF_SENSORS_OTHER]):
                                    cv.multi_select(CONF_SENSORS_OTHER_KEY_TEXT),

                        vol.Required('opt_action',
                                default=self._action_default_text('save')):
                                selector.SelectSelector(
                                        selector.SelectSelectorConfig(options=self.opt_actions)),
                    })

        elif step_id == '':
            pass

        return schema
