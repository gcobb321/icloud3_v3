import logging

from ..globals          import GlobalVariables as Gb
from ..const_general    import (UNKNOWN, HIGH_INTEGER, HHMMSS_ZERO, DATETIME_ZERO, CRLF_DOT, CRLF,
                                NOT_HOME, NOT_SET, PAUSED, PAUSED_CAPS, ICLOUD3_ERROR_MSG, EVLOG_DEBUG,
                                IOSAPP, ICLOUD, EVLOG_NOTICE, UTC_TIME, IOS_TRIGGER_ABBREVIATIONS, )
from ..const_attrs      import (NEXT_UPDATE_TIME, INFO, TRACE_ICLOUD_ATTRS_BASE, TRACE_ATTRS_BASE,
                                LOCATION, ATTRIBUTES, TRIGGER, )
from .base              import (combine_lists, instr, isnumber, inlist,
                                round_to_zero, is_inzone_zone, is_statzone, isnot_inzone_zone,
                                post_event, post_error_msg, post_log_info_msg,
                                post_monitor_msg, display_info_msg,
                                _trace, _traceha, )
from .time              import (datetime_to_secs, secs_to_time)

from .logging           import (log_debug_msg, log_error_msg, log_rawdata, )

_LOGGER = logging.getLogger(__name__)
#########################################################
#
#    Entity State and Attributes functions
#
#########################################################
def get_state(entity_id):
    """
    Return the state of an entity
    """

    try:
        entity_state = ''
        entity_state = Gb.hass.states.get(entity_id).state
        if entity_state in IOS_TRIGGER_ABBREVIATIONS:
            state = IOS_TRIGGER_ABBREVIATIONS[entity_state]
        else:
            state = Gb.state_to_zone.get(entity_state, entity_state.lower())
        # _trace(f"{entity_id=} {entity_state=}-->{state=} ")

    except Exception as err:
        #When starting iCloud3, the device_tracker for the iosapp might
        #not have been set up yet. Catch the entity_id error here.
        #_LOGGER.exception(err)
        state = NOT_SET

    #if Gb.log_rawdata_flag:
    #    _trace(f" > {entity_id} > {entity_state=} {state=}")

    return state

#--------------------------------------------------------------------
def get_attributes(entity_id):
    """
    Return the attributes of an entity.
    """

    try:
        entity_data  = Gb.hass.states.get(entity_id)
        entity_attrs = entity_data.attributes

        retry_cnt = 0
        while retry_cnt < 10:
            if entity_attrs:
                break
            retry_cnt += 1
            log_msg = (f"No attribute data returned for <{entity_id} >. Retrying #{retry_cnt}")
            log_debug_msg('*', log_msg)

    except (KeyError, AttributeError):
        entity_attrs = {}
        pass

    except Exception as err:
        _LOGGER.exception(err)
        entity_attrs = {}
        entity_attrs[TRIGGER] = (f"Error {err}")

    #if Gb.log_rawdata_flag:
    #    _trace(f" > {entity_id} > {entity_data=} {entity_attrs=}")

    return dict(entity_attrs)

#--------------------------------------------------------------------
def get_last_changed_time(entity_id):
    """
    Return the entity's last changed time attribute in secs
    Last changed time format '2019-09-09 14:02:45.12345+00:00' (utc value)
    """

    try:
        changed_time  = Gb.hass.states.get(entity_id).last_changed

        timestamp_utc = str(changed_time).split(".")[0]
        time_secs     = datetime_to_secs(timestamp_utc, UTC_TIME)

    except Exception as err:
        #_LOGGER.exception(err)
        time_secs = HIGH_INTEGER

    #if Gb.log_rawdata_flag:
    #    _trace(f" > {entity_id} > {changed_time=} {secs_to_time(time_secs)=}")

    return time_secs

#--------------------------------------------------------------------
def get_entity_ids(domain):
    """
    Return a list of all of the entities for this domain
    """

    try:
        entity_ids =  Gb.hass.states.entity_ids(domain)

    except Exception as err:
        entity_ids = []

    #if Gb.log_rawdata_flag:
    #    _trace(f" > {domain} > {entity_ids=}")

    return entity_ids
#--------------------------------------------------------------------
def set_state_attributes(entity_id, state_value, attrs_value):
    """
    Update the state and attributes of an entity_id
    """

    try:
        Gb.hass.states.set(entity_id, state_value, attrs_value, force_update=True)

    except Exception as err:
        log_msg =   (f"Error updating entity > <{entity_id} >, StateValue-{state_value}, "
                    f"AttrsValue-{attrs_value}")
        log_error_msg(log_msg)
        _LOGGER.exception(err)

#--------------------------------------------------------------------
def extract_attr_value(attributes, attribute_name, numeric=False):
    ''' Get an attribute out of the attrs attributes if it exists'''

    try:
        if attribute_name in attributes:
            return attributes[attribute_name]
        elif numeric:
            return 0
        else:
            return ''

    except:
        return ''

#--------------------------------------------------------------------
def trace_device_attributes(Device,
                description, fct_name, attrs):

    try:
        #Extract only attrs needed to update the device
        if attrs is None:
            return

        attrs_in_attrs = {}
        if description.find("iCloud") >= 0 or description.find("FamShr") >= 0:
            attrs_base_elements = TRACE_ICLOUD_ATTRS_BASE
            if LOCATION in attrs:
                attrs_in_attrs  = attrs[LOCATION]
        elif 'Zone' in description:
            attrs_base_elements = attrs
        else:
            attrs_base_elements = TRACE_ATTRS_BASE
            if ATTRIBUTES in attrs:
                attrs_in_attrs  = attrs[ATTRIBUTES]

        trace_attrs = {k: v for k, v in attrs.items() \
                            if k in attrs_base_elements}

        trace_attrs_in_attrs = {k: v for k, v in attrs_in_attrs.items() \
                            if k in attrs_base_elements}

        ls = Device.state_last_poll
        cs = Device.state_this_poll
        log_msg = (f"{description} Attrs ___ ({fct_name})")
        log_debug_msg(Device.devicename, log_msg)

        log_msg = (f"{description} Last State-{ls}, This State-{cs}")
        log_debug_msg(Device.devicename, log_msg)

        log_msg = (f"{description} Attrs-{trace_attrs}{trace_attrs_in_attrs}")
        log_debug_msg(Device.devicename, log_msg)

        log_rawdata(f"iCloud Rawdata - {Device.devicename}--{description}", attrs)

    except Exception as err:
        pass
        #_LOGGER.exception(err)

    return
