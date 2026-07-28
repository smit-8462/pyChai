# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import clr
# from System.Drawing import Size, Point

clr.AddReference("System")
clr.AddReference("System.Windows.Forms")
from System import IntPtr
# from System.Windows import Window, WindowState, SystemParameters, WindowStartupLocation
from System.Windows import Window, WindowState, WindowStartupLocation
from System.Windows.Interop import HwndSource, HwndSourceHook, WindowInteropHelper
from System.Windows.Forms import Screen
from System.Diagnostics import Process

# ===============
# ---> CLASSES <---
class WindowBase(Window):
	"""
	A base class for all the custom WPF windows used in pyRevit.
	Reason -
		1. We are overriding the WindowState.Maximized, because it will slip 8px fom all sides.
		2. Therefore, we are manually adjusting the Window size by applying custom size to window.
	"""
	# Right-click button internal codes
	WM_SYSCOMMAND = 0x0112  	# Windows message
	SC_MAXIMIZE = 0xF030  		# System command for Maximize
	SC_RESTORE = 0xF120  		# System command for Restore
	SC_MINIMIZE = 0xF020  		# System command for Minimize

	def __init__(self):
		super(WindowBase, self).__init__()
		self.WindowStartupLocation = WindowStartupLocation.Manual	# Get the window's initial position.
		self.is_fullscreen = False
		self._is_toggling = False  		# Toggle for checking if the window is fullscreened
		self._old_top = 0.0  			# Window Y-position
		self._old_left = 0.0  			# Window X-position
		self._old_width = 0.0  			# Window width
		self._old_height = 0.0  		# Window height

		# Use Loaded instead of SourceInitialized, to fire it after all the XAMLs are loaded in Window.
		self.Loaded += self._on_loaded
		self.StateChanged += self._on_state_changed

	# ===============
	# ---> HOOK <---
	def _on_loaded(self, sender, event):
		"""Called automatically when the window finishes loading."""
		self.center_on_revit_monitor()
		source = HwndSource.FromHwnd(self._get_handle())
		if source:
			source.AddHook(HwndSourceHook(self._wnd_proc))

	def _get_handle(self):
		"""Returns the Win32 window handle (HWND) of this WPF window, which is needed to hook into Windows messages."""
		return WindowInteropHelper(self).Handle

	def _wnd_proc(self, hwnd, msg, wparam, lparam, handled):
		"""The Windows message handler (called for every Win32 message)."""
		if msg == self.WM_SYSCOMMAND:
			sc = wparam.ToInt32() & 0xFFF0  # Convert IntPtr to int
			if sc == self.SC_MAXIMIZE:
				self.on_maximize_restore()
				handled.Value = True
			elif sc == self.SC_RESTORE:
				if self.is_fullscreen and self.WindowState != WindowState.Minimized:
					self.on_maximize_restore()
					handled.Value = True
			elif sc == self.SC_MINIMIZE:
				self.on_minimize()
				handled.Value = True
		return IntPtr.Zero

	def center_on_revit_monitor(self):
		"""Positions this window centered on the same monitor Revit's main window is on."""
		# HWND of Revit's main window, used to determine which monitor it's on.
		revit_handle = Process.GetCurrentProcess().MainWindowHandle
		if revit_handle == IntPtr.Zero:
			return  	# Let it be fallback, by leaving WPF's default placement as-is
		screen_left, screen_top, screen_width, screen_height = self._get_monitor_work_area(revit_handle)
		self.Left = screen_left + (screen_width - self.Width) / 2.0
		self.Top = screen_top + (screen_height - self.Height) / 2.0

	@staticmethod
	def _get_monitor_work_area(hwnd):
		"""Work area of the monitor containing the given HWND, in WPF logical units."""
		work_area = Screen.FromHandle(hwnd).WorkingArea
		return work_area.X, work_area.Y, work_area.Width, work_area.Height

	def on_maximize_restore(self):
		self.toggle_fullscreen()

	def on_minimize(self):
		self.minimize_window()

	def _on_state_changed(self, sender, event):
		"""Re-applies fullscreen dimensions when restoring from minimized. Skipped if toggle_fullscreen is running."""
		if self._is_toggling:
			return

		if self.WindowState == WindowState.Normal and self.is_fullscreen:
			left, top, width, height = self._get_current_monitor_work_area()
			self.Top = top
			self.Left = left
			self.Width = width
			self.Height = height

	# ===============
	# ---> MONITOR HELPER <---
	def _get_current_monitor_work_area(self):
		"""Work area of the monitor currently under this window itself."""
		return self._get_monitor_work_area(self._get_handle())

	# ===============
	# ---> BUTTON ACTIONS <---
	def toggle_fullscreen(self):
		self._is_toggling = True  # block _on_state_changed during this
		try:
			if self.is_fullscreen:
				# Restore saved position and size from before fullscreen
				self.WindowState = WindowState.Normal
				self.Top = self._old_top
				self.Left = self._old_left
				self.Width = self._old_width
				self.Height = self._old_height
				self.is_fullscreen = False
			else:
				# Save current position and size for future use
				self._old_top = self.Top
				self._old_left = self.Left
				self._old_width = self.Width
				self._old_height = self.Height

				# Reset to Normal state first
				self.WindowState = WindowState.Normal
				left, top, width, height = self._get_current_monitor_work_area()
				self.Top = top
				self.Left = left
				self.Width = width
				self.Height = height
				self.is_fullscreen = True
		finally:
			self._is_toggling = False

	def minimize_window(self):
		self.WindowState = WindowState.Minimized

	def close_window(self):
		self.Close()