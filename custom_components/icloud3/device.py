#------------------------------------------------------------------------------
#
#   This module handles all device data
#
#------------------------------------------------------------------------------
from .global_variables  import GlobalVariables as Gb
from .const             import (DEVICE_TRACKER, DEVICE_TRACKER_DOT,
                                NOTIFY, DISTANCE_TO_DEVICES, NEAR_DEVICE_DISTANCE,
                                DISTANCE_TO_OTHER_DEVICES, DISTANCE_TO_OTHER_DEVICES_DATETIME,
                                HOME, NOT_HOME, NOT_SET, UNKNOWN, DOT, RARROW, INFO_SEPARATOR,
                                PAUSED, TOWARDS, PAUSED_CAPS, RESUMING,
                                DATETIME_ZERO, HHMMSS_ZERO, HIGH_INTEGER,
                                TRACKING_NORMAL, TRACKING_PAUSED, TRACKING_RESUMED,
                                STAT_ZONE_NO_UPDATE, STAT_ZONE_MOVE_TO_BASE,
                                EVLOG_ALERT,
                                USE_RESTORE_STATE_VALUE_ON_STARTUP, BLANK_SENSOR_FIELD,
                                FMF, FAMSHR, FMF_FNAME, FAMSHR_FNAME,
                                IOSAPP, IOSAPP_FNAME,
                                TRACKING_METHOD_FNAME,
                                TRACK_DEVICE, MONITOR_DEVICE, INACTIVE_DEVICE,
                                NAME, DEVICE_TYPE_FNAME,
                                ICLOUD_HORIZONTAL_ACCURACY, ICLOUD_VERTICAL_ACCURACY, ICLOUD_BATTERY_STATUS,
                                ICLOUD_BATTERY_LEVEL, ICLOUD_DEVICE_CLASS, ICLOUD_DEVICE_STATUS, ICLOUD_LOW_POWER_MODE, ID,
                                FRIENDLY_NAME, PICTURE, ICON, BADGE,
                                LATITUDE, LONGITUDE,
                                DEVICE_TRACKER_STATE_VALUE, LOCATION,
                                LOCATION_SOURCE, TRIGGER, TRACKING,
                                ZONE, ZONE_DATETIME, LAST_ZONE, FROM_ZONE, LAST_ZONE_DATETIME,
                                ZONE_NAME, ZONE_FNAME, LAST_ZONE_NAME, LAST_ZONE_FNAME, INTERVAL,
                                BATTERY_SOURCE, BATTERY, BATTERY_LEVEL, BATTERY_STATUS, BATTERY_STATUS_FNAME,
                                ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD, HOME_DISTANCE, MAX_DISTANCE,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, MOVED_DISTANCE,
                                DEVICE_STATUS, LOW_POWER_MODE, RAW_MODEL, MODEL, MODEL_DISPLAY_NAME,
                                LAST_UPDATE, LAST_UPDATE_TIME, LAST_UPDATE_DATETIME,
                                NEXT_UPDATE, NEXT_UPDATE_TIME, NEXT_UPDATE_DATETIME,
                                LAST_LOCATED, LAST_LOCATED_TIME, LAST_LOCATED_DATETIME,
                                INFO, GPS_ACCURACY, GPS, VERT_ACCURACY, ALTITUDE,
                                DEVICE_STATUS_CODES, DEVICE_STATUS_OFFLINE, DEVICE_STATUS_PENDING,
                                CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_ZONES,
                                CONF_PICTURE,
                                CONF_DEVICE_TYPE, CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME,
                                CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                CONF_IOSAPP_DEVICE, CONF_FMF_EMAIL,
                                CONF_TRACKING_MODE, CONF_INZONE_INTERVAL,

                                )
from .const_sensor      import  (SENSOR_LIST_DISTANCE, )
from .                  import device_fm_zone
from .support           import determine_interval as det_interval
from .support           import restore_state
from .helpers           import entity_io

from .helpers.common    import (instr, is_inzone_zone, is_statzone, circle_letter, format_gps, zone_display_as,
                                round_to_zero, )
from .helpers.messaging import (post_event, post_error_msg, post_monitor_msg, log_exception, log_debug_msg,
                                post_internal_error, _trace, _traceha, )
from .helpers.time_util import ( time_now_secs, secs_to_time, secs_to_time_str, secs_since, secs_to,
                                time_to_12hrtime, secs_to_time,
                                datetime_to_secs, secs_to_datetime, datetime_now,
                                secs_to_age_str,  secs_to_time_age_str, hhmmss_to_secs, )
