# Python imports
import os
import numpy as np
import datetime as datetime
import time
from pytz import timezone

# Pythonista imports
import ui

class ResultsTable(object):
	def __init__(self, subview_, table_, ac_res, etime_res):
		self.subview = subview_
		self.table = table_
		self.etime = etime_res
		self.ac = ac_res
		results = []
		dt_string = self.etime.strftime("%b %d, %Y, %I:%M %p")
		for i in self.ac:
			results.append(dt_string[np.where(self.ac == self.ac[i])] + '     ' + round(self.ac[i]), 1) + ' ppm')
		self.table_items = results        
		self.list_source = ui.ListDataSource(self.table_items)
		self.table.data_source = self.list_source
