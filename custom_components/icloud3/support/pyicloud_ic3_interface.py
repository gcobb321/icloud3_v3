
from ..global_variables     import GlobalVariables as Gb
from ..const                import (HIGH_INTEGER,
                                    EVLOG_ALERT, EVLOG_IC3_STARTING,
                                    CRLF, CRLF_DOT, DASH_20,
                                    ICLOUD,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    )

from ..support              import start_ic3 as start_ic3
from ..support.pyicloud_ic3 import (PyiCloudService, PyiCloudFailedLoginException, PyiCloudNoDevicesException,
                                    PyiCloudAPIResponseException, PyiCloud2FARequiredException,)

from ..helpers.common       import (instr, is_statzone, )
from ..helpers.messaging    import (post_event, post_error_msg, post_monitor_msg,
                                    log_info_msg, log_exception, log_error_msg, internal_error_msg2, _trace, _traceha, )
from ..helpers.time_util    import (time_now_secs, secs_to_time, secs_to_datetime, secs_to_time_str, format_age,
                                    secs_to_time_age_str, )

import os
import time
import traceback
from re import match
from homeassistant.util    import slugify


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   PYICLOUD-IC3 INTERFACE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_PyiCloudService_executor_job():
    '''
    This is the entry point for the hass.async_add_executor_job statement from __init__
    '''
    create_PyiCloudService(Gb.PyiCloudInit, called_from='init')

#--------------------------------------------------------------------
def create_PyiCloudService(PyiCloud, called_from='unknown'):
    #See if pyicloud_ic3 is available

    Gb.pyicloud_authentication_cnt  = 0
    Gb.pyicloud_location_update_cnt = 0
    Gb.pyicloud_calls_time          = 0.0

    if Gb.username == '' or Gb.password == '':
        event_msg =(f"iCloud3 Alert > The iCloud username or password has not been set up. "
                    f"iCloud location tracking is not available.")
        post_event(event_msg)
        return

    authenticate_icloud_account(PyiCloud, called_from=called_from, initial_setup=True)

    if Gb.PyiCloud or Gb.PyiCloudInit:
        event_msg =(f"iCloud Location Services interface > Verified ({called_from})")
        post_event(event_msg)

    else:
        event_msg =(f"iCloud3 Error > Apple ID Verification is needed or "
                    f"another error occurred. The iOSApp tracking method will be "
                    f"used until the Apple ID Verification code has been entered. See the "
                    f"HA Notification area to continue. iCloud3 will then restart.")
        post_error_msg(event_msg)

#--------------------------------------------------------------------
def verify_pyicloud_setup_status():
    '''
    The PyiCloud Servicesinterface set up was started in __init__
    via create_PyiCloudService_executor_job above. The following steps are done to set up
    PyiCloudService:
        1. Initialize the variables and authenticate the account.
        2. Create the FamShr object and get the FamShr devices.
        3. Create the FmF object and get the FamShr devices.

    This function is called from Stage 4 to determine the set up status.
        1. If the set up started in __init__ is comlete, return the PyiCloudInit object
        2. If FamShr has not been completed, rerequest setting up the FamShr object.
        3. If FmF has not been completed, rerequest setting up the FmF object.
        4. Return the PyiCloudInit object after #2 and #3 above.
        5. If the the authenticate step from the original set up request is not done,
        start all over. The original request will eventually be comleted but it will
        not be used. This will prevent HA from issuing Blocking call errors indicating
        the PyiCloud session data requests must be run in the event loop.

    '''

    if Gb.PyiCloud:
        return

    # Gb.PyiCloudInit.init_stage['complete'] = False
    # Gb.PyiCloudInit.init_stage['authenticate'] = False
    # Gb.PyiCloudInit.init_stage['setup_famshr'] = False
    # Gb.PyiCloudInit.init_stage['setup_fmf'] = False

    # PyiCloud is started early in __init__ and set up is complete
    if (Gb.PyiCloudInit and Gb.PyiCloudInit.init_stage.get('complete', False)):
        Gb.PyiCloud = Gb.PyiCloudInit
        post_event('iCloud Location Services Interface > Started during iCloud3 '
                    'initialization completed successfully')

    # Autenticate is completed, continue with setup of FamShr and FmF objects
    elif (Gb.PyiCloudInit and Gb.PyiCloudInit.init_stage.get('authenticate', False)):
        Gb.PyiCloud = Gb.PyiCloudInit
        Gb.PyiCloud.__init__(Gb.username, Gb.password,
                                    cookie_directory=Gb.icloud_cookies_dir,
                                    session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                    called_from='start_ic3')

        post_event('iCloud Location Services Interface > Started during iCloud3 '
                    'initialization completed successfully')

    else:
        # __init__ set up was not authenticated, start all over
        create_PyiCloudService(Gb.PyiCloud, called_from='start_ic3')

