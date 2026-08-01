# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms, script
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback

from Autodesk.Revit.DB import Parameter, UnitUtils, StorageType, Transaction, ElementId
from Autodesk.Revit.UI import TaskDialog

clr.AddReference("System")

from Models.mo_failure_preprocessors import GroupEditPreProcessor
# ===============
# ---> VARIABLES <---
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
app = __revit__.Application
rvt_year = int(app.VersionNumber)

# `SpecTypeId` missing in pre-2023 versions.
if rvt_year > 2022:
	from Autodesk.Revit.DB import SpecTypeId
	YES_NO_TYPE = SpecTypeId.Boolean.YesNo
else:
	from Autodesk.Revit.DB import ParameterType
	YES_NO_TYPE = ParameterType.YesNo

# ===============
# ---> CLASSES <---
class ParameterApplication(object):
	def __init__(self, sorted_rows, transposed_excel_dict, mapped_dict):
		"""
		Constructor.
		
		:param sorted_rows: Choice Row list
		:type sorted_rows: ChoiceRowViewModel
		:param transposed_excel_dict: Transposed Excel Dictionary containing row data.
		:type transposed_excel_dict: dict
		:param mapped_dict: Mapped Dictionary containing row data.
		:type mapped_dict: dict
		"""
		self._sorted_rows = sorted_rows
		self._transposed_excel_dict = transposed_excel_dict
		self._mapped_dict = mapped_dict
		self._param_tuple_list = []
		self._paramters_readonly_string_errors = []
		self._elements_skipped_errors = []

	@staticmethod
	def _get_builtin_parameter(elem, param_type_recognize_object):
		"""
		Get a built-in Parameter object from an element, compatible with pre-2023 and 2023+.
		:param elem: The Revit element.
		:type elem: Element
		:param param_type_recognize_object: ForgeTypeId (2023+) or BuiltInParameter (pre-2023) identifying the parameter.
		:type param_type_recognize_object: ForgeTypeId | BuiltInParameter
		:return: Parameter object or None.
		:rtype: Parameter | None
		"""
		if rvt_year > 2022:
			return elem.GetParameter(param_type_recognize_object)
		else:
			return elem.get_Parameter(param_type_recognize_object)


	def _gather_parameter_collection(self):
		"""Collect all possible parameter object along with its value in a tuple list."""
		# Excluding PrimarySort parameter column
		_columns_excluding_primarysort_parameter = self._sorted_rows[1:]	# type: ChoiceRowViewModel
		for idx1, param_col_row in enumerate(_columns_excluding_primarysort_parameter):
			param_id = param_col_row.ParameterID
			param_storagetype = param_col_row.ParameterStorageType
			forge_type_id = param_col_row.ParameterDefinitionForgeType
			param_value_unit_type = param_col_row.ParameterValueUnitType
			param_type = param_col_row.ParameterType  # shared / project / built-in
			param_type_recognize_object = param_col_row.ParameterTypeIdentifyObjectStore

			for dict_key, dict_elem in self._mapped_dict.items():		# StorageType output value, element
				if dict_key in self._transposed_excel_dict:
					rest_of_values = self._transposed_excel_dict[dict_key]
					# Get parameter object based on shared / project / built-in
					# Since Revit 2025, get_Parameter is not recommended for BuiltInParameters.
					elem_param_object = None
					try:
						if param_type == "Built-In":
							elem_param_object = self._get_builtin_parameter(dict_elem, param_type_recognize_object)		# ForgeTypeID -> Built-in parameter
						elif param_type == "Shared":
							elem_param_object = dict_elem.get_Parameter(param_type_recognize_object)	# GUID -> Shared parameter
						elif param_type == "Project":
							elem_param_object = dict_elem.get_Parameter(param_type_recognize_object)	# Definition -> Project parameter
					except Exception as e:
						TaskDialog.Show("Error", "Failed to get parameter values. Check the values in the selected spreadsheet file.")
						continue
					specific_value = rest_of_values[idx1]

					# Skip empty/blank cells (already treated as "valid" by the checker)
					if specific_value is None or str(specific_value).strip() == "":
						continue

					try:
						if param_storagetype == StorageType.Integer:
							if forge_type_id != YES_NO_TYPE and param_value_unit_type is not None:
								# Convert to integer
								elem_param_internal_value = UnitUtils.ConvertToInternalUnits(int(specific_value),
																							 param_value_unit_type)
							else:
								# Normal integer
								elem_param_internal_value = int(specific_value)
						elif param_storagetype == StorageType.Double:
							if param_value_unit_type is not None:
								# Convert to double
								elem_param_internal_value = UnitUtils.ConvertToInternalUnits(float(specific_value),
																							 param_value_unit_type)
							else:
								# Normal double
								elem_param_internal_value = float(specific_value)
						else:
							# Normal string
							elem_param_internal_value = str(specific_value)
					except Exception as e:
						print("Skipping value '{}' for parameter id {}: {}".format(specific_value, param_id, e))
						continue
					collect_tuple = (elem_param_object, elem_param_internal_value, param_storagetype)
					self._param_tuple_list.append(collect_tuple)

	def _parameters_apply_old_method(self):
		"""Normal method."""
		tr = Transaction(doc, "Setting Multiple Parameters")
		f_opts = tr.GetFailureHandlingOptions()
		f_opts.SetFailuresPreprocessor(GroupEditPreProcessor())
		tr.SetFailureHandlingOptions(f_opts)
		tr.Start()
		try:
			skipped_elem_ids = []	# Temporary collection of skipped elements

			for tuple_val in self._param_tuple_list:
				param_object = tuple_val[0]		# type: Parameter
				param_value = tuple_val[1]		# Parameter value
				elem = param_object.Element

				# Skip elements which are part of linked model.
				if elem.Document.IsLinked:
					elem_id = elem.Id.Value if rvt_year > 2023 else elem.Id.IntegerValue
					if elem_id not in skipped_elem_ids:
						msg01 = "Element `{}` (Id {}) is part of a linked model, so it was skipped.".format(elem.Name, elem_id)
						self._elements_skipped_errors.append(msg01)
						skipped_elem_ids.append(elem_id)
						continue

				# Skip elements which are in a group, to bypass group-edit mode
				if elem.GroupId != ElementId.InvalidElementId:
					elem_id = elem.Id.Value if rvt_year > 2023 else elem.Id.IntegerValue
					if elem_id not in skipped_elem_ids:
						msg01 = "Element `{}` (Id {}) is part of a group, so it was skipped.".format(elem.Name, elem_id)
						self._elements_skipped_errors.append(msg01)
						skipped_elem_ids.append(elem_id)
						continue

				if not param_object.IsReadOnly:
					param_object.Set(param_value)
				else:
					msg01= "Element `{}` has readonly parameter `{}`".format(param_object.Element.Name, param_object.Definition.Name)
					self._paramters_readonly_string_errors.append(msg01)
					pass
			tr.Commit()
			return True
		except Exception as e:
			tr.RollBack()
			TaskDialog.Show("Error", "Parameters not applied. Check the values in the selected spreadsheet file.")
			print("Transaction failed: {}\n{}\n{}".format(e, '-' * 25, traceback.format_exc()))
			return False

	def apply_parameter_values(self):
		"""Apply parameter values."""
		try:
			self._gather_parameter_collection()
		except Exception as e:
			TaskDialog.Show("Error", "Failed to prepare parameter values. Check the spreadsheet data.")
			print("Gathering failed: {}\n{}\n{}".format(e, '-' * 25, traceback.format_exc()))
			return False
		return self._parameters_apply_old_method()

	def return_skipped_parameters_list(self):
		return self._paramters_readonly_string_errors

	def return_skipped_elements_list(self):
		return self._elements_skipped_errors