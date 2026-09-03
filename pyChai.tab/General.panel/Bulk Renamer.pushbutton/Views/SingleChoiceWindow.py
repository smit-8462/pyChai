# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback

clr.AddReference("System")
from lib_WPF.Helpers.he_resdict_manager import ResDictManager

from Converters.cv_TextToTokenConverter import StringToSegmentsConverter
from Converters.cv_CombinedTokenPartConverter import CombinedTokenPartConverter

# Import from shared libs
from lib_WPF.Helpers.he_View_WindowBase import WindowBase
from lib_WPF.Helpers.he_resdict_manager import ResDictManager
from lib_WPF.Helpers.he_userControlManager import UserControlManager
from lib_WPF.Helpers.he_theme_manager import ThemeManager

# ===============
# ---> VARIABLES <---
PATH_SCRIPT = os.path.dirname(__file__)    # type: str

# ===============
# ---> MAIN CLASS <---
class SingleChoiceWindow(WindowBase):
	def __init__(self, main_window, main_vm, rich_text_box):
		super(SingleChoiceWindow, self).__init__()
		self._main_window = main_window
		self._main_vm = main_vm
		self._rich_text_box = rich_text_box

		# Here, we are using InformationVM in MainWindow ViewModel to simplify process.
		self.DataContext = self._main_vm.InformationVM

		# Register converters before LoadComponent, so that XAML can resolve {StaticResource StringToSegmentsConverter}
		# during parsing. Since converters give error on using DynamicResource, thereby StaticResource is recommended.
		self.Resources["StringToSegmentsConverter"] = StringToSegmentsConverter()
		self.Resources["CombinedTokenPartConverter"] = CombinedTokenPartConverter()

		# Load shared resources
		ResDictManager.apply_shared(self)  # Applying shared list

		# Connect to .XAML file in the same folder
		xml_file_path = os.path.join(PATH_SCRIPT, 'SingleChoiceWindow.xaml')
		wpf.LoadComponent(self, xml_file_path)

		# All the UserControls wirings are handled here, by attaching it to the existing main window
		self.usercontrol_manager = UserControlManager(self, title="Select", hide_bottom_bar=True)

		# Managing themes
		extra_targets_usercontrols = [self.usercontrol_manager.top_bar]
		self.theme_manager = ThemeManager(self,
										  "Theme_Light.xaml",
										  "Theme_Dark.xaml",
										  extra_targets_usercontrols)

	# ===============
	# ---> EVENTS <---
	# General window events (applicable to all windows)
	def ButtonEvent_Window_Minimize(self, sender, event):
		self.minimize_window()

	def ButtonEvent_Window_Resize(self, sender, event):
		self.toggle_fullscreen()

	def ButtonEvent_Window_Close(self, sender, event):
		self._close_process()

	def ButtonEvent_Window_Theme(self, sender, event):
		self.theme_manager.toggle()

	def ButtonEvent_SelectWindow_Cancel(self, sender, event):
		self._close_process()

	def ButtonEvent_SelectWindow_Select(self, sender, event):
		self._apply_process()

	# ===============
	# ---> METHODS <---
	def _close_process(self):
		self._main_vm.InformationVM.SelectedItem = None
		self.close_window()

	def _apply_process(self):
		selected_text = self._main_vm.InformationVM.SelectedItem
		if selected_text:
			self._main_window.rename_tokenizer.set_text(selected_text)
		self._close_process()