


from ..globals          import GlobalVariables as Gb
from ..const_general    import (NOT_SET, HOME, HIGH_INTEGER, EVLOG_ALERT, EVLOG_ERROR, CRLF_DOT,
                                ICLOUD, IOSAPP,
                                STORAGE_DIR, STORAGE_KEY_ICLOUD)
from ..const_attrs      import (LATITUDE, AUTHENTICATED, CONF_NAME, )

from ..support           import start_ic3 as start_ic3

from ..helpers.base     import (instr, is_statzone,
                                post_event, post_error_msg, post_log_info_msg, post_startup_event, post_monitor_msg,
                                log_exception, internal_error_msg2, _trace, _traceha, )
from ..helpers.time     import (time_now_secs, secs_to_time, secs_to_datetime, )
from ..helpers.format   import (format_gps, format_time_age, format_age, )
from ..helpers.entity_io import (get_state, get_attributes, get_last_changed_time, extract_attr_value, )

from ..support.pyicloud_ic3  import PyiCloudService
from ..support.pyicloud_ic3  import (
            PyiCloudFailedLoginException,
            PyiCloudNoDevicesException,
            PyiCloudAPIResponseException,
            PyiCloud2SARequiredException,
            )


import os
import time
import traceback
from re import match

#########################################################
#
#   Check the icloud Device to see if it qualified to be updated
#   on this polling cycle
#
#########################################################
def check_device_update_qualification(Device):
    Device.icloud_update_reason = ''
    Device.icloud_no_update_reason = ''

    if Device.is_inzone and Device.next_update_time_reached is False:
        Device.icloud_no_update_reason = 'inZone & Next Update Time not Reached'
    elif Device.is_tracking_resumed:
        Device.icloud_update_reason = 'Resuming via iCloud'
    elif Device.is_tracking_paused:
        Device.icloud_no_update_reason = 'Paused'
    elif Gb.any_device_being_updated_flag:
        Device.icloud_no_update_reason = 'Another Device being updated'
    elif Device.verified_flag is False:
        Device.icloud_no_update_reason = 'Not Verified'
    elif Gb.tracking_method_IOSAPP:
        Device.icloud_no_update_reason = 'Global iOS App Tracking Method'
    elif Device.tracking_method_IOSAPP:
        Device.icloud_no_update_reason = 'Device iOS App Tracking Method'
    elif (Gb.start_icloud3_inprocess_flag and Device.icloud_initial_locate_done is False):
        Device.icloud_no_update_reason = 'Start inProcess & initial locate not done'
    elif (Device.icloud_initial_locate_done is False
            and (Device.old_loc_poor_gps_cnt > 35
                or Device.count_discarded_update > 125)):
        Device.icloud_no_update_reason = 'Initial locate not done & poor cnt > 35'
    elif Device.icloud_initial_locate_done is False:
        pass
    elif (Device.attrs_zone == NOT_SET
            and Device.DeviceFmZoneHome.next_update_secs > Gb.this_update_secs):
        Device.icloud_no_update_reason = 'Zone NotSet Next Update Time not Reached'

    Device.icloud_update_flag = (Device.icloud_no_update_reason == '')

