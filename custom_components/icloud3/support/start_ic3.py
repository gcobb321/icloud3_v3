

from ..globals           import GlobalVariables as Gb
from ..const_general     import (HOME, HOME_FNAME, ERROR, NOT_SET, NON_ZONE_ITEM_LIST, CRLF_DOT, UNKNOWN,
                                EVLOG_NOTICE, EVLOG_ALERT, EVLOG_ERROR, LARROW,
                                NAME, TITLE, FNAME, RADIUS, STATE_TO_ZONE_BASE, HIGH_INTEGER, NOT_SET_FNAME,
                                FMF, FAMSHR, FAMSHR_FMF, IOSAPP, ICLOUD, DEVICE_TRACKER, ICLOUD3_ERROR_MSG,
                                CRLF, CRLF_DOT, CRLF_CHK, CRLF_X, NEW_LINE,
                                TRACKING_METHOD_FNAME, WAZE_USED,
                                ICLOUD_EVENT_LOG_CARD_JS, EVLOG_DEBUG, EVLOG_INIT_HDR, DEFAULT_CONFIG_IC3_FILE_NAME,
                                STORAGE_DIR, STORAGE_KEY_ICLOUD, DEBUG_TRACE_CONTROL_FLAG,
                                PLATFORM, ENTITY_ID, NOTIFY, MOBILE_APP,STORAGE_KEY_ENTITY_REGISTRY, )
from ..const_attrs       import (CONF_ZONE, CONF_NAME, CONF_DEVICENAME, ZONE, LATITUDE, DEVICE_ID,
                                LOCATION, ICLOUD_DEVICE_CLASS,
                                CONF_DEVICENAME, CONF_SOURCE, CONF_NAME, CONF_PICTURE, CONF_EMAIL, )

from ..devices           import Devices
from ..zones             import Zones, StationaryZones
from ..support.waze      import Waze
from ..support.waze_history import WazeRouteHistory as WazeHist
from ..support           import icloud as icloud
from ..helpers.base      import (instr,
                                post_event, post_error_msg, post_monitor_msg, post_startup_event,
                                log_info_msg, log_debug_msg, log_rawdata, log_exception,
                                _trace, _traceha, )
from ..helpers.time      import (secs_to_time_str, time_str_to_secs, )
from ..helpers.entity_io import (get_entity_ids, get_attributes, )


import os
import json
import shutil
import homeassistant.util.dt as dt_util
from   homeassistant.util    import slugify
import homeassistant.util.yaml.loader as yaml_loader
from re import match


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 0
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>


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
    reinitialize_config_parameters()

def reinitialize_config_parameters():
    Gb.config_parm = Gb.config_parm_initial_load.copy()

#------------------------------------------------------------------------------
#
#   VARIABLE DEFINITION & INITIALIZATION FUNCTIONS
#
#------------------------------------------------------------------------------
def define_tracking_control_fields():
    Gb.any_device_being_updated_flag   = False
    Gb.trigger                         = {}       #device update trigger
    Gb.info_notification               = ''
    Gb.broadcast_msg                   = ''
    Gb.EvLog.tracking_msg              = ''       #text string used during initialization that is displayed in evlog

#------------------------------------------------------------------------------
#
#   SET GLOBAL VARIABLES BACK TO THEIR INITIAL CONDITION
#
#------------------------------------------------------------------------------
def initialize_global_variables():

    # Configuration parameters that can be changed in config_ic3.yaml
    Gb.um                               = 'mi'
    Gb.time_format                      = 12
    Gb.um_km_mi_factor                  = .62137
    Gb.um_m_ft                          = 'ft'
    Gb.um_kph_mph                       = 'mph'
    Gb.um_time_strfmt                   = '%I:%M:%S'
    Gb.um_time_strfmt_ampm              = '%I:%M:%S%P'
    Gb.um_date_time_strfmt              = '%Y-%m-%d %H:%M:%S'

    # Configuration parameters
    Gb.center_in_zone_flag              = False
    Gb.display_zone_format              = ''
    Gb.max_interval_secs                = 240
    Gb.travel_time_factor               = .6
    Gb.gps_accuracy_threshold           = 100
    Gb.old_location_threshold           = 180
    # Gb.ignore_gps_accuracy_inzone_flag  = False
    Gb.discard_poor_gps_inzone_flag     = True
    # Gb.check_gps_accuracy_inzone_flag   = True
    Gb.hide_gps_coordinates             = False
    Gb.legacy_mode_flag                 = False
    Gb.log_level                        = ''
    Gb.iosapp_request_loc_max_cnt       = HIGH_INTEGER

    Gb.distance_method_waze_flag        = True
    Gb.waze_region                      = 'US'
    Gb.waze_max_distance                = 1000
    Gb.waze_min_distance                = 1
    Gb.waze_realtime                    = False
    Gb.waze_history_max_distance       = 20
    Gb.waze_history_map_track_direction= 'north-south'


    Gb.stationary_still_time_str        = ''
    Gb.stationary_zone_offset           = 0
    Gb.stationary_inzone_interval_str   = ''

    # Variables used to config the device variables when setting up
    # intervals and determining the tracking method
    # TODO see if fields are used after everything is converted to OOP
    Gb.inzone_interval_secs             = {}       # Probably not needed
    Gb.devicename_email                 = {}
    Gb.config_inzone_interval_secs      = {}

    # Temporary variables used during startup
    # last_config_ic3_items = []      # Usec in configure_ic3

    # Tracking method control vaiables
    # Used to reset Gb.tracking_method  after pyicloud/icloud account successful reset
    # Will be changed to IOSAPP if pyicloud errors
    Gb.tracking_method_config_initial_load = '' #NOT_SET
    Gb.tracking_method_config           = ''    #NOT_SET
    Gb.tracking_method                  = ''    #NOT_SET
    Gb.tracking_method_FAMSHR           = False
    Gb.tracking_method_FMF              = False
    Gb.tracking_method_IOSAPP           = False
    Gb.tracking_method_FMF_used         = False
    Gb.tracking_method_FAMSHR_used      = False
    Gb.tracking_method_IOSAPP_used      = False

    # Variables that will be reinitialized on iCloud3 restart
    # Gb.trk_fm_zone                      = HOME
    # Gb.trk_fm_zone_name                 = HOME_FNAME
    # Gb.trk_fm_zone_lat                  = 0.00
    # Gb.trk_fm_zone_long                 = 0.00
    # Gb.trk_fm_zone_radius_km            = 0.00

