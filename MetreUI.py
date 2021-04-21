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
from app_single_launch import AppSingleLaunch

# Using single launch lock as suggested in
# https://forum.omz-software.com/topic/5440/prevent-duplicate-launch-from-shortcut/7


class MainView(ui.View):
    def __init__(self, app: AppSingleLaunch):
        self.app = app
        self.name = "MetreAce Home"
        self.flex = 'WH'
        self.background_color = 'black'
        self.add_subview(ui.TextField(
            width=200,
            height=30,
            placeholder="Type some text"))

    def will_close(self) -> None:
        self.app.will_close()


if __name__ == '__main__':
    app = AppSingleLaunch("MetreAce Home")
    if not app.is_active():
        view = MainView(app)
        app.will_present(view)
        view.present()
