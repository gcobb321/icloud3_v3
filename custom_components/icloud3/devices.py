#------------------------------------------------------------------------------
#
#   This module handles all device data
#
#------------------------------------------------------------------------------
from .globals           import GlobalVariables as Gb
from .const_general import (HHMMSS_ZERO, HOME, NOT_HOME, UNKNOWN, NOT_SET, STATIONARY, CRLF, CRLF_DOT,
                            TRACKING_METHOD_FNAME, FMF, FAMSHR, IOSAPP, FAMSHR_FMF, DEVICE_TRACKER,
                            PAUSED, RESUMING, TRACKING_NORMAL, TRACKING_PAUSED, TRACKING_RESUMED,
                            HIGH_INTEGER, DATETIME_ZERO, NEAR_ZONE, REGION_ENTERED,
                            STAT_ZONE_NO_UPDATE, STAT_ZONE_MOVE_TO_BASE, )
from .const_attrs   import (CONF_NAME, CONF_EMAIL, CONF_DEVICE_TYPE, CONF_PICTURE, CONF_TRACK_FROM_ZONE,
                            CONF_IOSAPP_INSTALLED, CONF_NO_IOSAPP, CONF_IOSAPP_ENTITY, CONF_IOSAPP_SUFFIX,
                            CONF_TRACKING_METHOD,
                            CONF_INZONE_INTERVAL, CONF_CONFIG, CONF_SOURCE, FRIENDLY_NAME, ICON,
                            DEFAULT_CONFIG_VALUES, DEFAULT_INZONE_INTERVAL,
                            GPS_ACCURACY,  NEXT_UPDATE_TIME,DEVICE_STATUS_ONLINE,
                            LOCATION_SOURCE, NAME, ZONE, LAST_ZONE, INTO_ZONE_DATETIME, TRIGGER, BATTERY,
                            BATTERY_STATUS, VERT_ACCURACY, ALTITUDE, DEVICE_STATUS, LOW_POWER_MODE, PICTURE,
                            GPS, LATITUDE, LONGITUDE, LOCATED_DATETIME, UPDATE_DATETIME, INTO_ZONE_DATETIME, )

from .device_fm_zones   import DeviceFmZones

from .helpers.base      import (instr, is_inzone_zone, is_statzone,
                                post_event, post_error_msg, post_monitor_msg, log_exception,
                                _trace, _traceha, )
from .helpers.time      import (datetime_now, time_now_secs, secs_to_time, secs_to_time_str, secs_since,
                                time_to_12hrtime, datetime_to_secs, )
