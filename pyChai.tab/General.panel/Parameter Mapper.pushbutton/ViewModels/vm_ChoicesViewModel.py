# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import clr

clr.AddReference("System")
from System.Collections.ObjectModel import ObservableCollection
from System.Windows import Visibility

from lib_WPF.Helpers.he_ViewModel_ViewModelBase import ViewModelBase
from lib_WPF.Helpers.he_RelayCommand import RelayCommand
from lib_WPF.Helpers.he_ViewModel_ViewModelBase_withValidationError import ViewModelBaseValidation

from Models.mo_ipy_cpy_subprocess import PySubprocess
from Models.mo_elem_selecter import RevitParameterCollection

from Helpers.he_validation_service import ValidationService

# ===============
# ---> VARIABLES <---
app = __revit__.Application                             # type:  Application
rvt_year = int(app.VersionNumber)

# ===============
# ---> CLASSES <---
class ChoiceRow(object):
	"""Initial default template for data template rows."""
	def __init__(self):
		self.SerialNumber = 0
		self.PrimarySort = False
		self.ParameterType = "Shared"
		self.RevitParameterValue = None
		self.ExcelColumnValue = None
		self.ParameterStorageType = None
		self.ParameterID = None
		self.ParameterObject = None
		self.ParameterDefinitionForgeType = None
		self.ParameterValueUnitType = None
		self.ParameterTypeIdentifyObjectStore = None


