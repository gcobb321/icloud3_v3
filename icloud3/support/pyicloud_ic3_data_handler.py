
from ..global_variables import GlobalVariables as Gb
from ..const            import (NOT_SET, HOME, HIGH_INTEGER, EVLOG_ALERT, EVLOG_ERROR, CRLF, CRLF_DOT,
                                HHMMSS_ZERO, RARROW, UNKNOWN,
                                ICLOUD, IOSAPP, FAMSHR_FNAME, FMF_FNAME,
                                STORAGE_DIR,

                                FAMSHR_FMF, ICLOUD_HORIZONTAL_ACCURACY,
                                LOCATION, LATITUDE, AUTHENTICATED, CONF_NAME, )

from ..support          import start_ic3 as start_ic3
from ..support          import pyicloud_ic3_interface

from ..helpers.base     import (instr, is_statzone,
                                post_event, post_error_msg, post_log_info_msg, post_startup_event, post_monitor_msg,
                                log_exception, log_rawdata, internal_error_msg2, _trace, _traceha, )
from ..helpers.time     import (time_now_secs, secs_to_time, secs_to_datetime, )
from ..helpers.format   import (format_gps, format_time_age, format_age, )
from ..helpers.entity_io import (get_state, get_attributes, get_last_changed_time, extract_attr_value, )

from .pyicloud_ic3  import PyiCloudService
from .pyicloud_ic3  import (
            PyiCloudFailedLoginException,
            PyiCloudNoDevicesException,
            PyiCloudAPIResponseException,
            PyiCloud2SARequiredException,
            )


import os
import time
import traceback
from re import match


#########################################################
#
#   Get iCloud device & location info when using the
#
#########################################################
def request_icloud_data_update(Device):
    '''
    Extract the data needed to determine location, direction, interval,
    etc. from the iCloud data set.

    Sample data set is:
        {'isOld': False, 'isInaccurate': False, 'altitude': 0.0, 'positionType': 'Wifi',
        'latitude': 27.72690098883266, 'floorLevel': 0, 'horizontalAccuracy': 65.0,
        'locationType': '', 'timeStamp': 1587306847548, 'locationFinished': True,
        'verticalAccuracy': 0.0, 'longitude': -80.3905776599289}
    '''
    devicename = Device.devicename

    try:
        if Gb.PyiCloud is None:
            return

        if Device.icloud_update_reason:
            Device.display_info_msg("Requesting iCloud Location Update")

            Device.icloud_data_updated_flag = _update_PyiCloud_DevData_data(Device)

            if Device.icloud_data_updated_flag:
                Device.display_info_msg(Device.icloud_update_reason)

                monitor_msg = (f"{Device.icloud_update_reason}, RequestedBy-{devicename}")
                post_monitor_msg(devicename, monitor_msg)

            else:
                Device.display_info_msg("iCloud Location Data Not Available")
                if Gb.icloud_no_data_error_cnt > 3:
                    error_msg = (f"iCloud3 Error > No Location Data Returned for {devicename}. "
                                    "iCloud may be down or there is an Authentication issue. ")
                    post_error_msg(error_msg)

    except Exception as err:
        log_exception(err)
        error_msg = ("iCloud Location Request Error > An error occured refreshing the iCloud "
                        "Location Data. iCloud may be down or there is an internet connection "
                        f"issue. iCloud3 will try again later. ({err})")
        post_error_msg(error_msg)
        Device.icloud_data_updated_flag = False

    return Device.icloud_data_updated_flag
