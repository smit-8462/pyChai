# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms, script
# wpf can be imported only after pyrevit.forms
import wpf, os, traceback, clr

clr.AddReference("System")
from System.Collections.ObjectModel import ObservableCollection
from System.Windows.Controls import RichTextBox

from Autodesk.Revit.UI import TaskDialog

# Import from shared libs
from lib_WPF.Helpers.he_ViewModel_ViewModelBase import ViewModelBase
from lib_WPF.Helpers.he_RelayCommand import RelayCommand

from lib_System.sys_output import SysOutput_Markdown

from ViewModels.vm_TreeView_ViewModel import TreeViewerVM_MainWindow
from ViewModels.vm_RenamerList_ViewModel import RenamerListVM_MainWindow

from Models.mo_template_iops import TemplateIOPS
from Models.mo_tokenizing_control import extract_richtextbox_contents

# ===============
# ---> VARIABLES <---
PY_SCRIPT_PATH = os.path.abspath(__file__)    # type: str

# ===============
# ---> CLASSES <---
class MainWindowViewModel(ViewModelBase):
	"""Main Window View Model."""
	def __init__(self, ext_event, ext_event_handler, main_window_view):
		super(MainWindowViewModel,self).__init__()
		# Reuse the shared ExternalEvent created in MainWindow.
		self.m_ExternalEvent = ext_event
		self.m_ExternalEventHandler = ext_event_handler
		self._main_window_view = main_window_view

		# Initial choice
		self._combo_pick_choice = "combo_pick_family_type"
		self.TreeViewerVM = TreeViewerVM_MainWindow(self._combo_pick_choice)
		self.InformationVM = InformationVM_MainWindow(self.TreeViewerVM)
		self.RenamerListVM = RenamerListVM_MainWindow(self.TreeViewerVM, self.InformationVM, self._main_window_view)

		# Use External Event after sub-VMs are initialised
		self.m_ExternalEventHandler.passable_method = self.apply_final_name		

	# Property
	# -------------------
	@property
	def ComboPickChoice(self):
		return self._combo_pick_choice

	@ComboPickChoice.setter
	def ComboPickChoice(self, value):
		if value == self._combo_pick_choice: return		# Don't change if same choice is made.
		self._combo_pick_choice = value
		self.OnPropertyChanged("ComboPickChoice")
		self.TreeViewerVM.set_workflow(value)		# Swap the active workflow.

	# Method
	# -------------------
	def cancel_all_process(self):
		"""Cancelling all process, restoring it to default state."""
		self.RenamerListVM.clear_all_groups()
		self.TreeViewerVM.tree_restore_hidden_items()
		self.TreeViewerVM.tree_search_collapse_all_items()
		self.TreeViewerVM.tree_selection_clear()
		self.InformationVM.release_template_edit()

	def cancel_when_combobox_switch(self):
		"""Use this only when switching the combobox options, since it is a destructing clear option."""
		self.cancel_all_process()
		self.RenamerListVM.clear_all_groups()

	def reset_renamer_list(self):
		"""Full reset of the Precheck Renamer list: clear all groups, restore their tree items for reselection, release any active edit hold."""
		self.RenamerListVM.clear_all_groups()
		self.TreeViewerVM.tree_restore_hidden_items()
		self.InformationVM.release_template_edit()

	def apply_final_name(self):
		"""Apply final name."""
		self.RenamerListVM.rename_final_elements()
		
	def finally_apply_values(self, on_complete=None):
		"""Finally apply the mapped parameter values, using External Event. \n
		Here, ``on_complete`` is a callback method, which is set right before ``Raise()`` call."""
		self.m_ExternalEventHandler.on_complete = on_complete	# stores the function reference
		self.m_ExternalEvent.Raise()							# queues the async work


