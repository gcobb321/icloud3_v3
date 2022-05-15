

from ..global_variables import GlobalVariables as Gb
from ..const            import (UNKNOWN, HIGH_INTEGER, HHMMSS_ZERO, DATETIME_ZERO, DATETIME_FORMAT, WAZE_USED, )

from .base              import (post_event, post_log_info_msg, internal_error_msg, )

import time
# from   homeassistant.util.location import distance
import homeassistant.util.dt       as dt_util
import time

import logging
_LOGGER = logging.getLogger(__name__)

#####################################################################
#
#   Time conversion and formatting functions
#
#####################################################################
def time_now_secs():
    ''' Return the current timestamp seconds '''

    return int(time.time())

#--------------------------------------------------------------------
def datetime_now():
    ''' Return now in MM/DD/YYYY hh:mm:ss format'''
    return (dt_util.now().strftime(DATETIME_FORMAT)[0:19])

#--------------------------------------------------------------------
def time_now():
    ''' Return now in MM/DD/YYYY hh:mm:ss format'''
    return (dt_util.now().strftime(DATETIME_FORMAT)[11:19])

#--------------------------------------------------------------------
def secs_to_time(timestamp_secs, hour_24=False):
    """ Convert seconds to hh:mm:ss """
    time_format = Gb.um_time_strfmt if hour_24==False else '%H:%M:%S'
    if timestamp_secs is None or timestamp_secs == 0 or timestamp_secs == HIGH_INTEGER:
        return HHMMSS_ZERO
    else:
        timestamp_secs = timestamp_secs + Gb.timestamp_local_offset_secs
        t_struct = time.localtime(timestamp_secs)
        return  (f"{time.strftime(time_format, t_struct).lstrip('0')}")

#--------------------------------------------------------------------
def msecs_to_time(timestamp_secs):
    """ Convert milliseconds (e.g., iCloud timestamp) to hh:mm:ss """
    return secs_to_time(int(timestamp_secs/1000))

#--------------------------------------------------------------------
def secs_to_time_str(secs):
    """ Create the time string from seconds """

    try:
        if secs >= 86400:
            time_str = secs_to_dhms_str(secs)
        elif secs < 60:
            time_str = f"{secs:.0f} sec"
        elif secs < 3600:
            time_str = f"{secs/60:.0f} min"
        elif secs == 3600:
            time_str = "1 hr"
        else:
            time_str = f"{secs/3600:.1f} hrs"

        # change xx.0 min/hr --> xx min/hr
        time_str = time_str.replace('.0 ', ' ')

    except Exception as err:
        #_LOGGER.exception(err)
        time_str = ''

    return time_str

#--------------------------------------------------------------------
def mins_to_time_str(mins):
    """ Create the time string from seconds """

    try:
        if mins >= 86400:
            time_str = secs_to_dhms_str(mins*60)
        elif mins < 60:
            time_str = f"{mins:.1f} min"
        elif mins == 60:
            time_str = "1 hr"
        else:
            time_str = f"{mins/60:.1f} hrs"

        # change xx.0 min/hr --> xx min/hr
        time_str = time_str.replace('.0 ', ' ')

    except Exception as err:
        time_str = ''

    return time_str
#--------------------------------------------------------------------
def secs_to_dhms_str(secs):
    """ Create the time 0w0d0h0m0s time string from seconds """

    try:
        secs_dhms = float(secs)
        dhms_str = ""
        if (secs >= 31557600):
            return f"{round(secs_dhms/31557600, 2)}y"

        if (secs >= 604800): dhms_str += f"{secs_dhms // 604800}w"
        secs_dhms = secs_dhms % 604800
        if (secs >= 86400): dhms_str += f"{secs_dhms // 86400}d"
        secs_dhms = secs_dhms % 86400
        if (secs >= 3600): dhms_str += f"{secs_dhms // 3600}h"
        secs_dhms %= 3600
        if (secs >= 60): dhms_str += f"{secs_dhms // 60}m"
        secs_dhms %= 60
        dhms_str += f"{secs_dhms}s"

        dhms_str = dhms_str.replace('.0', '')

    except:
        dhms_srt = ""

    return dhms_str

#--------------------------------------------------------------------
def waze_mins_to_time_str(waze_time_from_zone):
    '''
    Return:
        Waze used:
            The waze time string (hrs/mins) if Waze is used
        Waze not used:
            'N/A'
    '''

    #Display time to the nearest minute if more than 3 min away
    if Gb.waze_status == WAZE_USED:
        mins = waze_time_from_zone * 60
        secs = 0
        if mins > 180:
            mins, secs = divmod(mins, 60)
            mins = mins + 1 if secs > 30 else mins
            secs = mins * 60

        waze_time_str = secs_to_time_str(secs)

    else:
        waze_time_str = 'N/A'

    return waze_time_str