from .helpers.distance  import (calc_distance_km, )
from .helpers.format    import (format_gps, format_dist, format_dist_m, format_time_age, )
from .helpers.entity_io import (set_state_attributes, set_state_attributes, )


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class Devices(object):

    def __init__(self, devicename, device_fields):

        self.devicename          = devicename
        self.StatZone            = None
        self.stationary_zonename = (f"{self.devicename}_stationary")
        self.DeviceFmZoneHome    = None         # DeviceFmZone object for the Home zone
        self.DeviceFmZoneCurrent = None         # DeviceFmZone object last or currently being updated in determine_interval

        self.initialize()
        self.configure_device(device_fields)
        self.initialize_attrs()
        self.initialize_track_from_zones()

    def initialize(self):
        self.devicename_verified         = False

        # Operational variables
        self.tracking_status              = TRACKING_NORMAL
        self.update_timer                 = 0
        self.override_interval_secs       = 0
        self.dist_from_zone_km_small_move_total = 0
        self.device_tracker_entity_ic3    = (f"{DEVICE_TRACKER}{self.devicename}")
        self.into_zone_datetime           = ''
        self.located_secs                 = 0
        self.went_3km                     = False
        self.stationary_zone_update_control = STAT_ZONE_NO_UPDATE
        self.next_update_DeviceFmZone     = None    # Set to the DeviceFmZone when it's next_update_time is reached
        self.trace_text_change_1          = ''
        self.trace_text_change_2          = ''
        self.trace_text_change_3          = ''

        # Trigger & Update variables
        self.trigger                      = 'iCloud3'
        self.seen_this_device_flag        = False
        self.iosapp_zone_enter_secs       = 0
        self.iosapp_zone_enter_time       = HHMMSS_ZERO
        self.iosapp_zone_enter_zone       = ''
        self.iosapp_zone_exit_secs        = 0
        self.iosapp_zone_exit_time        = HHMMSS_ZERO
        self.iosapp_zone_exit_zone        = ''
        self.device_being_updated_flag    = False
        self.device_being_updated_retry_cnt = 0
        self.got_exit_trigger_flag        = False
        self.outside_no_exit_trigger_flag = False

        # Device location & gps fields
        self.old_loc_poor_gps_cnt    = 0
        self.old_loc_poor_gps_msg    = ''
        self.old_loc_threshold_secs  = 120
        self.poor_gps_flag           = False
        self.inzone_interval_secs    = 600    #7200
        self.data_source             = ''

        self.last_iosapp_msg         = ''
        self.last_device_monitor_msg = ''
        self.iosapp_stat_zone_action_msg_cnt = 0
        # self.waze_data_copied_from   = ''

        # Device Counters
        self.count_update_icloud     = 0
        self.count_update_iosapp     = 0
        self.count_discarded_update  = 0
        self.count_state_changed     = 0
        self.count_trigger_changed   = 0
        self.count_waze_locates      = 0
        self.time_waze_calls         = 0.0

        # Device iOSApp message fields
        self.iosapp_request_loc_sent_flag  = False
        self.iosapp_request_loc_sent_secs  = 0.0
        self.iosapp_request_loc_cnt        = 0
        self.iosapp_request_loc_retry_cnt  = 0

        # iOSApp state variables
        self.iosapp_data_state             = NOT_SET
        self.iosapp_data_latitude          = 0.0
        self.iosapp_data_longitude         = 0.0
        self.iosapp_data_state_secs        = 0
        self.iosapp_data_trigger_secs      = 0
        self.iosapp_data_secs              = 0
        self.iosapp_data_state_time        = HHMMSS_ZERO
        self.iosapp_data_trigger_time      = HHMMSS_ZERO
        self.iosapp_data_time              = HHMMSS_ZERO
        self.iosapp_data_trigger           = NOT_SET
        self.iosapp_data_gps_accuracy      = 0
        self.iosapp_data_vertical_accuracy = 0
        self.iosapp_data_battery_level     = 0
        self.iosapp_data_altitude          = 0

        self.iosapp_data_invalid_error_cnt = 0
        self.iosapp_data_updated_flag      = False
        self.iosapp_data_change_reason     = ''         # Why a state/trigger is causing an update
        self.iosapp_data_reject_reason     = ''         # Why a state/trigger was not updated
        self.iosapp_update_flag            = False
        self.last_iosapp_trigger           = ''

        self.icloud_update_flag            = False
        self.icloud_update_reason          = ''
        self.icloud_no_update_reason       = ''
        self.icloud_update_retry_flag      = False           # Set to True for initial locate
        self.icloud_initial_locate_done    = False

        # Location Data from iCloud or the iOS App
        self.dev_data_source         = NOT_SET          #icloud or iosapp data
        self.dev_data_fname          = ''
        self.dev_data_device_class   = 'iPhone'
        self.dev_data_battery_level  = 0
        self.dev_data_battery_status = UNKNOWN
        self.dev_data_device_status  = UNKNOWN
        self.dev_data_low_power_mode = False

        self.loc_data_zone           = NOT_SET
        self.loc_data_latitude       = 0.0
        self.loc_data_longitude      = 0.0
        self.loc_data_gps_accuracy   = 0
        self.loc_data_secs           = 0
        self.loc_data_time           = HHMMSS_ZERO
        self.loc_data_datetime       = DATETIME_ZERO
        self.loc_data_altitude       = 0.0
        self.loc_data_vert_accuracy  = 0
        self.loc_data_isold          = False
        self.loc_data_ispoorgps      = False
        self.lod_data_distance_moved = 0.0

        self.sensor_prefix            = (f"sensor.{self.devicename}_")

    def __repr__(self):
        return (f"<Device: {self.devicename}>")

#------------------------------------------------------------------------------
    def initialize_attrs(self):
        # device_tracker.[devicename] attributes for the Device
        self.attrs                     = {}
        self.kwargs                    = {}
        self.attrs[LOCATION_SOURCE]    = ''             #icloud:fmf/famshr or iosapp
        self.attrs[NAME]               = self.fname
        self.attrs[ZONE]               = NOT_SET
        self.attrs[LATITUDE]           = 0.0
        self.attrs[LONGITUDE]          = 0.0
        self.attrs[LAST_ZONE]          = NOT_SET
        self.attrs[INTO_ZONE_DATETIME] = ''
        self.attrs[TRIGGER]            = ''
        self.attrs[UPDATE_DATETIME]    = DATETIME_ZERO  #dt_util.utcnow().isoformat()[0:19]
        self.attrs[LOCATED_DATETIME]   = DATETIME_ZERO  #dt_util.utcnow().isoformat()[0:19]
        self.attrs[BATTERY]            = 0
        self.attrs[BATTERY_STATUS]     = UNKNOWN
        self.attrs[ALTITUDE]           = 0
        self.attrs[GPS_ACCURACY]       = 0
        self.attrs[VERT_ACCURACY]      = 0
        self.attrs[DEVICE_STATUS]      = UNKNOWN
        self.attrs[LOW_POWER_MODE]     = ''
        self.attrs[PICTURE]            = self.badge_picture

        self.kwargs[GPS]               = (0, 0)
        self.kwargs[BATTERY]           = 0
        self.kwargs[GPS_ACCURACY]      = 0
        self.kwargs['dev_id']          = self.devicename
        self.kwargs['host_name']       = self.fname
        self.kwargs['source_type']     = GPS

        self.attrs_located_secs   = 0

        self.info_msg_entity          = (f"sensor.{self.devicename}_info")
        self.info_msg                 = "● HA is initializing dev_trk attributes ●"
        self.info_msg_sensor_attrs    = {}
        self.info_msg_sensor_attrs[FRIENDLY_NAME] = f"{self.fname}Info"
        self.info_msg_sensor_attrs[ICON]          = "mdi:information-outline"