#------------------------------------------------------------------------------
#
#   GET FILE AND DIRECTORY NAMES FOR ICLOUD3, CONFIG_IC3.YAML AND
#   ICLOUD3_EVENT_LOG_CARD.JS
#
#------------------------------------------------------------------------------
def get_icloud3_directory_and_file_names():
    try:
        Gb.icloud3_dir           = os.path.abspath(os.path.dirname(__file__)).replace("//", "/")
        Gb.icloud3_dir           = Gb.icloud3_dir.split("/support")[0]
        Gb.icloud3_filename      = Gb.icloud3_dir.split("/custom_components/")[1]
        Gb.www_evlog_js_dir      = (f"{Gb.icloud3_dir.split('custom_components')[0]}"
                                    f"{Gb.event_log_card_directory}")
        Gb.www_evlog_js_filename = (f"{Gb.www_evlog_js_dir}/{ICLOUD_EVENT_LOG_CARD_JS}")
        Gb.icloud3_evlog_js_filename = (f"{Gb.icloud3_dir}/{ICLOUD_EVENT_LOG_CARD_JS}")

        post_startup_event(f"iCloud3 Directory > {Gb.icloud3_dir}")

    except Exception as err:
        log_exception(err)

#------------------------------------------------------------------------------
# Get path of config_ic3.yaml file
    config_filename = ""

    #File name specified
    if Gb.config_ic3_filename != "":
        if (instr(Gb.config_ic3_filename, "/")
                and os.path.exists(Gb.config_ic3_filename)):
            config_filename = Gb.config_ic3_filename

        elif os.path.exists(f"/config/{Gb.config_ic3_filename}"):
            config_filename = (f"/config/{Gb.config_ic3_filename}")

        elif os.path.exists(f"{Gb.icloud3_dir}/{Gb.config_ic3_filename}"):
            config_filename = (f"{Gb.icloud3_dir}/{Gb.config_ic3_filename}")

    elif os.path.exists(DEFAULT_CONFIG_IC3_FILE_NAME):
        config_filename = DEFAULT_CONFIG_IC3_FILE_NAME

    elif os.path.exists(f"{Gb.icloud3_dir}/config_ic3.yaml"):
        config_filename = (f"{Gb.icloud3_dir}/config_ic3.yaml")

        alert_msg = (f"{EVLOG_ALERT}iCloud3 Alert > The `config_ic3.yaml` "
                    f"configuration file should moved to the `/config` "
                    f"directory so it is not deleted when HACS updates iCloud3")
        post_event(alert_msg)

    Gb.config_ic3_filename = config_filename.replace("//", "/")

    if config_filename == "":
        if Gb.config_ic3_filename:
            event_msg =(f"iCloud3 Error, Configuration File > "
                        f"File not Found - {Gb.config_ic3_filename}")
        else:
            event_msg = "iCloud3 Configuration File > config_ic3.yaml not used"
        post_event(event_msg)

    post_event(f"iCloud3 Configuration File > {Gb.config_ic3_filename}")

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
        ic3_version, ic3_beta_version, ic3_version_text = _read_event_log_card_js_file(Gb.icloud3_evlog_js_filename)
        www_version, www_beta_version, www_version_text = _read_event_log_card_js_file(Gb.www_evlog_js_filename)

        if www_version > 0:
            event_msg =(f"Event Log Version Check > Current release is being used"
                        f"{CRLF_DOT}Version-{www_version_text}"
                        f"{CRLF_DOT}Directory-{Gb.www_evlog_js_dir}")
            post_startup_event(event_msg)

        # Event log card is not in iCloud3 directory. Nothing to do.
        if ic3_version == 0:
            return

        # Event Log card does not exist in www directory. Copy it from iCloud3 directory
        if www_version == 0:
            try:
                os.mkdir(Gb.www_evlog_js_dir)
            except FileExistsError:
                pass
            except Exception as err:
                log_exception(err)
                pass

        update_event_log_card_flag = False
        if ic3_version > www_version:
            update_event_log_card_flag = True
        elif ic3_version == www_version:
            if www_beta_version == 0:
                pass
            elif (ic3_beta_version > www_beta_version
                    or ic3_beta_version == 0 and www_beta_version > 0):
                update_event_log_card_flag = True

        if update_event_log_card_flag:
            shutil.copy(Gb.icloud3_evlog_js_filename, Gb.www_evlog_js_filename)
            event_msg =(f"{EVLOG_NOTICE}"
                        f"Event Log Alert > Event Log was updated"
                        f"{CRLF_DOT}Old Version.. - v{www_version_text}"
                        f"{CRLF_DOT}New Version - v{ic3_version_text}"
                        f"{CRLF_DOT}Copied From - {Gb.icloud3_dir}"
                        f"{CRLF_DOT}Copied To..... - {Gb.www_evlog_js_dir}"
                        f"CRLF{'-'*75}"
                        f"CRLFThe Event Log Card was updated to v{ic3_version_text}. "
                        "Refresh your browser and do the following on every tracked "
                        "devices running the iOS App to load the new version."
                        "CRLF1. Select HA Sidebar > APP Configuration."
                        "CRLF2. Scroll to the botton of the General screen."
                        "CRLF3. Select Reset Frontend Cache, then select Done."
                        "CRLF4. Display the Event Log, then pull down to refresh the page. "
                        "You should see the busy spinning wheel as the new version is loaded.")
            post_startup_event(event_msg)
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
        return

#------------------------------------------------------------------------------
def _read_event_log_card_js_file(evlog_filename):
    '''
    Read the records in the the evlog_filename up to the 'class' statement and
    extract the version and date.
    Return the Version number and the Version text (#.#.#b## (m/d/yyy))
    Return 0, 0, "Unknown" if the Version number was not found
    '''
    try:

        if os.path.exists(evlog_filename) == False:
            return (0, 0, UNKNOWN)

        #Cycle thru the file looking for the Version
        evlog_file = open(evlog_filename)

        for evlog_recd in evlog_file:
            if instr(evlog_recd.lower().replace(' ', ''), 'version='):
                break

            #exit if find 'class' recd before 'version' recd
            elif instr(evlog_recd, "class"):
                return (0, 0, UNKNOWN)

        evlog_recd   = evlog_recd.replace("("," (").replace("  "," ")
        version_text = evlog_recd.split("=")[1].replace('\n', '')
        version_date = version_text.split(' ')
        version_beta = (f"{version_date[0]}b0").split('b')

        version_parts = version_beta[0].split('.')
        beta_version = int(version_beta[1])

        version  = 0
        version += int(version_parts[0])*10000
        version += int(version_parts[1])*100
        version += int(version_parts[2])*1

    except FileNotFoundError:
        return (0, 0, UNKNOWN)

    except Exception as err:
        log_exception(err)
        return (0, 0, ERROR)

    evlog_file.close()

    return (version, beta_version, version_text)

