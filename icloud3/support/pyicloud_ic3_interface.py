
from ..global_variables import GlobalVariables as Gb
from ..const            import (NOT_SET, HOME, HIGH_INTEGER, EVLOG_ALERT, EVLOG_ERROR, CRLF_DOT,
                                ICLOUD, DOMAIN, IOSAPP,
                                CONF_TRACKING_METHOD, OPT_TRACKING_METHOD, OPT_TM_IOSAPP_ONLY,
                                STORAGE_DIR,
                                LATITUDE, AUTHENTICATED, CONF_NAME, CONF_USERNAME, CONF_PASSWORD, )

from ..support           import start_ic3 as start_ic3

from ..helpers.base     import (instr, is_statzone,
                                post_event, post_error_msg, post_log_info_msg, post_startup_event, post_monitor_msg,
                                log_exception, log_error_msg, internal_error_msg2, _trace, _traceha, )
from ..helpers.time     import (time_now_secs, secs_to_time, secs_to_datetime, )
from ..helpers.format   import (format_age, )
# from ..helpers.entity_io import (get_state, get_attributes, get_last_changed_time, extract_attr_value, )

from ..support.pyicloud_ic3  import PyiCloudService
from ..support.pyicloud_ic3  import (
            PyiCloudFailedLoginException,
            PyiCloudServiceNotActivatedException,
            PyiCloudNoDevicesException,
            PyiCloudAPIResponseException,
            PyiCloud2SARequiredException,
            )


import os
import time
import traceback
from re import match
from   homeassistant.util    import slugify


#########################################################
#
#   PYICLOUD-IC3 INTERFACE FUNCTIONS
#
#########################################################
def pyicloud_initialize_device_api():
    #See if pyicloud_ic3 is available

    Gb.pyicloud_authentication_cnt  = 0
    Gb.pyicloud_location_update_cnt = 0
    Gb.pyicloud_calls_time          = 0.0

    if Gb.username == '' or Gb.password == '':
        event_msg =(f"iCloud3 Alert > The iCloud username or password has not been set up. "
                    f"iCloud location tracking will not be done. ")
        post_startup_event(event_msg)
        return

    #Set up pyicloud cookies directory & file names
    try:
        ##config_flow mod
        # Gb.icloud_cookies_dir  = Gb.hass.config.path(STORAGE_DIR, STORAGE_KEY_ICLOUD)
        Gb.icloud_cookies_dir  = Gb.ha_storage_icloud3
        Gb.icloud_cookies_file = "".join([c for c in Gb.username if match(r"\w", c)])
        if not os.path.exists(Gb.icloud_cookies_dir):
            os.makedirs(Gb.icloud_cookies_dir)

    except Exception as err:
        log_exception(err)

    pyicloud_authenticate_account(initial_setup=True)

    if Gb.PyiCloud:
        event_msg =("iCloud Web Services interface (pyicloud_ic3.py) > Verified")
        post_startup_event(event_msg)

    else:
        event_msg =(f"iCloud3 Error > iCloud Account Authentication is needed or "
                    f"another error occurred. The iOSApp tracking method will be "
                    f"used until the iCloud account authentication is complete. See the "
                    f"HA Notification area to continue. iCloud3 will then restart.")
        post_error_msg(event_msg)