#------------------------------------------------------------------------------
    def configure_device(self, device_fields):
        # Configuration parameters

        email_parm = device_fields.get(CONF_EMAIL, '')
        if (type(email_parm) is str) is False:
            # email is actually a phone number used to identify the fmf device
            email_parm = (f"+{str(email_parm)}").replace('++', '+')

        self.fname            = device_fields.get(CONF_NAME, self.devicename)
        self.email            = email_parm
        self.devicename_email = email_parm
        self.picture          = device_fields.get(CONF_PICTURE, '')
        self.device_type      = device_fields.get(CONF_DEVICE_TYPE, UNKNOWN)    #.lower()
        self.config           = device_fields.get(CONF_CONFIG, '')
        self.config_error_msg = ''
        self.source           = device_fields.get(CONF_SOURCE, '')
        self.tracking_method  = device_fields.get(CONF_TRACKING_METHOD, '')
        self.tracking_method_config = device_fields.get(CONF_TRACKING_METHOD, '')

        # Set up badge sensor attributes
        if self.picture:
            self.badge_picture        = self.picture if instr(self.picture, '/') else (f"/local/{self.picture}")
        self.sensor_badge_attrs       = {}
        self.sensor_badge_attrs[PICTURE]       = self.badge_picture
        self.sensor_badge_attrs[FRIENDLY_NAME] = self.fname
        self.sensor_badge_attrs[ICON]          = 'mdi:account-circle-outline'

        # Validate zone name and get Zone Object for a valid zone
        self.track_from_zones = device_fields.get(CONF_TRACK_FROM_ZONE, '').replace(',', ' ').split()
        if HOME not in self.track_from_zones:
            self.track_from_zones.append(HOME)

        # Set up iOS App variables
        iosapp_monitor_flag          = device_fields.get(CONF_IOSAPP_INSTALLED, True)
        iosapp_device_trkr_entity_id = ''
        iosapp_device_trkr_suffix    = ''
        iosapp_setup_msg             = ''
        iosapp_inzone_interval_key   = ''

        if iosapp_monitor_flag is False:
            iosapp_inzone_interval_key   = CONF_NO_IOSAPP
            iosapp_setup_msg             = "iOSApp-NotUsed"
        elif CONF_IOSAPP_ENTITY in device_fields:
            iosapp_device_trkr_entity_id = device_fields.get(CONF_IOSAPP_ENTITY)
            iosapp_setup_msg             = (f"iOSAppEntity-{device_fields.get(CONF_IOSAPP_ENTITY)}")
        elif CONF_IOSAPP_SUFFIX in device_fields:
            iosapp_device_trkr_entity_id = (f"{self.devicename}{device_fields.get(CONF_IOSAPP_SUFFIX)}")
            iosapp_device_trkr_suffix    = device_fields.get(CONF_IOSAPP_SUFFIX)
            iosapp_setup_msg             = (f"iOSAppSuffix-{device_fields.get(CONF_IOSAPP_SUFFIX)}")

        # Set Device fields
        self.iosapp_device_trkr_entity_id    = iosapp_device_trkr_entity_id
        self.iosapp_sensor_trigger_entity_id = ''
        self.iosapp_monitor_flag       = iosapp_monitor_flag
        self.iosapp_device_trkr_suffix = iosapp_device_trkr_suffix
        self.iosapp_setup_msg          = iosapp_setup_msg
        self.iosapp_notify_devices     = []
        self.initialize_inzone_interval(device_fields)

        # Fields used in FmF and FamShr initialization
        self.verified_flag    = False           # Indicates this is a valid and trackable Device
        self.device_id_fmf    = ''              # iCloud devce_id
        self.device_id_famshr = ''              #       "
        self.PyiCloud_DevData_famshr = None     # PyiCloud device data object for this device's icloud id
        self.PyiCloud_DevData_fmf    = None     #       "                   "
        self.PyiCloud_DevData        = None     #       " (one of the above if only famshr or fmf is available)

    def initialize_inzone_interval(self, device_fields):
        '''
        Determine the inzone_interval for the Device in the following order:
            1. Device parameter 'inzone_interval: xxx'
            2. Device parameter 'iosapp_installed: False'
            3. Device type
            4. Global parameter 'inzone_interval: xxx'
            5. Default global inzone interval
        '''
        if CONF_INZONE_INTERVAL in device_fields:
            izi = device_fields[CONF_INZONE_INTERVAL]
        elif self.iosapp_monitor_flag is False:
            izi = Gb.inzone_interval_secs[CONF_NO_IOSAPP]
        elif self.device_type.lower() in Gb.inzone_interval_secs:
            izi = Gb.inzone_interval_secs[self.device_type.lower()]
        elif CONF_INZONE_INTERVAL in Gb.inzone_interval_secs:
            izi = Gb.inzone_interval_secs[CONF_INZONE_INTERVAL]
        else:
            izi = DEFAULT_INZONE_INTERVAL

        self.inzone_interval_secs =  izi

