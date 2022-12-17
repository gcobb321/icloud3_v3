

from ..global_variables     import GlobalVariables as Gb
from ..const                import (RESTORE_STATE_FILE, )

from ..helpers.common       import (instr, )
from ..helpers.messaging    import (log_exception, _trace, _traceha, )
from ..helpers.time_util    import (datetime_now, )

import os
import json
import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   .STORAGE/ICLOUD3.RESTORE_STATE FILE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def load_storage_icloud3_restore_state_file():

    try:
        if os.path.exists(Gb.icloud3_restore_state_filename) is False:
            build_initial_restore_state_file_structure()
            write_storage_icloud3_restore_state_file()

        success = read_storage_icloud3_restore_state_file()

        if success is False:
            _LOGGER.info(f"Invalid icloud3.restore_state File-{Gb.icloud3_restore_state_filename}")
            build_initial_restore_state_file_structure()
            write_storage_icloud3_restore_state_file()
            read_storage_icloud3_restore_state_file()

        return

    except Exception as err:
        log_exception(err)
        build_initial_restore_state_file_structure()
        write_storage_icloud3_restore_state_file()
        read_storage_icloud3_restore_state_file()

#--------------------------------------------------------------------
def build_initial_restore_state_file_structure():
    '''
    Create the initial data structure of the ic3 config file

    |---profile
    |---devices
        |---sensors
            |---actual sensor names & values
        |---from_zone
            |---home
                |---actual sensor names & values
            |---warehouse
                |---actual sensor names & values
        .
        .
        .
    '''

    _LOGGER.info(f"Creating iCloud3 Restore State File - {Gb.icloud3_restore_state_filename}")
    Gb.restore_state_file_data = RESTORE_STATE_FILE.copy()
    Gb.restore_state_profile = Gb.restore_state_file_data['profile']
    Gb.restore_state_devices = Gb.restore_state_file_data['devices']

#-------------------------------------------------------------------------------------------
def clear_devices():
    Gb.restore_state_devices = {}

#-------------------------------------------------------------------------------------------
def read_storage_icloud3_restore_state_file():
    '''
    Read the config/.storage/.icloud3.restore_state file and extract the
    data into the Global Variables
    '''

    try:
        with open(Gb.icloud3_restore_state_filename, 'r') as f:
            Gb.restore_state_file_data = json.load(f)
            Gb.restore_state_profile   = Gb.restore_state_file_data['profile']
            Gb.restore_state_devices   = Gb.restore_state_file_data['devices']
        return True

    except Exception as err:
        return False
        # log_exception(err)

    return False

#--------------------------------------------------------------------
def write_storage_icloud3_restore_state_file():
    '''
    Update the config/.storage/.icloud3.restore_state file
    '''

    try:
        with open(Gb.icloud3_restore_state_filename, 'w', encoding='utf8') as f:
            Gb.restore_state_profile['last_update'] = datetime_now()
            Gb.restore_state_file_data['profile'] = Gb.restore_state_profile
            Gb.restore_state_file_data['devices'] = Gb.restore_state_devices

            json.dump(Gb.restore_state_file_data, f, indent=4)

        return True

    except Exception as err:
        log_exception(err)

    return False