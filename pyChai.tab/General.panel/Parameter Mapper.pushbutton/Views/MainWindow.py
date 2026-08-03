# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback
from Autodesk.Revit.UI import TaskDialog, ExternalEvent

clr.AddReference("System")
from System.Windows import WindowState

# Import from shared libs
from lib_WPF.ViewModels.vm_WindowBottomBarViewModel import WindowBottomBarViewModel

from lib_WPF.Helpers.he_View_WindowBase import WindowBase
from lib_WPF.Helpers.he_resdict_manager import ResDictManager
from lib_WPF.Helpers.he_userControlManager import UserControlManager
from lib_WPF.Helpers.he_theme_manager import ThemeManager

from lib_WPF.Models.mo_ModelExternalEvent import BasicExEventHandler

from Views.PreviewWindow import PreviewWindow

from ViewModels.vm_MainWindowViewModel import MainWindowViewModel

from MVVM.mvvm_FileExtensionConverter import FileExtensionConverter

# ===============
# ---> VARIABLES <---
PATH_SCRIPT = os.path.dirname(__file__)    # type: str
RES_LIST = ["resourceDict_General.xaml", "Themes/Theme_Light.xaml", "Themes/Theme_Dark.xaml",
			"resourceDict_ComboBox.xaml", "resourceDict_Choices.xaml", "resourceDict_DataGrid.xaml"]