#----------------------------------------------------------------------------
def _update_PyiCloud_DevData_data(Device):
    '''
    Refresh the location data for a device and all oer dvices with the
    same tracking method.

    Input:  Device:     Device that wants to be updated. After getting the
                        data for that device, all other devices wth the
                        same trackin method are also updated since the data is available.

    Return: True        The device data was updated successfully
            False       Anf api error occurred or no device data was retured returned
    '''

    try:
        pyicloud_start_call_time = time_now_secs()

        if Gb.PyiCloud.requires_2fa:
            # pyicloud_ic3_interface.icloud_2fa_initiate_reauth_config_flow()
            # pyicloud_ic3_interface._icloud_2fa1_show_verification_code_entry_form()
            return False

        # Request an update for the Device's iCloud data
        last_pyicloud_refresh = Gb.pyicloud_refresh_time[Device.tracking_method]
        famshr_last_loc_time  = fmf_last_loc_time = ''
        famshr_last_loc_secs  = fmf_last_loc_secs = 0
        update_method = ''
        try:
            if Device.device_id_famshr:
                update_method = FAMSHR_FNAME
                famshr_last_loc_time = Device.PyiCloud_DevData_famshr.location_time
                famshr_last_loc_secs = Device.PyiCloud_DevData_famshr.location_secs
        except Exception as err:
            # **changed 4/24 - Added log_execption msg,
            log_exception(err)
            famshr_last_loc_time = HHMMSS_ZERO
            famshr_last_loc_secs = 0

        try:
            if Device.device_id_fmf:
                update_method = FMF_FNAME
                fmf_last_loc_time = Device.PyiCloud_DevData_fmf.location_time
                fmf_last_loc_secs = Device.PyiCloud_DevData_fmf.location_secs
        except Exception as err:
            #** changed 4/24 - Added log_execption msg, was getting error and set lastloc_time
            # to 00:00:00 on and then looping on old iosapp data msg
            log_exception(err)
            fmf_last_loc_time = HHMMSS_ZERO
            fmf_last_loc_secs = 0

        # Request FamShr or FmF Data
        if Device.tracking_method_FAMSHR:
            Gb.PyiCloud_FamilySharing.refresh_client()

        elif Device.tracking_method_FMF:
            Gb.PyiCloud_FindMyFriends.refresh_client()

        Gb.pyicloud_location_update_cnt += 1
        Gb.pyicloud_refresh_time[Device.tracking_method] = time_now_secs()

    except (PyiCloud2SARequiredException, PyiCloudAPIResponseException) as err:
        # log_exception(err)
        error_msg = ("iCloud Location Request Error > An error occured refreshing the iCloud "
                        f"{update_method} Location Data. iCloud may be down or there is an "
                        f"internet connection issue. iCloud3 will try again later. ({err})")
        post_monitor_msg(error_msg)
        return False

    try:
        # Update all devices with the new data just received from iCloud
        # it is is better or newer than the old data
        # and _Device.device_id in Gb.PyiCloud_DevData_by_device_id):
        # Determine if the famshr or fmf raw data is newer. Use the newest
        # data to update the Device if that data is newer than the Device's
        # current data
        for _Device in Gb.Devices:
            # If only famshr or fmf is available
            if _Device.PyiCloud_DevData:
                PyiCloud_DevData = _Device.PyiCloud_DevData

            # If both famshr and fmf are available, get best one
            elif _Device.PyiCloud_DevData_famshr and _Device.PyiCloud_DevData_fmf:
                PyiCloud_DevData = _get_famshr_fmf_PyiCloud_DevData_to_use(_Device)
            else:
                continue

            if Gb.log_rawdata_flag:
                log_rawdata(f"iCloud Device Data - <{_Device.devicename}>", PyiCloud_DevData.device_data)

            # Add info for the Device that requested the update
            better_raw_data_flag = _is_pyicloud_raw_data_better(_Device, Device, PyiCloud_DevData)

            # **changed 4/20
            trk_method_loc_time_msg = ''
            if better_raw_data_flag is False:
                if _Device is Device:
                    event_msg =(f"Discarding New iCloud Data (older or not accurate) > "
                            f"NewData-{PyiCloud_DevData.location_time} "
                            f"vs {_Device.loc_data_time}, "
                            f"GPSAccur-{PyiCloud_DevData.gps_accuracy_msg}m "
                            f"vs {_Device.loc_data_gps_accuracy:.0f}m, "
                            f"KeepingDataFrom-{_Device.dev_data_source}")
                    post_event(_Device.devicename, event_msg)
                continue
                            # f"GPSAccur-"
                            # f"{PyiCloud_DevData.location.get(ICLOUD_HORIZONTAL_ACCURACY, UNKNOWN)}m "

            try:
                if (_Device.device_id_famshr
                        and famshr_last_loc_time
                        and Gb.tracking_method_FAMSHR_used):
                    trk_method_loc_time_msg += (f", FamShr-{famshr_last_loc_time}")
                    if famshr_last_loc_secs != _Device.PyiCloud_DevData_famshr.location_secs:
                        trk_method_loc_time_msg += \
                                (f"{RARROW}{_Device.PyiCloud_DevData_famshr.location_time}")
            except:
                pass

            try:
                if (_Device.device_id_fmf
                        and fmf_last_loc_time
                        and Gb.tracking_method_FMF_used):
                    trk_method_loc_time_msg += (f", FmF-{fmf_last_loc_time}")
                    if fmf_last_loc_secs != _Device.PyiCloud_DevData_fmf.location_secs:
                        trk_method_loc_time_msg += \
                                (f"{RARROW}{_Device.PyiCloud_DevData_fmf.location_time}")
            except:
                pass

            if _Device.iosapp_monitor_flag:
                trk_method_loc_time_msg += (f", iOSApp-{_Device.iosapp_data_trigger_time}")

            # iOSApp data might have just been updated. Make sure iCloud data is newer
            if PyiCloud_DevData.location_secs >= _Device.iosapp_data_trigger_secs:
                _Device.update_dev_loc_data_from_raw_data(FAMSHR_FMF, PyiCloud_DevData)

            else:
                _Device.update_dev_loc_data_from_raw_data(IOSAPP)

            monitor_msg_devicename = f"{Device.devicename}, " if _Device is not Device else ""
            event_msg =(f"Analyzed New iCloud Data ({_Device.tracking_method_fname}) > "
                        f"{monitor_msg_devicename}"
                        f"Selected-{_Device.dev_data_source}, "
                        f"GPSAccuracy-{_Device.loc_data_gps_accuracy}m"
                        f"{trk_method_loc_time_msg}")

            if _Device is Device:
                post_event(_Device.devicename, event_msg)
            else:
                post_monitor_msg(_Device.devicename, event_msg)


        pyicloud_ic3_interface.reset_authentication_time()

        update_took_time = time_now_secs() - pyicloud_start_call_time
        Gb.pyicloud_calls_time += update_took_time

        return True

    except Exception as err:
        log_exception(err)

        return False

