# -*- coding: utf-8 -*-
# ---> IMPORTS <---
# import sys
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr

clr.AddReference("System")
clr.AddReference('System.Data')

from System.Collections.ObjectModel import ObservableCollection
from System.Collections.Generic import Dictionary
from System.Data import DataTable

from lib_WPF.Helpers.he_ViewModel_ViewModelBase_withValidationError import ViewModelBaseValidation

from ViewModels.vm_ChoicesViewModel import ChoicesViewModel_MainWindow
from ViewModels.vm_MainWindowViewModel import ElementSelection_MainWindow

from Models.mo_datatable import transpose_dict, valid_element_list_generator, DataTableOperations
from Models.mo_param_ops import ParameterApplication

# ===============
# ---> CLASSES <---
class PreviewWindowViewModel(ViewModelBaseValidation):
	"""Preview Window View Model."""
	def __init__(self, choices_vm, element_selection_vm, ext_event, ext_event_handler):
		super(PreviewWindowViewModel, self).__init__()
		self._choices_vm = choices_vm	# type: ChoicesViewModel_MainWindow
		self._element_selection_vm = element_selection_vm 	# type: ElementSelection_MainWindow

		self._data_column_headers = []
		self._data_rows = []
		self._mapping_dict = {}

		# Datagrid list
		self._datagrid_column_headers = ObservableCollection[str]()
		self._datagrid_rows_data = ObservableCollection[str]()
		self._dataview_datatable = DataTable()		# DataTable for preview contents

		# Cell validity map, keyed by "{RowIndex}|{ColumnName}" -> bool (True = valid)
		# Using a .NET Dictionary[str, bool] so it can be consumed directly from XAML via converter.
		self._cell_validity_map = Dictionary[str, bool]()

		# Cell tooltip map, same key scheme -> error message string (only populated for invalid cells)
		self._cell_error_map = Dictionary[str, str]()

		# Row-sibling-error map, SAME key scheme as CellValidityMap.
		self._row_sibling_error_map = Dictionary[str, bool]()

		self._error_textbox = []					# Error textbox
		self._has_errors = False					# Check if error is there
		self._is_apply_button_visible = False		# Apply button visibility

		# Values shared between preview_data_generate and apply_generated_values methods.
		self._sorted_rows_shared = None
		self._excel_dict_transposed_shared = None
		self._mapped_sorting_parameter_with_elements_dict_shared = None

		# Reuse the shared ExternalEvent created in MainWindow.
		# self._is_applying = False  # True while ExternalEvent.Execute() is in flight and running
		self.m_ExternalEvent = ext_event
		self.m_ExternalEventHandler = ext_event_handler
		self.m_ExternalEventHandler.passable_method = self.apply_generated_values

		self._has_user_clicked_on_final_apply_button = False

	# Property
	# --------------------
	@property
	def HasUserClickedOnFinalApplyButton(self):
		return self._has_user_clicked_on_final_apply_button

	@HasUserClickedOnFinalApplyButton.setter
	def HasUserClickedOnFinalApplyButton(self, value):
		self._has_user_clicked_on_final_apply_button = value
		self.OnPropertyChanged("HasUserClickedOnFinalApplyButton")

	@property
	def IsApplyButtonVisible(self):
		return self._is_apply_button_visible

	@IsApplyButtonVisible.setter
	def IsApplyButtonVisible(self, value):
		self._is_apply_button_visible = value
		self.OnPropertyChanged("IsApplyButtonVisible")

	@property
	def DataViewDataTable(self):
		return self._dataview_datatable

	@DataViewDataTable.setter
	def DataViewDataTable(self, value):
		self._dataview_datatable = value
		self.OnPropertyChanged("DataViewDataTable")

	@property
	def CellValidityMap(self):
		return self._cell_validity_map

	@CellValidityMap.setter
	def CellValidityMap(self, value):
		self._cell_validity_map = value
		self.OnPropertyChanged("CellValidityMap")

	@property
	def CellErrorMap(self):
		return self._cell_error_map

	@CellErrorMap.setter
	def CellErrorMap(self, value):
		self._cell_error_map = value
		self.OnPropertyChanged("CellErrorMap")

	@property
	def RowSiblingErrorMap(self):
		return self._row_sibling_error_map

	@RowSiblingErrorMap.setter
	def RowSiblingErrorMap(self, value):
		self._row_sibling_error_map = value
		self.OnPropertyChanged("RowSiblingErrorMap")

	@property
	def ErrorTextBoxDataFill(self):
		_joined_text = ""
		for index in range(len(self._error_textbox)):
			line = self._error_textbox[index]
			_joined_text += "{}. {}".format(index + 1, line)
			if index < len(self._error_textbox) - 1:
				_joined_text += "\n"
		return _joined_text

	@ErrorTextBoxDataFill.setter
	def ErrorTextBoxDataFill(self, value):
		self._error_textbox = value or []
		self.OnPropertyChanged("ErrorTextBoxDataFill")
		self.HasErrors = len(self._error_textbox) > 0

	@property
	def HasErrors(self):
		return self._has_errors

	@HasErrors.setter
	def HasErrors(self, value):
		self._has_errors = value
		self.OnPropertyChanged("HasErrors")

	# Methods
	# --------------------
	def preview_data_generate(self):
		# Generate columns
		self._prepare_data()
		DataTableOperations().datatable_operations(self._sorted_rows_shared,
		                                           self._excel_dict_transposed_shared,
		                                           self._mapped_sorting_parameter_with_elements_dict_shared,
		                                           self,
		                                           self._element_selection_vm)

	def _prepare_data(self):
		# Put row which has sorting selected at the top of list
		_sorted_rows = []
		_list_parameter_ids = []
		_selected_sorting_parameter_id = None
		_selected_sorting_parameter_object = None  # The parameter object is unique to that specific element
		_selected_sorting_storage_type = None
		_selected_sorting_parameter_name = None
		# It has selected rows
		for rows in self._choices_vm.ChoiceRows:		# type: ChoiceRowViewModel
			if rows.PrimarySort:
				_sorted_rows.insert(0, rows)
				_selected_sorting_parameter_id = rows.ParameterID
				_selected_sorting_parameter_object = rows.ParameterObject
				_selected_sorting_storage_type = rows.ParameterStorageType
				_selected_sorting_parameter_name = rows.RevitParameterValue
			else:
				_sorted_rows.append(rows)
				_param_id_general = rows.ParameterID

		# List of elements extracted ===> dictionary -> PrimarySort StorageType output value : Element
		_mapped_sorting_parameter_with_elements_dict = valid_element_list_generator(
			self._choices_vm.SelectedElementsList, _selected_sorting_parameter_id)

		# Transpose dictionary
		excel_dict_transposed = transpose_dict(self._choices_vm.InternalExcelDict, _sorted_rows)

		self._sorted_rows_shared = _sorted_rows
		self._excel_dict_transposed_shared = excel_dict_transposed
		self._mapped_sorting_parameter_with_elements_dict_shared = _mapped_sorting_parameter_with_elements_dict

	def apply_generated_values(self):
		"""
		Finalize and apply the mapped parameter values.
		"""
		# Apply values
		param_app = ParameterApplication(self._sorted_rows_shared,
										 self._excel_dict_transposed_shared,
										 self._mapped_sorting_parameter_with_elements_dict_shared)
		param_app.apply_parameter_values()
		self._element_selection_vm.ReadOnlyParameters = param_app.return_skipped_parameters_list()
		self._element_selection_vm.SkippedElementsDueToErrors = param_app.return_skipped_elements_list()
		
	def OnClosing(self, sender, event):
		"""
		Before the form is closed, everything must be disposed properly (including events, otherwise leaks will happen).
		"""
		if self.m_ExternalEventHandler is not None:
			self.m_ExternalEventHandler.passable_method = None  # unbind, don't dispose
			self.m_ExternalEventHandler.on_complete = None		# External event plain callback
		self.m_ExternalEvent = None
		self.m_ExternalEventHandler = None

	def finally_apply_values(self, on_complete=None):
		"""Finally apply the mapped parameter values, using External Event. \n
		Here, ``on_complete`` is a callback method, which is set right before ``Raise()`` call."""
		self.m_ExternalEventHandler.on_complete = on_complete	# stores the function reference
		self.m_ExternalEvent.Raise()							# queues the async work