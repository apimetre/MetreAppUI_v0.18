import time
import datetime as datetime
from pytz import timezone
# Pythonista imports
import cb
import console
import Image
# Metre imports
from lib.ParamsDb import ParamsDb
from lib.ViewListView import ViewListView
from lib.LineBuffer import LineBuffer
from lib.PythonistaUartBleClient import PythonistaUartBleClient
from lib.FileConverter import FileConverter
from lib.UIFeatures import ConsoleAlert
# Global constants


class BleUploader():
    def __init__(self, progress_bar_, console_box_, ble_status_icon_, v_, version_id):
        self.progress_bar_ = progress_bar_
        self.console_box_ = console_box_
        self.ble_status_icon_ = ble_status_icon_
	@@ -42,6 +42,7 @@ def __init__(self, progress_bar_, console_box_, ble_status_icon_, v_, version_id
        self.DEBUG = False
        self.CONSOLE_WIDTH = 140
        self.INDENT_STR = '        '

        # Global variables
        self.in_buf =b''
	@@ -63,9 +64,10 @@ def __init__(self, progress_bar_, console_box_, ble_status_icon_, v_, version_id
        self.py_ble_uart = PythonistaUartBleClient('py_ble', self.event_queue,    self.PERIPHERAL_PREAMBLE, self.py_ble_buffer, DEBUG=self.DEBUG)

    def print_wrap(self, text, indent_str, len):
        lines = textwrap.wrap(text, width=len, subsequent_indent=indent_str)
        for line in lines:
            print(line)



	@@ -81,7 +83,8 @@ def execute_transfer(self):
        while not self.py_ble_uart.peripheral:
            if len(self.event_queue):
                event = self.event_queue.pop()
                print(f"event: {event}")
        if self.py_ble_uart.peripheral:
            self.console_box_.alpha =1
            self.console_box_.text = ("Connecting to MetreAce instrument")
	@@ -110,20 +113,16 @@ def calc_utc_offset(timeval):
            dt1 = datetime.datetime.fromtimestamp(timeval).astimezone(timezone(tz))
            dst_term_sec = is_dst(datetime.datetime(int(dt1.year), int(dt1.month), int(dt1.day)), tzone="US/Pacific")
            tz_factor = int(tz_dict[tz]) - dst_term_sec/3600
            print('THIS IS THE AMOUNT TO SUBTRACT from GMT interp in hours', tz_factor)
            return int(tz_factor)


        def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter = 0, warning = False, to_max = 80):
            global in_buf
            #print(f"json_text: {out_msg}")
            in_buf = (out_msg + '\n').encode('utf-8')
            #print(in_buf)

            while True:
                if self.py_ble_uart.peripheral:
                    #print('self.py_ble_uart.peripheral connection made')
                    #print(cmd_counter)
                    try:
                        if show_progress:
                            if self.progress_bar_.fillbar_.width < 0.8:
	@@ -133,24 +132,26 @@ def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter

                    # Sends commands to buffer
                        if len(in_buf):
                            print('the length of in_buff is ', len(in_buf))
                            in_chars = in_buf
                            self.py_ble_buffer.buffer(in_chars)
                            in_buf = ''
                        # if events then process them
                        while len(self.event_queue) and self.py_ble_uart.peripheral:
                            print('processing events')
                            event = self.event_queue.pop()

                            if 'post' in event:
                                response = json.loads(event['post'])
                                print('recieved event post')
                                if 'cmd' in response:
                                    try:
                                        self.py_ble_uart.write((event    ['post']+'\n').encode())
                                                            # print(f"event: {event}")
                                        self.print_wrap(f"event: {event}",   self.INDENT_STR, self.CONSOLE_WIDTH)
                                        print('sent a post cmd')

                                        continue
                                    except:
	@@ -159,20 +160,23 @@ def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter

                                else:


                                    print('cmd not in post')
                                    try:
                                        print('printing event response')
                                        self.print_wrap(f"event: {response}",    self.INDENT_STR, self.CONSOLE_WIDTH)
                                        if cmd_type in response['ack']:
                                            return response['resp'], cmd_counter
                                        else:
                                            continue
                                    except:
                                        print('could not get event response')
                                        continue
                            else:
                                print('No post in event')
                                self.print_wrap(f"event: {event}", self.INDENT_STR,   self.CONSOLE_WIDTH)


	@@ -183,7 +187,8 @@ def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter
                    time.sleep(0.2)
                    cmd_counter = cmd_counter + 1
                    to_counter = to_counter + 1
                    print('cmd_counter', cmd_counter)
                    if warning and to_counter > to_max:
                        self.console_box_.text = "Ooops. MetreAce needs to be restarted. \n Eject mouthpiece, close the phone app, and try again"
                        break
	@@ -197,7 +202,8 @@ def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter
        if self.py_ble_uart.peripheral:
            self.v_['ble_status'].text = 'Connected'
            self.console_box_.text = "Connected"
            print('will be using ' + self.cwd + '/data_files/dat_files/ as current working directory for writing log files')
            global counter
            counter = 0
            time.sleep(0.2)
	@@ -262,20 +268,24 @@ def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter

                timeout_counter = 1
                if file.startswith('._'):
                    print('I SEE ' + file)
                    out_msg_del_e =json.dumps({"cmd": "remove", "path":     "/sd/" + file})
                    r_del, counter = cmd_fn(out_msg_del_e, "remove", show_progress = False, warning = True, to_max = 150)
                elif file.endswith(('.bin', '.json')):
                    if "device" in file:
                        print('I SEE ' + file)
                        print('Skipping over ' + file)
                        continue
                    elif "params" in file:
                        print('I SEE ' + file)
                        print('Skipping over ' + file)
                        continue
                    else:
                        print('I SEE ' + file)
                        file_ix = list_of_dirs.index(file)
                        file_size = file_sizes[file_ix]
                        try:
	@@ -321,17 +331,15 @@ def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter
                                                        result_resp.append(str(response['ack']))
                                                        self.print_wrap(f"ack_event: {response}",   self.INDENT_STR, self.CONSOLE_WIDTH)
                                                else:
                                                    print("RESPONSE IS NOT OKAY")
                                                    break
                                        except:
                                            # This is where you need to fix the alert in case there is NOT a ble issue---but maybe break explicitly
                                            #self.console_box_.text = "Ooops. MetreAce needs to be restarted. \n Eject mouthpiece, close the phone app, and try again"
                                            # self.py_ble_uart.peripheral = False
                                            pass
                                            #break

                                    else:
                                        print(str(event))
                                        #response = json.loads(str(event))
                                        if event['ok']:
                                           self.print_wrap(f"event: {event}",   self.INDENT_STR, self.CONSOLE_WIDTH)
	@@ -354,37 +362,41 @@ def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter
                                break

                            if "{'file_path': './result.bin'}" in result_resp:
                                print('ENTERING TRANSFER AND REMOVAL ATTEMPT')

                                try:
                                    shutil.move('./result.bin', self.base_dir + '/data_files/uploaded_files/' + file)
                                    upload_size = os.stat(self.base_dir + '/data_files/uploaded_files/' + file)[6]
                                    print('Sent move command')
                                    if upload_size == file_size:
                                        print('upload and file size are the same size')
                                        out_msg_del =json.dumps({"cmd": "remove", "path":"/sd/" + file})
                                        r_del, counter = cmd_fn(out_msg_del, "remove", show_progress = True, cmd_counter = counter, warning = True)      
                                        print('Sent remove command here')
                                    else:
                                        print('FILE IS THE WRONG SIZE')
                                        size_diff = file_size - upload_size
                                        file_wrongsize.append(file)
                                        file_wrongsize.append(size_diff)
                                        out_msg_del =json.dumps({"cmd": "remove", "path":"/sd/" + file})
                                        r_del, counter = cmd_fn(out_msg_del, "remove", show_progress = True, cmd_counter = counter, warning = True)
                                    print('Got past else statement')

                                    if file.endswith('bin'):
                                        counter = counter + 1
                                        self.progress_bar_.update_progress_bar(counter*.002)
                                        #continue
                                        break  #Was originally break
                                        # No break and no continue makes it exit and not remove the bin file
                                    elif file.endswith('json'):
                                        pass

                                except:
                                    print('BROKE OUT OF TRANSFER AND REMOVAL ATTEMPT')
                                    break
                        if FLAG:
                           counter = 0
	@@ -396,10 +408,9 @@ def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter
            # Now use FileConverter
            fc = FileConverter(self.progress_bar_, self.console_box_, file_wrongsize)
            cwd = os.getcwd()
            print('THIS IS THE CURRENT DIR')
            print(cwd)
            print('THIS IS SELF.BASEDIR')
            print(self.base_dir)

            conversion_status = fc.match_files(self.base_dir + '/data_files/uploaded_files', self.base_dir + '/data_files/processed_files', self.base_dir + '/data_files/converted_files', self.base_dir + '/data_files/unpaired_files')
            self.console_box_.text = 'Transfer of ' + str(len(file_list)) + ' out of ' + str(len(file_list)) + ' test files complete'
	@@ -411,22 +422,19 @@ def cmd_fn(out_msg, cmd_type, show_progress = False, cmd_counter = 0, to_counter
                out_msg_txt =json.dumps({"cmd":"set_ble_state","active":False})
                cmd_fn(out_msg_txt, "set_ble_state", show_progress = False, to_max = 10)
            except:
                print('could not send disconnect command')

            #out_msg_tone =json.dumps({"cmd": "avr", "payload": { "cmd": "tone", "freq":"1000", "duration":"1000" }})
            #cmd_fn(out_msg_tone, show_progress = False)

            self.console_box_.text = 'Disconnecting from MetreAce Instrument'
            #outmsg_s0 = json.dumps({'cmd':'avr', 'payload':{ "cmd": "sensors", "rep_ms":0, "smpl_ms":0, "n":1 }})
            #cmd_fn(outmsg_s0, show_progress = False)

            #outmsg_t0 = json.dumps({'cmd':'avr', 'payload':{ "cmd": "thermistor", "rep_ms":0, "smpl_ms":0, "n":1 }})
            #cmd_fn(outmsg_t0, show_progress = False)
            try:          
                out_msg2 =json.dumps({"cmd": "disconnect_ble"})
                rstring, no_counter = cmd_fn(out_msg2, "disconnect_ble", show_progress = True, to_max = 10)
            except:
                print('could not send disconnect command')
            ConsoleAlert('Remove Mouthpiece!', self.v_)
            ble_icon_path = 'images/ble_off.png'
            self.ble_status_icon_.image = ui.Image.named(ble_icon_path)
