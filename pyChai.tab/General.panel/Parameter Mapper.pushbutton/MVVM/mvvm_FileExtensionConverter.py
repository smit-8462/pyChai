# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr

clr.AddReference("System")
from System.Windows.Data import IValueConverter, Binding

# ===============
# ---> HELPER CLASS <---
class FileExtensionConverter(IValueConverter):
	"""
	Converts a string property to bool by comparing with ConverterParameter. It supports multiple parameters separated
	by '|' pipe character (e.g. ConverterParameter=.xlsx|.xls|.xlsm|.xlsb)
	"""
	def Convert(self,value,targetType,parameter,culture):
		"""Returns True if bound value matches any of the ConverterParameters."""
		if parameter is None:
			return False
		parameters = parameter.split("|")
		return value in parameters

	def ConvertBack(self,value,targetType,parameter,culture):
		"""Returns first ConverterParameter when RadioButton is checked."""
		if value:
			return parameter.split("|")[0]  # Returns first extension e.g. ".xlsx"
		return Binding.DoNothing