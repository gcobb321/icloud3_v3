

from ..global_variables  import GlobalVariables as Gb
from ..const             import (HOME, RARROW, APPLE_DEVICE_TYPES, DEVICE_TYPE_FNAME, ICLOUD,
                                WAZE, CALC, NEW_LINE, EVLOG_ERROR, EVLOG_NOTICE, EVLOG_ALERT, EVLOG_DEBUG,

                                CONFIG_IC3,
                                CONF_VERSION, CONF_UPDATE_DATE,
                                CONF_CONFIG_IC3_FILE_NAME, CONF_EVENT_LOG_CARD_DIRECTORY,
                                CONF_ENTITY_REGISTRY_FILE, CONF_EVENT_LOG_CARD_PROGRAM,

                                CONF_USERNAME, CONF_PASSWORD, CONF_ACCOUNT_NAME, CONF_FNAME, CONF_NAME,
                                CONF_TRACKING_METHOD, CONF_IOSAPP_REQUEST_LOC_MAX_CNT,
                                CONF_TRACK_DEVICES, CONF_DEVICES, CONF_UNIT_OF_MEASUREMENT,
                                CONF_CREATE_SENSORS, CONF_EXCLUDE_SENSORS,
                                CONF_DISPLAY_TEXT_AS, CONF_ZONE,

                                CONF_MAX_INTERVAL, CONF_TRAVEL_TIME_FACTOR,
                                CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_STAT_ZONE_BASE_LATITUDE, CONF_STAT_ZONE_BASE_LONGITUDE,

                                CONF_INZONE_INTERVALS, IPHONE, IPAD, WATCH, AIRPODS, NO_IOSAPP,

                                CONF_DISPLAY_ZONE_FORMAT, CONF_CENTER_IN_ZONE,
                                CONF_TIME_FORMAT, CONF_INTERVAL, CONF_BASE_ZONE, CONF_INZONE_INTERVAL,
                                CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD,
                                CONF_IGNORE_GPS_ACC_INZONE, CONF_DISCARD_POOR_GPS_INZONE,
                                CONF_HIDE_GPS_COORDINATES, CONF_DISTANCE_METHOD,

                                CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                                CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED,
                                CONF_WAZE_HISTORY_MAX_DISTANCE, CONF_WAZE_HISTORY_TRACK_DIRECTION,

                                CONF_COMMAND, CONF_LOG_LEVEL, CONF_LEGACY_MODE,

                                CONF_IC3_DEVICENAME,
                                CONF_DEVICENAME, CONF_TRACK_FROM_ZONES, CONF_IOSAPP_SUFFIX,
                                CONF_IOSAPP_DEVICE, CONF_FAMSHR_DEVICENAME, CONF_FMF_EMAIL,
                                CONF_IOSAPP_ENTITY, CONF_NO_IOSAPP,
                                CONF_IOSAPP_INSTALLED, CONF_PICTURE, CONF_EMAIL,
                                CONF_CONFIG, CONF_SOURCE, CONF_DEVICE_TYPE,

                                NAME, BADGE, BATTERY,
                                TRIGGER, INTERVAL, LAST_UPDATE,
                                NEXT_UPDATE, LAST_LOCATED, TRAVEL_TIME, DIR_OF_TRAVEL,
                                TRAVEL_TIME_MIN, ZONE_DISTANCE, WAZE_DISTANCE,
                                CALC_DISTANCE, TRAVEL_DISTANCE, GPS_ACCURACY,
                                ZONE, ZONE_FNAME, ZONE_NAME,
                                ZONE_DATETIME,
                                POLL_COUNT, INFO,
                                LAST_ZONE, LAST_ZONE_FNAME, LAST_ZONE_NAME,
                                BATTERY_STATUS, ALTITUDE, VERTICAL_ACCURACY,

                                DEFAULT_CONFIG_VALUES, DEFAULT_GENERAL_CONF, DEFAULT_TRACKING_CONF,
                                DEFAULT_PROFILE_CONF, DEFAULT_DEVICE_CONF, DEFAULT_SENSORS_CONF,
                                DEFAULT_SENSORS_CONF, CF_DEFAULT_IC3_CONF_FILE, DEFAULT_DEVICE_CONF,
                                EVENT_LOG_CARD_WWW_DIRECTORY, EVENT_LOG_CARD_WWW_JS_PROG,

                                CF_PROFILE, CF_DATA,
                                CF_DATA_TRACKING, CF_DATA_GENERAL, CF_DATA_SENSORS,
                                )