#--------------------------------------------------------------------
def secs_since(timestamp_secs) -> int:
    return round(time.time() - timestamp_secs)
#--------------------------------------------------------------------
def secs_to(timestamp_secs) -> int:
    return round(timestamp_secs - time.time())
#--------------------------------------------------------------------
def hhmmss_to_secs(hhmmss):
    return time_to_secs(hhmmss)

def time_to_secs(hhmmss):
    """ Convert hh:mm:ss into seconds """
    try:
        hh_mm_ss = hhmmss.split(":")
        secs = int(hh_mm_ss[0]) * 3600 + int(hh_mm_ss[1]) * 60 + int(hh_mm_ss[2])

    except:
        secs = 0

    return secs

#--------------------------------------------------------------------
def secs_to_12hrtime(timestamp_secs, ampm=False):
    """ Convert seconds to hh:mm:ss """
    time_to_12hrtime(secs_to_time(timestamp_secs, ampm))

#--------------------------------------------------------------------
def hhmmss_to_12hrtime(hhmmss, ampm=False):
    return time_to_12hrtime(hhmmss, ampm)

def time_to_12hrtime(hhmmss, ampm=False):
    '''
    Change hh:mm:ss time to a 12 hour time
    Input : hh:mm:ss where hh=(0-23)
            : hh:mm:ss (30s)
    Return: hh:mm:ss where hh=(0-11) with 'a' or 'p'
    '''
    try:
        if Gb.time_format == 12:
            hh_mm_ss    = hhmmss.split(':')
            hhmmss_hh   = int(hh_mm_ss[0])
            secs_suffix = hh_mm_ss[2].split('-')

            ap = 'a'
            if hhmmss_hh > 12:
                hhmmss_hh -= 12
                ap = 'p'
            elif hhmmss_hh == 12:
                ap = 'p'
            elif hhmmss_hh == 0:
                hhmmss_hh = 12

            ap = '' if ampm is False else ap

            hhmmss = f"{hhmmss_hh}:{hh_mm_ss[1]}:{secs_suffix[0]}{ap}"
            if len(secs_suffix) == 2:
                hhmmss += f"-{secs_suffix[1]}"
    except:
            pass

    return hhmmss
#--------------------------------------------------------------------
def time_str_to_secs(time_str='30 min') -> int:
    """
    Calculate the seconds in the time string.
    The time attribute is in the form of '15 sec' ',
    '2 min', '60 min', etc
    """

    if time_str == "":
        return 0

    try:
        s1 = str(time_str).replace('_', ' ') + " min"
        time_part = float((s1.split(" ")[0]))
        text_part = s1.split(" ")[1]

        if text_part in ('sec', 'secs'):
            secs = time_part
        elif text_part in ('min', 'mins'):
            secs = time_part * 60
        elif text_part in ('hr', 'hrs'):
            secs = time_part * 3600
        else:
            secs = 1800      #default to 20 minutes

    except:
        secs = 1800

    return secs

#--------------------------------------------------------------------
def timestamp_to_time_utcsecs(utc_timestamp) -> int:
    """
    Convert iCloud timeStamp into the local time zone and
    return hh:mm:ss
    """
    ts_local = int(float(utc_timestamp)/1000) + Gb.time_zone_offset_seconds
    hhmmss   = dt_util.utc_from_timestamp(ts_local).strftime(Gb.um_time_strfmt)
    if hhmmss[0] == "0":
        hhmmss = hhmmss[1:]

    return hhmmss

#--------------------------------------------------------------------
def datetime_to_time(datetime):
    """
    Extract the time from the device timeStamp attribute
    updated by the IOS app.
    Format #1 is --'datetime': '2019-02-02 12:12:38.358-0500'
    Format #2 is --'datetime': '2019-02-02 12:12:38 (30s)'
    """

    try:
        #'0000-00-00 00:00:00' --> '00:00:00'
        if datetime == DATETIME_ZERO:
            return HHMMSS_ZERO

        #'2019-02-02 12:12:38.358-0500' --> '12:12:38'
        elif datetime.find('.') >= 0:
            return datetime[11:19]

        #'2019-02-02 12:12:38 (30s)' --> '12:12:38 (30s)'
        elif datetime.find('-') >= 0:
            return datetime[11:]

        else:
            return datetime

    except:
        pass

    return datetime

