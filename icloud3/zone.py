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

from .global_variables  import GlobalVariables as Gb
from .const             import (STATIONARY, HOME,
                                STAT_ZONE_NO_UPDATE, STAT_ZONE_MOVE_DEVICE_INTO, STAT_ZONE_MOVE_TO_BASE,
                                NAME, FRIENDLY_NAME, LATITUDE, LONGITUDE, ICON,
                                RADIUS, PASSIVE, HIGH_INTEGER, )

from .helpers.base      import (instr, is_statzone,
                                post_event, post_error_msg, post_monitor_msg, log_exception, _trace, _traceha, )
from .helpers.time      import (time_now_secs, datetime_now, secs_to_time, )
from .helpers.distance  import (calc_distance_m, calc_distance_km, )
from .helpers.format    import (format_gps, format_dist, format_dist_m, format_time_age, )

from   homeassistant.util.location import distance


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#   GLOBAL SUPPORT FUNCTIONS & CONSTANTS
#
#####################################################################

MDI_NAME_LETTERS = {'circle-outline': '', 'box-outline': '', 'circle': '', 'box': ''}


#####################################################################
#
#   Zones Class Object
#       Set up the object for each Zone.
#
#       Input:
#           zone - Zone name
#           zone_data - A dictionary containing the Zone attributes
#                   (latitude, longitude. radius, passive, friendly name)
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3Zone(object):

    def __init__(self, zone, zone_data):
        self.zone = zone

        if NAME in zone_data:
            ztitle = zone_data[NAME].title()
        else:
            ztitle = zone.title().replace("_S_","'s " ).replace("_", " ")
            ztitle = ztitle.replace(' Iphone', ' iPhone')
            ztitle = ztitle.replace(' Ipad', ' iPad')
            ztitle = ztitle.replace(' Ipod', ' iPod')

        self.title      = ztitle
        self.latitude   = zone_data.get(LATITUDE, 0)
        self.longitude  = zone_data.get(LONGITUDE, 0)
        self.passive    = zone_data.get(PASSIVE, True)
        self.radius     = int(zone_data.get(RADIUS, 100))
        self.name       = ztitle.replace(" ","")
        self.dist_time_history = []        #Entries are a list - [lat, long, distance, travel time]

        if instr(zone, STATIONARY):
            self.fname      = Gb.stat_zone_fname
            self.display_as = Gb.stat_zone_fname
        else:
            self.fname      = zone_data.get(FRIENDLY_NAME, ztitle)
            self.display_as = self.name

        self.sensor_prefix = '' if self.zone == HOME else self.display_as

        self.name.replace("'", "`")
        self.fname.replace("'", "`")
        self.display_as.replace("'", "`")

        if zone == HOME:
            Gb.HomeZone = self


    def __repr__(self):
        return (f"<Zone: {self.zone}>")

    #---------------------------------------------------------------------
    @property
    def latitude5(self):
            return round(self.latitude, 5)

    @property
    def longitude5(self):
            return round(self.longitude, 5)

    @property
    def radius_km(self):
        return round(self.radius/1000, 4)

    # Calculate distance in meters
    def distance_m(self, to_latitude, to_longitude):
        return calc_distance_m(self.latitude, self.longitude,
                            to_latitude, to_longitude)

    # Calculate distance in kilometers
    def distance_km(self, to_latitude, to_longitude):
        return calc_distance_km(self.latitude, self.longitude,
                    to_latitude, to_longitude)

    # Return the DeviceFmZone obj from the devicename and this zone
    @property
    def DeviceFmZone(self, Device):
        return (f"{Device.devicename}:{self.zone}")

