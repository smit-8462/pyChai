# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import os, clr, wpf

clr.AddReference("System")
from System.Windows.Controls import UserControl
from System.Windows import RoutedEvent, EventManager, RoutingStrategy, RoutedEventHandler, RoutedEventArgs
from System import ArgumentException

from lib_WPF.Helpers.he_resdict_manager import ResDictManager
from lib_WPF.Helpers.he_event_manager import get_or_register_event

# ===============
# ---> VARIABLES <---
PATH_SCRIPT = os.path.dirname(__file__)    # type: str

# ===============
# ---> CLASSES <---
class WindowTopBarUC(UserControl):
	# Reservation of name, no registration of event done yet
	CloseEvent = None
	MinimizeEvent = None
	ResizeEvent = None
	ThemeEvent = None

	def __init__(self):
		super(WindowTopBarUC, self).__init__()
		self._title = ""  # No Dependency Property used

		ResDictManager.apply_shared(self)  # Applying shared list

		# Connect to .XAML file in the same folder
		xml_file_path = os.path.join(PATH_SCRIPT, 'WindowTopBarUC.xaml')
		wpf.LoadComponent(self, xml_file_path)

		# Now safe to access XAML elements. In this, we are using code-behind for this specific part ,i.e., adding
		# "Title" text, because there is some weird complexity when dealing with Dependency Property in UserControl.
		self.tb_title.Text = self._title

		# Register or retrieve Routed Events
		owner = type(self)
		WindowTopBarUC.CloseEvent = get_or_register_event("WindowClose", owner)
		WindowTopBarUC.MinimizeEvent = get_or_register_event("WindowMinimize", owner)
		WindowTopBarUC.ResizeEvent = get_or_register_event("WindowResize", owner)
		WindowTopBarUC.ThemeEvent = get_or_register_event("WindowTheme", owner)

	# Title Property get/set
	@property
	def Title(self):
		return self._title

	@Title.setter
	def Title(self, value):
		self._title = value
		if self.tb_title is not None:	# Update the TextBlock in XAML directly
			self.tb_title.Text = value

	# Routed Event Handler
	# --------------------------------
	# CloseEvent
	def add_WindowClose(self, handler):				# Add event handler
		self.AddHandler(WindowTopBarUC.CloseEvent, RoutedEventHandler(handler))

	def remove_WindowClose(self, handler):				# Remove event handler
		self.RemoveHandler(WindowTopBarUC.CloseEvent, RoutedEventHandler(handler))

	# MinimizeEvent
	def add_WindowMinimize(self, handler):				# Add event handler
		self.AddHandler(WindowTopBarUC.MinimizeEvent, RoutedEventHandler(handler))

	def remove_WindowMinimize(self, handler):				# Remove event handler
		self.RemoveHandler(WindowTopBarUC.MinimizeEvent, RoutedEventHandler(handler))

	# ResizeEvent
	def add_WindowResize(self, handler):				# Add event handler
		self.AddHandler(WindowTopBarUC.ResizeEvent, RoutedEventHandler(handler))

	def remove_WindowResize(self, handler):				# Remove event handler
		self.RemoveHandler(WindowTopBarUC.ResizeEvent, RoutedEventHandler(handler))

	# ThemeEvent
	def add_WindowTheme(self, handler):				# Add event handler
		self.AddHandler(WindowTopBarUC.ThemeEvent, RoutedEventHandler(handler))

	def remove_WindowTheme(self, handler):				# Remove event handler
		self.RemoveHandler(WindowTopBarUC.ThemeEvent, RoutedEventHandler(handler))

	# Below methods raising the events
	# --------------------------------
	def RaiseWindowCloseEvent(self, sender, event):
		new_event_args = RoutedEventArgs(WindowTopBarUC.CloseEvent)
		self.RaiseEvent(new_event_args)

	def RaiseWindowMinimizeEvent(self, sender, event):
			new_event_args = RoutedEventArgs(WindowTopBarUC.MinimizeEvent)
			self.RaiseEvent(new_event_args)

	def RaiseWindowResizeEvent(self, sender, event):
			new_event_args = RoutedEventArgs(WindowTopBarUC.ResizeEvent)
			self.RaiseEvent(new_event_args)

	def RaiseWindowThemeEvent(self, sender, event):
			new_event_args = RoutedEventArgs(WindowTopBarUC.ThemeEvent)
			self.RaiseEvent(new_event_args)