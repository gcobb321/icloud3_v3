from ..global_variables import GlobalVariables as Gb
from ..const            import (VERSION, VERSION_BETA, ICLOUD3, ICLOUD3_VERSION, DOMAIN, ICLOUD3_VERSION_MSG,
                                NOT_SET, IC3LOG_FILENAME,
                                CRLF, CRLF_DOT, CRLF_HDOT, CRLF_LDOT, CRLF_X, CRLF_RED_ALERT,
                                NL, NL_DOT, LINK, YELLOW_ALERT, RED_ALERT,
                                EVLOG_ALERT, EVLOG_ERROR, EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR, NBSP6, DOT,
                                ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                CONF_VERSION, ICLOUD, ZONE_DISTANCE,
                                CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL, CONF_SERVER_LOCATION,
                                ICLOUD, MOBAPP, DISTANCE_TO_DEVICES,
                                )

from ..utils.utils      import (instr, is_empty, isnot_empty, list_to_str, list_add, list_del,
                                username_id, )
from ..utils.messaging  import (broadcast_info_msg,
                                post_event, post_error_msg, log_error_msg, post_alert,
                                post_monitor_msg, post_internal_error, post_evlog_greenbar_msg,
                                write_ic3log_recd,
                                log_debug_msg, log_warning_msg, log_info_msg, log_exception, log_data,
                                _evlog, _log, more_info, format_filename,
                                write_config_file_to_ic3log,
                                open_ic3log_file, )
from ..utils.time_util  import (time_now, time_now_secs, secs_to_time, format_day_date_now, )

from ..apple_acct       import pyicloud_ic3_interface
from ..mobile_app       import mobapp_interface
from ..startup          import hacs_ic3
from ..startup          import start_ic3
from ..startup          import config_file
from ..tracking         import determine_interval as det_interval