#--------------------------------------------------------------------
def pyicloud_authenticate_account(initial_setup=False):
    '''
    Authenticate the iCloud Acount via pyicloud
    If successful - Gb.PyiCloud to the api of the pyicloudservice for the username
    If not        - set Gb.PyiCloud = None
    '''
    try:
        # If not using the iCloud location svcs, nothing to do
        _traceha(f"87 pyi {Gb.tracking_method_use_icloud=} {Gb.tracking_method_use_iosapp=}")
        if Gb.tracking_method_use_icloud is False:
            return
        elif Gb.username == '' or Gb.password == '':
            return

        auth_start_time = time.time()
        if Gb.PyiCloud:
            Gb.PyiCloud.authenticate(refresh_session=True, service='find')

        else:
            Gb.PyiCloud = PyiCloudService(Gb.username, Gb.password,
                                    cookie_directory=Gb.icloud_cookies_dir,
                                    session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                    with_family=True)

        Gb.pyicloud_calls_time += (time.time() - auth_start_time)
        if Gb.authentication_error_retry_secs != HIGH_INTEGER:
            Gb.authenticated_time = 0
            Gb.authentication_error_retry_secs = HIGH_INTEGER
            start_ic3.set_tracking_method(ICLOUD)

        if Gb.PyiCloud:
            Gb.PyiCloud_FamilySharing = Gb.PyiCloud.family_sharing_object
            Gb.PyiCloud_FindMyFriends = Gb.PyiCloud.find_my_friends_object
            _is_authentication_2fa_code_needed(initial_setup=True)

        reset_authentication_time()

    except (PyiCloudFailedLoginException, PyiCloudNoDevicesException,
            PyiCloudAPIResponseException) as err:

        _is_authentication_2fa_code_needed()
        return False

    except (PyiCloud2SARequiredException) as err:
        _is_authentication_2fa_code_needed()
        return False

    except Exception as err:
        log_exception(err)
        return False

    return True

#--------------------------------------------------------------------
def reset_authentication_time():
    '''
    If an authentication was done, update the count & time and display
    an Event Log message
    '''
    authentication_method = Gb.PyiCloud.authentication_method
    if authentication_method == '':
        return

    Gb.pyicloud_authentication_cnt += 1
    last_authenticated_time = Gb.authenticated_time
    Gb.authenticated_time   = time_now_secs()
    Gb.attrs[AUTHENTICATED] = secs_to_datetime(time_now_secs())

    event_msg =(f"iCloud Account Authenticated "
                f"(#{Gb.pyicloud_authentication_cnt}) > LastAuth-")
    if last_authenticated_time == 0:
        event_msg += "Never (Initializing)"
    else:
        event_msg += (f"{secs_to_time(last_authenticated_time)} "
                    f" ({format_age(time_now_secs() - last_authenticated_time)})")
    event_msg += (f", Method-{authentication_method}")
    post_log_info_msg("*", event_msg)

#--------------------------------------------------------------------
def _is_authentication_2fa_code_needed(initial_setup=False):
    '''
    Make sure iCloud is still available and doesn't need to be authenticationd
    in 15-second polling loop

    Returns True  if Authentication is needed.
    Returns False if Authentication succeeded
    '''

    if Gb.PyiCloud.requires_2fa:
        pass
    elif Gb.tracking_method_IOSAPP is False:
        return
    elif initial_setup:
        pass
    elif Gb.start_icloud3_inprocess_flag:
        return False

    # from ..support.pyicloud_ic3 import PyiCloudException

    try:
        if initial_setup is False:
            if Gb.PyiCloud is None:
                event_msg =("iCloud/FmF API Error, No device API information "
                                "for devices. Resetting iCloud")
                post_error_msg(event_msg)
                Gb.start_icloud3_request_flag = True

            elif Gb.start_icloud3_request_flag:    #via service call
                event_msg =("iCloud Restarting, Reset command issued")
                post_error_msg(event_msg)
                Gb.start_icloud3_request_flag = True

            if Gb.PyiCloud is None:
                event_msg =("iCloud Authentication Required, will retry")
                post_error_msg(event_msg)
                return True #Authentication needed

        if Gb.PyiCloud is None:
            return True

        #See if 2fa Verification needed
        if Gb.PyiCloud.requires_2fa is False:
            return False

        alert_msg = (f"{EVLOG_ALERT}iCloud3 Alert > iCloud account authorization is "
                        f"required. Tracking will be paused until the 6-digit Apple "
                        f"ID Verification code has been entered.")
        post_event(alert_msg)

        icloud_2fa_initiate_reauth_config_flow()

        return True

        # if Gb.verification_code is None:
        #     icloud_2fa1_show_verification_code_entry_form()
        #     return True  #Verification needed

        # Gb.authenticated_time = time.time()

        # return False         #Verification succeeded

    # except PyiCloudException as error:
    #     event_msg =(f"iCloud3 Error > Setting up 2fa > {error}")
    #     post_error_msg(event_msg)
    #     return True         #Verification needed, Verification Failed

    except Exception as err:
        internal_error_msg2('Authenticate iCloud', traceback.format_exc)
        return True