#------------------------------------------------------------------------------
#
#   LOAD THE ZONE DATA FROM HA
#
#   Retrieve the zone entity attributes from HA and initialize Zone object
#   that is used when a Device is located
#
#------------------------------------------------------------------------------
def create_Zones_object():
    '''
    Get the zone names from HA, fill the zone tables
    '''

    try:
        if Gb.start_icloud3_initial_load_flag is False:
            Gb.hass.services.call(ZONE, "reload")
    except:
        pass

    #log_msg = (f"Reloading Zone.yaml config file")
    #log_debug_msg(log_msg)

    # zone_entities = Gb.hass.states.entity_ids(ZONE)
    zone_entities = get_entity_ids(ZONE)
    #log_debug_msg("*",f"ZONES - {zone_entities}")

    Gb.state_to_zone = STATE_TO_ZONE_BASE.copy()
    OldZones_by_zone = Gb.Zones_by_zone.copy()

    Gb.Zones = []
    Gb.Zones_by_zone = {}

    # Add away, not_set, not_home, stationary, etc. so display_name is set
    # for these zones/states. Radius=0 is used to ypass normal zone processing.
    for zone, display_as in NON_ZONE_ITEM_LIST.items():
        if zone in OldZones_by_zone:
            Zone = OldZones_by_zone[zone]
        else:
            Zone = Zones(zone, {NAME: display_as, TITLE: display_as, FNAME: display_as, RADIUS: 0})
            Zone.display_as = display_as
        Gb.Zones.append(Zone)
        Gb.Zones_by_zone[zone] = Zone
    _traceha(f"{Gb.Zones_by_zone=}")
    _traceha(f"{OldZones_by_zone=}")
    _traceha(f"{zone_entities=}")
    for zone_entity in zone_entities:
        try:
            _traceha(f"{zone_entity=}")
            zone_data = get_attributes(zone_entity)
            zone      = zone_entity.replace('zone.', '')
            _traceha(f"{zone=} {zone_data=}")

            #log_debug_msg("*",f"ZONE.DATA - [zone.{zone}--{zone_data}]")

            if LATITUDE not in zone_data: continue

            # Update Zone data if it already exists, else add a new one
            if zone in OldZones_by_zone:
                Zone = OldZones_by_zone[zone]
                _traceha(f"{Zone.zone=} {zone_data=}")
                Zone.__init__(zone, zone_data)
                post_monitor_msg(f"INITIALIZED Zone-{zone}")

            else:
                Zone = Zones(zone, zone_data)
                post_monitor_msg(f"ADDED Zone-{zone}")

            Gb.Zones.append(Zone)
            Gb.Zones_by_zone[zone] = Zone

            zfname = Zone.fname
            ztitle = Zone.title

            Gb.state_to_zone[zfname] = zone
            if ztitle not in Gb.state_to_zone:
                Gb.state_to_zone[ztitle] = zone
            ztitle_w = ztitle.replace(' ', '')
            if ztitle_w not in Gb.state_to_zone:
                Gb.state_to_zone[ztitle_w] = zone

            if zone == HOME:
                Gb.HomeZone = Zone

        except Exception as err:
            log_exception(err)

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
def initialize_debug_control(log_level):

    #Save log_level flags across restarts via Event Log > Actions
    if Gb.log_debug_flag_restart is not None or Gb.log_rawdata_flag_restart is not None:
        if Gb.log_debug_flag_restart is not None:
            Gb.log_debug_flag         = Gb.log_debug_flag_restart
            Gb.log_debug_flag_restart = None

        if Gb.log_rawdata_flag_restart is not None:
            Gb.log_rawdata_flag         = Gb.log_rawdata_flag_restart
            Gb.log_rawdata_flag_restart = None
    else:
        Gb.log_debug_flag   = instr(log_level, 'debug') or DEBUG_TRACE_CONTROL_FLAG
        Gb.log_rawdata_flag = instr(log_level, 'rawdata')
        Gb.log_rawdata_flag_unfiltered = instr(log_level, 'unfiltered')

    if Gb.log_rawdata_flag: Gb.log_debug_flag = True
    Gb.evlog_trk_monitors_flag = Gb.evlog_trk_monitors_flag or instr(log_level, 'eventlog')


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 1
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>


#------------------------------------------------------------------------------
#
#   SET THE DISPLAY_AS FOR EACH ZONE
#
#   After the configuration file is loaded and the 'zone_display_as' parameter is
#   that is used when a Device is located
#
#------------------------------------------------------------------------------
def initialize_zone_table_display_as():

    zone_msg = ''

    try:
        for Zone in Gb.Zones:
            if Zone.radius > 0:
                if Gb.display_zone_format   == CONF_ZONE: Zone.display_as = Zone.zone
                elif Gb.display_zone_format == CONF_NAME: Zone.display_as = Zone.name
                elif Gb.display_zone_format == TITLE:     Zone.display_as = Zone.title
                elif Gb.display_zone_format == FNAME:     Zone.display_as = Zone.fname

                zone_msg += (f"{CRLF_DOT}{Zone.zone}/{Zone.display_as} "
                        f"(r{Zone.radius}m)")

        log_msg = (f"Set up Zones (zone/{Gb.display_zone_format}) > {zone_msg}")
        post_startup_event("*", log_msg)

    except Exception as err:
        log_exception(err)

    return


#------------------------------------------------------------------------------
#
#   SET THE GLOBAL TRACKING METHOD
#
#   This is used during the startup routines and in other routines when errors occur.
#
#------------------------------------------------------------------------------
def set_tracking_method(tracking_method):
    '''
    Set up tracking method. These fields will be reset based on the device_id's available
    for the Device once the famshr and fmf tracking methods are set up.
    '''
    if tracking_method in [FAMSHR, FMF] and Gb.password == '':
        event_msg =("iCloud3 Error > The password is required for the "
                    f"iCloud Location Services tracking method. "
                    f"The iOS App tracking_method will be used.")
        post_error_msg(event_msg)
        tracking_method = IOSAPP

    # Note: Gb.tracking_method_config is original config_tracking_method entry
    # which can be used to see if a user actually specified a tracking_method
    # instead of using the FAMSHR default value.
    Gb.tracking_method = FAMSHR if tracking_method == '' else tracking_method

    Gb.tracking_method_FAMSHR     = (tracking_method == FAMSHR)
    Gb.tracking_method_FMF        = (tracking_method == FMF)
    Gb.tracking_method_IOSAPP     = (tracking_method == IOSAPP)

