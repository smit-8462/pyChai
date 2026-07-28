# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import os, clr, wpf

clr.AddReference("System")
from System.Windows import RoutedEvent, EventManager, RoutingStrategy, RoutedEventHandler
from System import ArgumentException

# ===============
# ---> VARIABLES <---

# ===============
# ---> METHODS <---
def get_or_register_event(name, owner_type):
	"""
	Register a RoutedEvent, or retrieve it if already registered.
	:param name: The name of the RoutedEvent
	:type name: str
	:param owner_type: The class of the RoutedEvent
	:type owner_type: type
	"""
	try:
		return EventManager.RegisterRoutedEvent(
			name, RoutingStrategy.Bubble, RoutedEventHandler, owner_type)
	except ArgumentException:
		# Already registered — find and return the existing one
		existing = EventManager.GetRoutedEventsForOwner(owner_type)
		if existing:
			for evt in existing:
				if evt.Name == name:
					return evt
		return None  # Shouldn't happen, but safe fallback