#########################################################
#
#   Check the icloud device_tracker entity and last_update_trigger entity to
#   see if anything has changed and the icloud3 device_tracker entity should be
#   updated with the new location information.
#
#########################################################
def check_icloud_loc_data_change_needed(Device):
    try:
        devicename = Device.devicename
        Device.icloud_update_reason = ''
        Device.icloud_no_update_reason = ''
        Device.icloud_update_flag   = False

        if (Device.attrs_zone == NOT_SET
                or Device.attrs[LATITUDE] == 0
                or Device.loc_data_latitude == 0
                or Device.icloud_initial_locate_done is False):
            Device.icloud_update_reason = "Initial iCloud Locate"

        elif (Device.is_tracking_resumed):
            Device.icloud_update_reason = "Resuming via iCloud"

        elif Device.icloud_update_retry_flag:
            Device.icloud_update_reason  = "Retrying Location Refresh"

        elif (is_statzone(Device.loc_data_zone)
                and Device.loc_data_latitude  == Device.StatZone.base_latitude
                and Device.loc_data_longitude == Device.StatZone.base_longitude):
            Device.icloud_no_update_reason = "Stat Zone Base Location"

        # Data change older than the current data
        elif Device.loc_data_secs < Device.attrs_located_secs:
            Device.icloud_update_reason = (f"Old Location Data-{Device.loc_data_time}")

        elif (Device.StatZone.timer_expired
                and Device.old_loc_poor_gps_cnt == 0):
            Device.icloud_update_reason = "Statationary Timer Reached"

            # event_msg =(f"Move into Stationary Zone Timer reached > "
            #             f"Expired-{secs_to_time(Device.StatZone.timer)}")
            # post_event(devicename, event_msg)

        elif Device.next_update_time_reached:
            Device.icloud_update_reason = (f"Next Update Time reached > "
                            f"{Device.next_update_DeviceFmZone.next_update_time}")
            if Device.next_update_DeviceFmZone.zone != HOME:
                Device.icloud_update_reason += (f" ({Device.next_update_DeviceFmZone.zone})")

        elif (Device.is_inzone is False
                and Device.loc_data_secs > Device.attrs_located_secs + Device.old_loc_threshold_secs):
            Device.icloud_update_reason = "Newer Data is Available"

        Device.icloud_update_flag = (Device.icloud_update_reason != '')

    except Exception as err:
        log_exception(err)
        Device.icloud_update_flag = False


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

    #Set up pyicloud cookies directory & file names
    try:
        Gb.icloud_cookies_dir  = Gb.hass.config.path(STORAGE_DIR, STORAGE_KEY_ICLOUD)
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

    from ..support.pyicloud_ic3 import PyiCloudException

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

        alert_msg = (f"{EVLOG_ALERT}iCloud3 Alert > 2fa Verification Required")
        post_event(alert_msg)

        if Gb.verification_code is None:
            icloud_2fa1_show_verification_code_entry_form()
            return True  #Verification needed

        Gb.authenticated_time = time.time()

        return False         #Verification succeeded

    except PyiCloudException as error:
        event_msg =(f"iCloud3 Error > Setting up 2fa > {error}")
        post_error_msg(event_msg)
        return True         #Verification needed, Verification Failed

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
def check_ic3_update_2sa_to_2fa():
    '''
    When upgrading from v2.2.1 (2sa) to v2.2.2 (2fa), the cookies file must be deleted
    so the trust cookie for 2sa is reset. If this is not done, the 2fa code is not requested
    and it constantly asks for a notification code.

    This routine checks to see if '\session\cookiesfilename(icloudacct@email.com)' exists. If not, it is an upgrade
    and the cookie file is deleted.
        - rename cookiesfile to cookiesfile.2sa
        - rename sessionfile to sessionfile.2sa
    '''
    try:
        Gb.icloud_cookies_dir  = Gb.hass.config.path(STORAGE_DIR, STORAGE_KEY_ICLOUD)
        Gb.icloud_cookies_file = "".join([c for c in Gb.username if match(r"\w", c)])
        cookies_file     = (f"{Gb.icloud_cookies_dir}/{Gb.icloud_cookies_file}")
        session_file     = (f"{Gb.icloud_cookies_dir}/{Gb.icloud_cookies_file}")

        if os.path.isfile(session_file):
            return
        elif os.path.isfile(cookies_file):
            event_msg =("iCloud3 Upgrade Notification > Deleted the iCloud cookies file "
                        "with 2sa data to prepare for Apple native 2fa support")

            file_msg = ""
            cookies_file_2sa = (f"{Gb.icloud_cookies_dir}/{Gb.icloud_cookies_file}.2sa")

            if os.path.isfile(cookies_file_2sa):
                os.remove(cookies_file)
                file_msg += (f"{CRLF_DOT}Deleted cookies file ({cookies_file})")
            elif os.path.isfile(cookies_file):
                os.rename(cookies_file, cookies_file_2sa)
                file_msg += (f"{CRLF_DOT}Renamed current cookies file ({cookies_file}"
                            f" --> {cookies_file_2sa})")
            post_event(event_msg + file_msg)

    except Exception as err:
        log_exception(err)