#--------------------------------------------------------------------
    def initialize_track_from_zones(self):
        '''
        Cycle through each track_from_zones zone.
            - Validate the zone name
            - Create the DeviceFmZones object
            - Set up the global variables with the DeviceFmZone objects
        '''
        try:
            try:
                old_DeviceFmZones_by_zone = self.DeviceFmZones_by_zone.copy()
            except:
                old_DeviceFmZones_by_zone = {}

            self.DeviceFmZones_by_zone = {}
            # Validate the zone in the config parameter. If valid, get the Zone object
            # and add to the device's DeviceFmZones_by_zone object list
            # Reuse current DeviceFmZones if it exists.
            for zone in self.track_from_zones:
                if zone in Gb.Zones_by_zone:
                    if zone in old_DeviceFmZones_by_zone:
                        DeviceFmZone = old_DeviceFmZones_by_zone[zone]
                        DeviceFmZone.__init__(self, zone)
                        post_monitor_msg(f"INITIALIZED DeviceFmZone-{self.devicename}:{zone}")

                    else:
                        DeviceFmZone = DeviceFmZones(self, zone)
                        post_monitor_msg(f"ADDED DeviceFmZone-{self.devicename}:{zone}")

                    self.DeviceFmZones_by_zone[zone] = DeviceFmZone

                    if zone not in Gb.TrackedZones_by_zone:
                        Gb.TrackedZones_by_zone[zone] = Gb.Zones_by_zone[zone]

                    if zone == HOME:
                        self.DeviceFmZoneHome    = DeviceFmZone
                        self.DeviceFmZoneCurrent = DeviceFmZone
                else:
                    self.track_from_zones.pop(zone)
                    self.config_error_msg += (f"Devices>Invalid track_from_zone ({zone})")

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    @property
    def fname_devicename(self):
        return (f"{self.fname} ({self.devicename})")

    @property
    def devicename_fname(self):
        return (f"{self.devicename} ({self.fname})")

    @property
    def fname_devtype(self):
        return (f"{self.fname} ({self.device_type})")

    # @property
    # def device_id8(self):
    #     if self.device_id
    #     return self.device_id[:8]

    @property
    def device_id8_famshr(self):
        if self.device_id_famshr:
            return self.device_id_famshr[:8]
        else:
            return 'None'

    @property
    def device_id8_fmf(self):
        if self.device_id_fmf:
            return self.device_id_fmf[:8]
        else:
            return 'None'

    @property
    def iosapp_device_trkr_entity_id_fname(self):
        return (f"{self.iosapp_device_trkr_entity_id.replace(DEVICE_TRACKER, '')}")

    @property
    def notify_iosapp_device_trkr_entity_id_fname(self):
        return (f"{str(self.notify_iosapp_device_trkr_entity_id).replace(DEVICE_TRACKER, '')}")

    @property
    def DeviceFmZone(self, Zone):
        return (f"{self.devicename}:{Zone.zone}")

    @property
    def state_change_flag(self):
        return (self.attrs[ZONE] != self.loc_data_zone)

    @property
    def attrs_zone(self):
        return self.attrs[ZONE]

