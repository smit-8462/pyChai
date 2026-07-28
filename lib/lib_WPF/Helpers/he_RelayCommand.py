# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr

clr.AddReference("System")
from System.Windows.Input import ICommand
from System import EventArgs

# ===============
# ---> CLASSES <---
class RelayCommand(ICommand):
	def __init__(self, execute, can_execute = None):
		super(RelayCommand, self).__init__()
		self._execute = execute
		self._can_execute = can_execute
		self._handlers = []

	def add_CanExecuteChanged(self, handler):
		self._handlers.append(handler)

	def remove_CanExecuteChanged(self, handler):
		if handler in self._handlers:
			self._handlers.remove(handler)

	def RaiseCanExecuteChanged(self):
		for handler in self._handlers:
			handler(self, EventArgs.Empty)

	# ICommand members
	#------------------
	def CanExecute(self,parameter):
		if self._can_execute is None:
			return True
		return self._can_execute(parameter)

	def Execute(self, parameter):
		self._execute(parameter)