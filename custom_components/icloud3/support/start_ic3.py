

from ..global_variables import GlobalVariables as Gb
from ..const            import (
                                DEBUG_TRACE_CONTROL_FLAG,
                                STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY, IC3LOGGER_FILENAME,
                                DEVICE_TRACKER, DEVICE_TRACKER_DOT, NOTIFY, DOMAIN,
                                HOME, STATIONARY, ERROR,
                                STATE_TO_ZONE_BASE, CMD_RESET_PYICLOUD_SESSION,
                                EVLOG_INIT_HDR, EVLOG_ALERT, EVLOG_IC3_STARTING, EVLOG_NOTICE, EVLOG_IC3_STAGE_HDR,
                                EVLOG_TABLE_MAX_CNT_BASE, EVLOG_TABLE_MAX_CNT_ZONE,
                                CRLF, CRLF_DOT, CRLF_CHK, CRLF_NBSP6_DOT, CRLF_HDOT, DOT2, CRLF_X, CRLF_NBSP6_X,
                                RARROW, NBSP4, NBSP6, CIRCLE_X, INFO_SEPARATOR, DASH_20, CHECK_MARK,
                                ICLOUD, FMF, FAMSHR,
                                DEVICE_TYPE_FNAME,
                                IPHONE, IPAD, IPOD, WATCH, AIRPODS,
                                IOSAPP, NO_IOSAPP,
                                INACTIVE_DEVICE, TRACKING_METHOD_FNAME,
                                NAME, FNAME, TITLE, RADIUS, NON_ZONE_ITEM_LIST, FRIENDLY_NAME,
                                LOCATION, LATITUDE, RADIUS,
                                TRIGGER,
                                ZONE, ID,
                                BATTERY_LEVEL, BATTERY_STATUS,
                                CONF_ENCODE_PASSWORD,
                                CONF_VERSION,  CONF_VERSION_INSTALL_DATE,
                                CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_CARD_PROGRAM,
                                CONF_USERNAME, CONF_PASSWORD,
                                CONF_DATA_SOURCE, CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX,
                                CONF_DEVICE_TYPE, CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME,
                                CONF_INZONE_INTERVALS, CONF_TRACK_FROM_ZONES,
                                CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT,
                                CONF_MAX_INTERVAL, CONF_OFFLINE_INTERVAL, CONF_EXIT_ZONE_INTERVAL,
                                CONF_IOSAPP_ALIVE_INTERVAL, CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD,
                                CONF_OLD_LOCATION_ADJUSTMENT,
                                CONF_TFZ_TRACKING_MAX_DISTANCE, CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                CONF_TRAVEL_TIME_FACTOR, CONF_PASSTHRU_ZONE_TIME, CONF_DISTANCE_BETWEEN_DEVICES,
                                CONF_LOG_LEVEL,
                                CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_FORMAT,
                                CONF_CENTER_IN_ZONE, CONF_DISCARD_POOR_GPS_INZONE,
                                CONF_WAZE_USED, CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                                CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE,
                                CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                CONF_STAT_ZONE_FNAME, CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_STAT_ZONE_BASE_LATITUDE,
                                CONF_STAT_ZONE_BASE_LONGITUDE, CONF_DISPLAY_TEXT_AS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                CONF_FAMSHR_DEVICE_ID, CONF_FAMSHR_DEVICE_ID2, CONF_FMF_DEVICE_ID,
                                CONF_IOSAPP_DEVICE, CONF_FMF_EMAIL,
                                CONF_TRACKING_MODE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                CONF_ZONE, CONF_NAME,
                                DEFAULT_GENERAL_CONF,
                                )

from ..device               import iCloud3_Device
from ..zone                 import iCloud3_Zone, iCloud3_StationaryZone
from ..support.waze         import Waze
from ..support.waze_history import WazeRouteHistory as WazeHist
from ..support              import iosapp_interface
from ..support              import iosapp_data_handler
from ..support              import service_handler
from ..support              import config_file
from ..helpers              import entity_io
from ..helpers.common       import (instr, format_gps, circle_letter, zone_display_as, list_to_str, is_statzone, )
from ..helpers.messaging    import (broadcast_info_msg,
                                    post_event, post_error_msg, post_monitor_msg,
                                    log_info_msg, log_debug_msg, log_warning_msg, log_rawdata, log_exception,
                                    open_ic3_debug_log_file, close_ic3_debug_log_file,
                                    _trace, _traceha, )
from ..helpers.dist_util    import (format_dist_km, )
from ..helpers.time_util    import (secs_to_time_str, )

import os
import json
import shutil
from datetime               import timedelta, date, datetime
from collections            import OrderedDict
from homeassistant.util     import slugify
from re import match

import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- INITIALIZATION
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def initialize_directory_filenames():
    """ Set up common directories and file names """


    Gb.ha_config_directory            = Gb.hass.config.path()
    Gb.ha_storage_directory           = Gb.hass.config.path(STORAGE_DIR)
    Gb.ha_storage_icloud3             = Gb.hass.config.path(STORAGE_DIR, 'icloud3')
    Gb.icloud3_config_filename        = Gb.hass.config.path(STORAGE_DIR, 'icloud3', 'configuration')
    Gb.icloud3_restore_state_filename = Gb.hass.config.path(STORAGE_DIR, 'icloud3', 'restore_state')
    Gb.wazehist_database_filename     = Gb.hass.config.path(STORAGE_DIR, 'icloud3', 'waze_location_history.db')
    Gb.icloud3_directory              = Gb.hass.config.path('custom_components', 'icloud3')
    Gb.entity_registry_file           = Gb.hass.config.path(STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY)

    # Note: The Event Log  directory & filename are initialized in config_file.py
    # after the configuration file has been read

    #Set up pyicloud cookies directory & file names
    Gb.icloud_cookies_dir  = Gb.hass.config.path(STORAGE_DIR, 'icloud')
    Gb.icloud_cookies_file = "".join([c for c in Gb.username if match(r"\w", c)])
    if not os.path.exists(Gb.icloud_cookies_dir):
        os.makedirs(Gb.icloud_cookies_dir)

#------------------------------------------------------------------------------
#
#   UPDATE LOVELACE RESOURCES FOR EVENT LOG CARD
#
#------------------------------------------------------------------------------
async def update_lovelace_resource_event_log_js_entry():
    '''
    Check the lovelace resource for an icloud3_event-log-card.js entry.
    If found, it is already set up and there is nothing to do.
    If not found, add it to the lovelace resource so the user does not
        have to manually add it. The browser needs to be refreshed so also
        generate a broadcast message.
    '''
    Resources = Gb.hass.data["lovelace"]["resources"]
    if Resources:
        if not Resources.loaded:
            await Resources.async_load()
            Resources.loaded = True

        www_evlog_js_directory = Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]
        evlog_url = (   f"{Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]}/"
                        f"{Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]}")
        evlog_url = Gb.www_evlog_js_filename.replace('www', '/local')
        update_lovelace_resources = True
        for item in Resources.async_items():
            if instr(item["url"], evlog_url):
                update_lovelace_resources = False

        if update_lovelace_resources:
            if getattr(Resources, "async_create_item", None):
                await Resources.async_create_item({"res_type": "module", "url": evlog_url, })

            elif (getattr(Resources, "data", None)
                    and getattr(Resources.data, "append", None)):
                Resources.data.append({"type": "module", "url": evlog_url, })
            Resources.loaded = False

            post_event( f"{EVLOG_ALERT}Lovelace Resources Updated > "
                        f"Browser cache must be cleared, "
                        f"Added-{evlog_url}")

            title       = 'Action Required - Clear Browser Cache'
            message     = (f'The Event Log Custom Card was added to the Lovelace Resource list.'
                        f'<br>File-*{evlog_url}*'
                        f'<br><br>The browser cache must be cleared before the Event Log '
                        f'Custom Card can be added.'
                        f'<br>1. Press **Ctrl+Shift+Del**'
                        f'<br>2. On the *Settings* tab, check *Clear images and files*'
                        f'<br>3. Click **Clear Data/Clear Now**'
                        f'<br>4. Select the *Home Assistant* tab'
                        f'<br>5. **Refresh** the display')
            service_handler.set_ha_notification(title, message, issue=False)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 0
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#------------------------------------------------------------------------------
#
#   VARIABLE DEFINITION & INITIALIZATION FUNCTIONS
#
#------------------------------------------------------------------------------
def define_tracking_control_fields():
    # Gb.any_device_being_updated_flag   = False
    Gb.trigger                         = {}       #device update trigger
    Gb.info_notification               = ''
    Gb.broadcast_msg                   = ''

#------------------------------------------------------------------------------
#
#   SET GLOBAL VARIABLES BACK TO THEIR INITIAL CONDITION
#
#------------------------------------------------------------------------------
def initialize_global_variables():

    # Configuration parameters that can be changed in config_ic3.yaml
    Gb.um                               = DEFAULT_GENERAL_CONF[CONF_UNIT_OF_MEASUREMENT]
    # Gb.time_format                      = 12
    Gb.time_format_12_hour              = True
    Gb.um_km_mi_factor                  = .62137
    Gb.um_m_ft                          = 'ft'
    Gb.um_kph_mph                       = 'mph'
    Gb.um_time_strfmt                   = '%I:%M:%S'
    Gb.um_time_strfmt_ampm              = '%I:%M:%S%P'
    Gb.um_date_time_strfmt              = '%Y-%m-%d %H:%M:%S'

    # Configuration parameters
    Gb.center_in_zone_flag             = DEFAULT_GENERAL_CONF[CONF_CENTER_IN_ZONE]
    Gb.display_zone_format             = DEFAULT_GENERAL_CONF[CONF_DISPLAY_ZONE_FORMAT]
    Gb.device_tracker_state_format     = DEFAULT_GENERAL_CONF[CONF_DEVICE_TRACKER_STATE_FORMAT]
    Gb.distance_method_waze_flag       = True
    Gb.max_interval_secs               = DEFAULT_GENERAL_CONF[CONF_MAX_INTERVAL] * 60
    Gb.offline_interval_secs           = DEFAULT_GENERAL_CONF[CONF_OFFLINE_INTERVAL] * 60
    Gb.exit_zone_interval_secs         = DEFAULT_GENERAL_CONF[CONF_EXIT_ZONE_INTERVAL] * 60
    Gb.iosapp_alive_interval_secs      = DEFAULT_GENERAL_CONF[CONF_IOSAPP_ALIVE_INTERVAL] * 3600
    Gb.travel_time_factor              = DEFAULT_GENERAL_CONF[CONF_TRAVEL_TIME_FACTOR]
    Gb.track_from_base_zone            = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_BASE_ZONE]
    Gb.track_from_home_zone            = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_HOME_ZONE]
    Gb.gps_accuracy_threshold          = DEFAULT_GENERAL_CONF[CONF_GPS_ACCURACY_THRESHOLD]
    Gb.old_location_threshold          = DEFAULT_GENERAL_CONF[CONF_OLD_LOCATION_THRESHOLD] * 60
    Gb.old_location_adjustment         = DEFAULT_GENERAL_CONF[CONF_OLD_LOCATION_ADJUSTMENT] * 60
    Gb.log_level                       = 'info'

    Gb.tfz_tracking_max_distance      = DEFAULT_GENERAL_CONF[CONF_TFZ_TRACKING_MAX_DISTANCE]

    Gb.waze_region                     = DEFAULT_GENERAL_CONF[CONF_WAZE_REGION]
    Gb.waze_max_distance               = DEFAULT_GENERAL_CONF[CONF_WAZE_MAX_DISTANCE]
    Gb.waze_min_distance               = DEFAULT_GENERAL_CONF[CONF_WAZE_MIN_DISTANCE]
    Gb.waze_realtime                   = DEFAULT_GENERAL_CONF[CONF_WAZE_REALTIME]
    Gb.waze_history_database_used      = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_DATABASE_USED]
    Gb.waze_history_max_distance       = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_MAX_DISTANCE]
    Gb.waze_history_track_direction    = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_TRACK_DIRECTION]

    # Tracking method control vaiables
    # Used to reset Gb.tracking_method  after pyicloud/icloud account successful reset
    # Will be changed to IOSAPP if pyicloud errors
    Gb.tracking_method_FAMSHR           = False
    Gb.tracking_method_FMF              = False
    Gb.tracking_method_IOSAPP           = False
    Gb.tracking_method_FMF_used         = False
    Gb.tracking_method_FAMSHR_used      = False
    Gb.tracking_method_IOSAPP_used      = False