#--------------------------------------------------------------------
    @property
    def poll_count(self):
        return (f"{self.count_update_icloud}:"
                f"{self.count_update_iosapp}:"
                f"{self.count_discarded_update}")

    @property
    def tracking_method_fname(self):
        return (TRACKING_METHOD_FNAME.get(self.tracking_method, self.tracking_method))

    @property
    def tracking_method_FMF(self):
        return (self.tracking_method == FMF)

    @property
    def tracking_method_FAMSHR(self):
        return (self.tracking_method == FAMSHR)

    @property
    def tracking_method_FAMSHR_FMF(self):
        return (self.tracking_method in [FAMSHR, FMF])

    @property
    def tracking_method_ICLOUD(self):
        return (self.tracking_method in [FAMSHR, FMF])

    @property
    def tracking_method_IOSAPP(self):
        return (self.tracking_method == IOSAPP)

    @property
    def is_online(self):
        return True
        ''' Returns True/False if the device is online based on the device_status '''
        if self.tracking_method_IOSAPP:
            return True
        else:
            return (self.dev_data_device_status in DEVICE_STATUS_ONLINE)

    @property
    def is_offline(self):
        ''' Returns True/False if the device is offline based on the device_status '''
        return (not self.is_online)

    # @property
    # def icloud_initial_locate_done(self):
    #     return (self.attrs[ZONE] != NOT_SET)

    @property
    def track_from_other_zone_flag(self):
        ''' Returns True if tracking from multiple zones '''
        return (len(self.DeviceFmZones_by_zone) > 1)

#--------------------------------------------------------------------
    def update_location_gps_accuracy_status(self):
        self.loc_data_isold = (self.loc_data_secs < \
                                    (time_now_secs() - self.old_loc_threshold_secs))
        self.loc_data_ispoorgps = (self.loc_data_gps_accuracy > Gb.gps_accuracy_threshold)

    @property
    def iosapp_data_isold(self):
        return (self.iosapp_data_secs < (time_now_secs() - self.old_loc_threshold_secs))

    @property
    def located_secs_plus_5(self):
        ''' timestamp (secs) plus 5 secs for next cycle '''
        return (self.loc_data_secs)# + 5)

    @property
    def is_location_old_or_gps_poor(self):
        return (self.loc_data_isold or self.loc_data_ispoorgps)

    @property
    def is_location_old_and_gps_poor(self):
        return (self.loc_data_isold and self.loc_data_ispoorgps)

    @property
    def is_location_gps_good(self):
        return (self.loc_data_isold is False and self.loc_data_ispoorgps is False)

    @property
    def is_location_old(self):
        return self.loc_data_isold

    @property
    def is_location_good(self):
        return not self.loc_data_isold

    @property
    def is_gps_poor(self):
        return self.loc_data_ispoorgps

    @property
    def is_gps_good(self):
        return not self.loc_data_ispoorgps

#--------------------------------------------------------------------
    @property
    def attrs_secs(self):
        return (datetime_to_secs(self.attrs[UPDATE_DATETIME]))

    @property
    def loc_data_age(self):
        ''' timestamp(secs) --> age (secs ago)'''
        return (secs_since(self.loc_data_secs))

    @property
    def loc_data_time_age(self):
        ''' timestamp (secs) --> hh:mm:ss (secs ago)'''
        return (f"{self.loc_data_time} "
                f"({secs_to_time_str(self.loc_data_age)} ago)")

    @property
    def loc_data_time_utc(self):
        ''' timestamp (secs) --> hh:mm:ss'''
        return (secs_to_time(self.loc_data_secs))

    @property
    def loc_data_12hrtime_age(self):
        ''' location time --> 12:mm:ss (secs ago)'''
        return (f"{time_to_12hrtime(self.loc_data_time)} "
                f"({secs_to_time_str(self.loc_data_age)} ago)")

    @property
    def format_loc_data_gps(self):
        return (format_gps(self.loc_data_latitude, self.loc_data_longitude, self.loc_data_gps_accuracy))

#--------------------------------------------------------------------
    @property
    def isnot_set(self):
        return (self.attrs[ZONE] == NOT_SET)

    @property
    def is_inzone(self):
        return (self.loc_data_zone not in [NOT_HOME, NOT_SET])

    @property
    def isnot_inzone(self):
        return (self.loc_data_zone == NOT_HOME)

    @property
    def was_inzone(self):
        return (self.attrs[ZONE] not in [NOT_HOME, NOT_SET])

    @property
    def wasnot_inzone(self):
        return (self.attrs[ZONE] == NOT_HOME)

    @property
    def is_inzone_stationary(self):
        return (is_statzone(self.loc_data_zone))

    @property
    def isnot_inzone_stationary(self):
        return (is_statzone(self.loc_data_zone) is False)

    @property
    def was_inzone_stationary(self):
        return (is_statzone(self.attrs[ZONE]))

    @property
    def wasnot_inzone_stationary(self):
        return (is_statzone(self.attrs[ZONE]) is False)

