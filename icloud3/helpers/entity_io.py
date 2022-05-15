
from ..global_variables import GlobalVariables as Gb
from ..const            import (UNKNOWN, HIGH_INTEGER, HHMMSS_ZERO, DATETIME_ZERO, CRLF_DOT, CRLF,
                                NOT_HOME, NOT_SET, PAUSED, PAUSED_CAPS, ICLOUD3_ERROR_MSG, EVLOG_DEBUG,
                                IOSAPP, ICLOUD, EVLOG_NOTICE, UTC_TIME, IOS_TRIGGER_ABBREVIATIONS,

                                NEXT_UPDATE_TIME, INFO, TRACE_ICLOUD_ATTRS_BASE, TRACE_ATTRS_BASE,
                                LOCATION, ATTRIBUTES, TRIGGER, )
from .base              import (instr, ordereddict_to_dict, post_event, post_error_msg, post_log_info_msg,
                                post_monitor_msg, _trace, _traceha,
                                log_debug_msg, log_exception, log_debug_msg, log_error_msg, log_rawdata, )
from .time              import (datetime_to_secs, secs_to_time)

# from .logging           import (log_debug_msg, log_error_msg, log_rawdata, )

from homeassistant.helpers import entity_registry
from homeassistant.helpers import device_registry

# import logging
# _LOGGER = logging.getLogger(__name__)
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
        # _traceha(f"{entity_id=} {entity_state=} {state=}")
        # _trace(f"{entity_id=} {entity_state=}-->{state=} ")

    except Exception as err:
        #When starting iCloud3, the device_tracker for the iosapp might
        #not have been set up yet. Catch the entity_id error here.
        #log_exception(err)
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
        log_exception(err)
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
        #log_exception(err)
        time_secs = HIGH_INTEGER

    #if Gb.log_rawdata_flag:
    #    _trace(f" > {entity_id} > {changed_time=} {secs_to_time(time_secs)=}")

    return time_secs

#--------------------------------------------------------------------
def get_entity_registry_data(platform=None, domain=None) -> list:
    """
    Cycle through the entity registry and extract the entities in a platform.

    Parameter:
        platform - platform to extract from the entity_registry
    Returns:
        [platform_entity_ids], [platform_entity_data]

    Esample data:
        platform_entity_ids  = ['zone.quail', 'zone.warehouse', 'zone.the_point', 'zone.home']
        platform_entity_data = {'zone.quail': {'entity_id': 'zone.quail', 'unique_id': 'quail',
                    'platform': 'zone', 'area_id': None, 'capabilities': {}, 'config_entry_id': None,
                    'device_class': None, 'device_id': None, 'disabled_by': None, 'entity_category': None,
                    'icon': None, 'id': 'e064e09a8f8c51f6f1d8bb3313bf5e1f', 'name': None, 'options': {},
                    'original_device_class': None, 'original_icon': 'mdi:map-marker',
                    'original_name': 'quail', 'supported_features': 0, 'unit_of_measurement': None}, {...}}
    """

    try:
        entity_reg           = entity_registry.async_get(Gb.hass)
        entities             = {k:_registry_data_str_to_dict(k, v, platform, domain)
                                    for k, v in entity_reg.entities.items()
                                    if _base_domain(k) in ['device_tracker', 'zone', 'sensor']}

        if platform is None and domain:
            platform_entity_data = {k:v for k, v in entities.items()
                                        if _base_domain(k) == domain}

        elif platform and domain is None:
            platform_entity_data = {k:v for k, v in entities.items()
                                        if v['platform'] == platform}

        elif platform and domain:
            platform_entity_data = {k:v for k, v in entities.items()
                                        if (v['platform'] == platform and _base_domain(k) == domain)}

        else:
            return [], {}

        platform_entity_ids  = [k for k in platform_entity_data.keys()]

        # The Home zone is not included in the entity registry
        if platform == 'zone': platform_entity_ids.append('zone.home')

        # if domain:
        #     domain_entity_data = {k:v for k, v in platform_entity_data.items() if k.startswith(domain)}
        #     domain_entity_ids  = [k for k in platform_entity_data.keys() if k.startswith(domain)]
        #     return domain_entity_ids, domain_entity_data
        # else:
        return platform_entity_ids, platform_entity_data

    except Exception as err:
        log_exception(err)
        return [], {}

        # device_reg = dr.async_get(Gb.hass)
        # devices    = ordereddict_to_dict(device_reg.devices)

#-------------------------------------------------------------------------------------------
def _base_domain(domain_entity_id):
    return domain_entity_id.split('.')[0]

def _base_entity_id(domain_entity_id):
    return domain_entity_id.split('.')[1]

#--------------------------------------------------------------------
def _registry_data_str_to_dict(key, text, platform, domain):
    """ Convert the entity/device registry data to a dictionary

        Input (EntityRegistry or DeviceRegistry attribute items for an entity/device):
            key:        The key of the items data
            text:       String that is in the form a dictioary.
            platform:   Requested platform

            Input text:
                "RequestedEntry(entity_id='zone.quail', area_id=None, capabilities={},
                version='11.22', item_type=[], supported_features=0,
                unit_of_measurement=None)"
            Reformatted:
                ['entity_id:'zone.quail', 'area_id': None, 'capabilities': {},
                'version': 11.22, item_tupe: [], 'supported_features': 0,
                'unit_of_measurement': None}
    """
    text = str(text).replace('RegistryEntry(', '')[:-1]
    items = [item.replace("'", "") for item in text.split(', ')]

    # Do not reformat items if not requested platform
    # _traceha(f'{key=} {domain=} {platform=}')
    if (f"platform={platform}" in items
            and (domain is None or _base_domain(key) == domain)):
        pass
    elif platform is None and _base_domain(key) == domain:
        pass
    else:
        return {'platform': 'not_platform_domain'}

    items_dict = {}
    for item in items:
        try:
            if instr(item, '=') is False:
                continue

            key_value = item.split('=')
            key = key_value[0]
            value = key_value[1]
            if value == 'None':
                items_dict[key] = None
            elif value.isnumeric():
                items_dict[key] = int(value)
            elif value.find('.') and value.split('.')[0].isnumeric() and value.split('.')[1].isnumeric():
                items_dict[key] = float(value)
            elif value.startswith('{'):
                items_dict[key] = eval(value)
            elif value.startswith('['):
                items_dict[key] = eval(value)
            else:
                items_dict[key] = value.replace('xa0', '')
        except:
            pass

    return items_dict

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
        log_exception(err)

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
        #log_exception(err)

    return
