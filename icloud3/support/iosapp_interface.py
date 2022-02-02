

from ..global_variables  import GlobalVariables as Gb
from ..const             import (NOT_SET, HIGH_INTEGER, NUMERIC, IOS_TRIGGERS_EXIT,
                                EVLOG_NOTICE, UTC_TIME, CRLF_DOT,
                                STATIONARY, STAT_ZONE_MOVE_DEVICE_INTO, STAT_ZONE_MOVE_TO_BASE,
                                STAT_ZONE_NO_UPDATE, ENTER_ZONE, EXIT_ZONE, NOT_HOME, __init__,
                                TRIGGER, LATITUDE, LONGITUDE, TRIGGER,
                                GPS_ACCURACY, VERT_ACCURACY, BATTERY_LEVEL, ALTITUDE, )

from ..helpers.base      import (instr, is_statzone,
                                post_event, post_error_msg, post_log_info_msg, post_monitor_msg,
                                log_exception, _trace, _traceha, )
from ..helpers.time      import (secs_to_time, secs_since, datetime_to_secs, )
from ..helpers.format    import (format_gps, format_time_age, format_age, )
from ..helpers.entity_io import (get_state, get_attributes, get_last_changed_time, extract_attr_value, )
import json

#########################################################
#
#   Cycle through HA entity registry and get mobile_app device info that
#   can be monitored for the config_flow iosapp device selection list and
#   setting up the Device object
#
#########################################################
def get_entity_registry_mobile_app_devices():
    device_id_by_devicename      = {}
    devicename_by_device_id      = {}
    device_info_devicename       = {}
    last_updt_trig_by_devicename = {}
    notify_devicenames           = []

    try:
        with open(Gb.entity_registry_file, 'r') as f:
            entity_reg_data   = json.load(f)
            mobile_app_entities = [x for x in entity_reg_data['data']['entities']
                                        if x['platform'] == 'mobile_app']
            dev_trkr_entities = [x for x in mobile_app_entities
                                    if x['entity_id'].startswith('device_tracker')]
            last_updt_trigger_sensors = [x for x in mobile_app_entities
                                    if x['unique_id'].endswith('_last_update_trigger')]

            for dev_trkr_entity in dev_trkr_entities:
                devicename = dev_trkr_entity['entity_id'].replace('device_tracker.', '')
                device_id_by_devicename[devicename] = dev_trkr_entity['device_id']
                devicename_by_device_id[dev_trkr_entity['device_id']] = devicename
                device_info_devicename[devicename] = dev_trkr_entity['original_name']

            for sensor in last_updt_trigger_sensors:
                devicename = devicename_by_device_id[sensor['device_id']]
                last_updt_trig_by_devicename[devicename] = sensor['entity_id'].replace('sensor.', '')

            try:
                # Get notification ids for each device
                services = Gb.hass.services
                notify_services = dict(services.__dict__)['_services']['notify']

                for notify_service in notify_services:
                    if notify_service.startswith("mobile_app_"):
                        notify_devicenames.append(notify_service)

            except:
                pass

    except Exception as err:
        log_exception(err)

    return device_id_by_devicename, devicename_by_device_id, \
                device_info_devicename, last_updt_trig_by_devicename, \
                notify_devicenames


#########################################################
#
#   Send a message to the iosapp
#
#########################################################
def send_message_to_device(Device, service_data):
    '''
    Send a message to the device. An example message is:
        service_data = {
            "title": "iCloud3/iOSApp Zone Action Needed",
            "message": "The iCloud3 Stationary Zone may "\
                "not be loaded in the iOSApp. Force close "\
                "the iOSApp from the iOS App Switcher. "\
                "Then restart the iOSApp to reload the HA zones. "\
                f"Distance-{dist_fm_zone_m} m, "
                f"StatZoneTestDist-{zone_radius * 2} m",
            "data": {"subtitle": "Stationary Zone Exit "\
                "Trigger was not received"}}
    '''
    try:
        if Device.iosapp_notify_devices == []:
            return

        if service_data.get('message') != "request_location_update":
            evlog_msg = (f"{EVLOG_NOTICE}Sending Message to Device > "
                        f"Message-{service_data.get('message')}")
            post_log_info_msg(Device.devicename, evlog_msg)

        notify_devicename = NOT_SET
        for notify_devicename in Device.iosapp_notify_devices:
            Gb.hass.services.call("notify", notify_devicename, service_data)

        #Gb.hass.async_create_task(
        #    Gb.hass.services.async_call('notify', entity_id, service_data))

        return True

    except Exception as err:
        event_msg =(f"iCloud3 Error > An error occurred sending a message to device "
                    f"{notify_devicename} via notify.{notify_devicename} service. "
                    f"{CRLF_DOT}Message-{str(service_data)}")
        if instr(err, "notify/none"):
            event_msg += (f"{CRLF_DOT}The devicename can not be found")
        else:
            event_msg += f"{CRLF_DOT}Error-{err}"
        post_error_msg(Device.devicename, event_msg)

    return False

#########################################################
#
#   Using the iosapp tracking method or iCloud is disabled
#   so trigger the osapp to send a
#   location transaction
#
#########################################################
def request_location(Device):
    '''
    Send location request to phone. Check to see if one has been sent but not responded to
    and, if true, set interval based on the retry count.
    '''
    devicename = Device.devicename

    try:
        #Save initial sent time if not sent before, otherwise increase retry cnt and
        #set new interval time
        if Device.iosapp_request_loc_sent_flag is False:
            Device.iosapp_request_loc_sent_secs = Gb.this_update_secs
            Device.iosapp_request_loc_retry_cnt = 0
        else:
            Device.iosapp_request_loc_retry_cnt += 1

        event_msg =(f"Requesting iOSApp Location (#{Device.iosapp_request_loc_retry_cnt}) > ")

        if Device.loc_data_age > 60480:
            event_msg += "iOSApp Initial Locate"
        else:
            event_msg += (f"LastLocTime-{Device.loc_data_time_age}")

        if Device.iosapp_request_loc_retry_cnt > 0:
            event_msg += (f", LastRequested-{format_time_age(Device.iosapp_request_loc_sent_secs)}")

            if Device.iosapp_request_loc_retry_cnt > 10:
                event_msg += ", May be offline/asleep"

        Device.iosapp_request_loc_sent_flag = True
        Device.iosapp_request_loc_cnt += 1

        message = {"message": "request_location_update"}
        return_code = send_message_to_device(Device, message)

        #Gb.hass.async_create_task(
        #    Gb.hass.services.async_call('notify',  entity_id, service_data))

        post_event(devicename, event_msg)

        if return_code:
            Device.display_info_msg(event_msg)
        else:
            event_msg = f"{EVLOG_NOTICE}{event_msg} > Failed to send message"
            post_event(devicename, event_msg)

    except Exception as err:
        log_exception(err)
        error_msg = (f"iCloud3 Error > An error occurred sending a location request > "
                    f"Device-{Device.fname_devicename}, Error-{err}")
        post_error_msg(devicename, error_msg)