# from ..config_flow      import (OPT_LOG_LEVEL, OPT_UNIT_OF_MEASUREMENT, OPT_TIME_FORMAT,
#                                 OPT_DISTANCE_METHOD, OPT_DISPLAY_ZONE_FORMAT,
#                                 OPT_WAZE_REGION,)

CONF_DEVICENAME       = 'device_name'
CONF_NO_IOSAPP        = 'no_iosapp'
CONF_IOSAPP_INSTALLED = 'iosapp_installed'
CONF_IOSAPP_SUFFIX    = 'iosapp_suffix'
CONF_IOSAPP_ENTITY    = 'iosapp_entity'
CONF_EMAIL            = 'email'
CONF_CONFIG           = 'config'
CONF_SOURCE           = 'source'

VALID_CONF_DEVICES_ITEMS = [CONF_DEVICENAME, CONF_EMAIL, CONF_PICTURE, CONF_NAME,
                            CONF_INZONE_INTERVAL, 'track_from_zone', CONF_IOSAPP_SUFFIX,
                            CONF_IOSAPP_ENTITY, CONF_IOSAPP_INSTALLED,
                            CONF_NO_IOSAPP, CONF_TRACKING_METHOD, ]

SENSOR_ID_NAME_LIST = {
        'zon': ZONE,
        'lzon': LAST_ZONE,
        # 'bzon': BASE_ZONE,
        'zonn': ZONE_NAME,
        'zont': ZONE_NAME,
        'zonfn': ZONE_FNAME,
        'lzonn': LAST_ZONE_NAME,
        'lzont': LAST_ZONE_NAME,
        'lzonfn': LAST_ZONE_FNAME,
        'zonts': ZONE_DATETIME,
        'zdis': ZONE_DISTANCE,
        'cdis': CALC_DISTANCE,
        'wdis': WAZE_DISTANCE,
        'tdis': TRAVEL_DISTANCE,
        'ttim': TRAVEL_TIME,
        'mtim': TRAVEL_TIME_MIN,
        'dir': DIR_OF_TRAVEL,
        'intvl':  INTERVAL,
        'lloc': LAST_LOCATED,
        'lupdt': LAST_UPDATE,
        'nupdt': NEXT_UPDATE,
        'cnt': POLL_COUNT,
        'info': INFO,
        'trig': TRIGGER,
        'bat': BATTERY,
        'batstat': BATTERY_STATUS,
        'alt': ALTITUDE,
        'gpsacc': GPS_ACCURACY,
        'vacc': VERTICAL_ACCURACY,
        'badge': BADGE,
        'name': NAME,
        }

CONF_SENSORS_DEVICE_LIST            = ['name', 'badge', 'battery', 'battery_status', 'info',]
CONF_SENSORS_TRACKING_UPDATE_LIST   = ['interval', 'last_update', 'next_update', 'last_located']
CONF_SENSORS_TRACKING_TIME_LIST     = ['travel_time', 'travel_time_min']
CONF_SENSORS_TRACKING_DISTANCE_LIST = ['zone_distance', 'home_distance', 'dir_of_travel', 'travel_distance']
CONF_SENSORS_TRACKING_BY_ZONES_LIST = []
CONF_SENSORS_TRACKING_OTHER_LIST    = ['trigger', 'waze_distance', 'calc_distance', 'pll_count']
CONF_SENSORS_ZONE_LIST              = ['zone', 'zone_fname', 'zone_name', 'zone_timestamp', 'last_zone']
CONF_SENSORS_OTHER_LIST             = ['gps_accuracy', 'vertical_accuracy', 'altitude']