#--------------------------------------------------------------------
def pyicloud_reset_session():
    '''
    Reset the urrent session and authenticate to restart pyicloud_ic3
    and enter a new verification code
    '''
    if Gb.PyiCloud is None:
        return

    try:
        post_event(f"^^^iCloud interface initialization started")
        cookies_file     = (f"{Gb.icloud_cookies_dir}/{Gb.icloud_cookies_file}")
        session_file     = (f"{Gb.icloud_cookies_dir}/{Gb.icloud_cookies_file}")

        _cookies_file_rename("", "cookies")
        _cookies_file_rename("/session", "session")

        session_dir_suffix = ''
        post_event(f"iCloud initializing interface")
        Gb.PyiCloud.__init__(Gb.username, Gb.password,
                        cookie_directory=Gb.icloud_cookies_dir,
                        session_directory=(f"{Gb.icloud_cookies_dir}/session{session_dir_suffix}"),
                        with_family=True)

        Gb.PyiCloud = None
        Gb.verification_code = None

        pyicloud_authenticate_account(initial_setup=True)

        post_event(f"^^^iCloud interface initialization completed")

        Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _cookies_file_rename(dir_sub_path, file_desc, save_extn='sv'):
    try:
        file_msg = ""
        file_name = (f"{Gb.icloud_cookies_dir}{dir_sub_path}/{Gb.icloud_cookies_file}")
        file_name_sv = (f"{file_name}.{save_extn}")
        if os.path.isfile(file_name_sv):
            os.remove(file_name_sv)
            file_msg += (f"{CRLF_DOT}Deleted backup {file_desc} file ({Gb.icloud_cookies_file}.{save_extn})")
        if os.path.isfile(file_name):
            os.rename(file_name, file_name_sv)
            file_msg += (f"{CRLF_DOT}Renamed current {file_desc} file ({Gb.icloud_cookies_file}"
                        f" -- > {Gb.icloud_cookies_file}.{save_extn})")
        if file_msg != "":
            event_msg =(f"Reset iCloud {file_desc} file > CRLF•{file_name}{file_msg}")
            post_event(event_msg)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
# def pyicloud_check_ic3_update_2sa_to_2fa():
#     '''
#     When upgrading from v2.2.1 (2sa) to v2.2.2 (2fa), the cookies file must be deleted
#     so the trust cookie for 2sa is reset. If this is not done, the 2fa code is not requested
#     and it constantly asks for a notification code.

#     This routine checks to see if '\session\cookiesfilename(icloudacct@email.com)' exists. If not, it is an upgrade
#     and the cookie file is deleted.
#         - rename cookiesfile to cookiesfile.2sa
#         - rename sessionfile to sessionfile.2sa
#     '''
#     try:
#         # Gb.icloud_cookies_dir  = Gb.hass.config.path(STORAGE_DIR, STORAGE_KEY_ICLOUD)
#         Gb.icloud_cookies_dir = Gb.ha_storage_icloud3
#         Gb.icloud_cookies_dir = Gb.icloud_cookies_dir.replace('icloud3', 'icloud')
#         Gb.icloud_cookies_file = "".join([c for c in Gb.username if match(r"\w", c)])
#         cookies_file     = (f"{Gb.icloud_cookies_dir}/{Gb.icloud_cookies_file}")
#         session_file     = (f"{Gb.icloud_cookies_dir}/{Gb.icloud_cookies_file}")

