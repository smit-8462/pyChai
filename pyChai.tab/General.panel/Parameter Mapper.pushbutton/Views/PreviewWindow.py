# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import traceback
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr

from Autodesk.Revit.UI import TaskDialog

clr.AddReference("System")
from System.Windows import Style, Setter, DataTrigger, DynamicResourceExtension
from System.Windows.Controls import DataGridCell
from System.Windows.Data import Binding

from lib_WPF.ViewModels.vm_WindowBottomBarViewModel import WindowBottomBarViewModel

from lib_WPF.Helpers.he_View_WindowBase import WindowBase
from lib_WPF.Helpers.he_resdict_manager import ResDictManager
from lib_WPF.Helpers.he_userControlManager import UserControlManager
from lib_WPF.Helpers.he_theme_manager import ThemeManager

from ViewModels.vm_PreviewWindowMainModel import PreviewWindowViewModel

from MVVM.mvvm_ValidationToBrushConverter import CellValidityConverter, ValidationToTooltipConverter

# ===============
# ---> VARIABLES <---
PATH_SCRIPT = os.path.dirname(__file__)    # type: str

# Resource keys defined in theme XAML.
_INVALID_CELL_BG_KEY = "theme_datagrid_invalid_cell_bg"
_INVALID_ROW_BG_KEY = "theme_datagrid_invalid_row_bg"

