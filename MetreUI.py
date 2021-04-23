## Python imports
import os
import requests
import shutil
import numpy as np
from io import BytesIO
import datetime as datetime
import time
from pytz import timezone
import json
import threading
import fnmatch
import pprint
import math
from functools import partial
import itertools
import matplotlib.pyplot as plt
from matplotlib.dates import num2date, date2num, num2epoch

# Pythonista imports
import ui
import Image
import console
from objc_util import on_main_thread


# Metre imports
import process_test
from ble_file_uploader import BleUploader
from lib.UISummaryDelegate import SummaryDelegate
from lib.UIBleDelegate import BleDelegate, BokehDelegate, loading_html, updating_html, nolog_html, getPlot
from lib.UIHelpDelegate import HelpDelegate
from lib.UIFeatures import ProgressBar, ConsoleAlert
from app_single_launch import AppSingleLaunch

# Using single launch lock as suggested in
# https://forum.omz-software.com/topic/5440/prevent-duplicate-launch-from-shortcut/7

APP_VERSION = 'v0.18'



class MainView(ui.View):
    def __init__(self):
    #def __init__(self, app: AppSingleLaunch):
        #self.app = app
        self.name = "MetreAce_Home"
        self.flex = 'WH'
        #self.tint_color = '#494949'
        self.background_color = 'black'
        
        # Setup of UI Features
        
        self.v = ui.load_view('mainview')
        self.v.frame = self.bounds
        self.v.flex = 'WH'
        
        # Console
        self.app_console = self.v['console']
        self.app_console.alpha = 0
       
        
        # Ble connection
        self.start_button = self.v['start_button']
        self.ble_icon = self.v['ble_icon']
        self.ble_status_icon = self.v['ble_status_icon']
        self.ble_status = self.v['ble_status']
        ble_icon_path = 'images/ble_off.png'
        self.ble_status_icon.image = ui.Image.named(ble_icon_path)
                
        # Status bar
        self.fillbar = self.v['fill_bar']
        self.fillbar_outline = self.v['background']
        self.fillbar.x = 31.1
        self.fullbar = self.fillbar_outline.width
        
        # Version label
        self.vlabel = self.v['vlabel']
        self.vlabel.text = APP_VERSION
        
        # Setup
        self.cwd = os.getcwd()
        on_main_thread(console.set_idle_timer_disabled)(True)
        
        # Download Single Launch Lock if it's not already installed
        print(self.cwd)
        root_dir, metre_dir = self.cwd.split('MetreiOS')
        print(root_dir)
        check_path = root_dir + 'site-packages/single_launch.lock'
        if os.path.exists(check_path):
        	print('path already exists')
        else:
        	shutil.copy(self.cwd + '/resources/single_launch.lock', check_path )
        	print('moved')

        
        # Set up UI Functions
        self.getData()
        self.start_button.action = self.bleStatus
        self.add_subview(self.v)
        
        # Implementation of navigation view/mainview
        self.l = self.create_l_buttonItems('Settings','|','Results','|', 'Help')
        self.left_button_items = self.l
        self.files_to_upload = os.listdir('data_files/converted_files/')

        # Process pre-uploaded tests (if available)
        if len(self.files_to_upload) >=2:
            self.start_button.alpha = 0.5
            self.ble_status.text = ''
            self.main()  
        else:
            #self.app_console.text = 'Once MetreAce reads "UPLOAD rdy", push CONNECT (above) to initiate data transfer from MetreAce'
            self.ble_status.text = 'CONNECT'
        
        
    def will_close(self) -> None:
        self.app.will_close()

    # This sets up main navigation view

    def button_nav(self, sender):
        def connect(a,b):
            
            if sender.title == a:
                view_to_push = b
                pushed_view = ui.load_view(view_to_push)
                self.v.navigation_view.push_view(pushed_view)
                    
                if sender.title=='Settings':
                    settings_page = pushed_view['view1']
                    s_table=settings_page['tableview1']
                    d_table = settings_page['dt_table']
                    ble_delegate = BleDelegate(settings_page, s_table, d_table, self.cwd)
                    
                if sender.title=='Results':
                    results_page = pushed_view['bokeh_bg']
                    bview = ui.load_view('bokehview')
                    self.add_subview(bview)
                    bokeh_delegate = BokehDelegate(bview['webview1'], self.cwd)

                if sender.title =='Help':
                    help_page = pushed_view['toolbarview']
                    #hview = ui.load_view('toolbar')
                    #self.add_subview(hview)
                    inst_page = help_page['online_instructions']
                    qa_page = help_page['online_qa']
                    recover_page = help_page['recover_button']
                    help_delegate = HelpDelegate(hview, inst_page, qa_page, recover_page)
                    #hview.present()
                    
        connect('Settings','file_view')
        connect('Help','toolbar')
        connect('Results','bokehview')


    def create_l_buttonItems(self, *buttons):
        items=[]
        for b in buttons:
            b=ui.ButtonItem(b)
            b.tint_color='#494949'
            b.action= self.button_nav
            items.append(b)
        return items

