

from ..global_variables import GlobalVariables as Gb
from ..const            import (NOT_HOME, STATIONARY, CIRCLE_LETTERS_DARK, UNKNOWN, CRLF_DOT, CRLF,
                                BATTERY_STATUS_FNAME,)
from collections        import OrderedDict

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DATA VERIFICATION FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def combine_lists(parm_lists):
    '''
    Take a list of lists and return a single list of all of the items.
        [['a,b,c'],['d,e,f']] --> ['a','b','c','d','e','f']
    '''
    new_list = []
    for lists in parm_lists:
        lists_items = lists.split(',')
        for lists_item in lists_items:
            new_list.append(lists_item)

    return new_list

#--------------------------------------------------------------------
def list_to_str(list_value, separator=None):
    '''
    Convert list values into a string

    list_valt - list to be converted
    separator - Strig valut that separates each item (default = ', ')
    '''
    separator_str = separator if separator else ', '
    list_str = separator_str.join(list_value)

    if separator.startswith(CRLF):
        return f"{separator_str}{list_str}"
    else:
        return list_str

#--------------------------------------------------------------------
def instr(string, substring):
    '''
    Fine a substring or a list of substrings strings in a string
    '''
    if substring is None:
        return False

    if type(substring) is str:
        substring = [substring]
        # return (str(string).find(substring) >= 0)

    for substring_str in substring:
        if str(string).find(substring_str) >= 0:
            return True
    return False

#--------------------------------------------------------------------
def is_statzone(string):
        return (str(string).find(STATIONARY) >= 0)

#--------------------------------------------------------------------
def isnumber(string):

    try:
        test_number = float(string)

        return True

    except:
        return False

#--------------------------------------------------------------------
def inlist(string, list_items):
    for item in list_items:
        if str(string).find(item) >= 0:
            return True

    return False

#--------------------------------------------------------------------
def round_to_zero(value):
    if abs(value) < .001: value = 0
    return round(value, 2)

#--------------------------------------------------------------------
def is_inzone_zone(zone):
    return (zone != NOT_HOME)

#--------------------------------------------------------------------
def isnot_inzone_zone(zone):
    return (zone == NOT_HOME)

#--------------------------------------------------------------------
def ordereddict_to_dict(odict_item):
    if isinstance(odict_item, OrderedDict):
        dict_item = dict(odict_item)
    else:
        dict_item = odict_item
    try:
        for key, value in dict_item.items():
            dict_item[key] = ordereddict_to_dict(value)
            if isinstance(value, list):
                new_value = []
                for item in value:
                    if isinstance(item, OrderedDict):
                        item = ordereddict_to_dict(item)
                    new_value.append(item)
                dict_item[key] = new_value
    except AttributeError:
        pass

    return dict_item

#--------------------------------------------------------------------
def circle_letter(field):
    first_letter = field[:1].lower()
    return CIRCLE_LETTERS_DARK.get(first_letter, '✪')

#--------------------------------------------------------------------
def obscure_field(field):
    '''
    An obscured field is one where the first and last 2-characters are kept and the others
    are replaced by a string of periods to hide it's actual value. This is used for usernames
    and passwords. (geekstergary@gmail.com --> ge..........ry@gm.....om))

    Input:
        Field to be obscurred

    Return:
        The obscured field
    '''
    if field == '':
        return ''

    if instr(field, '@'):
        # 12/19/2022 (beta 3)-An error was generated if there was more than 1 @-sign in the email field
        field_parts   = field.split('@')
        email_name    = field_parts[0]
        email_domain  = field_parts[1]
        obscure_field = (   f"{email_name[0:2]}{'.'*(len(email_name)-2)}@"
                            f"{email_domain[0:2]}{'.'*(len(email_domain)-2)}")
        # obscure_field = (   f"{email_name[0:2]}{'.'*(len(email_name)-2)}{email_name[-2:]}@"
        #                     f"{email_domain[0:2]}{'.'*(len(email_domain)-2)}{email_domain[-2:]}")
        return obscure_field

    obscure_field = (f"{field[0:2]}{'.'*(len(field)-2)}")
    # obscure_field = (f"{field[0:2]}{'.'*(len(field)-2)}{field[-2:]}")
    return obscure_field

#--------------------------------------------------------------------
def zone_fname(zone):
    return Gb.zone_display_as.get(zone, zone.title())

#--------------------------------------------------------------------
def format_gps(latitude, longitude, accuracy, latitude_to=None, longitude_to=None):
    '''Format the GPS string for logs & messages'''

    if longitude is None or latitude is None:
        gps_text = UNKNOWN
    else:
        accuracy_text = (f"/±{accuracy:.0f}m)") if accuracy > 0 else ")"
        gps_to_text   = (f" to {latitude_to:.5f}, {longitude_to:.5f})") if latitude_to else ""
        gps_text      = f"({latitude:.5f}, {longitude:.5f}{accuracy_text}{gps_to_text}"

    return gps_text

#--------------------------------------------------------------------
def format_battery_status(battery_status):
    return BATTERY_STATUS_FNAME.get(battery_status, battery_status.title())

#--------------------------------------------------------------------
def format_list(arg_list):
    formatted_list = str(arg_list)
    formatted_list = formatted_list.replace("[", "").replace("]", "")
    formatted_list = formatted_list.replace("{", "").replace("}", "")
    formatted_list = formatted_list.replace("'", "").replace(",", f"{CRLF_DOT}")

    return (f"{CRLF_DOT}{formatted_list}")

#--------------------------------------------------------------------
def format_cnt(desc, n):
    return f", {desc}(#{n})" if n > 1 else ''
