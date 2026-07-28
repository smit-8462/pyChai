# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr

clr.AddReference("System")
from System.ComponentModel import INotifyPropertyChanged, INotifyDataErrorInfo
from System.ComponentModel import PropertyChangedEventArgs, DataErrorsChangedEventArgs
from System.Collections.Generic import List

# ===============
# ---> CLASSES <---
class ViewModelBaseValidation(INotifyPropertyChanged, INotifyDataErrorInfo):
	"""View Model Base Class implementing INotifyPropertyChanged and INotifyDataErrorInfo."""
	def __init__(self):
		super(ViewModelBaseValidation,self).__init__()
		self.propertyChangedEventHandler = []		# This is the PropertyChangedEventHandler
		self.dataErrorsChangedEventHandler = []		# This is the DataErrorsChangedEventArgs
		self._errors = {}

	# INotifyPropertyChanged
	# -------------------------
	def add_PropertyChanged(self, handler):
		self.propertyChangedEventHandler.append(handler)	# adding to list

	def remove_PropertyChanged(self, handler):
		self.propertyChangedEventHandler.remove(handler)	# removing from list

	def OnPropertyChanged(self, property_name):
		args = PropertyChangedEventArgs(property_name)
		for handler in self.propertyChangedEventHandler:
			handler(self, args)

	# INotifyDataErrorInfo
	# -------------------------
	def add_ErrorsChanged(self, handler):
		self.dataErrorsChangedEventHandler.append(handler)

	def remove_ErrorsChanged(self, handler):
		if handler in self.dataErrorsChangedEventHandler:
			self.dataErrorsChangedEventHandler.remove(handler)

	def OnErrorsChanged(self, property_name):
		args = DataErrorsChangedEventArgs(property_name)
		for handler in self.dataErrorsChangedEventHandler:
			handler(self, args)

	@property
	def HasErrors(self):
		return any(self._errors.values())

	def GetErrors(self, property_name):
		result = List[str]()
		if property_name and property_name in self._errors:
			for error in self._errors[property_name]:
				result.Add(error)
		return result

	# Validation Helpers
	# -------------------------
	def AddError(self, property_name, error_message):
		if property_name not in self._errors:
			self._errors[property_name] = []
		if error_message not in self._errors[property_name]:
			self._errors[property_name].append(error_message)
			self.OnErrorsChanged(property_name)

	def ClearErrors(self, property_name):
		if property_name in self._errors:
			del self._errors[property_name]		# Deleting errors
			self.OnErrorsChanged(property_name)

	def SetProperty(self, field_name, value, property_name):
		"""Helper to set a backing field and raise PropertyChanged."""
		setattr(self, field_name, value)
		self.OnPropertyChanged(property_name)