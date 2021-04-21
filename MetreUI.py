# Python imports
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
from lib.UIBleDelegate import BleDelegate, loading_html, updating_html, nolog_html, getPlot
from lib.UIHelpDelegate import HelpDelegate
from lib.UIFeatures import ProgressBar, ConsoleAlert


APP_VERSION = 'v0.18'

# SETUP
m = ui.View('Sheet')
m.name='MetreAce Home'
m.background_color='black'
t = ui.TextView()
t.width=768
t.height=768
t.font=('Avenir Light',16)
t.text = 'Placeholder text'
v = ui.load_view('mainview')
v.frame = m.bounds
v.flex = 'WH'

#v setup
ble_status = v['ble_status']
ble_icon = v['ble_icon']
icon_header = v['icon_header']
vbutton = v['vbutton']
start_button = v['start_button']
fillbar = v['fill_bar']
fillbar_outline = v['background']
fillbar.x = 31.1

fullbar = fillbar_outline.width
app_console = v['console']
app_console.text_color= '#fff0f0'
vlabel = v['vlabel']
bokeh_view = v['bokeh_view']

testdate_box = v['testdate_view']
testres_box = v['testres_view']

ble_status_icon = v['ble_status_icon']


cwd = os.getcwd()


# This sets up main navigation view

def button_nav(sender):
    def connect(a,b):
        cwd = os.getcwd()
        if sender.title == a:
            view_to_push = b
            pushed_view = ui.load_view(view_to_push)
            v.navigation_view.push_view(pushed_view)
        
            if sender.title == 'Summaries':
                summaryview = pushed_view['sview']
                dailyview = pushed_view['daily_view']
                weeklyview = pushed_view['weekly_view']
                summary_delegate = SummaryDelegate(summaryview, dailyview, weeklyview, cwd)
                
            if sender.title=='Settings':
                settings_page = pushed_view['view1']
                s_table=settings_page['tableview1']
                d_table = settings_page['dt_table']
                ble_delegate = BleDelegate(settings_page, s_table, d_table, cwd, bokeh_view)
                
            if sender.title =='Help':
                
                help_page = pushed_view['toolbarview']
                
                hview = ui.load_view('toolbar')
                m.add_subview(hview)
                inst_page = hview['online_instructions']
                qa_page = hview['online_qa']
                recover_page = hview['recover_button']
                help_delegate = HelpDelegate(hview, inst_page, qa_page, recover_page)
                hview.present()
  
    
    connect('Settings','file_view')
    connect('Help','toolbar')
    #connect('Tools','toolbar')
    connect('Summaries','summaries_view')


def create_l_buttonItems(*buttons):
    items=[]
    for b in buttons:
        b=ui.ButtonItem(b)
        b.tint_color='#494949'
        b.action= button_nav
        items.append(b)
    return items

# This sets up the bluetooth upload
@ui.in_background
def bleStatus(sender):
    progress_bar = ProgressBar(fillbar, fillbar_outline, fullbar)
    start_button.alpha = 0.5
    progress_bar.fillbar_outline_.alpha = 1
    fillbar.alpha = 1
    loaded = False

    if not loaded:
        #ble_icon_path = 'images/ble_disconnected.png'
        ble_status.text= 'Connecting...'
        #ble_icon.image = ui.Image.named(ble_icon_path)

        ble_file_uploader = BleUploader(progress_bar, app_console, ble_status_icon, v, APP_VERSION)
        ready_status = ble_file_uploader.execute_transfer()
        
        if ready_status:
            done = True
            start_button.alpha = 0.25
            ble_status.text = ''
            
            
            # HERE is where you trigger the main function (i.e. after the button is pushed)
            main(app_console, log)
            start_button.alpha = 1
            return done
        else:
            app_console.text = 'No breath tests are ready to be processed'
            if ble_file_uploader.py_ble_uart.peripheral:
                ble_file_uploader.py_ble_uart.peripheral = False
                ble_icon_path = 'images/ble_off.png'
                ble_status_icon.image = ui.Image.named(ble_icon_path)
                ble_status.text= 'CONNECT'
                start_button.alpha = 1
                progress_bar.fillbar_outline_.alpha = 0
                fillbar.alpha = 0
            else:
                print("UI senses it is disconnected")
                time.sleep(0.5)
                app_console.text = 'Bluetooth connection lost. Reinsert mouthpiece to try again'
                ble_icon_path = 'images/ble_off.png'
                ble_status_icon.image = ui.Image.named(ble_icon_path)
                ble_status_icon.background_color = 'black'
                ble_status.text= 'CONNECT'
                start_button.alpha = 1
                progress_bar.fillbar_outline_.alpha = 0
                fillbar.alpha = 0
        
    else:
        ble_icon_path = 'images/ble_disconnected.png'
        #ble_status.text= 'connected'
        ble_icon.image = ui.Image.named(ble_icon_path)
        return done
    