from .helpers.dist_util import (calc_distance_m, calc_distance_km, km_to_mi_str, m_to_ft_str,
                                format_dist_km, format_dist_m, km_to_mi,)

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.util import slugify
import traceback
import copy

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3_Device(TrackerEntity):

    def __init__(self, devicename, conf_device):
        self.conf_device           = conf_device
        self.devicename            = devicename
        self.fname                 = devicename.title()
        self.StatZone              = None
        self.stationary_zonename   = (f"{self.devicename}_stationary")
        self.DeviceFmZones_by_zone = {}     # DeviceFmZones objects for the track_from_zones parameter for this Device
        self.DeviceFmZoneHome      = None     # DeviceFmZone object for the Home zone
        self.device_fm_zone_names  = []      # List of the from_zones in the DeviceFmZones_by_zone dictionary
        self.DeviceFmZoneCurrent   = None     # DeviceFmZone object last or currently being updated in determine_interval for EvLog TfZ info
        self.DeviceFmZoneLast      = None     # DeviceFmZone object the device was last in
        self.DeviceFmZoneTracked   = None     # DeviceFmZone object used to set the Device's sensors after determining the closest tracked zone
        self.TrackFromBaseZone     = None    # DeviceFmZone of Home or secondary tracked from zone
        self.track_from_base_zone  = HOME   # Name of secondary tracked from zone (normally Home), usee as another zone if away from Home
        self.next_update_DeviceFmZone = None    # Set to the DeviceFmZone when it's next_update_time is reached
        self.NearDevice            = None     # Device in the same location as this Device
        self.NearDeviceUsed        = None
        self.DeviceTracker         = None     # Device's device_tracker entity object
        self.Sensors               = Gb.Sensors_by_devicename.get(devicename, {})
        self.Sensors_from_zone     = Gb.Sensors_by_devicename_from_zone.get(devicename, {})

        self.initialize()
        self.initialize_sensors()
        self.configure_device(conf_device)
        self.initialize_track_from_zones()

    def initialize(self):
        self.devicename_verified          = False

        # Operational variables
        self.device_type                  = 'iPhone'
        self.raw_model                    = DEVICE_TYPE_FNAME.get(self.device_type, self.device_type)      # iPhone15,2
        self.model                        = DEVICE_TYPE_FNAME.get(self.device_type, self.device_type)      # iPhone
        self.ha_device_id                 = ''      # ha device_registry device_id
        self.model_display_name           = DEVICE_TYPE_FNAME.get(self.device_type, self.device_type)      # iPhone 14 Pro
        self.tracking_method              = None
        self.tracking_status              = TRACKING_NORMAL
        self.tracking_mode                = TRACK_DEVICE      #normal, monitor, inactive
        self.last_data_update_secs        = 0
        self.last_evlog_msg_secs          = 0
        self.dist_from_zone_km_small_move_total = 0
        self.device_tracker_entity_ic3    = (f"{DEVICE_TRACKER}.{self.devicename}")
        self.zone_change_datetime         = DATETIME_ZERO
        self.zone_change_secs             = 0
        self.went_3km                     = False
        self.stationary_zone_update_control = STAT_ZONE_NO_UPDATE
        self.near_device_distance         = 0       # Distance to the NearDevice device
        self.near_device_checked_secs     = 0       # When the nearby devices were last updated
        self.dist_apart_msg               = ''      # Distance to all other devices msg set in icloud3_main
        self.dist_apart_msg_by_devicename = {}      # Distance to all other devices msg set in icloud3_main
        self.last_update_loc_secs         = 0       # Located secs from the device tracker entity update
        self.last_update_loc_zone         = ''      # Zone from the device tracker entity update
        self.passthru_zone                = ''
        self.passthru_zone_expire_secs    = 0

        # Trigger & Update variables
        self.trigger                      = 'iCloud3'
        self.next_update_secs             = 0
        self.seen_this_device_flag        = False
        self.iosapp_zone_enter_secs       = 0
        self.iosapp_zone_enter_time       = HHMMSS_ZERO
        self.iosapp_zone_enter_zone       = ''
        self.iosapp_zone_exit_secs        = 0
        self.iosapp_zone_exit_time        = HHMMSS_ZERO
        self.iosapp_zone_exit_zone        = ''
        self.update_in_process_flag       = False
        self.device_being_updated_retry_cnt = 0
        self.got_exit_trigger_flag        = False
        self.outside_no_exit_trigger_flag = False
        self.moved_since_last_update      = 0

        # Fields used in FmF and FamShr initialization
        self.verified_flag           = False    # Indicates this is a valid and trackable Device
        self.device_id_famshr        = None     #       "
        self.device_id_famshr2       = None     #       "
        self.device_id_fmf           = None     # iCloud device_id
        self.PyiCloud_RawData_famshr = None     # PyiCloud device data object for this device's icloud id
        self.PyiCloud_RawData_fmf    = None     #       "                   "
        self.PyiCloud_RawData        = None     #       " (one of the above if only famshr or fmf is available)

        # iCloud configration fields
        self.conf_famshr_name        = None
        self.conf_famshr_devicename  = None
        self.conf_famshr_device_id   = None
        self.conf_famshr_name2       = None
        self.conf_famshr_devicename2 = None
        self.conf_famshr_device_id2  = None
        self.conf_fmf_email          = None
        self.conf_fmf_device_id      = None

        # Device location & gps fields
        self.old_loc_poor_gps_cnt    = 0
        self.old_loc_poor_gps_msg    = ''
        self.old_loc_threshold_secs  = 120
        self.poor_gps_flag           = False
        self.inzone_interval_secs    = 600
        self.data_source             = ''
        self.offline_secs            = 0        # Time the device went offline
        self.pending_secs            = 0        # Time the device went into a pending status (checked after authentication)
        self.dist_to_other_devices   = {}       # A dict of other devices distances
                                                # {devicename: [distance_m, gps_accuracy_factor, location_old_flag]}
        self.dist_to_other_devices_datetime = DATETIME_ZERO

        self.last_iosapp_msg         = ''
        self.last_device_monitor_msg = ''
        self.iosapp_stat_zone_action_msg_cnt = 0

        # Device Counters
        self.count_update_icloud     = 0
        self.count_update_iosapp     = 0
        self.count_discarded_update  = 0
        self.count_state_changed     = 0
        self.count_trigger_changed   = 0
        self.count_waze_locates      = 0
        self.time_waze_calls         = 0.0

        # Device iOSApp message fields
        self.iosapp_request_loc_first_secs = 0
        self.iosapp_request_loc_last_secs  = 0
        self.iosapp_request_loc_cnt        = 0

        # iOSApp state variables
        self.iosapp_monitor_flag           = False
        self.iosapp_data_state             = NOT_SET
        self.iosapp_data_latitude          = 0.0
        self.iosapp_data_longitude         = 0.0
        self.iosapp_data_state_secs        = 0
        self.iosapp_data_state_time        = HHMMSS_ZERO
        self.iosapp_data_trigger_secs      = 0
        self.iosapp_data_trigger_time      = HHMMSS_ZERO
        self.iosapp_data_secs              = 0
        self.iosapp_data_time              = HHMMSS_ZERO
        self.iosapp_data_trigger           = NOT_SET
        self.iosapp_data_gps_accuracy      = 0
        self.iosapp_data_vertical_accuracy = 0
        self.iosapp_data_altitude          = 0.0

        self.iosapp_data_battery_level     = 0
        self.iosapp_data_battery_status    = ''
        self.iosapp_data_battery_update_secs = 0

        # iOS App data update control variables
        self.invalid_error_cnt             = 0
        self.iosapp_data_invalid_error_cnt = 0
        self.iosapp_data_updated_flag      = False
        self.iosapp_data_change_reason     = ''         # Why a state/trigger is causing an update
        self.iosapp_data_reject_reason     = ''         # Why a state/trigger was not updated
        self.iosapp_update_flag            = False
        self.last_iosapp_trigger           = ''

        # iCloud data update control variables
        self.icloud_update_needed_flag     = False
        self.icloud_devdata_useable_flag   = False
        self.icloud_acct_error_flag        = False      # An error occured from the iCloud account update request
        self.icloud_update_reason          = 'Trigger > Initial Locate'
        self.icloud_no_update_reason       = ''
        self.icloud_update_retry_flag      = False       # Set to True for initial locate
        self.icloud_initial_locate_done    = False

        # Final update control variables -
        self.update_sensors_flag           = False       # The data is good and tracking can be updated
        self.update_sensors_error_msg      = ''          # Reason an error message will be displayed

        # Location Data from iCloud or the iOS App
        self.dev_data_source             = NOT_SET          #icloud or iosapp data
        self.dev_data_fname              = ''
        self.dev_data_device_class       = 'iPhone'
        self.dev_data_device_status      = "Online"
        self.dev_data_device_status_code = 200
        self.dev_data_low_power_mode     = False

        self.dev_data_battery_source     = ''
        self.dev_data_battery_level      = 0
        self.dev_data_battery_status     = ''
        self.dev_data_battery_level_last = 0
        self.dev_data_battery_status_last = ''

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
        self.loc_data_distance_moved = 0.0
        self.last_loc_data_time_gps = f"{HHMMSS_ZERO}/0m"

        self.sensor_prefix            = (f"sensor.{self.devicename}_")

        # Test variables used for saving the last value of a variable during debugging
        self.debug_save_number            = 0
        self.debug_save_string            = ''
        self.debug_save_list              = []
        self.debug_save_dict              = {}

    def __repr__(self):
        return (f"<Device: {self.devicename}>")

#------------------------------------------------------------------------------
    def initialize_sensors(self):
        # device_tracker.[devicename] attributes for the Device

        self.attrs              = {}
        self.kwargs             = {}
        self.sensors            = {}
        self.sensors_um         = {}
        self.sensor_badge_attrs = {}

        # Initialize the Device sensors[xxx] value from the restore_state file if
        # the sensor is in the file. Otherwise, initialize to this value. This will preserve
        # non-tracking sensors across restarts
        for sensor, default_value in USE_RESTORE_STATE_VALUE_ON_STARTUP.items():
            if (self.devicename in Gb.restore_state_devices
                    and 'sensor' in Gb.restore_state_devices[self.devicename]
                    and sensor in Gb.restore_state_devices[self.devicename]['sensors']):
                self.sensors[sensor] = Gb.restore_state_devices[self.devicename]['sensors'][sensor]
            else:
                self.sensors[sensor] = default_value

        # Device related sensors
        self.sensors[DEVICE_TRACKER_STATE_VALUE] = ''
        self.sensors[NAME]               = ''
        self.sensors[PICTURE]            = ''
        self.sensors[BADGE]              = ''
        self.sensors[LOW_POWER_MODE]     = ''
        self.sensors[INFO]               = ''

        # Location related items
        self.sensors[GPS]                = (0, 0)
        self.sensors[LATITUDE]           = 0
        self.sensors[LONGITUDE]          = 0
        self.sensors[GPS_ACCURACY]       = 0
        self.sensors[ALTITUDE]           = 0
        self.sensors[VERT_ACCURACY]      = 0
        self.sensors[LOCATION_SOURCE]    = ''             #icloud:fmf/famshr or iosapp
        self.sensors[TRIGGER]            = ''
        self.sensors[LAST_LOCATED_DATETIME] = DATETIME_ZERO
        self.sensors[LAST_LOCATED_TIME]     = HHMMSS_ZERO
        self.sensors[LAST_LOCATED]          = HHMMSS_ZERO

        self.sensors['dev_id']           = ''
        self.sensors[RAW_MODEL]          = ''
        self.sensors[MODEL]              = ''
        self.sensors[MODEL_DISPLAY_NAME] = ''
        self.sensors['host_name']        = ''
        self.sensors['source_type']      = GPS
        self.sensors[DEVICE_STATUS]      = UNKNOWN
        self.sensors[TRACKING]           = ''
        self.sensors[DISTANCE_TO_DEVICES]= ''
        self.sensors[DISTANCE_TO_OTHER_DEVICES] = {}
        self.sensors[DISTANCE_TO_OTHER_DEVICES_DATETIME] = HHMMSS_ZERO

        # Sensors overlaid with DeviceFmZone sensors for nearest zone
        self.sensors[FROM_ZONE]             = ''
        self.sensors[INTERVAL]              = ''
        self.sensors[NEXT_UPDATE_DATETIME]  = DATETIME_ZERO
        self.sensors[NEXT_UPDATE_TIME]      = HHMMSS_ZERO
        self.sensors[NEXT_UPDATE]           = HHMMSS_ZERO
        self.sensors[LAST_UPDATE_DATETIME]  = DATETIME_ZERO
        self.sensors[LAST_UPDATE_TIME]      = HHMMSS_ZERO
        self.sensors[LAST_UPDATE]           = HHMMSS_ZERO
        self.sensors[TRAVEL_TIME]           = 0
        self.sensors[TRAVEL_TIME_MIN]       = 0
        self.sensors[ZONE_DISTANCE]         = 0
        self.sensors[MAX_DISTANCE]          = 0
        self.sensors[HOME_DISTANCE]         = 0
        self.sensors[WAZE_DISTANCE]         = 0
        self.sensors[WAZE_METHOD]           = 0
        self.sensors[CALC_DISTANCE]         = 0
        self.sensors[DIR_OF_TRAVEL]         = NOT_SET
        self.sensors[MOVED_DISTANCE]        = 0

        # Zone related items
        self.sensors[ZONE]               = NOT_SET
        self.sensors[ZONE_FNAME]         = NOT_SET
        self.sensors[ZONE_NAME]          = NOT_SET
        self.sensors[ZONE_DATETIME]      = DATETIME_ZERO
        self.sensors[LAST_ZONE]          = NOT_SET
        self.sensors[LAST_ZONE_FNAME]    = NOT_SET
        self.sensors[LAST_ZONE_NAME]     = NOT_SET
        self.sensors[LAST_ZONE_DATETIME] = DATETIME_ZERO

        # The DeviceTracker & Sensors entities are created before the Device object
        # using the configuration parameters. Cycle thru them now to set there
        # self.Device variable to this evice object. This permits access to the
        # sensors & attrs values.

        # Link the DeviceTracker-Device objects
        if self.devicename in Gb.DeviceTrackers_by_devicename:
            self.DeviceTracker = Gb.DeviceTrackers_by_devicename[self.devicename]
            self.DeviceTracker.Device = self

        # Cycle through all sensors for this device.
        # Link the Sensor-Device objects to provide access the sensors dictionary
        # when they are updated.
        for Sensor in self.Sensors.values():
            Sensor.Device = self

        for sensor, Sensor in self.Sensors_from_zone.items():
            Sensor.Device = self

