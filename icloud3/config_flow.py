from copy import deepcopy
import json
import os
import time
from typing import Any, Dict, Optional
from collections import OrderedDict

from homeassistant import config_entries, data_entry_flow
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowHandler
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from   homeassistant.util    import slugify
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry,
)
import voluptuous as vol

import logging
_LOGGER = logging.getLogger(__name__)

from .const import *
from .global_variables      import GlobalVariables as Gb
from .helpers.base          import (instr, isnumber, log_exception, _traceha,
                                    post_event,
                                    write_storage_icloud3_configuration_file, )
from .support               import start_ic3
from .support.pyicloud_ic3  import PyiCloudService
from .support.pyicloud_ic3  import (
            PyiCloudException,
            PyiCloudFailedLoginException,
            PyiCloudServiceNotActivatedException,
            PyiCloudNoDevicesException,
            )
from .support.ic3v3_conf_converter import iCloud3V3ConfigurationConverter

# from .helpers.entity_io import (get_entity_ids, get_attributes, )

#-----------------------------------------------------------------------------------------

MENU_P1_1 = "ICLOUD ACCOUNT, TRACKING METHOD - iCloud Account Username/password, iOS App Info"
MENU_P1_2 = "UPDATE TRACKED DEVICES - Change, Add & Delete tracked devices, Change tracked device information"
MENU_P1_3 = "EVENT LOG FIELD FORMATS - Zones Name formats, Time formats"
MENU_P1_4 = "EVENT LOG 'DISPLAY TEXT AS' - Display a text value as something else (user names, email address, device names, etc.)"
MENU_P1_5 = "MISCELLENOUS PARAMETERS - Other Configuration Parameters, Unit of Measure, Accuracy Thresholds, Log Levels"

MENU_P2_1 = "INZONE INTERVALS - Default inZone interval by device type & iOS App"
MENU_P2_2 = "WAZE PARAMETERS - Region, Min/Max Intervals, History Database Controls"
MENU_P2_3 = "STATIONARY ZONE - inZone Interval, Still Time & Base Location Offsets"
MENU_P2_4 = "SENSORS - Sensors created by iCloud3"
MENU_P2_5 = "SYSTEM SETTINGS - File & Directory Names, Log Lovels"

MENU_CONTROL_1 = 'SELECT UPDATE FORM ... Display the Selected Parameter Update Form'
MENU_CONTROL_2 = 'UPDATE COMPLETE ... Finish parameter update and close form'

MENU_ITEMS_PAGE_1 = [MENU_P1_1, MENU_P1_2, MENU_P1_3, MENU_P1_4, MENU_P1_5]
MENU_ITEMS_PAGE_2 = [MENU_P2_1, MENU_P2_2, MENU_P2_3, MENU_P2_4, MENU_P2_5]
MENU_ITEMS_CONTROL = [MENU_CONTROL_1, MENU_CONTROL_2]

DEVICE_LIST_ADD = 'ADD NEW DEVICE - Add a devices to be tracked by iCloud3'
DEVICE_LIST_DELETE = 'DELETE DEVICE - Remove a device from the tracked device list'
DEVICE_LIST_UPDATE = 'UPDATE DEVICE - Update the selected tracked device'
DEVICE_LIST_LOGIN = 'LOG INTO ICLOUD - Log into the iCloud Account again'
DEVICE_LIST_RETURN = 'MAIN MENU - Return to the Main Menu'
DEVICE_LIST_CONTROL = [DEVICE_LIST_UPDATE, DEVICE_LIST_ADD, DEVICE_LIST_DELETE, DEVICE_LIST_RETURN]
DEVICE_LIST_CONTROL_NO_ADD = [DEVICE_LIST_UPDATE, DEVICE_LIST_DELETE, DEVICE_LIST_RETURN]

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                     ICLOUD3 CONFIG FLOW - INITIAL SETUP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class iCloud3ConfigFlow(config_entries.ConfigFlow, FlowHandler, domain=DOMAIN ):
    '''iCloud3 config flow Handler'''

    VERSION = 1
    def __init__(self):
        self.step_id = ''       # step_id for the window displayed
        self.errors  = {}       # Errors en.json error key


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

        schema = vol.Schema({vol.Required(CONF_VERIFICATION_CODE): str,})
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
        self.step_id             = ''       # step_id for the window displayed
        self.errors              = {}       # Errors en.json error key
        self.initialize_options()

    def initialize_options(self):
        # ic3v3_conf_converter = iCloud3V3ConfigurationConverter()
        # ic3v3_conf_converter.convert_v2_config_files_to_v3()

        # Gb.OptionsFlowHandler = self
        self.initialize_options_required_flag = False
        self.errors              = {}       # Errors en.json error key
        self.user_input_multi_form = {}     # Saves the user_input from form #1 on a multi-form update
        self.errors_user_input   = {}       # user_input text for a value with an error
        self.step_id             = ''       # step_id for the window displayed
        self.selected_menu_item  = ['', MENU_P1_1, MENU_P2_1]
        self.menu_page_no        = 1        # Menu currently displayed
        self.dta_page_no         = 1        # display_text_as current page
        self.called_from_step_id = ''       # Form/Fct to return to when verifying the icloud auth code
        self.menu_msg = ''     # Message displayed on menu after update

        self.logging_into_icloud_flag = False
        self.username = None
        self.password = None
        self.all_famshr_devices = True

        # Variables used for device selection and update on the device_list and device_update forms
        self.conf_devices_list_selected = ['', '', '']
        self.form_devices_list_all = []         #List of the device in the Gb.conf_tracking[DEVICES] parameter
        self.form_devices_list_displayed = []   #List of the device displayed on the device_list form
        self.form_devices_list_devicename = []  #List of the devicenames in the Gb.conf_tracking[DEVICES] parameter
        self.device_list_page_no = 1            #Devices List form page number
        self.devicename_being_updated = ''       # Devicename currently being updated
        self.selected_device_data = {}
        self.selected_device_index = 0
        self.selected_device_list_control = DEVICE_LIST_UPDATE     # Select the Return to main menu as the default
        self.add_device_flag = False
        self.add_device_enter_devicename_form_part_flag = False  # Add device started, True=form top part only displayed

        self.devicename_device_info_famshr = {}
        self.devicename_device_id_famshr = {}
        self.devicename_device_info_fmf = {}
        self.devicename_device_id_fmf = {}
        self.device_id_devicename_fmf = {}
        self.devicename_device_info_iosapp = {}

        self.device_form_picture_list = []
        self.device_form_icloud_famshr_list = []
        self.device_form_icloud_fmf_list = []
        self.device_form_iosapp_list = []
        self.device_form_zone_list = {}

        self._verification_code = None

        self._existing_entry = None
        self._description_placeholders = None

        Gb.config_flow_update_control = {''}

    async def async_step_init(self, user_input=None):
        if self.initialize_options_required_flag:
            self.initialize_options()
        self.errors = {}

        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_step_menu(self, user_input=None):
        '''Main Menu displays different screens for parameter entry'''
        Gb.config_flow_flag = True

        user_input = self._check_if_from_svc_call(user_input)

        self.step_id = 'menu'
        self.current_menu_step_id = self.step_id
        self.errors = {}
        # self._traceui(user_input)

        if user_input is not None:
            self.selected_menu_item[self.menu_page_no] = user_input['menu_item']

            sel_menu_item = 1

            if user_input:
                if user_input['menu_item']:
                    try:
                        sel_menu_item = 11
                        sel_menu_item += MENU_ITEMS_PAGE_1.index(user_input['menu_item'])
                    except ValueError:
                        try:
                            sel_menu_item = 21
                            sel_menu_item += MENU_ITEMS_PAGE_2.index(user_input['menu_item'])
                        except ValueError:
                            sel_menu_item = 11

            if user_input['menu_control'].startswith('UPDATE COMPLETE'):
                Gb.config_flow_flag = False
                self.initialize_options_required_flag = False

                if 'restart' in Gb.config_flow_update_control:
                    self.step_id = 'restart_icloud3'
                    return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors={},
                            last_step=False)
                else:
                    return self.async_create_entry(title="iCloud3", data={})

            elif 'menu_next_page_1' in user_input and user_input['menu_next_page_1']:
                self.menu_page_no = 1
            elif 'menu_next_page_2' in user_input and user_input['menu_next_page_2']:
                self.menu_page_no = 2

            elif user_input['menu_item'] == "":
                pass
            elif sel_menu_item == 11:
                return await self.async_step_icloud_account()
            elif sel_menu_item == 12:
                return await self.async_step_device_list()
            elif sel_menu_item == 13:
                return await self.async_step_evlog_field_formats()
            elif sel_menu_item == 14:
                return await self.async_step_display_text_as()
            elif sel_menu_item == 15:
                return await self.async_step_misc_parms()
            elif sel_menu_item == 21:
                return await self.async_step_inzone()
            elif sel_menu_item == 22:
                return await self.async_step_waze_1()
            elif sel_menu_item == 23:
                return await self.async_step_stationary_zone()
            elif sel_menu_item == 24:
                return await self.async_step_sensors()
            elif sel_menu_item == 25:
                return await self.async_step_settings()

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

        if user_input is not None:
            if user_input['restart_now_later'].startswith('RESTART LATER'):
                Gb.config_flow_update_control.remove('restart')
            post_event(f"{Gb.config_flow_update_control=}")
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

    def common_form_handler(self, user_input=None, errors=None):
        # self.step_id = 'icloud_account'
        self.errors = errors or {}
        self.errors_user_input = {}

        if user_input is not None:

            # Validate the user_input, update the config file with valid entries
            # self._validate_and_update_conf_file(user_input)
            if user_input.get('cancel_update', False):
                return True
            elif self.step_id == 'icloud_account':
                pass
            elif self.step_id == 'device_list':
                user_input = self._select_device_from_device_list(user_input)
            elif self.step_id == 'display_format':
                user_input = self._validate_display_format(user_input)
            elif self.step_id == 'inzone':
                user_input = self._validate_time_str(user_input)
            elif self.step_id == 'misc_parms':
                user_input = self._validate_misc_parms(user_input)
            elif self.step_id == "display_text_as":
                user_input = self._validate_display_text_as(user_input)
            elif self.step_id == "waze_1":
                user_input = self._validate_waze_1(user_input)
            elif self.step_id == "waze_2":
                user_input = self._validate_waze_2(user_input)
            elif self.step_id == "stationary_zone":
                user_input = self._validate_stationary_zone(user_input)
            elif self.step_id == "sensors":
                pass
            elif self.step_id == 'settings':
                user_input = self._validate_settings(user_input)

            self._update_configuration_file(user_input)

            if not self.errors:
                # Redisplay the menu if there were no errors
                return True

        # Display the config data entry form, any errors will be redisplayed and highlighted
        return False

