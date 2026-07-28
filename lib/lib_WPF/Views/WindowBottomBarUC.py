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
class WindowBottomBarUC(UserControl):
	WebsiteEvent = None  # Reservation of name, no registration of event done yet

	def __init__(self):
		super(WindowBottomBarUC, self).__init__()
		ResDictManager.apply_shared(self)	# Applying shared list

		# Connect to .XAML file in the same folder
		xml_file_path = os.path.join(PATH_SCRIPT, 'WindowBottomBarUC.xaml')
		wpf.LoadComponent(self, xml_file_path)

		# Register or retrieve the WebsiteVisit routed event
		WindowBottomBarUC.WebsiteEvent = get_or_register_event("WebsiteVisit", type(self))

	# Provide CLR accessors for the event. WindowBottomBarUC is a class-level attribute, not instance attribute.
	def add_WebsiteVisit(self, handler):				# Add event handler
		self.AddHandler(WindowBottomBarUC.WebsiteEvent, RoutedEventHandler(handler))

	def remove_WebsiteVisit(self, handler):				# Remove event handler
		self.RemoveHandler(WindowBottomBarUC.WebsiteEvent, RoutedEventHandler(handler))

	# This method raises the VisitWebsite event. It mirrors C#'s static readonly intent.
	def RaiseWebsiteVisitEvent(self, sender, event):
		new_event_args = RoutedEventArgs(WindowBottomBarUC.WebsiteEvent)
		self.RaiseEvent(new_event_args)