#         if os.path.isfile(session_file):
#             return
#         elif os.path.isfile(cookies_file):
#             event_msg =("iCloud3 Upgrade Notification > Deleted the iCloud cookies file "
#                         "with 2sa data to prepare for Apple native 2fa support")

#             file_msg = ""
#             cookies_file_2sa = (f"{Gb.icloud_cookies_dir}/{Gb.icloud_cookies_file}.2sa")

#             if os.path.isfile(cookies_file_2sa):
#                 os.remove(cookies_file)
#                 file_msg += (f"{CRLF_DOT}Deleted cookies file ({cookies_file})")
#             elif os.path.isfile(cookies_file):
#                 os.rename(cookies_file, cookies_file_2sa)
#                 file_msg += (f"{CRLF_DOT}Renamed current cookies file ({cookies_file}"
#                             f" --> {cookies_file_2sa})")
#             post_event(event_msg + file_msg)

#     except Exception as err:
#         log_exception(err)

#########################################################
#
#   These functions handle notification and entry of the
#   iCloud Account trusted device verification code.
#
#########################################################


# def icloud_2fa1_show_verification_code_entry_form(invalid_code_msg=""):
#     """Return the verification code."""

#     for Device in Gb.Devices:
#         Device.pause_tracking
#     # svc_handler.update_service_handler(action='pause')

#     configurator = Gb.hass.components.configurator
#     if Gb.username in Gb.hass_configurator_request_id:
#         request_id   = Gb.hass_configurator_request_id.pop(Gb.username)
#         configurator = Gb.hass.components.configurator
#         configurator.request_done(request_id)

#     Gb.hass_configurator_request_id[Gb.username] = configurator.request_config(
#             ("Apple ID Verification Code"),
#             _icloud_2fa2_handle_verification_code_entry,
#             description    = (f"{invalid_code_msg}Enter the Apple ID Verification Code sent to the Trusted Device"),
#             entity_picture = "/static/images/config_icloud.png",
#             submit_caption = 'Confirm',
#             fields         = [{'id': 'code', CONF_NAME: 'Verification Code'}]
#     )

# #--------------------------------------------------------------------
# def _icloud_2fa2_handle_verification_code_entry(callback_data):
#     """Handle the chosen trusted device."""

#     invalid_code_text = ''
#     if _icloud_valid_api() is False:
#         return

#     from ..support.pyicloud_ic3 import PyiCloudException

#     Gb.verification_code = callback_data.get('code')
#     event_msg =(f"Submit Apple ID Verification Code > Code-{callback_data}")
#     post_event(event_msg)

#     try:
#         valid_code = Gb.PyiCloud.validate_2fa_code(Gb.verification_code)
#         if valid_code is False:
#             invalid_code_text = (f"The code {Gb.verification_code} in incorrect.\n\n")
#             icloud_2fa1_show_verification_code_entry_form(invalid_code_msg=invalid_code_text)
#             return

#         event_msg = "Apple/iCloud Account Verification Successful"
#         post_event(event_msg)

#     except PyiCloudException as error:
#         # Reset to the initial 2FA state to allow the user to retry
#         invalid_code_text = (f"Failed to verify account > Error-{error}")
#         post_error_msg(invalid_code_text)

#         # Trigger the code rentry step immediately
#         icloud_2fa1_show_verification_code_entry_form(invalid_code_msg=invalid_code_text)
#         return

#     if valid_code is False:
#             invalid_code_text = (f"The Verification Code {Gb.verification_code} in incorrect.\n\n")

#             icloud_2fa1_show_verification_code_entry_form(invalid_code_msg=invalid_code_text)
#             return

#     if Gb.username in Gb.hass_configurator_request_id:
#         request_id   = Gb.hass_configurator_request_id.pop(Gb.username)
#         configurator = Gb.hass.components.configurator
#         configurator.request_done(request_id)