#------------------------------------------------------------------------------
    def configure_device(self, conf_device):

        # Configuration parameters
        self.tracking_mode        = conf_device.get(CONF_TRACKING_MODE, 'track')
        self.fname                = conf_device.get(CONF_FNAME, self.devicename.title())
        self.sensors[NAME]        = self.fname
        self.sensors['dev_id']    = self.devicename
        self.sensors['host_name'] = self.fname

        # iosapp device_tracker/sensor entity ids
        self.iosapp_entity = {
            DEVICE_TRACKER: '',
            TRIGGER: '',
            BATTERY_LEVEL: 0,
            BATTERY_STATUS: '',
            NOTIFY: '',
        }

        self.sensor_badge_attrs[FRIENDLY_NAME] = self.fname
        self.sensor_badge_attrs[ICON]          = 'mdi:account-circle-outline'

        if Gb.data_source_use_icloud:
            self.conf_famshr_name       = self._extract_devicename(conf_device.get(CONF_FAMSHR_DEVICENAME, 'None'))
            self.conf_famshr_devicename = slugify(self.conf_famshr_name)
            self.conf_fmf_email         = self._extract_devicename(conf_device.get(CONF_FMF_EMAIL, 'None'))

        if conf_device.get(CONF_IOSAPP_DEVICE, 'None') != 'None':
            self.iosapp_entity[DEVICE_TRACKER] = conf_device.get(CONF_IOSAPP_DEVICE, 'None')

        self.device_type = conf_device.get(CONF_DEVICE_TYPE, 'iphone')
        picture          = conf_device.get(CONF_PICTURE, 'None').replace('www/', '/local/')
        if picture:
            self.sensors[PICTURE] = picture if instr(picture, '/') else (f"/local/{picture}")
            self.sensor_badge_attrs[PICTURE] = self.sensors[PICTURE]

        # Validate zone name and get Zone Object for a valid zone
        self.inzone_interval_secs = hhmmss_to_secs(conf_device.get(CONF_INZONE_INTERVAL, 3600))


        # Get and validate track from zone config
        self.track_from_base_zone = conf_device.get(CONF_TRACK_FROM_BASE_ZONE, HOME)
        self.track_from_zones     = conf_device.get(CONF_TRACK_FROM_ZONES, HOME).copy()
        if HOME not in self.track_from_zones:
            self.track_from_zones.append(HOME)

        # Update tfz with master base zone, also remove Home zone if necessary
        if Gb.track_from_base_zone != HOME:
            self.track_from_base_zone = Gb.track_from_base_zone
            if Gb.track_from_home_zone is False:
                self.track_from_zones.remove(HOME)

        # Make sure track_from_base_zone is is in the track_from_zones list. If it is,
        # make sure it is the last entry. If not, add it as a tracked_from_aone.
        if self.track_from_base_zone in self.track_from_zones:
            if self.track_from_base_zone != self.track_from_zones[-1]:
                self.track_from_zones.remove(self.track_from_base_zone)
                self.track_from_zones.append(self.track_from_base_zone)
        else:
            self.track_from_zones.append(self.track_from_base_zone)

        # Set tracking method info
        if self.conf_famshr_devicename:
            self.tracking_method = FAMSHR
        elif self.conf_fmf_email:
            self.tracking_method = FMF
        elif self.iosapp_entity[DEVICE_TRACKER]:
            self.tracking_method = IOSAPP
        else:
            self.tracking_method = None

    def _extract_devicename(self, device_field):
        # The xxx_device field will contain a '>' if it is a valid devicename that will be used
        if instr(device_field, '>'):
            device_name = device_field.split(' >')[0].strip()
        elif device_field.startswith('Select'):
            device_name = ''
        else:
            device_name = device_field

        return device_name

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
            if self.track_from_zones == []:
                self.track_from_zones.append(HOME)

            # Reuse current DeviceFmZones if it exists.
            track_from_zones = self.track_from_zones.copy()
            for zone in track_from_zones:
                if zone not in Gb.Zones_by_zone:
                    self.track_from_zones.remove(zone)

                    alert_msg = (f"{EVLOG_ALERT}Alert > Invalid Track-from-Zone "
                                    f"configuration parameter > Device-{self.fname_devicename}, "
                                    f"InvalidZone-{zone} (Removed), "
                                    f"Update `Track From Zone` parameter using the "
                                    f"iCloud3 Configurator")
                    post_event(alert_msg)

                    continue

                if zone in old_DeviceFmZones_by_zone:
                    DeviceFmZone = old_DeviceFmZones_by_zone[zone]
                    DeviceFmZone.__init__(self, zone)
                    post_monitor_msg(f"INITIALIZED DeviceFmZone-{self.devicename}:{zone}")

                else:
                    DeviceFmZone = device_fm_zone.iCloud3_DeviceFmZone(self, zone)
                    post_monitor_msg(f"ADDED DeviceFmZone-{self.devicename}:{zone}")

                self.DeviceFmZones_by_zone[zone] = DeviceFmZone

                if zone not in Gb.TrackedZones_by_zone:
                    Gb.TrackedZones_by_zone[zone] = Gb.Zones_by_zone[zone]

                # if zone == HOME:
                if zone == self.track_from_base_zone:
                    self.DeviceFmZoneHome    = DeviceFmZone
                    self.DeviceFmZoneLast    = DeviceFmZone
                    self.DeviceFmZoneCurrent = DeviceFmZone
                    self.DeviceFmZoneTracked = DeviceFmZone
                    self.TrackFromBaseZone   = DeviceFmZone

            # Set a list of tracked from zone names to make it easier to get them later
            self.device_fm_zone_names = [k for k in self.DeviceFmZones_by_zone.keys()]

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    @property
    def fname_devicename(self):
        return (f"{self.fname}{INFO_SEPARATOR}{self.devicename}")

    @property
    def devicename_fname(self):
        return (f"{self.devicename}{INFO_SEPARATOR}{self.fname}")

    @property
    def fname_devtype(self):
        if instr(self.fname, DEVICE_TYPE_FNAME.get(self.device_type, self.device_type)):
            return self.fname

        return (f"{self.fname}{INFO_SEPARATOR}"
                f"{DEVICE_TYPE_FNAME.get(self.device_type, self.device_type)}")

    @property
    def device_id8_famshr(self):
        if self.device_id_famshr:
            return f"#{self.device_id_famshr[:8]}"
        return 'None'

    @property
    def device_id8_fmf(self):
        if self.device_id_fmf:
            return f"#{self.device_id_fmf[:8]}"
        return 'None'

    @property
    def device_model(self):
        return f"{self.device_type}"

    @property
    def iosapp_device_trkr_entity_id_fname(self):
        return (f"{self.iosapp_entity[DEVICE_TRACKER].replace(DEVICE_TRACKER_DOT, '')}")

    @property
    def DeviceFmZone(self, Zone):
        return (f"{self.devicename}:{Zone.zone}")

    @property
    def state_change_flag(self):
        return (self.sensors[ZONE] != self.loc_data_zone)

    @property
    def sensor_zone(self):
        return self.sensors[ZONE]

    @property
    def loc_data_zone_fname(self):
        return zone_display_as(self.loc_data_zone)

    @property
    def loc_data_time_gps(self):
        return (f"{self.loc_data_time}/±"
                f"{self.loc_data_gps_accuracy:.0f}m")
    @property
    def iosapp_data_time_gps(self):
        return (f"{time_to_12hrtime(self.iosapp_data_time)}/±"
                f"{self.iosapp_data_gps_accuracy:.0f}m")

    @property
    def device_status(self):
        return f"{self.dev_data_device_status}/{self.dev_data_device_status_code}"

    @property
    def device_status_msg(self):
        return ( f"{DEVICE_STATUS_CODES.get(self.dev_data_device_status_code, 'Unknown')}/"
                f"{self.dev_data_device_status_code}")

    @property
    def loc_data_fgps(self):
        return format_gps(self.loc_data_latitude, self.loc_data_longitude, self.loc_data_gps_accuracy)

    @property
    def iosapp_data_fgps(self):
        return format_gps(self.iosapp_data_latitude, self.iosapp_data_longitude, self.iosapp_data_gps_accuracy)

    @property
    def loc_data_gps(self):
        return (self.loc_data_latitude, self.loc_data_longitude)

    @property
    def iosapp_data_gps(self):
        return (self.iosapp_data_latitude, self.iosapp_data_longitude)

    #--------------------------------------------------------------------
    @property
    def format_battery_level(self):
        return f"{self.dev_data_battery_level}%"

    @property
    def format_battery_status(self):
        return f"{BATTERY_STATUS_FNAME.get(self.dev_data_battery_status, self.dev_data_battery_status.title())}"

    @property
    def format_battery_status_source(self):
        return (f"{BATTERY_STATUS_FNAME.get(self.dev_data_battery_status, self.dev_data_battery_status.title())} "
                f"({self.dev_data_battery_source})")

    @property
    def format_battery_level_status_source(self):
        return f"{self.format_battery_level}, {self.format_battery_status_source}"

