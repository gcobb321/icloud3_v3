###################################################################################
#
#   EVENT LOG ROUTINES - Set up the Event Log, Post events to the
#           setup_event_log - Set up the Event Log
#           post_event - Add an event to the Event Log internal table
#           update_event_log_display - Extract the filterd records from the event log
#                       table and update the display
#           export_event_log - Export the event log records to the ic3_event_log.text file
#
#
###################################################################################

from ..global_variables  import GlobalVariables as Gb
from ..const             import (DOT, HHMMSS_ZERO, HIGH_INTEGER, STATIONARY, CRLF, CRLF_DOT, CRLF_CHK,
                                EVLOG_ERROR,
                                EVLOG_ALERT, EVLOG_DEBUG, EVLOG_INIT_HDR, EVLOG_TIME_RECD, HOME,
                                EVLOG_RECDS_PER_DEVICE, EVLOG_RECDS_PER_DEVICE_ZONE,
                                EVENT_LOG_CLEAR_SECS, EVENT_LOG_CLEAR_CNT, )

from ..helpers.base      import instr, is_statzone, log_exception, _traceha, log_info_msg
from ..helpers.time      import time_to_12hrtime, datetime_now
from ..helpers.entity_io import set_state_attributes


import os
import time
import homeassistant.util.dt as dt_util



CONTROL_RECD            = [HHMMSS_ZERO,'','','','','','Control Record']
SENSOR_EVENT_LOG_ENTITY = 'sensor.icloud3_event_log'

# The text starts with a special character:
# ^1^ - LightSeaGreen
# ^2^ - BlueViolet
# ^3^ - OrangeRed
# ^4^ - DeepPink
# ^5^ - MediumVioletRed
# ^6^ - --dark-primary-color
# EVLOG_NOTICE      = "^2^"
# EVLOG_ERROR       = "^3^"
# EVLOG_ALERT       = "^4^"
# EVLOG_TRACE       = "^5^"
# EVLOG_DEBUG       = "^6^"
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class EventLog(object):
    def __init__(self, hass):
        self.hass = hass
        self.initialize()

    def initialize(self):
        self.display_text_as         = {}
        self.event_log_table         = []
        self.devicename_fname        = {}
        self.base_attrs              = ''
        self.log_table_max_items     = 999
        self.clear_secs              = HIGH_INTEGER
        self.last_devicename         = '*'
        self.trk_monitors_flag       = False
        self.log_debug_flag          = False
        self.log_rawdata_flag        = False

###################################################################################
#
#   EVENT LOG ROUTINES
#
###################################################################################
    def setup_event_log(self):
        '''
        Set up the name, picture and device attributes in the Event Log
        sensor. Read the sensor attributes first to see if it was set up by
        another instance of iCloud3 for a different iCloud acount.
        '''
        try:
            curr_base_attrs = self.hass.states.get(SENSOR_EVENT_LOG_ENTITY).attributes
            base_attrs = {k: v for k, v in curr_base_attrs.items()}

        except (KeyError, AttributeError):
            base_attrs         = {}
            base_attrs["logs"] = ""

        except Exception as err:
            log_exception(err)

        try:
            self.devicename_fname = {}
            if len(Gb.Devices_by_devicename) > 0:
                for devicename, Device in Gb.Devices_by_devicename.items():
                    self.devicename_fname[devicename] = Device.fname
            else:
                self.devicename_fname = {'No Tracked Devices Error': ''}

            self.log_table_max_items = 0
            for devicename, Device in Gb.Devices_by_devicename.items():
                self.log_table_max_items += EVLOG_RECDS_PER_DEVICE + EVLOG_RECDS_PER_DEVICE_ZONE*len(Device.DeviceFmZones_by_zone)

            base_attrs["names"] = self.devicename_fname

            # self._set_state(SENSOR_EVENT_LOG_ENTITY, "Initialized", base_attrs)
            set_state_attributes(SENSOR_EVENT_LOG_ENTITY, "Initialized", base_attrs)

            self.base_attrs = {k: v for k, v in base_attrs.items() if k != "logs"}
            self.base_attrs["logs"] = ""

        except Exception as err:
            log_exception(err)

        return