#####################################################################
#
#   StationaryZones Class Object
#       Set up the Stationary Zone for each device. Then add the Stationary Zone
#       To the Zones Class Object.
#
#       Input:
#           device - Device's name
#
#        Methods:
#           attrs - Return the attributes for the Stat Zone to be used to update the HA Zone entity
#           time_left - The time left until the phone goes into a Stat Zone
#           update_dist(dist) - Add the 'dist' to the moved_dist
#
#####################################################################
class iCloud3StationaryZone(iCloud3Zone):

    def __init__(self, Device):
        self.zone       = f"{Device.devicename}_stationary"
        self.Device     = Device
        self.devicename = Device.devicename

        self.base_latitude  = Gb.stat_zone_base_latitude
        self.base_longitude = Gb.stat_zone_base_longitude

        statzone_data = {LATITUDE: self.base_latitude,
                         LONGITUDE: self.base_longitude,
                         RADIUS: 1, PASSIVE: True}

        # Initialize Zone with location
        super().__init__(self.zone, statzone_data)
        Gb.Zones.append(self)
        Gb.Zones_by_zone[self.zone] = self

        # Initialize tracking movement fields
        self.inzone_interval_secs      = Gb.stat_zone_inzone_interval_secs
        self.still_time                = Gb.stat_zone_still_time_secs
        self.stat_zone_half_still_time = Gb.stat_zone_still_time_secs / 2

        self.timer      = 0
        self.moved_dist = 0

        # Initialize Stat Zone size based on Home zone size
        home_zone_radius_km        = Gb.HomeZone.radius_km
        self.min_dist_from_zone_km = round(home_zone_radius_km * 2, 2)
        self.dist_move_limit       = round(home_zone_radius_km * 1.5, 2)
        self.inzone_radius_km      = round(home_zone_radius_km * 2, 2)
        self.inzone_radius         = home_zone_radius_km * 2000
        if self.inzone_radius_km   > .1:  self.inzone_radius_km = .1
        if self.inzone_radius      > 100: self.inzone_radius    = 100
        self.radius                = 1

    #---------------------------------------------------------------------
        # dist = Gb.HomeZone.distance_km(self.base_latitude, self.base_longitude)

        # event_msg =(f"Set Initial Stationary Zone Location > {self.zone} > "
        #             f"GPS-{format_gps(self.base_latitude, self.base_longitude, 0)}, "
        #             f"Radius-{self.radius}m, DistFromHome-{dist}km, "
        #             f"MinDistFromZone-{format_dist(self.min_dist_from_zone_km)}, "
        #             f"DistMoveLimit-{format_dist_m(self.dist_move_limit)}")
        # Gb.EvLog.post_event(event_msg)

        first_initial = self.devicename[0]
        icon_name     = first_initial
        for mdi_name, mdi_letter in MDI_NAME_LETTERS.items():
            if first_initial not in mdi_letter:
                icon_name = (f"{first_initial}-{mdi_name}")
                MDI_NAME_LETTERS[mdi_name] += first_initial
                break

        #base_attrs is used to move the stationary zone back to it's base
        self.base_attrs = {}
        self.base_attrs[NAME]          = self.zone
        self.base_attrs[ICON]          = f"mdi:alpha-{icon_name}"
        self.base_attrs[FRIENDLY_NAME] = (f"{self.devicename}_{STATIONARY}").title()
        self.base_attrs[LATITUDE]      = self.base_latitude
        self.base_attrs[LONGITUDE]     = self.base_longitude
        self.base_attrs[RADIUS]        = 1
        self.base_attrs[PASSIVE]       = True

        #away_attrs is used to move the stationary zone back to it's base
        self.away_attrs = self.base_attrs.copy()
        self.away_attrs[RADIUS]        = self.inzone_radius
        self.away_attrs[PASSIVE]       = False

        # _trace(f"{self.__dict__}")

    def __repr__(self):
        return (f"<StatZone: {self.zone}>")

    #---------------------------------------------------------------------
    # Return True if the device is in the Stationary Zone
    @property
    def inzone(self):
        return (self.radius == 100)

    # Return True if the device is not in the Stationary Zone
    @property
    def not_inzone(self):
        return (self.radius == 1)

    # Return the seconds left before the phone should be moved into a Stationary Zone
    @property
    def timer_left(self):
        if self.timer > 0:
            return (self.timer - time_now_secs())
        else:
            return HIGH_INTEGER

    # Return True if the timer has expired
    @property
    def timer_expired(self):
        return (self.timer_left <= 0)

    # Return the attributes for the Stat Zone to be used to update the HA Zone entity
    @property
    def attrs(self):
        _attrs = self.base_attrs
        _attrs[LATITUDE]  = self.latitude
        _attrs[LONGITUDE] = self.longitude
        _attrs[RADIUS]    = self.radius

        return _attrs