# This sets up the bluetooth upload
    @ui.in_background
    def bleStatus(self, sender):
        self.progress_bar = ProgressBar(self.fillbar, self.fillbar_outline, self.fullbar)
        self.start_button.alpha = 0.5
        self.progress_bar.fillbar_outline_.alpha = 1
        self.fillbar.alpha = 1
        loaded = False
    
        if not loaded:
            self.ble_status.text= 'Connecting...'
            ble_file_uploader = BleUploader(self.progress_bar, self.app_console, self.ble_status_icon, self.v, APP_VERSION)
            ready_status = ble_file_uploader.execute_transfer()
            
            if ready_status:
                done = True
                self.start_button.alpha = 0.25
                self.ble_status.text = ''
                
                
                # HERE is where you trigger the main function (i.e. after the button is pushed)
                self.main()
                self.start_button.alpha = 1
                return done
            else:
                self.app_console.text = 'No breath tests are ready to be processed'
                if ble_file_uploader.py_ble_uart.peripheral:
                    ble_file_uploader.py_ble_uart.peripheral = False
                    self.ble_icon_path = 'images/ble_off.png'
                    self.ble_status_icon.image = ui.Image.named(ble_icon_path)
                    self.ble_status.text= 'CONNECT'
                    self.start_button.alpha = 1
                    self.progress_bar.fillbar_outline_.alpha = 0
                    self.fillbar.alpha = 0
                else:
                    print("UI senses it is disconnected")
                    time.sleep(0.5)
                    self.app_console.text = 'Bluetooth connection lost. Reinsert mouthpiece to try again'
                    self.ble_icon_path = 'images/ble_off.png'
                    self.ble_status_icon.image = ui.Image.named(ble_icon_path)
                    self.ble_status_icon.background_color = 'black'
                    self.ble_status.text= 'CONNECT'
                    self.start_button.alpha = 1
                    self.progress_bar.fillbar_outline_.alpha = 0
                    self.fillbar.alpha = 0
            
        else:
            self.ble_icon_path = 'images/ble_disconnected.png'
            ble_icon.image = ui.Image.named(ble_icon_path)
            return done
        
    
    def getData(self):
        
        with open('log/log_003.json') as json_file:
            self.log = json.load(json_file)
        self.etime = []
        self.weektime = []
        for val in self.log['Etime']:
                tval = datetime.datetime.fromtimestamp(int(val))
                year, weeknum = tval.strftime("%Y-%U").split('-')
                weekcalc = str(year) + '-W' + str(weeknum)
                day_of_week = datetime.datetime.strptime(weekcalc + '-1', "%Y-W%W-%w")
                self.weektime.append(day_of_week)
                self.etime.append(tval)
        self.acetone = np.array(self.log['Acetone'])
        dtDateTime = []
        for i in range(0, len(self.log['DateTime'])):
            dtDateTime.append(datetime.datetime.strptime(self.log['DateTime'][i], '%Y-%m-%d %H:%M:%S'))
        vectorized = []
    
        for i in range(0, len(self.acetone)):
                vectorized.append([self.weektime[i], self.acetone[i], dtDateTime[i]])
                self.varray = np.array(vectorized)
        if len(self.acetone) <=0:
            self.varray = []
        
    
    # Command for larger Bokeh plot pop-up
    def popUpView(self,sender):
        try:
            url = 'https://us-central1-metre3-1600021174892.cloudfunctions.net/get_bokeh'
            newWindow = ui.WebView()
            newWindow.load_html(loading_html)
            logData = json.dumps(self.log)
            try:
                tzData = json.loads('log/timezone_settings.json')
            except:
                tzData = json.dumps({'timezone': 'US/Pacific'})
            response = requests.post(url, files = [('json_file', ('log.json', logData, 'application/json')), ('tz_info', ('tz.json', tzData, 'application/json'))])
            
            newWindow.load_html(response.text)
            newWindow.present()
        except:
            newWindow.load_html(nolog_html)

    ########################################
    
    def main(self):
                                            
        self.main_progress_bar =ProgressBar(self.fillbar, self.fillbar_outline, self.fullbar)
        global process_done
        process_done = False
        def animate_bar(self):
            cloud_progress_bar = ProgressBar(self.fillbar, self.fillbar_outline, self.fullbar)
            for i in range(0, 100):
                if process_done:
                    break
                cloud_progress_bar.update_progress_bar(0.005*i + 0.15)
                print(i)
                time.sleep(0.5)

    
        source_path = self.cwd + '/data_files/converted_files/'
        all_src_files = os.listdir(source_path)
        files = []
        for file in all_src_files:
            if ".gitkeep" not in file:
                files.append(file)
        print("these are the files")
        print(files)
        numOfFiles = len(files)
        if numOfFiles >1:
               self.app_console.text = str(numOfFiles-1) + ' breath tests are ready to be processed. Beginning data processing...'
        elif numOfFiles == 1:
               self.app_console.text = '1 breath test is ready to be processed. Beginning data processing...'
        else:
               self.app_console.text = 'No breath tests are ready to be processed at this time'
        time.sleep(3)
        
        try:
            with open('log/timezone_settings.json') as f:
                tzsource = json.loads(f)
                tz = 'US/Pacific'
        
        
        except:
                tz = 'US/Pacific'
        
        for file in files:
               if fnmatch.fnmatch(file, '*.json'):
    
                   dt = datetime.datetime.fromtimestamp(int(file.split('-')[0])).astimezone(timezone(tz)).strftime('%b %d, %Y, %I:%M %p')
                   print('Beginning Analysis of test from ' + dt)
                   json_path = source_path + '/'+ file
                   self.main_progress_bar.update_progress_bar(0)
                   process_done = False
                   with open(json_path) as f:
                       data_dict = json.load(f)
                   data_dict_to_send = process_test.process(data_dict, dt)
                   url = 'https://us-central1-metre3-1600021174892.cloudfunctions.net/metre-7500'
                   data_dict_to_send['App_Version'] = APP_VERSION
                   json_text = json.dumps(data_dict_to_send)
                   self.main_progress_bar.update_progress_bar(0.1)
                   self.app_console.text = 'Interpretting results from test from ' + dt +'. This may take a few moments...'
                   pt = threading.Thread(target = animate_bar) # don't do this unless u start a parallel thread to send request
                   pt.start()
    
                   print('sending to cloud')
                   start = time.time()
                   response = requests.post(url, files = [('json_file', ('test.json', json_text, 'application/json'))])
                   #pt.join()
                   process_done = True
                   elapsedtime = time.time()-start
                   print('received response--response time ' + str(elapsedtime))
                   response_json = json.loads(response.text)
                   pt.join()
                   process_done = True
                   try:
                       app_console.text = 'Results from ' + dt + ': ' + response_json['pred_content']
                       print(response_json['pred_content'])
                       self.main_progress_bar.update_progress_bar(0.92)
                       newlog = {'Etime': response_json['refnum'],
                                  'DateTime': response_json['DateTime'],
                                  'Acetone': float(response_json['Acetone']),
                                  'Sensor': response_json['sensor'],
                                  'Instr': response_json['instrument']}
                       for key, value in self.log.items():
                          self.log[key].append(newlog[key])
                       with open("log/log_003.json", "w") as outfile:
                          json.dump(self.log, outfile)
                       self.getData()
                                            
                       ########################### 
                                            
                       #testdate_box.text = max(self.etime).strftime("%b %d, %Y, %I:%M %p")
                                            
                       #if self.acval[self.etime.index(max(self.etime))] <2:
                       #   res_string = "<2 ppm"
                       #else:
                       #   res_string = str(round(acval[etime.index(max(etime))],2)) + ' ppm'
                       #testres_box.text = res_string
                        #getPlot(bokeh_view, cwd, initial = False)
                                            
                       self.main_progress_bar.update_progress_bar(0.95)
                       
                       main_progress_bar.update_progress_bar(0.97)
                                            
                       #### UPDATE TABLE HERE
                       
                       main_progress_bar.update_progress_bar(1)
                   except:
                       app_console.text = 'Oops...something was wrong with the test from ' + dt + ' and it could not be processed'
                   time.sleep(1)
                   shutil.move(source_path + file, cwd +'/data_files/processed_files/' + file)
               else:
                   pass
               time.sleep(1)
                                        
        self.fillbar.alpha =0
        self.fillbar_outline.alpha = 0
        self.main_progress_bar.update_progress_bar(0)
                                            
        self.app_console.text = 'Test Processing and Upload Complete.'
        time.sleep(3)
        self.start_button.alpha = 1
        self.ble_status.text = 'CONNECT'


class NavView(ui.View):
    def __init__(self, app: AppSingleLaunch):
        self.app = app
        self.tint_color =  '#494949'  
        self.name = "MetreAce Nav"
        self.flex = 'WH'
        self.nav = ui.NavigationView(MainView())

if __name__ == '__main__':
    app = AppSingleLaunch("MetreAce Nav")
    if not app.is_active():
        nav_view = NavView(app).nav
        nav_view.tint_color =  '#494949'                                   
        app.will_present(nav_view)
        nav_view.present()