#--------------------------------------------------------------------
def authenticate_icloud_account(PyiCloud, called_from='unknown', initial_setup=False):
    '''
    Authenticate the iCloud Account via pyicloud

    Arguments:
        PyiCloud - Gb.PyiCloud or Gb.PyiCloudInit object depending on called_from module
        called_from - Called from module (init or start_ic3)

    If successful - Gb.PyiCloud or Gb.PyiCloudInit = PyiCloudService object
    If not        - Gb.PyiCloud or Gb.PyiCloudInit = None
    '''

    # If not using the iCloud location svcs, nothing to do
    if (Gb.data_source_use_icloud is False
            or Gb.username == ''
            or Gb.password == ''):
        return

    try:
        Gb.pyicloud_auth_started_secs = time.time()
        if PyiCloud and PyiCloud.init_stage['complete']:
            PyiCloud.authenticate(refresh_session=True, service='find')

        elif PyiCloud:
            PyiCloud.__init__(Gb.username, Gb.password,
                                    cookie_directory=Gb.icloud_cookies_dir,
                                    session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                    called_from=called_from)

        else:
            log_info_msg(f"Connecting to and Authenticating iCloud Location Services Interface ({called_from})")
            PyiCloud = PyiCloudService(Gb.username, Gb.password,
                                    cookie_directory=Gb.icloud_cookies_dir,
                                    session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                    called_from=called_from)

        authentication_took_secs = time.time() - Gb.pyicloud_auth_started_secs
        Gb.pyicloud_calls_time += authentication_took_secs
        if Gb.authentication_error_retry_secs != HIGH_INTEGER:
            Gb.authenticated_time = 0
            Gb.authentication_error_retry_secs = HIGH_INTEGER
            start_ic3.set_tracking_method(ICLOUD)

        is_authentication_2fa_code_needed(PyiCloud, initial_setup=True)
        reset_authentication_time(PyiCloud, authentication_took_secs)

    except (PyiCloudAPIResponseException, PyiCloudFailedLoginException,
                PyiCloudNoDevicesException) as err:
        event_msg =(f"iCloud3 Error > An error occurred communicating with "
                    f"iCloud Account servers. This can be caused by:"
                    f"{CRLF_DOT}Your network or wifi is down, or"
                    f"{CRLF_DOT}Apple iCloud servers are down"
                    f"{CRLF}Error-{err}")
        post_error_msg(event_msg)
        check_all_devices_online_status()
        return False

    except (PyiCloud2FARequiredException) as err:
        is_authentication_2fa_code_needed(PyiCloud, initial_setup=True)
        return False

    except Exception as err:
        log_exception(err)
        return False

    return True

#--------------------------------------------------------------------
def reset_authentication_time(PyiCloud, authentication_took_secs):
    '''
    If an authentication was done, update the count & time and display
    an Event Log message
    '''
    authentication_method = PyiCloud.authentication_method
    if authentication_method == '':
        return

    Gb.pyicloud_auth_started_secs = 0
    Gb.pyicloud_authentication_cnt += 1
    last_authenticated_time = Gb.authenticated_time
    Gb.authenticated_time   = time_now_secs()

    event_msg =(f"iCloud Account Authenticated "
                f"(#{Gb.pyicloud_authentication_cnt}) > LastAuth-")
    if last_authenticated_time == 0:
        event_msg += "Never (Initializing)"
    else:
        event_msg += (f"{secs_to_time(last_authenticated_time)} "
                    f" ({format_age(time_now_secs() - last_authenticated_time)})")
    event_msg += (f", Method-{authentication_method}, "
                    f"Took-{secs_to_time_str(authentication_took_secs)}")
    post_event(event_msg)

#--------------------------------------------------------------------
def is_authentication_2fa_code_needed(PyiCloud, initial_setup=False):
    '''
    A wrapper for seeing if an authentication is needed and setting up the config_flow
    reauth request
    '''
    if PyiCloud is None:
        return False
    elif PyiCloud.requires_2fa:
        pass
    elif Gb.tracking_method_IOSAPP is False:
        return False
    elif initial_setup:
        pass
    elif Gb.start_icloud3_inprocess_flag:
        return False

    if new_2fa_authentication_code_requested(PyiCloud, initial_setup):
        if PyiCloud.new_2fa_code_already_requested_flag is False:
            Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)
            PyiCloud.new_2fa_code_already_requested_flag = True