#--------------------------------------------------------------------
    @property
    def tracking_method_fname(self):
        return TRACKING_METHOD_FNAME.get(self.tracking_method, self.tracking_method)

    @property
    def tracking_method_FMF(self):
        return self.tracking_method == FMF

    @property
    def tracking_method_FAMSHR(self):
        return self.tracking_method == FAMSHR

    @property
    def tracking_method_FAMSHR_FMF(self):
        return self.tracking_method in [FAMSHR, FMF]

    @property
    def tracking_method_ICLOUD(self):
        return self.tracking_method in [FAMSHR, FMF]

    @property
    def tracking_method_IOSAPP(self):
        return self.tracking_method == IOSAPP

    # is_data_source properties
    @property
    def isnot_data_source_NOT_SET(self):
        return self.dev_data_source != NOT_SET

    @property
    def is_data_source_NOT_SET(self):
        return self.dev_data_source == NOT_SET

    @property
    def is_data_source_FMF(self):
        return self.dev_data_source in [FMF, FMF_FNAME]

    @property
    def is_data_source_FAMSHR(self):
        return self.dev_data_source in [FAMSHR, FAMSHR_FNAME]

    @property
    def is_data_source_FAMSHR_FMF(self):
        return self.dev_data_source in [FAMSHR, FMF, FAMSHR_FNAME, FMF_FNAME]

    @property
    def is_data_sourced_ICLOUD(self):
        return self.is_data_source_FAMSHR_FMF

    @property
    def is_data_source_IOSAPP(self):
        return self.dev_data_source in [IOSAPP, IOSAPP_FNAME]

    # is_tracking_method properties
    @property
    def is_tracking_method_FMF(self):
        return self.tracking_method == FMF

    @property
    def is_tracking_method_FAMSHR(self):
        return self.tracking_method == FAMSHR

    @property
    def is_tracking_method_FAMSHR_FMF(self):
        return self.tracking_method in [FAMSHR, FMF]

    @property
    def is_tracking_method_ICLOUD(self):
        return self.tracking_method in [FAMSHR, FMF]

    @property
    def is_tracking_method_IOSAPP(self):
        return self.tracking_method == IOSAPP

    # is_xxx other properties
    @property
    def is_tracked(self):
        return self.tracking_mode == TRACK_DEVICE

    @property
    def is_monitored(self):
        return self.tracking_mode == MONITOR_DEVICE

    @property
    def is_inactive(self):
        return self.tracking_mode == INACTIVE_DEVICE

    @property
    def is_online(self):
        return not self.is_offline

    @property
    def is_offline(self):
        ''' Returns True/False if the device is offline based on the device_status '''
        if self.tracking_method_FMF:
            return False
        return (self.dev_data_device_status in DEVICE_STATUS_OFFLINE)

    @property
    def is_pending(self):
        ''' Returns True/False if the device is pending based on the device_status '''
        return (self.dev_data_device_status in DEVICE_STATUS_PENDING)

    @property
    def is_using_iosapp_data(self):
        ''' Return True/False if using IOSApp data '''
        return self.dev_data_source == IOSAPP_FNAME

    @property
    def track_from_other_zone_flag(self):
        ''' Returns True if tracking from multiple zones '''
        return (len(self.DeviceFmZones_by_zone) > 1)

    @property
    def located_secs_plus_5(self):
        ''' timestamp (secs) plus 5 secs for next cycle '''
        return (self.loc_data_secs)     # + 5)

    @property
    def is_approaching_tracked_zone(self):
        '''
        Determine if the Device is going towards a tracked zone, is within 1km of
        the zone, on a 15-sec inerval and the location is older than 15-secs.
        When this occurs, we want to refresh the location or set the old
        location threshold to 15-secs.
        '''
        if self.DeviceFmZoneTracked:
            if (secs_to(self.next_update_secs) <= 15
                    and secs_since(self.loc_data_secs > 15)
                    and self.DeviceFmZoneTracked.is_going_towards
                    and self.DeviceFmZoneTracked.zone_dist < 1
                    and self.went_3km):
                return True
        return False

#--------------------------------------------------------------------
    def update_location_gps_accuracy_status(self):
        if self.loc_data_secs == 0:
            self.loc_data_isold = False
            self.loc_data_ispoorgps = False
        else:
            self.loc_data_isold     = (secs_since(self.loc_data_secs) > self.old_loc_threshold_secs)
            self.loc_data_ispoorgps = (self.loc_data_gps_accuracy > Gb.gps_accuracy_threshold)

    @property
    def is_iosapp_data_good(self):
        return not self.is_iosapp_data_old

    @property
    def is_iosapp_data_old(self):
        return secs_since(self.iosapp_data_secs) > self.old_loc_threshold_secs

    @property
    def is_location_old_or_gps_poor(self):
        self.update_location_gps_accuracy_status()
        return (self.loc_data_isold or self.loc_data_ispoorgps)

    @property
    def is_location_old_and_gps_poor(self):
        self.update_location_gps_accuracy_status()
        return (self.loc_data_isold and self.loc_data_ispoorgps)

    @property
    def is_location_gps_good(self):
        self.update_location_gps_accuracy_status()
        return (self.loc_data_isold is False and self.loc_data_ispoorgps is False)

    @property
    def is_location_old(self):
        self.update_location_gps_accuracy_status()
        return self.loc_data_isold

    @property
    def is_location_good(self):
        return not self.is_location_old

    @property
    def is_gps_poor(self):
        self.update_location_gps_accuracy_status()
        return self.loc_data_ispoorgps

    @property
    def is_gps_good(self):
        return not self.is_gps_poor