#------------------------------------------------------
    def post_event(self, devicename, event_text='+'):
    #def post_event(self, device, iosapp_state, ic3_zone,
    #                    interval, travel_time, distance, event_text):
        '''
        Add records to the Event Log table the device. If the device="*",
        the event_text is added to all deviceFNAMEs table.

        The event_text can consist of pseudo codes that display a 2-column table (see
        _display_usage_counts function for an example and details)

        The event_log lovelace card will display the event in a special color if
        the text starts with a special character:
        '''
        try:
            if event_text == '+':
                event_text = devicename
                devicename = "*"
            if devicename is None or devicename == '':
                 devicename = '*'

            if (instr(event_text, "▼") or instr(event_text, "▲")
                    or len(event_text) == 0
                    or instr(event_text, "event_log")):
                return

            this_update_time = dt_util.now().strftime('%H:%M:%S')
            this_update_time = time_to_12hrtime(this_update_time, ampm=True)

            try:
                if devicename != '*':
                    Device = Gb.Devices_by_devicename[devicename]
                    if (Device.DeviceFmZoneCurrent.zone != HOME
                            or event_text.startswith('^t^')):
                        this_update_time = (f"»{Device.DeviceFmZoneCurrent.zone_display_as[:6]}")

            except Exception as err:
                # log_exception(err)
                pass

            if (instr(type(event_text), 'dict') or instr(type(event_text), 'list')):
                 event_text = str(event_text)

            if event_text.startswith(EVLOG_TIME_RECD):
                event_text = event_text.replace('N/A', '')

            if len(event_text) == 0: event_text = 'Info Message'
            event_text = event_text.replace('__', '')
            event_text = event_text.replace('"', '`')
            event_text = event_text.replace("'", "`")
            event_text = event_text.replace('~','--')
            event_text = event_text.replace('Background','Bkgnd')
            event_text = event_text.replace('Geographic','Geo')
            event_text = event_text.replace('Significant','Sig')

            for from_text in self.display_text_as:
                event_text = event_text.replace(from_text, self.display_text_as[from_text])

            #Keep track of special colors so it will continue on the
            #next text chunk
            color_symbol = ''
            if event_text.startswith('^1^'): color_symbol = '^1^'
            if event_text.startswith('^2^'): color_symbol = '^2^'
            if event_text.startswith('^3^'): color_symbol = '^3^'
            if event_text.startswith('^4^'): color_symbol = '^4^'
            if event_text.startswith('^5^'): color_symbol = '^5^'
            if event_text.startswith('^6^'): color_symbol = '^6^'
            if instr(event_text, EVLOG_ERROR):     color_symbol = '!'
            char_per_line = 2000

            #Break the event_text string into chunks of 250 characters each and
            #create an event_log recd for each chunk
            if len(event_text) < char_per_line:
                event_recd = [devicename, this_update_time, event_text]
                self._insert_event_log_recd(event_recd)

            else:
                line_no       = int(len(event_text)/char_per_line + .5)
                char_per_line = int(len(event_text) / line_no)
                event_text   +=f" ({len(event_text)}-{line_no}-{char_per_line})"

                if event_text.find(CRLF) > 0:
                    split_str = CRLF
                else:
                    split_str = " "
                split_str_end_len = -1 * len(split_str)
                word_chunk = event_text.split(split_str)

                line_no = len(word_chunk)-1
                event_chunk = ''
                while line_no >= 0:
                    if len(event_chunk) + len(word_chunk[line_no]) + len(split_str) > char_per_line:
                        event_recd = [devicename, '',
                                        (f"{color_symbol}{event_chunk[:split_str_end_len]} ({event_chunk[:split_str_end_len]})")]
                        self._insert_event_log_recd(event_recd)

                        event_chunk = ''

                    if len(word_chunk[line_no]) > 0:
                        event_chunk = word_chunk[line_no] + split_str + event_chunk

                    line_no-=1

                event_recd = [devicename, this_update_time,
                                (f"{event_chunk[:split_str_end_len]} ({event_chunk[:split_str_end_len]})")]
                self._insert_event_log_recd(event_recd)

        except Exception as err:
            log_exception(err)