#--------------------------------------------------------------------
def check_all_devices_online_status():
    '''
    See if all the devices are 'pending'. If so, the devices are probably in airplane mode.
    Set the time and display a message
    '''
    any_device_online_flag = False
    for Device in Gb.Devices_by_devicename_tracked.values():
        if Device.is_online:
            Device.offline_secs = 0
            Device.pending_secs = 0
            any_device_online_flag = True

        elif Device.is_offline:
            if Device.offline_secs == 0:
                Device.offline_secs = Gb.this_update_secs
            event_msg = (   f"Device Offline and not available > "
                            f"OfflineSince-{secs_to_time_age_str(Device.offlineg_secs)}")
            post_event(Device.devicename, event_msg)

        elif Device.is_pending:
            if Device.pending_secs == 0:
                Device.pending_secs = Gb.this_update_secs
            event_msg = (   f"Device status is Pending/Unknown > "
                            f"PendingSince-{secs_to_time_age_str(Device.pending_secs)}")
            post_event(Device.devicename, event_msg)

    if any_device_online_flag == False:
        event_msg = (   f"All Devices are offline or have a pending status. "
                        f"They may be in AirPlane Mode and not available")
        post_event(event_msg)

#--------------------------------------------------------------------
def new_2fa_authentication_code_requested(PyiCloud, initial_setup=False):
    '''
    Make sure iCloud is still available and doesn't need to be authenticationd
    in 15-second polling loop

    Returns True  if Authentication is needed.
    Returns False if Authentication succeeded
    '''

    try:
        if initial_setup is False:
            if PyiCloud is None:
                event_msg =("iCloud/FmF API Error, No device API information "
                                "for devices. Resetting iCloud")
                post_error_msg(event_msg)
                Gb.start_icloud3_request_flag = True

            elif Gb.start_icloud3_request_flag:         # via service call
                event_msg =("iCloud Restarting, Reset command issued")
                post_error_msg(event_msg)
                Gb.start_icloud3_request_flag = True

            if PyiCloud is None:
                event_msg =("iCloud Authentication Required, will retry")
                post_error_msg(event_msg)
                return True         # Authentication needed

        if PyiCloud is None:
            return True

        #See if 2fa Verification needed
        if PyiCloud.requires_2fa is False:
            return False

        alert_msg = (f"{EVLOG_ALERT}Alert > Apple ID Verification is needed. "
                        f"FamShr and FmF tracking may be paused until the 6-digit Apple "
                        f"ID Verification code has been entered. Do the following:{CRLF}"
                        f"{CRLF}1. Select `Notifications Bell` in the HA Sidebar"
                        f"{CRLF}2. Select `Integration Requires Reconfiguration > Check it out`"
                        f"{CRLF}3. Select Red `Attention Required > iCloud3 > Reconfigure`"
                        f"{CRLF}4. Enter the 6-digit code. Select `Submit`")
        post_event(alert_msg)

        return True

    except Exception as err:
        internal_error_msg2('Apple ID Verification', traceback.format_exc)
        return True

#--------------------------------------------------------------------
def pyicloud_reset_session():
    '''
    Reset the current session and authenticate to restart pyicloud_ic3
    and enter a new verification code
    '''
    if Gb.PyiCloud is None:
        return

    try:
        post_event(f"{EVLOG_IC3_STARTING}Apple ID Verification - Started")

        _cookies_file_rename('cookies', Gb.PyiCloud.cookie_directory_filename)
        _cookies_file_rename('session', Gb.PyiCloud.session_directory_filename)

        post_event(f"iCloud initializing interface")
        Gb.PyiCloud.__init__(Gb.username, Gb.password,
                        cookie_directory=Gb.icloud_cookies_dir,
                        session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                        with_family=True,
                        called_from='reset')

        Gb.PyiCloud = None
        Gb.verification_code = None

        authenticate_icloud_account(Gb.PyiCloud, initial_setup=True)

        post_event(f"{EVLOG_IC3_STARTING}Apple ID Verification - Completed")

        Gb.EvLog.update_event_log_display(Gb.EvLog.devicename)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def create_PyiCloudService_secondary(username, password, called_from):
    '''
    Create the PyiCloudService object without going through the error checking and
    authentication test routines. This is used by config_flow to open a second
    PyiCloud session
    '''
    return PyiCloudService(username, password,
                            cookie_directory=Gb.icloud_cookies_dir,
                            session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                            called_from=called_from)


#--------------------------------------------------------------------
def _cookies_file_rename(file_desc, directory_filename, save_extn='sv'):
    try:
        file_msg = ""
        directory_filename_sv = (f"{directory_filename}.{save_extn}")
        filename    = directory_filename.replace(Gb.PyiCloud.cookie_directory, '')
        filename_sv = directory_filename_sv.replace(Gb.PyiCloud.cookie_directory, '')

        if os.path.isfile(directory_filename_sv):
            os.remove(directory_filename_sv)
            file_msg += (f"{CRLF_DOT}Delete backup file (...{filename_sv})")

        if os.path.isfile(directory_filename):
            os.rename(directory_filename, directory_filename_sv)
            file_msg += (f"{CRLF_DOT}Rename current file to ...{filename}.{save_extn})")

        if file_msg != "":
            event_msg =(f"Current iCloud {file_desc} file > "
                        f"{CRLF}•{directory_filename}{file_msg}")
            post_event(event_msg)

    except Exception as err:
        log_exception(err)