class ChoiceRowViewModel(ViewModelBaseValidation):
	"""Choices row view model for row item."""
	def __init__(self, parent_view_model, serial_number):
		super(ChoiceRowViewModel, self).__init__()
		# Target view model
		self._parent_view_model = parent_view_model  # type: ChoicesViewModel_MainWindow
		self._serial_number = serial_number
		self._primary_sort = False
		self._parameter_type = None
		self._revit_parameter_value = None
		self._excel_column_value = None
		self._parameter_storage_type = None
		self._parameter_id = None
		self._parameter_object = None
		self._parameter_definition_forge_type = None
		self._parameter_value_unit_type = None
		self._parameter_forgetype_type_id_object = None
		self._has_error = True				# Default Error
		self._error_messages = "Invalid"	# Default message
		self._error_tooltip = "Invalid"		# Default message

	# Property
	# -------------------
	@property
	def SerialNumber(self):
		return self._serial_number

	@SerialNumber.setter
	def SerialNumber(self, value):
		self._serial_number = value
		self.OnPropertyChanged("SerialNumber")

	@property
	def PrimarySort(self):
		return self._primary_sort

	@PrimarySort.setter
	def PrimarySort(self, value):
		self._primary_sort = value
		self.OnPropertyChanged("PrimarySort")
		# Notifying ChoicesViewModel_MainWindow parent window that button state have changed.
		self._parent_view_model.OnPropertyChanged("HasPrimarySort")
		self._parent_view_model.OnPropertyChanged("IsButtonEnabled")

	@property
	def ParameterType(self):
		return self._parameter_type

	@ParameterType.setter
	def ParameterType(self, value):
		self._parameter_type = value
		self.OnPropertyChanged("ParameterType")

	@property
	def RevitParameterValue(self):
		return self._revit_parameter_value

	@RevitParameterValue.setter
	def RevitParameterValue(self, value):
		self._revit_parameter_value = value
		self.OnPropertyChanged("RevitParameterValue")
		result_output = self._parent_view_model.LookupDictParams.get(value)
		if result_output:
			self.ParameterType = result_output[0]
			self.ParameterStorageType = result_output[1]
			# From Revit 2024, IntegerValue is obsolete. Therefore, use Value for 2024+.
			if rvt_year > 2023:
				self.ParameterID = result_output[4].Value
			else:
				self.ParameterID = result_output[4].IntegerValue
			self.ParameterObject = result_output[3]
			self.ParameterDefinitionForgeType = result_output[5]
			self.ParameterValueUnitType = result_output[6]
			self.ParameterTypeIdentifyObjectStore = result_output[7]
		else:
			self.ParameterType = None
			self.ParameterStorageType = None
			self.ParameterID = None
			self.ParameterObject = None
			self.ParameterDefinitionForgeType = None
			self.ParameterValueUnitType = None
			self.ParameterTypeIdentifyObjectStore = None
		# Notifying parent window about changes
		self._parent_view_model.OnPropertyChanged("AllRowsFilled")
		self._parent_view_model.OnPropertyChanged("IsButtonEnabled")
		self._parent_view_model.ValidateDuplicates()

	@property
	def ExcelColumnValue(self):
		return self._excel_column_value

	@ExcelColumnValue.setter
	def ExcelColumnValue(self, value):
		self._excel_column_value = value
		self.OnPropertyChanged("ExcelColumnValue")
		# Notifying parent window about changes
		self._parent_view_model.OnPropertyChanged("AllRowsFilled")
		self._parent_view_model.OnPropertyChanged("IsButtonEnabled")
		self._parent_view_model.ValidateDuplicates()

	@property
	def ParameterStorageType(self):
		return self._parameter_storage_type

	@ParameterStorageType.setter
	def ParameterStorageType(self, value):
		self._parameter_storage_type = value
		self.OnPropertyChanged("ParameterStorageType")

	@property
	def ParameterID(self):
		return self._parameter_id

	@ParameterID.setter
	def ParameterID(self, value):
		self._parameter_id = value
		self.OnPropertyChanged("ParameterID")

	@property
	def ParameterObject(self):
		return self._parameter_object

	@ParameterObject.setter
	def ParameterObject(self, value):
		self._parameter_object = value
		self.OnPropertyChanged("ParameterObject")

	@property
	def ParameterTypeIdentifyObjectStore(self):
		return self._parameter_forgetype_type_id_object

	@ParameterTypeIdentifyObjectStore.setter
	def ParameterTypeIdentifyObjectStore(self, value):
		self._parameter_forgetype_type_id_object = value
		self.OnPropertyChanged("ParameterTypeIdentifyObjectStore")

	@property
	def HasError(self):
		return self._has_error

	@HasError.setter
	def HasError(self, value):
		if self._has_error != value:
			self._has_error = value
			self.OnPropertyChanged("HasError")
			self.OnPropertyChanged("ShowErrorIcon")
			self.OnPropertyChanged("ShowCorrectIcon")

	@property
	def ErrorMessages(self):
		return self._error_messages

	@ErrorMessages.setter
	def ErrorMessages(self, value):
		if self._error_messages != value:
			self._error_messages = value
			self.OnPropertyChanged("ErrorMessages")
			self.ErrorTooltip = value  # Auto-update tooltip

	@property
	def ErrorTooltip(self):
		return self._error_tooltip

	@ErrorTooltip.setter
	def ErrorTooltip(self, value):
		if self._error_tooltip != value:
			self._error_tooltip = value
			self.OnPropertyChanged("ErrorTooltip")

	@property
	def IsFilled(self):
		"""Check if both Revit Parameter and Spreadsheet Column are filled."""
		has_param = self.RevitParameterValue and str(self.RevitParameterValue).strip()
		has_col = self.ExcelColumnValue and str(self.ExcelColumnValue).strip()
		return has_param and has_col

	@property
	def ShowErrorIcon(self):
		return Visibility.Visible if self._has_error else Visibility.Collapsed

	@property
	def ShowCorrectIcon(self):
		return Visibility.Collapsed if self._has_error else Visibility.Visible

	@property
	def ParameterDefinitionForgeType(self):
		return self._parameter_definition_forge_type

	@ParameterDefinitionForgeType.setter
	def ParameterDefinitionForgeType(self, value):
		self._parameter_definition_forge_type = value
		self.OnPropertyChanged("ParameterDefinitionForgeType")

	@property
	def ParameterValueUnitType(self):
		return self._parameter_value_unit_type

	@ParameterValueUnitType.setter
	def ParameterValueUnitType(self, value):
		self._parameter_value_unit_type = value
		self.OnPropertyChanged("ParameterValueUnitType")