from ..helpers.base      import (instr, _traceha, log_info_msg, )


import os
import json
from   homeassistant.util    import slugify
import homeassistant.util.yaml.loader as yaml_loader
from .                       import start_ic3
import logging
_LOGGER = logging.getLogger(__name__)

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3V3ConfigurationConverter(object):

    def __init__(self):
        self.config_track_devices_fields = []
        self.config_ic3_track_devices_fields = []
        self.devicename_list = []

        self.config_parm          = DEFAULT_CONFIG_VALUES.copy()
        self.config_parm_general  = DEFAULT_GENERAL_CONF.copy()
        self.config_parm_tracking = DEFAULT_TRACKING_CONF.copy()
        self.config_parm_sensors  ={}

        Gb.conf_profile   = DEFAULT_PROFILE_CONF.copy()
        Gb.conf_tracking  = DEFAULT_TRACKING_CONF.copy()
        Gb.conf_devices   = []
        Gb.conf_general   = DEFAULT_GENERAL_CONF.copy()
        Gb.conf_sensors   = DEFAULT_SENSORS_CONF.copy()
        Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()

    #######################################################################
    #
    #   EXTRACT ICLOUD3 PARAMETERS FROM THE CONFIG_IC3.YAML PARAMETER FILE.
    #
    #   The ic3 parameters are specified in the HA configuration.yaml file and
    #   processed when HA starts. The 'config_ic3.yaml' file lets you specify
    #   parameters at HA startup time or when iCloud3 is restarted using the
    #   Restart-iC3 command on the Event Log screen. When iC3 is restarted,
    #   the parameters will override those specified at HA startup time.
    #
    #   1. You can, for example, add new tracked devices without restarting HA.
    #   2. You can specify the username, password and tracking method in this
    #      file but these items are onlyu processed when iC3 initially loads.
    #      A restart will discard these items
    #
    #   Default file is config/custom_components/icloud3/config-ic3.yaml
    #   if no '/' on the config_ic3_filename parameter:
    #       check the default directory
    #       if not found, check the /config directory
    #
    #######################################################################
    def convert_v2_config_files_to_v3(self):
        log_info_msg('Converting iCloud3 configuration parameters')
        self._extract_config_parameters(Gb.config_parm_ha_config_yaml)

        config_ic3_records = self._get_config_ic3_records()
        self._extract_config_parameters(config_ic3_records)
        self._set_data_fields_from_config_parameter_dictionary()
        return

    #-------------------------------------------------------------------------
    def _extract_config_parameters(self, config_yaml_recds):
        '''
        OrderedDict([('devices', [OrderedDict([('device_name', 'Gary-iPhone'),
        ('name', 'Gary'), ('email', 'gcobb321@gmail.com'),
        ('picture', 'gary.png'), ('track_from_zone', 'warehouse')]), OrderedDict([('device_name', 'lillian_iphone'),
        ('name', 'Lillian'), ('picture', 'lillian.png'), ('email', 'lilliancobb321@gmail.com')])]),
        ('display_text_as', ['gcobb321@gmail.com > gary_2fa@email.com', 'lilliancobb321@gmail.com > lillian_2fa@email.com',
        'twitter:@lillianhc > twitter:@lillian_twitter_handle', 'gary-real-email@gmail.com > gary_secret@email.com',
        'lillian-real-email@gmail.com > lillian_secret@email.com']),
        ('inzone_interval', '30 min'),
        ('display_zone_format', FNAME)])
        '''

        if CONF_DISPLAY_TEXT_AS in config_yaml_recds:
            display_text_as = DEFAULT_GENERAL_CONF[CONF_DISPLAY_TEXT_AS].copy()
            cdta_idx = 0
            for dta_text in config_yaml_recds[CONF_DISPLAY_TEXT_AS]:
                if dta_text.strip():
                    display_text_as[cdta_idx] = dta_text
                    cdta_idx += 1

            config_yaml_recds[CONF_DISPLAY_TEXT_AS] = display_text_as

        log_info_msg(f"Converting parameters - HA configuration.yaml")
        for pname, pvalue in config_yaml_recds.items():
            if pname == CONF_DEVICES:
                pvalue = json.loads(json.dumps(pvalue))
                self.config_ic3_track_devices_fields.extend(\
                        self._get_devices_list_from_config_devices_parm(pvalue, CONFIG_IC3))

            else:
                self._set_non_device_parm_in_config_parameter_dictionary(pname, pvalue)

        return

    #-------------------------------------------------------------------------
    def _get_config_ic3_records(self):
        try:
            config_yaml_recds = {}

            # Get config_ic3.yaml file name from parameters, then reformat since adding to the '/config/ variable
            config_ic3_filename = Gb.config_parm_ha_config_yaml.get(CONF_CONFIG_IC3_FILE_NAME, CONFIG_IC3)
            config_ic3_filename = config_ic3_filename.replace("config/", "")
            if config_ic3_filename.startswith('/'):
                config_ic3_filename = config_ic3_filename[1:]
            if config_ic3_filename.endswith('.yaml') is False:
                config_ic3_filename = f"{config_ic3_filename}.yaml"

            if instr(config_ic3_filename, "/"):
                pass

            elif os.path.exists(f"{Gb.ha_config_directory}{config_ic3_filename}"):
                config_ic3_filename = (f"{Gb.ha_config_directory}{config_ic3_filename}")

            elif os.path.exists(f"{Gb.icloud3_directory}/{config_ic3_filename}"):
                config_ic3_filename = (f"{Gb.icloud3_directory}/{config_ic3_filename}")

            config_ic3_filename = config_ic3_filename.replace("//", "/")

            log_info_msg(f"Converting parameters - {config_ic3_filename}")
            if os.path.exists(config_ic3_filename) is False:
                msg = (f"Not converting configuration parameters. config_ic3.yaml file does not exist "
                        f"or is not specified ({config_ic3_filename})")
                log_info_msg(msg)
                return {}

            log_info_msg(f"Converting configuration parameters in {config_ic3_filename}")

            Gb.config_ic3_yaml_filename = config_ic3_filename
            config_yaml_recds = yaml_loader.load_yaml(config_ic3_filename)

        except Exception as err:
            self.log_exception(err)

        return config_yaml_recds

    #-------------------------------------------------------------------------
    def _get_devices_list_from_config_devices_parm(self, conf_devices_parameter, source_file):
        '''
        Process the CONF_DEVICES parameter. This is the general routine for parsing
        the parameter and creating a dictionary (devices_list) containing values
        associated with each device_name.

        Input:      The CONF_DEVICES parameter
        Returns:    The dictionary with the fields associated with all of the devices
        '''
        devices_list = []

        for device in conf_devices_parameter:
            devicename = slugify(device[CONF_DEVICENAME])
            if devicename in self.devicename_list:
                continue
            self.devicename_list.append(devicename)
            conf_device = DEFAULT_DEVICE_CONF.copy()

            log_info_msg(f"Extracted device - {devicename}")
            for pname, pvalue in device.items():
                if pname in VALID_CONF_DEVICES_ITEMS:
                    if pname == CONF_DEVICENAME:
                        devicename = slugify(pvalue)

                        fname, device_type = self._extract_name_device_type(pvalue)
                        conf_device[CONF_IC3_DEVICENAME]    = devicename
                        conf_device[CONF_FNAME]             = fname
                        conf_device[CONF_FAMSHR_DEVICENAME] = devicename
                        conf_device[CONF_DEVICE_TYPE]       = device_type

                    #You can track from multiple zones, cycle through zones and check each one
                    #The value can be zone name or zone friendly name. Change to zone name.
                    elif pname == 'track_from_zone':
                            if instr(pvalue, 'home') is False:
                                pvalue += ',home'
                            pvalue = pvalue.replace(', ', ',').lower()
                            tfz_list = pvalue.split(',')
                            conf_device[CONF_TRACK_FROM_ZONES] = tfz_list

                    elif pname == CONF_EMAIL:
                        conf_device[CONF_FMF_EMAIL] = pvalue

                    elif pname == CONF_NAME:
                        conf_device[CONF_FNAME] = pvalue

                    elif pname == CONF_IOSAPP_SUFFIX:
                            conf_device[CONF_IOSAPP_DEVICE] = f"{devicename}{pvalue}"

                    elif pname == CONF_IOSAPP_ENTITY:
                            conf_device[CONF_IOSAPP_DEVICE] = pvalue

                    elif pname == CONF_NO_IOSAPP and pvalue:
                        conf_device[CONF_IOSAPP_DEVICE] = 'None'

                    elif pname == CONF_IOSAPP_INSTALLED and pvalue is False:
                        conf_device[CONF_IOSAPP_DEVICE] = 'None'

                    elif pname == CONF_TRACKING_METHOD:
                        if pvalue == 'fmf':
                            conf_device[CONF_FAMSHR_DEVICENAME] = 'None'
                        elif pvalue == 'iosapp':
                            conf_device[CONF_FAMSHR_DEVICENAME] = 'None'
                            conf_device[CONF_FMF_EMAIL] = 'None'

                    elif pname == CONF_PICTURE:
                        pvalue = pvalue.replace('local', '').replace('www', '').replace('/', '')
                        conf_device[CONF_PICTURE] = pvalue

                    else:
                        conf_device[pname] = pvalue


            if "cancel_update" in conf_device:
                conf_device.pop("cancel_update")
            devices_list.append(conf_device)

        return devices_list

    #-------------------------------------------------------------------------
    def _set_non_device_parm_in_config_parameter_dictionary(self, pname, pvalue):
        '''
        Set the config_parameters[key] master parameter dictionary from the
        config_ic3 parameter file

        Input:      parameter name & value
        Output:     Valid parameters are added to the config_parameter[pname] dictionary
        '''
        try:
            if pname == "":
                return

            if pname in self.config_parm_general:
                self.config_parm_general[pname] = pvalue

            elif pname in self.config_parm_tracking:
                self.config_parm_tracking[pname] = pvalue

            elif pname in ['exclude_sensors', 'create_sensors']:
                self._set_sensors(pname, pvalue)

            elif pname == CONF_INZONE_INTERVALS:
                iztype_iztime = {}
                for iztype_iztimes in pvalue:
                    for iztype, iztime in iztype_iztimes.items():
                        iztype_iztime[iztype] = iztime

                inzone_intervals = {}
                inzone_intervals['default'] = iztype_iztime.get('inzone_interval', '02:00:00')
                inzone_intervals[IPHONE]    = iztype_iztime.get(IPHONE, '02:00:00')
                inzone_intervals[IPAD]      = iztype_iztime.get(IPAD, '02:00:00')
                inzone_intervals[WATCH]     = iztype_iztime.get(WATCH, '00:15:00')
                inzone_intervals[AIRPODS]   = iztype_iztime.get(AIRPODS, '00:15:00')
                inzone_intervals[NO_IOSAPP] = iztype_iztime.get(NO_IOSAPP, '00:15:00')
                self.config_parm_general[CONF_INZONE_INTERVALS] = inzone_intervals.copy()

            elif pname == 'stationary_zone_offset':
                sz_offset = pvalue.split(',')
                self.config_parm_general[CONF_STAT_ZONE_BASE_LATITUDE]  = float(sz_offset[0])
                self.config_parm_general[CONF_STAT_ZONE_BASE_LONGITUDE] = float(sz_offset[1])


        except Exception as err:
            self.log_exception(err)
            pass

        return

    def _set_sensors(self, pname, pvalue):
        device_list            = []
        tracking_update        = []
        tracking_time_list     = []
        tracking_distance_list = []
        tracking_other_list    = []
        zone_list              = []
        other_list             = []

        sensor_list = []
        pvalue = f",{pvalue.replace(' ', '')},"
        if pname == 'exclude_sensors':
            for sensor_abbrev, sensor in SENSOR_ID_NAME_LIST.items():
                if instr(pvalue, f",{sensor_abbrev},") is False:
                    sensor_list.append(sensor)

        elif pname == 'create_sensors':
            for sensor_abbrev, sensor in SENSOR_ID_NAME_LIST.items():
                 if instr(pvalue, f",{sensor_abbrev},"):
                    sensor_list.append(sensor)

        for sname in sensor_list:
            if sname in ['name', 'badge', 'battery', 'battery_status', 'info',]:
                device_list.append(sname)
            if sname in ['interval', 'last_update', 'next_update', 'last_located']:
                tracking_update.append(sname)
            if sname in ['travel_time', 'travel_time_min']:
                tracking_time_list.append(sname)
            if sname in ['zone_distance', 'home_distance', 'dir_of_travel', 'travel_distance']:
                tracking_distance_list.append(sname)
            if sname in ['trigger', 'waze_distance', 'calc_distance', 'pll_count']:
                tracking_other_list.append(sname)
            if sname in ['zone', 'zone_fname', 'zone_name', 'zone_title', 'zone_timestamp']:
                if sname not in zone_list:
                    zone_list.append(sname)
            if sname in ['last_zone', 'last_zone_fname', 'last_zone_name', 'last_zone_title']:
                if 'last_zone' not in zone_list:
                    zone_list.append('last_zone')
            if sname in ['gps_accuracy', 'vertical_accuracy',   'altitude']:
                other_list.append(sname)

        Gb.conf_sensors['device']            = device_list
        Gb.conf_sensors['tracking_update']   = tracking_update
        Gb.conf_sensors['tracking_time']     = tracking_time_list
        Gb.conf_sensors['tracking_distance'] = tracking_distance_list
        Gb.conf_sensors['tracking_by_zones'] = []
        Gb.conf_sensors['tracking_other']    = tracking_other_list
        Gb.conf_sensors['zone']              = zone_list
        Gb.conf_sensors['other']             = other_list

        return


    #######################################################################
    #
    #   GET DEVICES FROM HA CONFIGURATION.YAML devices parameter
    #
    #######################################################################
    def _get_devices_list_from_ha_config_yaml_file(self):

        try:
            # Extract device fields from ha config file 'devices:' parameter
            self.config_track_devices_fields.extend(
                    self._get_devices_list_from_config_devices_parm(\
                            Gb.config_parm_ha_config_yaml[CONF_DEVICES], 'HA config'))
                            # Gb.devices              , 'HA config'))

            # Get device fields from iCloud3 config_ic3 file
            self.config_track_devices_fields.extend(self.config_ic3_track_devices_fields)

            # See if there are any changes to the devices parameter on a restart. If nothing
            # changed, only change parameter values and bypass Stages 2, 3 & 4.
            if self.config_track_devices_fields != self.config_track_devices_fields_last_restart:
                self.config_track_devices_fields_last_restart = []
                self.config_track_devices_fields_last_restart.extend(self.config_track_devices_fields)
                # Gb.config_track_devices_change_flag = True

        except Exception as err:
            # log_exception(err)
            pass


    #######################################################################
    #
    #   INITIALIZE THE GLOBAL VARIABLES WITH THE CONFIGURATION FILE PARAMETER
    #   VALUES
    #
    #######################################################################
    def _set_data_fields_from_config_parameter_dictionary(self):
        '''
        Set the iCloud3 variables from the configuration parameters
        '''

        if 'stationary_still_time' in self.config_parm_general:
            self.config_parm_general[CONF_STAT_ZONE_STILL_TIME] = self.config_parm_general['stationary_still_time']
        if 'stationary_inzone_interval' in self.config_parm_general:
            self.config_parm_general[CONF_STAT_ZONE_INZONE_INTERVAL] = self.config_parm_general['stationary_inzone_interval']

        Gb.conf_tracking[CONF_USERNAME]                  = self.config_parm_tracking[CONF_USERNAME]
        Gb.conf_tracking[CONF_PASSWORD]                  = self.config_parm_tracking[CONF_PASSWORD]
        Gb.conf_tracking[CONF_DEVICES]                   = self.config_ic3_track_devices_fields

        Gb.conf_profile[CONF_EVENT_LOG_CARD_DIRECTORY]   = self.config_parm_general.get(CONF_EVENT_LOG_CARD_DIRECTORY, EVENT_LOG_CARD_WWW_DIRECTORY).replace('www', '').replace('/', '')
        Gb.conf_profile[CONF_EVENT_LOG_CARD_PROGRAM]     = self.config_parm_general.get(CONF_EVENT_LOG_CARD_PROGRAM, EVENT_LOG_CARD_WWW_JS_PROG)

        Gb.conf_general[CONF_UNIT_OF_MEASUREMENT]        = self.config_parm_general[CONF_UNIT_OF_MEASUREMENT].lower()
        Gb.conf_general[CONF_TIME_FORMAT]                = f"{self.config_parm_general[CONF_TIME_FORMAT]}-hour"
        Gb.conf_general[CONF_TRAVEL_TIME_FACTOR]         = self.config_parm_general[CONF_TRAVEL_TIME_FACTOR]
        Gb.conf_general[CONF_DISTANCE_METHOD]            = self.config_parm_general[CONF_DISTANCE_METHOD].lower()
        Gb.conf_general[CONF_MAX_INTERVAL]               = self.config_parm_general[CONF_MAX_INTERVAL]
        Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]     = self.config_parm_general[CONF_GPS_ACCURACY_THRESHOLD]
        Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD]     = self.config_parm_general[CONF_OLD_LOCATION_THRESHOLD]
        Gb.conf_general[CONF_LOG_LEVEL]                  = 'info'
        Gb.conf_general[CONF_DISPLAY_ZONE_FORMAT]        = self.config_parm_general[CONF_DISPLAY_ZONE_FORMAT].lower()
        Gb.conf_general[CONF_CENTER_IN_ZONE]             = self.config_parm_general[CONF_CENTER_IN_ZONE]
        Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]    = self.config_parm_general.get(CONF_DISCARD_POOR_GPS_INZONE, False)
        Gb.conf_general[CONF_WAZE_REGION]                = self.config_parm_general[CONF_WAZE_REGION].lower()
        Gb.conf_general[CONF_WAZE_MIN_DISTANCE]          = self.config_parm_general[CONF_WAZE_MIN_DISTANCE]
        Gb.conf_general[CONF_WAZE_MAX_DISTANCE]          = self.config_parm_general[CONF_WAZE_MAX_DISTANCE]
        Gb.conf_general[CONF_WAZE_REALTIME]              = self.config_parm_general[CONF_WAZE_REALTIME]

        Gb.conf_general[CONF_STAT_ZONE_STILL_TIME]      = self.config_parm_general[CONF_STAT_ZONE_STILL_TIME]
        Gb.conf_general[CONF_STAT_ZONE_BASE_LATITUDE]   = self.config_parm_general[CONF_STAT_ZONE_BASE_LATITUDE]
        Gb.conf_general[CONF_STAT_ZONE_BASE_LONGITUDE]  = self.config_parm_general[CONF_STAT_ZONE_BASE_LONGITUDE]
        Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL] = self.config_parm_general[CONF_STAT_ZONE_INZONE_INTERVAL]
        Gb.conf_general[CONF_DISPLAY_TEXT_AS]           = self.config_parm_general[CONF_DISPLAY_TEXT_AS]

        start_ic3.write_storage_icloud3_configuration_file()

        log_info_msg(f"Created iCloud3 configuration file - {Gb.icloud3_config_filename}")

    #--------------------------------------------------------------------
    def _extract_name_device_type(self, devicename):
        '''Extract the name and device type from the devicename'''

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

        except Exception as err:
            # log_exception(err)
            pass

        return (fname, device_type)

    #--------------------------------------------------------------------
    def log_exception(self, err):
        _LOGGER.exception(err)