#=========================================================================
    def update_event_log_display(self, devicename):
        '''
        Extract the records from the event log table, select the items to
        be displayed based on the log_level_debug and devicename filters and
        update the sensor.ic3_event_log attribute. This will be caught by
        the icloude-event-log-card.js custom card and display the selected
        records.

        This is called from device_tracker.py using:
            Gb.EvLog.log_attr_debug_selection

        Input variables:
            log_attr_debug_selection - A text field containing evlog (display
                    tracking monitors), halog (show Debug logging is on),
                    rawdata (show RawData log dump is on)

        '''

        try:
            log_attrs = self.base_attrs.copy() if self.base_attrs else {}

            attr_recd  = {}

            log_attr_text = ""
            if Gb.evlog_trk_monitors_flag: log_attr_text += "evlog,"
            if Gb.log_debug_flag:          log_attr_text += "halog,"
            if Gb.log_rawdata_flag:        log_attr_text += "rawdata,"

            log_attrs["log_level_debug"] = log_attr_text

            if devicename is None:
                return
            elif devicename == "clear_log_items":
                log_attrs["filtername"] = "ClearLogItems"
            elif devicename == "*" or devicename == '':
                log_attrs["filtername"] = "Initialize"
            elif devicename not in self.devicename_fname:
                log_attrs["filtername"] = "Unknown"
            else:
                log_attrs["filtername"] = self.devicename_fname[devicename]

            if devicename == 'clear_log_items':
                max_recds  = EVENT_LOG_CLEAR_CNT
                self.clear_secs = HIGH_INTEGER
                devicename = self.last_devicename
            else:
                max_recds = HIGH_INTEGER
                self.clear_secs = int(time.time()) + EVENT_LOG_CLEAR_SECS
                self.last_devicename = devicename

            #The state must change for the recds to be refreshed on the
            #Lovelace card. If the state does not change, the new information
            #is not displayed. Add the update time to make it unique.
            log_update_time = ( f"{dt_util.now().strftime('%a, %m/%d')}, "
                                f"{dt_util.now().strftime(Gb.um_time_strfmt)}")
            log_attrs["update_time"] = log_update_time
            sensor_state = (f"{devicename}:{log_update_time}")

            attr_recd = self._update_sensor_ic3_event_log_recds(devicename, max_recds)
            log_attrs["logs"] = attr_recd

            set_state_attributes(SENSOR_EVENT_LOG_ENTITY, sensor_state, log_attrs)

        except Exception as err:
            log_exception(err)

#------------------------------------------------------
    def export_event_log(self):
        '''
        Export Event Log to 'config/icloud_event_log.txt'.
        '''

        try:
            log_update_time =   (f"{dt_util.now().strftime('%a, %m/%d')}, "
                                f"{dt_util.now().strftime(Gb.um_time_strfmt)}")
            hdr_recd    = (f"Time\t\t   Event\n{'-'*115}\n")
            export_recd = (f"iCloud3 Event Log\n\n"
                            f"Log Update Time: {log_update_time}\n"
                            f"Tracked Devices:\n")

            for devicename, Device in Gb.Devices_by_devicename.items():
                export_recd += (f"\t{DOT}{Device.fname_devicename}\n")

            #Prepare Global '*' records. Reverse the list elements using [::-1] and make a string of the results
            export_recd += (f"\n\nSystem Events\n\n")
            export_recd += hdr_recd
            el_recds     = [el_recd for el_recd in self.event_log_table if (el_recd[0] == "*")]
            export_recd += self._export_ic3_event_log_reformat_recds('*', el_recds)

            #Prepare recds for each device. Each record is [devicename, time, text]
            # event_msg =(f"{EVLOG_TIME_RECD}{iosapp_state},{ic3_zone},{interval},{travel_time},{distance}")
            for devicename, Device in Gb.Devices_by_devicename.items():
                export_recd += (f"\n\n{Device.fname_devicename}\n\n")
                export_recd += hdr_recd

                el_recds     = [el_recd for el_recd in self.event_log_table \
                                if (el_recd[0] == devicename and el_recd[2] != "Device.Cnts")]
                export_recd += self._export_ic3_event_log_reformat_recds(devicename, el_recds)

            # ic3_directory = os.path.abspath(os.path.dirname(__file__))
            # # export_filename = (f"{Gb.icloud3_dir}/~icloud3_event_log-{datetime_now().replace(' ', '_')}.txt")
            # export_filename = (f"icloud3_event_log-{datetime_now().replace(' ', '_')}.txt")
            # export_filename = (f"{ic3_directory.split('custom_components')[0]}/{export_filename}.txt")
            # export_filename = export_filename.replace("//", "/")
            # # export_filename = Gb.icloud3_dir +


            # ic3_directory = os.path.abspath(os.path.dirname(__file__))
            # self.post_event(f"{datetime_now()=} {ic3_directory=} {Gb.icloud3_dir=}")
            datetime = datetime_now().replace('-', '.').replace(':', '.').replace(' ', '-')
            export_filename = (f"icloud3-event-log_{datetime}.txt")
            export_directory = (f"{Gb.icloud3_dir.split('custom_components')[0]}/{export_filename}")
            export_directory = export_directory.replace("//", "/")

            export_file = open(export_directory, "w")
            export_file.write(export_recd)
            export_file.close()

            self.post_event(f"iCloud3 Event Log Exported > {export_directory}")

        except Exception as err:
            log_exception(err)