#--------------------------------------------------------------------
    @property
    def still_at_last_location(self):
        return False
        return (self.loc_data_latitude == self.sensors[LATITUDE]
                    and self.loc_data_longitude == self.sensors[LONGITUDE])

    @property
    def sensor_secs(self):
        return (datetime_to_secs(self.sensors[LAST_UPDATE_DATETIME]))

    @property
    def loc_data_age(self):
        ''' timestamp(secs) --> age (secs ago)'''
        return (secs_since(self.loc_data_secs))

    @property
    def loc_data_time_age(self):
        ''' timestamp (secs) --> hh:mm:ss (secs ago)'''
        return self.loc_data_12hrtime_age

    @property
    def loc_data_time_utc(self):
        ''' timestamp (secs) --> hh:mm:ss'''
        return (secs_to_time(self.loc_data_secs))

    @property
    def loc_data_12hrtime_age(self):
        ''' location time --> 12:mm:ss (secs ago)'''
        return (f"{time_to_12hrtime(self.loc_data_time)} "
                f"({secs_to_time_str(self.loc_data_age)} ago)")

#--------------------------------------------------------------------
    @property
    def isnot_set(self):
        return (self.sensors[ZONE] == NOT_SET)

    @property
    def is_inzone(self):
        return (self.loc_data_zone not in [NOT_HOME, NOT_SET])

    @property
    def isnot_inzone(self):
        return (self.loc_data_zone == NOT_HOME)

    @property
    def is_inzone_iosapp_state(self):
        return (self.iosapp_data_state not in [NOT_HOME, NOT_SET])

    @property
    def isnot_inzone_iosapp_state(self):
        return (self.iosapp_data_state == NOT_HOME)

    @property
    def was_inzone(self):
        return (self.sensors[ZONE] not in [NOT_HOME, NOT_SET])

    @property
    def wasnot_inzone(self):
        return (self.sensors[ZONE] == NOT_HOME)

    @property
    def is_inzone_stationary(self):
        return (is_statzone(self.loc_data_zone))

    @property
    def isnot_inzone_stationary(self):
        return (is_statzone(self.loc_data_zone) is False)

    @property
    def was_inzone_stationary(self):
        return (is_statzone(self.sensors[ZONE]))

    @property
    def wasnot_inzone_stationary(self):
        return (is_statzone(self.sensors[ZONE]) is False)

#--------------------------------------------------------------------
    @property
    def pause_tracking(self):
        '''
        Pause tracking the device
        '''
        try:
            self.tracking_status = TRACKING_PAUSED

            self.write_ha_sensor_state(NEXT_UPDATE, PAUSED)
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
            self.tracking_status             = TRACKING_RESUMED
            Gb.all_tracking_paused_flag      = False
            Gb.any_device_was_updated_reason = ''
            Gb.device_update_in_process_flag = False
            Gb.master_update_in_process_flag = False
            Gb.initial_locate_complete_flag  = True

            for DeviceFmZone in self.DeviceFmZones_by_zone.values():
                DeviceFmZone.next_update_secs = 0
                DeviceFmZone.next_update_time = HHMMSS_ZERO

            self.next_update_DeviceFmZone     = self.DeviceFmZoneHome
            self.next_update_secs             = 0
            self.old_loc_poor_gps_cnt         = 0
            self.old_loc_poor_gps_msg         = ''
            self.poor_gps_flag                = False
            self.outside_no_exit_trigger_flag = False
            self.dev_data_device_status       = "Online"
            self.dev_data_device_status_code  = 200
            self.icloud_update_reason          = 'Trigger > Resume/Relocate'
            self.icloud_no_update_reason       = ''
            self.icloud_initial_locate_done    = False

            self.iosapp_request_loc_first_secs = 0
            self.iosapp_request_loc_last_secs  = 0
            self.passthru_zone_expire_secs     = 0

            if Gb.is_stat_zone_used and self.StatZone:
                self.stationary_zone_update_control = STAT_ZONE_MOVE_TO_BASE
                self.StatZone.update_stationary_zone_location()

            self.write_ha_sensor_state(NEXT_UPDATE, RESUMING)
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
        if (self.icloud_initial_locate_done is False
                or self.is_tracking_resumed):
            return True

        if self.next_update_DeviceFmZone is None:
            self.next_update_DeviceFmZone = self.DeviceFmZoneHome

        return self.next_update_secs <= Gb.this_update_secs

#--------------------------------------------------------------------
    @property
    def set_next_update_secs(self):
        '''
        Cycle thru the DeviceFmZones and get the lowest (next) updated secs

        Return:
            next_update_secs for the DeviceFmZone that will be updaed next
        Sets:
            next_update_DeviceFmZone to the object
        '''
        self.next_update_secs = HIGH_INTEGER
        self.next_update_DeviceFmZone = None
        for DeviceFmZone in self.DeviceFmZones_by_zone.values():
            if DeviceFmZone.next_update_secs <= self.next_update_secs:
                self.next_update_secs = DeviceFmZone.next_update_secs
                self.next_update_DeviceFmZone = DeviceFmZone

        return self.next_update_secs

#--------------------------------------------------------------------
    def calculate_distance_moved(self):
        '''
        Calculate the distance (km) from the last updated location to
        the current location
        '''
        if self.sensor_zone == NOT_SET:
            self.loc_data_distance_moved = 0
        else:
            self.loc_data_distance_moved = calc_distance_km(self.sensors[GPS], self.loc_data_gps)

#--------------------------------------------------------------------
    def distance_m(self, to_latitude, to_longitude):
        to_gps = (to_latitude, to_longitude)
        distance = calc_distance_m(self.loc_data_gps, to_gps)
        distance = 0 if distance < .2 else distance
        return distance

    def distance_km(self, to_latitude, to_longitude):
        to_gps = (to_latitude, to_longitude)
        distance = calc_distance_km(self.loc_data_gps, to_gps)
        distance = 0 if distance < .002 else distance
        return distance

#--------------------------------------------------------------------
    @property
    def badge_sensor_value(self):
        """ Determine the badge sensor state value """

        try:
            HOME_DISTANCE = km_to_mi_str(self.DeviceFmZoneHome.zone_dist)

            # Tracking Paused
            if self.is_tracking_paused:
                sensor_value = PAUSED_CAPS

            # Display zone name if in a zone
            elif self.loc_data_zone != NOT_HOME:
                sensor_value = self.loc_data_zone_fname

            # Display the distance to Home
            elif self.DeviceFmZoneHome:
                sensor_value = HOME_DISTANCE

            else:
                sensor_value = BLANK_SENSOR_FIELD

        except Exception as err:
            log_exception(err)
            sensor_value = BLANK_SENSOR_FIELD

        return sensor_value

#--------------------------------------------------------------------
    def write_ha_sensor_state(self, sensor_name, sensor_value):
        '''
        Display a value in a ic3 sensor field

        Input:
            sensor_name     Attribute field name (LOCATED_DATETIME)
            sensor_value    Value that should be displayed (self.loc_data_datetime)
        '''
        self.sensors[sensor_name] = sensor_value

        self.write_ha_sensors_state([sensor_name])

#--------------------------------------------------------------------
    def write_ha_device_tracker_state(self):
        ''' Update the device_tracker entity for this device '''

        if self.DeviceTracker:
            self.DeviceTracker.write_ha_device_tracker_state()

        self._update_restore_state_values()

#--------------------------------------------------------------------
    def write_ha_sensors_state(self, sensors=None):
        ''' Update the sensors for the Device that are in the sensor_list '''

        if sensors:
            update_sensors_list = {k:v  for sensor in sensors
                                        for k, v in self.Sensors.items()
                                        if k == sensor}
        else:
            update_sensors_list = self.Sensors

        for sensor, Sensor in update_sensors_list.items():
            Sensor.write_ha_sensor_state()

        self._update_restore_state_values()

#--------------------------------------------------------------------
    def write_ha_device_from_zone_sensors_state(self, sensors=None):
        ''' Update the sensors for the Device that are in the sensor_list '''

        if sensors:
            update_sensors_list = {k:v  for sensor in sensors
                                        for k, v in self.Sensors_from_zone.items()
                                        if k.startswith(sensor)}
        else:
            update_sensors_list = self.Sensors_from_zone

        for sensor, Sensor in update_sensors_list.items():
            Sensor.write_ha_sensor_state()

#--------------------------------------------------------------------
    def _update_restore_state_values(self):
        """ Save the Device's updated sensors in the icloud3.restore_state file """

        if self.update_sensors_flag is False:
            return

        Gb.restore_state_devices[self.devicename] = {}
        # Gb.restore_state_devices[self.devicename]['sensors'] = {}
        Gb.restore_state_devices[self.devicename]['last_update'] = datetime_now()
        Gb.restore_state_devices[self.devicename]['sensors'] = copy.deepcopy(self.sensors)

        Gb.restore_state_devices[self.devicename]['from_zone'] = {}
        for from_zone, DeviceFmZone in self.DeviceFmZones_by_zone.items():
            Gb.restore_state_devices[self.devicename]['from_zone'][from_zone] = copy.deepcopy(DeviceFmZone.sensors)

        restore_state.write_storage_icloud3_restore_state_file()