# ===============
# ---> MAIN CLASS <---
class PreviewWindow(WindowBase):
	def __init__(self, main_window, main_vm, ext_event, ext_event_handler):
		# Passing the external event and event handler from MainWindow view to PreviewWindow.
		super(PreviewWindow, self).__init__()
		self._main_window = main_window
		self._main_vm = main_vm

		# ViewModel initialise once
		self.vm_windowBottomBar = WindowBottomBarViewModel()
		self.vm_previewWindow = PreviewWindowViewModel(self._main_vm.ChoicesVM, self._main_vm.ElementSelection,
		                                               ext_event, ext_event_handler)

		# Data Context
		self.DataContext = self.vm_previewWindow

		# Converters are created once. CellValidityConverter is used twice by pointing at two different maps.
		# _cell_validity_converter => CellValidityMap (own-cell check)
		# _row_sibling_error_converter=> RowSiblingErrorMap (sibling check)
		self._cell_validity_converter = CellValidityConverter(lambda: self.vm_previewWindow.CellValidityMap)
		self._row_sibling_error_converter = CellValidityConverter(lambda: self.vm_previewWindow.RowSiblingErrorMap)
		self._validation_tooltip_converter = ValidationToTooltipConverter(lambda: self.vm_previewWindow.CellErrorMap)

		# Load shared resources
		ResDictManager.apply_shared(self)  # Applying shared list

		# Connect to .XAML file in the same folder
		xml_file_path = os.path.join(PATH_SCRIPT, 'PreviewWindow.xaml')
		wpf.LoadComponent(self, xml_file_path)

		# All the UserControls wirings are handled here, by attaching it to the existing main window
		self.usercontrol_manager = UserControlManager(self, title="pyChai - Parameter Mapper")

		# Managing themes
		extra_targets_usercontrols = [self.usercontrol_manager.top_bar, self.usercontrol_manager.bottom_bar]
		self.theme_manager = ThemeManager(self,
										  "Theme_Light.xaml",
										  "Theme_Dark.xaml",
										  extra_targets_usercontrols, use_lib_resources=True)

		# Hooking up event after LoadComponent XAML file
		self.PreviewDataGrid.AutoGeneratingColumn += self.OnAutoGeneratingColumn

		self.Closing += self.vm_previewWindow.OnClosing		# Subscribe to closing event

	# ===============
	# ---> EVENTS <---
	def ButtonEvent_Window_Minimize(self, sender, event):
		self.minimize_window()

	def ButtonEvent_Window_Resize(self, sender, event):
		self.toggle_fullscreen()

	def ButtonEvent_Window_Close(self, sender, event):
		self.close_window()

	def ButtonEvent_Window_Theme(self, sender, event):
		self.theme_manager.toggle()

	def ButtonEvent_Window_VisitProfile(self, sender, event):
		self.vm_windowBottomBar.visit_website()

	def ButtonEvent_Preview_GoBack(self, sender, event):
		self._main_window.Show()	# To prevent window from shifting its position after restoring
		self.Close()

	def ButtonEvent_Preview_Apply(self, sender, event):
		self.pakka_apply_values()

	def ButtonEvent_Preview_Cancel(self, sender, event):
		self.close_window()

	# ===============
	# ---> METHODS <---
	def OnAutoGeneratingColumn(self, sender, e):
		"""
		Creating data triggers in code-behind (due to some issue, I had to use ;( ).

		The 1st time AutoGenerateColumns builds columns for DataTable instance bound as ItemsSource, this event fires.
		Each DataTrigger's Binding needs a Converter and a ConverterParameter (the column name).
		Both are known only at the time of dynamic column-generation.

		Two triggers are added below, in a specific order:
		  1. Sibling-error trigger (added 1st)  --> faint/row-wide color.
		  	 It fires when RowSiblingErrorMap says some other column in this row is invalid.
		  2. Own-cell trigger (added 2nd) 		--> strong color.
		     It fires when CellValidityMap says that this cell itself is invalid.
		"""
		column_name = e.Column.Header.ToString()

		base_style = self.Resources["ValidatedCellStyle"]  # XAML-defined base
		style = Style(DataGridCell, base_style)  # new instance per column

		# Trigger 01 - Creates a row-wide color when an error-cell is detected.
		sibling_binding = Binding(".")  # Binding to the whole row item itself (DataRowView)
		sibling_binding.Converter = self._row_sibling_error_converter
		sibling_binding.ConverterParameter = column_name
		sibling_trigger = DataTrigger()
		sibling_trigger.Binding = sibling_binding
		sibling_trigger.Value = False
		sibling_trigger.Setters.Add(Setter(DataGridCell.BackgroundProperty,
										   DynamicResourceExtension(_INVALID_ROW_BG_KEY)))
		style.Triggers.Add(sibling_trigger)

		# Trigger 02 - Creates a row-wide color when an own-error-cell itself is detected.
		validity_binding = Binding(".")  # Binding to the whole row item itself (DataRowView)
		validity_binding.Converter = self._cell_validity_converter
		validity_binding.ConverterParameter = column_name
		invalid_trigger = DataTrigger()
		invalid_trigger.Binding = validity_binding
		invalid_trigger.Value = False
		invalid_trigger.Setters.Add(Setter(DataGridCell.BackgroundProperty,
										   DynamicResourceExtension(_INVALID_CELL_BG_KEY)))
		style.Triggers.Add(invalid_trigger)

		# Binding Tooltip to error
		tooltip_binding = Binding(".")
		tooltip_binding.Converter = self._validation_tooltip_converter
		tooltip_binding.ConverterParameter = column_name
		style.Setters.Add(Setter(DataGridCell.ToolTipProperty, tooltip_binding))
		e.Column.CellStyle = style

	def pakka_apply_values(self):
		self.PreviewButtonApply.IsEnabled = False
		try:
			# self._on_apply_complete has no parentheses. This doesn't call the method, it passes the method itself as a value.
			# Now self.m_ExternalEventHandler.on_complete is self._on_apply_complete - same function object,
			# just reachable from a different place (the handler).
			self.vm_previewWindow.finally_apply_values(on_complete=self._on_apply_complete)
			self.vm_previewWindow.HasUserClickedOnFinalApplyButton = True
		except Exception as e:
			self.ButtonApply.IsEnabled = True  # Raise() itself failed synchronously
			print("Failed to apply values:\n\n{}\n\n{}".format(e, traceback.format_exc()))
			TaskDialog.Show("Error", "Failed to apply values.")

	def _on_apply_complete(self, success):
		self.PreviewButtonApply.IsEnabled = True  # re-enable now that Execute() has actually finished
		if not success:
			TaskDialog.Show("Error", "Failed to apply parameter values.")
			return

		mesa = "Element parameter values successfully applied!\n\nChoose to following options - "
		res = forms.alert(msg=mesa, title="Success", footer="Success", warn_icon=None,
		                  options=["Show report", "Continue working with tool", "Exit"])
		if res == "Show report":
			self._main_vm.markdown_output()
			self.Close()
		elif res == "Continue working with tool":
			self._main_window.Show()  # restore original window at its position
			self.Close()
		else:
			self.Close()
