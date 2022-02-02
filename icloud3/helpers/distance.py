

from   homeassistant.util.location import distance

from ..global_variables import GlobalVariables as Gb
from ..const            import (UNKNOWN, HIGH_INTEGER, HHMMSS_ZERO, DATETIME_ZERO, CRLF_DOT, CRLF,
                            NOT_HOME, NOT_SET, PAUSED, PAUSED_CAPS, ICLOUD3_ERROR_MSG, EVLOG_DEBUG,
                            IOSAPP, ICLOUD, EVLOG_NOTICE,

                            NEXT_UPDATE_TIME, INFO, TRACE_ICLOUD_ATTRS_BASE, TRACE_ATTRS_BASE,
                            LOCATION, ATTRIBUTES, TRIGGER, )
from .base              import (round_to_zero, _trace, )
#####################################################################
#
#   Distance conversion and formatting functions
#
#####################################################################
def km_to_mi(distance):
    """
    convert km to miles
    """
    try:
        mi = distance * Gb.um_km_mi_factor

        if mi == 0:
            mi = 0
        elif mi <= 10:
            mi = round(mi, 2)
        elif mi <= 100:
            mi = round(mi, 1)
        else:
            mi = round(mi)

    except:
        mi = 0
    return mi

def mi_to_km(distance):
    return round(float(distance) / Gb.um_km_mi_factor, 2)

#--------------------------------------------------------------------
def calc_distance_km(from_lat, from_long, to_lat, to_long):
    if from_lat is None or from_long is None or to_lat is None or to_long is None:
        return 0

    dist_km = distance(from_lat, from_long, to_lat, to_long) / 1000

    return dist_km

#--------------------------------------------------------------------
def calc_distance_m(from_lat, from_long, to_lat, to_long):
    if from_lat is None or from_long is None or to_lat is None or to_long is None:
        return 0

    dist_m = distance(from_lat, from_long, to_lat, to_long)

    return round(dist_m, 2)