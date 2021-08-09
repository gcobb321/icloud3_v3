


from ..globals          import GlobalVariables as Gb
from ..const_general    import (UNKNOWN, HIGH_INTEGER, HHMMSS_ZERO, DATETIME_ZERO, CRLF_DOT, CRLF,
                                NOT_HOME, NOT_SET, PAUSED, PAUSED_CAPS, ICLOUD3_ERROR_MSG, EVLOG_DEBUG,
                                IOSAPP, ICLOUD, EVLOG_NOTICE, )
from ..const_attrs      import (NEXT_UPDATE_TIME, INFO, TRACE_ICLOUD_ATTRS_BASE, TRACE_ATTRS_BASE,
                                LOCATION, ATTRIBUTES, TRIGGER, )
from .time              import (secs_since, secs_to_time, secs_to_time_str, )

import homeassistant.util.dt       as dt_util
#####################################################################
#
#   Formatting functions
#
#####################################################################
#--------------------------------------------------------------------
def format_gps(latitude, longitude, accuracy, latitude_to=None, longitude_to=None):
    '''Format the GPS string for logs & messages'''

    if longitude is None or latitude is None:
        gps_text = UNKNOWN
    else:
        accuracy_text = (f"/{accuracy:.0f}m)") if accuracy > 0 else ")"
        gps_to_text   = (f" to {latitude_to:.5f}, {longitude_to:.5f})") if latitude_to else ""
        gps_text      = f"({latitude:.5f}, {longitude:.5f}{accuracy_text}{gps_to_text}"

    return gps_text

#--------------------------------------------------------------------
def format_dist(dist):
    return f"{dist:.1f}km" if dist > .5 else f"{dist*1000:.0f}m"

def format_dist_m(dist):
    return f"{dist/1000:.1f}km" if dist > 500 else f"{dist:.0f}m"

#--------------------------------------------------------------------
def format_list(arg_list):
    formatted_list = str(arg_list)
    formatted_list = formatted_list.replace("[", "").replace("]", "")
    formatted_list = formatted_list.replace("{", "").replace("}", "")
    formatted_list = formatted_list.replace("'", "").replace(",", f"{CRLF_DOT}")

    return (f"{CRLF_DOT}{formatted_list}")
#--------------------------------------------------------------------
def format_time_age(time_secs):
    if time_secs == 0 or time_secs == HIGH_INTEGER:
        return 'Never'

    time_age_str = (f"{secs_to_time(time_secs)} "
                    f"({secs_to_time_str(secs_since(time_secs))} ago)")

    return time_age_str

#--------------------------------------------------------------------
def format_age_ts(time_secs):
    return (f"{secs_to_time_str(secs_since(time_secs))} ago")

#--------------------------------------------------------------------
def format_age(secs):
    return (f"{secs_to_time_str(secs)} ago")

#--------------------------------------------------------------------
def format_date_time_now(strftime_parameters):
    return (dt_util.now().strftime(strftime_parameters))

#--------------------------------------------------------------------
def format_cnt(desc, n):
    return f", {desc}(#{n})" if n > 1 else ''