#--------------------------------------------------------------------
    @property
    def pause_tracking(self):
        '''
        Pause tracking the device
        '''
        try:
            self.tracking_status = TRACKING_PAUSED

            attrs = {}
            attrs[NEXT_UPDATE_TIME] = PAUSED
            Gb.Sensors.update_device_sensors(self, attrs)

            self.display_info_msg(PAUSED)

        except Exception as err:
            log_exception(err)
            pass

#--------------------------------------------------------------------
    @property
    def is_tracking_paused(self):
        '''
        Return:
            True    Device is paused
            False   Device not pause
        '''
        try:
            return (self.tracking_status == TRACKING_PAUSED)

        except Exception as err:
            log_exception(err)
            return False

#--------------------------------------------------------------------
    @property
    def resume_tracking(self):
        '''
        Resume tracking
        '''
        try:
            self.tracking_status = TRACKING_RESUMED

            for from_zone, DeviceFmZone in self.DeviceFmZones_by_zone.items():
                DeviceFmZone.next_update_secs = 0
                DeviceFmZone.next_update_time = HHMMSS_ZERO

            self.override_interval_secs = 0
            self.old_loc_poor_gps_cnt  = 0
            self.old_loc_poor_gps_msg  = ''
            self.poor_gps_flag          = False
            self.outside_no_exit_trigger_flag = False

            self.iosapp_request_loc_retry_cnt = 0
            self.iosapp_request_loc_retry_cnt = 0
            self.iosapp_request_loc_sent_secs = 0
            self.iosapp_request_loc_sent_flag = False
            Gb.icloud_acct_auth_error_cnt     = 0

            attrs = {}
            attrs[NEXT_UPDATE_TIME] = RESUMING
            Gb.Sensors.update_device_sensors(self, attrs)

            self.display_info_msg(RESUMING)

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    @property
    def is_tracking_resumed(self):
        '''
        Return
            True    Device is resuming tracking
            False   Device tracking is normal
        '''
        try:
            return (self.tracking_status == TRACKING_RESUMED)

        except Exception as err:
            log_exception(err)
            return False

#--------------------------------------------------------------------
    @property
    def next_update_time_reached(self):
        '''
        Check to see if any of this Device's DeviceFmZone items will
        need to be updated within the next 5-secs

        Return:
            True    Next update time reached
            False   Next update time not reached
        '''
        self.next_update_DeviceFmZone = self.DeviceFmZoneHome
        if self.icloud_initial_locate_done is False:
            return True
        elif self.is_tracking_resumed:
            return True

        self.next_update_DeviceFmZone = None
        for from_zone, DeviceFmZone in self.DeviceFmZones_by_zone.items():
            if DeviceFmZone.next_update_secs <= (Gb.this_update_secs):  #+ 5):
                self.next_update_DeviceFmZone = DeviceFmZone
                return True
        return False

#--------------------------------------------------------------------
    def calculate_distance_moved(self):
        '''
        Calculate the distance (km) from the last updated location to
        the current location
        '''
        if self.attrs_zone == NOT_SET:
            self.loc_data_distance_moved = 0
        else:
            self.loc_data_distance_moved = calc_distance_km(
                                                self.attrs[LATITUDE],
                                                self.attrs[LONGITUDE],
                                                self.loc_data_latitude,
                                                self.loc_data_longitude)

            if self.loc_data_distance_moved < .002:
                self.loc_data_distance_moved = 0

#--------------------------------------------------------------------
    def post_location_data_event_msg(self, msg_title):
        '''
        Post an event message describing the location/gps status of the data being used
        '''
        old_loc_sym  = '>' if self.is_location_old else '<'
        poor_gps_sym = '>' if self.is_gps_poor else '<'
        event_msg =(f"{msg_title} > {self.dev_data_source} > "
                    f"Located-{self.loc_data_time_age}, "
                    f"GPS-{self.format_loc_data_gps}, ")
        if self.is_location_old_or_gps_poor:
            event_msg +=(f"isOld-{self.loc_data_isold} "
                    f"({old_loc_sym} {secs_to_time_str(self.old_loc_threshold_secs)}), "
                    f"isPoorGPS-{self.loc_data_ispoorgps} "
                    f"({poor_gps_sym} {Gb.gps_accuracy_threshold}m)")
        else:
            event_msg += "Status-Acceptable Location"
        post_event(self.devicename, event_msg)

#--------------------------------------------------------------------
    def display_info_msg(self, info_msg="+"):
        '''
        Display the info msg in the Device's sensor.[devicename]_info entity

        Return:
            Message text
        '''

        if info_msg == "+": info_msg = self.info_msg
        info_dot = "" if info_msg.startswith(' •') else "• "

        set_state_attributes(self.info_msg_entity, f"{info_dot}{info_msg}", self.info_msg_sensor_attrs)

        return (f"{CRLF_DOT}{info_msg}")

