# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr

clr.AddReference("System")
from System.ComponentModel import INotifyPropertyChanged
from System.ComponentModel import PropertyChangedEventArgs

# ===============
# ---> CLASSES <---
class ViewModelBase(INotifyPropertyChanged):
	def __init__(self):
		super(ViewModelBase,self).__init__()
		self.propertyChangedEventHandler = []		# This is the PropertyChangedEventHandler

	def OnPropertyChanged(self, property_name):
		args = PropertyChangedEventArgs(property_name)
		for handler in self.propertyChangedEventHandler:
			handler(self, args)

	def add_PropertyChanged(self, handler):
		self.propertyChangedEventHandler.append(handler)	# adding to list

	def remove_PropertyChanged(self, handler):
		self.propertyChangedEventHandler.remove(handler)	# removing from list