# Python imports
import os
import numpy as np
import datetime as datetime
import time
from pytz import timezone

# Pythonista imports
import ui


class ResultsTable(object):
	def __init__(self, subview_, table_, data_array):
		self.subview = subview_
		self.table = table_
		self.table_items = data_array
		self.list_source = ui.ListDataSource(self.table_items)
		self.table.data_source = self.list_source
#		self.table.delegate.action = self.select_device
#		
#		self.dt_table = dt_table_
#		self.dt_table_items = ['US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific', 'US/Alaska', 'US/Hawaii']
#		self.dt_source = ui.ListDataSource(self.dt_table_items)
#		self.dt_table.data_source = self.dt_source
#		self.dt_table.delegate.action = self.select_time
#		
#		self.cwd_ = cwd_
#		
#		self.selector = ui.Button(title = 'Choose a device to pair', action = self.save_device)
#		self.selector.y = self.table.y - 30
#		self.selector.x = self.table.x - 10
#		self.selector.alignment = ui.ALIGN_LEFT
#		self.subview.add_subview(self.selector)
#		
#		self.time_selector = ui.Button(title = 'Choose a timezone ', action = self.save_time)
#		self.time_selector.y = self.dt_table.y - 30
#		self.time_selector.x = self.dt_table.x - 10
#		self.time_selector.alignment = ui.ALIGN_LEFT
#		self.subview.add_subview(self.time_selector)
#		
#		
#		self.current_device = ui.Label(text = self.fetch_value('dev'), font =('Arial-ItalicMT', 12))
#		self.current_device.x = self.table.x + 10
#		self.current_device.y = self.table.x + self.table.height -10
#		self.current_device.width = self.table.width + 150
#		self.subview.add_subview(self.current_device)
#		self.current_tz = ui.Label(text = self.fetch_value('tz'), font = ('Arial-ItalicMT', 12))
#		self.current_tz.x = self.dt_table.x + 10
#		self.current_tz.y = self.dt_table.y + self.dt_table.height-55
#		self.current_tz.width = self.dt_table.width + 150
#		self.subview.add_subview(self.current_tz)
#		
#	def select_device(self, sender):
#		self.selection = self.list_source.items[sender.selected_row]
#		print(self.selection)
#		self.selector.title = 'Save Device' 
#		self.selector.bg_color = 'orange'
#		self.current_device.text = 'Change default device to ' + str(self.selection) + ' ?'