#------------------------------------------------------------------------------
#
#   INITIALIZE THE GLOBAL VARIABLES WITH THE CONFIGURATION FILE PARAMETER
#   VALUES
#
#------------------------------------------------------------------------------
def set_global_variables_from_conf_parameters(evlog_msg=True):
    '''
    Set the iCloud3 variables from the configuration parameters
    '''
    try:
        config_event_msg = "Configure iCloud3 Operations >"
        config_event_msg += f"{CRLF_DOT}Load configuration parameters"

        set_icloud_username_password()

        Gb.www_evlog_js_directory       = Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]
        Gb.www_evlog_js_filename        = Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]

        Gb.um                           = Gb.conf_general[CONF_UNIT_OF_MEASUREMENT]
        Gb.time_format_12_hour          = Gb.conf_general[CONF_TIME_FORMAT].startswith('12')
        Gb.device_tracker_state_format  = Gb.conf_general[CONF_DEVICE_TRACKER_STATE_FORMAT]
        Gb.display_zone_format          = Gb.conf_general[CONF_DISPLAY_ZONE_FORMAT]
        Gb.center_in_zone_flag          = Gb.conf_general[CONF_CENTER_IN_ZONE]
        Gb.max_interval_secs            = Gb.conf_general[CONF_MAX_INTERVAL] * 60
        Gb.exit_zone_interval_secs      = Gb.conf_general[CONF_EXIT_ZONE_INTERVAL] * 60
        Gb.offline_interval_secs        = Gb.conf_general[CONF_OFFLINE_INTERVAL] * 60
        Gb.iosapp_alive_interval_secs   = Gb.conf_general[CONF_IOSAPP_ALIVE_INTERVAL] * 3600
        Gb.travel_time_factor           = Gb.conf_general[CONF_TRAVEL_TIME_FACTOR]
        Gb.passthru_zone_interval_secs  = Gb.conf_general[CONF_PASSTHRU_ZONE_TIME] * 60
        Gb.is_passthru_zone_used        = (14400 > Gb.passthru_zone_interval_secs > 0)   # time > 0 and < 4 hrs
        Gb.old_location_threshold       = Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD] * 60
        Gb.old_location_adjustment      = Gb.conf_general[CONF_OLD_LOCATION_ADJUSTMENT] * 60
        Gb.track_from_base_zone         = Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE]
        Gb.track_from_home_zone         = Gb.conf_general[CONF_TRACK_FROM_HOME_ZONE]
        Gb.gps_accuracy_threshold       = Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]
        Gb.discard_poor_gps_inzone_flag = Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]
        Gb.distance_between_device_flag = Gb.conf_general[CONF_DISTANCE_BETWEEN_DEVICES]

        Gb.tfz_tracking_max_distance   = Gb.conf_general[CONF_TFZ_TRACKING_MAX_DISTANCE]

        # Setup the Stationary Zone location and times
        # The stat_zone_base_lat/long will be adjusted after the Home zone is set up
        Gb.stat_zone_fname                = Gb.conf_general[CONF_STAT_ZONE_FNAME]
        Gb.stat_zone_base_latitude        = Gb.conf_general[CONF_STAT_ZONE_BASE_LATITUDE]
        Gb.stat_zone_base_longitude       = Gb.conf_general[CONF_STAT_ZONE_BASE_LONGITUDE]
        Gb.stat_zone_still_time_secs      = Gb.conf_general[CONF_STAT_ZONE_STILL_TIME] * 60
        Gb.stat_zone_inzone_interval_secs = Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL] * 60
        Gb.is_stat_zone_used              = (14400 > Gb.stat_zone_still_time_secs > 0)

        Gb.log_level                      = Gb.conf_general[CONF_LOG_LEVEL]

        # update the interval time for each of the interval types (i.e., ipad: 2 hrs, no_iosapp: 15 min)
        inzone_intervals = Gb.conf_general[CONF_INZONE_INTERVALS]
        Gb.inzone_interval_secs = {}
        Gb.inzone_interval_secs[IPHONE]     = inzone_intervals[IPHONE] * 60
        Gb.inzone_interval_secs[IPAD]       = inzone_intervals[IPAD] * 60
        Gb.inzone_interval_secs[WATCH]      = inzone_intervals[WATCH] * 60
        Gb.inzone_interval_secs[IPOD]       = inzone_intervals[IPHONE] * 60
        Gb.inzone_interval_secs[AIRPODS]    = inzone_intervals[AIRPODS] * 60
        Gb.inzone_interval_secs[NO_IOSAPP]  = inzone_intervals[NO_IOSAPP] * 60
        Gb.inzone_interval_secs[CONF_INZONE_INTERVAL] = inzone_intervals['other'] * 60

        Gb.EvLog.display_text_as = {}
        for display_text_as in Gb.conf_general[CONF_DISPLAY_TEXT_AS]:
            if instr(display_text_as, '>'):
                from_to_text = display_text_as.split('>')
                Gb.EvLog.display_text_as[from_to_text[0].strip()] = from_to_text[1].strip()
        config_event_msg += f"{CRLF_DOT}Set Display Text As Fields ({len(Gb.EvLog.display_text_as)} used)"

        set_waze_conf_parameters()

        # Set other fields and flags based on configuration parameters
        set_tracking_method(Gb.tracking_method)
        config_event_msg += (   f"{CRLF_DOT}Set Default Tracking Method "
                                f"({TRACKING_METHOD_FNAME.get(Gb.tracking_method, Gb.tracking_method)})")

        set_log_level(Gb.log_level)
        config_event_msg += f"{CRLF_DOT}Initialize Debug Control ({Gb.log_level})"

        set_um_formats()
        config_event_msg += f"{CRLF_DOT}Set Unit of Measure Formats ({Gb.um})"

        evlog_table_max_cnt = set_evlog_table_max_cnt()
        config_event_msg += f"{CRLF_DOT}Set Event Log Record Limits ({evlog_table_max_cnt} Events)"

        if evlog_msg:
            post_event(config_event_msg)

    except Exception as err:
        log_exception(err)

#------------------------------------------------------------------------------
#
#   HOMEASSISTANT STARTED EVENT
#
#   This is fired when Home Assistant is started and is used to complete any
#   setup tasks that were not completed since iCloud3 can start before HA
#   startup is complete.
#
#------------------------------------------------------------------------------
def ha_startup_completed(dummy_parameter):

    # HA may have not set up the notify service before iC3 starts. If so, the mobile_app
    # Notify entity was not setup either. Do it now.
    setup_notify_service_name_for_iosapp_devices(post_event_msg=True)

def ha_stopping(dummy_parameter):
    post_event("HA Shutting Down")
    close_ic3_debug_log_file()

#------------------------------------------------------------------------------
#
#   SET THE GLOBAL TRACKING METHOD
#
#   This is used during the startup routines and in other routines when errors occur.
#
#------------------------------------------------------------------------------
def set_icloud_username_password():
    '''
    Set up icloud username/password and devices from the configuration parameters
    '''
    Gb.username                     = Gb.conf_tracking[CONF_USERNAME].lower()
    Gb.username_base                = Gb.username.split('@')[0]
    Gb.password                     = Gb.conf_tracking[CONF_PASSWORD]
    Gb.encode_password_flag         = Gb.conf_tracking[CONF_ENCODE_PASSWORD]
    Gb.data_source_use_icloud       = instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD)
    Gb.data_source_use_iosapp       = instr(Gb.conf_tracking[CONF_DATA_SOURCE], IOSAPP)
    Gb.devices                      = Gb.conf_devices

#------------------------------------------------------------------------------
def initialize_PyiCloud():
    Gb.PyiCloud = None

#------------------------------------------------------------------------------
def set_tracking_method(tracking_method):
    '''
    Set up tracking method. These fields will be reset based on the device_id's available
    for the Device once the famshr and fmf tracking methods are set up.
    '''
    if (Gb.conf_profile[CONF_VERSION] > 0
            and Gb.data_source_use_icloud
            and Gb.password == ''):
        error_msg =("iCloud3 Error > The password is required for the "
                    f"iCloud Location Services tracking method. "
                    f"The iOS App tracking_method will be used.")
        post_error_msg(error_msg)
        tracking_method = IOSAPP

    # If the tracking_method is in OPT_TRACK_METHOD, we are processing one from the
    # config parameters. If not, it is the actual tracking method to assign
    if Gb.data_source_use_icloud:
        tracking_method = FAMSHR
    elif Gb.data_source_use_iosapp:
        tracking_method = IOSAPP


    # If the tracking method changes, the complete initialization must be done
    if Gb.data_source_use_icloud:
        Gb.tracking_method = FAMSHR if tracking_method == '' else tracking_method
        Gb.tracking_method_FAMSHR     = (tracking_method == FAMSHR)
        Gb.tracking_method_FMF        = (tracking_method == FMF)

    if Gb.data_source_use_iosapp:
        Gb.tracking_method_IOSAPP     = (tracking_method == IOSAPP)

