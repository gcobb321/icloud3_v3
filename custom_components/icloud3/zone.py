#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from .global_variables  import GlobalVariables as Gb
from .const             import (HOME, STATIONARY, HIGH_INTEGER,
                                ZONE, TITLE, FNAME,
                                STAT_ZONE_NO_UPDATE, STAT_ZONE_MOVE_DEVICE_INTO, STAT_ZONE_MOVE_TO_BASE,
                                NAME, STATIONARY_FNAME, ID,
                                FRIENDLY_NAME, ICON,
                                LATITUDE, LONGITUDE, RADIUS, PASSIVE,
                                )

from .helpers.common    import (instr, is_statzone, format_gps, )
from .helpers.messaging import (post_event, post_error_msg, post_monitor_msg,
                                log_exception, log_rawdata,_trace, _traceha, )
from .helpers.time_util import (time_now_secs, datetime_now, secs_to_time,  format_time_age, )
from .helpers.dist_util import (calc_distance_m, calc_distance_km, format_dist_km, )

from   homeassistant.util.location import distance


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   GLOBAL SUPPORT FUNCTIONS & CONSTANTS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

MDI_NAME_LETTERS = {'circle-outline': '', 'box-outline': '', 'circle': '', 'box': ''}


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Zones Class Object
#       Set up the object for each Zone.
#
#       Input:
#           zone - Zone name
#           zone_data - A dictionary containing the Zone attributes
#                   (latitude, longitude. radius, passive, friendly name)
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_Zone(object):

    def __init__(self, zone, zone_data):
        self.zone = zone

        # zfname = Zone.fname
        # ztitle = Zone.title

        # if ztitle not in Gb.state_to_zone:
        #     Gb.state_to_zone[ztitle] = zone
        # ztitle_w = ztitle.replace(' ', '')
        # if ztitle_w not in Gb.state_to_zone:
        #     Gb.state_to_zone[ztitle_w] = zone


        if NAME in zone_data:
            ztitle = zone_data[NAME].title()
        else:
            ztitle = zone.title().replace("_S_","'s " ).replace("_", " ")
            ztitle = ztitle.replace(' Iphone', ' iPhone')
            ztitle = ztitle.replace(' Ipad', ' iPad')
            ztitle = ztitle.replace(' Ipod', ' iPod')

        # self.fname      = zone_data.get(FRIENDLY_NAME, ztitle)      # From zones_states attribute (zones config file)
        self.fname      = zone_data.get('original_name', ztitle)    # From entity_registry
        self.display_as = self.fname
        self.title      = ztitle
        self.name       = ztitle.replace(" ","").replace("'", "`")

        self.latitude   = zone_data.get(LATITUDE, 0)
        self.longitude  = zone_data.get(LONGITUDE, 0)
        self.passive    = zone_data.get(PASSIVE, True)
        self.radius_m   = round(zone_data.get(RADIUS, 100))

        self.entity_id  = zone_data.get(ID, zone.lower()).replace('sensor.', '')
        self.unique_id  = zone_data.get('unique_id', zone.lower())

        self.dist_time_history = []        #Entries are a list - [lat, long, distance, travel time]

        self.setup_zone_display_name()

        log_rawdata(f"Zone Data - <{zone} > ", zone_data, log_rawdata_flag=True)

        if zone == HOME:
            Gb.HomeZone = self

    def __repr__(self):
        return (f"<Zone: {self.zone}>")

    #---------------------------------------------------------------------
    def setup_zone_display_name(self):
        '''
        Set the zone display_as field using the config display_as format value
        '''
        if Gb.display_zone_format   == ZONE:  self.display_as = self.zone
        elif Gb.display_zone_format == FNAME: self.display_as = self.fname
        elif Gb.display_zone_format == NAME:  self.display_as = self.name
        elif Gb.display_zone_format == TITLE: self.display_as = self.title
        else: self.display_as = self.fname

        self.sensor_prefix = '' if self.zone == HOME else self.display_as

        # Used in entity_io to change ios app state value to the actual zone entity name for internal use
        Gb.state_to_zone[self.fname]      = self.zone
        Gb.state_to_zone[self.display_as] = self.zone

    #---------------------------------------------------------------------
    @property
    def gps(self):
        return (self.latitude, self.longitude)

    @property
    def latitude5(self):
        return round(self.latitude, 5)

    @property
    def longitude5(self):
        return round(self.longitude, 5)

    @property
    def radius_km(self):
        return round(self.radius_m/1000, 4)

    # Calculate distance in meters
    def distance_m(self, to_latitude, to_longitude):
        to_gps = (to_latitude, to_longitude)
        return calc_distance_m(self.gps, to_gps)

    # Calculate distance in kilometers
    def distance_km(self, to_latitude, to_longitude):
        to_gps = (to_latitude, to_longitude)
        return calc_distance_km(self.gps, to_gps)

    # Return the DeviceFmZone obj from the devicename and this zone
    @property
    def DeviceFmZone(self, Device):
        return (f"{Device.devicename}:{self.zone}")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_StationaryZone(iCloud3_Zone):

    def __init__(self, Device):
        self.zone       = f"{Device.devicename}_stationary"
        self.Device     = Device
        self.devicename = Device.devicename

        self.base_latitude  = Gb.stat_zone_base_latitude
        self.base_longitude = Gb.stat_zone_base_longitude

        statzone_data = {   LATITUDE: self.base_latitude,
                            LONGITUDE: self.base_longitude,
                            RADIUS: 1, PASSIVE: True}

        # Initialize Zone with location
        super().__init__(self.zone, statzone_data)
        Gb.Zones.append(self)
        Gb.Zones_by_zone[self.zone] = self

        self.set_stationary_zone_fname(Device)

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
        self.radius_m              = 1

    #---------------------------------------------------------------------
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
        # stat_zone_fname = (f"{self.devicename}_{STATIONARY}").title()
        # ztitle = stat_zone_fname.replace("_S_","'s " ).replace("_", " ")
        # ztitle = ztitle.replace(' Iphone', ' iPhone')
        # ztitle = ztitle.replace(' Ipad', ' iPad')
        # ztitle = ztitle.replace(' Ipod', ' iPod')
        self.base_attrs[FRIENDLY_NAME] = self.display_as
        self.base_attrs[LATITUDE]      = self.base_latitude
        self.base_attrs[LONGITUDE]     = self.base_longitude
        self.base_attrs[RADIUS]        = 1
        self.base_attrs[PASSIVE]       = True

        #away_attrs is used to move the stationary zone back to it's base
        self.away_attrs = self.base_attrs.copy()
        self.away_attrs[RADIUS]        = self.inzone_radius
        self.away_attrs[PASSIVE]       = False

    def __repr__(self):
        return (f"<StatZone: {self.zone}>")

    #---------------------------------------------------------------------
    def set_stationary_zone_fname(self, Device):
        '''
        Format the Stationary Zones friendly and display_as name

        This is done when the StatZone is initialized and in the
        start_ic3.set_global_variables_from_conf_parameters function that
        is run when iC3 is started and when the stat zone parameters are changed in config_flow
        '''
        if Device.stat_zone_fname != '':
            self.fname = self.display_as = Device.stat_zone_fname
        elif Gb.stat_zone_fname:
            self.fname = self.display_as = Gb.stat_zone_fname.replace('[name]', Device.fname[:3])
        else:
            self.fname = self.display_as = STATIONARY_FNAME

        Gb.zone_display_as[self.zone] = self.display_as

    #---------------------------------------------------------------------
    # Return True if the device is in the Stationary Zone
    @property
    def inzone(self):
        return (self.radius_m > 1)

    # Return True if the device is not in the Stationary Zone
    @property
    def not_inzone(self):
        return (self.radius_m == 1)

    # Return True if the device is not in the Stationary Zone
    @property
    def is_at_base(self):
        return (self.radius_m == 1)

    # Return the seconds left before the phone should be moved into a Stationary Zone
    @property
    def timer_left(self):
        if self.timer > 0:
            return (self.timer - time_now_secs())
        else:
            return HIGH_INTEGER

    # Return True if the timer has expired, False if not expired or not using Stat Zone
    @property
    def timer_expired(self):
        return (Gb.is_stat_zone_used and self.timer_left <= 0)

    @property
    def move_limit_exceeded(self):
        return (self.moved_dist > self.dist_move_limit)

    # Return the attributes for the Stat Zone to be used to update the HA Zone entity
    @property
    def attrs(self):
        _attrs = self.base_attrs
        _attrs[LATITUDE]  = self.latitude
        _attrs[LONGITUDE] = self.longitude
        _attrs[RADIUS]    = self.radius_m

        return _attrs



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Methods to move the Stationary Zone to it's new location or back
#   to the base location based on the Update Control value.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_stationary_zone_location(self):

        try:
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

        if self.Device.old_loc_poor_gps_cnt > 0:
            return

        try:
            latitude  = self.Device.loc_data_latitude
            longitude = self.Device.loc_data_longitude

            # Make sure stationary zone is not being moved to another zone's location unless it a
            # Stationary Zone
            for Zone in Gb.Zones:
                if Zone.radius_m <= 1:
                    continue

                zone_dist_km = Zone.distance_km(latitude, longitude)

                if is_statzone(Zone.zone) is False:
                    if zone_dist_km < self.min_dist_from_zone_km:   #self.inzone_radius:
                        event_msg =(f"Move into stationary zone cancelled > "
                                    f"Too close to zone-{Zone.display_as}, "
                                    f"DistFmZone-{format_dist_km(zone_dist_km)}")
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
            self.radius_m              = self.inzone_radius

            Gb.hass.states.async_set(f"zone.{self.zone}", 0, self.away_attrs, force_update=True)

            # Set Stationary Zone at new location
            self.Device.loc_data_zone      = self.zone
            self.Device.into_zone_datetime = datetime_now()

            event_msg =(f"Setting Stationary Zone Location > "
                        f"StationarySince-{format_time_age(still_since_secs)}, "
                        f"GPS-{format_gps(latitude, longitude, 0)}"
                        f"/r{self.radius_m}m")
                        # f"GPS-{format_gps(latitude, longitude, self.radius_m)}")
            post_event(self.devicename, event_msg)

            return True

        except Exception as err:
            log_exception(err)

            return False