#####################################################################
#
#   Methods to move the Stationary Zone to it's new location or back
#   to the base location based on the Update Control value.
#
#####################################################################
    def update_stationary_zone_location(self):

        try:
            #_trace(f"{self.zone=} {self.Device.devicename=} {self.Device.stationary_zone_update_control=} ")
            if self.Device.stationary_zone_update_control == STAT_ZONE_NO_UPDATE:
                return

            elif self.Device.stationary_zone_update_control == STAT_ZONE_MOVE_TO_BASE:
                self.move_stationary_zone_to_base_location()

            elif self.Device.stationary_zone_update_control == STAT_ZONE_MOVE_DEVICE_INTO:
                self.move_stationary_zone_to_new_location()

            self.Device.stationary_zone_update_control = STAT_ZONE_NO_UPDATE
            return

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def move_stationary_zone_to_new_location(self):
        try:
            latitude  = self.Device.loc_data_latitude
            longitude = self.Device.loc_data_longitude

            #Make sure stationary zone is not being moved to another zone's location unless it a
            #Stationary Zone
            for Zone in Gb.Zones:
                if Zone.radius <= 1:
                    continue

                zone_dist_km = Zone.distance_km(latitude, longitude)

                if is_statzone(Zone.zone) is False:
                    if zone_dist_km < self.min_dist_from_zone_km:   #self.inzone_radius:
                        event_msg =(f"Move into stationary zone cancelled > "
                                    f"Too close to zone-{Zone.display_as}, "
                                    f"DistFmZone-{format_dist(zone_dist_km)}")
                        post_event(self.devicename, event_msg)
                        self.timer = Gb.this_update_secs + self.still_time

                        return False

            # Set new location, it will be updated when Device's attributes are updated in main routine
            self.latitude              = latitude
            self.longitude             = longitude
            self.away_attrs[LATITUDE]  = latitude
            self.away_attrs[LONGITUDE] = longitude
            still_since_secs           = self.timer - self.still_time
            self.moved_dist            = 0
            self.timer                 = 0
            self.radius                = self.inzone_radius

            Gb.hass.states.set(f"zone.{self.zone}", "zoning", self.away_attrs, force_update=True)

            #Set Stationary Zone at new location
            self.Device.loc_data_zone      = self.zone
            self.Device.into_zone_datetime = datetime_now()

            # trace_device_attributes(Device.stationary_zonename, "SET.STAT.ZONE", "SetStatZone", attrs)

            event_msg =(f"Setting Stationary Zone Location > "
                        f"StationarySince-{format_time_age(still_since_secs)}, "
                        f"GPS-{format_gps(latitude, longitude, self.radius)}")
            post_event(self.devicename, event_msg)

            return True

        except Exception as err:
            log_exception(err)

            return False

#--------------------------------------------------------------------
    def move_stationary_zone_to_base_location(self):
        ''' Move stationary zone back to base location '''
        # Set new location, it will be updated when Device's attributes are updated in main routine

        self.clear_timer
        self.radius = 1

        Gb.hass.states.set(f"zone.{self.zone}", "zoning", self.base_attrs, force_update=True)

        event_msg =(f"Reset Stationary Zone Location > {self.zone}, "
                    f"Moved back to Base Location-{format_gps(self.base_latitude, self.base_longitude, 1)}")
        post_event(self.devicename, event_msg)

        return True

#--------------------------------------------------------------------
    @property
    def reset_timer_time(self):
        '''
        Set the Stationary Zone timer expiration time
        '''
        self.moved_dist = 0
        self.timer      = Gb.this_update_secs + self.still_time

    @property
    def clear_timer(self):
        '''
        Clear the Stationary Zone timer
        '''
        self.moved_dist = 0
        self.timer      = 0

#####################################################################
#
#   Methods to update the Stationary Zone's distance moved and to
#   determine if the update should be reset or to move the device into
#   it's Stationary Zone
#
#####################################################################
    def update_distance_moved(self, distance):
        self.moved_dist += distance

        if Gb.evlog_trk_monitors_flag:
            log_msg =  (f"Stat Zone Movement > "
                        f"TotalMoved-{format_dist(self.Device.StatZone.moved_dist)}, "
                        f"UnderMoveLimit-{self.Device.StatZone.moved_dist <= self.Device.StatZone.dist_move_limit}, "
                        f"Timer-{secs_to_time(self.Device.StatZone.timer)}, "
                        f"TimerLeft- {self.Device.StatZone.timer_left} secs, "
                        f"TimerExpired-{self.Device.StatZone.timer_expired}")
            post_monitor_msg(self.Device.devicename, log_msg)

        return self.moved_dist
