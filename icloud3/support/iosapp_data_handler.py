

from ..global_variables  import GlobalVariables as Gb
from ..const             import (NOT_SET, HIGH_INTEGER, NUMERIC, IOS_TRIGGERS_EXIT,
                                EVLOG_NOTICE, UTC_TIME, CRLF_DOT,
                                STATIONARY, STAT_ZONE_MOVE_DEVICE_INTO, STAT_ZONE_MOVE_TO_BASE,
                                STAT_ZONE_NO_UPDATE, ENTER_ZONE, EXIT_ZONE, NOT_HOME, __init__,
                                TRIGGER, LATITUDE, LONGITUDE, TRIGGER,
                                GPS_ACCURACY, VERT_ACCURACY, BATTERY_LEVEL, ALTITUDE, PASS_THRU_ZONE_INTERVAL_SECS, )

from ..helpers.base      import (instr, is_statzone,
                                post_event, post_error_msg, post_log_info_msg, post_monitor_msg,
                                log_exception, _trace, _traceha, )
from ..helpers.time      import (secs_to_time, secs_since, datetime_to_secs, time_now_secs, )
from ..helpers.format    import (format_gps, format_time_age, format_age, )
from ..helpers.entity_io import (get_state, get_attributes, get_last_changed_time, extract_attr_value, )
from ..support           import iosapp_interface as iosapp_interface