class ChoicesViewModel_MainWindow(ViewModelBase):
	"""ViewModel for whole collection of choice rows, encapsuled in ScrollViewer."""
	def __init__(self, category_selection, element_selection, file_selection):
		super(ChoicesViewModel_MainWindow, self).__init__()
		self._category_selection = category_selection	# reference to shared instance
		self._element_selection = element_selection		# reference to shared instance
		self._file_selection = file_selection		# reference to shared instance

		self._rvt_param_list = []			# List used in XAML
		self._excel_column_list = []		# List used in XAML
		self._lookup_dict_params = {}

		# Initialise ObservableCollections for Revit parameters and Excel/LibreOffice columns
		self._rvt_parameter_items = ObservableCollection[str]()
		self._excel_column_items_headers = ObservableCollection[str]()

		# Command binding
		# The "row" value is already assigned by XAML CommandParameter. It means, the row is simply passed on as a
		# variable by the XAML to method. Here, "row" variable is used by AddRow and DeleteRow method.
		self._command_add_row = RelayCommand(lambda row: self.AddRow(row))
		self._command_delete_row = RelayCommand(lambda row: self.DeleteRow(row))
		self._choice_rows = ObservableCollection[ChoiceRowViewModel]()	# Row collections
		self._choice_rows.Add(ChoiceRowViewModel(self, 1))	# Initialise atleast one row
		self._internal_excel_data = {}		# Internal data for further use

	# Property
	# -------------------
	# Getting values from other classes
	@property
	def SelectedBuiltInCategory(self):
		"""Delegates to CategorySelection to get the current BuiltInCategory."""
		return self._category_selection.SelectedBuiltInCategory

	@property
	def SelectedElementsList(self):
		"""Delegates to ElementSelection to get the current Elements."""
		return self._element_selection.SelectedElements

	@property
	def FilePath(self):
		"""Delegates to FileSelection to get the selected file path."""
		return self._file_selection.SelectedFilePath

	@property
	def FileExtension(self):
		"""Delegates to FileSelection to get the selected file extension."""
		return self._file_selection.SelectedFileExtension

	# Choice row data
	# -------------------
	@property
	def ChoiceRows(self):
		"""Choice row property for returning full row."""
		return self._choice_rows

	# Excel column items
	# -------------------
	@property
	def ExcelColumnList(self):
		return self._excel_column_list

	@ExcelColumnList.setter
	def ExcelColumnList(self, value):
		self._excel_column_list = value or []		# Receiving values
		self._excel_column_items_headers.Clear()
		for item in self._excel_column_list:
			self._excel_column_items_headers.Add(item)
		self.OnPropertyChanged("ExcelColumnList")

	# Excel data for further internal use
	@property
	def InternalExcelDict(self):
		return self._internal_excel_data

	@InternalExcelDict.setter
	def InternalExcelDict(self, value):
		self._internal_excel_data = value or {}
		self.OnPropertyChanged("InternalExcelDict")

	# Revit Parameters items
	# -------------------
	@property
	def RevitParameterList(self):
		return self._rvt_parameter_items

	@RevitParameterList.setter
	def RevitParameterList(self, value):
		# Setting up collection of items when the data is detected
		self._rvt_param_list = value or []
		self._rvt_parameter_items.Clear()	# Clear existing items
		for item in self._rvt_param_list:
			self._rvt_parameter_items.Add(item)
		self.OnPropertyChanged("RevitParameterList")

	@property
	def LookupDictParams(self):
		return self._lookup_dict_params

	@LookupDictParams.setter
	def LookupDictParams(self, value):
		self._lookup_dict_params = value or {}
		self.OnPropertyChanged("LookupDictParams")

	# Exposing command to XAML file
	# -------------------
	@property
	def CanDeleteRow(self):
		return self._choice_rows.Count > 1		# Returns boolean

	@property
	def Command_AddRow(self):
		return self._command_add_row

	@property
	def Command_DeleteRow(self):
		return self._command_delete_row

	# Getting properties for button disabling
	@property
	def HasPrimarySort(self):
		"""Check if any row has PrimarySort selected."""
		for row in self._choice_rows:
			if row.PrimarySort:
				return True
		return False

	@property
	def HasAnyErrors(self):
		"""Check if any row has any error."""
		for row in self._choice_rows:
			if row.HasError:
				return True
		return False

	@property
	def AllRowsFilled(self):
		"""Check if all rows have both Revit Parameter and Spreadsheet Column filled."""
		if self._choice_rows.Count == 0:
			return False
		for row in self._choice_rows:
			has_param = row.RevitParameterValue and str(row.RevitParameterValue).strip()
			has_col = row.ExcelColumnValue and str(row.ExcelColumnValue).strip()
			if not (has_param and has_col):
				return False
		return True

	@property
	def IsButtonEnabled(self):
		"""Button is enabled only if a PrimarySort is selected, no errors exist and all rows are filled."""
		return self.HasPrimarySort and not self.HasAnyErrors and self.AllRowsFilled

	# Methods
	# -------------------
	def choices_list_setup(self):
		param_list, combined_dic_params = RevitParameterCollection(self.SelectedElementsList).list_making_from_dict()
		self.RevitParameterList = sorted(param_list, key=lambda name: name.lower())
		self.LookupDictParams = combined_dic_params

	def excel_dict_setup(self):
		"""Setting up Excel Dictionary."""
		excel_dict = PySubprocess().launch_pipeline_pyrevit(self.FilePath, self.FileExtension)
		self.ExcelColumnList = sorted(excel_dict.keys(), key=lambda name: name.lower())
		self.InternalExcelDict = excel_dict

	def _renumber_rows(self):
		"""Renumber rows after deleting rows."""
		index = 1	# Starting number for a row
		for row in self._choice_rows:
			row.SerialNumber = index
			index += 1
		self.ValidateDuplicates()	# Re-validate after renumbering

	def AddRow(self, row):
		"""Add a row below the current row."""
		current_index = self._choice_rows.IndexOf(row)			# Get index of selected row
		row_item = ChoiceRowViewModel(self, current_index + 2)	# Access entire row
		self._choice_rows.Insert(current_index + 1, row_item)	# Index starts from 0, therefore +1 is used.
		self._renumber_rows()
		self.OnPropertyChanged("CanDeleteRow")
		self.ValidateDuplicates()								# Validate duplicates

	def DeleteRow(self, row):
		"""Delete the current selected row."""
		if self._choice_rows.Count > 1:
			self._choice_rows.Remove(row)
			self._renumber_rows()
		self.OnPropertyChanged("CanDeleteRow")
		self.ValidateDuplicates()

	def reset_to_default_row_collection(self):
		"""Purge all rows, and add only 1 default row (also defined in __init__)."""
		self._choice_rows.Clear()
		self._choice_rows.Add(ChoiceRowViewModel(self, 1))
		self.ValidateDuplicates()

	def ValidateDuplicates(self):
		"""Validating all rows and updating the error states."""
		errors = ValidationService.validate(self._choice_rows)
		for row in self._choice_rows:
			serial = row.SerialNumber
			if serial in errors:
				row.HasError = True
				row.ErrorMessages = errors[serial]
			else:
				row.HasError = False
				row.ErrorMessages = ""

		# Notify UI that button state may have changed
		self.OnPropertyChanged("HasPrimarySort")
		self.OnPropertyChanged("HasAnyErrors")
		self.OnPropertyChanged("AllRowsFilled")
		self.OnPropertyChanged("IsButtonEnabled")