#-------------------------------------------------------------------------------------------
    async def async_step_evlog_field_formats(self, user_input=None, errors=None):
        self.step_id = 'evlog_field_formats'
        if self.common_form_handler(user_input, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_display_text_as(self, user_input=None, errors=None):
        self.step_id = 'display_text_as'

        dta_next_page_no = 0
        #self._traceui(user_input)

        if user_input is not None:
            # If next page was selected, increment the page number and display it
            if 'dta_next_page_1' in user_input and user_input['dta_next_page_1']:
                dta_next_page_no = 1
            elif 'dta_next_page_2' in user_input and user_input['dta_next_page_2']:
                dta_next_page_no = 2

        if (self.common_form_handler(user_input, errors)
                and dta_next_page_no == 0):
            return await self.async_step_menu()

        if self.errors == {}:
            self.dta_page_no = dta_next_page_no

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_misc_parms(self, user_input=None, errors=None):
        self.step_id = 'misc_parms'
        if self.common_form_handler(user_input, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_inzone(self, user_input=None, errors=None):
        self.step_id = 'inzone'
        if self.common_form_handler(user_input, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_waze_1(self, user_input=None, errors=None):
        self.step_id = 'waze_1'
        if self.common_form_handler(user_input, errors):
            if (user_input['cancel_update']
                    or user_input[CONF_DISTANCE_METHOD].startswith('Calc')):
                return await self.async_step_menu()
            else:
                return await self.async_step_waze_2()

        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors,
                         last_step=False)

#-------------------------------------------------------------------------------------------
    async def async_step_waze_2(self, user_input=None, errors=None):
        self.step_id = 'waze_2'
        if self.common_form_handler(user_input, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors,
                         last_step=True)

#-------------------------------------------------------------------------------------------
    async def async_step_stationary_zone(self, user_input=None, errors=None):
        self.step_id = 'stationary_zone'
        if self.common_form_handler(user_input, errors):
            return await self.async_step_menu()

        # self._traceui(user_input)

        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_sensors(self, user_input=None, errors=None):
        self.step_id = 'sensors'
        if self.common_form_handler(user_input, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_settings(self, user_input=None, errors=None):
        self.step_id = 'settings'
        if self.common_form_handler(user_input, errors):
            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                         data_schema=self.form_schema(self.step_id),
                         errors=self.errors)


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
        for pname, pvalue in user_input.items():
            if pname == CONF_LOG_LEVEL:
                Gb.conf_general[CONF_LOG_LEVEL] = pvalue
                start_ic3.set_log_level
                pname = ''

            if type(pvalue) is str:
                pvalue = pvalue.strip()
            if (pname not in self.errors
                    and pname in CONF_PARAMETER_FLOAT):
               pvalue = float(pvalue)

            if pname in Gb.conf_tracking:
                if Gb.conf_tracking[pname] != pvalue:
                    Gb.conf_tracking[pname] = pvalue
                    Gb.config_flow_update_control.update(['tracking', 'restart'])

            if pname in Gb.conf_general:
                if Gb.conf_general[pname] != pvalue:
                    Gb.conf_general[pname] = pvalue
                    Gb.config_flow_update_control.update(['general'])
                    if 'waze' in self.step_id:
                        Gb.config_flow_update_control.update(['waze'])

            if (pname in Gb.conf_sensors
                    and type(pvalue) is bool):
                if Gb.conf_sensors[pname] != pvalue:
                    Gb.conf_sensors[pname] = pvalue
                    Gb.config_flow_update_control.update(['sensors', 'restart'])

            if pname in Gb.conf_profile:
                if Gb.conf_profile[pname] != pvalue:
                    Gb.conf_profile[pname] = pvalue
                    Gb.config_flow_update_control.update(['profile'])

            # If default or converted file, update version so the
            # ic3 parameters are now handled by config_flow
            if Gb.conf_profile[CONF_VERSION] == 0:
                Gb.conf_profile[CONF_VERSION] = 1

            write_storage_icloud3_configuration_file()

            self.menu_msg = 'conf_updated'

        return

#-------------------------------------------------------------------------------------------
    def _validate_display_format(self, user_input):
        '''
        The display_zone_format may contain '(Example: ...). If so, strip it off.
        '''
        return self._strip_example_text_from_user_input(user_input)

#-------------------------------------------------------------------------------------------
    def _validate_misc_parms(self, user_input):
        '''
        The display_zone_format may contain '(Example: ...). If so, strip it off.
        '''
        # self._traceui(user_input)

        user_input = self._validate_time_str(user_input)
        user_input = self._validate_numeric_field(user_input)

        if user_input[CONF_LOG_LEVEL] == '.':
            self.errors[CONF_LOG_LEVEL] = 'required_field'

        if CONF_TRAVEL_TIME_FACTOR not in self.errors:
            travel_time_factor = float(user_input[CONF_TRAVEL_TIME_FACTOR])
            if (travel_time_factor < .1 or travel_time_factor > 1):
                self.errors[CONF_TRAVEL_TIME_FACTOR] = 'time_factor_invalid_range'
                self.errors_user_input[CONF_TRAVEL_TIME_FACTOR] = user_input[CONF_TRAVEL_TIME_FACTOR]

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_display_text_as(self, user_input):
        '''
        Cycle through the text items and make sure they have a '>' that seperates the actual text
        with the text to be displayed. Display an error message if it doed not have a '>'.
        Then, update the conf display_text_as parameter with the valid values.

        Return = valid display_text_as list
        '''
        display_text_as = Gb.conf_general[CONF_DISPLAY_TEXT_AS].copy()
        for pname, pvalue in user_input.items():
            if pname.startswith('text_') is False:
                continue

            pvalue = pvalue.strip()

            if pvalue:
                if instr(pvalue, '>') is False:
                    self.errors[pname] = 'display_text_as_no_gtsign'
                    self.errors_user_input[pname] = pvalue
                else:
                    pvalue_part = pvalue.split('>')
                    pvalue_part_from_text = pvalue_part[0].strip()
                    pvalue_part_display_text = pvalue_part[1].strip()
                    if pvalue_part_from_text == '':
                        self.errors[pname] = 'display_text_as_no_actual'
                        self.errors_user_input[pname] = pvalue
                    elif pvalue_part_display_text == '':
                        self.errors[pname] = 'display_text_as_no_display_as'
                        self.errors_user_input[pname] = pvalue
                    else:
                        pvalue = f"{pvalue_part_from_text} > {pvalue_part_display_text}"

            if self.errors.get(pname) is None:
                pitem = int(pname.replace('text_', ''))
                display_text_as[pitem] = pvalue.strip()

        if not self.errors:
            display_text_as = self._compress_display_text_as(display_text_as)

        new_user_input = {}
        new_user_input[CONF_DISPLAY_TEXT_AS] = display_text_as

        return new_user_input

#-------------------------------------------------------------------------------------------
    def _compress_display_text_as(self, display_text_as):
        '''
        Compress the display_text_as list to move text fields to the front of the list and
        put all blank fields at the end
        '''
        compressed_display_text_as = DEFAULT_GENERAL_CONF[CONF_DISPLAY_TEXT_AS].copy()
        cdta_item = 0
        for dta_text in display_text_as:
            if dta_text:
                compressed_display_text_as[cdta_item] = dta_text
                cdta_item += 1

        return compressed_display_text_as

#-------------------------------------------------------------------------------------------
    def _validate_waze_1(self, user_input):
        '''
        Validate the Waze numeric fields
        '''
        user_input = self._validate_numeric_field(user_input)
        if user_input[CONF_DISTANCE_METHOD] == '.':
            self.errors[CONF_DISTANCE_METHOD] = 'required_field'
        if user_input[CONF_WAZE_REGION] == '.':
            self.errors[CONF_WAZE_REGION] = 'required_field'
        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_waze_2(self, user_input):
        '''
        Validate the Waze numeric fields
        '''
        user_input = self._validate_numeric_field(user_input)
        if user_input[CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION] == '.':
            self.errors[CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION] = 'required_field'

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_stationary_zone(self, user_input):
        '''
        Validate the stationary one fields
        '''
        user_input = self._validate_time_str(user_input)
        user_input = self._validate_numeric_field(user_input)

        # user_input = self._validate_numeric_field(user_input, CONF_STAT_ZONE_BASE_LATITUDE)
        # user_input = self._validate_numeric_field(user_input, CONF_STAT_ZONE_BASE_LONGITUDE)
        # self._traceui(user_input)
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
    def _validate_settings(self, user_input):

        evlog_directory = user_input[CONF_EVENT_LOG_CARD_DIRECTORY]
        if instr(evlog_directory, 'www/'):
            evlog_directory = evlog_directory.split('www')[1]
        evlog_directory = f"{Gb.ha_config_www_directory}{evlog_directory}"
        evlog_js_program_path = f"{evlog_directory}/{user_input[CONF_EVENT_LOG_CARD_PROGRAM]}"

        if os.path.exists(evlog_directory) is False:
            self.errors[CONF_EVENT_LOG_CARD_DIRECTORY] = 'not_found_directory'
            self.errors_user_input[CONF_EVENT_LOG_CARD_DIRECTORY] = evlog_directory

        elif os.path.exists(evlog_js_program_path) is False:
            self.errors[CONF_EVENT_LOG_CARD_PROGRAM] = 'not_found_file'
            self.errors_user_input[CONF_EVENT_LOG_CARD_PROGRAM] = user_input[CONF_EVENT_LOG_CARD_PROGRAM]

        if not self.errors:
            user_input[CONF_EVENT_LOG_CARD_DIRECTORY] = evlog_directory.replace(Gb.ha_config_directory, '')
            user_input[CONF_EVENT_LOG_CARD_PROGRAM]   = evlog_js_program_path.replace(f"{evlog_directory}/", '')


        if user_input[CONF_LOG_LEVEL] == '.':
            self.errors[CONF_LOG_LEVEL] = 'required_field'


        return user_input


#-------------------------------------------------------------------------------------------
    def _strip_example_text_from_user_input(self, user_input):
        '''
        The user_input options may contain '(Example: exampletext)' after the actual parameter
        value. If so, strip it off so the field can be updated in the configuration file.

        Returns:
            user_input  - user_input without the example text
        '''

        for pname, pvalue in user_input.items():
            if instr(pvalue, '(Example:'):
                user_input[pname] = pvalue.split(' (Example:')[0].strip()

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

        if Gb.conf_tracking[CONF_TRACKING_METHOD] not in OPT_TRACKING_METHOD:
            Gb.conf_tracking[CONF_TRACKING_METHOD] = OPT_TRACKING_METHOD[OPT_TM_ICLOUD_IOSAPP]

        if user_input is not None:
            # if user_input['cancel_update']:
            if user_input.get('cancel_update', False):
                return await self.async_step_menu()

            elif not self.errors:
                self._validate_icloud_account_conf(user_input)

                if user_input[CONF_TRACKING_METHOD].startswith('iOS App'):
                    self._update_configuration_file(user_input)
                    Gb.PyiCloud = None
                    return await self.async_step_menu()

                elif user_input[CONF_TRACKING_METHOD] != Gb.conf_tracking[CONF_TRACKING_METHOD]:
                    user_input_tm = {CONF_TRACKING_METHOD: user_input[CONF_TRACKING_METHOD]}
                    self._update_configuration_file(user_input_tm)

                if self.errors:
                    self.errors_user_input[CONF_USERNAME] = user_input[CONF_USERNAME]
                    self.errors_user_input[CONF_PASSWORD] = user_input[CONF_PASSWORD]

                elif (user_input['icloud_acct_login']
                        or user_input[CONF_USERNAME] != Gb.conf_tracking[CONF_USERNAME]
                        or user_input[CONF_PASSWORD] != Gb.conf_tracking[CONF_PASSWORD]):
                    await self._log_into_icloud_account(user_input, self.step_id)

                    if (Gb.PyiCloud
                            and Gb.PyiCloud.requires_2fa):
                        return await self.async_step_reauth()

                else:
                    self._update_configuration_file(user_input)
                    return await self.async_step_menu()

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
        # They are optional if only tracking with the iOS App

        # self._traceui(user_input)

        if (user_input[CONF_USERNAME] == Gb.conf_tracking[CONF_USERNAME]
                and user_input[CONF_PASSWORD] == Gb.conf_tracking[CONF_PASSWORD]
                and user_input[CONF_TRACKING_METHOD] == Gb.conf_tracking[CONF_TRACKING_METHOD]
                and user_input['icloud_acct_login'] is False):
            return False

        if (user_input[CONF_USERNAME] == ''
                and user_input[CONF_PASSWORD] != ''):
            self.errors[CONF_USERNAME] = 'required_field'
            self.errors_user_input[CONF_USERNAME] = ''
        elif (user_input[CONF_USERNAME] != ''
                and user_input[CONF_PASSWORD] == ''):
            self.errors[CONF_PASSWORD] = 'required_field'
            self.errors_user_input[CONF_PASSWORD] = ''
        elif (user_input[CONF_USERNAME] == ''
                and user_input[CONF_PASSWORD] == ''
                and user_input[CONF_TRACKING_METHOD].startswith('iOS App') is False):
            self.errors[CONF_USERNAME] = 'required_field'
            self.errors_user_input[CONF_USERNAME] = ''
            self.errors[CONF_PASSWORD] = 'required_field'
            self.errors_user_input[CONF_PASSWORD] = ''

        if self.errors:
            return True

        #Gb.log_rawdata_flag = True
        self.username = user_input[CONF_USERNAME]
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
            self.device_form_icloud_famshr_list & self.device_form_icloud_famf_list =
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

        # except (PyiCloudFailedLoginException, PyiCloudAPIResponseException) as err:
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

    # async def async_step_icloud_verification_code(self, user_input=None, errors=None):
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

        schema = vol.Schema({vol.Required(CONF_VERIFICATION_CODE): str,})
        return self.async_show_form(step_id=config_entries.SOURCE_REAUTH,
                                    data_schema=schema,
                                    errors=self.errors)






        # if user_input is None:
        #     return await self.show_verification_code_form(user_input, errors)

        # try:
        #     verification_code = user_input[CONF_VERIFICATION_CODE]
        #     if Gb.PyiCloud.requires_2fa:
        #         if not await self.hass.async_add_executor_job(
        #                             Gb.PyiCloud.validate_2fa_code,
        #                             verification_code):
        #             raise PyiCloudException("The code you entered is not valid")
        #     # else:
        #     #     if not await self.hass.async_add_executor_job(
        #     #                         Gb.PyiCloud.validate_2fa_code,
        #     #                         verification_code):
        #     #         raise PyiCloudException("The code you entered is not valid")

        # except PyiCloudException as err:
        #     _LOGGER.error(f"The Apple ID Verification Code is invalid. "
        #                     f"Requesting a new code.")
        #     errors = {'base': 'invalid_verification_code'}

        #     if Gb.PyiCloud.requires_2fa:
        #         try:
        #             Gb.PyiCloud = await self.hass.async_add_executor_job(
        #                                         PyiCloudService,
        #                                         self.username,
        #                                         self.password,
        #                                         Gb.ha_storage_icloud3,
        #                                         f"{Gb.ha_storage_icloud3}/session",
        #                                         True)

        #             return await self.async_step_reauth(None, errors)

        #         except PyiCloudFailedLoginException as err:
        #             Gb.PyiCloud = None
        #             _LOGGER.error(f"Error logging into iCloud service: {err}")
        #             errors = {'base': 'icloud_invalid_auth'}
        #             return self.async_step_icloud_account(None, errors)

        # if not self.errors:
        #     self.errors = {'base': 'icloud_logged_into'}

        # if self.called_from_step_id:
        #     self.step_id = self.called_from_step_id

        #     return self.async_show_form(step_id=self.step_id,
        #                     data_schema=self.form_schema(self.step_id),
        #                     errors=self.errors)
        # else:
        #     # return self.async_create_entry(title="iCloud3", data={})
        #     entry = await self.async_set_unique_id(DOMAIN)
        #     self.hass.config_entries.async_update_entry(entry, data={})
        #     await self.hass.config_entries.async_reload(entry.entry_id)
        #     return self.async_abort(reason="reauth_successful")

#----------------------------------------------------------------------
    async def show_verification_code_form(self, user_input=None, errors=None):
        """Show the verification_code form to the user."""
        # _traceha(f"{self.form_schema('reauth')=}")
        # return self.async_show_form(step_id='icloud_verification_code',
        return self.async_show_form(step_id='reauth',
                        #  data_schema=self.form_schema('icloud_verification_code'),
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
        dev_list_page_no = self.device_list_page_no
        # self._traceui(user_input)

        if Gb.PyiCloud is None:
            await self._log_into_icloud_account({}, self.step_id)

            if (Gb.PyiCloud
                    and Gb.PyiCloud.requires_2fa):
                # return await self.async_step_icloud_verification_code()
                return await self.async_step_reauth()
        elif (self.device_form_icloud_famshr_list == []
                or self.device_form_icloud_fmf_list == []):
            self._build_device_form_selection_lists()
            _traceha(f"buildlist {self.device_form_icloud_famshr_list=}")

        if (Gb.conf_tracking[CONF_USERNAME] == ''
                or Gb.conf_tracking[CONF_PASSWORD] == ''):
            self.menu_msg = 'icloud_acct_not_set_up'
            user_input = {'device_control': DEVICE_LIST_RETURN}

        if user_input is not None:
            # If next page was selected, increment the page number and display it
            if 'next_page_1' in user_input and user_input['next_page_1']:
                dev_list_page_no = 1
                self.device_list_page_no = dev_list_page_no
            elif 'next_page_2' in user_input and user_input['next_page_2']:
                dev_list_page_no = 2
                self.device_list_page_no = dev_list_page_no

            elif user_input['device_control'] == DEVICE_LIST_RETURN:
                self.selected_device_list_control = DEVICE_LIST_RETURN
                return await self.async_step_menu()

            elif user_input['device_control'] == DEVICE_LIST_ADD:
                self.add_device_flag = True
                self.selected_device_data = DEFAULT_DEVICE_CONF.copy()
                return await self.async_step_device_1()

            elif user_input['device_control'] == DEVICE_LIST_DELETE:
                self._select_device_from_device_list(user_input)
                return await self.async_step_delete_device()

            elif user_input['device_control'] == DEVICE_LIST_UPDATE:
                self.selected_device_list_control = DEVICE_LIST_UPDATE
                self._select_device_from_device_list(user_input)
                return await self.async_step_device_1()

        menu_msg = {'base': self.menu_msg} if self.menu_msg else {}
        self.menu_msg = ''

        self._prepare_device_selection_list()

        self.step_id = 'device_list'
        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=menu_msg,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    def _select_device_from_device_list(self, user_input):
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
                self.selected_device_data = Gb.conf_devices[form_devices_list_index]
                self.selected_device_index = form_devices_list_index
                break

        user_input[CONF_DEVICES] = self.selected_device_data[CONF_IC3_DEVICENAME]

        self.selected_device_index = form_devices_list_index

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

        if user_input is not None:
            if user_input['action'].startswith('YES'):
                Gb.conf_devices.pop(self.selected_device_index)
                self.form_devices_list_all.pop(self.selected_device_index)
                devicename = self.form_devices_list_devicename.pop(self.selected_device_index)
                write_storage_icloud3_configuration_file()

                device_cnt = len(self.form_devices_list_all) - 1
                if self.selected_device_index > device_cnt:
                    self.selected_device_index = device_cnt
                if self.selected_device_index <= 4:
                    self.device_list_page_no = 1

            return await self.async_step_device_list()

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema('delete_device'),
                        errors=self.errors,
                        last_step=False)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            TRACKED DEVICE MENU - DEVICE LIST, DEVICE UPDATE FORMS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_device_1(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'device_1'
        self.errors = errors or {}
        self.errors_user_input = {}
        self._traceui(user_input)

        if user_input is not None:
            if user_input.get('cancel_update', False):
                self.add_device_flag = False
                self.user_input_multi_form = {}
                return await self.async_step_device_list()

            change_flag, user_input = self._validate_device_conf_1(user_input)
            if self.add_device_flag:
                user_input = self._add_device_1(user_input)
                self.user_input_multi_form = user_input.copy()

            if change_flag:
                self._update_configuration_file(user_input)

            if not self.errors:
                if change_flag:
                    Gb.config_flow_update_control.update(['devices', 'restart'])
                    self.menu_msg = 'conf_updated'

                return await self.async_step_device_2()

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    async def async_step_device_2(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'device_2'
        self.errors = errors or {}
        self.errors_user_input = {}
        # self._traceui(user_input)

        if user_input is not None:
            if user_input.get('cancel_update', False):
                self.add_device_flag = False
                self.user_input_multi_form = {}
                return await self.async_step_device_list()

            change_flag, user_input = self._validate_device_conf_2(user_input)

            if change_flag:
                if self.add_device_flag:
                    user_input = self._add_device_2(user_input)
                self._update_configuration_file(user_input)
                Gb.config_flow_update_control.update(['devices', 'restart'])

            if not self.errors:
                return await self.async_step_device_list()

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors,
                        last_step=True)

#-------------------------------------------------------------------------------------------
    def _validate_device_conf_1(self, user_input):
        '''
        Validate the device parameters
        '''
        # self._traceui(user_input)

        self.errors = {}
        if 'cancel_update' in user_input:
            user_input.pop('cancel_update')

        user_input[CONF_IC3_DEVICENAME] = slugify(user_input[CONF_IC3_DEVICENAME].strip())
        if user_input[CONF_IC3_DEVICENAME].strip() == '':
            self.errors[CONF_IC3_DEVICENAME] = 'required_field'
            return False, user_input

        elif (self.add_device_flag
                    and user_input[CONF_IC3_DEVICENAME] in self.form_devices_list_devicename):
            self.errors[CONF_IC3_DEVICENAME] = 'duplicate_devicename'
            return False, user_input

        elif (user_input[CONF_IC3_DEVICENAME] in self.form_devices_list_devicename
                and self.form_devices_list_devicename.index(user_input[CONF_IC3_DEVICENAME]) != self.selected_device_index):
            self.errors[CONF_IC3_DEVICENAME] = 'duplicate_devicename'
            return False, user_input

        user_input[CONF_NAME] = user_input[CONF_NAME].strip()
        if user_input[CONF_NAME] == '':
            self.errors[CONF_NAME] = 'required_field'

        # Check to make sure either the iCloud Device or iosApp device was entered
        # You must have one of them to enable tracking
        if (user_input[CONF_FAMSHR_DEVICENAME].strip() == ''):
            user_input[CONF_FAMSHR_DEVICENAME] = OPT_FAMSHR_DEVICENAME[OPT_NONE]

        if (user_input[CONF_FMF_EMAIL].strip() == ''):
            user_input[CONF_FMF_EMAIL] = OPT_FMF_EMAIL[OPT_NONE]

        if (user_input[CONF_IOSAPP_DEVICE].strip() == ''):
            user_input[CONF_IOSAPP_DEVICE] = OPT_IOSAPP_DEVICE[OPT_NONE]

        if (user_input[CONF_FAMSHR_DEVICENAME] == OPT_FAMSHR_DEVICENAME[OPT_NONE]
                and user_input[CONF_FMF_EMAIL] == OPT_FMF_EMAIL[OPT_NONE]
                and user_input[CONF_IOSAPP_DEVICE] == OPT_IOSAPP_DEVICE[OPT_NONE]):
            self.errors['base'] = 'required_field_device'

        change_flag = False
        if not self.errors:
            # iCloud and iOS App devices are valid. Continue
            devicename = user_input[CONF_FAMSHR_DEVICENAME].split(' >')[0]
            user_input[CONF_FAMSHR_DEVICE_ID] = self.devicename_device_id_famshr.get(devicename, '')

            devicename = user_input[CONF_FMF_EMAIL].split(' >')[0]
            user_input[CONF_FMF_DEVICE_ID] = self.devicename_device_id_fmf.get(devicename, '')

            for pname, pvalue in self.selected_device_data.items():
                if pname not in user_input or user_input[pname] != pvalue:
                    change_flag = True
                    break

            if change_flag:
                self.selected_device_data.update(user_input)

        return change_flag, user_input

#-------------------------------------------------------------------------------------------
    def _validate_device_conf_2(self, user_input):

        if 'cancel_update' in user_input:
            user_input.pop('cancel_update')

        user_input = self._validate_time_str(user_input)

        if (user_input[CONF_PICTURE].startswith('Select')
                or user_input[CONF_PICTURE].startswith('━')):
            user_input[CONF_PICTURE] = ''

        track_from_zones = []
        for zone, zone_name in self.device_form_zone_list.items():
            if zone in user_input[CONF_TRACK_FROM_ZONES]:
                track_from_zones.append(zone)

        if 'home' in track_from_zones:
            track_from_zones.remove('home')
        track_from_zones.append('home')
        user_input[CONF_TRACK_FROM_ZONES] = track_from_zones

        change_flag = False
        if not self.errors:
            for pname, pvalue in self.selected_device_data.items():
                if pname not in user_input or user_input[pname] != pvalue:
                    change_flag = True
                    break

        if self.add_device_flag:
            change_flag = True

        if change_flag:
            self.selected_device_data.update(user_input)

        return change_flag, user_input

#-------------------------------------------------------------------------------------------
    def _add_device_1(self, user_input):
        '''
        Adding a device. Get the user_input and use it to set default fields to be used on the
        update device_2 form.
        '''
        self.errors = {}

        change_flag, user_input = self._validate_device_conf_1(user_input)

        # If adding a new device and validating on the top part (devicename and icloud/iosapp
        # device selectionh), fill in other fields and display the complete device form
        if not self.errors:
            name, device_type = self._extract_name_device_type(user_input[CONF_IC3_DEVICENAME])

            user_input[CONF_DEVICE_TYPE] = device_type
            user_input[CONF_TRACK_FROM_ZONES] = [HOME]

            default_inzone_interval_field = 'inzone_interval_'
            if user_input[CONF_IOSAPP_DEVICE] == OPT_IOSAPP_DEVICE[OPT_NONE]:
                default_inzone_interval_field += 'no_iosapp'
            else:
                default_inzone_interval_field += device_type.lower()

            if default_inzone_interval_field in Gb.conf_general:
                user_input[CONF_INZONE_INTERVAL] = Gb.conf_general[default_inzone_interval_field]
            else:
                user_input[CONF_INZONE_INTERVAL] = DEFAULT_INZONE_INTERVAL

            self.selected_device_data.update(user_input)
            return user_input

        return user_input

#-------------------------------------------------------------------------------------------
    def _add_device_2(self, user_input):
        '''
        Adding a device. Combine the user_input from device_1 with device_2 forms and update
        config lists.
        '''
        self.user_input_multi_form.update(user_input)
        user_input = self.user_input_multi_form.copy()
        self.user_input_multi_form = {}

        user_input[CONF_ACTIVE] = True
        self.selected_device_data.update(user_input)
        self.selected_device_data.pop('cancel_update')
        user_input = self.selected_device_data.copy()

        Gb.conf_devices.append(user_input)

        # Add the new device to the device_list form and and set it's position index
        self.form_devices_list_all.append(self._format_device_list_item(user_input))
        self.form_devices_list_devicename.append(user_input[CONF_IC3_DEVICENAME])
        self.selected_device_index = len(Gb.conf_devices) - 1
        # self.selected_device_index = len(Gb.conf_tracking[CF_DATA_DEVICES]) - 1
        if self.selected_device_index >= 5:
            self.device_list_page_no = 2
        self.conf_devices_list_selected[self.device_list_page_no] = \
                    self.form_devices_list_all[self.selected_device_index]

        return user_input

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            DEVICES LIST FORM, DEVICE UPDATE FORM SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _build_device_form_selection_lists(self):

        if Gb.PyiCloud is None:
            _traceha('Not logged into iCloud Account')
            return

        # Build the lists for the device form selection fields
        self._get_device_form_picture_list()
        self._get_famshr_devices_list()
        self._get_fmf_devices_list()
        self._get_device_form_iosapp_list()
        self._get_zone_list()


#----------------------------------------------------------------------
    def _get_famshr_devices_list(self):
        '''
        Cycle through famshr data and get devices that can be tracked for the
        icloud device selection list
        '''
        devices_desc = start_ic3.get_famshr_devices()

        device_id_by_device_fname   = devices_desc[0]
        device_fname_by_device_id   = devices_desc[1]
        device_info_device_fname    = devices_desc[2]
        self.device_form_icloud_famshr_list = OPT_FAMSHR_DEVICENAME.copy()

        for device_fname, device_info in device_info_device_fname.items():
            self.device_form_icloud_famshr_list.append(f"{device_fname} > {device_info}")
            for device in Gb.conf_devices:
                if device[CONF_FAMSHR_DEVICENAME] == device_fname:
                    device[CONF_FAMSHR_DEVICENAME] = f"{device_fname} > {device_info}"
        _traceha(f"bef6 {self.device_form_icloud_famshr_list=}")
        self._ensure_six_list_items(self.device_form_icloud_famshr_list)
        _traceha(f"aft6 {self.device_form_icloud_famshr_list=}")

#----------------------------------------------------------------------
    def _get_fmf_devices_list(self):
        '''
        Cycle through fmf following, followers and contact details data and get
        devices that can be tracked for the icloud device selection list
        '''

        devices_desc = start_ic3.get_fmf_devices()

        device_id_by_fmf_email   = devices_desc[0]
        fmf_email_by_device_id   = devices_desc[1]
        device_info_by_fmf_email = devices_desc[2]
        self.device_form_icloud_fmf_list = OPT_FMF_EMAIL

        for email, device_info in device_info_by_fmf_email.items():
            self.device_form_icloud_fmf_list.append(f"{email} > {device_info}")
            for device in Gb.conf_devices:
                if device[CONF_FMF_EMAIL] == email:
                    device[CONF_FMF_EMAIL] = f"{email} > {device_info}"

        self._ensure_six_list_items(self.device_form_icloud_fmf_list)

#----------------------------------------------------------------------
    def _get_device_form_iosapp_list(self):
        '''
        Cycle through the /config/.storage/core.entity_registry file and return
        the entities for platform ('mobile_app', 'ios', etc)
        '''

        try:
            if Gb.entity_registry_file == '':
                Gb.entity_registry_file  = Gb.hass.config.path( STORAGE_DIR,
                                                                STORAGE_KEY_ENTITY_REGISTRY)
            self.devicename_device_info_iosapp = {}
            self.device_form_iosapp_list = OPT_IOSAPP_DEVICE.copy()

            with open(Gb.entity_registry_file, 'r') as f:
                entity_reg_data     = json.loads(f.read())

                mobile_app_entity_list = [x for x in entity_reg_data['data']['entities'] if x['platform'] == 'mobile_app']
                device_tracker_list = [x for x in mobile_app_entity_list if x[ENTITY_ID].startswith('device_tracker')]

                for entity in device_tracker_list:
                    devicename = slugify(entity['original_name'])
                    self.devicename_device_info_iosapp[devicename] = (
                                f"{entity['original_name']} "
                                f"({entity[ENTITY_ID].replace('device_tracker.', '')})")

        except Exception as err:
            log_exception(err)
            pass

        for devicename, device_info in self.devicename_device_info_iosapp.items():
            self.device_form_iosapp_list.append(f"{devicename} > {device_info}")

        self._ensure_six_list_items(self.device_form_iosapp_list)

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
            self.form_devices_list_all.append(self._format_device_list_item(conf_device_data))
            self.form_devices_list_devicename.append(conf_device_data[CONF_IC3_DEVICENAME])

        # No devices in config, reset to initial conditions
        if self.form_devices_list_all == []:
            self.conf_devices_list_selected = ['', '', '']
            self.selected_device_index = 0
            return

        # Build the device-list page items
        device_list_index_from = 0 if self.device_list_page_no <= 1 else 5
        device_list_index_to = device_list_index_from + 5
        if device_list_index_to > len(self.form_devices_list_all):
            device_list_index_to = len(self.form_devices_list_all)

        for index in range(device_list_index_from, device_list_index_to):
            self.form_devices_list_displayed.append(self.form_devices_list_all[index])

        # Save the selected item info just updated to be used in reselecting the same item via the default value
        if self.conf_devices_list_selected[self.device_list_page_no] == '':
            self.conf_devices_list_selected[self.device_list_page_no] = \
                            self.form_devices_list_all[device_list_index_from]

        # Only update the default value for the page the device item is on
        elif ((self.device_list_page_no == 1 and self.selected_device_index < 5)
                or (self.device_list_page_no == 2 and self.selected_device_index >= 5)):
            self.conf_devices_list_selected[self.device_list_page_no] = \
                            self.form_devices_list_all[self.selected_device_index]



#-------------------------------------------------------------------------------------------
    def _format_device_list_item(self, conf_device_data):
        '''
        Format the text that is displayed for the device on the device_list form
        '''

        device_info  = (f"{conf_device_data[CONF_IC3_DEVICENAME]} . {RARROW} . ")

        if conf_device_data[CONF_ACTIVE] is False:
            device_info += "INACTIVE, "

        device_info += (f"{conf_device_data[CONF_NAME]}, "
                        f"FamShr-({conf_device_data[CONF_FAMSHR_DEVICENAME]}), "
                        f"FmF-({conf_device_data[CONF_FMF_EMAIL]}), "
                        f"iOSApp-({conf_device_data[CONF_IOSAPP_DEVICE]})")

        return device_info

#-------------------------------------------------------------------------------------------
    def _get_device_form_picture_list(self):
        self.device_form_picture_list = OPT_PICTURE
        self.device_form_picture_list.extend([
                x for x in os.listdir(Gb.ha_config_www_directory)
                if (x.endswith('.png') or x.endswith('.jpg'))])

        self._ensure_six_list_items(self.device_form_picture_list)

#-------------------------------------------------------------------------------------------
    def _get_zone_list(self):

        self.device_form_zone_list = OrderedDict()
        with open(Gb.entity_registry_file, 'r') as f:
            entity_reg_data     = json.loads(f.read())
            zone_entities = [x for x in entity_reg_data['data']['entities'] if x['platform'] == 'zone']

        for zone_entity in zone_entities:
            zone      = zone_entity['entity_id'].replace('zone.', '')
            if (zone and zone != 'home'):
                zone_name = zone.title().replace('_', '')
                self.device_form_zone_list[zone] = zone_name
        self.device_form_zone_list['home'] = 'Home'

        dummy_key = ''
        for i in range(6 - len(self.device_form_zone_list)):
            dummy_key += '.'
            self.device_form_zone_list[dummy_key] = '.'

#-------------------------------------------------------------------------------------------
    def _ensure_six_list_items(self, item_list):
        for i in range(6 - len(item_list)):
            item_list.append('')

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                      MISCELLANEOUS SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

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
    def _parm_or_error_msg(self, pname, conf_group=CF_DATA_GENERAL):
        '''
        Determine the value that should be displayed in the config_flow parameter entry screen based
        on whether it was entered incorrectly and has an error message.

        Return:
            Value in errors if it is in errors
            Value in Gb.conf_general[CONF_pname] if it is valid
        '''
        if conf_group == CF_PROFILE:
            return self.errors_user_input.get(pname) or Gb.conf_profile[pname]
        elif conf_group == CF_DATA_TRACKING:
            return self.errors_user_input.get(pname) or Gb.conf_tracking[pname]
        else:
            pvalue = self.errors_user_input.get(pname) or Gb.conf_data[conf_group][pname]
            if pname in CONF_PARAMETER_FLOAT:
                pvalue = str(pvalue).replace('.0', '')
            return pvalue

#-------------------------------------------------------------------------------------------
    def _parm_or_device(self, pname, suggested_value=''):
        parm_displayed = self.errors_user_input.get(pname) \
                            or self.user_input_multi_form.get(pname) \
                            or self.selected_device_data.get(pname) \
                            or suggested_value
        parm_displayed = ' ' if parm_displayed == '' else parm_displayed
        _traceha(f"parm {parm_displayed=}")
        return parm_displayed

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
                elif isnumber(str(time_parts[0])) is False:
                    self.errors[pname] = "not_numeric"
                    self.errors_user_input[pname] = user_input[pname]
                    continue
                elif instr(time_parts[1], 'm'):
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
    def _display_text_as_or_error_msg(self, item_no):
        '''
        Determine the value that should be displayed in the config_flow display_text_as
        parameter entry screen based on whether it was entered incorrectly and has an
        error message.

        Input:
            item_no - The index of the item in the display_text_as variable
            errors  - The errors dictionary
        Return:
            Value in errors if it is in errors
            Value in Gb.conf_general[CONF_DISPLAY_TEXT_AS][item_no] variable if it is valid
        '''

        return self.errors_user_input.get(f"text_{item_no}") or Gb.conf_general[CONF_DISPLAY_TEXT_AS][item_no]
        # return self.errors.get(f"text_{item_no}") or Gb.conf_general[CONF_DISPLAY_TEXT_AS][item_no]

#-------------------------------------------------------------------------------------------
    def _parm_with_example_text(self, config_parameter, input_select_list_items):
        '''
        The input_select_list for the parameter has an example text '(Example: exampletext)'
        as part of list of options display for user selection. The exampletext is not part
        of the configuration parameter. Dydle through the input_select_list and determine which
        one should be the default value.

        Return:
            default - The input_select item to be used for the default value
        '''
        for isli_with_example in input_select_list_items:
            if isli_with_example.startswith(Gb.conf_general[config_parameter]):
                return isli_with_example

        return input_select_list_items[0]

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
        if step_id == 'menu':
            if self.menu_page_no == 1:
                menu_items = MENU_ITEMS_PAGE_1
                menu_next_page = 'menu_next_page_2'
            else:
                menu_items = MENU_ITEMS_PAGE_2
                menu_next_page = 'menu_next_page_1'

            # schema = {}
            schema = vol.Schema({
                    vol.Required("menu_item",
                                default=self.selected_menu_item[self.menu_page_no]): vol.In(menu_items),
                    vol.Optional(menu_next_page, default=False): bool,
                    vol.Required("menu_control",
                                default=MENU_ITEMS_CONTROL[0]): vol.In(MENU_ITEMS_CONTROL),
            })

            return schema

        elif step_id == 'restart_icloud3':
            return  vol.Schema({
                        vol.Required('restart_now_later',
                                    default=OPT_RESTART_NOW_LATER[0]):
                                    vol.In(OPT_RESTART_NOW_LATER),
                    })

        elif step_id == 'icloud_account':
            return  vol.Schema({
                        vol.Optional(CONF_USERNAME,
                                    default=self._parm_or_error_msg(CONF_USERNAME, CF_DATA_TRACKING)): str,
                        vol.Optional(CONF_PASSWORD,
                                    default=self._parm_or_error_msg(CONF_PASSWORD, CF_DATA_TRACKING)): str,
                        vol.Required(CONF_TRACKING_METHOD,
                                    default=self._parm_or_error_msg(CONF_TRACKING_METHOD, CF_DATA_TRACKING)):
                                    vol.In(OPT_TRACKING_METHOD),
                        vol.Optional('icloud_acct_login',
                                     default=(Gb.PyiCloud is None)): bool,
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == 'reauth':
            return  vol.Schema({
                        vol.Required(CONF_VERIFICATION_CODE): str,
                    })

        elif step_id == 'device_list':
            if self.device_list_page_no <= 1:
                next_page = 'next_page_2'
            else:
                next_page = 'next_page_1'

            device_list_control = DEVICE_LIST_CONTROL \
                if len(self.form_devices_list_all) < 10 else DEVICE_LIST_CONTROL_NO_ADD

            schema = {}
            schema = vol.Schema({})
            if self.form_devices_list_displayed != []:
                    schema = schema.extend({
                        vol.Required("devices",
                                    default=self.conf_devices_list_selected[self.device_list_page_no]):
                                    vol.In(self.form_devices_list_displayed),})

            if len(self.form_devices_list_all) > 5:
                    schema = schema.extend({
                        vol.Optional(next_page, default=False): bool})

            schema = schema.extend({
                        vol.Required("device_control",
                                    #  default=DEVICE_LIST_CONTROL[3]): vol.In(device_list_control)})
                                     default=self.selected_device_list_control):
                                     vol.In(device_list_control)})

            return schema

        elif step_id == 'device_1':
            _traceha(f"dev1 {self.device_form_icloud_famshr_list=}")
            schema = vol.Schema({
                        vol.Optional(CONF_IC3_DEVICENAME,
                                    default=self._parm_or_device(CONF_IC3_DEVICENAME)): str,
                        vol.Optional(CONF_NAME,
                                    default=self._parm_or_device(CONF_NAME)): str,
                        vol.Optional(CONF_FAMSHR_DEVICENAME,
                                    default=self._parm_or_device(CONF_FAMSHR_DEVICENAME,
                                                     OPT_FAMSHR_DEVICENAME[OPT_NONE])):
                                    vol.In(self.device_form_icloud_famshr_list),
                        vol.Optional(CONF_FMF_EMAIL,
                                    default=self._parm_or_device(CONF_FMF_EMAIL,
                                                    OPT_FMF_EMAIL[OPT_NONE])):
                                    vol.In(self.device_form_icloud_fmf_list),
                        vol.Optional(CONF_IOSAPP_DEVICE,
                                    default=self._parm_or_device(CONF_IOSAPP_DEVICE,
                                                    OPT_IOSAPP_DEVICE[OPT_NONE])):
                                    vol.In(self.device_form_iosapp_list),
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == 'device_2':
            schema = vol.Schema({
                        vol.Optional(CONF_IC3_DEVICENAME,
                                    default=self._parm_or_device(CONF_IC3_DEVICENAME)): str,
                        vol.Optional(CONF_PICTURE,
                                    default=self._parm_or_device(CONF_PICTURE,
                                                    OPT_PICTURE[OPT_NONE])):
                                    vol.In(self.device_form_picture_list),
                        vol.Optional(CONF_TRACK_FROM_ZONES,
                                    default=self._parm_or_device(CONF_TRACK_FROM_ZONES)):
                                    cv.multi_select(self.device_form_zone_list),
                        vol.Optional(CONF_DEVICE_TYPE,
                                    default=self._parm_or_device(CONF_DEVICE_TYPE)):
                                    vol.In(APPLE_DEVICE_TYPES_FNAME),
                        vol.Optional(CONF_INZONE_INTERVAL,
                                    default=self._parm_or_device(CONF_INZONE_INTERVAL)): str,
                        vol.Optional(CONF_ACTIVE, default=True): bool,
                        # vol.Optional(CONF_ACTIVE, default=self._parm_or_device(CONF_ACTIVE)): bool,
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == 'delete_device':
            schema = vol.Schema({
                        vol.Required('action',
                                    default='NO - Cancel the delete request'):
                                    vol.In(['YES - Delete the device', 'NO - Cancel the delete request']),
                    })

        elif step_id == 'evlog_field_formats':
            default_display_zone_format = self._parm_with_example_text(CONF_DISPLAY_ZONE_FORMAT, OPT_DISPLAY_ZONE_FORMAT)

            schema = vol.Schema({
                        vol.Required(CONF_DISPLAY_ZONE_FORMAT,
                                    default=default_display_zone_format): vol.In(OPT_DISPLAY_ZONE_FORMAT),
                        vol.Required(CONF_TIME_FORMAT,
                                    default=Gb.conf_general[CONF_TIME_FORMAT]): vol.In(OPT_TIME_FORMAT),
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == 'display_text_as':
            if self.dta_page_no <= 1:
                schema = vol.Schema({
                            vol.Optional('text_0', default=self._display_text_as_or_error_msg(0)): str,
                            vol.Optional('text_1', default=self._display_text_as_or_error_msg(1)): str,
                            vol.Optional('text_2', default=self._display_text_as_or_error_msg(2)): str,
                            vol.Optional('text_3', default=self._display_text_as_or_error_msg(3)): str,
                            vol.Optional('text_4', default=self._display_text_as_or_error_msg(4)): str,
                            vol.Optional('dta_next_page_2', default=False): bool,
                            vol.Optional('cancel_update', default=False): bool,
                        })
            else:
                schema = vol.Schema({
                            vol.Optional('text_5', default=self._display_text_as_or_error_msg(5)): str,
                            vol.Optional('text_6', default=self._display_text_as_or_error_msg(6)): str,
                            vol.Optional('text_7', default=self._display_text_as_or_error_msg(7)): str,
                            vol.Optional('text_8', default=self._display_text_as_or_error_msg(8)): str,
                            vol.Optional('text_9', default=self._display_text_as_or_error_msg(9)): str,
                            # vol.Optional('text_10', default=self._display_text_as_or_error_msg(10)): str,
                            # vol.Optional('text_11', default=self._display_text_as_or_error_msg(11)): str,
                            vol.Optional('dta_next_page_1', default=False): bool,
                            vol.Optional('cancel_update', default=False): bool,
                        })

        elif step_id == 'misc_parms':
            schema = vol.Schema({
                        vol.Required(CONF_UNIT_OF_MEASUREMENT,
                                    default=Gb.conf_general[CONF_UNIT_OF_MEASUREMENT]): vol.In(OPT_UNIT_OF_MEASUREMENT),
                        vol.Required(CONF_MAX_INTERVAL,
                                    default=Gb.conf_general[CONF_MAX_INTERVAL]): str,
                        vol.Required(CONF_GPS_ACCURACY_THRESHOLD,
                                    default=Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]): cv.positive_int,
                        vol.Required(CONF_OLD_LOCATION_THRESHOLD,
                                    default=Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD]): str,
                        vol.Required(CONF_TRAVEL_TIME_FACTOR,
                                    default=str(self._parm_or_error_msg(CONF_TRAVEL_TIME_FACTOR))): str,
                        vol.Required(CONF_LOG_LEVEL,
                                    default=Gb.conf_general[CONF_LOG_LEVEL]): vol.In(OPT_LOG_LEVEL),
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == 'inzone':
            schema = vol.Schema({
                        vol.Required(CONF_CENTER_IN_ZONE,
                                    default=Gb.conf_general[CONF_CENTER_IN_ZONE]): bool,
                        vol.Required(CONF_DISCARD_POOR_GPS_INZONE,
                                    default=Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]): bool,
                        vol.Required(CONF_INZONE_INTERVAL_DEFAULT,
                                    default=self._parm_or_error_msg(CONF_INZONE_INTERVAL_DEFAULT)): str,
                        vol.Required(CONF_INZONE_INTERVAL_IPHONE,
                                    default=self._parm_or_error_msg(CONF_INZONE_INTERVAL_IPHONE)): str,
                        vol.Required(CONF_INZONE_INTERVAL_IPAD,
                                    default=self._parm_or_error_msg(CONF_INZONE_INTERVAL_IPAD)): str,
                        vol.Required(CONF_INZONE_INTERVAL_WATCH,
                                    default=self._parm_or_error_msg(CONF_INZONE_INTERVAL_WATCH)): str,
                        vol.Required(CONF_INZONE_INTERVAL_IPOD,
                                    default=self._parm_or_error_msg(CONF_INZONE_INTERVAL_IPOD)): str,
                        vol.Required(CONF_INZONE_INTERVAL_NO_IOSAPP,
                                    default=self._parm_or_error_msg(CONF_INZONE_INTERVAL_NO_IOSAPP)): str,
                        vol.Optional('cancel_update', default=False): bool,
                     })

        elif step_id == 'waze_1':
            schema = vol.Schema({
                        vol.Required(CONF_DISTANCE_METHOD,
                                    default=Gb.conf_general[CONF_DISTANCE_METHOD]): vol.In(OPT_DISTANCE_METHOD),
                        vol.Required(CONF_WAZE_REGION,
                                    default=Gb.conf_general[CONF_WAZE_REGION]): vol.In(OPT_WAZE_REGION),
                        vol.Required(CONF_WAZE_MIN_DISTANCE,
                                    default=Gb.conf_general[CONF_WAZE_MIN_DISTANCE]): cv.positive_int,
                        vol.Required(CONF_WAZE_MAX_DISTANCE,
                                    default=Gb.conf_general[CONF_WAZE_MAX_DISTANCE]): cv.positive_int,
                        vol.Required(CONF_WAZE_REALTIME,
                                    default=Gb.conf_general[CONF_WAZE_REALTIME]): bool,
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == 'waze_2':
            schema = vol.Schema({
                        vol.Required(CONF_WAZE_HISTORY_DATABASE_USED,
                                    default=Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED]): bool,
                        vol.Required(CONF_WAZE_HISTORY_MAX_DISTANCE,
                                    default=Gb.conf_general[CONF_WAZE_HISTORY_MAX_DISTANCE]): cv.positive_int,
                        vol.Required(CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION,
                                    default=Gb.conf_general[CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION]):
                                    vol.In(OPT_WAZE_HISTORY_MAP_TRACK_DIRECTION),
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == 'stationary_zone':
            schema = vol.Schema({
                        vol.Required(CONF_STAT_ZONE_STILL_TIME,
                                    default=self._parm_or_error_msg(CONF_STAT_ZONE_STILL_TIME)): str,
                        vol.Required(CONF_STAT_ZONE_INZONE_INTERVAL,
                                    default=self._parm_or_error_msg(CONF_STAT_ZONE_INZONE_INTERVAL)): str,
                        vol.Required(CONF_STAT_ZONE_BASE_LATITUDE,
                                    default=self._parm_or_error_msg(CONF_STAT_ZONE_BASE_LATITUDE)): str,
                                    # default=str(self._parm_or_error_msg(CONF_STAT_ZONE_BASE_LATITUDE))): str,
                        vol.Required(CONF_STAT_ZONE_BASE_LONGITUDE,
                                    default=self._parm_or_error_msg(CONF_STAT_ZONE_BASE_LONGITUDE)): str,
                                    # default=str(self._parm_or_error_msg(CONF_STAT_ZONE_BASE_LONGITUDE)): str,
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == 'sensors':
            schema = vol.Schema({
                        vol.Optional(CONF_SENSOR_NAME, default=Gb.conf_sensors[CONF_SENSOR_NAME]): bool,
                        vol.Optional(CONF_SENSOR_BADGE, default=Gb.conf_sensors[CONF_SENSOR_BADGE]): bool,
                        vol.Optional(CONF_SENSOR_BATTERY, default=Gb.conf_sensors[CONF_SENSOR_BATTERY]): bool,
                        vol.Optional(CONF_SENSOR_BATTERY_STATUS, default=Gb.conf_sensors[CONF_SENSOR_BATTERY_STATUS]): bool,
                        vol.Optional(CONF_SENSOR_TRIGGER, default=Gb.conf_sensors[CONF_SENSOR_TRIGGER]): bool,
                        vol.Optional(CONF_SENSOR_INTERVAL, default=Gb.conf_sensors[CONF_SENSOR_INTERVAL]): bool,
                        vol.Optional(CONF_SENSOR_LAST_LOCATED, default=Gb.conf_sensors[CONF_SENSOR_LAST_LOCATED]): bool,
                        vol.Optional(CONF_SENSOR_LAST_UPDATE, default=Gb.conf_sensors[CONF_SENSOR_LAST_UPDATE]): bool,
                        vol.Optional(CONF_SENSOR_NEXT_UPDATE, default=Gb.conf_sensors[CONF_SENSOR_NEXT_UPDATE]): bool,
                        vol.Optional(CONF_SENSOR_ZONE_DISTANCE, default=Gb.conf_sensors[CONF_SENSOR_ZONE_DISTANCE]): bool,
                        vol.Optional(CONF_SENSOR_WAZE_DISTANCE, default=Gb.conf_sensors[CONF_SENSOR_WAZE_DISTANCE]): bool,
                        vol.Optional(CONF_SENSOR_CALC_DISTANCE, default=Gb.conf_sensors[CONF_SENSOR_CALC_DISTANCE]): bool,
                        vol.Optional(CONF_SENSOR_TRAVEL_TIME, default=Gb.conf_sensors[CONF_SENSOR_TRAVEL_TIME]): bool,
                        vol.Optional(CONF_SENSOR_TRAVEL_DISTANCE, default=Gb.conf_sensors[CONF_SENSOR_TRAVEL_DISTANCE]): bool,
                        vol.Optional(CONF_SENSOR_DIR_OF_TRAVEL, default=Gb.conf_sensors[CONF_SENSOR_DIR_OF_TRAVEL]): bool,
                        vol.Optional(CONF_SENSOR_GPS_ACCURACY, default=Gb.conf_sensors[CONF_SENSOR_GPS_ACCURACY]): bool,
                        vol.Optional(CONF_SENSOR_ALTITUDE, default=Gb.conf_sensors[CONF_SENSOR_ALTITUDE]): bool,
                        vol.Optional(CONF_SENSOR_VERTICAL_ACCURACY, default=Gb.conf_sensors[CONF_SENSOR_VERTICAL_ACCURACY]): bool,
                        vol.Optional(CONF_SENSOR_ZONE, default=Gb.conf_sensors[CONF_SENSOR_ZONE]): bool,
                        vol.Optional(CONF_SENSOR_ZONE_NAME, default=Gb.conf_sensors[CONF_SENSOR_ZONE_NAME]): bool,
                        vol.Optional(CONF_SENSOR_ZONE_TITLE, default=Gb.conf_sensors[CONF_SENSOR_ZONE_TITLE]): bool,
                        vol.Optional(CONF_SENSOR_ZONE_FNAME, default=Gb.conf_sensors[CONF_SENSOR_ZONE_FNAME]): bool,
                        vol.Optional(CONF_SENSOR_ZONE_TIMESTAMP, default=Gb.conf_sensors[CONF_SENSOR_ZONE_TIMESTAMP]): bool,
                        vol.Optional(CONF_SENSOR_LAST_ZONE, default=Gb.conf_sensors[CONF_SENSOR_LAST_ZONE]): bool,
                        vol.Optional(CONF_SENSOR_LAST_ZONE_NAME, default=Gb.conf_sensors[CONF_SENSOR_LAST_ZONE_NAME]): bool,
                        vol.Optional(CONF_SENSOR_LAST_ZONE_TITLE, default=Gb.conf_sensors[CONF_SENSOR_LAST_ZONE_TITLE]): bool,
                        vol.Optional(CONF_SENSOR_LAST_ZONE_FNAME, default=Gb.conf_sensors[CONF_SENSOR_LAST_ZONE_FNAME]): bool,
                        vol.Optional(CONF_SENSOR_POLL_CNT, default=Gb.conf_sensors[CONF_SENSOR_POLL_CNT]): bool,
                        vol.Optional(CONF_SENSOR_INFO, default=Gb.conf_sensors[CONF_SENSOR_INFO]): bool,
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == 'settings':
            schema = vol.Schema({
                        vol.Required(CONF_EVENT_LOG_CARD_DIRECTORY,
                                    default=self._parm_or_error_msg(CONF_EVENT_LOG_CARD_DIRECTORY)): str,
                                    # default=Gb.conf_general[CONF_EVENT_LOG_CARD_DIRECTORY]): str,
                        vol.Required(CONF_EVENT_LOG_CARD_PROGRAM,
                                    default=self._parm_or_error_msg(CONF_EVENT_LOG_CARD_PROGRAM)): str,
                        vol.Required(CONF_LOG_LEVEL,
                                    default=Gb.conf_general[CONF_LOG_LEVEL]): vol.In(OPT_LOG_LEVEL),
                        vol.Optional('cancel_update', default=False): bool,
                    })

        elif step_id == '':
            pass

        return schema