#########################################################
#
#   Check the iosapp device_tracker entity and last_update_trigger entity to
#   see if anything has changed and the icloud3 device_tracker entity should be
#   updated with the new location information.
#
#########################################################
def check_iosapp_state_trigger_change(Device):
    try:
        Device.iosapp_data_updated_flag = False
        Device.iosapp_data_change_reason = ''
        Device.iosapp_data_reject_reason = ''

        iosapp_data_state_not_set_flag = (Device.iosapp_data_state == NOT_SET)

        # GET DEVICE TRACKER STATE DATA
        entity_id = Device.iosapp_device_trkr_entity_id
        iosapp_data_state_secs = get_last_changed_time(entity_id)

        # Get the new state data if the last_changed_time has changed
        if (iosapp_data_state_secs > Device.iosapp_data_state_secs
                or iosapp_data_state_not_set_flag):
            Device.iosapp_data_state_secs = iosapp_data_state_secs
            Device.iosapp_data_state_time = secs_to_time(iosapp_data_state_secs)

            if get_iosapp_device_trkr_entity_attrs(Device) is False:
                Device.iosapp_data_reject_reason = 'Error reading iOSApp entity'
                if Gb.start_icloud3_initial_load_flag is False:
                    Device.iosapp_data_invalid_error_cnt += 1
                return

        # GET LAST CHANGED TRIGGER DATA
        entity_id = Device.iosapp_sensor_trigger_entity_id
        iosapp_data_trigger_secs        = get_last_changed_time(entity_id)
        iosapp_data_trigger             = get_state(entity_id)
        iosapp_data_trigger_change_flag = (Device.iosapp_data_trigger != iosapp_data_trigger)


        if Device.iosapp_data_state_secs > iosapp_data_trigger_secs:
            Device.iosapp_data_secs = Device.iosapp_data_state_secs
        else:
            Device.iosapp_data_secs = iosapp_data_trigger_secs
        Device.iosapp_data_time = secs_to_time(Device.iosapp_data_secs)

        dist_home = Gb.HomeZone.distance_m(Device.iosapp_data_latitude, Device.iosapp_data_longitude)

        # If enter/exit zone, save zone and enter/exit time
                # and Device.iosapp_data_state != NOT_HOME
        if (Device.iosapp_data_trigger == EXIT_ZONE
                and Device.is_inzone_iosapp_state
                and Device.iosapp_data_state_secs >= Device.iosapp_zone_exit_secs):
            Device.iosapp_zone_exit_secs = Device.iosapp_data_state_secs
            Device.iosapp_zone_exit_time = Device.iosapp_data_state_time
            Device.iosapp_zone_exit_zone = Device.iosapp_zone_enter_zone

                # and Device.iosapp_data_state != NOT_HOME
        if (Device.iosapp_data_trigger == ENTER_ZONE
                and Device.is_inzone_iosapp_state
                and Device.iosapp_data_state_secs >= Device.iosapp_zone_enter_secs):
            Device.iosapp_zone_enter_secs = Device.iosapp_data_state_secs
            Device.iosapp_zone_enter_time = Device.iosapp_data_state_time
            Device.iosapp_zone_enter_zone = Device.iosapp_data_state

        # Get the new trigger data if the last_changed_time has changed
        if (iosapp_data_trigger_secs > Device.iosapp_data_trigger_secs
                or iosapp_data_trigger_change_flag
                or iosapp_data_state_not_set_flag):
            Device.iosapp_data_trigger_secs = iosapp_data_trigger_secs
            Device.iosapp_data_trigger_time = secs_to_time(iosapp_data_state_secs)
            Device.iosapp_data_trigger      = iosapp_data_trigger


        # dist_home = Gb.HomeZone.distance_m(Device.iosapp_data_latitude, Device.iosapp_data_longitude)
        iosapp_msg =(f"iOSApp Monitor > "
                    f"ThisTrigger-{Device.iosapp_data_trigger}@{Device.iosapp_data_trigger_time} (%tage), "
                    f"LastTrigger-{Device.sensors[TRIGGER]}, "
                    f"ThisState-{Device.iosapp_data_state}@{Device.iosapp_data_state_time} (%sage), "
                    f"GPS-{format_gps(Device.iosapp_data_latitude, Device.iosapp_data_longitude, Device.iosapp_data_gps_accuracy)}, "
                    f"LastLocTime-{Device.loc_data_time}, "
                    f"TriggerChanged-{iosapp_data_trigger_change_flag},")

        if Device.iosapp_zone_enter_zone:
            iosapp_msg +=(f", LastZoneEnter-{Device.iosapp_zone_enter_zone}@"
                            f"{Device.iosapp_zone_enter_time}")
        if Device.iosapp_zone_exit_zone:
            iosapp_msg +=(f", LastZoneExit-{Device.iosapp_zone_exit_zone}@"
                            f"{Device.iosapp_zone_exit_time}")

        if iosapp_data_state_not_set_flag:
            Device.iosapp_data_change_reason = "iOSApp Initial Locate"
            Device.iosapp_data_trigger       = "iOSApp Initial Locate"

        elif (is_statzone(Device.iosapp_data_state)
                and Device.iosapp_data_latitude  == Device.StatZone.base_latitude
                and Device.iosapp_data_longitude == Device.StatZone.base_longitude):
            Device.iosapp_data_reject_reason = "Stat Zone Base Location"

        # Reject State and trigger changes older than the current data
        elif (Device.iosapp_data_state_secs <= Device.last_attrs_update_loc_secs
                and Device.iosapp_data_trigger_secs <= Device.last_attrs_update_loc_secs):
            Device.iosapp_data_reject_reason = "Before Last Update"

        # Check just entered non-tracked zone and delay entry in case just passing thru
        elif (Device.is_inzone_iosapp_state
                and Device.isnot_inzone
                and Device.iosapp_data_state not in Device.DeviceFmZones_by_zone
                and secs_since(Device.iosapp_data_state_secs) < 60
                and Device.passthru_zone_expire_secs == 0):
            Device.iosapp_data_reject_reason = "Pass through zone delay"
            Device.passthru_zone_expire_secs = Gb.this_update_secs + PASS_THRU_ZONE_INTERVAL_SECS

        # RegionExit trigger and the trigger changed from last poll overrules trigger change time
                # and Device.iosapp_data_state == NOT_HOME):
        elif (Device.iosapp_data_trigger == EXIT_ZONE
                and Device.isnot_inzone_iosapp_state):
            Device.iosapp_data_reject_reason = "Exit Zone and not in a zone"

        # RegionExit trigger and the trigger changed from last poll overrules trigger change time
        elif (Device.iosapp_data_trigger == EXIT_ZONE
                and iosapp_data_trigger_change_flag):
            Zone = Gb.Zones_by_zone.get(Device.iosapp_zone_exit_zone)
            zone_display_name = Gb.Zones_by_zone[Device.iosapp_zone_exit_zone] if Zone else 'Unidentified Zone'
            Device.iosapp_data_change_reason = (f"{EXIT_ZONE} > {zone_display_name}")
                                                # f"{Device.iosapp_zone_exit_time}")

        # RegionExit trigger overrules old location, gps accuracy and other checks
        elif (Device.iosapp_data_trigger == EXIT_ZONE
                and Device.iosapp_data_trigger_secs > Device.located_secs_plus_5):
            Zone = Gb.Zones_by_zone.get(Device.iosapp_zone_exit_zone)
            zone_display_name = Gb.Zones_by_zone[Device.iosapp_zone_exit_zone] if Zone else 'Unidentified Zone'
            Device.iosapp_data_change_reason = (f"{EXIT_ZONE} > {zone_display_name}")
                                                # f"{Device.iosapp_zone_exit_time}")

        # RegionEnter trigger and the trigger changed from last poll overrules trigger change time
        elif (Device.iosapp_data_trigger == ENTER_ZONE
                and iosapp_data_trigger_change_flag):
            Zone = Gb.Zones_by_zone.get(Device.iosapp_zone_enter_zone)
            zone_display_name = (Gb.Zones_by_zone.get(Device.iosapp_zone_exit_zone)
                                    if Zone else Device.iosapp_zone_enter_zone)
            Device.iosapp_data_change_reason = (f"{ENTER_ZONE}@{Device.iosapp_data_trigger_time} > "
                                                f"{zone_display_name}")

        elif (Device.iosapp_data_trigger not in [ENTER_ZONE, EXIT_ZONE]
                and Device.iosapp_data_trigger_secs > Device.located_secs_plus_5
                and Device.iosapp_data_gps_accuracy > Gb.gps_accuracy_threshold):
            Device.iosapp_data_reject_reason = (f"Poor GPS Accuracy-{Device.iosapp_data_gps_accuracy}m "
                                f"(#{Device.old_loc_poor_gps_cnt})")

        if (Device.iosapp_data_reject_reason != "Before Last Update"
                and Device.passthru_zone_expire_secs > 0):
            _trace(Device.devicename,f"PASSTHRUTEST > "
                f"TriggerTime-{Device.iosapp_data_trigger_time}, "
                f"Trigger-{Device.iosapp_data_trigger}, "
                f"inZoneiOSAppState-{Device.is_inzone_iosapp_state}, DevAway-{Device.isnot_inzone}, "
                f"NotTfZ-{Device.iosapp_data_state not in Device.DeviceFmZones_by_zone}, "
                f"secsSinceiosappStateChg-{secs_since(Device.iosapp_data_state_secs)}, "
                f"rejReason-{Device.iosapp_data_reject_reason}, "
                f"chgReason-{Device.iosapp_data_change_reason}, "
                f"passThruExpireTime={secs_to_time(Device.passthru_zone_expire_secs)}/"
                f"{Device.passthru_zone_expire_secs}")


        # Discard StatZone entered if StatZone was created in the last 15-secs
        if (Device.iosapp_data_trigger == ENTER_ZONE
                and is_statzone(Device.iosapp_data_state)
                and Device.last_attrs_update_loc_zone == STATIONARY
                and secs_since(Device.loc_data_secs <= 15)):
            Device.iosapp_data_reject_reason = "Enter into StatZone just created"

        # Discard if already in the zone
        elif (Device.iosapp_data_trigger == ENTER_ZONE
                and Device.iosapp_data_state == Device.last_attrs_update_loc_zone):
            Device.iosapp_data_reject_reason = "Enter Zone and already in zone"

        #trigger time is after last locate
        elif Device.iosapp_data_trigger_secs > Device.located_secs_plus_5:
            Device.count_trigger_changed += 1
            Device.iosapp_data_change_reason = (f"Trigger Change-{Device.iosapp_data_trigger}@{Device.iosapp_data_trigger_time} ")
                                        # f"> {secs_to_time(Device.located_secs_plus_5)}")

        # TODO 8/26 <<
        # No update needed if no location changes
        elif (Device.iosapp_data_state == Device.last_attrs_update_loc_zone
                and Device.iosapp_data_latitude == Device.loc_data_latitude
                and Device.iosapp_data_longitude == Device.loc_data_longitude):
            Device.iosapp_data_reject_reason = "Location did not change"
        # TODO 8/26 >>

        #iOSAPP location changed and State changed more than 5-secs after last locate
        elif Device.iosapp_data_state_secs > Device.located_secs_plus_5:
            Device.iosapp_data_change_reason = (f"iOSApp Loc Update@{Device.iosapp_data_state_time} ")
                                        #f"{Device.iosapp_data_trigger_secs}")
            Device.count_state_changed += 1
            Device.iosapp_data_trigger = "State Loc Change"

        #Prevent duplicate update if State & Trigger changed at the same time
        #and state change was handled on last cycle
        elif (Device.iosapp_data_trigger_secs == Device.iosapp_data_state_secs
                or Device.iosapp_data_trigger_secs <= Device.located_secs_plus_5):
            Device.iosapp_data_reject_reason = "Already Processed"

        #Bypass if trigger contains ic3 date stamp suffix (@hhmmss)
        elif instr(Device.iosapp_data_trigger, '@'):
            Device.iosapp_data_reject_reason = "Trigger Already Processed"

        elif Device.iosapp_data_trigger_secs <= Device.located_secs_plus_5:
            Device.iosapp_data_reject_reason = "Trigger Before Last Locate"

        else:
            Device.iosapp_data_reject_reason = "Failed Update Tests"

        # **changed 4/28# Device.iosapp_data_updated_flag = (Device.iosapp_data_change_reason != "")
        Device.iosapp_data_updated_flag = (Device.iosapp_data_reject_reason == "")
        iosapp_msg += (f", WillUpdate-{Device.iosapp_data_updated_flag}")

        if Device.iosapp_data_change_reason:
            iosapp_msg += (f" ({Device.iosapp_data_change_reason})")
        if Device.iosapp_data_reject_reason:
            iosapp_msg += (f" ({Device.iosapp_data_reject_reason})")

        #Show iOS App monitor every half hour
        if Gb.this_update_time.endswith(':00:00') or Gb.this_update_time.endswith(':30:00'):
            Device.last_iosapp_msg = ""

        if (iosapp_msg != Device.last_iosapp_msg):
            Device.last_iosapp_msg = iosapp_msg

            iosapp_msg = iosapp_msg.replace("%tage", format_age(secs_since(Device.iosapp_data_trigger_secs)))
            iosapp_msg = iosapp_msg.replace("%sage", format_age(secs_since(Device.iosapp_data_state_secs)))
            post_monitor_msg(Device.devicename, iosapp_msg)

        return

    except Exception as err:
        log_exception(err)
        return