#----------------------------------------------------------------------------
def _get_famshr_fmf_PyiCloud_DevData_to_use(_Device):
    '''
    Analyze tracking method and location times to get best data to use
    '''
    try:
        # Is famshr raw data newer than fmf raw data
        if (_Device.PyiCloud_DevData_famshr.location_secs >=
                    _Device.PyiCloud_DevData_fmf.location_secs):
            PyiCloud_DevData = _Device.PyiCloud_DevData_famshr

        # Is fmf raw data newer than famshr raw data
        elif (_Device.PyiCloud_DevData_fmf.location_secs >=
                    _Device.PyiCloud_DevData_famshr.location_secs):
            PyiCloud_DevData = _Device.PyiCloud_DevData_fmf

        elif _Device.PyiCloud_DevData_famshr and _Device.tracking_method_FAMSHR:
            PyiCloud_DevData = _Device.PyiCloud_DevData_famshr

        elif _Device.PyiCloud_DevData_fmf and _Device.tracking_method_FMF:
            PyiCloud_DevData = _Device.PyiCloud_DevData_fmf

        elif _Device.PyiCloud_DevData_famshr:
            PyiCloud_DevData = _Device.PyiCloud_DevData_famshr

        elif _Device.PyiCloud_DevData_fmf:
            PyiCloud_DevData = _Device.PyiCloud_DevData_fmf

        else:
            error_msg = (f"{EVLOG_ALERT}Data Exception > {_Device.devicename} > No iCloud FamShr  "
                        f"or FmF Device Id was assigned to this device. This can be caused by "
                        f"No location data was returned from iCloud when iCloud3 was started."
                        f"{CRLF}Actions > Restart iCloud3. If the error continues, check the Event Log "
                        f"(iCloud3 Initialization Stage 2) and verify that the device is valid and a "
                        f"tracking method has been assigned. "
                        f"The device will be tracked by the iOS App.")
            post_event(error_msg)
            start_ic3.set_tracking_method(IOSAPP)

            PyiCloud_DevData = None

        error_msg = ''
        if PyiCloud_DevData.device_data is None:
            error_msg = 'No Device Data'
        elif LOCATION not in PyiCloud_DevData.device_data:
            error_msg = 'No Location Data'
        elif PyiCloud_DevData.device_data[LOCATION] == {}:
            error_msg = 'Location Data Empty'
        elif PyiCloud_DevData.device_data[LOCATION] is None:
            error_msg = 'Location Data Empty'
        elif _Device.is_tracking_paused:
            error_msg = 'Paused'

        if error_msg:
            if Gb.log_debug_flag:
                event_msg =(f"Location data not updated > {error_msg}, Will Retry")
                post_monitor_msg(_Device.devicename, event_msg)
            PyiCloud_DevData = None

        return PyiCloud_DevData

    except Exception as err:
        log_exception(err)
        return None