#--------------------------------------------------------------------
    def initialize_usage_counters(self):
        self.count_update_icloud    = 0
        self.count_update_iosapp    = 0
        self.count_discarded_update = 0
        self.count_state_changed    = 0
        self.count_trigger_changed  = 0
        self.count_waze_locates     = 0
        self.iosapp_request_loc_cnt = 0
        self.time_waze_calls        = 0.0

#--------------------------------------------------------------------------------
    @property
    def format_info_msg(self):
        """
        Analyze the Device's fields.

        Return: Info text to be displayed in the info field
        """
        try:
            info_msg = f"{DOT}"
            if Gb.info_notification != '':
                info_msg = f"●● {Gb.info_notification} ●●"
                Gb.info_notification = ''

            if self.offline_secs > 0:
                info_msg +=(f"DeviceOffline@{secs_to_time_age_str(self.offline_secs)} "
                            f"({self.device_status}) ")

            if (Gb.is_stat_zone_used
                    and self.StatZone.timer > 0
                    and self.sensors[MOVED_DISTANCE] == 0):
                info_msg += (f"IntoStatZone@{secs_to_time(self.StatZone.timer)}, ")

            elif self.zone_change_secs > 0:
                into_exit_text = "Into" if self.is_inzone else "Exit"
                info_msg += (f"{into_exit_text}Zone@{secs_to_time_age_str(self.zone_change_secs)}, ")

            elif self.sensors[FROM_ZONE] and self.sensors[FROM_ZONE] != NOT_SET and self.sensors[FROM_ZONE] != HOME:
                from_zone = self.sensors[FROM_ZONE]
                Zone = Gb.Zones_by_zone[from_zone]
                info_msg += f"TrackFmZone-{Zone.display_as}, "

            if self.NearDeviceUsed:
                info_msg +=(f"Used Nearby Device {self.NearDeviceUsed.fname}, "
                            f"({format_dist_m(self.near_device_distance)}")

            if self.tracking_method != self.dev_data_source.lower():
                info_msg += (f"DataSource-{self.dev_data_source}, ")

            if self.dev_data_battery_level > 0:
                info_msg += f"Battery-{self.format_battery_level}, "

            if self.is_gps_poor:
                info_msg += (f"Poor.GPS.Accuracy, Dist-{self.loc_data_gps_accuracy}m "
                            f"(#{self.old_loc_poor_gps_cnt})")
                if (is_inzone_zone(self.loc_data_zone)
                        and Gb.discard_poor_gps_inzone_flag):
                    info_msg += "(Ignored)"
                info_msg += ", "

            if self.old_loc_poor_gps_cnt > 16:
                info_msg += (f"May Be Offline, "
                            f"LocTime-{self.loc_data_12hrtime_age}, "
                            f"OldCnt-#{self.old_loc_poor_gps_cnt}, ")

        except Exception as err:
            log_exception(err)

        return info_msg[:-2]

#-------------------------------------------------------------------
    def display_info_msg(self, info_msg):
        '''
        Display the info msg in the Device's sensor.[devicename]_info entity

        Return:
            Message text
        '''
        Gb.broadcast_info_msg = None

        if instr(info_msg, DOT) is False:
            info_msg = f"{DOT}{info_msg}"

        try:
            self.write_ha_sensor_state(INFO, info_msg)
        except:
            pass

        return info_msg