#########################################################
#
#   Update the device on a state or trigger change was recieved from the ios app
#     ●►●◄►●▬▲▼◀►►●◀ oPhone=►▶
#
#########################################################
# If this Device is entering a zone also assigned to another device. The ios app
# will move issue a Region Entered trigger and the state is the other devicename's
# stat zone name. Create this device's stat zone at the current location to get the
# zone tables in sync. Must do this before processing the state/trigger change or
# this devicename will use this trigger to start a timer rather than moving it ineo
# the stat zone.
def check_enter_exit_stationary_zone(Device):
    try:


        Device.stationary_zone_update_control = STAT_ZONE_NO_UPDATE

        if (Device.iosapp_data_trigger == ENTER_ZONE):
            if is_statzone(Device.iosapp_data_state):
                # Check to see if entering another device's stationary zone (iosapp_data_state).
                # If so, change this Device's ios_state and
                if (instr(Device.iosapp_data_state, Device.devicename) is False
                        and Device.isnot_inzone_stationary):
                    event_msg =(f"Stationary Zone Entered > iOS App used another device's "
                                f"Stationary Zone, changed {Device.iosapp_data_state } to "
                                f"{Device.stationary_zonename}")
                    post_event(Device.devicename, event_msg)

                    Device.iosapp_data_state = Device.stationary_zonename

                Device.stationary_zone_update_control = STAT_ZONE_MOVE_DEVICE_INTO

        elif (Device.iosapp_data_trigger in IOS_TRIGGERS_EXIT):
            if Device.StatZone.inzone:
                Device.stationary_zone_update_control = STAT_ZONE_MOVE_TO_BASE

        Device.StatZone.update_stationary_zone_location()

        if is_statzone(Device.iosapp_data_state):
            Device.iosapp_data_state = STATIONARY

    except Exception as err:
        log_exception(err)