#----------------------------------------------------------------------------
def _is_pyicloud_raw_data_better(_Device, Device, PyiCloud_DevData):

    try:
        if PyiCloud_DevData is None:
            return False
        #** 5/3/2022 added gps=-1 check and commented out below if stmts
        elif PyiCloud_DevData.gps_accuracy == -1:
            return False
        # elif PyiCloud_DevData.device_data is None:
        #     return False
        # elif LOCATION not in PyiCloud_DevData:
        # elif LOCATION not in PyiCloud_DevData.device_data:


        device_being_updated_flag = (_Device is Device)
        new_loc_secs      = PyiCloud_DevData.location_secs
        #** 5/3/2022 Changed to use gps_accuracy property
        new_gps_accuracy  = PyiCloud_DevData.gps_accuracy
        # new_gps_accuracy  = PyiCloud_DevData.location.get(
        #                             ICLOUD_HORIZONTAL_ACCURACY, HIGH_INTEGER)

        # Use the data just returned if it is newer or has better accuracy than the
        # data last used. It may still be old or have poor gps accuracy. Is so,
        # display msg and then discard it later.
        more_accurate_flag = False
        newer_data_flag    = False

        # PyiCloud location newer than the devices location
        if new_loc_secs >= _Device.loc_data_secs:
            newer_data_flag = True
        # Is this data after the Device's old location threshold
        elif (new_loc_secs >= (time_now_secs() + _Device.old_loc_threshold_secs)):
            newer_data_flag = True

        # Is the new data more accurate than the Device's data
        if new_gps_accuracy <= Gb.gps_accuracy_threshold:
            more_accurate_flag = True
        elif new_gps_accuracy <= _Device.loc_data_gps_accuracy:
            more_accurate_flag = True

        update_data_flag = False

        #** 5/9/2022 Added check for passthru zone enter time
        # Is the PyiCloud location after the pass thru zone timer expires
        if (_Device.passthru_zone_expire_secs > 0
                and new_loc_secs > _Device.passthru_zone_expire_secs):
            newer_data_flag = True
            update_data_flag = True

        # Discard if older and less accurate
        if newer_data_flag is False and more_accurate_flag is False:
            update_data_flag = False

        # Update if newer and more accurate
        elif newer_data_flag and more_accurate_flag:
            update_data_flag = True

        #** 5/11/2022 No fmf data and old iOSapp data, was never updating
        # Discard if older and next update time is reached
        elif (newer_data_flag is False
                and new_loc_secs < _Device.next_update_secs):
            update_data_flag = False

        # Update if this is the Device being updated and the data is
        # better than previously saved
        elif (device_being_updated_flag
                and (newer_data_flag or more_accurate_flag)):
            update_data_flag = True
        # Update if this data is better than previously set

        elif (device_being_updated_flag is False
                and (newer_data_flag or more_accurate_flag)):
            update_data_flag = True

        monitor_msg = (f"isRawDataBetter > Newer-{newer_data_flag}, "
                        f"MoreAccurate-{more_accurate_flag}, "
                        f"ThisDeviceUpdated-{device_being_updated_flag}, "
                        f"UseData-{update_data_flag}")
        post_monitor_msg(_Device.devicename, monitor_msg)

        return update_data_flag

    except Exception as err:
        log_exception(err)
        return False