#--------------------------------------------------------------------
    def is_location_data_rejected(self):
        '''
        Post an event message describing the location/gps status of the data being used
        '''
        if (self.is_location_gps_good or self.is_data_source_NOT_SET
                #or self.old_loc_poor_gps_cnt < 2
                or self.loc_data_secs > self.last_update_loc_secs):
            return False

        try:
            interval, error_cnt, max_error_cnt = det_interval.get_error_retry_interval(self)
            det_interval.update_all_device_fm_zone_sensors_interval(self, interval)

            if self.old_loc_poor_gps_cnt < 2:
                return False

            reason_msg = ''

            if self.is_tracked:
                if self.loc_data_isold:
                    reason_msg = (f"Old>{secs_to_time_str(self.old_loc_threshold_secs)}")
                elif self.loc_data_ispoorgps:
                    reason_msg = (f"PoorGPS>{Gb.gps_accuracy_threshold}m")

            event_msg =(f"Rejected (#{self.old_loc_poor_gps_cnt}) > "
                        f"{self.dev_data_source}-{self.loc_data_time_gps}, "
                        f"{secs_to_age_str(self.loc_data_secs)}, "
                        f"{reason_msg}, "
                        f"NextUpdate-{secs_to_time(self.next_update_secs)} "
                        f"({secs_to_time_str(interval)}), "
                        f"LastUpdate-{secs_to_age_str(self.last_update_loc_secs)}")

            post_event(self.devicename, event_msg)

        except Exception as err:
            log_exception(err)

        return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   CALCULATE THE OLD LOCATION THRESHOLD FOR THE DEVICE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def calculate_old_location_threshold(self):
        """
        The old_loc_threshold_secs is used to determine if the Device's location is too
        old to be used. If it is too old, the Device's location will be requested again
        using an interval calculated in the determine_interval_after_error routine. The
        old_loc_threshold_secs is recalculated each time the Device's location is
        updated.
        """
        try:
            # Device is approaching a TrackFmZone (distance less than 1-km, on a 15-secs
            # interval). Set threshold to 15-secs so the location will be updated
            # immediately.
            if self.is_approaching_tracked_zone:
                self.old_loc_threshold_secs = 30 + Gb.old_location_adjustment
                return

            # Get smallest interval of all zones being tracked from
            interval = HIGH_INTEGER
            for from_zone, DeviceFmZone in self.DeviceFmZones_by_zone.items():
                if DeviceFmZone.interval_secs < interval:
                    interval = DeviceFmZone.interval_secs

            threshold_secs = 60
            if self.is_inzone:
                threshold_secs = interval * .025        # 2.5% of interval time
                if threshold_secs < 120: threshold_secs = 120

            elif self.DeviceFmZoneCurrent.zone_dist > 5:
                threshold_secs = 180

            elif interval < 90:
                threshold_secs = 60
            else:
                threshold_secs = interval * .125

            if self.passthru_zone_expire_secs > 0:
                threshold_secs = 15
            elif threshold_secs < 60:
                threshold_secs = 60
            elif threshold_secs > 600:
                threshold_secs = 600

            if (Gb.old_location_threshold > 0
                    and threshold_secs > Gb.old_location_threshold):
                threshold_secs = Gb.old_location_threshold

            self.old_loc_threshold_secs = threshold_secs + Gb.old_location_adjustment

        except Exception as err:
            log_exception(err)
            post_internal_error('Calc Old Threshold', traceback.format_exc)
            self.old_loc_threshold_secs = 120


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE DISTANCE TO OTHER DEVICES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_distance_to_other_devices(self):
        '''
        Cycle through all devices and update this device's and the other device's
        dist_to_other_device_info field

        {devicename: [distance_m, gps_accuracy_factor, display_text]}
        '''

        for _Device in Gb.Devices:
            if _Device is self:
                continue

            if self.sensor_zone == _Device.sensor_zone and self.is_inzone:
                is_location_old = False
            else:
                is_location_old = ((secs_since(_Device.loc_data_secs) > _Device.old_loc_threshold_secs * 1.5)
                                        or (secs_since(self.loc_data_secs) > self.old_loc_threshold_secs * 1.5))
            if is_location_old:
                continue

            dist_apart_m        = _Device.distance_m(self.loc_data_latitude, self.loc_data_longitude)
            min_gps_accuracy    = (min(self.loc_data_gps_accuracy, _Device.loc_data_gps_accuracy))
            gps_accuracy_factor = round(min_gps_accuracy * dist_apart_m / NEAR_DEVICE_DISTANCE)

            if dist_apart_m > 500:
                display_text = f"{dist_apart_m/1000:.1f}km/±{min_gps_accuracy}m"
            else:
                display_text = f"{dist_apart_m}m/±{min_gps_accuracy}m"

            distance_apart_data = [dist_apart_m, gps_accuracy_factor, display_text]

            if (_Device.devicename not in self.dist_to_other_devices
                    or self.devicename not in _Device.dist_to_other_devices
                    or _Device.dist_to_other_devices[self.devicename] != distance_apart_data
                    or self.dist_to_other_devices[_Device.devicename] != distance_apart_data):
                before_s = self.dist_to_other_devices.get(_Device.devicename)

                self.dist_to_other_devices[_Device.devicename] = distance_apart_data
                self.dist_to_other_devices_datetime = datetime_now()
                _Device.dist_to_other_devices[self.devicename] = distance_apart_data

                Gb.dist_to_other_devices_update_sensor_list.add(self.devicename)
                Gb.dist_to_other_devices_update_sensor_list.add(_Device.devicename)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE BATTERY INFORMATION
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_iosapp_battery_information(self):
        '''
        Update the battery info from the iOS App if the iOS App data is newer than the FamShr
        battery info. Then update the sensors if it has changed.

        Return:
            True - Data has changed
            False - Data has not changed
        '''

        try:
            if self.iosapp_entity[BATTERY_LEVEL]:
                try:
                    self.dev_data_battery_level = int(entity_io.get_state(self.iosapp_entity[BATTERY_LEVEL]))
                except:
                    self.dev_data_battery_leve = 0

                battery_status = entity_io.get_state(self.iosapp_entity[BATTERY_STATUS])
                self.dev_data_battery_status = battery_status if battery_status else UNKNOWN
                self.dev_data_battery_source = IOSAPP_FNAME

            if (self.dev_data_battery_level == self.sensors[BATTERY]
                    and self.dev_data_battery_status.lower() == self.sensors[BATTERY_STATUS].lower()):
                return False

            elif self.dev_data_battery_level == 0:
                return False

            self.dev_data_battery_level_last = self.sensors[BATTERY]
            # self.dev_data_battery_status_last = self.sensors[BATTERY_STATUS]

            self.sensors[BATTERY]        = self.dev_data_battery_level
            self.sensors[BATTERY_SOURCE] = self.dev_data_battery_source
            self.sensors[BATTERY_STATUS] = self.format_battery_status
            self.write_ha_sensors_state([BATTERY, BATTERY_STATUS])

            return True

        except Exception as err:
            # log_exception(err)
            return False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Update the Device data from the iOS App raw data or from the RawData
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_dev_loc_data_from_raw_data_IOSAPP(self, RawData=None):
        if (self.iosapp_data_secs <= self.loc_data_secs
                or self.iosapp_data_secs == 0):
            return

        self.last_data_update_secs = time_now_secs()

        self.dev_data_source            = IOSAPP_FNAME
        self.dev_data_fname             = self.fname
        self.dev_data_device_class      = self.device_type
        self.dev_data_device_status     = "Online"
        self.dev_data_device_status_code = 200

        if (self.iosapp_data_battery_level > 0
                and self.iosapp_data_battery_status):
            self.dev_data_battery_level  = self.iosapp_data_battery_level
            self.dev_data_battery_status = self.iosapp_data_battery_status
            self.dev_data_battery_source = IOSAPP_FNAME

        self.loc_data_latitude          = self.iosapp_data_latitude
        self.loc_data_longitude         = self.iosapp_data_longitude
        self.loc_data_gps_accuracy      = self.iosapp_data_gps_accuracy
        self.loc_data_vertical_accuracy = self.iosapp_data_vertical_accuracy
        self.loc_data_altitude          = self.iosapp_data_altitude
        self.loc_data_secs              = self.iosapp_data_secs
        self.loc_data_datetime          = secs_to_datetime(self.iosapp_data_secs)
        self.loc_data_time              = secs_to_time(self.iosapp_data_secs)

        self.calculate_distance_moved()
        self.update_distance_to_other_devices()
        self.write_ha_sensor_state(LAST_LOCATED, self.loc_data_time)
        self.display_update_location_msg()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_dev_loc_data_from_raw_data_FAMSHR_FMF(self, RawData, requesting_device_flag=True):
        '''
        Update the Device's location data with the RawData (FamShr or FmF) from the iCloud Account.

        Parameters:
            RawData - FamShr or FmF object to be used to update this Device
            requesting_device_flag - Multiple devices can be updated since all device info is returned
                    from iCloud on a location request.
                        True-   This is the Device that requested the update and the Update Location
                                info should be displayed in the Event Log
                        False - This is another device and do not display the Update Location msg
        '''
        if (LOCATION not in RawData.device_data
                or RawData.device_data[LOCATION] is None
                or (RawData.location_secs <= self.loc_data_secs and self.loc_data_secs > 0)):
            return

        self.last_data_update_secs = time_now_secs()

        location                       = RawData.device_data[LOCATION]
        location_secs                  = RawData.location_secs
        RawData.last_used_location_secs = RawData.location_secs
        RawData.last_used_location_time = RawData.location_time

        self.dev_data_source           = RawData.tracking_method
        self.dev_data_fname            = RawData.device_data.get(NAME, "")
        self.dev_data_device_class     = RawData.device_data.get(ICLOUD_DEVICE_CLASS, "")
        self.dev_data_low_power_mode   = RawData.device_data.get(ICLOUD_LOW_POWER_MODE, "")

        icloud_rawdata_battery_level = round(RawData.device_data.get(ICLOUD_BATTERY_LEVEL, 0) * 100)
        icloud_rawdata_battery_status = RawData.device_data.get(ICLOUD_BATTERY_STATUS, '')
        if (icloud_rawdata_battery_level > 0
                and icloud_rawdata_battery_status):
            self.dev_data_battery_level  = icloud_rawdata_battery_level
            self.dev_data_battery_status = icloud_rawdata_battery_status
            self.dev_data_battery_source = RawData.tracking_method

        self.dev_data_device_status_code = RawData.device_data.get(ICLOUD_DEVICE_STATUS, 0)
        self.dev_data_device_status      = DEVICE_STATUS_CODES.get(self.dev_data_device_status_code, UNKNOWN)

        self.loc_data_latitude       = location.get(LATITUDE, 0)
        self.loc_data_longitude      = location.get(LONGITUDE, 0)
        self.loc_data_gps_accuracy   = round(location.get(ICLOUD_HORIZONTAL_ACCURACY, 0))
        self.loc_data_secs           = location_secs
        self.loc_data_datetime       = secs_to_datetime(location_secs)
        self.loc_data_time           = secs_to_time(location_secs)
        self.loc_data_altitude       = float(f"{location.get(ALTITUDE, 0):.1f}")
        self.loc_data_vert_accuracy  = round(location.get(ICLOUD_VERTICAL_ACCURACY, 0))
        self.loc_data_isold          = location.get('isOld', False)
        self.loc_data_ispoorgps      = location.get('isInaccurate', False)

        self.calculate_distance_moved()
        self.update_distance_to_other_devices()
        self.write_ha_sensor_state(LAST_LOCATED, self.loc_data_time)
        if requesting_device_flag or self.is_monitored:
            self.display_update_location_msg()