# #--------------------------------------------------------------------
#     def set_stat_zone_state(self):
#             Gb.hass.states.set(f"zone.{self.zone}", "zoning", self.away_attrs, force_update=True)

#--------------------------------------------------------------------
    def move_stationary_zone_to_base_location(self):
        ''' Move stationary zone back to base location '''
        # Set new location, it will be updated when Device's attributes are updated in main routine

        self.clear_timer
        self.radius_m = 1

        self.base_attrs[LATITUDE] += 20
        Gb.hass.states.async_set(f"zone.{self.zone}", 0, self.base_attrs, force_update=True)

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

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Methods to update the Stationary Zone's distance moved and to
#   determine if the update should be reset or to move the device into
#   it's Stationary Zone
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_distance_moved(self, distance):
        self.moved_dist += distance

        if Gb.evlog_trk_monitors_flag:
            log_msg =  (f"Stat Zone Movement > "
                        f"TotalMoved-{format_dist_km(self.Device.StatZone.moved_dist)}, "
                        f"UnderMoveLimit-{self.Device.StatZone.moved_dist <= self.Device.StatZone.dist_move_limit}, "
                        f"Timer-{secs_to_time(self.Device.StatZone.timer)}, "
                        f"TimerLeft- {self.Device.StatZone.timer_left} secs, "
                        f"TimerExpired-{self.Device.StatZone.timer_expired}")
            post_monitor_msg(self.Device.devicename, log_msg)

        return self.moved_dist