#------------------------------------------------------------------------------
#
#   INITIALIZE THE UNIT_OF_MEASURE FIELDS
#
#------------------------------------------------------------------------------
def initialize_um_formats():
    #Define variables, lists & tables
    if Gb.um == 'mi':
        if Gb.time_format != 24: Gb.time_format = 12
        Gb.um_km_mi_factor          = 0.62137
        Gb.um_m_ft                  = 'ft'
        Gb.um_kph_mph               = 'mph'
    else:
        if Gb.time_format != 12: Gb.time_format = 24
        Gb.um_km_mi_factor          = 1
        Gb.um_m_ft                  = 'm'
        Gb.um_kph_mph               = 'kph'

    if Gb.time_format == 12:
        Gb.um_time_strfmt       = '%I:%M:%S'
        Gb.um_time_strfmt_ampm  = '%I:%M:%S%P'
        Gb.um_date_time_strfmt  = '%Y-%m-%d %I:%M:%S'
    else:
        Gb.um_time_strfmt       = '%H:%M:%S'
        Gb.um_time_strfmt_ampm  = '%H:%M:%S'
        Gb.um_date_time_strfmt  = '%Y-%m-%d %H:%M:%S'

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
                                Gb.waze_history_max_distance,
                                Gb.waze_history_map_track_direction)
        else:
            Gb.Waze = Waze(     Gb.distance_method_waze_flag,
                                Gb.waze_min_distance,
                                Gb.waze_max_distance,
                                Gb.waze_realtime,
                                Gb.waze_region)
            Gb.WazeHist = WazeHist(
                                Gb.waze_history_max_distance,
                                Gb.waze_history_map_track_direction)

    except Exception as err:
        log_exception(err)


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 2
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>


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
        old_Devices_by_devicename = Gb.Devices_by_devicename.copy()
        Gb.Devices               = []
        Gb.Devices_by_devicename = {}
        Gb.TrackedZones_by_zone  = {}
        Gb.TrackedZones_by_zone[HOME] = Gb.HomeZone
        attr_tracking_msg     = ""   # devices tracked attribute

        for device_fields in Gb.config_track_devices_fields:
            if CONF_DEVICENAME not in device_fields:
                continue

            devicename = device_fields.get(CONF_DEVICENAME)

            if devicename in old_Devices_by_devicename:
                Device = old_Devices_by_devicename[devicename]
                Device.__init__(devicename, device_fields)
                post_monitor_msg(f"INITIALIZED Device-{devicename}")
            else:
                Device = Devices(devicename, device_fields)
                post_monitor_msg(f"ADDED Device-{devicename}")

            Gb.Devices.append(Device)
            Gb.Devices_by_devicename[devicename] = Device

            event_msg =  (f"Decoding ... {device_fields.get(CONF_SOURCE)} >CRLF") if CONF_SOURCE in device_fields else ""
            event_msg += (f"✓ {devicename} > Name-{device_fields.get(CONF_NAME)}, ")
            if Device.picture:  event_msg += (f"Picture-{device_fields.get(CONF_PICTURE)}, ")
            if Device.email:    event_msg += (f"email-{device_fields.get(CONF_EMAIL, '')}, ")
            event_msg += (f"Type-{Device.device_type}, "
                            f"inZoneInterval-{secs_to_time_str(Device.inzone_interval_secs)}")

            if Device.track_from_zones != [HOME]:
                zones_str = ", ".join(Device.track_from_zones)
                event_msg += (f", TrackFromZone-{zones_str}, ")
            if Device.iosapp_setup_msg: event_msg += (f", {Device.iosapp_setup_msg} ")
            if Device.config_error_msg: event_msg += (f", WARNING-{Device.config_error_msg}")

            post_startup_event(event_msg)

    except Exception as err:
        log_exception(err)

    return

#########################################################
#
#   INITIALIZE PYICLOUD DEVICE API
#   DEVICE SETUP SUPPORT FUNCTIONS FOR MODES FMF, FAMSHR, IOSAPP
#
#########################################################

def setup_tracked_devices_for_fmf():
    '''
    Cycle thru the Find My Friends contact data. Extract the name, id &
    email address. Scan fmf_email config parameter to tie the devicename_device_id in
    the location record to the devicename.

                email --> devicename <--devicename_device_id
    '''
    PyiCloud_friends_data = None
    try:
        PyiCloud_friends_data = Gb.PyiCloud_FindMyFriends.data
    except:
        pass

    if PyiCloud_friends_data == None:
        event_msg = "FindMy App Friends (People) that can be tracked > No entries found"
        post_event(event_msg)
        return

    # if Gb.log_rawdata_flag:
    #     log_rawdata(f"PyiCloud_friends_data", PyiCloud_friends_data)

    try:
        if Gb.log_rawdata_flag:
            log_rawdata("FmF PyiCloud Data (friends data)", PyiCloud_friends_data)


        #Extract the email & ID from the friends being followed by the main user
        try:
            extracted_device_ids = []
            for fmf_type in ['following', 'followers', 'contact_details']:
                if fmf_type == 'following':
                    Pyicloud_FmF_data = Gb.PyiCloud_FindMyFriends.following
                    fmf_email_field   = 'invitationAcceptedHandles'
                elif fmf_type == 'followers':
                    Pyicloud_FmF_data = Gb.PyiCloud_FindMyFriends.followers
                    fmf_email_field   = 'invitationFromHandles'
                elif fmf_type == 'contact_details':
                    Pyicloud_FmF_data = Gb.PyiCloud_FindMyFriends.contact_details
                    fmf_email_field   = 'emails'

                for friend in Pyicloud_FmF_data:
                    friend_emails = friend.get(fmf_email_field)
                    device_id     = friend.get('id')

                    extracted_device_ids.append(_extract_fmf_email_id(device_id, friend_emails))

                    if Gb.log_rawdata_flag:
                        log_rawdata(f"{fmf_type} -- {friend_emails}", friend)

        except Exception as err:
            log_exception(err)
            pass

        try:
            # SGo thru the extracted device ids and ave the Device's device id and set the verify flag
            # Format the Friends in the Find My Friends List that can be tracked event msg

            # Sample extracted_device_ids:
            #   {'JHt5rv4Se7u': 'lillian_iphone'},
            #   {'geekstergary@gmail.com': 'Not Tracked'},
            #   {'LOi9nf5RtVB45': 'gary_iphone'},
            #   {'JHt5rv4Se7u': 'lillian_iphone'},
            #   {'geekstergary@gmail.com': 'Not Tracked'},
            #   {'LOi9nf5RtVB45': 'gary_iphone', '+17723213766»LOi9nf5RtVB45': 'Not Used'},
            #   {'twitter:@lilliebell»JHt5rv4Se7u': 'Not Used', 'JHt5rv4Se7u': 'lillian_iphone'},
            #   {'geekstergary@gmail.com': 'Not Tracked'}

            event_msg = "Friends in the Find-my-Friends List >"
            duplicate_check = {}
            device_id_devicename = {}
            for devicename_device_ids in extracted_device_ids:
                for device_id, devicename in devicename_device_ids.items():
                    if devicename not in ['Not Used', 'Not Tracked']:
                        if device_id not in device_id_devicename:
                            device_id_devicename[device_id] = devicename
                            Device = Gb.Devices_by_devicename[devicename]
                            Device.verified_flag = True
                            Device.device_id_fmf = device_id

                            event_msg += (f"{CRLF_CHK}{devicename} > {Device.email}")

            for devicename_device_ids in extracted_device_ids:
                for device_id, devicename in devicename_device_ids.items():
                    if device_id not in duplicate_check:
                        duplicate_check[device_id] = True
                        if devicename == 'Not Tracked':
                            event_msg += (f"{CRLF_DOT}{devicename} > {device_id}")
                        elif devicename == 'Not Used':
                            if device_id.find('»')>=0:
                                # device_id really is 'email/phone:device_id', split off device_id to get devicename
                                email_device_id = device_id.split('»')
                                email_devicename = (f"{email_device_id[0]} "
                                                f"({device_id_devicename.get(email_device_id[1], 'Unknown')})")
                            else:
                                email_devicename = device_id
                            event_msg += (f"{CRLF_DOT}{devicename} > {email_devicename}")

            post_startup_event(event_msg)

        except Exception as err:
            log_exception(err)
            pass

    except Exception as err:
        set_tracking_method(IOSAPP)
        log_exception(err)

