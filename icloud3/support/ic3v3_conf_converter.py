

from ..global_variables  import GlobalVariables as Gb
from ..const             import (HOME, APPLE_DEVICE_TYPES, DEVICE_TYPE_FNAME, ICLOUD,
                                NEW_LINE, CRLF, CRLF_DOT, CRLF_CHK, UNKNOWN,
                                WAZE, CALC, NEW_LINE, EVLOG_ERROR, EVLOG_NOTICE, EVLOG_ALERT, EVLOG_DEBUG,

                                CONFIG_IC3,
                                CONF_VERSION, CONF_UPDATE_DATE,
                                CONF_CONFIG_IC3_FILE_NAME, CONF_EVENT_LOG_CARD_DIRECTORY,
                                CONF_ENTITY_REGISTRY_FILE, CONF_EVENT_LOG_CARD_PROGRAM,

                                CONF_USERNAME, CONF_PASSWORD, CONF_ACCOUNT_NAME, CONF_NAME,
                                CONF_TRACKING_METHOD, CONF_IOSAPP_REQUEST_LOC_MAX_CNT,
                                CONF_TRACK_DEVICES, CONF_DEVICES, CONF_UNIT_OF_MEASUREMENT,
                                CONF_CREATE_SENSORS, CONF_EXCLUDE_SENSORS,
                                CONF_DISPLAY_TEXT_AS, CONF_ZONE,

                                CONF_MAX_INTERVAL, CONF_TRAVEL_TIME_FACTOR,
                                CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_STAT_ZONE_BASE_LATITUDE, CONF_STAT_ZONE_BASE_LONGITUDE,

                                CONF_INZONE_INTERVALS, CONF_INZONE_INTERVAL_DEFAULT,
                                CONF_INZONE_INTERVAL_IPHONE,
                                CONF_INZONE_INTERVAL_IPAD, CONF_INZONE_INTERVAL_WATCH,
                                CONF_INZONE_INTERVAL_IPOD, CONF_INZONE_INTERVAL_NO_IOSAPP,

                                CONF_DISPLAY_ZONE_FORMAT, CONF_CENTER_IN_ZONE,
                                CONF_TIME_FORMAT, CONF_INTERVAL, CONF_BASE_ZONE, CONF_INZONE_INTERVAL,
                                CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD,
                                CONF_IGNORE_GPS_ACC_INZONE, CONF_DISCARD_POOR_GPS_INZONE,
                                CONF_HIDE_GPS_COORDINATES, CONF_DISTANCE_METHOD,

                                CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                                CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED,
                                CONF_WAZE_HISTORY_MAX_DISTANCE, CONF_WAZE_HISTORY_MAP_TRACK_DIRECTION,

                                CONF_COMMAND, CONF_LOG_LEVEL, CONF_LEGACY_MODE,

                                CONF_IC3_DEVICENAME,
                                CONF_DEVICENAME, CONF_TRACK_FROM_ZONES, CONF_IOSAPP_SUFFIX,
                                CONF_IOSAPP_DEVICE, CONF_FAMSHR_DEVICENAME, CONF_FMF_EMAIL,
                                CONF_IOSAPP_ENTITY, CONF_NOIOSAPP, CONF_NO_IOSAPP,
                                CONF_IOSAPP_INSTALLED, CONF_PICTURE, CONF_EMAIL,
                                CONF_CONFIG, CONF_SOURCE, CONF_DEVICE_TYPE,

                                OPT_IOSAPP_DEVICE,

                                CONF_SENSOR_NAME, CONF_SENSOR_BADGE, CONF_SENSOR_BATTERY,
                                CONF_SENSOR_TRIGGER, CONF_SENSOR_INTERVAL, CONF_SENSOR_LAST_UPDATE,
                                CONF_SENSOR_NEXT_UPDATE, CONF_SENSOR_LAST_LOCATED, CONF_SENSOR_TRAVEL_TIME,
                                CONF_SENSOR_TRAVEL_TIME_MIN, CONF_SENSOR_ZONE_DISTANCE, CONF_SENSOR_WAZE_DISTANCE,
                                CONF_SENSOR_CALC_DISTANCE, CONF_SENSOR_TRAVEL_DISTANCE, CONF_SENSOR_GPS_ACCURACY,
                                CONF_SENSOR_DIR_OF_TRAVEL, CONF_SENSOR_ZONE, CONF_SENSOR_ZONE_NAME,
                                CONF_SENSOR_ZONE_TITLE, CONF_SENSOR_ZONE_FNAME, CONF_SENSOR_ZONE_TIMESTAMP,
                                CONF_SENSOR_POLL_CNT, CONF_SENSOR_INFO, CONF_SENSOR_LAST_ZONE,
                                CONF_SENSOR_LAST_ZONE_NAME, CONF_SENSOR_LAST_ZONE_TITLE, CONF_SENSOR_LAST_ZONE_FNAME,
                                CONF_SENSOR_BATTERY_STATUS, CONF_SENSOR_ALTITUDE, CONF_SENSOR_VERTICAL_ACCURACY,

                                OPT_LOG_LEVEL, OPT_UNIT_OF_MEASUREMENT, OPT_TIME_FORMAT,
                                OPT_DISTANCE_METHOD, OPT_DISPLAY_ZONE_FORMAT, OPT_DISPLAY_ZONE_FORMAT_EXAMPLE,
                                OPT_WAZE_REGION,

                                DEFAULT_CONFIG_VALUES, DEFAULT_GENERAL_CONF, DEFAULT_TRACKING_CONF,
                                DEFAULT_SENSORS_CONF, CF_DEFAULT_IC3_CONF_FILE, DEFAULT_DEVICE_CONF,

                                CF_PROFILE, CF_DATA,
                                CF_DATA_TRACKING, CF_DATA_GENERAL, CF_DATA_SENSORS,
                                )