#------------------------------------------------------------------------------
#
#   INITIALIZE THE UNIT_OF_MEASURE FIELDS
#
#------------------------------------------------------------------------------
def set_um_formats():
    #Define variables, lists & tables
    if Gb.um == 'mi':
        Gb.um_km_mi_factor          = 0.62137
        Gb.um_m_ft                  = 'ft'
        Gb.um_kph_mph               = 'mph'
    else:
        Gb.um_km_mi_factor          = 1
        Gb.um_m_ft                  = 'm'
        Gb.um_kph_mph               = 'kph'

    if Gb.time_format_12_hour:
        Gb.um_time_strfmt       = '%I:%M:%S'
        Gb.um_time_strfmt_ampm  = '%I:%M:%S%P'
        Gb.um_date_time_strfmt  = '%Y-%m-%d %I:%M:%S'
    else:
        Gb.um_time_strfmt       = '%H:%M:%S'
        Gb.um_time_strfmt_ampm  = '%H:%M:%S'
        Gb.um_date_time_strfmt  = '%Y-%m-%d %H:%M:%S'

#------------------------------------------------------------------------------
def set_evlog_table_max_cnt():
    '''
    Set te initial Event Log Table Record Limit. This will be updated after the devices
    are initialized and the Event Log attributes are then reset.
    '''
    evlog_table_max_cnt = EVLOG_TABLE_MAX_CNT_BASE
    for conf_device in Gb.conf_devices:
        evlog_table_max_cnt += \
                EVLOG_TABLE_MAX_CNT_ZONE*len(conf_device[CONF_TRACK_FROM_ZONES])

    if evlog_table_max_cnt > Gb.EvLog.evlog_table_max_cnt:
        Gb.EvLog.evlog_table_max_cnt = evlog_table_max_cnt
    return Gb.EvLog.evlog_table_max_cnt

#------------------------------------------------------------------------------
#
#   INITIALIZE THE DEBUG CONTROL FLAGS
#
#   Decode the log_level: debug parameter
#      debug            - log 'debug' messages to the log file under the 'info' type
#      debug_rawdata    - log data read from records to the log file
#      eventlog         - Add debug items to ic3 event log
#      debug+eventlog   - Add debug items to HA log file and ic3 event log
#
#------------------------------------------------------------------------------
def set_log_level(log_level):

    log_level = log_level.lower()

    # Log level can be set on Event Log > Actions in service_handler.py which overrides
    # the configuration/log_level parameter. The current log_level is preserved in the
    # log_debug/rawdata_flag _restart in service_handler (Restart) to reassign any log
    # level overrides on an iC3 restart
    if Gb.log_debug_flag_restart is not None or Gb.log_rawdata_flag_restart is not None:
        if Gb.log_debug_flag_restart is not None:
            Gb.log_debug_flag         = Gb.log_debug_flag_restart
            Gb.log_debug_flag_restart = None

        if Gb.log_rawdata_flag_restart is not None:
            Gb.log_rawdata_flag         = Gb.log_rawdata_flag_restart
            Gb.log_rawdata_flag_restart = None
    else:
        Gb.log_debug_flag   = instr(log_level, 'debug')
        Gb.log_rawdata_flag = instr(log_level, 'rawdata')
        Gb.log_rawdata_flag_unfiltered = instr(log_level, 'unfiltered')

    # Turn on debug log if beta version or less than 5-days after an install
    # of a new version or the loglevel is rawdata log
    dt_auto_debug_end = datetime.strptime(Gb.conf_profile[CONF_VERSION_INSTALL_DATE], \
                                        "%Y-%m-%d %H:%M:%S").date() + timedelta(days=5)
    Gb.log_debug_flag = Gb.log_debug_flag or instr(Gb.version, 'b')
    Gb.log_debug_flag = Gb.log_debug_flag or dt_auto_debug_end > date.today()
    Gb.log_debug_flag = Gb.log_debug_flag or Gb.log_rawdata_flag

    Gb.evlog_trk_monitors_flag = Gb.evlog_trk_monitors_flag or instr(log_level, 'eventlog')

#------------------------------------------------------------------------------
#
#   Initialize the Waze parameters
#
#------------------------------------------------------------------------------
def set_waze_conf_parameters():
    Gb.waze_max_distance = Gb.conf_general[CONF_WAZE_MAX_DISTANCE]
    Gb.waze_min_distance = Gb.conf_general[CONF_WAZE_MIN_DISTANCE]
    Gb.waze_realtime     = Gb.conf_general[CONF_WAZE_REALTIME]
    Gb.waze_region       = Gb.conf_general[CONF_WAZE_REGION]

    Gb.distance_method_waze_flag = Gb.conf_general[CONF_WAZE_USED]
    if Gb.distance_method_waze_flag is False:
        Gb.waze_history_database_used = False
    else:
        Gb.waze_history_database_used = Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED]

    Gb.waze_history_max_distance    = Gb.conf_general[CONF_WAZE_HISTORY_MAX_DISTANCE]
    Gb.waze_history_track_direction = Gb.conf_general[CONF_WAZE_HISTORY_TRACK_DIRECTION]

    # Update Waze & WazeHist with updated parameters
    create_Waze_object()

    if Gb.WazeHist:
        if Gb.waze_history_database_used and Gb.WazeHist.connection is None:
            Gb.WazeHist.open_waze_history_database(Gb.wazehist_database_filename)
        if Gb.waze_history_database_used is False and Gb.WazeHist.connection:
            Gb.WazeHist.close_waze_history_database()

#------------------------------------------------------------------------------
def set_zone_display_as():
    '''
    Set the zone display_as config format. Refresh the display_as for each zone if the
    config format value changed. But don't do this on the initial load. It will be
    done when the zone is created.

    '''

    if Gb.initial_icloud3_loading_flag:
        return

    zone_msg = ''
    Gb.zone_display_as = NON_ZONE_ITEM_LIST.copy()

    for zone, Zone in Gb.Zones_by_zone.items():
        if is_statzone(zone) is False:
            Zone.setup_zone_display_name()

        if Zone.radius_m > 1:
            crlf_dot_x = CRLF_X if Zone.passive else CRLF_DOT
            zone_msg +=(f"{crlf_dot_x}{Zone.zone}, "
                        f"{Zone.display_as}, {Zone.device_tracker_state} "
                        f"(r{Zone.radius_m}m)")

    log_msg =  (f"Set up Zones > zone, Display ({Gb.display_zone_format}), "
                f"device_tracker ({Gb.device_tracker_state_format})")
    post_event(f"{log_msg}{zone_msg}")

#------------------------------------------------------------------------------
#
#   ICLOUD3 CONFIGURATION PARAMETERS WERE UPDATED VIA CONFIG_FLOW
#
#   Determine the type of parameters that were updated and reset the variables or
#   devices based on the type of changes.
#
#------------------------------------------------------------------------------
def process_config_flow_parameter_updates():

    if 'restart' in Gb.config_flow_updated_parms:
        set_icloud_username_password()
        Gb.start_icloud3_request_flag = True
        if 'profile' in Gb.config_flow_updated_parms:
            Gb.EvLog.display_user_message('The Browser may need to be refreshed')
        return

    post_event(f"{EVLOG_IC3_STAGE_HDR}Configuration Update - Complete")
    if 'general' in Gb.config_flow_updated_parms:
        set_global_variables_from_conf_parameters()

    if 'zone_formats' in Gb.config_flow_updated_parms:
        set_zone_display_as()

    if 'profile' in Gb.config_flow_updated_parms:
        post_event('Processing Event Log Profile Update')
        check_ic3_event_log_file_version()
        Gb.hass.loop.create_task(update_lovelace_resource_event_log_js_entry())
        Gb.EvLog.setup_event_log_trackable_device_info()
        if 'profile' in Gb.config_flow_updated_parms:
            Gb.EvLog.display_user_message('The Browser may need to be refreshed')

    if 'reauth' in Gb.config_flow_updated_parms:
        Gb.evlog_action_request = CMD_RESET_PYICLOUD_SESSION

    if 'waze' in Gb.config_flow_updated_parms:
        set_waze_conf_parameters()

    if 'tracking' in Gb.config_flow_updated_parms:
        set_icloud_username_password()

    elif 'devices' in Gb.config_flow_updated_parms:
        set_icloud_username_password()
        pass

    post_event(f"{EVLOG_IC3_STAGE_HDR}Configuration Update - Started")
    Gb.config_flow_updated_parms = {''}
#------------------------------------------------------------------------------
#
#   LOAD HA CONFIGURATION.YAML FILE
#
#   Load the configuration.yaml file and save it's contents. This contains the default
#   parameter values used to reset the configuration when iCloud3 is restarted.
#
#   'load_ha_config_parameters' is run in device_tracker.__init__ when iCloud3 starts
#   'reinitialize_config_parameters' is run in device_tracker.start_icloud3 when iCloud3
#   starts or is restarted before the config_ic3.yaml parameter file is processed
#
#------------------------------------------------------------------------------
def load_ha_config_parameters(ha_config_yaml_and_defaults):
    Gb.config_parm_initial_load = {k:v for k, v in ha_config_yaml_and_defaults.items()}
    _traceha(f"{Gb.config_parm_initial_load=}")
    reinitialize_config_parameters()

def reinitialize_config_parameters():
    _traceha(f"{Gb.config_parm_initial_load=}")
    _traceha(f"{Gb.config_parm=}")
    Gb.config_parm = Gb.config_parm_initial_load.copy()