#--------------------------------------------------------------------
import homeassistant.util.dt as dt_util


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_1_setup_variables():


    Gb.trace_prefix = 'STAGE1'
    stage_title = f'Stage 1 > Initial Preparations'

    open_ic3log_file()

    # if Gb.prestartup_log:
    #     _prestartup_log = Gb.prestartup_log
    #     Gb.prestartup_log = ''
    #     write_ic3log_recd(f"$$$$$\n#####\n{_prestartup_log}")

    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    broadcast_info_msg(stage_title)

    Gb.EvLog.display_user_message(f'iCloud3 v{Gb.version} > Initializiing')

    try:
        Gb.EvLog.alert_message          = ''
        Gb.config_track_devices_change_flag = False
        Gb.reinitialize_icloud_devices_flag = False     # Set when no devices are tracked and iC3 needs to automatically restart
        Gb.reinitialize_icloud_devices_cnt  = 0

        config_file.load_icloud3_configuration_file()
        write_config_file_to_ic3log()
        start_ic3.initialize_global_variables()
        start_ic3.set_global_variables_from_conf_parameters()

        # Run these setup items on a restart. Do not then when initially starting iC3
        if Gb.initial_icloud3_loading_flag is False:
            Gb.EvLog.startup_event_recds = []
            Gb.EvLog.startup_event_save_recd_flag = True
            post_event( f"{EVLOG_IC3_STARTING}Restarting > {ICLOUD3_VERSION_MSG}, "
                        f"{dt_util.now().strftime('%A, %b %d')}")

            if (Gb.use_data_source_ICLOUD):
                # Can not run this as an executor job to avoid 'no running event loop' error
                # Gb.hass.async_add_executor_job(
                #        pyicloud_ic3_interface.log_into_apple_acct_restart_icloud3)
                pyicloud_ic3_interface.log_into_apple_acct_restart_icloud3()


        if Gb.ha_config_directory != '/config':
            post_event(f"Base Config Directory > {CRLF_DOT}{Gb.ha_config_directory}")
        post_event(f"iCloud3 Directory > {CRLF_DOT}{Gb.icloud3_directory}")
        post_event(f"iCloud3 Configuration File >{CRLF_DOT}{format_filename(Gb.icloud3_config_filename)}")

        start_ic3.display_platform_operating_mode_msg()
        # start_ic3.update_lovelace_resource_event_log_js_entry()
        # hacs_ic3.check_hacs_icloud3_update_available()
        Gb.hass.loop.create_task(start_ic3.update_lovelace_resource_event_log_js_entry())
        Gb.hass.loop.create_task(hacs_ic3.check_hacs_icloud3_update_available())
        start_ic3.check_ic3_event_log_file_version()

        post_monitor_msg(f"LocationInfo-{Gb.ha_location_info}")

        start_ic3.set_event_recds_max_cnt()
        start_ic3.define_tracking_control_fields()

        post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.update_event_log_display("")

        if Gb.InternetError.internet_error_test:
            Gb.internet_error = True

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_2_prepare_configuration():

    Gb.trace_prefix = 'STAGE2'
    stage_title = f'Stage 2 > Prepare Support Services'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        start_ic3.create_Zones_object()
        start_ic3.create_Waze_object()

        Gb.WazeHist.load_track_from_zone_table()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")

    try:
        configuration_needed_msg = ''
        # Default configuration was installed
        if Gb.conf_profile[CONF_VERSION] == -1:
            configuration_needed_msg = 'INITIAL INSTALLATION - CONFIGURATION IS REQUIRED'

        elif Gb.conf_profile[CONF_VERSION] == 0:
            configuration_needed_msg = 'INITIAL CONFIGURATION PARAMETERS WERE INSTALLED - ' \
                                        'THEY MUST BE REVIEWED BEFORE STARTING ICLOUD3'
        elif ((is_empty(Gb.conf_apple_accounts) and Gb.conf_data_source_ICLOUD)
                or is_empty(Gb.conf_devices)):
            configuration_needed_msg = 'ICLOUD3 APPLE ACCT OR DEVICES HAVE NOT BEEN SETUP '

        if configuration_needed_msg:
            post_evlog_greenbar_msg('iCloud3 Configuration not set up')
            event_msg =(f"{EVLOG_ALERT}{configuration_needed_msg}{CRLF}"
                        f"{more_info('configure_icloud3')}")
            post_event(event_msg)

            Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_3_setup_configured_devices():

    Gb.trace_prefix = 'STAGE3'
    stage_title = f'Stage 3 > Device Configuration'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        # Make sure a full restart is done if all of the devices were not found in the iCloud data
        data_sources = ''
        Gb.startup_alerts_by_source = {}

        if Gb.conf_data_source_ICLOUD: data_sources += f"{ICLOUD}, "
        if Gb.conf_data_source_MOBAPP: data_sources += f"{MOBAPP}, "
        data_sources = data_sources[:-2] if data_sources else 'NONE'
        post_event(f"Data Sources > {data_sources}")

        # Recheck paswords and validate ones that failed
        Gb.ValidateAppleAcctUPW.validate_all_apple_accts_upw()

        # # valid_upw is False if there was no internet connection
        # for username, valid_upw in Gb.username_valid_by_username.items():
        #     if valid_upw:
        #         continue

        #     error_msg = f"{EVLOG_ALERT}Apple Acct > {username_id(username)}, Login Failed, "
        #     if Gb.internet_error is False:
        #         error_msg += f"{CRLF_DOT}INVALID USERNAME/PASSWORD"
        #     else:
        #         error_msg += f"INTERNET ERROR"
        #     post_event(error_msg)
        #     post_alert(username_id(username), "Apple Acct Login Failed")

        if Gb.config_track_devices_change_flag:
            pass
        elif (Gb.conf_data_source_ICLOUD
                and Gb.icloud_device_verified_cnt < len(Gb.Devices)):
            Gb.config_track_devices_change_flag = True
        elif Gb.log_debug_flag:
            Gb.config_track_devices_change_flag = True

        start_ic3.create_Devices_object()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_4_setup_data_sources():

    Gb.trace_prefix = 'STAGE4'
    stage_title = f"Stage 4 > Connect to Apple Accounts"
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message(stage_title)
    broadcast_info_msg(stage_title)

    for Device in Gb.Devices:
        Device.set_fname_alert('')

    apple_acct_used_msg = 'Apple Account used-'
    if Gb.use_data_source_ICLOUD:
        apple_acct_used_msg += "Yes"
    else:
        apple_acct_used_msg = f"{RED_ALERT}{apple_acct_used_msg}No"
    mobapp_used_msg = 'HA Mobile App used-'
    if Gb.use_data_source_MOBAPP:
        mobapp_used_msg += "Yes"
    else:
        mobapp_used_msg = f"{RED_ALERT}{mobapp_used_msg}No"

    post_event(f"Data Source > {apple_acct_used_msg}")
    post_event(f"Data Source > {mobapp_used_msg}")

    try:
        # Get list of all unique Apple Acct usernames in config
        Gb.conf_usernames = [apple_account[CONF_USERNAME]
                                    for apple_account in Gb.conf_apple_accounts
                                    if (apple_account[CONF_USERNAME] in Gb.username_valid_by_username
                                            and apple_account[CONF_USERNAME] != '')]

        if Gb.use_data_source_ICLOUD:
            _log_into_apple_accounts(retry=True)

            start_ic3.setup_data_source_ICLOUD()

            for PyiCloud in Gb.PyiCloud_by_username.values():
                if PyiCloud.account_locked:
                    post_error_msg( f"{EVLOG_ERROR}Apple Account {PyiCloud.account_owner} "
                                    f"is Locked. Log onto www.icloud.com and unlock "
                                    f"your account to reauthorize location services.")
                    post_alert(PyiCloud.username_id, "Apple Acct is Locked")

        stage_title = f"Stage 4 > Connect to Mobile App Integration"
        log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.display_user_message(stage_title)

        mobapp_interface.get_entity_registry_mobile_app_devices()
        mobapp_interface.get_mobile_app_integration_device_info()

        if Gb.conf_data_source_MOBAPP:
            start_ic3.setup_tracked_devices_for_mobapp()

        stage_title = f"Stage 4 > Finalize Date Source Connections"
        log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.display_user_message(stage_title)

        start_ic3.set_devices_verified_status()
        all_verified_flag = _are_all_devices_verified()

        if isnot_empty(Gb.username_pyicloud_503_internet_error):
            username_base = [username_id(username)
                                        for username in Gb.username_pyicloud_503_internet_error]
            retry_at = secs_to_time(time_now_secs() + 900)
            post_event( f"{EVLOG_ALERT}Apple Acct > {list_to_str(username_base)}, Login Failed, "
                        f"{CRLF_DOT}Error-503 (Apple Server Refused SRP Password Validation Request), "
                        f"Retry At-{retry_at}")

    except Exception as err:
        log_exception(err)
        all_verified_flag = False

    post_event(f"{EVLOG_IC3_STAGE_HDR} {stage_title}")
    Gb.EvLog.update_event_log_display("")

    return all_verified_flag

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_4_setup_data_sources_retry(final_retry=False):
    '''
    Apple accounts with login errors or containing tracked devices that are not found
    in Stage 4 are added to Gb.usernames_setup_error_retry_list. iCloud3_main checks to
    see if there are any devices that are in this list when starting up. Their setup
    will be retried here if necessary. This is a shortened version of the full Stage 4
    where all devices for all data sources are set up.
    '''

    Gb.trace_prefix = 'STAGE4'
    stage_title = f"Stage 4 > Data Source Device Assignment (Retry)"
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message(stage_title)
    broadcast_info_msg(stage_title)

    post_event(f"{EVLOG_ALERT}Apple Acct setup will be retried to resolve Missing Devices:"
                f"{CRLF_DOT}Apple Account > {list_to_str(Gb.usernames_setup_error_retry_list)}")

    for Device in Gb.Devices:
        Device.set_fname_alert('')

        # Test code for invalid apple_account value. Set config value for dev #2 to invalid@gmail.com
        # Then set it to the valid apple_account value here. It will fail in Stage 4 & retry #1
        # but pass in the last_retry
        # if final_retry and Device.conf_apple_acct_username == 'invalid@gmail.com':
        #     Device.conf_apple_acct_username = 'valid@gmail.com'
        #     Gb.conf_devices[1]['apple_account'] = 'valid@gmail.com'

    try:
        all_verified_flag = True
        for username in Gb.usernames_setup_error_retry_list:
            if username not in Gb.conf_usernames:
                continue

            _log_into_apple_accounts(retry=True)

            PyiCloud = Gb.PyiCloud_by_username.get(username)

            if PyiCloud:
                # If Connection was refused, do not retry logging into apple acct
                if PyiCloud.response_code == 302:
                    continue

                post_event(f"Verify Apple Acct > {PyiCloud.username_id}, Verified")
                start_ic3.setup_data_source_ICLOUD(retry=True)

                if PyiCloud.account_locked:
                    post_error_msg( f"{EVLOG_ERROR}Apple Acct > {PyiCloud.username_id}, "
                                    f"Acct is Locked. Log onto www.icloud.com and unlock "
                                    f"your account to reauthorize location services.")
                    post_alert(PyiCloud.username_id, "Apple Acct is Locked")
            else:
                post_event(f"{EVLOG_ALERT}APPLE ACCT LOGIN FAILED > {username_id(username)}, Unavailable")
                post_alert(username_id(username), "Apple Acct Login Failed")

            start_ic3.set_devices_verified_status()
            all_verified_flag = _are_all_devices_verified(retry=True)

            if all_verified_flag:
                Gb.usernames_setup_error_retry_list = \
                    list_del(Gb.usernames_setup_error_retry_list, PyiCloud.username)

    except Exception as err:
        log_exception(err)
        all_verified_flag = False

    post_event(f"{EVLOG_IC3_STAGE_HDR} {stage_title}")
    Gb.EvLog.update_event_log_display("")

    # if final_retry:
    #     if is_empty(Gb.usernames_setup_error_retry_list):
    #         post_event(f"{EVLOG_ALERT}ALL ICLOUD STARTUP ERRORS RESOLVED")
    #     else:
    #         apple_acct_list = [username_id(username)
    #                             for username in Gb.usernames_setup_error_retry_list]
    #         post_alert(apple_acct_list[0], "Apple Acct Device Setup Issue")

    return all_verified_flag

