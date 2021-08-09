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


from .globals           import GlobalVariables as Gb
from .const_general     import (HHMMSS_ZERO, HOME, DATETIME_ZERO, HIGH_INTEGER, )
from .const_attrs       import (ZONE_DISTANCE, INTERVAL, LAST_UPDATE_TIME,
                                NEXT_UPDATE_TIME, CALC_DISTANCE, TRAVEL_DISTANCE, DIR_OF_TRAVEL,
                                TRAVEL_TIME, WAZE_DISTANCE,  )
from .helpers.distance  import (km_to_mi, calc_distance_km, )
from .helpers.base      import (log_exception, post_internal_error,  _trace, _traceha, )


import homeassistant.util.dt as dt_util
import traceback


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class DeviceFmZones(object):

    def __init__(self, Device, zone):
        try:
            self.Device          = Device
            self.devicename      = Device.devicename
            self.Zone            = Gb.Zones_by_zone[zone]
            self.zone            = zone
            self.devicename_zone = (f"{self.devicename}:{zone}")
            self.zone_display_as = self.Zone.display_as

            self.initialize()
            self.initialize_attrs()

        except Exception as err:
            log_exception(err)

    def initialize(self):
        try:
            self.interval_secs     = 0
            self.interval_str      = '0 sec'
            self.last_tavel_time   = ''
            self.last_distance_str = ''
            self.last_update_time  = HHMMSS_ZERO
            self.last_update_secs  = 0
            self.next_update_time  = HHMMSS_ZERO
            self.next_update_secs  = 0
            self.next_update_devicenames= ''

            self.sensor_prefix       = (f"sensor.{self.devicename}_") \
                                            if self.zone== HOME else (f"sensor.{self.devicename}_{self.zone}_")
            self.sensor_prefix_zone  = '' if self.zone== HOME else (f"{self.zone}_")
            self.info_status_msg     = (f"From-({self.zone})")

            self.waze_time = 0
            self.waze_dist = HIGH_INTEGER
            self.calc_dist = HIGH_INTEGER
            self.zone_dist = HIGH_INTEGER
            self.waze_results = []

        except:
            post_internal_error(traceback.format_exc)

    def initialize_attrs(self):
        self.attrs                     = {}
        self.attrs[INTERVAL]           = ''
        self.attrs[LAST_UPDATE_TIME]   = DATETIME_ZERO
        self.attrs[NEXT_UPDATE_TIME]   = DATETIME_ZERO
        self.attrs[TRAVEL_TIME]        = ''
        self.attrs[ZONE_DISTANCE]      = ''
        self.attrs[CALC_DISTANCE]      = ''
        self.attrs[WAZE_DISTANCE]      = ''
        self.attrs[DIR_OF_TRAVEL]      = ''
        self.attrs[TRAVEL_DISTANCE]    = ''

        self.after_error_attrs                     = {}
        self.after_error_attrs[INTERVAL]           = ''
        self.after_error_attrs[LAST_UPDATE_TIME]   = DATETIME_ZERO
        self.after_error_attrs[NEXT_UPDATE_TIME]   = DATETIME_ZERO

    def __repr__(self):
        return (f"<DeviceFmZone: {self.devicename_zone}>")

    @property
    def zone_distance_str(self):
        return ('' if self.zone_dist == 0 else (f"{km_to_mi(self.zone_dist)} {Gb.um}"))

    @property
    def distance(self):
        return calc_distance_km(    self.Device.loc_data_latitude,
                                    self.Device.loc_data_longitude,
                                    self.Zone.latitude,
                                    self.Zone.longitude)

