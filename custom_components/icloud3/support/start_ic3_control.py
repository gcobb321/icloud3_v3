from ..global_variables     import GlobalVariables as Gb
from ..const                import (NOT_SET,
                                    NEW_LINE, CRLF,
                                    EVLOG_ALERT, EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    CONF_VERSION, ICLOUD_FNAME,
                                    )

from ..support              import start_ic3
from ..support              import pyicloud_ic3_interface
from ..support              import icloud_data_handler
from ..support              import determine_interval as det_interval

from ..helpers.common       import (instr, obscure_field, )
from ..helpers.messaging    import (broadcast_info_msg,
                                    post_event, post_error_msg, log_error_msg,
                                    post_monitor_msg, post_internal_error,
                                    log_debug_msg, log_info_msg, log_exception, log_rawdata,
                                    _trace, _traceha, )
from ..helpers.time_util    import (time_now_secs, calculate_time_zone_offset, )

import homeassistant.util.dt as dt_util


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_1_setup_variables():

    Gb.trace_prefix = 'STAGE 1 > '
    stage_title = 'Stage 1 > Initial Preparations'

    broadcast_info_msg(stage_title)

    #check to see if restart is in process
    if Gb.start_icloud3_inprocess_flag:
        return

    Gb.EvLog.display_user_message('iCloud3 > Initializiing')

    try:
        Gb.this_update_secs             = time_now_secs()
        Gb.start_icloud3_inprocess_flag = True
        Gb.start_icloud3_request_flag   = False
        Gb.all_tracking_paused_flag     = False
        Gb.config_track_devices_change_flag = False

        if Gb.initial_icloud3_loading_flag is False:
            post_event( f"{EVLOG_IC3_STARTING}Restarting iCloud3 v{Gb.version} > "
                        f"{dt_util.now().strftime('%A, %b %d')}")
            # Gb.EvLog.update_event_log_display("")
            start_ic3.reinitialize_config_parameters()
            start_ic3.initialize_global_variables()
            start_ic3.set_global_variables_from_conf_parameters()

        start_ic3.define_tracking_control_fields()

        post_event(f"iCloud3 Directory > {Gb.icloud3_directory}")
        if Gb.conf_profile[CONF_VERSION] == 0:
            post_event(f"iCloud3 Configuration File > {Gb.config_ic3_yaml_filename}")
        else:
            post_event(f"iCloud3 Configuration File > {Gb.icloud3_config_filename}")

        start_ic3.display_platform_operating_mode_msg()
        Gb.hass.loop.create_task(start_ic3.update_lovelace_resource_event_log_js_entry())
        start_ic3.check_ic3_event_log_file_version()

        post_monitor_msg(f"LocationInfo-{Gb.ha_location_info}")

        calculate_time_zone_offset()
        start_ic3.set_evlog_table_max_cnt()

        post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_2_prepare_configuration():

    Gb.trace_prefix = 'STAGE 2 > '
    stage_title = 'Stage 2 > Prepare Support Services'

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        if Gb.initial_icloud3_loading_flag is False:
            start_ic3.initialize_PyiCloud()

        start_ic3.create_Zones_object()
        start_ic3.create_Waze_object()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")

    try:
        configuration_needed_msg = ''
        # Default configuration that has not been updated or migrated from v2
        if Gb.conf_profile[CONF_VERSION] == -1:
            configuration_needed_msg = 'INITIAL INSTALLATION - CONFIGURATION IS REQUIRED'

        elif Gb.conf_profile[CONF_VERSION] == 0:
            configuration_needed_msg = 'CONFIGURATION PARAMETERS WERE MIGRATED FROM v2 to v3 - ' \
                                        'THEY MUST BE REVIEWED BEFORE STARTING ICLOUD3'
        elif Gb.conf_devices == []:
            configuration_needed_msg = 'DEVICES MUST BE SET UP TO ENABLE TRACKING'

        if configuration_needed_msg:
            event_msg =(f"{EVLOG_ALERT}Alert > {configuration_needed_msg}{CRLF}"
                        f"{CRLF}1. Select {SETTINGS_INTEGRATIONS_MSG}"
                        f"{CRLF}2. Select `+Add Integration` to add the iCloud3 integration if it is not dislayed. Then search "
                        f"for `iCloud3`, select it and complete the installation."
                        f"{CRLF}3. Select `{INTEGRATIONS_IC3_CONFIG_MSG}` to open the iCloud3 Configurator"
                        f"{CRLF}4. Review and setup the `iCloud Account` and `iCloud3 Devices` configuration windows "
                        f"{CRLF}5. Exit the configurator and `Restart iCloud3`")
            post_event(event_msg)

            Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_3_setup_configured_devices():

    Gb.trace_prefix = 'STAGE 3 > '
    stage_title = 'Stage 3 > Prepare Configured Devices'

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        # Make sure a full restart is done if all of the devices were not found in the iCloud data
        if Gb.config_track_devices_change_flag:
            pass
        elif (Gb.tracking_method_FMF
                and Gb.fmf_device_verified_cnt < len(Gb.Devices)):
            Gb.config_track_devices_change_flag = True
        elif (Gb.tracking_method_FAMSHR
                and Gb.famshr_device_verified_cnt < len(Gb.Devices)):
            Gb.config_track_devices_change_flag = True
        elif Gb.log_debug_flag:
            Gb.config_track_devices_change_flag = True

        start_ic3.create_Devices_object()

        Gb.WazeHist.load_track_from_zone_table()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_4_setup_tracking_methods(retry=False):

    Gb.trace_prefix = 'STAGE 4 > '
    stage_title = 'Stage 4 > Setup iCloud & iOSApp Tracking Methods'

    # Missing username/password, PyiCloud can not be started
    if Gb.data_source_use_icloud:
        if Gb.username == '' and Gb.password == '':
            Gb.data_source_use_icloud = False
            event_msg =(f"{EVLOG_ALERT}Alert > The iCloud username or password has not been "
                                f"configured. iCloud will not be used for location tracking")
            post_event(event_msg)

    return_code = True
    retry_msg = ', Retrying iCloud Device Setup' if retry else ''
    Gb.EvLog.display_user_message(stage_title)
    broadcast_info_msg(stage_title)

    try:
        if Gb.data_source_use_icloud:
            post_event(f"iCloud Account Used > {obscure_field(Gb.username)}")

            pyicloud_ic3_interface.verify_pyicloud_setup_status()

            if Gb.PyiCloud:
                start_ic3.setup_tracked_devices_for_famshr()
                start_ic3.setup_tracked_devices_for_fmf()
                start_ic3.set_device_tracking_method_famshr_fmf()
                start_ic3.tune_device_tracking_method_famshr_fmf()
            else:
                event_msg = 'iCloud Location Services is not being used to locate devices'
                post_event(event_msg)

        if Gb.data_source_use_iosapp:
            start_ic3.setup_tracked_devices_for_iosapp()
        else:
            event_msg = 'iOS App is not being used to locate devices'
            post_event(event_msg)

        return_code = _list_unverified_devices(retry=retry)

    except Exception as err:
        log_exception(err)
        return_code = False

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}{retry_msg}")
    Gb.EvLog.update_event_log_display("")
    return return_code