# ===============
# ---> MAIN CLASS <---
class MainWindow(WindowBase):
	def __init__(self):
		super(MainWindow, self).__init__()

		# ViewModel initialise once
		self.vm_windowBottomBar = WindowBottomBarViewModel()
		self.vm_mainWindow = MainWindowViewModel()

		# Data Context
		self.DataContext = self.vm_mainWindow

		# Load Resource Dictionary files
		res_manager = ResDictManager()
		res_manager.apply_to(self, RES_LIST)	# Now, it populates shared list

		# Register converters before LoadComponent, so that XAML can resolve {StaticResource FileExtensionConverter}
		# during parsing. Since converters give error on using DynamicResource, thereby StaticResource is recommended.
		self.Resources["FileExtensionConverter"] = FileExtensionConverter()

		# Connect to .XAML file in the same folder
		xml_file_path = os.path.join(PATH_SCRIPT, 'MainWindow.xaml')
		wpf.LoadComponent(self, xml_file_path)

		# All the UserControls wirings are handled here
		# Attaching to the existing main window
		self.usercontrol_manager = UserControlManager(self, title="pyChai - Parameter Mapper")
		extra_targets_usercontrols = [self.usercontrol_manager.top_bar, self.usercontrol_manager.bottom_bar]
		self.theme_manager = ThemeManager(self,
										  "Theme_Light.xaml",
										  "Theme_Dark.xaml",
										  extra_targets_usercontrols, use_lib_resources=True)

		# The External Event is created only once, at the starting of script.
		self.ext_event_handler = BasicExEventHandler()
		self.ext_event = ExternalEvent.Create(self.ext_event_handler)

		self.Closing += self.OnMainWindowClosing	# Event is disposed only when the whole tool closes.

	# ===============
	# ---> EVENTS <---
	def ButtonEvent_Window_Minimize(self, sender, event):
		self.minimize_window()

	def ButtonEvent_Window_Resize(self, sender, event):
		self.toggle_fullscreen()

	def ButtonEvent_Window_Close(self, sender, event):
		self.close_window()

	def ButtonEvent_Main_Clear(self, sender, event):
		self.vm_mainWindow.clear_all_things()
		# Since it's no longer bound 2-way, setting `SelectedCategory = None` in the ViewModel won't clear the ComboBox's own displayed selection.
		self.mw_category_picker.SelectedIndex = -1

	def ButtonEvent_Window_Theme(self, sender, event):
		self.theme_manager.toggle()

	def ButtonEvent_Main_PickFile(self, sender, event):
		self.vm_mainWindow.pick_file_method()		

	def ButtonEvent_Main_RefreshContent(self, sender, event):
		if self.vm_mainWindow.FileSelection.SelectedFilePath:
			self.vm_mainWindow.ChoicesVM.excel_dict_setup()
		else:
			TaskDialog.Show("Warning", "File not selected.\nKindly select file.")

	def ButtonEvent_Main_SelectManual(self, sender, event):
		try:
			self.vm_mainWindow.select_elements("manual")
		except Exception as e:
			print("Transaction failed: {}\n{}\n{}".format(e, '-' * 25, traceback.format_exc()))
		# Restore window on top after manual selection, since it used to go behind.
		if self.WindowState == WindowState.Minimized:
			self.WindowState = WindowState.Normal
		self.Activate()

	def ButtonEvent_Main_SelectAll(self, sender, event):
		try:
			self.vm_mainWindow.select_elements("all")
		except Exception as e:
			print("Transaction failed: {}\n{}\n{}".format(e, '-' * 25, traceback.format_exc()))

	def ButtonEvent_Main_SelectClear(self, sender, event):
		self.vm_mainWindow.clear_main_things()

	def ButtonEvent_Main_ShowError(self, sender, event):
		if self.vm_mainWindow.ElementSelection.HasPreviewWindowOpened:
			try:
				self.vm_mainWindow.markdown_output()
			except Exception as e:
				print("Transaction failed: {}\n{}\n{}".format(e, '-' * 25, traceback.format_exc()))
		else:
			TaskDialog.Show("Warning", "No preview window opened.\nNeed to Generate Preview atleast once.")

	def ButtonEvent_Window_VisitProfile(self, sender, event):
		self.vm_windowBottomBar.visit_website()

	def ButtonEvent_Main_PreviewContent(self, sender, event):
		try:
			self._generate_preview_content()
		except Exception as e:
			TaskDialog.Show("Preview Error",
							"Failed to generate preview:\n\n{}\n\n{}".format(e, traceback.format_exc()))

	def ButtonEvent_Main_Cancel(self, sender, event):
		self.close_window()

	# -----------------------------
	# Fixing issues in pre .NET 8
	# -----------------------------
	"""
	`SelectedItem="{Binding CategorySelection.SelectedCategory, Mode=TwoWay}"`

	- The above XAML code in ComboBox "mw_category_picker" is causing issues pre-Revit 2025 versions, because it is using .NET 4.8.
	- In .NET 4.8, there is a documented quirk with `SelectedItem`, when using with 2-way binding, especially when used with ComboBox (`ComboBox.SelectedItem`).
	- Rather than keep fighting the native SelectedItem binding across .NET Framework vs .NET Core WPF quirks, the more reliable fix is to bypass it 
		and set the property explicitly in code-behind via SelectionChanged, used below. 
	- It works identically on every Revit version since it doesn't depend on WPF's binding engine reconciling custom Python objects.
	- So, we are proceeding with code-behind. The `SelectionChanged` is a ComboBox event, having `ComboBox_Category_SelectionChanged` name.
	"""
	def ComboBox_Category_SelectionChanged(self, sender, event):
		self.vm_mainWindow.CategorySelection.SelectedCategory = sender.SelectedItem

	"""
	XAML codes - 
	|  <!--  Revit Parameter  -->                      |  <!--  Excel Column  -->                    |
	|  `SelectedItem="{Binding RevitParameterValue}"`  |  SelectedItem="{Binding ExcelColumnValue}"  |
	
	- It still handles ViewModel -> View updates fine, when a row is cleared programmatically. 
	- It's only the View -> ViewModel direction that is broken on Revit 2024, so we are patching that side with `SelectionChanged`.
	- Since each ComboBox sits inside the ItemsControl's DataTemplate, its DataContext at the time of the event is the individual ChoiceRowViewModel for that row, 
		so `sender.DataContext` gives us exactly the row instance we need, and assigning through the existing property setters 
		keeps triggering ValidateDuplicates(), AllRowsFilled, IsButtonEnabled, etc. exactly as before.
	"""
	def ComboBox_RevitParameter_SelectionChanged(self, sender, event):
		row = sender.DataContext		# type: ChoiceRowViewModel
		if row is not None:
			row.RevitParameterValue = sender.SelectedItem
	
	def ComboBox_ExcelColumn_SelectionChanged(self, sender, event):
		row = sender.DataContext		# type: ChoiceRowViewModel
		if row is not None:
			row.ExcelColumnValue = sender.SelectedItem

	# ===============
	# ---> METHODS <---
	def OnMainWindowClosing(self, sender, event):
		"""Disposing events after closing of window."""
		if self.ext_event is not None:
			self.ext_event.Dispose()
			self.ext_event = None
			self.ext_event_handler = None

	def _generate_preview_content(self):
		# pass the MainWindow ViewModel, external event and event handler, since we are ceating event for only one time,
		# creating at the start of window lifecycle of MainWindow, and dying at the end of window lifecycle of MainWindow.
		# Since MainWindow is the starting point / launching point of plugin, therefore we are creating (initializing) it here.
		preview_window = PreviewWindow(self, self.vm_mainWindow, self.ext_event, self.ext_event_handler)
		self.Hide()  # Hide MainWindow
		preview_window.Show()  # Show PreviewWindow
		# Show preview of generated data
		preview_window.vm_previewWindow.preview_data_generate()  # Call on the ViewModel via the local variable
		self.vm_mainWindow.ElementSelection.HasPreviewWindowOpened = True
		self.vm_mainWindow.PreviewWindowVMProperty = preview_window.vm_previewWindow   # Pass the reference for further use.