#########################################################
#
#   These functions handle notification and entry of the
#   iCloud Account trusted device verification code.
#
#########################################################
def icloud_2fa1_show_verification_code_entry_form(invalid_code_msg=""):
    """Return the verification code."""

    for Device in Gb.Devices:
        Device.pause_tracking
    # svc_handler.update_service_handler(action='pause')

    configurator = Gb.hass.components.configurator
    if Gb.username in Gb.hass_configurator_request_id:
        request_id   = Gb.hass_configurator_request_id.pop(Gb.username)
        configurator = Gb.hass.components.configurator
        configurator.request_done(request_id)

    Gb.hass_configurator_request_id[Gb.username] = configurator.request_config(
            ("Apple ID Verification Code"),
            _icloud_2fa2_handle_verification_code_entry,
            description    = (f"{invalid_code_msg}Enter the Apple ID Verification Code sent to the Trusted Device"),
            entity_picture = "/static/images/config_icloud.png",
            submit_caption = 'Confirm',
            fields         = [{'id': 'code', CONF_NAME: 'Verification Code'}]
    )

#--------------------------------------------------------------------
def _icloud_2fa2_handle_verification_code_entry(callback_data):
    """Handle the chosen trusted device."""


    if _icloud_valid_api() is False:
        return

    from ..support.pyicloud_ic3 import PyiCloudException

    Gb.verification_code = callback_data.get('code')
    event_msg =(f"Submit Apple ID Verification Code > Code-{callback_data}")
    post_event(event_msg)

    try:
        valid_code = Gb.PyiCloud.validate_2fa_code(Gb.verification_code)
        if valid_code is False:
            invalid_code_text = (f"The code {Gb.verification_code} in incorrect.\n\n")
            icloud_2fa1_show_verification_code_entry_form(invalid_code_msg=invalid_code_text)
            return

        event_msg = "Apple/iCloud Account Verification Successful"
        post_event(event_msg)

    except PyiCloudException as error:
        # Reset to the initial 2FA state to allow the user to retry
        invalid_code_text = (f"Failed to verify account > Error-{error}")
        post_error_msg(invalid_code_text)

        # Trigger the code rentry step immediately
        icloud_2fa1_show_verification_code_entry_form(invalid_code_msg=invalid_code_text)
        return

    if valid_code is False:
            invalid_code_text = (f"The Verification Code {Gb.verification_code} in incorrect.\n\n")

            icloud_2fa1_show_verification_code_entry_form(invalid_code_msg=invalid_code_text)
            return

    if Gb.username in Gb.hass_configurator_request_id:
        request_id   = Gb.hass_configurator_request_id.pop(Gb.username)
        configurator = Gb.hass.components.configurator
        configurator.request_done(request_id)

    event_msg =(f"{EVLOG_ALERT}iCloud Alert > iCloud Account Verification completed")
    post_event(event_msg)

    start_ic3.set_tracking_method(ICLOUD)
    Gb.start_icloud3_request_flag = True

#--------------------------------------------------------------------
def _icloud_valid_api():
    '''
    Make sure the pyicloud_ic3 api is valid
    '''

    if Gb.PyiCloud == None:
        event_msg =(f"{EVLOG_ERROR}iCloud3 Error > There was an error logging into the "
                    f"Apple/iCloud Account when iCloud3 was started. Verification can not "
                    f"be completed. Review the iCloud3 Event Log for more information.")
        post_error_msg(event_msg)
        return False
    return True