#------------------------------------------------------------------------------
#
#   CHECK THE IC3 EVENT LOG VERSION BEING USED
#
#   Read the icloud3-event-log-card.js file in the iCloud3 directory and the
#   Lovelace Custom Card directory (default=www/custom_cards) and extract
#   the current version (Version=x.x.x (mm.dd.yyyy)) comment entry before
#   the first 'class' statement. If the version in the ic3 directory is
#   newer than the www/custom_cards directory, copy the ic3 version
#   to the www/custom_cards directory.
#
#   The custom_cards directory can be changed using the event_log_card_directory
#   parameter.
#
#------------------------------------------------------------------------------
def check_ic3_event_log_file_version():
    try:
        ic3_evlog_js_directory = Gb.hass.config.path(Gb.icloud3_directory, 'event_log_card')
        ic3_evlog_js_filename  = Gb.hass.config.path(Gb.icloud3_directory, 'event_log_card',
                                                        Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM])
        www_evlog_js_directory = Gb.hass.config.path(Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY])
        www_evlog_js_filename  = Gb.hass.config.path(Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY],
                                                        Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM])

        # The _l is a html command and will stop the msg from displaying
        ic3_evlog_js_directory_msg = "icloud3/event_log_card".replace('_log', '___log')
        ic3_evlog_js_filename_msg  = ic3_evlog_js_filename.replace('_log', '___log')
        www_evlog_js_directory_msg = www_evlog_js_directory.replace('_log', '___log')
        www_evlog_js_filename_msg  = www_evlog_js_filename.replace('_log', '___log')

        ic3_version, ic3_beta_version, ic3_version_text = _read_event_log_card_js_file(ic3_evlog_js_filename)
        www_version, www_beta_version, www_version_text = _read_event_log_card_js_file(www_evlog_js_filename)

        if ic3_version_text == 'Not Installed':
            Gb.version_evlog = f' Not Found: {ic3_evlog_js_filename_msg}'
            event_msg =(f"iCloud3 Event Log > "
                        f"{CRLF_DOT}Current Version Installed-v{www_version_text}"
                        f"{CRLF_DOT}WARNING: SOURCE FILE NOT FOUND"
                        f"{CRLF_DOT}...{ic3_evlog_js_filename_msg}")
            post_event(event_msg)
        else:
            Gb.version_evlog = ic3_version_text

        # Event log card is not in iCloud3 directory. Nothing to do.
        if ic3_version == 0:
            return

        # Event Log card does not exist in www directory. Copy it from iCloud3 directory
        if www_version == 0:
            try:
                os.mkdir(Gb.www_evlog_js_directory)
            except FileExistsError:
                pass
            except Exception as err:
                log_exception(err)
                pass

        current_version_installed_flag = True
        if ic3_version > www_version:
            current_version_installed_flag = False
        elif ic3_version == www_version:
            if ic3_beta_version == 0:
                pass
            elif ic3_beta_version > www_beta_version:
                current_version_installed_flag = False

        if current_version_installed_flag:
            event_msg =(f"iCloud3 Event Log > "
                        f"{CRLF_DOT}Current Version Installed-v{www_version_text}"
                        f"{CRLF_DOT}File-{www_evlog_js_filename_msg}")
            post_event(event_msg)

            return

        try:
            _copy_image_files_to_www_directory(www_evlog_js_directory)
            shutil.copy(ic3_evlog_js_filename, www_evlog_js_filename)

            event_msg =(f"{EVLOG_ALERT}"
                        f"Event Log Alert > iCloud3 Event Log was updated to v{ic3_version_text}"
                        f"{CRLF_DOT}Refresh your browser >"
                        f"{CRLF_HDOT}Ctrl_Shift_Del, Clear Data, Refresh"
                        f"{CRLF_DOT}Refresh the iOS App on iPhones, iPads, etc"
                        f"{CRLF_HDOT}HA Sidebar, Configuration, Companion App"
                        f"{CRLF_HDOT}Debugging, Reset frontend cache, Settings, Done"
                        f"{CRLF_HDOT}Close Companion App, Redisplay iCloud3 screen"
                        f"{CRLF_HDOT}Refresh, Pull down from the top, Spinning wheel, Done"
                        f"{CRLF}{'-'*80}"
                        f"{CRLF_DOT}Old Version.. - v{www_version_text}"
                        f"{CRLF_DOT}New Version - v{ic3_version_text}"
                        f"{CRLF_DOT}Copied From - /config/.../{ic3_evlog_js_directory_msg}/"
                        f"{CRLF_DOT}Copied To.... - {www_evlog_js_directory_msg}/")
            post_event(event_msg)

            Gb.info_notification = (f"Event Log Card updated to v{ic3_version_text}. "
                        "See Event Log for more info.")
            title       = (f"iCloud3 Event Log Card updated to v{ic3_version_text}")
            message     = ("Refresh the iOS App to load the new version. "
                        "Select HA Sidebar > APP Configuration. Scroll down. Select Refresh "
                        "Frontend Cache. Select Done. Pull down to refresh App.")
            Gb.broadcast_msg = {
                        "title": title,
                        "message": message,
                        "data": {"subtitle": "Event Log needs to be refreshed"}}

        except Exception as err:
            log_exception(err)

    except Exception as err:
        log_exception(err)

#------------------------------------------------------------------------------
def _read_event_log_card_js_file(evlog_filename):
    '''
    Read the records in the the evlog_filename extract the version in the record
    with the javascript 'const version' in it (const version = '3.1.28' or '3.1.28b1').

    Return:
        version - A numeric value of the version text (3.1.28 = 30128
        version_beta - Value after the 'b' or '' if not a beta
        version_beta_text - Value in the 'const version' statement

        0, 0, "Unknown" if the 'const version' was not found
        0, 0, "Not Installed" if the 'icloud3-event-log-card.js' file was not found
    '''
    try:
        if os.path.exists(evlog_filename) == False:
            return (0, 0, 'Not Installed')

        #Cycle thru the file looking for the line with the 'const version'
        evlog_file = open(evlog_filename)

        recd_no = 0
        for evlog_recd in evlog_file:
            recd_no += 1

            if instr(evlog_recd, 'const version'):
                break

            #exit if find 'class' recd before 'version' recd
            elif recd_no > 50:
                return (0, 0, ' Unknown')

        evlog_recd          = evlog_recd.replace(' ', '').replace('"','|').replace("'","|")
        version_number_beta = evlog_recd.split('|')[1]

        if instr(version_number_beta, 'b'):
            version_number      = version_number_beta.split('b')[0]
            version_beta        = int(version_number_beta.split('b')[1])
        else:
            version_number      = version_number_beta
            version_beta        = 0

        version_parts = (f"{version_number}.0.0").split('.')
        version  = 0
        version += int(version_parts[0])*10000
        version += int(version_parts[1])*100
        version += int(version_parts[2])*1

    except FileNotFoundError:
        return (0, 0, 'Not Installed')

    except Exception as err:
        log_exception(err)
        return (0, 0, ERROR)

    evlog_file.close()

    return (version, version_beta, version_number_beta)