# ===============
# ---> Helper Classes <---
class InformationVM_MainWindow(ViewModelBase):
	"""Class related to Information."""
	def __init__(self, vm_tree_viewer):
		super(InformationVM_MainWindow,self).__init__()
		self._vm_tree_viewer = vm_tree_viewer		# type: TreeViewerVM_MainWindow
		self._template_iops = TemplateIOPS(self)

		# Commands - must be RelayCommand-wrapped so WPF's Command binding gets a real ICommand
		self._command_text_case_type = RelayCommand(lambda sender: self._text_case_type_changed(sender))
		self._command_text_slicing_side = RelayCommand(lambda sender: self._text_slicing_side_changed(sender))

		# Initializing properties
		self._count_success = 0
		self._count_failed = 0
		self._has_error = False
		self._error_list_combined = []
		self._common_parameters = set()
		self._dynamic_params_collection = ObservableCollection[object]()   # type: list
		# Related to templates
		self._selected_item = None
		self._template_collection = ObservableCollection[object]()   # type: list
		self._template_import_file_path = None
		# Related to text manipulation controls
		self._text_case = None
		self._slicing_side = None
		self._slicing_value = 0
		self._editing_template = None
		self._total_error_captured = 0
		self._is_final_apply_button_enabled = False
		self._is_list_generated = False		# Check whether the template items in listview is generated or not.
		self._is_final_apply_button_clicked = False

	# Property
	# -------------------
	@property
	def TotalErrorCaptured(self):
		"""Total error captured and found in listview."""
		return self._total_error_captured

	@TotalErrorCaptured.setter
	def TotalErrorCaptured(self, value):
		self._total_error_captured = value
		self.OnPropertyChanged("TotalErrorCaptured")
		self.OnPropertyChanged("IsFinalApplyButtonEnabled")

	@property
	def IsListGenerated(self):
		return self._is_list_generated

	@IsListGenerated.setter
	def IsListGenerated(self, value):
		self._is_list_generated = value
		self.OnPropertyChanged("IsListGenerated")
		self.OnPropertyChanged("IsFinalApplyButtonEnabled")

	@property
	def IsFinalApplyButtonEnabled(self):
		return self._is_list_generated and self._total_error_captured == 0
	
	@property
	def IsFinalApplyButtonClicked(self):
		return self._is_final_apply_button_clicked

	@IsFinalApplyButtonClicked.setter
	def IsFinalApplyButtonClicked(self, value):
		self._is_final_apply_button_clicked = value
		self.OnPropertyChanged("IsFinalApplyButtonClicked")

	@property
	def EditingTemplate(self):
		"""The GroupData_Renamer currently 'held' for editing, or None."""
		return self._editing_template

	@EditingTemplate.setter
	def EditingTemplate(self, value):
		self._editing_template = value
		self.OnPropertyChanged("EditingTemplate")
		self.OnPropertyChanged("IsToggleButtonOnHold")
		self.OnPropertyChanged("IsToggleButtonOnHoldInvert")

	@property
	def IsToggleButtonOnHold(self):
		return self._editing_template is not None

	@property
	def IsToggleButtonOnHoldInvert(self):
		return self._editing_template is None

	# Text manipulate
	@property
	def Command_TextCaseType(self):
		return self._command_text_case_type

	@property
	def Command_TextSlicingSide(self):
		return self._command_text_slicing_side
	
	@property
	def TextCase(self):
		return self._text_case

	@TextCase.setter
	def TextCase(self, value):
		self._text_case = value
		self.OnPropertyChanged("TextCase")
		self.OnPropertyChanged("CombineTextManipulate")

	@property
	def SlicingSide(self):
		return self._slicing_side

	@SlicingSide.setter
	def SlicingSide(self, value):
		self._slicing_side = value
		self.OnPropertyChanged("SlicingSide")
		self.OnPropertyChanged("CombineTextManipulate")

	@property
	def SlicingValue(self):
		return self._slicing_value

	@SlicingValue.setter
	def SlicingValue(self, value):
		self._slicing_value = value
		self.OnPropertyChanged("SlicingValue")
		self.OnPropertyChanged("CombineTextManipulate")

	@property
	def CombineTextManipulate(self):
		case = self.TextCase or ""
		side = self.SlicingSide or ""
		value = self.SlicingValue if self.SlicingValue else ""
		return "<{}:{}:{}>".format(case, side, value)		

	@property
	def CountSuccess(self):
		return self._count_success
	
	@CountSuccess.setter
	def CountSuccess(self, value):
		self._count_success = value
		self.OnPropertyChanged("CountSuccess")
		self.OnPropertyChanged("CountTotal")

	@property
	def CountFailed(self):
		return self._count_failed
	
	@CountFailed.setter
	def CountFailed(self, value):
		self._count_failed = value
		self.OnPropertyChanged("CountFailed")
		self.OnPropertyChanged("CountTotal")

	@property
	def CountTotal(self):
		return self.CountSuccess + self.CountFailed

	@property
	def HasError(self):
		return self._has_error
	
	@HasError.setter
	def HasError(self, value):
		self._has_error = value
		self.OnPropertyChanged("HasError")

	@property
	def ErrorListCombined(self):
		return self._error_list_combined
	
	@ErrorListCombined.setter
	def ErrorListCombined(self, value):
		self._error_list_combined = value
		self.OnPropertyChanged("ErrorListCombined")

	@property
	def DynamicParameters(self):
		return self._dynamic_params_collection

	@DynamicParameters.setter
	def DynamicParameters(self, value):
		self._dynamic_params_collection = value
		self.OnPropertyChanged("DynamicParameters")

	@property
	def DynamicParameterSet(self):
		return self._common_parameters

	@DynamicParameterSet.setter
	def DynamicParameterSet(self, value):
		self._common_parameters = value
		self.OnPropertyChanged("DynamicParameterSet")

	@property
	def SelectedItem(self):
		return self._selected_item

	@SelectedItem.setter
	def SelectedItem(self, value):
		self._selected_item = value
		self.OnPropertyChanged("SelectedItem")
		self.OnPropertyChanged("IsApplyButtonEnabled_SingleChoice")		# Enable the "Select" button

	@property
	def TemplateCollection(self):
		return self._template_collection

	@property
	def IsApplyButtonEnabled_SingleChoice(self):
		return True if self.SelectedItem is not None else False

	@property
	def TemplateImportFilePath(self):
		return self._template_import_file_path

	@TemplateImportFilePath.setter
	def TemplateImportFilePath(self, value):
		self._template_import_file_path = value
		self.OnPropertyChanged("TemplateImportFilePath")
		self.OnPropertyChanged("IsTemplateFileLoaded")

	@property
	def IsTemplateFileLoaded(self):
		return True if self.TemplateImportFilePath is not None else False
	
	# Methods
	# -------------------
	def _text_case_type_changed(self, sender):
		# type: (RadioButton) -> None
		"""Process based on radio button selected option. Here, param is RadioButton itself."""
		try:
			radio_button_name = sender.Name
			if radio_button_name == "Choice_Text_Title":
				self.TextCase = "title"
			elif radio_button_name == "Choice_Text_Upper":
				self.TextCase = "upper"
			elif radio_button_name == "Choice_Text_Lower":
				self.TextCase = "lower"
			else:
				self.TextCase = None
		except Exception as e:
			print("Command_TextCaseType failed:\n\n{}\n\n{}".format(e, traceback.format_exc()))

	def _text_slicing_side_changed(self, sender):
		# type: (RadioButton) -> None
		"""Process based on radio button selected option. Here, param is RadioButton itself."""
		try:
			radio_button_name = sender.Name
			if radio_button_name == "Choice_Slice_Left":
				self.SlicingSide = "left"
			elif radio_button_name == "Choice_Slice_Right":
				self.SlicingSide = "right"
			else:
				self.SlicingSide = None
		except Exception as e:
			print("Command_TextSlicingSide failed:\n\n{}\n\n{}".format(e, traceback.format_exc()))

	def template_import(self):
		template_list = self._template_iops.template_import()
		self._template_populate(template_list)

	def template_export(self, rich_text_box_object):
		try:
			extracted_text = extract_richtextbox_contents(rich_text_box_object)		# Extract text from RichTextBox
			if extracted_text:
				self._template_iops.template_export(extracted_text)
			else:
				TaskDialog.Show("Error", "Empty textbox.")
				return
		except Exception as e:
			print("Failed to generate preview:\n\n{}\n\n{}".format(e, traceback.format_exc()))

	def template_reload(self):
		template_list = self._template_iops.template_reload()
		self._template_populate(template_list)

	def error_output_show(self):
		template_md_file_list = ["TemplateOutput01.md", "TemplateOutput02.md"]
		template_variables = {
			"md_type_total_count" : self.CountTotal,
			"md_type_success_count" : self.CountSuccess,
			"md_type_failed_count" : self.CountFailed,
			"md_errors_list" : ""
		}
		if self.CountFailed > 0:
			# Building errors
			errors_list = ""
			for idx, (old_name, error_message) in enumerate(self.ErrorListCombined, start=1):
				errors_list += "{}. **{}** - {}\n".format(idx, old_name, error_message)

			template_variables["md_errors_list"] = (
				"### Failed Rename\n\n"
				"The following errors were raised while renaming type names -\n\n"
				"{}".format(errors_list)
			)
		sys_md = SysOutput_Markdown(PY_SCRIPT_PATH, template_md_file_list, template_variables)
		sys_md.show_error_output()

	def reset_text_manip(self):
		"""Reset all selected choices while doing text manipulation."""
		self.TextCase = None
		self.SlicingSide = None
		self.SlicingValue = 0
		
	def _add_text_transform_token_text(self, rtb):
		# type: (RichTextBox) -> str|None
		"""Combine the pending |Type Name| token (possibly already a chip) with `<case:side:value>`."""
		extracted_text = extract_richtextbox_contents(rtb)   # chip-aware, unlike TextRange
		if not extracted_text: return	# Text not found, so returning
		final_text = extracted_text + self.CombineTextManipulate
		return str(final_text)
	
	# -------------------------
	# Helper methods
	def _build_parameter_set(self):
		"""Build a set of parameters common to all checked items (intersection)."""
		checked_items = self._vm_tree_viewer.CheckedItems
		if not checked_items:
			self._common_parameters = set()
			return

		item_param_sets = []
		for item in checked_items:
			item_param_sets.append(set(item.ParameterObjectsList.keys()))
		self._common_parameters = set.intersection(*item_param_sets)	# Unpacking list into individual elements

	def make_parameter_button_set_from_group(self, group_data):
		# type: (GroupData_Renamer) -> None
		"""Same as make_parameter_button_set, but sourced from an already-held template's rows
		(ParameterSnapshot) instead of live tree selection - tree items for a grouped template
		are already unchecked/hidden by the time it can be edited, so CheckedItems is empty."""
		self.DynamicParameters.Clear()
		self._common_parameters.clear()

		rows = group_data.DataGridCollection
		if not rows or rows.Count == 0:
			TaskDialog.Show("Selection", "No items found for this template.")
			return

		item_param_sets = [set(row.ParameterSnapshot.keys()) for row in rows]
		self._common_parameters = set.intersection(*item_param_sets)
		if len(self._common_parameters) > 0:
			for par in sorted(self._common_parameters, key=str.lower):
				self.DynamicParameters.Add(par)
		else:
			TaskDialog.Show("Selection", "No common parameters found for this template's items.")

	def make_parameter_button_set(self):
		"""Make buttons from a parameter set."""
		self.DynamicParameters.Clear()
		self._common_parameters.clear()
		self._build_parameter_set()
		if len(self._common_parameters) > 0:
			for par in sorted(self._common_parameters, key=str.lower):
				self.DynamicParameters.Add(par)		# Add to collection
		else:
			TaskDialog.Show("Selection", "Selection required: Please pick a type.")
			return

	def _template_populate(self, template_list):
		if template_list is None:
			return  # user cancelled or nothing valid found
		self._template_collection.Clear()
		for line in template_list:
			self._template_collection.Add(line)

	def release_template_edit(self):
		self.EditingTemplate = None
		self.DynamicParameters.Clear()
		self._common_parameters.clear()

	def clear_dynamic_parameters(self):
		"""Clear the dynamic-parameter button set after a template has been applied to the list."""
		self.DynamicParameters.Clear()
		self._common_parameters.clear()