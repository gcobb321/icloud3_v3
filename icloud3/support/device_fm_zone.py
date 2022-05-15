#####################################################################
#
#   This module handles all tracking activities for a device. It contains
#   the following modules:
#       TrackFromZones - iCloud3 creates an object for each device/zone
#           with the tracking data fields.
#
#   The primary methods are:
#       determine_interval - Determines the polling interval, update times,
#           location data, etc for the device based on the distance from
#           the zone.
#       determine_interval_after_error - Determines the interval when the
#           location data is to be discarded due to poor GPS, it is old or
#           some other error occurs.
#
#####################################################################


from ..global_variables  import GlobalVariables as Gb
from ..const             import (HHMMSS_ZERO, NOT_SET, HOME, DATETIME_ZERO, HIGH_INTEGER,
                                ZONE_DISTANCE, HOME_DISTANCE, DISTANCE, INTERVAL, FROM_ZONE,
                                LAST_UPDATE_DATETIME, LAST_UPDATE_TIME, LAST_UPDATE,
                                NEXT_UPDATE_DATETIME, NEXT_UPDATE_TIME, NEXT_UPDATE,
                                CALC_DISTANCE, TRAVEL_DISTANCE, DIR_OF_TRAVEL,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, WAZE_DISTANCE,  )
from ..helpers.distance  import (km_to_mi, calc_distance_km, )
from ..helpers.time      import (datetime_to_12hrtime, )
from ..helpers.base      import (log_exception, post_internal_error,  _trace, _traceha, )

import homeassistant.util.dt as dt_util
import traceback


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3DeviceFmZone(object):

    def __init__(self, Device, from_zone):
        try:
            self.Device               = Device
            self.devicename           = Device.devicename
            self.FromZone             = Gb.Zones_by_zone[from_zone]
            self.from_zone            = from_zone
            self.devicename_zone      = (f"{self.devicename}:{from_zone}")
            self.from_zone_display_as = self.FromZone.display_as

            self.initialize()
            self.initialize_sensors()

        except Exception as err:
            log_exception(err)

    def initialize(self):
        try:
            self.interval_secs           = 0
            self.interval_str            = '0'
            self.interval_method         = ''
            self.last_tavel_time         = ''
            self.last_distance_str       = ''
            self.last_distance_km        = 0
            self.dir_of_travel           = NOT_SET
            self.last_update_time        = HHMMSS_ZERO
            self.last_update_secs        = 0
            self.next_update_time        = HHMMSS_ZERO
            self.next_update_secs        = 0
            self.next_update_devicenames = ''
            self.waze_time               = 0
            self.waze_dist               = 0
            self.calc_dist               = 0
            self.zone_dist               = 0
            self.waze_results            = None

            self.sensor_prefix       = (f"sensor.{self.devicename}_") \
                                            if self.from_zone== HOME else (f"sensor.{self.devicename}_{self.from_zone}_")
            self.sensor_prefix_zone  = '' if self.from_zone== HOME else (f"{self.from_zone}_")
            self.info_status_msg     = (f"From-({self.from_zone})")

        except:
            post_internal_error(traceback.format_exc)

    def initialize_sensors(self):
        self.sensors                       = {}
        self.sensors_um                    = {}

        self.sensors[FROM_ZONE]            = self.from_zone
        self.sensors[INTERVAL]             = '0'
        self.sensors[NEXT_UPDATE_DATETIME] = DATETIME_ZERO
        self.sensors[NEXT_UPDATE_TIME]     = HHMMSS_ZERO
        self.sensors[NEXT_UPDATE]          = HHMMSS_ZERO
        self.sensors[LAST_UPDATE_DATETIME] = DATETIME_ZERO
        self.sensors[LAST_UPDATE_TIME]     = HHMMSS_ZERO
        self.sensors[LAST_UPDATE]          = HHMMSS_ZERO
        self.sensors[TRAVEL_TIME]          = 0
        self.sensors[TRAVEL_TIME_MIN]      = 0
        self.sensors[DISTANCE]             = 0
        self.sensors[ZONE_DISTANCE]        = 0
        self.sensors[WAZE_DISTANCE]        = 0
        self.sensors[CALC_DISTANCE]        = 0
        self.sensors[DIR_OF_TRAVEL]        = NOT_SET
        self.sensors[TRAVEL_DISTANCE]      = 0

        Sensors_from_zone      = Gb.Sensors_by_devicename_from_zone[self.devicename]
        from_this_zone_sensors = {k:v for k, v in Sensors_from_zone.items()
                                        if v.from_zone == self.from_zone}
        for sensor, Sensor in from_this_zone_sensors.items():
            Sensor.DeviceFmZone = self

    def __repr__(self):
        return (f"<DeviceFmZone: {self.devicename_zone}>")

    @property
    def zone_distance_str(self):
        return ('' if self.zone_dist == 0 else (f"{km_to_mi(self.zone_dist)} {Gb.um}"))

    @property
    def distance_km(self):
        return calc_distance_km(    self.Device.loc_data_latitude,
                                    self.Device.loc_data_longitude,
                                    self.FromZone.latitude,
                                    self.FromZone.longitude)