#-------------------------------------------------------------------
    def display_update_location_msg(self):

        if self.loc_data_time_gps == self.last_loc_data_time_gps:
            return

        if self.isnot_inzone or self.moved_since_last_update > .015:
            event_msg =(f"Updated ({self.dev_data_source}) > "
                        f"{self.last_loc_data_time_gps}"
                        f"{RARROW}{self.loc_data_time_gps}, "
                        f"Located-{secs_to_age_str(self.loc_data_secs)}, "
                        f"Moved-{format_dist_km(self.moved_since_last_update)}")
            post_event(self.devicename,event_msg)

        self.last_loc_data_time_gps = self.loc_data_time_gps

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_sensor_values_from_data_fields(self):
        #Note: Final prep and update device attributes via
        #device_tracker.see. The gps location, battery, and
        #gps accuracy are not part of the attrs variable and are
        #reformatted into device attributes by 'See'. The gps
        #location goes to 'See' as a "(latitude, longitude)" pair.
        #'See' converts them to LATITUDE and LONGITUDE
        #and discards the 'gps' item.

        # Determine the soonest DeviceFmZone to update, then get the sensor
        # values to be displayed with the Device sensors

        try:
            # Reset any special um message fields before update
            self.sensors_um = {}

            # Device related sensors
            self.sensors[INFO]                 = self.format_info_msg
            self.sensors[BATTERY]              = self.dev_data_battery_level
            self.sensors[BATTERY_STATUS]       = self.format_battery_status
            self.sensors[BATTERY_SOURCE]       = self.dev_data_battery_source
            self.sensors[DEVICE_STATUS]        = self.device_status
            self.sensors[LOW_POWER_MODE]       = self.dev_data_low_power_mode
            self.sensors[BADGE]                = self.badge_sensor_value

            # Location related items
            self.sensors[GPS]                  = (self.loc_data_latitude, self.loc_data_longitude)
            self.sensors[LATITUDE]             = self.loc_data_latitude
            self.sensors[LONGITUDE]            = self.loc_data_longitude
            self.sensors[GPS_ACCURACY]         = m_to_ft_str(self.loc_data_gps_accuracy)
            self.sensors[ALTITUDE]             = m_to_ft_str(self.loc_data_altitude)
            self.sensors[VERT_ACCURACY]        = m_to_ft_str(self.loc_data_vert_accuracy)
            self.sensors[LOCATION_SOURCE]      = self.dev_data_source
            self.sensors[TRIGGER]              = self.trigger
            self.sensors[LAST_LOCATED_DATETIME]= self.loc_data_datetime
            self.sensors[LAST_LOCATED_TIME]    = self.loc_data_time
            self.sensors[LAST_LOCATED]         = self.loc_data_time
            self.sensors[DISTANCE_TO_DEVICES]  = self.dist_apart_msg.rstrip(', ')

            self.next_update_secs              = self.DeviceFmZoneTracked.next_update_secs
            self.next_update_DeviceFmZone      = self.DeviceFmZoneTracked

            self.sensors[FROM_ZONE]            = self.DeviceFmZoneTracked.from_zone
            self.sensors[INTERVAL]             = self.DeviceFmZoneTracked.sensors[INTERVAL]
            self.sensors[NEXT_UPDATE_DATETIME] = self.DeviceFmZoneTracked.sensors[NEXT_UPDATE_DATETIME]
            self.sensors[NEXT_UPDATE_TIME]     = self.DeviceFmZoneTracked.sensors[NEXT_UPDATE_TIME]
            self.sensors[NEXT_UPDATE]          = self.DeviceFmZoneTracked.sensors[NEXT_UPDATE]
            self.sensors[LAST_UPDATE_DATETIME] = self.DeviceFmZoneTracked.sensors[LAST_UPDATE_DATETIME]
            self.sensors[LAST_UPDATE_TIME]     = self.DeviceFmZoneTracked.sensors[LAST_UPDATE_TIME]
            self.sensors[LAST_UPDATE]          = self.DeviceFmZoneTracked.sensors[LAST_UPDATE]
            self.sensors[TRAVEL_TIME_MIN]      = self.DeviceFmZoneTracked.sensors[TRAVEL_TIME_MIN]
            self.sensors[TRAVEL_TIME]          = self.DeviceFmZoneTracked.sensors[TRAVEL_TIME]
            self.sensors[ZONE_DISTANCE]        = self.DeviceFmZoneTracked.sensors[ZONE_DISTANCE]
            self.sensors[MAX_DISTANCE]         = self.DeviceFmZoneTracked.sensors[MAX_DISTANCE]
            self.sensors[WAZE_DISTANCE]        = self.DeviceFmZoneTracked.sensors[WAZE_DISTANCE]
            self.sensors[WAZE_METHOD]          = self.DeviceFmZoneTracked.sensors[WAZE_METHOD]
            self.sensors[CALC_DISTANCE]        = self.DeviceFmZoneTracked.sensors[CALC_DISTANCE]
            self.sensors[MOVED_DISTANCE]       = self.DeviceFmZoneTracked.sensors[MOVED_DISTANCE]
            self.sensors[HOME_DISTANCE]        = self.DeviceFmZoneHome.sensors[ZONE_DISTANCE]

            # If moving towards a tracked from zone, change the direction to 'To-[zonename]'
            if self.DeviceFmZoneTracked.sensors[DIR_OF_TRAVEL].startswith(TOWARDS):
                self.DeviceFmZoneTracked.dir_of_travel = \
                self.DeviceFmZoneTracked.sensors[DIR_OF_TRAVEL] = \
                self.sensors[DIR_OF_TRAVEL] = TOWARDS
            else:
                self.sensors[DIR_OF_TRAVEL] = self.DeviceFmZoneTracked.sensors[DIR_OF_TRAVEL]

            # Zone related sensors
            if self.loc_data_zone != self.sensor_zone:
                self.sensors[LAST_ZONE]      = self.sensors[ZONE]
                self.sensors[LAST_ZONE_NAME] = self.sensors[ZONE_NAME]
                self.sensors[LAST_ZONE_FNAME]= self.sensors[ZONE_FNAME]
                self.sensors[ZONE_DATETIME]  = self.zone_change_datetime

            try:
                Zone = Gb.Zones_by_zone[self.loc_data_zone]
                self.sensors[ZONE] = Zone.display_as if Gb.zone_sensor_evlog_format else self.loc_data_zone
            except:
                self.sensors[ZONE] = self.loc_data_zone
            self.sensors[ZONE_NAME]  = Zone.name
            self.sensors[ZONE_FNAME] = Zone.fname

            self.sensors[DEVICE_TRACKER_STATE_VALUE] = self.sensors[ZONE]

            if self.sensors[FROM_ZONE] != HOME:
                self.sensors_um[ZONE_DISTANCE] = (f"{Gb.um} "
                                        f"{circle_letter(self.DeviceFmZoneTracked.from_zone)}")
            if Gb.is_stat_zone_used and self.StatZone:
                self.StatZone.update_stationary_zone_location()

            self.last_update_loc_secs = self.loc_data_secs

        except Exception as err:
            post_internal_error('Set Attributes', traceback.format_exc)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def log_data_fields(self):

        if self.NearDevice:
            near_devicename = self.NearDevice.devicename
        else:
            near_devicename = 'None'

        log_msg = ( f"Device Status > {self.devicename} > "
                    f"NearDevice-{near_devicename}, "
                    f"iOSAppZone-{self.iosapp_data_state}, "
                    f"iC3Zone-{self.loc_data_zone}, ")
        if self.DeviceFmZoneHome:
            log_msg += (f"Interval-{self.sensors[INTERVAL]}, "
                        f"TravTime-{self.sensors[TRAVEL_TIME]}, "
                        f"Dist-{self.sensors[HOME_DISTANCE]} {Gb.um}, "
                        f"NextUpdt-{self.sensors[NEXT_UPDATE]}, "
                        f"Dir-{self.sensors[DIR_OF_TRAVEL]}, ")
        log_msg += (f"Moved-{self.sensors[MOVED_DISTANCE]}, "
                    f"LastUpdate-{self.sensors[LAST_UPDATE_TIME]}, "
                    f"IntoStatZone@{secs_to_time(self.StatZone.timer)}, "
                    f"GPS-{self.loc_data_fgps}, "
                    f"LocAge-{secs_to_age_str(self.loc_data_secs)}, "
                    f"OldThreshold-{secs_to_time_str(self.old_loc_threshold_secs)}, "
                    f"LastEvLogMsg-{secs_to_time(self.last_evlog_msg_secs)}, "
                    f"Battery-{self.format_battery_level_status_source})")

        log_debug_msg(log_msg)
        # log_msg = ( f"Device Status > {self.devicename} > "
        #             f"NearDevice-{near_devicename}, "
        #             f"iOSAppZone-{self.iosapp_data_state}, "
        #             f"iC3Zone-{self.loc_data_zone}, ")
        # if self.DeviceFmZoneHome:
        #     log_msg += (f"Interval-{self.DeviceFmZoneHome.interval_str}, "
        #                 f"TravTime-{self.DeviceFmZoneHome.last_tavel_time}, "
        #                 f"Dist-{km_to_mi(self.DeviceFmZoneHome.zone_dist)} {Gb.um}, "
        #                 f"NextUpdt-{self.DeviceFmZoneHome.next_update_time}, "
        #                 f"Dir-{self.DeviceFmZoneHome.dir_of_travel}, ")
        # log_msg += (f"Moved-{format_dist_km(self.StatZone.moved_dist)}, "
        #             f"LastUpdate-{secs_to_time(self.last_data_update_secs)}, "
        #             f"IntoStatZone@{secs_to_time(self.StatZone.timer)}, "
        #             f"GPS-{self.loc_data_fgps}, "
        #             f"LocAge-{secs_to_age_str(self.loc_data_secs)}, "
        #             f"OldThreshold-{secs_to_time_str(self.old_loc_threshold_secs)}, "
        #             f"LastEvLogMsg-{secs_to_time(self.last_evlog_msg_secs)}, "
        #             f"Battery-{self.dev_data_battery_level}%, "
        #             f"{self.dev_data_battery_status} "
        #             f"({self.dev_data_battery_source})")

        # log_debug_msg(log_msg)