#------------------------------------------------------------------
def _log_into_apple_accounts(retry=False):
    '''
    Verify that all Apple Account PyiCloud objects have been created
    '''
    if Gb.use_data_source_ICLOUD is False:
        return False

    if Gb.initial_icloud3_loading_flag is False:
        return True

    if is_empty(Gb.conf_usernames):
        return False

    # Verify that all apple accts have been setup. Restart the setup process for any that
    # are not complete
    aa_login_error = ''
    for username in Gb.conf_usernames:
        PyiCloud = Gb.PyiCloud_by_username.get(username)
        if (PyiCloud is None
                or PyiCloud.AADevData_by_device_id == {}):

            conf_apple_acct, _idx = config_file.conf_apple_acct(username)

            PyiCloud = pyicloud_ic3_interface.log_into_apple_account(
                                        username,
                                        Gb.PyiCloud_password_by_username[username],
                                        apple_server_location=conf_apple_acct[CONF_SERVER_LOCATION],
                                        locate_all_devices=conf_apple_acct[CONF_LOCATE_ALL])

            if PyiCloud:
                Gb.PyiCloud_by_username[username] = PyiCloud
                if PyiCloud.auth_failed_503:
                    if aa_login_error: aa_login_error += ', '
                    aa_login_error += f"{PyiCloud.account_owner} (503)"

    if Gb.internet_error:
        return False

    if (aa_login_error
            or is_empty(PyiCloud.AADevData_by_device_id)):
        pass

    elif is_empty(Gb.devices_without_location_data):
        post_event(f"Apple Acct > All Tracked Devices Located")

    else:
        post_event( f"{RED_ALERT}Apple Acct > Some Tracked Devices not Located:"
                    f"{CRLF}{NBSP6}{DOT}{list_to_str(Gb.devices_without_location_data)}")

    return True