#--------------------------------------------------------------------
def _extract_fmf_email_id(device_id, friend_emails):
    '''
    Cycle thru the emails on the tracked_devices config parameter and
    get the device_id associated with the email

    Returns:
        Dictionary: key/value:
                    device_id/devicename if the email was found
                    email/'Not Tracked' if the email is not tracked or
                    email»device_id/'Not Used' if the data is valid but not used
    '''

    try:
        devicename_by_emails        = {}
        friend_emails_by_id         = {}
        devicename_id_by_devicename = {}

        # Build a table of the devicename's emails to be matched against
        # ex. {'gary@email.com': 'gary_iphone', 'lillian@gmail.com': 'lillian_iphone'}
        for Device in Gb.Devices:
            devicename_by_emails[Device.email] = Device.devicename

        # Go through the FmF data and get the device_id or see if it is not used or not tracked
        for friend_email in friend_emails:
            if device_id in Gb.PyiCloud_DevData_by_device_id_fmf:
                devicename = devicename_by_emails.get(friend_email, '')
                friend_emails_by_id[friend_email] = device_id
                if friend_email in devicename_by_emails:
                    devicename_id_by_devicename[device_id]  = devicename
                else:
                    devicename_id_by_devicename[(f"{friend_email}»{device_id}")] = 'Not Used'
            else:
                devicename_id_by_devicename[friend_email] = 'Not Tracked'

        return devicename_id_by_devicename


    except Exception as err:
        log_exception(err)
        return {}