def getData():
    global etime, weektime
    with open('log/log_003.json') as json_file:
        log = json.load(json_file)
    etime = []
    weektime = []
    for val in log['Etime']:
            tval = datetime.datetime.fromtimestamp(int(val))
            year, weeknum = tval.strftime("%Y-%U").split('-')
            weekcalc = str(year) + '-W' + str(weeknum)
            day_of_week = datetime.datetime.strptime(weekcalc + '-1', "%Y-W%W-%w")
            weektime.append(day_of_week)
            etime.append(tval)
    acetone = np.array(log['Acetone'])
    dtDateTime = []
    for i in range(0, len(log['DateTime'])):
        dtDateTime.append(datetime.datetime.strptime(log['DateTime'][i], '%Y-%m-%d %H:%M:%S'))
    vectorized = []

    for i in range(0, len(acetone)):
            vectorized.append([weektime[i], acetone[i], dtDateTime[i]])
            varray = np.array(vectorized)
    if len(acetone) <=0:
        varray = []
    return acetone, etime, weektime, varray, log

# Command for larger Bokeh plot pop-up
def popUpView(sender):
    try:
        url = 'https://us-central1-metre3-1600021174892.cloudfunctions.net/get_bokeh'
        newWindow = ui.WebView()
        newWindow.load_html(loading_html)
        logData = json.dumps(log)
        try:
            tzData = json.loads('log/timezone_settings.json')
        except:
            tzData = json.dumps({'timezone': 'US/Pacific'})
        response = requests.post(url, files = [('json_file', ('log.json', logData, 'application/json')), ('tz_info', ('tz.json', tzData, 'application/json'))])
        
        newWindow.load_html(response.text)
        newWindow.present()
    except:
        newWindow.load_html(nolog_html)
    

############### START MAIN CODE HERE #######################
start_button.alpha = 0.25
on_main_thread(console.set_idle_timer_disabled)(True)
vlabel.text = APP_VERSION
#ConsoleAlert('Insert mouthpiece to connect your MetreAce and follow the instructions on the MetreAce display. CONNECT once MetreAce readys "UPLOAD rdy', v)

global etime, acval, weektime, varray
global log
acval, etime, weektime, varray, log = getData()
getPlot(bokeh_view, cwd)
vbutton.alpha = 1
vbutton.action = popUpView

start_button.alpha = 1
start_button.action = bleStatus
app_console.text = 'Once MetreAce reads "UPLOAD rdy", push CONNECT (above) to initiate data transfer from MetreAce'
ble_status.text = 'CONNECT'
ble_icon_path = 'images/ble_off.png'
ble_status_icon.image = ui.Image.named(ble_icon_path)
try:
    testdate_box.text = max(etime).strftime("%b %d, %Y, %I:%M %p")
    if acval[etime.index(max(etime))] <2:
        res_string = "<2 ppm"
    else:
        res_string = str(round(acval[etime.index(max(etime))],2)) + ' ppm'
    testres_box.text = res_string
except:
    testdate_box.text = "No data yet"
    testres_box.text = "No data yet"
files_to_upload = os.listdir('data_files/converted_files/')