#     event_msg =(f"{EVLOG_ALERT}iCloud Alert > iCloud Account Verification completed")
#     post_event(event_msg)

#     start_ic3.set_tracking_method(ICLOUD)
#     Gb.start_icloud3_request_flag = True

# #--------------------------------------------------------------------
# def _icloud_valid_api():
#     '''
#     Make sure the pyicloud_ic3 api is valid
#     '''

#     if Gb.PyiCloud == None:
#         event_msg =(f"{EVLOG_ERROR}iCloud3 Error > There was an error logging into the "
#                     f"Apple/iCloud Account when iCloud3 was started. Verification can not "
#                     f"be completed. Review the iCloud3 Event Log for more information.")
#         post_error_msg(event_msg)
#         return False
#     return True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Config_Flow pyicloud routines >>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def config_flow_pyicloud_authenticate_account(initial_setup=False):
    '''
    Authenticate the iCloud Acount via pyicloud
    If successful - Gb.PyiCloud to the api of the pyicloudservice for the username
    If not        - set Gb.PyiCloud = None
    '''
    try:
        # If not using the iCloud location svcs, nothing to do
        if (Gb.conf_tracking[CONF_TRACKING_METHOD] == OPT_TRACKING_METHOD[OPT_TM_IOSAPP_ONLY]) is False:
            return
        elif Gb.username == '' or Gb.password == '':
            return

        Gb.icloud_cookies_dir  = Gb.ha_storage_icloud3
        Gb.icloud_cookies_file = "".join([c for c in Gb.username if match(r"\w", c)])
        _traceha(f"52 {Gb.ha_storage_icloud3=} {Gb.icloud_cookies_dir=} {Gb.icloud_cookies_file=} ")
        if not os.path.exists(Gb.icloud_cookies_dir):
            os.makedirs(Gb.icloud_cookies_dir)

        cookie_directory  = Gb.icloud_cookies_dir
        session_directory = f"{Gb.icloud_cookies_dir}/session"

        Gb.PyiCloud = await Gb.hass.async_add_executor_job(
                                PyiCloudService,
                                Gb.username,
                                Gb.password,
                                cookie_directory,
                                session_directory,
                                True)

        if Gb.PyiCloud.api.requires_2fa:
            return 'verification_code_needed'

            # if Gb.PyiCloud:
            #     Gb.PyiCloud_FamilySharing = Gb.PyiCloud.family_sharing_object
            #     Gb.PyiCloud_FindMyFriends = Gb.PyiCloud.find_my_friends_object
            #     _is_authentication_2fa_code_needed(initial_setup=True)

        return 'success'

    except (PyiCloudFailedLoginException, PyiCloudNoDevicesException,
            PyiCloudAPIResponseException) as err:

            log_error_msg(f"ERROR: Failed to connect to the iCloud service: {err}")
            Gb.api = None
            return 'invalid_auth'

    except (PyiCloudServiceNotActivatedException, PyiCloudNoDevicesException):
            log_error_msg(f"ERROR: No devices were found in the iCloud account: {Gb._username}")
            Gb.api = None
            return 'no_devices'

    except (PyiCloud2SARequiredException) as err:
        log_exception(err)
        return 'verification_code_needed'

    except Exception as err:
        log_exception(err)
        return f"error-{err}"

    return 'success'

#--------------------------------------------------------------------
def icloud_2fa_initiate_reauth_config_flow():
    '''
    Pause all tracking and request the Verification Code entry form on the
    HA Configuration > Integrations screen.
    '''
    for Device in Gb.Devices:
        Device.pause_tracking

    Gb.hass.add_job(
            Gb.hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={'source': 'reauth'},
                    data={
                        'icloud3_service_call': True,
                        'step_id': 'reauth',
                        "unique_id": DOMAIN,
                    },
                )
            )