#------------------------------------------------------------------------------
def _copy_image_files_to_www_directory(www_evlog_directory):
    '''
    Copy any image files from the icloud3/event_log directory to the /www/[event_log_directory]
    '''
    try:
        image_extensions = ['png', 'jpg', 'jpeg']
        image_filenames = [f'{Gb.icloud3_directory}/event_log_card/{x}'
                                    for x in os.listdir(f"{Gb.icloud3_directory}/event_log_card/")
                                    if instr(x, '.') and x.rsplit('.', 1)[1] in image_extensions]

        for image_filename in image_filenames:
            shutil.copy(image_filename, www_evlog_directory)

    except Exception as err:
        log_exception(err)
        return

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   LOAD THE ZONE DATA FROM HA
#
#   Retrieve the zone entity attributes from HA and initialize Zone object
#   that is used when a Device is located
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_Zones_object():
    '''
    Get the zone names from HA, fill the zone tables
    '''

    try:
        if Gb.initial_icloud3_loading_flag is False:
            Gb.hass.services.call(ZONE, "reload")
    except:
        pass

    #log_msg = (f"Reloading Zone.yaml config file")
    #log_debug_msg(log_msg)

    zone_entities = Gb.hass.states.entity_ids(ZONE)
    er_zones, zone_entity_data = entity_io.get_entity_registry_data(platform=ZONE)

    Gb.state_to_zone = STATE_TO_ZONE_BASE.copy()
    OldZones_by_zone = Gb.Zones_by_zone.copy()

    Gb.Zones = []
    Gb.Zones_by_zone = {}
    Gb.zone_display_as = NON_ZONE_ITEM_LIST.copy()

    # Add away, not_set, not_home, stationary, etc. so display_name is set
    # for these zones/states. Radius=0 is used to ypass normal zone processing.
    for zone, display_as in NON_ZONE_ITEM_LIST.items():
        # if zone.lower() in Gb.Zones_by_zone:
        #     continue

        if zone in OldZones_by_zone:
            Zone = OldZones_by_zone[zone]
        else:
            zone_data ={ZONE: zone, NAME: display_as, TITLE: display_as, FNAME: display_as,
                        FRIENDLY_NAME: display_as, RADIUS: 0}
            Zone = iCloud3_Zone(zone, zone_data)

        Gb.Zones.append(Zone)
        Gb.Zones_by_zone[zone] = Zone

    zone_msg = ''
    for zone in er_zones:
        try:
            zone_entity_name = f"zone.{zone}"
            zone_data = entity_io.get_attributes(zone_entity_name)
            if (zone_entity_name in zone_entity_data
                    and ID in zone_entity_data[zone_entity_name]):
                zone_data[ZONE] = zone
                zone_data[ID] = zone_entity_data[zone_entity_name][ID]
                zone_data['unique_id'] = zone_entity_data[zone_entity_name]['unique_id']
                zone_data['original_name'] = zone_entity_data[zone_entity_name]['original_name']
            else:
                zone_data[ID] = zone.lower()
                zone_data['unique_id'] = zone.lower()

            #log_debug_msg(f"ZONE.DATA - [zone.{zone}--{zone_data}]")

            if LATITUDE not in zone_data: continue

            # Update Zone data if it already exists, else add a new one
            if zone in OldZones_by_zone:
                if instr(zone, STATIONARY):
                    continue
                Zone = OldZones_by_zone[zone]
                Zone.__init__(zone, zone_data)

            else:
                Zone = iCloud3_Zone(zone, zone_data)

            Gb.Zones.append(Zone)
            Gb.Zones_by_zone[zone] = Zone

            if Zone.radius_m > 0:
                crlf_dot_x = CRLF_X if Zone.passive else CRLF_DOT
                zone_msg +=(f"{crlf_dot_x}{Zone.zone}, "
                            f"{Zone.display_as}, {Zone.device_tracker_state} "
                            f"(r{Zone.radius_m}m)")

            if zone == HOME:
                Gb.HomeZone = Zone

                if (float(Gb.stat_zone_base_latitude) == int(Gb.stat_zone_base_latitude)
                        or Gb.stat_zone_base_latitude < 25):
                    offset_lat          = float(Gb.stat_zone_base_latitude) * 0.008983
                    offset_long         = float(Gb.stat_zone_base_longitude) * 0.010094
                    Gb.stat_zone_base_latitude  = Gb.HomeZone.latitude  + offset_lat
                    Gb.stat_zone_base_longitude = Gb.HomeZone.longitude + offset_long

        except Exception as err:
            log_exception(err)

    log_msg =  (f"Set up Zones > zone, Display ({Gb.display_zone_format}), "
                f"device_tracker ({Gb.device_tracker_state_format})")
    post_event(f"{log_msg}{zone_msg}")

    if Gb.track_from_base_zone != HOME:
        event_msg = (   f"Primary 'Home' Zone > {zone_display_as(Gb.track_from_base_zone)} "
                        f"{circle_letter(Gb.track_from_base_zone)}")
        post_event(event_msg)


    event_msg = "Special Zone Setup >"
    if Gb.is_passthru_zone_used:
        event_msg += f"{CRLF_DOT}PassThru Zone > Delay-{secs_to_time_str(Gb.passthru_zone_interval_secs)}"
    else:
        event_msg += f"{CRLF_DOT}PASSTHRU ZONE IS NOT BEING USED"

    dist = Gb.HomeZone.distance_km(Gb.stat_zone_base_latitude, Gb.stat_zone_base_longitude)
    home_zone_radius_km   = Gb.HomeZone.radius_km
    min_dist_from_zone_km = round(home_zone_radius_km * 2, 2)
    dist_move_limit       = round(home_zone_radius_km * 1.5, 2)

    if Gb.is_stat_zone_used:
        event_msg += (  f"{CRLF_DOT}Stationary Zone > "
                        f"Radius-{Gb.HomeZone.radius_m * 2}m, "
                        f"DistMoveLimit-{format_dist_km(dist_move_limit)}, "
                        f"MinDistFromAnotherZone-{format_dist_km(min_dist_from_zone_km)}, "
                        f"BaseDistFromHome-{format_dist_km(dist)}, "
                        f"BaseLocation-{format_gps(Gb.stat_zone_base_latitude, Gb.stat_zone_base_longitude, 0)}")
    else:
        event_msg += f"{CRLF_DOT}STATIONARY ZONES ARE NOT BEING USED"

    post_event(event_msg
    )
    # Cycle thru the Device's conf and get all zones that are tracked from for all devices
    Gb.TrackedZones_by_zone = {}
    for conf_device in Gb.conf_devices:
        for from_zone in conf_device[CONF_TRACK_FROM_ZONES]:
            Gb.TrackedZones_by_zone[from_zone] = Gb.Zones_by_zone[from_zone]

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 1
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#------------------------------------------------------------------------------
#
#   INITIALIZE THE WAZE FIELDS
#
#------------------------------------------------------------------------------
def create_Waze_object():
    '''
    Create the Waze object even if Waze is not used.
    Also st up the WazeHist object here to keep object creation together
    '''
    try:
        if Gb.Waze:
            Gb.Waze.__init__(   Gb.distance_method_waze_flag,
                                Gb.waze_min_distance,
                                Gb.waze_max_distance,
                                Gb.waze_realtime,
                                Gb.waze_region)
            Gb.WazeHist.__init__(
                                Gb.waze_history_database_used,
                                Gb.waze_history_max_distance,
                                Gb.waze_history_track_direction)
        else:
            Gb.Waze = Waze(     Gb.distance_method_waze_flag,
                                Gb.waze_min_distance,
                                Gb.waze_max_distance,
                                Gb.waze_realtime,
                                Gb.waze_region)
            Gb.WazeHist = WazeHist(
                                Gb.waze_history_database_used,
                                Gb.waze_history_max_distance,
                                Gb.waze_history_track_direction)

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 2
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#------------------------------------------------------------------------------
#
#   CREATE THE DEVICES OBJECT FROM THE DEVICE PARAMETERS IN THE
#   CONFIGURATION FILE
#
#   Set up the devices to be tracked and it's associated information
#   for the configuration line entry. This will fill in the following
#   fields based on the extracted devicename:
#       device_type
#       friendly_name
#       fmf email address
#       sensor.picture name
#       device tracking flags
#       tracked_devices list
#   These fields may be overridden by the routines associated with the
#   operating mode (fmf, icloud, iosapp)
#
#------------------------------------------------------------------------------
def create_Devices_object():

    try:
        device_tracker_entities, device_tracker_entity_data = \
                entity_io.get_entity_registry_data(platform='icloud3', domain=DEVICE_TRACKER)

        old_Devices_by_devicename = Gb.Devices_by_devicename.copy()
        Gb.Devices               = []
        Gb.conf_devicenames      = []
        Gb.conf_famshr_devicenames = []
        Gb.Devices_by_devicename = {}
        # Gb.TrackedZones_by_zone  = {}
        # if Gb.track_from_base_zone != HOME and Gb.track_from_home_zone:
        #     Gb.TrackedZones_by_zone[HOME] = Gb.HomeZone

        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            Gb.conf_famshr_devicenames.append(conf_device[CONF_FAMSHR_DEVICENAME])
            broadcast_info_msg(f"Set up Device > {devicename}")

            if conf_device[CONF_TRACKING_MODE] ==  INACTIVE_DEVICE:
                event_msg = (f"{CIRCLE_X}{devicename} > {conf_device[CONF_FNAME]}/{conf_device[CONF_DEVICE_TYPE]}, INACTIVE, "
                            f"{CRLF_NBSP6_DOT}FamShr Device-{conf_device[CONF_FAMSHR_DEVICENAME]}"
                            f"{CRLF_NBSP6_DOT}FmF Device-{conf_device[CONF_FMF_EMAIL]}"
                            f"{CRLF_NBSP6_DOT}iOSApp Entity-{conf_device[CONF_IOSAPP_DEVICE]}")
                post_event(event_msg)
                continue

            # Reinitialize or add device, preserve the Sensor object if reinitializing
            if devicename in old_Devices_by_devicename:
                Device = old_Devices_by_devicename[devicename]
                Device.__init__(devicename, conf_device)
                post_monitor_msg(f"INITIALIZED Device-{devicename}")
            else:
                Device = iCloud3_Device(devicename, conf_device)
                post_monitor_msg(f"ADDED Device-{devicename}")

            Gb.Devices.append(Device)
            Gb.conf_devicenames.append(devicename)
            Gb.Devices_by_devicename[devicename] = Device

            famshr_dev_msg = Device.conf_famshr_name if Device.conf_famshr_name else 'None'
            fmf_dev_msg    = Device.conf_fmf_email if Device.conf_fmf_email else 'None'
            iosapp_dev_msg = Device.iosapp_entity[DEVICE_TRACKER] \
                                    if Device.iosapp_entity[DEVICE_TRACKER] else 'NotMonitored'
            monitored_msg  = '(Monitored)' if Device.is_monitored else '(Tracked)'

            event_msg = (   f"{CHECK_MARK}{devicename} > {Device.fname_devtype} {monitored_msg}"
                            f"{CRLF_NBSP6_DOT}FamShr Device: {famshr_dev_msg}"
                            f"{CRLF_NBSP6_DOT}FmF Device: {fmf_dev_msg}"
                            f"{CRLF_NBSP6_DOT}iOSApp Entity: {iosapp_dev_msg}")

            if Device.track_from_base_zone != HOME:
                event_msg += f"{CRLF_NBSP6_DOT}Primary 'Home' Zone: {zone_display_as(Device.track_from_base_zone)}"
            if Device.track_from_zones != [HOME]:
                event_msg += f"{CRLF_NBSP6_DOT}Track from Zones: {', '.join(Device.track_from_zones)}"
            post_event(event_msg)

            try:
                # 12/19/2022 (beta 3)-Added the try/except to not generate an error if the device was not in the registry
                # Get the ha device_registry device_id
                Device.ha_device_id = device_tracker_entity_data[f"{DEVICE_TRACKER_DOT}{devicename}"]['device_id']
            except:
                pass

            # Initialize device_tracker entity to display before PyiCloud starts up
            Device.write_ha_device_tracker_state()

    except Exception as err:
        log_exception(err)

    return

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 4
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def setup_tracked_devices_for_famshr(PyiCloud=None):
    '''
    The Family Share device data is available from PyiCloud when logging into the iCloud
    account. This routine will get all the available FamShr devices from this data.
    The raw data devices are then cycled through and matched with the conf tracked devices.
    Their status is displayed on the Event Log. The device is also marked as verified.

    Arguments:
        PyiCloud: Object containing data to be processed. This might be from Gb.PyiCloud (normal/default)
                    or the one created in config_flow if the username was changed.
    '''
    broadcast_info_msg(f"Stage 3 > Set up Family Share Devices")
    if PyiCloud is None:
        PyiCloud = Gb.PyiCloud
    if PyiCloud is None:
        return

    PyiCloud = Gb.PyiCloud
    _FamShr = PyiCloud.FamilySharing

    event_msg = "Family Sharing devices > "
    if Gb.conf_famshr_device_cnt == 0:
        event_msg += "No FamShr devices configured"
        post_event(event_msg)
        return

    elif _FamShr is None or _FamShr.device_fname_by_device_id == {}:
        event_msg += "NO DEVICES FOUND"
        post_event(event_msg)
        return

    for _RawData in PyiCloud.RawData_by_device_id.values():
        if _RawData.fname_dup_suffix:
            dup_msg = ( f"{EVLOG_NOTICE}Duplicate FamShr device name found > Reassigned"
                        f"{CRLF_DOT}{_RawData.name}{RARROW}{_RawData.fname}")
            post_event(dup_msg)

    Gb.famshr_device_verified_cnt = 0

    try:
        # Cycle thru the devices from those found in the iCloud data. We are not cycling
        # through the PyiCloud_RawData so we get devices without location info
        sorted_device_id_by_device_fname = OrderedDict(sorted(_FamShr.device_id_by_device_fname.items()))
        for device_fname, device_id in sorted_device_id_by_device_fname.items():
            exception_msg = ''

            try:
                raw_model, model, model_display_name = \
                                        _FamShr.device_model_info_by_fname[device_fname]
            except:
                log_debug_msg(  f"Error extracting device info, "
                                f"source-{_FamShr.device_model_info_by_fname[device_fname]}, "
                                f"fname-{device_fname}, "
                                f"desc-{model_display_name}, "
                                f"raw_model-{raw_model}")
                continue

            broadcast_info_msg(f"Set up FamShr Device > {device_fname}")

            _RawData    = PyiCloud.RawData_by_device_id_famshr.get(device_id, None)
            conf_device = _verify_conf_device(device_fname, device_id, _FamShr)

            devicename = conf_device.get(CONF_IC3_DEVICENAME, 'Not Tracked')

            if _RawData is None:
                exception_msg += 'Not Tracked, '

            elif conf_device.get(CONF_TRACKING_MODE, False) == INACTIVE_DEVICE:
                exception_msg += 'INACTIVE, '

            if (instr(device_fname, '*' )
                    or instr(exception_msg, "INACTIVE")
                    or instr(exception_msg, "NO LOCATION")):
                device_fname = device_fname.replace('*', '')
                crlf_mark = CRLF_X
            else:
                crlf_mark = CRLF_DOT

            if exception_msg:
                event_msg += (  f"{crlf_mark}"
                                f"{device_fname}{RARROW}{exception_msg}"
                                f"{model_display_name} ({raw_model})")
                continue

            # If no location info in pyiCloud data but tracked device is matched, refresh the
            # data and see if it is locatable now. If so, all is OK. If not, set to verified but
            # display no location exception msg in EvLog
            exception_msg = ''
            if _RawData.is_location_data_available is False:
                exception_msg = f", NO LOCATION DATA"

                PyiCloud.FamilySharing.refresh_client()

            if _RawData and Gb.log_rawdata_flag:
                log_title = (   f"FamShr PyiCloud Data (device_data -- "
                                f"{devicename}/{device_fname}), "
                                f"{model_display_name} ({raw_model})")
                log_rawdata(log_title, {'data': _RawData.device_data})

            device_type = ''
            if devicename in Gb.Devices_by_devicename:
                Device                  = Gb.Devices_by_devicename[devicename]
                device_type             = Device.device_type
                Device.verified_flag    = True
                Device.device_id_famshr = device_id
                Gb.Devices_by_icloud_device_id[device_id] = Device
                Gb.famshr_device_verified_cnt += 1

                crlf_mark = CRLF_CHK

            elif (instr(exception_msg, "INACTIVE")
                    or instr(exception_msg, "TRACKING DISABLED")
                    or instr(exception_msg, "NO LOCATION")):
                crlf_mark = CRLF_X

            else:
                crlf_mark = CRLF_DOT

            event_msg += (  f"{crlf_mark}"
                            f"{device_fname}{RARROW}{devicename}, "
                            f"{model_display_name} ({raw_model})"
                            f"{exception_msg}")

        post_event(event_msg)

        return

    except Exception as err:
        log_exception(err)

        event_msg =(f"iCloud3 Error from iCloud Loc Svcs > "
            "Error Authenticating account or no data was returned from "
            "iCloud Location Services. iCloud access may be down or the "
            "Username/Password may be invalid.")
        post_error_msg(event_msg)

    return