def main(app_console, log):
    main_progress_bar =ProgressBar(fillbar, fillbar_outline, fullbar)
    global process_done, t
    process_done = False
    def animate_bar():
        cloud_progress_bar = ProgressBar(fillbar, fillbar_outline, fullbar)
        for i in range(0, 100):
            if process_done:
                break
            cloud_progress_bar.update_progress_bar(0.005*i + 0.15)
            print(i)
            time.sleep(0.5)
    print('CWD FROM MAIN IS ')
    print(cwd)

    source_path = cwd + '/data_files/converted_files/'
    all_src_files = os.listdir(source_path)
    files = []
    for file in all_src_files:
        if ".gitkeep" not in file:
            files.append(file)
    print("these are the files")
    print(files)
    numOfFiles = len(files)
    if numOfFiles >1:
           app_console.text = str(numOfFiles-1) + ' breath tests are ready to be processed. Beginning data processing...'
    elif numOfFiles == 1:
           app_console.text = '1 breath test is ready to be processed. Beginning data processing...'
    else:
           app_console.text = 'No breath tests are ready to be processed at this time'
    time.sleep(1)
    
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
               main_progress_bar.update_progress_bar(0)
               process_done = False
               with open(json_path) as f:
                   data_dict = json.load(f)
               data_dict_to_send = process_test.process(data_dict, dt)
               url = 'https://us-central1-metre3-1600021174892.cloudfunctions.net/metre-7500'
               data_dict_to_send['App_Version'] = APP_VERSION
               json_text = json.dumps(data_dict_to_send)
               main_progress_bar.update_progress_bar(0.1)
               app_console.text = 'Interpretting results from test from ' + dt +'. This may take a few moments...'
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
                   main_progress_bar.update_progress_bar(0.92)
                   newlog = {'Etime': response_json['refnum'],
                              'DateTime': response_json['DateTime'],
                             
    ##################   Will need to remove this factor once you have working ML model!    ##################
                              'Acetone': float(response_json['Acetone']),
                              'Sensor': response_json['sensor'],
                              'Instr': response_json['instrument']}
                   for key, value in log.items():
                      log[key].append(newlog[key])
                   with open("log/log_003.json", "w") as outfile:
                      json.dump(log, outfile)
                   acval, etime, weektime, varray, log = getData()
                   testdate_box.text = max(etime).strftime("%b %d, %Y, %I:%M %p")
                   if acval[etime.index(max(etime))] <2:
                      res_string = "<2 ppm"
                   else:
                      res_string = str(round(acval[etime.index(max(etime))],2)) + ' ppm'
                   testres_box.text = res_string
                   main_progress_bar.update_progress_bar(0.95)
                   getPlot(bokeh_view, cwd, initial = False)
                   main_progress_bar.update_progress_bar(0.97)
                   main_progress_bar.update_progress_bar(0.99)
                   main_progress_bar.update_progress_bar(1)
               except:
                   app_console.text = 'Oops...something was wrong with the test from ' + dt + ' and it could not be processed'
               time.sleep(1)
               shutil.move(source_path + file, cwd +'/data_files/processed_files/' + file)
           else:
               pass
           time.sleep(1)
    fillbar.alpha =0
    fillbar_outline.alpha = 0
    main_progress_bar.update_progress_bar(0)
    start_button.alpha = 1
    ble_status.text = 'CONNECT'
    time.sleep(1)
    app_console.text = 'Test Processing and Upload Complete.'
m.tint_color = '#494949'

m.add_subview(v)

# Implementation of navigation view/mainview
l = create_l_buttonItems('Settings','|','Summaries','|', 'Help')
m.left_button_items = l

nav = ui.NavigationView(m)

nav.tint_color = '#494949'
nav.present()
if len(files_to_upload) >=2:
    start_button.alpha = 0.5
    ble_status.text = ''
    main(app_console, log)

    
else:
    app_console.text = 'Once MetreAce reads "UPLOAD rdy", push CONNECT (above) to initiate data transfer from MetreAce'
    ble_status.text = 'CONNECT'