#------------------------------------------------------------------
def _are_all_devices_verified(retry=False):
    '''
    See if all tracked devices are verified.

    Arguments:
        retry   - True  - The verification was retried
                - False - This is the first time the verification was done

    Return:
        True  - All were verifice
        False - Some were not verified
    '''


    # Get a list of all tracked devices that have not been set up by icloud or the Mobile App
    unverified_devices = [Device.fname_devicename
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if Device.verified_flag is False and Device.isnot_inactive]
    unverified_device_usernames = [Device.conf_apple_acct_username
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if (Device.verified_flag is False
                                    and Device.isnot_inactive)]

    Gb.usernames_setup_error_retry_list   = list(set(unverified_device_usernames))
    Gb.devicenames_setup_error_retry_list = list(set(unverified_devices))

    Gb.startup_lists['_.usernames_setup_error_retry_list']   = Gb.usernames_setup_error_retry_list
    Gb.startup_lists['_.devicenames_setup_error_retry_list'] = Gb.devicenames_setup_error_retry_list

    if is_empty(unverified_devices):
        return True

    if retry:
        post_evlog_greenbar_msg("Some Tracked Devices could not be verified. Restart may be needed.")
        event_msg = (f"{EVLOG_ALERT}Some Tracked Devices could not be verified. Review and correct "
                    f"any configuration errors. Then restart iCloud3")
    else:
        event_msg = f"{EVLOG_ALERT}UNVERIFIED DEVICES ALERT > Some Tracked Devices could not be verified."
    event_msg += (f"{CRLF_DOT}Unverified Devices > {', '.join(unverified_devices)}")
    post_event(event_msg)

    return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_5_configure_tracked_devices():

    Gb.trace_prefix = 'STAGE5'
    stage_title = f'Stage 5 > Device Configuration Summary'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")


    for username, PyiCloud in Gb.PyiCloud_by_username.items():
        log_debug_msg(f"PyiCloud Finialized > {PyiCloud.account_owner}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        # start_ic3.remove_unverified_untrackable_devices()
        start_ic3.identify_tracked_monitored_devices()

        start_ic3.setup_trackable_devices()
        start_ic3.display_inactive_devices()
        start_ic3.display_all_devices_config_info()
        Gb.EvLog.setup_event_log_trackable_device_info()

    except Exception as err:
        log_exception(err)

    Gb.EvLog.update_event_log_display("")
    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message('')


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_6_initialization_complete():

    Gb.trace_prefix = 'STAGE6'
    stage_title = f'{ICLOUD3} Initialization Complete'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    broadcast_info_msg(stage_title)

    start_ic3.display_platform_operating_mode_msg()
    Gb.EvLog.display_user_message('')

    Gb.startup_log_msgs = ''

    try:
        start_ic3.display_object_lists()
        start_ic3.dump_startup_lists_to_log()
        alert_msg = ''
        if Gb.alerts_sensor_attrs:
            for source, msg in Gb.alerts_sensor_attrs.items():
                alert_msg += f"{CRLF_DOT}{source} > {msg}"

            Gb.EvLog.alert_message = 'Problems occured during startup up that should be reviewed'
            post_event( f"{EVLOG_ALERT}The following issues were detected when starting iCloud3. "
                        f"Scroll through the Startup Log for more information: "
                        f"{alert_msg}")

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_7_initial_locate():
    '''
    The PyiCloud Authentication function updates the iCloud raw data after the account
    has been authenticated. Requesting the initial data update there speeds up loading iC3
    since the Apple Acct login & authentication was started in the __init__ module.

    This routine processes the new raw iCloud data and set the initial location.
    '''

    # The restart will be requested if using iCloud as a data source and no data was returned
    # from PyiCloud
    if Gb.PyiCloud_by_username == {}:
        return

    if Gb.reinitialize_icloud_devices_flag and Gb.conf_icloud_device_cnt > 0:
        return_code = reinitialize_icloud_devices()

    Gb.trace_prefix = '1stLOC'

    Gb.this_update_secs = time_now_secs()
    Gb.this_update_time = time_now()
    post_event("Requesting Initial Locate")
    post_event( f"{EVLOG_IC3_STARTING}Start up Complete > {ICLOUD3_VERSION_MSG}, "
                f"{format_day_date_now()}")
                # f"{dt_util.now().strftime('%A, %b %d')}")

    for Device in Gb.Devices:
        post_evlog_greenbar_msg(f"Initial Locate > {Device.fname_devicename}")
        Device.update_sensors_flag = True
        Device.icloud_initial_locate_done = True

        if Device.AADevData_icloud:
            Device.update_dev_loc_data_from_raw_data_ICLOUD(Device.AADevData_icloud)
        else:
            continue

        Gb.iCloud3.process_updated_location_data(Device, ICLOUD)

        post_event(Device,
                    f"{Device.dev_data_source} Trigger > Initial Locate@"
                    f"{Device.loc_data_time_gps}")

        if Device.no_location_data:
            post_event(Device, f"{EVLOG_ALERT}NO GPS DATA RETURNED FROM ICLOUD LOCATION SERVICE")
            error_msg = (f"iCloud3 > {Device.fname_devicename} > "
                        "No GPS data was returned from iCloud Location "
                        "Service on the initial locate")
            log_warning_msg(error_msg)


    # Update the distance between all devices not that they have all been located
    # Then go back through and update the device_tracker entity to set the distance
    # between devices for the first time
    det_interval.set_dist_to_devices(post_event_msg=True)
    for Device in Gb.Devices:
        Device.sensors[DISTANCE_TO_DEVICES] = \
                    det_interval.format_dist_to_devices_msg(Device, time=True, age=False)
        Device.write_ha_device_tracker_state()

#------------------------------------------------------------------
def reinitialize_icloud_devices():
    '''
    Setup restarting iCloud3 if it has not already been done.

    Return  - True - Continue with Initial Locate
            - False - Restart failes
    '''
    try:
        if Gb.PyiCloud is None:
            return

        Gb.reinitialize_icloud_devices_cnt += 1
        if Gb.reinitialize_icloud_devices_cnt > 2:
            return

        Gb.start_icloud3_inprocess_flag = False
        Gb.reinitialize_icloud_devices_flag = False
        Gb.initial_icloud3_loading_flag = False

        alert_msg = f"{EVLOG_ALERT}"
        if Gb.conf_data_source_ICLOUD:
            unverified_devices = [devicename
                        for devicename, Device in Gb.Devices_by_devicename.items() \
                        if Device.verified_flag is False]

            alert_msg +=(f"UNVERIFIED DEVICES > One or more devices was not verified. "
                        f"Apple Account access may be down, slow to respond or the internet may be down."
                        f"{CRLF_DOT}Unverified Devices > {', '.join(unverified_devices)}")
        post_event(alert_msg)

    except Exception as err:
        log_exception(err)

    return