#--------------------------------------------------------------------
def _verify_conf_device(device_fname, device_id, _FamShr):
    '''
    Get the this famshr device's configuration item. Then see if the raw_model, model
    or model_display_name has changed. If so, update it in the configuration file.

    Return:
        conf_device configuration item or {} if it is not being tracked
    '''
    # Cycle through the config tracked devices and find the matching device.
    update_conf_file_flag = False
    try:
        conf_device = [cd_item  for cd_item in Gb.conf_devices
                                if device_fname == cd_item[CONF_FAMSHR_DEVICENAME]][0]
    except:
        return {}

    # Get the model info from PyiCloud data and update it if necessary
    raw_model, model, model_display_name = \
                    _FamShr.device_model_info_by_fname[device_fname]

    if (conf_device[CONF_RAW_MODEL] != raw_model
            or conf_device[CONF_MODEL] != model
            or conf_device[CONF_MODEL_DISPLAY_NAME] != model_display_name):
        conf_device[CONF_RAW_MODEL] = raw_model
        conf_device[CONF_MODEL] = model
        conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name
        update_conf_file_flag = True

    if conf_device[CONF_FAMSHR_DEVICE_ID] != device_id:
        conf_device[CONF_FAMSHR_DEVICE_ID] = device_id

    if update_conf_file_flag:
        config_file.write_storage_icloud3_configuration_file()

    return conf_device

#--------------------------------------------------------------------
def setup_tracked_devices_for_fmf(PyiCloud=None):
    '''
    The Find-my-Friends device data is available from PyiCloud when logging into the iCloud
    account. This routine will get all the available FmF devices from the email contacts/following/
    followed data. The devices are then cycled through to be matched with the tracked devices
    and their status is displayed on the Event Log. The device is also marked as verified.

    Arguments:
        PyiCloud: Object containing data to be processed. This might be from Gb.PyiCloud (normal/default)
                    or the one created in config_flow if the username was changed.
    '''
    broadcast_info_msg(f"Stage 3 > Set up Find-my-Friends Devices")

    # devices_desc             = get_fmf_devices(PyiCloud)
    # device_id_by_fmf_email   = devices_desc[0]
    # fmf_email_by_device_id   = devices_desc[1]
    # device_info_by_fmf_email = devices_desc[2]

    if PyiCloud is None:
        PyiCloud = Gb.PyiCloud
    if PyiCloud is None:
        return

    PyiCloud = Gb.PyiCloud
    _FmF = PyiCloud.FindMyFriends

    event_msg = "Find-My-Friends devices > "
    if Gb.conf_fmf_device_cnt == 0:
        event_msg += "No FmF devices configured"
        post_event(event_msg)
        return

    elif _FmF is None or _FmF.device_id_by_fmf_email == {}:
        event_msg += "NO DEVICES FOUND"
        post_event(event_msg)
        return

    try:
        Gb.fmf_device_verified_cnt = 0

        # Cycle through all the FmF devices in the iCloud account
        exception_event_msg = ''
        device_fname_by_device_id = {}
        sorted_device_id_by_fmf_email = OrderedDict(sorted(_FmF.device_id_by_fmf_email.items()))
        for fmf_email, device_id in sorted_device_id_by_fmf_email.items():
            broadcast_info_msg(f"Set up FmF Device > {fmf_email}")
            devicename    = ''
            device_fname  = ''
            _RawData      = None
            exception_msg = ''

            # Cycle througn the tracked devices and find the matching device
            # Verify the device_id in the configuration with the found
            # device and display a configuration error msg later if something
            # doesn't match
            for device in Gb.conf_devices:
                conf_fmf_email = device[CONF_FMF_EMAIL].split(" >")[0].strip()

                if conf_fmf_email == fmf_email:
                    devicename   = device[CONF_IC3_DEVICENAME]
                    device_fname = device[CONF_FNAME]
                    device_type  = device[CONF_DEVICE_TYPE]
                    _RawData = PyiCloud.RawData_by_device_id_fmf[device_id]

                    if device[CONF_FMF_DEVICE_ID] != device_id:
                        device[CONF_FMF_DEVICE_ID] = device_id
                    break

            crlf_mark = CRLF_DOT
            if _RawData is None:
                exception_msg = 'Not Tracked'

            elif device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
                exception_msg = 'INACTIVE'
                crlf_mark = CRLF_X

            if exception_msg:
                exception_event_msg += (f"{crlf_mark}{fmf_email}{RARROW}{exception_msg}")
                continue

            # If no location info in pyiCloud data but tracked device is matched, refresh the
            # data and see if it is locatable now. If so, all is OK. If not, set to verified but
            # display no location exception msg in EvLog
            exception_msg = ''
            if _RawData.is_location_data_available is False:
                exception_msg = f", NO LOCATION DATA"

                PyiCloud.FindMyFriends.refresh_client()

            if _RawData and Gb.log_rawdata_flag:
                log_title = (f"FmF PyiCloud Data (device_data -- {devicename}/{fmf_email})")
                log_rawdata(log_title, {'data': _RawData.device_data})

            device_type = ''
            # The tracked or monitored device has been matched with available devices, mark it as verified.
            if devicename in Gb.Devices_by_devicename:
                Device               = Gb.Devices_by_devicename[devicename]
                device_fname_by_device_id[device_id] = Device.fname
                device_type          = Device.device_type
                Device.verified_flag = True
                Device.device_id_fmf = device_id
                Gb.Devices_by_icloud_device_id[device_id] = Device
                Gb.fmf_device_verified_cnt += 1

                event_msg += (  f"{CRLF_CHK}"
                                f"{fmf_email}{RARROW}{devicename}, "
                                f"{DEVICE_TYPE_FNAME.get(device_type, device_type)}"
                                f"{exception_msg}")
            else:
                event_msg += (  f"{CRLF_X}"
                                f"{fmf_email}{RARROW}{devicename}, "
                                f"{DEVICE_TYPE_FNAME.get(device_type, device_type)}"
                                f"{exception_msg}")

        # Replace known device_ids whith the actual name
        for device_id, device_fname in device_fname_by_device_id.items():
            exception_event_msg = exception_event_msg.replace(  f"({device_id})", \
                                                                f"({device_fname_by_device_id[device_id]})")

        # Remove any unknown device_ids
        for device_id, fmf_email in _FmF.fmf_email_by_device_id.items():
            exception_event_msg = exception_event_msg.replace(f"({device_id})", "")

        event_msg += exception_event_msg
        post_event(event_msg)

        return

    except Exception as err:
        log_exception(err)

        event_msg =(f"iCloud3 Error from iCloud Loc Svcs > "
            "Error Authenticating account or no data was returned from "
            "iCloud Location Services. iCloud access may be down or the "
            "Username/Password may be invalid.")
        post_error_msg(event_msg)

    return

#----------------------------------------------------------------------
def get_famshr_devices_pyicloud(PyiCloud):
    '''
    The device information tables are built when the devices are added the when
    the FamilySharing object and RawData objects are created when logging into
    the iCloud account.
    '''
    if PyiCloud is None: PyiCloud = Gb.PyiCloud

    _FamShr = PyiCloud.FamilySharing
    return [_FamShr.device_id_by_device_fname,
            _FamShr.device_fname_by_device_id,
            _FamShr.device_info_by_device_fname,
            _FamShr.device_model_info_by_fname]

#----------------------------------------------------------------------
def get_fmf_devices_pyicloud(PyiCloud):
    '''
    The device information tables are built when the devices are added the when
    the FamilySharing object and RawData objects are created when logging into
    the iCloud account.
    '''

    if PyiCloud is None: PyiCloud = Gb.PyiCloud

    _FmF = PyiCloud.FindMyFriends
    return (_FmF.device_id_by_fmf_email,
            _FmF.fmf_email_by_device_id,
            _FmF.device_info_by_fmf_email)


#--------------------------------------------------------------------
def set_device_tracking_method_iosapp():
    '''
    The Global tracking method is iosapp so set all Device's tracking method
    to iosapp
    '''
    if Gb.data_source_use_iosapp is False:
        return

    for Device in Gb.Devices:
        Device.tracking_method = 'iosapp'