#--------------------------------------------------------------------
def datetime_to_12hrtime(datetime, ampm=False):
    """
    Convert 2120-07-19 14:28:34 to 2:28:34
    """
    return(time_to_12hrtime(datetime_to_time(datetime)), ampm)
#--------------------------------------------------------------------
def secs_to_datetime(secs):
    """
    Convert seconds to timestamp
    Return timestamp (2020-05-19 09:12:30)
    """

    try:
        time_struct = time.localtime(secs)
        timestamp   = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)

    except Exception as err:
        timestamp = "0000-00-00 00:00:00"

    return timestamp

#--------------------------------------------------------------------
def datetime_to_secs(datetime, utc_local=False) -> int:
    """
    Convert the timestamp from the device timestamp attribute
    updated by the IOS app.
    Format is --'timestamp': '2019-02-02T12:12:38.358-0500'
    Return epoch seconds
    """
    try:
        if datetime is None:
            secs = 0
        elif datetime == '' or datetime[0:19] == '0000-00-00 00:00:00':
            secs = 0
        else:
            datetime = datetime.replace("T", " ")[0:19]
            secs = time.mktime(time.strptime(datetime, "%Y-%m-%d %H:%M:%S"))
            if utc_local is True:
                secs += Gb.time_zone_offset_seconds

    except:
        secs = 0

    return secs

#--------------------------------------------------------------------
# def sleep_mins(sleep_minutes):
#     time.sleep(sleep_minutes)

#--------------------------------------------------------------------
def timestamp4(timestamp_secs):
    ts_str = str(timestamp_secs).replace('.0', '')
    return str(ts_str)[-4:]

#--------------------------------------------------------------------
def secs_to_time_age_str(time_secs):
    """ Secs to '17:36:05 (2 sec ago)' """
    if time_secs == 0 or time_secs == HIGH_INTEGER:
        return 'Never'

    time_age_str = (f"{secs_to_time(time_secs)} "
                    f"({secs_to_time_str(secs_since(time_secs))} ago)")

    return time_age_str

#--------------------------------------------------------------------
def secs_to_12hrtime_age_str(time_secs, ampm=False):
    """ Secs to '5:36:05p (2 sec ago)' """
    if time_secs == 0 or time_secs == HIGH_INTEGER:
        return 'Never'

    time_age_str = (f"{time_to_12hrtime(secs_to_time(time_secs), ampm)} "
                    f"({secs_to_time_str(secs_since(time_secs))} ago)")

    return time_age_str

#--------------------------------------------------------------------
# def format_age_ts(time_secs):
def secs_to_age_str(time_secs):
    """ Secs to `2 sec ago`, `3 mins ago`/, 1.5 hrs ago` """
    return f"{secs_to_time_str(secs_since(time_secs))} ago"

#--------------------------------------------------------------------
def format_age(secs):
    """ Secs to `52.3y ago` """
    return f"{secs_to_time_str(secs)} ago"

#--------------------------------------------------------------------
def format_date_time_now(strftime_parameters):
    return dt_util.now().strftime(strftime_parameters)

#########################################################
#
#   TIME UTILITY ROUTINES
#
#########################################################
def calculate_time_zone_offset():
    """
    Calculate time zone offset seconds
    """
    try:
        local_zone_offset = dt_util.now().strftime('%z')
        local_zone_name   = dt_util.now().strftime('%Z')
        local_zone_offset_secs = int(local_zone_offset[1:3])*3600 + int(local_zone_offset[3:])*60
        if local_zone_offset[:1] == "-":
            local_zone_offset_secs = -1*local_zone_offset_secs

        t_now    = int(time.time())
        t_hhmmss = dt_util.now().strftime('%H%M%S')
        l_now    = time.localtime(t_now)
        l_hhmmss = time.strftime('%H%M%S', l_now)
        g_now    = time.gmtime(t_now)
        g_hhmmss = time.strftime('%H%M%S', g_now)

        if (l_hhmmss == g_hhmmss):
            Gb.timestamp_local_offset_secs = local_zone_offset_secs

        post_event(f"Local Time Zone Offset > "
                            f"UTC{local_zone_offset[:3]}:{local_zone_offset[-2:]} hrs, "
                            f"{local_zone_name}")

    except Exception as err:
        _LOGGER.exception(err)
        internal_error_msg(err, 'CalcTimeOffset')
        local_zone_offset_secs = 0

    Gb.time_zone_offset_seconds = local_zone_offset_secs

    return local_zone_offset_secs