##################################################################################
#
#   Support functions
#
###################################################################################
    def _insert_event_log_recd(self, event_recd):
        """Add the event recd into the event table"""

        if self.event_log_table is None:
            self.event_log_table = CONTROL_RECD

        try:
            while len(self.event_log_table) >= self.log_table_max_items:
                self.event_log_table.pop()
        except:
            pass

        self.event_log_table.insert(0, event_recd)

#------------------------------------------------------
    def _update_sensor_ic3_event_log_recds(self, devicename, max_recds=HIGH_INTEGER):
        '''
        Build the event items attribute for the event log sensor. Each item record
        is [device, time, state, zone, interval, travTime, dist, textMsg]
        Select the items for the device or '*' and return the string of
        the resulting list to be passed to the Event Log
        '''
        if devicename == "startup_log":
            devicename = "*"

        el_devicename_check=['*', devicename]

        if Gb.evlog_trk_monitors_flag:
            attr_recd = [el_recd[1:8] for el_recd in self.event_log_table \
                if el_recd[0] in el_devicename_check]

        elif devicename == "*":
            attr_recd = [el_recd[1:8] for el_recd in self.event_log_table \
                if ((el_recd[0] in el_devicename_check
                        or el_recd[2].startswith(EVLOG_ALERT))
                    and (el_recd[2].startswith(EVLOG_DEBUG) is False))]

        else:
            attr_recd = [el_recd[1:8] for el_recd in self.event_log_table \
                if (el_recd[0] in el_devicename_check
                    and el_recd[2].startswith(EVLOG_DEBUG) is False)]

        if max_recds == EVENT_LOG_CLEAR_CNT:
            recd_cnt = len(attr_recd)
            attr_recd = attr_recd[0:max_recds]

            refresh_msg = (f"{EVLOG_INIT_HDR}Click `Refresh` to display "
                           f"all records ({max_recds} of {recd_cnt} displayed)")
            refresh_recd = ['',refresh_msg]
            attr_recd.insert(0, refresh_recd)

        attr_recd.append(CONTROL_RECD)

        return str(attr_recd)

#--------------------------------------------------------------------
    def _export_ic3_event_log_reformat_recds(self, devicename, el_records):

        try:
            record_str = ''
            record_str2 = ''
            last_recd_home_zone_flag = False
            inside_home_det_interval_flag = False
            for record in el_records:
                devicename = record[0]
                time       = record[1]
                text       = record[2]

                # Time-record = {iosapp_state},{ic3_zone},{interval},{travel_time},{distance
                if time == '»Home' and inside_home_det_interval_flag:
                    block_char = '\t\t└─ '
                    inside_home_det_interval_flag = False
                elif time == '»Home' and inside_home_det_interval_flag is False:
                    block_char = '\t\t┌─ '
                    inside_home_det_interval_flag = True
                elif time.startswith('»') and text.startswith('^'):
                    block_char = '\t\t├─ '
                elif time.startswith('»'):
                    block_char = '\t\t│  '
                elif inside_home_det_interval_flag:
                    block_char = '\t│  '
                else:
                    block_char = '\t   '

                if text.startswith(EVLOG_TIME_RECD):
                    text = text[3:]
                    item = text.split(',')
                    text = (f"iOSAppState-{item[0]}, iCloud3Zone-{item[1]}, Interval-{item[2]}, TravelTime-{item[3]}, Distance-{item[4]}")

                text = text.replace("'", "")
                text = text.replace(CRLF, ", ").replace(CRLF_DOT, ", ").replace(CRLF_CHK, ", ")
                if text.startswith('^'):
                        text = text[3:]

                chunk_len = 95
                start_pos=0
                end_pos = chunk_len + 5
                while start_pos < len(text):
                    if start_pos == 0:
                        chunk = (f"{time}{block_char}{text[start_pos:end_pos]}\n")
                    elif time.startswith('»'):
                        chunk = (f"\t{block_char}\t\t{text[start_pos:end_pos]}\n")
                    else:
                        chunk= (f"\t\t{block_char}\t\t{text[start_pos:end_pos]}\n")
                    record_str += chunk
                    start_pos += end_pos
                    end_pos += chunk_len

            record_str += '\n\n'
            return record_str

        except Exception as err:
            log_exception(err)