#--------------------------------------------------------------------
def _get_me_device_id(PyiCloud_friends, friend_valid_emails_msg):
    '''
    Check to see if the devicename email is the same as the username and is verified by being
    in the followed or is being followed list. If it was not verified, get this devicename's
    device id from fmf MyPrefs, then follow the trail to get the device_id from the famshr
    devices. That device id will be used to get the 'me device' location. If it is verified,
    fmf tracking is already set up for it.
    '''
    try:
        for devicename, Device in Gb.Devices_by_devicename.items():
            if Device.device_id_famshr:
                continue
            if (Device.email == Gb.username):
                fmf_data = Gb.PyiCloud_FindMyFriends.data
                my_info = fmf_data['myInfo']
                if Gb.username in my_info['emails']:
                    for fmf_device in fmf_data['devices']:
                        if fmf_device['id'] == my_info['meDeviceId']:
                            me_device_id = fmf_device['idsDeviceId']

                            for device_id, PyiCloud_DevData in Gb.PyiCloud_DevData_by_device_id_famshr.items():
                                if PyiCloud_DevData.data['deviceDiscoveryId'] == me_device_id:
                                    friend_valid_emails_msg += (f"{CRLF_CHK}{devicename} > "
                                                f"{Device.fname_devtype}, Me in FindMy App (FamShr)")
                                    Device.verified_flag    = True
                                    Device.device_id_famshr = device_id
                                    break

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def setup_tracked_devices_for_famshr():
    '''
    Get the device info from iCloud Web Svcs via pyicloud. Then cycle through
    the iCloud devices and for each device, see if it is in the list of devicenames
    to be tracked. If in the list, set it's verified flag to True.

    Returns the devices being tracked and the devices in the iCloud list that are
    not being tracked.
    '''

    if Gb.PyiCloud_DevData_by_device_id == {}:
        event_msg = "Family Sharing List devices that can be tracked > No entries found"
        post_event(event_msg)
        return

    try:
        event_msg = "Family Sharing List devices that can be tracked >"
        for device_id, PyiCloud_DevData in Gb.PyiCloud_DevData_by_device_id_famshr.items():
            device_data = PyiCloud_DevData.data

            device_fname = device_data[NAME]
            devicename   = slugify(device_fname)
            device_type  = device_data[ICLOUD_DEVICE_CLASS]
            show_device_id = (f", {device_id[:8]}") if Gb.log_debug_flag else ''

            if Gb.log_rawdata_flag:
                log_rawdata(f"FamShr PyiCloud Data (device_data -- {devicename})", device_data)

            if (LOCATION not in device_data
                    or device_data[LOCATION] is None):
                if devicename in Gb.Devices_by_devicename:
                    event_msg += (f"{CRLF_X}{devicename} > {device_fname} ({device_type}), "
                                    f"No Location Info{show_device_id}")
                    post_event(devicename, event_msg)
                continue

            if devicename in Gb.Devices_by_devicename:
                Device                  = Gb.Devices_by_devicename[devicename]
                Device.device_type      = device_data[ICLOUD_DEVICE_CLASS]
                Device.verified_flag    = True
                Device.device_id_famshr = device_id

                crlf_mark = CRLF_CHK
            else:
                crlf_mark = CRLF_DOT
            event_msg += (f"{crlf_mark}{devicename} > {device_fname} ({device_type}){show_device_id}")

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
def set_device_tracking_method_famshr_fmf():
    '''
    The goal is to get either all fmf or all famshr to minimize the number of
    calls to iCloud Web Services by pyicloud_ic3. Look at the fmf and famshr
    devices to see if:
    1. If all devices are fmf or all devices are famshr:
            Do not make any changes
    2. If set to fmf but it also has a famshr id, change to famshr.
    2. If set to fmf and no famshr id, leave as fmf.
    '''

    try:
        if Gb.Devices_by_devicename == {}:
            return

        Gb.Devices_by_icloud_device_id = {}
        for devicename, Device in Gb.Devices_by_devicename.items():
            tracking_method = ''

            if Gb.tracking_method_config == '':
                pass
            elif Gb.tracking_method_FAMSHR and Device.device_id_famshr:
                tracking_method = FAMSHR
            elif Gb.tracking_method_FMF and Device.device_id_fmf:
                tracking_method = FMF

            # Check Device's tracking_method parameter and Device's icloud device_id
            # It overrides the Global setting if specified
            if Device.tracking_method == '':
                pass
            elif Device.tracking_method_FAMSHR and Device.device_id_famshr:
                tracking_method = FAMSHR
            elif Device.tracking_method_FMF and Device.device_id_fmf:
                tracking_method = FMF

            # Neither a Global or a Device's tracking_method parameter specified
            if tracking_method == '':
                if Device.device_id_famshr:
                    tracking_method = FAMSHR
                elif Device.device_id_fmf:
                    tracking_method = FMF

            override_flag = False
            if Device.tracking_method:
                override_flag = (tracking_method != Device.tracking_method)
            elif Gb.tracking_method_config:
                override_flag = (tracking_method != Gb.tracking_method_config)

            if tracking_method and override_flag:
                gb_config  = TRACKING_METHOD_FNAME[Gb.tracking_method_config] if Gb.tracking_method_config else 'Not Specified'
                dev_config = TRACKING_METHOD_FNAME[Device.tracking_method] if Device.tracking_method else 'Not Specified'
                alert_msg =(f"{EVLOG_ALERT}Tracking_method Override > {devicename} > No Location Data is available "
                            f"for the tracking method specified."
                            f"{CRLF_DOT}Global Tracking Method Config Parm - {gb_config}"
                            f"{CRLF_DOT}Device Tracking Method Config Parm - {dev_config}"
                            f"{CRLF_DOT}Global Tracking Method Default Used.- {TRACKING_METHOD_FNAME[Gb.tracking_method]}"
                            f"{CRLF_DOT}Device Tracking method changed to ..- {TRACKING_METHOD_FNAME[tracking_method]} {LARROW} Will Use"
                            f"{CRLF_DOT}FamShr iCloud Device Data Id - {Device.device_id8_famshr}"
                            f"{CRLF_DOT}FmF...... iCloud Device Data Id - {Device.device_id8_fmf}")
                post_event(alert_msg)


            # If still not set, there is no device_id in iCloud, do not verify device
            if tracking_method:
                if (Device.device_id_famshr
                        and Device.device_id_famshr in Gb.PyiCloud_DevData_by_device_id):
                    Gb.Devices_by_icloud_device_id[Device.device_id_famshr] = Device
                    Device.PyiCloud_DevData_famshr = Gb.PyiCloud_DevData_by_device_id[Device.device_id_famshr]
                else:
                    Device.device_id_famshr = None

                if (Device.device_id_fmf
                        and Device.device_id_fmf in Gb.PyiCloud_DevData_by_device_id):
                    Gb.Devices_by_icloud_device_id[Device.device_id_fmf] = Device
                    Device.PyiCloud_DevData_fmf = Gb.PyiCloud_DevData_by_device_id[Device.device_id_fmf]
                else:
                    Device.device_id_fmf = None

                # If only one available, set it so it does not need to be determined every time we get
                # iCloud data
                if Device.device_id_famshr and Device.device_id_fmf is None:
                    Device.PyiCloud_DevData = Device.PyiCloud_DevData_famshr
                elif Device.device_id_fmf and Device.device_id_famshr is None:
                    Device.PyiCloud_DevData = Device.PyiCloud_DevData_fmf

                info_msg = (f"Set PyiCloud Device Id > {Device.devicename}, "
                            f"TrkMethod-{tracking_method}, "
                            f"{CRLF}FamShr-{Device.device_id8_famshr}, "
                            f"FmF-{Device.device_id8_fmf})")
                post_monitor_msg(info_msg)

            else:
                tracking_method = IOSAPP
                alert_msg =(f"iCloud3 Error > {devicename} > The tracking method could not be determined "
                            f"and the device will not be tracked. This is caused when no location data is available "
                            f"when the iCloud Device Id assigned. The iOS App will be used."
                            f"{CRLF_DOT}Device Tracking method changed to - {TRACKING_METHOD_FNAME[tracking_method]} {LARROW} Will Use"
                            f"{CRLF_DOT}FamShr iCloud Device Data Id - {Device.device_id8_famshr}"
                            f"{CRLF_DOT}FmF...... iCloud Device Data Id - {Device.device_id8_fmf}")
                post_event(alert_msg)

            Device.tracking_method = tracking_method

        info_msg = (f"PyiCloud Devices > ")
        for _device_id, _PyiCloud_DevData in Gb.PyiCloud_DevData_by_device_id.items():
            info_msg += (f"{_device_id[:8]} ({_PyiCloud_DevData.tracking_method}), ")
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

    try:
        # Global tracking_method specified, nothing to do
        if Gb.tracking_method_config:
            return
        elif Gb.Devices_by_devicename == {}:
            return

        cnt_famshr = 0     # famshr is specified as the tracking_method for the device in config
        cnt_fmf    = 0     # fmf is specified as the tracking_method for the device in config
        cnt_famshr_to_fmf = 0
        cnt_fmf_to_famshr = 0

        for devicename, Device in Gb.Devices_by_devicename.items():
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
    The devices to be tracked are in the track_devices or the
    include_devices config parameters.
    '''
    event_msg = "iOS App Devices that will be tracked > "
    for devicename, Device in Gb.Devices_by_devicename.items():
        if Device.iosapp_monitor_flag:
            Device.verified_flag = True
            event_msg += (f"{CRLF_CHK}{devicename} > {Device.fname_devtype}")

            if Device.tracking_method_FAMSHR_FMF is False:
                Device.tracking_method = IOSAPP

    post_event(event_msg)
    # post_startup_event(event_msg)
    return


#--------------------------------------------------------------------
def setup_monitored_iosapp_entities(Device, iosapp_device_trkr_suffix):

    #Cycle through the mobile_app 'core.entity_registry' items and see
    #if this 'device_tracker.devicename' exists. If so, it is using
    #the iosapp v2 component. Return the devicename with the device suffix (_#)
    #and the sensor.xxxx_last_update_trigger entity for that device.

    devicename = Device.devicename

    # If no iOS App monitoring, use the ic3 device tracker entity instead
    if Device.iosapp_monitor_flag is False:
        Device.iosapp_device_trkr_entity_id = (f"{DEVICE_TRACKER}{devicename}")
        Device.iosapp_notify_devices        = []
        return ("", "", "", "")

    iosapp_device_trkr_suffix       = "" if iosapp_device_trkr_suffix == None else iosapp_device_trkr_suffix
    iosapp_device_trkr_entity_id    = devicename + iosapp_device_trkr_suffix if iosapp_device_trkr_suffix != "" else ""
    iosapp_sensor_trigger_entity_id = ""
    sensor_battery_level_entity     = ""
    dev_trk_list                    = ""
    iosapp_device_trkr_entity_device_id = ""

    #Cycle through iosapp_entities in
    #.storage/core.entity_registry (mobile_app pltform) and get the
    #names of the iosapp device_tracker and sensor.last_update_trigger
    #names for this devicename. If iosapp_id suffix or device tracker entity name
    # is specified, look for the device_tracker with that number.

    #Get the entity for the devicename entity specified on the track_devices parameter
    iosapp_device_trkr_entity_cnt = 0
    if iosapp_device_trkr_entity_id != "":
        device_tracker_entities = [x for x in Gb.iosapp_entities \
                if (x[ENTITY_ID] == f"{DEVICE_TRACKER}{iosapp_device_trkr_entity_id}")]
        iosapp_device_trkr_entity_cnt = len(device_tracker_entities)

    #If the entity specified was not found, get all entities for the device
    if iosapp_device_trkr_entity_cnt == 0:
        device_tracker_entities = [x for x in Gb.iosapp_entities \
                if (x[ENTITY_ID].startswith(DEVICE_TRACKER) and instr(x[ENTITY_ID], devicename))]
        iosapp_device_trkr_entity_cnt = len(device_tracker_entities)

    #Extract the device_id for each entity found. If more than 1 was found, display an
    #error message about duplicate entities and select the last one.
    for entity in device_tracker_entities:
        iosapp_device_trkr_entity_id        = entity[ENTITY_ID]
        iosapp_device_trkr_suffix           = iosapp_device_trkr_entity_id.replace(DEVICE_TRACKER, '').replace(devicename, '')
        iosapp_device_trkr_entity_device_id = entity[DEVICE_ID]
        dev_trk_list         += (f"{CRLF_DOT}{iosapp_device_trkr_entity_id.replace(DEVICE_TRACKER, '')} ({iosapp_device_trkr_suffix})")

    #Will monitor if found an iosapp device_tracker entity
    Device.iosapp_monitor_flag = (iosapp_device_trkr_entity_cnt > 0)

    if iosapp_device_trkr_entity_cnt > 1:
        Gb.info_notification = (f"iOS App Device Tracker not specified for "
                        f"{Device.fname_devicename}. See Event Log for more information.")
        dev_trk_list += " ← ← Will be monitored"
        event_msg =(f"iCloud3 Setup Error > There are {iosapp_device_trkr_entity_cnt} iOS App "
                    f"device_tracker entities for {devicename}. iCloud3 can only monitor one."
                    f"CRLF{'-'*25}CRLFDo one of the following:"
                    f"CRLF●  Delete the incorrect device_tracker from the Entity Registry, or"
                    f"CRLF●  Add the full entity name or the suffix of the device_tracker entity that "
                    f"should be monitored to the `devices/device_name: {devicename}` parameter, or"
                    f"CRLF●  Change the device_tracker entity's name of the one that should not be monitored "
                    f"so it does not start with `{devicename}`."
                    f"CRLF{'-'*25}CRLFDevice_tracker entities (suffixes) found:"
                    f"{dev_trk_list}")
        post_event(event_msg)

    #Get the sensor.last_update_trigger for deviceID
    if iosapp_device_trkr_entity_device_id:
        iosapp_sensor_trigger_entity_id = \
            _get_entity_registry_item(Device, iosapp_device_trkr_entity_device_id, '_last_update_trigger')
        sensor_battery_level_entity = ''

    if Device.iosapp_monitor_flag is False:
        event_msg =(f"iCloud3 Error > {devicename} > "
                    f"The iOS App device_tracker entity was not found in the "
                    f"Entity Registry for this device.")
        post_event(event_msg)
        Gb.info_notification = ICLOUD3_ERROR_MSG

        iosapp_device_trkr_entity_id    = ''
        iosapp_device_trkr_suffix       = ''
        iosapp_sensor_trigger_entity_id = ''
        sensor_battery_level_entity     = ''

    Device.iosapp_device_trkr_entity_id    = iosapp_device_trkr_entity_id
    Device.iosapp_device_trkr_suffix       = iosapp_device_trkr_suffix
    Device.iosapp_sensor_trigger_entity_id = iosapp_sensor_trigger_entity_id
    Device.iosapp_battery_level_entity     = sensor_battery_level_entity

    #Extract the all notify entitity id's with this devicename in them from hass notify services notify list
    if iosapp_device_trkr_entity_id:
        notify_devicename_list = []
        for notify_devicename in Gb.iosapp_notify_devicenames:
            if instr(notify_devicename, devicename):
                notify_devicename_list.append(notify_devicename)

        Device.iosapp_notify_devices = notify_devicename_list
    else:
        Device.iosapp_notify_devices        = []
        Device.iosapp_device_trkr_entity_id = ''
        Device.iosapp_monitor_flag is False

    return

#--------------------------------------------------------------------
def _get_entity_registry_item(Device, device_id, desired_entity_name):
    '''
    Scan through the iosapp entities and get the actual ios app entity_id for
    the desired entity
    '''
    for entity in (x for x in Gb.iosapp_entities \
            if x['unique_id'].endswith(desired_entity_name)):

        if (entity[DEVICE_ID] == device_id):
            # real_entity = entity[ENTITY_ID].replace('sensor.', '')
            entity_id = entity[ENTITY_ID]
            log_msg = (f"Matched iOS App {entity_id} with "
                        f"iCloud3 tracked_device {Device.devicename}")
            log_info_msg(log_msg)

            return entity_id

    return ''

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 3
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

def remove_unverified_device(Device):
    '''
    The Device was not verificed from the iCloud FamShr or FmF tracking methods.
    Remove it from the PyiCloud Device's list and the available Device's list,
    leaving only those that will be tracked. Note: The actual PyiCloud_data object
    will still exist for the device.
    '''
    devicename = Device.devicename
    if Device.device_id_famshr:
        Gb.Devices_by_icloud_device_id.pop(Device.device_id_famshr)
        Gb.PyiCloud_Devices_by_device_id.pop(Device.device_id_famshr)
        Gb.PyiCloud_Devices_by_device_id_famshr.pop(Device.device_id_famshr)
    if Device.device_id_fmf:
        Gb.Devices_by_icloud_device_id.pop(Device.device_id_fmf)
        Gb.PyiCloud_Devices_by_device_id.pop(Device.device_id_fmf)
        Gb.PyiCloud_Devices_by_device_id_fmf.pop(Device.device_id_fmf)

    Gb.Devices_by_devicename.pop(devicename)
    # Gb.Devices_by_devicename_not_tracked[devicename] = Device


    #If the devicename is not valid & verified, it will not be tracked
    if Device.tracking_method_ICLOUD:
        event_msg =(f"iCloud3 Error for {Device.devicename_fname} > "
            f"The iCloud Account did not return any device information for this device."
            f"CRLF{'-'*25}"
            f"CRLF 1. Restart iCloud3 (Event Log > Actions > Restart iCloud3) or restart HA."
            f"CRLF 2. Verify the devicename is correct on the `devices/device_name: {devicename}` "
            f"parameter.")
        post_event(event_msg)

    Gb.EvLog.tracking_msg += (f"{CRLF_DOT}{devicename} > {Device.fname} --> Not Tracking, ")

#------------------------------------------------------------------------------
def get_mobile_app_entities():
    '''
    Cycle through the HA Entity Registry and get all of the mobile_app entries
    '''
    _get_entity_registry_entities('mobile_app', 'device_tracker')
    if Gb.iosapp_entities != []:
        _get_mobile_app_notify_devicenames()
    else:
        event_msg =(f"iCloud3 Alert > No mobile_app device_tracker entities "
                    f"were found in the HA Entity Registry. The iOSApp "
                    f"will not be monitored for any device.")
        post_event(event_msg)

#------------------------------------------------------------------------------
def _get_entity_registry_entities(platform, entity_prefix):
    '''
    Read the /config/.storage/core.entity_registry file and return
    the entities for platform ('mobile_app', 'ios', etc)
    '''

    try:
        if Gb.entity_registry_file == '':
            Gb.entity_registry_file  = Gb.hass.config.path(
                    STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY)
        entity_prefix       += '.'
        Gb.iosapp_entities  = []
        entity_reg_file     = open(Gb.entity_registry_file)
        entity_reg_str      = entity_reg_file.read()
        entity_reg_data     = json.loads(entity_reg_str)
        entity_reg_entities = entity_reg_data['data']['entities']
        entity_reg_file.close()

        entity_devicename_list = ""
        for entity in entity_reg_entities:
            if (entity[PLATFORM] == platform):
                Gb.iosapp_entities.append(entity)

                # Select it if it starts with 'device_tracker.'
                if entity[ENTITY_ID].startswith(entity_prefix):
                    devicename = slugify(entity['original_name'])
                    devicename_iosapp_suffix = entity[ENTITY_ID].replace(entity_prefix, '')
                    crlf_dot_chk = CRLF_CHK if devicename in Gb.Devices_by_devicename else CRLF_DOT
                    entity_devicename_list += (f"{crlf_dot_chk}{devicename_iosapp_suffix}, "
                                                f"{entity['original_name']}")

        event_msg =(f"Entity Registry {platform} {entity_prefix[:-1]} entities found >{entity_devicename_list}")
        post_event(event_msg)

    except Exception as err:
        log_exception(err)
        pass

#------------------------------------------------------------------------------
def _get_mobile_app_notify_devicenames():
    '''
    Extract notify services devicenames from hass
    '''
    try:
        Gb.iosapp_notify_devicenames = []
        services = Gb.hass.services
        notify_services = dict(services.__dict__)['_services'][NOTIFY]

        for notify_service in notify_services:
            if notify_service.startswith(MOBILE_APP):
                Gb.iosapp_notify_devicenames.append(notify_service)
    except:
        pass

#------------------------------------------------------------------------------
def display_object_lists():
    '''
    Display the object list values
    '''
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


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 4
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

def create_Device_StationaryZone_object(Device):

    devicename = Device.devicename
    old_StatZones_by_devicename = Gb.StatZones_by_devicename.copy()
    Gb.StatZones = []
    Gb.StatZones_by_devicename = {}

    stat_zone_inzone_interval_secs = time_str_to_secs(Gb.stationary_inzone_interval_str)
    stat_zone_still_secs           = time_str_to_secs(Gb.stationary_still_time_str)

    # Setup Stationary zone for the device, set to base location
    if devicename in old_StatZones_by_devicename:
        StatZone = old_StatZones_by_devicename[devicename]
        StatZone.__init__(Device,
                    stat_zone_inzone_interval_secs,
                    stat_zone_still_secs,
                    Gb.stationary_zone_offset)
        post_monitor_msg(f"INITIALIZED StationaryZone-{devicename}_stationary")
    else:
        StatZone = StationaryZones(Device,
                    stat_zone_inzone_interval_secs,
                    stat_zone_still_secs,
                    Gb.stationary_zone_offset)
        post_monitor_msg(f"ADDED StationaryZone-{devicename}_stationary")

    Device.StatZone = StatZone
    Gb.StatZones.append(StatZone)
    Gb.StatZones_by_devicename[devicename] = StatZone
    Gb.state_to_zone[Device.stationary_zonename] = Device.stationary_zonename



#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 4
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
def post_restart_icloud3_complete_msg():
    for devicename, Device in Gb.Devices_by_devicename.items():   #
        Device.display_info_msg("Setup Complete, Locating Device")

    post_startup_event(NEW_LINE)
    event_msg =(f"{EVLOG_INIT_HDR}Initializing iCloud3 v{Gb.version} > Complete")
                # f"Took {round(time_now_secs()-self.start_timer, 2)} sec")
    post_startup_event(event_msg)
    Gb.EvLog.update_event_log_display("")