#########################################################
#
#  Check the state of the iosapp to see if it is alive on regular intervals by
#  sending a location request at regular intervals. It will be considered dead/inactive
#  if there is no response with it's location.
#
#########################################################
def check_if_iosapp_is_alive(Device):
    try:
        if Device.iosapp_monitor_flag is False:
            return

        # Send a location request f the iosapp data is more than 1-hour old
        if secs_since(Device.iosapp_data_secs) > 3600:
            # If a request was sent, wait 10-minutes before sending another one
            if (Device.iosapp_request_loc_sent_flag
                    and secs_since(Device.iosapp_request_loc_sent_secs) > 600):
                Device.iosapp_request_loc_sent_flag = False

            iosapp_interface.request_location(Device)

        return

        # Request the iosapp location every 6 hours
        if (Gb.this_update_time in ['23:45:00', '05:45:00', '11:45:00', '17:45:00']
                and secs_since(Device.iosapp_data_state_secs) > 20700
                and secs_since(Device.iosapp_data_trigger_secs) > 20700):
            pass

        # No activity, display Alert msg in Event Log
        if (Gb.this_update_time in ['00:00:00', '06:00:00', '12:00:00', '18:00:00']
                and secs_since(Device.iosapp_data_state_secs) > 21600
                and secs_since(Device.iosapp_data_trigger_secs) > 21600):
            event_msg =(f"{EVLOG_NOTICE}iOS App Alert > No iOS App updates for more than 6 hours > "
                        f"Device-{Device.iosapp_device_trkr_entity_id_fname}, "
                        f"LastTrigger-{Device.iosapp_data_trigger}@{format_time_age(Device.iosapp_data_trigger_secs)}, "
                        f"LastState-{Device.iosapp_data_state}@{format_time_age(Device.iosapp_data_state_secs)})")
            # self._save_event_halog_info(devicename, event_msg)
            event_msg =(f"Last iOS App update from {Device.iosapp_device_trkr_entity_id_fname}"
                        f"—{format_time_age(Device.iosapp_data_trigger_secs)}")
            Device.display_info_msg( event_msg)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def get_iosapp_device_trkr_entity_attrs(Device):
    '''
    Return the state and attributes of the ios app device tracker.
    The ic3 device tracker state and attributes are returned if
    the ios app data is not available or an error occurs.
    '''
    try:
        entity_id = Device.iosapp_device_trkr_entity_id
        Device.iosapp_data_state = get_state(entity_id)

        iosapp_attrs = get_attributes(entity_id)
        if iosapp_attrs == {}:
            Device.iosapp_data_invalid_error_cnt += 1
            return False

        elif LATITUDE not in iosapp_attrs:
            Device.iosapp_data_invalid_error_cnt += 1
            return False

        elif LATITUDE in iosapp_attrs:
            Device.iosapp_data_invalid_error_cnt = 0
            Device.iosapp_data_latitude          = extract_attr_value(iosapp_attrs, LATITUDE, NUMERIC)
            Device.iosapp_data_longitude         = extract_attr_value(iosapp_attrs, LONGITUDE, NUMERIC)
            Device.iosapp_data_gps_accuracy      = extract_attr_value(iosapp_attrs, GPS_ACCURACY, NUMERIC)
            Device.iosapp_data_battery_level     = extract_attr_value(iosapp_attrs, BATTERY_LEVEL, NUMERIC)
            Device.iosapp_data_vertical_accuracy = extract_attr_value(iosapp_attrs, VERT_ACCURACY, NUMERIC)
            Device.iosapp_data_altitude          = extract_attr_value(iosapp_attrs, ALTITUDE, NUMERIC)

    except Exception as err:
        log_exception(err)
        return False

    return True

#--------------------------------------------------------------------
def _get_entity_last_changed_time(entity_id):
    """
    Get entity's last changed time attribute
    Last changed time format '2019-09-09 14:02:45.12345+00:00' (utc value)
    Return time, seconds, timestamp
    """

    try:
        timestamp_utc = str(Gb.hass.states.get(entity_id).last_changed)
        timestamp_utc = timestamp_utc.split(".")[0]
        secs     = datetime_to_secs(timestamp_utc, UTC_TIME)
        return secs

    except Exception as err:
        log_exception(err)
        return HIGH_INTEGER