#--------------------------------------------------------------------
def set_device_tracking_method_famshr_fmf(PyiCloud=None):
    '''
    The goal is to get either all fmf or all famshr to minimize the number of
    calls to iCloud Web Services by pyicloud_ic3. Look at the fmf and famshr
    devices to see if:
    1. If all devices are fmf or all devices are famshr:
            Do not make any changes
    2. If set to fmf but it also has a famshr id, change to famshr.
    2. If set to fmf and no famshr id, leave as fmf.
    '''
    broadcast_info_msg(f"Stage 3 > Set up device data source")

    try:
        if Gb.Devices_by_devicename == {}:
            return

        if PyiCloud is None: PyiCloud = Gb.PyiCloud

        Gb.Devices_by_icloud_device_id = {}
        devicename_not_tracked = {}
        for devicename, Device in Gb.Devices_by_devicename.items():
            tracking_method = None
            broadcast_info_msg(f"Determine Device Tracking Method >{devicename}")

            if Device.device_id_famshr:
                device_id = Device.device_id_famshr
                if device_id in PyiCloud.RawData_by_device_id:
                    tracking_method = FAMSHR
                    Gb.Devices_by_icloud_device_id[device_id] = Device
                    _RawData = PyiCloud.RawData_by_device_id[device_id]
                    _RawData.Device = Device
                    # _RawData.devicename = devicename
                    Device.PyiCloud_RawData_famshr = _RawData

            if Device.device_id_fmf:
                device_id = Device.device_id_fmf
                if device_id in PyiCloud.RawData_by_device_id:
                    if tracking_method is None:
                        tracking_method = FMF
                    Gb.Devices_by_icloud_device_id[device_id] = Device
                    _RawData = PyiCloud.RawData_by_device_id[device_id]
                    _RawData.Device = Device
                    # _RawData.devicename = devicename
                    Device.PyiCloud_RawData_fmf = _RawData

            if (Device.iosapp_monitor_flag
                    and tracking_method is None):
                tracking_method = IOSAPP

            if tracking_method != IOSAPP:
                if Device.device_id_famshr and Device.device_id_fmf is None:
                    Device.PyiCloud_RawData = Device.PyiCloud_RawData_famshr
                elif Device.device_id_fmf and Device.device_id_famshr is None:
                    Device.PyiCloud_RawData = Device.PyiCloud_RawData_fmf

                info_msg = (f"Set PyiCloud Device Id > {Device.devicename}, "
                            f"TrkMethod-{tracking_method}, "
                            f"{CRLF}FamShr-({Device.device_id8_famshr}), "
                            f"FmF-({Device.device_id8_fmf})")
                post_monitor_msg(info_msg)

            Device.tracking_method = tracking_method

        info_msg = (f"PyiCloud Devices > ")
        for _device_id, _RawData in PyiCloud.RawData_by_device_id.items():
            info_msg += (f"{_RawData.name}/{_device_id[:8]}-{_RawData.tracking_method}, ")
        post_monitor_msg(info_msg)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def tune_device_tracking_method_famshr_fmf():
    '''
    The goal is to get either all fmf or all famshr to minimize the number of
    calls to iCloud Web Services by pyicloud_ic3. Look at the fmf and famshr
    devices to see if:
    1. If all devices are fmf or all devices are famshr:
            Do not make any changes
    2. If set to fmf but it also has a famshr id, change to famshr.
    2. If set to fmf and no famshr id, leave as fmf.
    '''
    broadcast_info_msg(f"Stage 3 > Tune Tracking Method")

    try:
        # Global tracking_method specified, nothing to do
        if Gb.data_source_use_icloud is False:
            return
        elif Gb.Devices_by_devicename == {}:
            return

        cnt_famshr = 0     # famshr is specified as the tracking_method for the device in config
        cnt_fmf    = 0     # fmf is specified as the tracking_method for the device in config
        cnt_famshr_to_fmf = 0
        cnt_fmf_to_famshr = 0

        for devicename, Device in Gb.Devices_by_devicename.items():
            broadcast_info_msg(f"Tune Device Tracking Method > {devicename}")

            if Device.tracking_method_FAMSHR:
                cnt_famshr += 1
            elif Device.tracking_method_FMF:
                cnt_fmf += 1

            # Only count those with no tracking_method config parm
            Devices_famshr_to_fmf = []
            Devices_fmf_to_famshr = []
            if Device.tracking_method_config == '':
                if Device.tracking_method_FAMSHR and Device.device_id_fmf:
                    Devices_fmf_to_famshr.append(Device)
                    cnt_famshr_to_fmf += 1
                elif Device.tracking_method_FMF and Device.device_id_famshr:
                    Devices_famshr_to_fmf.append(Device)
                    cnt_fmf_to_famshr += 1

        if cnt_famshr == 0 or cnt_fmf == 0:
            pass
        elif cnt_famshr_to_fmf == 0 or cnt_fmf_to_famshr == 0:
            pass
        elif cnt_famshr >= cnt_fmf:
            for Device in Devices_fmf_to_famshr:
                Device.tracking_method = FAMSHR
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_fmf)
                Gb.Devices_by_icloud_device_id[Device.device_id_famshr] = Device
        else:
            for Device in Devices_famshr_to_fmf:
                Device.tracking_method = FMF
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_famshr)
                Gb.Devices_by_icloud_device_id[Device.device_id_fmf] = Device
    except:
        pass

#--------------------------------------------------------------------
def setup_tracked_devices_for_iosapp():
    '''
    Get the iOSApp device_tracker entities from the entity registry. Then cycle through the
    Devices being tracked and match them up. Anything left over at the end is not matched and not monitored.
    '''
    devices_desc = iosapp_interface.get_entity_registry_mobile_app_devices()
    iosapp_id_by_iosapp_devicename             = devices_desc[0]
    iosapp_devicename_by_iosapp_id             = devices_desc[1]
    device_info_by_iosapp_devicename           = devices_desc[2]
    device_model_info_by_iosapp_devicename     = devices_desc[3]
    last_updt_trig_by_iosapp_devicename        = devices_desc[4]
    notify_iosapp_devicenames                  = devices_desc[5]
    battery_level_sensors_by_iosapp_devicename = devices_desc[6]
    battery_state_sensors_by_iosapp_devicename = devices_desc[7]

    Gb.iosapp_device_verified_cnt = 0

    not_monitored_iosapp_devices = iosapp_id_by_iosapp_devicename.copy()

    tracked_msg = "iOS App Devices > "

    for devicename, Device in Gb.Devices_by_devicename.items():
        broadcast_info_msg(f"Set up iOS App Devices > {devicename}")

        monitored_iosapp_devices = []
        conf_iosapp_device = Device.iosapp_entity[DEVICE_TRACKER].replace(DEVICE_TRACKER_DOT, '')

        # Set iosapp devicename to icloud devicename if nothing is specified. Set to not monitored
        # if no icloud famshr name
        if conf_iosapp_device in ['', 'None']:
            Device.iosapp_entity[DEVICE_TRACKER] = ''
            continue

        # Check if the specified iosapp device tracker is valid and in the entity registry
        if conf_iosapp_device.startswith('Search: ') is False:
            if conf_iosapp_device not in iosapp_id_by_iosapp_devicename:
                alert_msg =(f"{EVLOG_ALERT}Configuration Alert > {Device.fname_devicename} > "
                            f"The iOS `device_tracker.{conf_iosapp_device}` "
                            f"entity was not found"
                            f"{CRLF_DOT}Verify the iOS App device selected in the configuration")
                post_event(alert_msg)
                continue

            iosapp_devicename = conf_iosapp_device
        else:
            conf_iosapp_device = conf_iosapp_device.replace('Search: ', '')

            monitored_iosapp_devices = [k for k, v in iosapp_id_by_iosapp_devicename.items()
                            if k.startswith(conf_iosapp_device) and v.startswith('DISABLED') is False]

            if len(monitored_iosapp_devices) == 0:
                alert_msg = (f"{EVLOG_ALERT}Configuration Alert > {Device.fname_devicename} > "
                        f"The iOS `device_tracker.{conf_iosapp_device}_???` "
                        f"search failed. No mobile_app entity was found"
                        f"{CRLF_DOT}Verify the iOS App device selected in the configuration")
                post_event(alert_msg)
                continue

            elif len(monitored_iosapp_devices) == 1:
                iosapp_devicename = monitored_iosapp_devices[0]

            elif len(monitored_iosapp_devices) > 1:
                iosapp_devicename = monitored_iosapp_devices[-1]
                alert_msg =(f"{EVLOG_ALERT}Configuration Alert > {Device.fname_devicename} > "
                        f"Search for iOS `device_tracker.{conf_iosapp_device}_???` "
                        f"entity failure. More than one entity found. "
                        f"{CRLF}Review and correct the mobile_app device_tracker entities and delete the older ones. "
                        f"{CRLF}{'-'*25}"
                        f"{CRLF}Count-{len(monitored_iosapp_devices)}, "
                        f"{CRLF}Entities-{', '.join(monitored_iosapp_devices)}, "
                        f"{CRLF}Monitored-{iosapp_devicename}")
                post_event(alert_msg)

            else:
                continue

        if iosapp_id_by_iosapp_devicename[iosapp_devicename].startswith('DISABLED'):
            continue

        Device.verified_flag = True
        Device.iosapp_monitor_flag = True
        Gb.iosapp_device_verified_cnt += 1
        if Device.tracking_method_FAMSHR_FMF is False:
            Device.tracking_method = IOSAPP
        try:
            iosapp_fname = device_info_by_iosapp_devicename[iosapp_devicename].rsplit('(')[0]
        except:
            iosapp_fname = f"{iosapp_devicename.replace('_', ' ').title()}(?)"

        # Set raw_model that will get picked up by device_tracker and set in the device registry if it is still
        # at it's default value. Normally, raw_model is set when setting up FamShr if that is available, FmF does not
        # set raw_model since it is only shared via an email addres or phone number. This will also be saved in the
        # iCloud3 configuration file.
        if Device.raw_model.lower() == Device.device_type:
            raw_model, model, model_display_name = device_model_info_by_iosapp_devicename[iosapp_devicename]
            Device.raw_model = raw_model # iPhone15,2

            for conf_device in Gb.conf_devices:
                if conf_device[CONF_IOSAPP_DEVICE] == iosapp_devicename:
                    conf_device[CONF_RAW_MODEL] = Device.raw_model
                    config_file.write_storage_icloud3_configuration_file()
                    break

        Gb.Devices_by_iosapp_devicename[iosapp_devicename] = Device
        Device.iosapp_entity[DEVICE_TRACKER] = f"device_tracker.{iosapp_devicename}"
        Device.iosapp_entity[TRIGGER]        = f"sensor.{last_updt_trig_by_iosapp_devicename.get(iosapp_devicename)}"
        Device.iosapp_entity[BATTERY_LEVEL]  = f"sensor.{battery_level_sensors_by_iosapp_devicename.get(iosapp_devicename)}"
        Device.iosapp_entity[BATTERY_STATUS] = f"sensor.{battery_state_sensors_by_iosapp_devicename.get(iosapp_devicename)}"

        tracked_msg += (f"{CRLF_CHK}{iosapp_fname} ({iosapp_devicename}){RARROW}{devicename} "
                        f"({Device.raw_model})")

        # Remove the iosapp device from the list since we know it is tracked
        if iosapp_devicename in not_monitored_iosapp_devices:
            not_monitored_iosapp_devices.pop(iosapp_devicename)

    setup_notify_service_name_for_iosapp_devices()

    # Devices in the list were not matched with an iCloud3 device or are disabled
    for iosapp_devicename, iosapp_id in not_monitored_iosapp_devices.items():
        try:
            iosapp_fname = device_info_by_iosapp_devicename[iosapp_devicename].rsplit('(')[0]
        except:
            iosapp_fname = f"{iosapp_devicename.replace('_', ' ').title()}(?)"

        if iosapp_id_by_iosapp_devicename[iosapp_devicename].startswith('DISABLED'):
            tracked_msg += (f"{CRLF_X}{iosapp_fname} ({iosapp_devicename}){RARROW}DISABLED, "
                            f"{device_info_by_iosapp_devicename[iosapp_devicename]}")
        else:
            tracked_msg += (f"{CRLF_DOT}{iosapp_fname} ({iosapp_devicename}){RARROW}Not Monitored, "
                            f"{device_info_by_iosapp_devicename[iosapp_devicename]}")
    post_event(tracked_msg)

    return