CONF_DEVICENAME                 = 'device_name'
CONF_NO_IOSAPP                  = 'no_iosapp'
CONF_IOSAPP_INSTALLED           = 'iosapp_installed'
CONF_IOSAPP_SUFFIX              = 'iosapp_suffix'
CONF_IOSAPP_ENTITY              = 'iosapp_entity'
CONF_EMAIL                      = 'email'
CONF_CONFIG                     = 'config'
CONF_SOURCE                     = 'source'

VALID_CONF_DEVICES_ITEMS = [CONF_DEVICENAME, CONF_EMAIL, CONF_PICTURE, CONF_NAME,
                            CONF_INZONE_INTERVAL, 'track_from_zone', CONF_IOSAPP_SUFFIX,
                            CONF_IOSAPP_ENTITY, CONF_IOSAPP_INSTALLED, CONF_NOIOSAPP,
                            CONF_NO_IOSAPP, CONF_TRACKING_METHOD, ]

SENSOR_ID_NAME_LIST = {
        'zon': CONF_SENSOR_ZONE,
        'lzon': CONF_SENSOR_LAST_ZONE,
        # 'bzon': BASE_ZONE,
        'zonn': CONF_SENSOR_ZONE_NAME,
        'zont': CONF_SENSOR_ZONE_TITLE,
        'zonfn': CONF_SENSOR_ZONE_FNAME,
        'lzonn': CONF_SENSOR_LAST_ZONE_NAME,
        'lzont': CONF_SENSOR_LAST_ZONE_TITLE,
        'lzonfn': CONF_SENSOR_LAST_ZONE_FNAME,
        'zonts': CONF_SENSOR_ZONE_TIMESTAMP,
        'zdis': CONF_SENSOR_ZONE_DISTANCE,
        'cdis': CONF_SENSOR_CALC_DISTANCE,
        'wdis': CONF_SENSOR_WAZE_DISTANCE,
        'tdis': CONF_SENSOR_TRAVEL_DISTANCE,
        'ttim': CONF_SENSOR_TRAVEL_TIME,
        'mtim': CONF_SENSOR_TRAVEL_TIME_MIN,
        'dir': CONF_SENSOR_DIR_OF_TRAVEL,
        'intvl':  CONF_SENSOR_INTERVAL,
        'lloc': CONF_SENSOR_LAST_LOCATED,
        'lupdt': CONF_SENSOR_LAST_UPDATE,
        'nupdt': CONF_SENSOR_NEXT_UPDATE,
        'cnt': CONF_SENSOR_POLL_CNT,
        'info': CONF_SENSOR_INFO,
        'trig': CONF_SENSOR_TRIGGER,
        'bat': CONF_SENSOR_BATTERY,
        'batstat': CONF_SENSOR_BATTERY_STATUS,
        'alt': CONF_SENSOR_ALTITUDE,
        'gpsacc': CONF_SENSOR_GPS_ACCURACY,
        'vacc': CONF_SENSOR_VERTICAL_ACCURACY,
        'badge': CONF_SENSOR_BADGE,
        'name': CONF_SENSOR_NAME,
        }