#--------------------------------------------------------------------
    def display_sensor_field(self, sensor_name, sensor_value):
        '''
        Display a value in a ic3 sensor field

        Input:
            sensor_name     Attribute field name (LOCATED_DATETIME)
            sensor_value    Value that should be displayed (Device.loc_data_datetime)
        '''
        attrs = {}
        attrs[sensor_name] = sensor_value
        Gb.Sensors.update_device_sensors(self, attrs)

#--------------------------------------------------------------------
    def initialize_usage_counters(self):
        self.count_update_icloud    = 0
        self.count_update_iosapp    = 0
        self.count_discarded_update = 0
        self.count_state_changed    = 0
        self.count_trigger_changed  = 0
        self.count_waze_locates     = 0
        self.time_waze_calls        = 0.0

#--------------------------------------------------------------------------------
    @property
    def format_info_text(self):

        """
        Analyze the Device's fields.

        Return: Info text to be displayed in the info field
        """
        try:
            info_msg = ''
            if Gb.info_notification != '':
                info_msg = f"●● {Gb.info_notification} ●●"
                Gb.info_notification = ''

            if self.tracking_method != self.dev_data_source.lower():
                info_msg += (f" • Source-{self.dev_data_source}")

            if self.override_interval_secs > 0:
                info_msg += " • Overriding.Interval"

            if instr(self.loc_data_zone, NEAR_ZONE):
                info_msg += " • NearZone"

            if self.dev_data_battery_level > 0:
                info_msg += f" • Battery-{self.dev_data_battery_level}%"

            if self.is_gps_poor:
                info_msg += (f" • Poor.GPS.Accuracy, Dist-{self.loc_data_gps_accuracy}m "
                            f"(#{self.old_loc_poor_gps_cnt})")
                if (is_inzone_zone(self.loc_data_zone)
                        and Gb.ignore_gps_accuracy_inzone_flag):
                    info_msg += "-Ignored"

            if self.old_loc_poor_gps_cnt > 16:
                info_msg += (f" • May Be Offline, "
                            f"LocTime-{self.loc_data_12hrtime_age}, "
                            f"OldCnt-#{self.old_loc_poor_gps_cnt}")

            if self.StatZone.timer > 0:
                info_msg += (f" • IntoStatZone@{secs_to_time(self.StatZone.timer)}")

        except Exception as err:
            log_exception(err)

        return info_msg

#########################################################
#
#   DEVICE ZONE ROUTINES
#
#########################################################
    def _get_device_zone(self, device_being_updated_flag):
        '''
        Finish setting up the location data for the Device
            - Select the zone for the location data

        Attributes:
            Device      Device being updated
            _Device     All tracked Devices
        '''

        zone, Zone = self.get_zone(display_zone_msg=device_being_updated_flag)

        # Zone changed, set Device location data to new zone
        if self.loc_data_zone != zone:
            self.loc_data_zone      = zone
            self.into_zone_datetime = datetime_now()

