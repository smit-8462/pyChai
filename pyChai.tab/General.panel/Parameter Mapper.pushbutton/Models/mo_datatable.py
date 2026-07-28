# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import os, clr
from collections import OrderedDict

from Autodesk.Revit.DB import *
clr.AddReference("System")
from System.Data import DataTable
from System import Array, Object, Tuple, Collections
from System.Collections.Generic import Dictionary, List

from lib_Document.doc_parameter import param_output

# ===============
# ---> VARIABLES <---
app = __revit__.Application                             # type:  Application
rvt_year = int(app.VersionNumber)

if rvt_year > 2022:
	YES_NO_TYPE = SpecTypeId.Boolean.YesNo
else:
	from Autodesk.Revit.DB import ParameterType
	YES_NO_TYPE = ParameterType.YesNo

# ===============
# ---> METHODS <---
def transpose_dict(existing_dictionary, mapped_columns):
	"""
	Transpose dictionary from existing dictionary extracted from Excel.
	:param existing_dictionary: Existing dictionary.
	:type existing_dictionary: dict
	:param mapped_columns: Mapped columns.
	:type mapped_columns: list
	:return: Transposed dictionary.
	:rtype: dict
	"""
	# Adding actual mapped columns into new dictionary
	actual_mapped_columns_dict = {}
	for col in mapped_columns:
		excel_col_name = col.ExcelColumnValue  # extract the string key
		if excel_col_name and excel_col_name in existing_dictionary:
			actual_mapped_columns_dict[excel_col_name] = existing_dictionary[excel_col_name]

	if not actual_mapped_columns_dict:
		return {}

	# Use OrderedDict to guarantee that PrimarySort column stays first. It retains order
	ordered = OrderedDict()
	for col in mapped_columns:  # iterate mapped_columns again, not the dict
		excel_col_name = col.ExcelColumnValue
		if excel_col_name in actual_mapped_columns_dict:
			ordered[excel_col_name] = actual_mapped_columns_dict[excel_col_name]

	# Transposing dictionary
	transposed_new_dict = {}
	unpacked_values = zip(*ordered.values())
	for row in unpacked_values:
		dict_key = row[0]  # now guaranteed to be PrimarySort column value
		dict_value = row[1:]
		transposed_new_dict[dict_key] = dict_value
	return transposed_new_dict


def valid_element_list_generator(selected_element_list, sorting_element_parameter_id):
	"""
	Gathering elements based on PrimarySort parameter, by checking eligibility of elements based on element type id
	(1-time checking for unique id).
	:param selected_element_list: The SelectedElementsList property of ChoicesVM
	:type selected_element_list: list
	:param sorting_element_parameter_id: ID of PrimarySort parameter.
	:type sorting_element_parameter_id: int
	:return: A list of eligible & not eligible elements
	:rtype: dict
	"""
	mapped_sorting_parameter_with_elements_dict = {}

	for elem in selected_element_list:  # type: Element
		elem_param_map = elem.ParametersMap
		if rvt_year > 2023:		# From Revit 2024, IntegerValue is obsolete. Therefor, use Value for 2024+ .
			pr_id_list = [pr.Id.Value for pr in elem_param_map]
		else:
			pr_id_list = [pr.Id.IntegerValue for pr in elem_param_map]
		if sorting_element_parameter_id in pr_id_list:
			# Getting the parameter object of this element by using the iterator, using existing PrimarySort id.
			if rvt_year > 2023:		# From Revit 2024, IntegerValue is obsolete. Therefor, use Value for 2024+ .
				matched_elem_param = next((pr for pr in elem_param_map if pr.Id.Value == sorting_element_parameter_id), None)
			else:
				matched_elem_param = next((pr for pr in elem_param_map if pr.Id.IntegerValue == sorting_element_parameter_id), None)
			dict_key = param_output(matched_elem_param)		# StorageType output value of parameter
			if dict_key is not None:
				if dict_key not in mapped_sorting_parameter_with_elements_dict:
					# dictionary --> PrimarySort StorageType output value : Element
					mapped_sorting_parameter_with_elements_dict[dict_key] = elem
	return mapped_sorting_parameter_with_elements_dict


