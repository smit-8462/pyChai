# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from lib_WPF.Views.WindowBottomBarUC import WindowBottomBarUC
from lib_WPF.Views.WindowTopBarUC import WindowTopBarUC

# ===============
# ---> CLASS <---
class UserControlManager(object):
	"""Handles initialization and event wiring of all UserControls (WindowBottomBarUC & WindowTopBarUC)."""
	def __init__(self, window_target, title="pyChai"):
		"""
		:param window_target: Parent Window class
		:type window_target: target
		"""
		self.window_target = window_target
		self._title = title
		self._window_top_bar_setup()
		self._window_bottom_bar_setup()

	def _window_top_bar_setup(self):
		self.top_bar = WindowTopBarUC()
		# Giving initial value for Title, since we can't control Title in UserControl in pyRevit.
		self.top_bar.Title = self._title

		# Adding event for initialization in MainWindow
		self.top_bar.add_WindowClose(self.window_target.ButtonEvent_Window_Close)
		self.top_bar.add_WindowMinimize(self.window_target.ButtonEvent_Window_Minimize)
		self.top_bar.add_WindowResize(self.window_target.ButtonEvent_Window_Resize)
		self.top_bar.add_WindowTheme(self.window_target.ButtonEvent_Window_Theme)

		# Adding to UserControl "window_top_bar_uc" Grid container (derived from XAML file)
		self.window_target.window_top_bar_uc.Children.Add(self.top_bar)

	def _window_bottom_bar_setup(self):
		self.bottom_bar = WindowBottomBarUC()
		# Adding event for initialization
		self.bottom_bar.add_WebsiteVisit(self.window_target.ButtonEvent_Window_VisitProfile)

		# Adding to UserControl "window_bottom_bar_uc" Grid container (derived from XAML file)
		self.window_target.window_bottom_bar_uc.Children.Add(self.bottom_bar)