#----------------------------------------------------------------------
    def get_zone(self, display_zone_msg=True):

        '''
        Get current zone of the device based on the location

        Returns:
            zone    zone name or not_home if not in a zone
            Zone    Zone object

        NOTE: This is the same code as (active_zone/async_active_zone) in zone.py
        but inserted here to use zone table loaded at startup rather than
        calling hass on all polls
        '''

        zone_selected_dist_km = HIGH_INTEGER
        ZoneSelected          = None
        zone_selected         = None
        zones_msg             = ""
        iosapp_zone_msg       = ""

        # zone_iosapp = self.iosapp_data_state if is_inzone_zone(self.iosapp_data_state) else None
        # iOSApp will trigger Enter Region when the edge of the devices's location area (100m)
        # touches or is inside the zones radius. If enterina a zone, increase the zone's radius
        # so the device will be in the zone when it is actually just outside of it.
        # But don't do this for a Stationary Zone.
        # if (self.isnot_set or (instr(self.iosapp_data_trigger, REGION_ENTERED))
        #         and is_statzone(self.iosapp_data_state) is False):
        #     zone_radius_iosapp_enter_adjustment_km = .100
        # else:
        zone_radius_iosapp_enter_adjustment_km = 0

        for Zone in Gb.Zones:
            zone           = Zone.zone
            zone_dist_km   = Zone.distance_km(self.loc_data_latitude, self.loc_data_longitude)
            zone_radius_km = Zone.radius_km + .1    #zone_radius_iosapp_enter_adjustment_km

            #Skip another device's stationary zone or if at base location
            if (is_statzone(zone) and instr(zone, self.devicename) is False):
                continue

            #Bypass stationary zone at base and Pseudo Zones (not_home, not_set, etc)
            elif Zone.radius <= 1:
                continue

            #Do not check Stat Zone if radius=1 (at base loc) but include in log_msg
            in_zone_flag      = zone_dist_km <= zone_radius_km
            closer_zone_flag  = zone_selected is None or zone_dist_km < zone_selected_dist_km
            smaller_zone_flag = (zone_dist_km == zone_selected_dist_km
                                     and zone_radius_km <= zone_selected_radius_km)

            if in_zone_flag and (closer_zone_flag or smaller_zone_flag):
                ZoneSelected          = Zone
                zone_selected         = zone
                zone_selected_dist_km = zone_dist_km
                iosapp_zone_msg       = ""
                zone_selected_radius_km = ZoneSelected.radius_km + zone_radius_iosapp_enter_adjustment_km

            # if (zone in self.track_from_zones or Gb.log_debug_flag):
            if is_statzone(zone):
                zones_msg += self.StatZone.display_as
            else:
                zones_msg += Zone.display_as
            zones_msg +=(f"-{format_dist(zone_dist_km)}/r{Zone.radius:.0f}m, ")

        if ZoneSelected is None:
            ZoneSelected       = Gb.Zones_by_zone[NOT_HOME]
            zone_selected      = NOT_HOME
            zone_selected_dist_km = 0

            #If not in a zone and was in a Stationary Zone, Exit the zone and reset everything
            if self.StatZone.inzone:
                self.stationary_zone_update_control = STAT_ZONE_MOVE_TO_BASE

        elif instr(zone,'nearzone'):
            zone_selected = NEAR_ZONE

        zones_msg = (f"Selected Zone > {ZoneSelected.display_as} > "
                    f"{zones_msg[:-2]}{iosapp_zone_msg}")

        if display_zone_msg:
            post_event(self.devicename, zones_msg)

        # Get distance between zone selected and current zone to see if they overlap.
        # If so, keep the current zone
        if (zone_selected != NOT_HOME
                and self._is_overlapping_zone(self.loc_data_zone, zone_selected)):
            zone_selected = self.loc_data_zone
            ZoneSelected  = Gb.Zones_by_zone[self.loc_data_zone]

        if self.loc_data_zone != zone_selected:
            self.loc_data_zone      = zone_selected
            self.into_zone_datetime = datetime_now()

        return (zone_selected, ZoneSelected)

#--------------------------------------------------------------------
    def _is_overlapping_zone(self, current_zone, new_zone):
        '''
        Check to see if two zones overlap each other. The current_zone and
        new_zone overlap if their distance between centers is less than 2m.

        Return:
            True    They overlap
            False   They do not oerlap, ic3 is starting
        '''
        try:
            if current_zone == NOT_SET:
                return False
            elif current_zone == new_zone:
                return True

            if current_zone == "": current_zone = HOME
            CurrentZone = Gb.Zones_by_zone[current_zone]
            NewZone     = Gb.Zones_by_zone[new_zone]

            zone_dist = CurrentZone.distance(NewZone.latitude, NewZone.longitude)

            return (zone_dist <= 2)

        except:
            return False


###############################################################################
#
#   CALCULATE THE OLD LOCATION THRESHOLD FOR THE DEVICE
#
###############################################################################
    def calculate_old_location_threshold(self):
        """
        The old_loc_threshold_secs is used to determine if the Device's location is too
        old to be used. If it is too old, the Device's location will be requested again
        using an interval calculated in the determine_interval_after_error routine. The
        old_loc_threshold_secs is recalculated each time the Device's location is
        updated.
        """
        try:
            # Get smallest interval of all zones being tracked from
            interval = HIGH_INTEGER
            for from_zone, DeviceFmZone in self.DeviceFmZones_by_zone.items():
                if DeviceFmZone.interval_secs < interval:
                    interval = DeviceFmZone.interval_secs

            threshold_secs = 60
            if self.is_inzone:
                threshold_secs = interval * .025        # 2.5% of interval time
                if threshold_secs < 120: threshold_secs = 120

            elif interval < 90:
                threshold_secs = 60
            else:
                threshold_secs = interval * .125

            if threshold_secs < 60:
                threshold_secs = 60
            elif threshold_secs > 600:
                threshold_secs = 600

            if (Gb.old_location_threshold > 0
                    and threshold_secs > Gb.old_location_threshold):
                threshold_secs = Gb.old_location_threshold

            self.old_loc_threshold_secs = threshold_secs

        except Exception as err:
            log_exception(err)
            self.old_loc_threshold_secs = 120

        return