from ..helpers.base      import (instr, _traceha, log_info_msg,
                                read_storage_icloud3_configuration_file,
                                write_storage_icloud3_configuration_file, )


import os
import json
from   homeassistant.util    import slugify
import homeassistant.util.yaml.loader as yaml_loader
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
        self.config_parm_sensors  = DEFAULT_SENSORS_CONF.copy()

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
            dta_list = config_yaml_recds[CONF_DISPLAY_TEXT_AS]
            for i in range(10 - len(dta_list)):
                dta_list.append('')
            config_yaml_recds[CONF_DISPLAY_TEXT_AS] = dta_list

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
            device_fields = DEFAULT_DEVICE_CONF.copy()

            log_info_msg(f"Extracted device - {devicename}")
            for pname, pvalue in device.items():
                if pname in VALID_CONF_DEVICES_ITEMS:
                    if pname == CONF_DEVICENAME:
                        devicename = slugify(pvalue)

                        name, device_type = self._extract_name_device_type(pvalue)
                        device_fields[CONF_IC3_DEVICENAME] = devicename
                        device_fields[CONF_NAME]           = name
                        device_fields[CONF_FAMSHR_DEVICENAME]  = devicename
                        device_fields[CONF_IOSAPP_DEVICE]  = devicename
                        device_fields[CONF_DEVICE_TYPE]    = device_type

                    #You can track from multiple zones, cycle through zones and check each one
                    #The value can be zone name or zone friendly name. Change to zone name.
                    elif pname == 'track_from_zone':
                            if instr(pvalue, 'home') is False:
                                pvalue += ',home'
                            pvalue = pvalue.replace(', ', ',').lower()
                            tfz_list = pvalue.split(',')
                            device_fields[CONF_TRACK_FROM_ZONES] = tfz_list

                    elif pname == CONF_IOSAPP_SUFFIX:
                            device_fields[CONF_IOSAPP_DEVICE] = f"{devicename}_{pvalue}"
                    elif pname == CONF_IOSAPP_ENTITY:
                            device_fields[CONF_IOSAPP_DEVICE] = pvalue

                    elif pname == CONF_EMAIL:
                        device_fields[CONF_FMF_EMAIL] = pvalue

                    elif pname == CONF_PICTURE:
                        pvalue = pvalue.replace('local', '').replace('www', '').replace('/', '')
                        device_fields[CONF_PICTURE] = pvalue

                    elif pname in [CONF_NOIOSAPP, CONF_NO_IOSAPP] and pvalue:
                        device_fields[CONF_IOSAPP_DEVICE] = OPT_IOSAPP_DEVICE[1]

                    else:
                        device_fields[pname] = pvalue
            device_fields[CONF_IOSAPP_DEVICE] = OPT_IOSAPP_DEVICE[0]
            device_fields.pop("cancel_update")
            devices_list.append(device_fields)

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

                self.config_parm_general[CONF_INZONE_INTERVAL_DEFAULT] = iztype_iztime.get('inzone_interval', '332 hrs')
                self.config_parm_general[CONF_INZONE_INTERVAL_IPHONE] = iztype_iztime.get('iphone', '332 hrs')
                self.config_parm_general[CONF_INZONE_INTERVAL_IPAD] = iztype_iztime.get('ipad', '332 hrs')
                self.config_parm_general[CONF_INZONE_INTERVAL_WATCH] = iztype_iztime.get('watch', '3315 mins')
                self.config_parm_general[CONF_INZONE_INTERVAL_IPOD] = iztype_iztime.get('ipod', '332 hrs')
                self.config_parm_general[CONF_INZONE_INTERVAL_NO_IOSAPP] = iztype_iztime.get('no_iosapp', '3315 mins')

            elif pname == 'stationary_zone_offset':
                sz_offset = pvalue.split(',')
                self.config_parm_general[CONF_STAT_ZONE_BASE_LATITUDE]  = float(sz_offset[0])
                self.config_parm_general[CONF_STAT_ZONE_BASE_LONGITUDE] = float(sz_offset[1])


        except Exception as err:
            self.log_exception(err)
            pass

        return

    def _set_sensors(self, pname, pvalue):
        for sensor in self.config_parm_sensors.keys():
            # Set all to True if excluding, False if creating
            self.config_parm_sensors[sensor] = (pname == 'exclude_sensors')
        _traceha(f"{self.config_parm_sensors=}")
        if type(pvalue) == list:
            pvalue = (",".join(pvalue))

        sensor_list = pvalue.split(',')
        for sensor in sensor_list:
            sabbrev = sensor.strip()
            if sabbrev in SENSOR_ID_NAME_LIST:
                sname = SENSOR_ID_NAME_LIST[sabbrev]
                # Set to True if creating, False if excluding
                if sname in self.config_parm_sensors:
                    self.config_parm_sensors[sname] = (pname == 'create_sensors')
        _traceha(f"{self.config_parm_sensors=}")

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
            # Gb.config_track_devices_change_flag = False
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

        _traceha(f"{self.config_parm_general=}")
        _traceha(f"{Gb.conf_general=}")

        Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE
        Gb.conf_profile   = Gb.conf_file_data[CF_PROFILE]
        Gb.conf_data      = Gb.conf_file_data[CF_DATA]

        Gb.conf_tracking = Gb.conf_data[CF_DATA_TRACKING]
        Gb.conf_devices  = Gb.conf_data[CF_DATA_TRACKING][CONF_DEVICES]
        Gb.conf_general  = Gb.conf_data[CF_DATA_GENERAL]
        Gb.conf_sensors  = Gb.conf_data[CF_DATA_SENSORS]

        Gb.conf_tracking[CONF_USERNAME]                  = self.config_parm_tracking[CONF_USERNAME]
        Gb.conf_tracking[CONF_PASSWORD]                  = self.config_parm_tracking[CONF_PASSWORD]
        Gb.conf_tracking[CONF_DEVICES]                   = self.config_ic3_track_devices_fields
        Gb.conf_devices                                  = self.config_ic3_track_devices_fields

        Gb.conf_profile[CONF_EVENT_LOG_CARD_DIRECTORY]   = self.config_parm_general[CONF_EVENT_LOG_CARD_DIRECTORY]
        Gb.conf_profile[CONF_EVENT_LOG_CARD_PROGRAM]     = self.config_parm_general[CONF_EVENT_LOG_CARD_PROGRAM]

        Gb.conf_general[CONF_UNIT_OF_MEASUREMENT]        = self._set_option_list_item(CONF_UNIT_OF_MEASUREMENT)
        Gb.conf_general[CONF_TIME_FORMAT]                = self._set_option_list_item(CONF_TIME_FORMAT)
        Gb.conf_general[CONF_TRAVEL_TIME_FACTOR]         = self.config_parm_general[CONF_TRAVEL_TIME_FACTOR]
        Gb.conf_general[CONF_DISTANCE_METHOD]            = self._set_option_list_item(CONF_DISTANCE_METHOD)
        Gb.conf_general[CONF_MAX_INTERVAL]               = self.config_parm_general[CONF_MAX_INTERVAL]
        Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]     = self.config_parm_general[CONF_GPS_ACCURACY_THRESHOLD]
        Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD]     = self.config_parm_general[CONF_OLD_LOCATION_THRESHOLD]
        Gb.conf_general[CONF_LOG_LEVEL]                  = OPT_LOG_LEVEL[0]
        Gb.conf_general[CONF_DISPLAY_ZONE_FORMAT]        = self._set_option_list_item(CONF_DISPLAY_ZONE_FORMAT)
        Gb.conf_general[CONF_CENTER_IN_ZONE]             = self.config_parm_general[CONF_CENTER_IN_ZONE]
        Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]    = self.config_parm_general.get(CONF_DISCARD_POOR_GPS_INZONE, False) \
                                                            or self.config_parm_general.get(CONF_IGNORE_GPS_ACC_INZONE, False)
        Gb.conf_general[CONF_WAZE_REGION]                = self._set_option_list_item(CONF_WAZE_REGION)
        Gb.conf_general[CONF_WAZE_MIN_DISTANCE]          = self.config_parm_general[CONF_WAZE_MIN_DISTANCE]
        Gb.conf_general[CONF_WAZE_MAX_DISTANCE]          = self.config_parm_general[CONF_WAZE_MAX_DISTANCE]
        Gb.conf_general[CONF_WAZE_REALTIME]              = self.config_parm_general[CONF_WAZE_REALTIME]

        Gb.conf_general[CONF_STAT_ZONE_STILL_TIME]      = self.config_parm_general[CONF_STAT_ZONE_STILL_TIME]
        Gb.conf_general[CONF_STAT_ZONE_BASE_LATITUDE]  = self.config_parm_general[CONF_STAT_ZONE_BASE_LATITUDE]
        Gb.conf_general[CONF_STAT_ZONE_BASE_LONGITUDE] = self.config_parm_general[CONF_STAT_ZONE_BASE_LONGITUDE]
        Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL] = self.config_parm_general[CONF_STAT_ZONE_INZONE_INTERVAL]
        Gb.conf_general[CONF_DISPLAY_TEXT_AS]            = self.config_parm_general[CONF_DISPLAY_TEXT_AS]


        write_storage_icloud3_configuration_file()
        # if Gb.mode_integration:
        # try:
        #     with open(Gb.icloud3_config_filename, 'w') as f:
        #         Gb.conf_profile[CONF_UPDATE_DATE] = ''
        #         json.dump(Gb.conf_file_data, f, indent=4)
        # except Exception as err:
        #     _LOGGER.exception(err)

        log_info_msg(f"Created iCloud3 configuration file - {Gb.icloud3_config_filename}")

    #--------------------------------------------------------------------
    def _set_option_list_item(self, pname):

        pvalue =  self.config_parm_general[pname]
        option_list = None
        if pname == CONF_UNIT_OF_MEASUREMENT:
            option_list = OPT_UNIT_OF_MEASUREMENT
        elif pname == CONF_TIME_FORMAT:
            option_list = OPT_TIME_FORMAT
        elif pname == CONF_DISTANCE_METHOD:
            option_list = OPT_DISTANCE_METHOD
        elif pname == CONF_DISPLAY_ZONE_FORMAT:
            option_list = OPT_DISPLAY_ZONE_FORMAT
        elif pname == CONF_LOG_LEVEL:
            option_list = OPT_LOG_LEVEL
        elif pname == CONF_WAZE_REGION:
            option_list = OPT_WAZE_REGION

        if option_list:
            return self._search_option_list(option_list, pvalue)
        else:
            return pvalue

    def _search_option_list(self, option_list, pvalue):

        for option in option_list:
            if option.startswith(str(pvalue)):
                return option
        return option_list[0]

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