class DataTableOperations(object):
	def datatable_operations(self, sorted_rows, transposed_excel_dict, mapped_dict,
							 preview_window_vm, element_selection_vm):
		"""
		Data Table Operations, simultaneously preparing parameter setting operations and
		validation check for each cell in the DataTable.
		:param sorted_rows: Sorted rows
		:type sorted_rows: ChoiceRowViewModel
		:param transposed_excel_dict: Transposed Excel Dictionary containing row data.
		:type transposed_excel_dict: dict
		:param mapped_dict: Mapped Dictionary containing row data.
		:type mapped_dict: dict
		:param preview_window_vm: PreviewWindow ViewModel instance (use as self.PreviewWindowViewModel)
		:type preview_window_vm: PreviewWindowViewModel
		:param element_selection_vm: ElementSelection MainWindow ViewModel instance
		:type element_selection_vm: ElementSelection_MainWindow
		"""
		new_table = DataTable()  # Create new instance of data table everytime.
		_column_storage_types = []		# list of (column_name, StorageType), list index similar to DataTable columns.
		_dict_params_column_related = {}		# Dictionary for storing parameter object based on its properties.

		for row in sorted_rows:
			rvt_param_col = row.RevitParameterValue
			rvt_param_storage_type = row.ParameterStorageType
			rvt_param_object = row.ParameterObject
			rvt_forge_type = row.ParameterDefinitionForgeType
			if rvt_param_col:
				new_table.Columns.Add(rvt_param_col)		# Column add to DataTable
				_column_storage_types.append((rvt_param_col, rvt_param_storage_type, rvt_forge_type))
				_dict_params_column_related[(rvt_param_col, rvt_param_storage_type)] = rvt_param_object

		for dict_key in mapped_dict:		# StorageType output value, like Mark 101,etc.
			if dict_key in transposed_excel_dict:
				dict_value = transposed_excel_dict[dict_key]
				rest_of_values = list(dict_value)	# Converting python tuple to list so that .NET can read the values
				# Convert to a .NET object array so that DataTable can read individual values.
				# To keep the dict_key as the first column value (PrimarySort value), prepend it.
				full_row = [dict_key] + rest_of_values
				net_row = Array[Object]([str(v) if v is not None else "" for v in full_row])
				new_table.Rows.Add(net_row)

		# Sort columns by using first column in ascending order. Here, ASC = Ascending order
		first_col = new_table.Columns[0].ColumnName
		new_table.DefaultView.Sort = "{} ASC".format(first_col)

		# Check validation for every cell.
		_new_validity_map = Dictionary[str, bool]()
		_new_error_map = Dictionary[str, str]()
		_error_entries = []					# list of (row_key, col_name, line) tuples (unsorted for now)
		_unique_error_rows_count = set()	# Any row having any error will be added to this set. Used only for counting

		first_col_name = _column_storage_types[0][0] if _column_storage_types else None	  # Getting RevitParameterValue
		_row_keys = []

		# Building validity map & error map based on Excel values
		for row_index in range(new_table.Rows.Count):
			data_row = new_table.Rows[row_index]		# Gets collection of rows in data table
			row_key = str(data_row[first_col_name]) if first_col_name else str(row_index)	# Index of 1st column
			_row_keys.append(row_key)
			# (rvt_param_col, rvt_param_storage_type, rvt_forge_type)
			for col_name, storage_type, forge_type_id in _column_storage_types:
				cell_value = data_row[col_name]		# Getting row value based on column name
				is_valid = self._validate_value(cell_value, storage_type, forge_type_id)	# Validation check
				cell_key = "{}|{}".format(row_key, col_name)
				_new_validity_map[cell_key] = is_valid
				if not is_valid:		# If invalid, adding it to error map
					_new_error_map[cell_key] = self._build_error_message(cell_value, storage_type, forge_type_id)
					error_line = self._build_error_line(first_col_name, row_key, col_name, cell_value, storage_type, forge_type_id)
					_error_entries.append((row_key, col_name, error_line))
					_unique_error_rows_count.add(row_key)

		_new_row_sibling_error_map = Dictionary[str, bool]()
		_column_names_only = [col_name for col_name, _, _ in _column_storage_types]		# Using only rvt_param_col

		# Building row error map if a row has any error (for mild background color in WPF)
		for row_key in _row_keys:
			for this_col in _column_names_only:
				this_cell_key = "{}|{}".format(row_key, this_col)		# It will be using in WPF View.
				has_other_error = False
				for other_col in _column_names_only:
					if other_col == this_col:
						continue  # exclude only THIS column, not the whole row
					other_cell_key = "{}|{}".format(row_key, other_col)
					if not _new_validity_map[other_cell_key]:
						has_other_error = True
						break
				_new_row_sibling_error_map[this_cell_key] = not has_other_error

		preview_window_vm.CellValidityMap = _new_validity_map
		preview_window_vm.CellErrorMap = _new_error_map
		preview_window_vm.RowSiblingErrorMap = _new_row_sibling_error_map

		# Counting the processed elements for updating the count in MainWindow.
		count_skipped_elements = element_selection_vm.ElementsTotal - new_table.Rows.Count
		count_datatable_errors = len(_unique_error_rows_count)
		element_selection_vm.ElementsErrorsValidated = count_datatable_errors
		element_selection_vm.ElementsSkipped = count_skipped_elements
		if count_datatable_errors:
			preview_window_vm.IsApplyButtonVisible = False
		else:
			preview_window_vm.IsApplyButtonVisible = True

		# Sort _error_entries by row_key
		_sorted_error_entries = sorted(_error_entries, key=lambda entry: (entry[0], entry[1]))
		_error_lines = [entry[2] for entry in _sorted_error_entries]

		preview_window_vm.ErrorTextBoxDataFill = _error_lines
		# For triggering the OnPropertyChanged property change event, assign a new instance to existing property.
		preview_window_vm.DataViewDataTable = new_table


	def _validate_value(self, value, storage_type, forge_type):
		"""
		Validate a cell value against a storage type.
		:param value: The cell value to validate.
		:type value: str
		:param storage_type: The storage type to validate against.
		:type storage_type: StorageType
		:param forge_type: The forge type to validate against.
		:type forge_type: ForgeTypeId
		:return: True if the cell value is valid, else False.
		:rtype: bool
		"""
		if value is None:
			return True
		val = str(value).strip()
		if val == "":
			return True
		try:
			if storage_type == StorageType.Integer:
				if forge_type == YES_NO_TYPE:
					if int(val) in (0,1):
						return True
					else:
						return False
				else:
					int(val)
			elif storage_type == StorageType.Double:
				float(val)
			elif storage_type == StorageType.ElementId:
				int(val)
			return True
		except:
			return False

	def _build_error_message(self, value, storage_type, forge_type):
		"""
		Building an error tooltip message for potential invalid cell.
		:param value: The cell value to validate.
		:type value: str
		:param storage_type: The storage type to validate against.
		:type storage_type: StorageType
		:param forge_type: The forge type to validate against.
		:type forge_type: ForgeTypeId
		:return: The error tooltip message.
		:rtype: str
		"""
		_expected_label = {
			StorageType.Integer: "an Integer",
			StorageType.Double: "a Number",
			StorageType.ElementId: "an Element ID",
			StorageType.String: "a String"
		}
		if forge_type == YES_NO_TYPE:
			expected = "a Boolean (0 or 1)"
		else:
			expected = _expected_label.get(storage_type, "a different value")
		return "Invalid value '{}'. Expected {}.".format(value, expected)

	def _build_error_line(self, primary_sort_col_name, row_key, col_name, value, storage_type, forge_type):
		"""
		Building an error line for the error textbox. It includes column name, PrimarySort value, the actual value, and the reason.
		Example - Structural (row A01): "y5h" — Expected an Integer.
		:param primary_sort_col_name: The primary sort column name.
		:type primary_sort_col_name: str
		:param row_key: The row key.
		:type row_key: str
		:param col_name: The primary sort column name.
		:type col_name: str
		:param value: The actual value.
		:type value: str
		:param storage_type: The storage type to validate against.
		:type storage_type: StorageType
		:param forge_type: The forge type to validate against.
		:type forge_type: ForgeTypeId
		:return: The error message for the error textbox.
		:rtype: str
		"""
		_expected_label = {
			StorageType.Integer: "an Integer",
			StorageType.Double: "a Number",
			StorageType.ElementId: "an Element ID",
			StorageType.String: "a String",
		}
		if forge_type == YES_NO_TYPE:
			expected = "a Boolean Integer (0 or 1)"
		else:
			expected = _expected_label.get(storage_type, "a different value")
		return "{} {} - Expected {} in {}, got \"{}\"".format(primary_sort_col_name, row_key, expected, col_name, value)