#--------------------------------------------------------------------
def setup_notify_service_name_for_iosapp_devices(post_event_msg=False):
    '''
    Get the iOSApp device_tracker entities from the entity registry. Then cycle through the
    Devices being tracked and match them up. Anything left over at the end is not matched and not monitored.

    Parameters:
        post_event_msg -
                Post an event msg indicating the notify device names were set up. This is done
                when they are set up when this is run after HA has started

    '''
    notify_iosapp_devicenames = iosapp_interface.get_mobile_app_notifications()

    setup_msg = ''

    # Cycle thru the ha notify names and match them up with a device. This function runs
    # while iC3 is starting and again when ha has started. HA may run iC3 before
    # 'notify.mobile_app' so running again when ha has started makes sure they are set up.
    for notify_iosapp_devicename in notify_iosapp_devicenames:
        iosapp_devicename = notify_iosapp_devicename.replace('mobile_app_', '')
        for devicename, Device in Gb.Devices_by_devicename.items():
            if instr(iosapp_devicename, devicename) or instr(devicename, iosapp_devicename):
                if Device.iosapp_entity[NOTIFY] == '':
                    Device.iosapp_entity[NOTIFY] = notify_iosapp_devicename
                    setup_msg += (f"{CRLF_DOT}{Device.devicename_fname}{RARROW}{notify_iosapp_devicename}")
                break

    if setup_msg and post_event_msg:
        post_event(f"Delayed iOSApp Notifications Setup Completed > {setup_msg}")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 5
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def remove_unverified_untrackable_devices(PyiCloud=None):

    if PyiCloud is None: PyiCloud = Gb.PyiCloud
    if PyiCloud is None:
        return
    if PyiCloud.FamilySharing is None and PyiCloud.FindMyFriends is None:
        return

    _Devices_by_devicename = Gb.Devices_by_devicename.copy()
    device_removed_flag = False
    alert_msg =(f"{EVLOG_ALERT}Untrackable Device Alert > Devices are not being tracked:")
    for devicename, Device in _Devices_by_devicename.items():
        Device.display_info_msg("Verifing Devices")

        # Device not verified as valid FmF, FamShr or iOSApp device. Remove from devices list
        if (Device.tracking_method is None
                or Device.verified_flag is False):
            device_removed_flag = True
            alert_msg +=(f"{CRLF_DOT}{devicename} ({Device.fname_devtype})")

            devicename = Device.devicename
            if Device.device_id_famshr:
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_famshr)
            if Device.device_id_fmf:
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_fmf)

            Gb.Devices_by_devicename.pop(devicename)

    if device_removed_flag:
        alert_msg +=(f"{CRLF}{DASH_20}"
                    f"{CRLF}This can be caused by:"
                    f"{CRLF_DOT}iCloud3 Device configuration error"
                    f"{CRLF_DOT}No iCloud or iOS App device have been selected"
                    f"{CRLF_DOT}This device is no longer in the FamShr or FmF device list"
                    f"{CRLF_DOT}iCloud or iOS App are not being used to locate devices"
                    f"{CRLF_DOT}iCloud is not responding to location requests"
                    f"{CRLF_DOT}An internal code error occurred")
        post_event(alert_msg)

#------------------------------------------------------------------------------
def identify_tracked_monitored_devices():
    '''
    Cycle thru the devices and determinine the tracked and monitored ones
    '''
    Gb.Devices_by_devicename_tracked   = {}
    Gb.Devices_by_devicename_monitored = {}
    for devicename, Device in Gb.Devices_by_devicename.items():
        if Device.is_tracked:
            Gb.Devices_by_devicename_tracked[devicename] = Device
        else:
            Gb.Devices_by_devicename_monitored[devicename] = Device

#------------------------------------------------------------------------------
def setup_trackable_devices():

    for devicename, Device in Gb.Devices_by_devicename.items():
        Device.display_info_msg(f"Set Trackable Devices > {devicename}")
        tracking_mode = 'Monitored' if Device.is_monitored else 'Tracked'
        event_msg =(f"{tracking_mode} Device > {devicename} ({Device.fname_devtype})")

        if Device.tracking_method_FAMSHR:
            Gb.tracking_method_FAMSHR_used = True
        elif Device.tracking_method_FMF:
            Gb.tracking_method_FMF_used = True

        famshr_icloud_error = fmf_icloud_error = ''
        # if Device.conf_famshr_name != 'None' and Device.device_id_famshr is None:
        #     famshr_icloud_error = "(NOT IN FAMILY SHARE LIST)"
        # if Device.conf_fmf_email != 'None' and Device.device_id_fmf is None:
        #     fmf_icloud_error = "(NO FINDMY APP SHARING INFO)"

        if Device.conf_famshr_name != 'None':
            event_msg += f"{CRLF_DOT}FamShr Device: {Device.conf_famshr_name} {famshr_icloud_error}"
        if Device.conf_fmf_email != 'None':
            event_msg += f"{CRLF_DOT}FmF Device: {Device.conf_fmf_email} {fmf_icloud_error}"

        # Initialize iosapp state & location fields
        if Device.iosapp_monitor_flag:
            Gb.tracking_method_IOSAPP_used = True
            iosapp_attrs = iosapp_data_handler.get_iosapp_device_trkr_entity_attrs(Device)
            if iosapp_attrs:
                iosapp_data_handler.update_iosapp_data_from_entity_attrs(Device, iosapp_attrs)

            event_msg += (  f"{CRLF_DOT}iOSApp Entity: {Device.iosapp_entity[DEVICE_TRACKER]}"
                            f"{CRLF_DOT}Update Trigger: {Device.iosapp_entity[TRIGGER].replace('sensor.', '')}"
                            f"{CRLF_DOT}Battery: {Device.iosapp_entity[BATTERY_LEVEL].replace('sensor.', '')}")
            if Device.iosapp_entity[NOTIFY]:
                event_msg += f"{CRLF_DOT}Notifications: {Device.iosapp_entity[NOTIFY].replace('sensor.', '')}"
            else:
                event_msg += f"{CRLF_DOT}Notifications: WAITING FOR NOTIFY SERVICE TO START"

        # Initialize distance_to_other_devices, add other devicenames to this Device's field
        for _devicename, _Device in Gb.Devices_by_devicename.items():
            if devicename != _devicename:
                Device.dist_to_other_devices[_devicename] = [0, 0, '0m/±0m']
                Device.near_device_distance         = 0       # Distance to the NearDevice device
                Device.near_device_checked_secs     = 0       # When the nearby devices were last updated
                Device.dist_apart_msg               = ''      # Distance to all other devices msg set in icloud3_main
                Device.dist_apart_msg_by_devicename = {}

        # Display all sensor entities early. Value displaye will be '---'
        create_Device_StationaryZone_object(Device)

        info_msg = f"Stationary Zone: {Device.stationary_zonename} ({Device.StatZone.display_as})"
        Device.display_info_msg(f"{info_msg}")
        event_msg += f"{CRLF_DOT}{info_msg}"

        if Device.track_from_base_zone != HOME:
                event_msg += f"{CRLF_DOT}Track from Base Zone: {zone_display_as(Device.track_from_base_zone)}"
        if Device.track_from_zones != [HOME]:
            event_msg += (f"{CRLF_DOT}Track from Zones: {', '.join(Device.track_from_zones)}")

        Device.initialize_usage_counters()

        post_event(event_msg)

#------------------------------------------------------------------------------
def display_inactive_devices():
    '''
    Display a list of the Inactive devices in the Event Log
    '''

    inactive_devices =[(f"{conf_device[CONF_IC3_DEVICENAME]} ("
                        f"{conf_device[CONF_FNAME]}/{conf_device[CONF_DEVICE_TYPE]})")
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE]

    if inactive_devices == []:
        return

    event_msg = f"Inactive/Untracked Devices > "
    event_msg+= list_to_str(inactive_devices, separator=CRLF_X)
    post_event(event_msg)

    if len(inactive_devices) == len(Gb.conf_devices):
        event_msg =(f"{EVLOG_ALERT}All devices are set to INACTIVE. No devices are being tracked. "
                    f"Review and update the devices on the `Devices & Settings > Integrations > "
                    f"iCloud3 Configuration > iCloud3 Devices` screen. For each device:"
                    f"{CRLF}1. Verify the FamShr, FmF and iOS App assigned to the device"
                    f"{CRLF}2. Change the `Tracking Mode` from INACTIVE to Tracked"
                    f"{CRLF}3. Exit the Configuration and Restart iCloud3")
        post_event(event_msg)

#------------------------------------------------------------------------------
def display_object_lists():
    '''
    Display the object list values
    '''
    broadcast_info_msg(f"Logging Initial Monitor Info")
    monitor_msg = (f"StatZones-{Gb.StatZones_by_devicename}")
    post_monitor_msg(monitor_msg)

    monitor_msg = (f"Devices-{Gb.Devices_by_devicename}")
    post_monitor_msg(monitor_msg)

    for Device in Gb.Devices:
        monitor_msg = (f"Device-{Device.devicename}, "
                        f"DeviceFmZones-{Device.DeviceFmZones_by_zone}")
        post_monitor_msg(monitor_msg)

    monitor_msg = (f"Zones-{Gb.Zones_by_zone}")
    post_monitor_msg(monitor_msg)

#------------------------------------------------------------------------------
def create_Device_StationaryZone_object(Device):

    devicename = Device.devicename
    old_StatZones_by_devicename = Gb.StatZones_by_devicename.copy()
    Gb.StatZones = []
    Gb.StatZones_by_devicename = {}

    # Setup Stationary zone for the device, set to base location
    if devicename in old_StatZones_by_devicename:
        StatZone = old_StatZones_by_devicename[devicename]
        StatZone.__init__(Device)
        post_monitor_msg(f"INITIALIZED StationaryZone-{devicename}_stationary")
    else:
        StatZone = iCloud3_StationaryZone(Device)
        post_monitor_msg(f"ADDED StationaryZone-{devicename}_stationary")

    Device.StatZone = StatZone
    Device.StatZone.set_stationary_zone_fname(Device)

    Gb.StatZones.append(StatZone)
    Gb.StatZones_by_devicename[devicename] = StatZone
    Gb.state_to_zone[Device.stationary_zonename] = Device.stationary_zonename

#------------------------------------------------------------------------------
def display_platform_operating_mode_msg():
    if Gb.ha_config_platform_stmt:
        alert_msg = (f"{EVLOG_ALERT}iCloud3 is an HA Integration. Delete the 'platform: icloud3` "
                    "configuration parameters in the HA `configuration.yaml` file.")

        post_event(alert_msg)

#------------------------------------------------------------------------------
def post_restart_icloud3_complete_msg():
    for devicename, Device in Gb.Devices_by_devicename.items():   #
        Device.display_info_msg("Setup Complete, Locating Device")

    event_msg =(f"{EVLOG_IC3_STARTING}Initializing iCloud3 v{Gb.version} > Complete")
    post_event(event_msg)

    Gb.EvLog.update_event_log_display("")