#------------------------------------------------------------------
def _list_unverified_devices(retry=False):
    '''
    See if all tracked devices are verified.

    Arguments:
        retry   - True  - The verification was retried
                - False - This is the first time the verification was done

    Return:
        True  - All were verifice
        False - Some were not verified
    '''

    unverified_devices = [devicename for devicename, Device in Gb.Devices_by_devicename_tracked.items() \
                                        if Device.verified_flag is False and Device.is_tracked]

    if unverified_devices == []:
        return True

    if retry:
        event_msg = (f"{EVLOG_ALERT}Some devices could not be verified. iCloud3 needs to be "
                        f"restarted to see if the unverified devices are available for "
                        f"tracking. If not, check the device parameters in the iCloud3 configurator:"
                        f"{CRLF}1. {SETTINGS_INTEGRATIONS_MSG} >"
                        f"{CRLF}2. {INTEGRATIONS_IC3_CONFIG_MSG}"
                        f"{CRLF}3. iCloud3 Devices")
    else:
        event_msg = (f"{EVLOG_ALERT}Alert > Some devices could not be verified. iCloud Location Services "
                        f"will be reinitialized")
    event_msg += (f"{CRLF}{CRLF}Unverified Devices > {', '.join(unverified_devices)}")
    post_event(event_msg)

    return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_5_configure_tracked_devices():

    Gb.trace_prefix = 'STAGE 5 > '
    stage_title = 'Stage 5 > Configure Tracked Devices'

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        start_ic3.remove_unverified_untrackable_devices()
        start_ic3.identify_tracked_monitored_devices()
        Gb.EvLog.setup_event_log_trackable_device_info()

        start_ic3.setup_trackable_devices()
        start_ic3.display_inactive_devices()
        Gb.EvLog.update_event_log_display("")
        start_ic3.display_object_lists()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message('')

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_6_initialization_complete():

    Gb.trace_prefix = 'STAGE 6 > '
    stage_title = 'iCloud3 Initialization Complete'

    broadcast_info_msg(stage_title)

    start_ic3.display_platform_operating_mode_msg()
    Gb.EvLog.display_user_message('')

    if Gb.log_debug_flag is False:
        Gb.startup_log_msgs = (NEW_LINE + '-'*55 +
                                Gb.startup_log_msgs.replace(CRLF, NEW_LINE) +
                                NEW_LINE + '-'*55)
        log_info_msg(Gb.startup_log_msgs)
    Gb.startup_log_msgs = ''

    start_ic3.display_object_lists()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_7_initial_locate():
    '''
    The PyiCloud Authentication function updates the FamShr raw data after the account
    has been authenticated. Requesting the initial data update there speeds up loading iC3
    since the iCloud acct login & authentication was started in the __init__ module.

    This routine processes the new raw FamShr data and set the initial location.

    If there are devices that use FmF and not FamShr, the FamF data will be requested
    and those devices will be updated.
    '''

    Gb.trace_prefix = 'INITLOC > '
    post_event("Requesting Initial Locate")
    event_msg =(f"{EVLOG_IC3_STARTING}Initializing iCloud3 v{Gb.version} > Complete")
    post_event(event_msg)

    evlog_results_displayed = False
    for Device in Gb.Devices:
        if Device.PyiCloud_RawData_famshr:
            Device.update_dev_loc_data_from_raw_data_FAMSHR_FMF(Device.PyiCloud_RawData_famshr)

        elif Device.PyiCloud_RawData_fmf:
            icloud_data_handler.update_PyiCloud_RawData_data(Device, results_msg_flag=False)
            Device.update_dev_loc_data_from_raw_data_FAMSHR_FMF(Device.PyiCloud_RawData_fmf)

        else:
            continue

        Device.update_sensors_flag = True

        Gb.iCloud3.process_updated_location_data(Device, ICLOUD_FNAME)

        Device.icloud_initial_locate_done = True
