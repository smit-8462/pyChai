# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback

clr.AddReference("System")
import System

from Autodesk.Revit.DB import *

from lib_Snippets.snip_selection import selectElement_multiple_builtincategory


# ===============
# ---> VARIABLES <---
doc = __revit__.ActiveUIDocument.Document 	# type: Document
app = __revit__.Application                 # type: Application
rvt_year = int(app.VersionNumber)

if rvt_year > 2022:
	from Autodesk.Revit.DB import SpecTypeId
	YES_NO_TYPE = SpecTypeId.Boolean.YesNo
else:
	from Autodesk.Revit.DB import ParameterType
	YES_NO_TYPE = ParameterType.YesNo

# ===============
# ---> CLASSES <---
class ElementSelecter(object):
	def __init__(self, built_in_cat):
		# type: (str | BuiltInCategory) -> None
		if isinstance(built_in_cat, str):
			self.built_in_cat = self._builtincategory_from_string(built_in_cat)
		else:
			self.built_in_cat = built_in_cat	# already a BuiltInCategory

	@staticmethod
	def _builtincategory_from_string(category_string):
		"""Convert string like "OST_Walls" to BuiltInCategory.OST_Walls."""
		if not category_string:
			return None
		try:
			return getattr(BuiltInCategory, category_string)
		except AttributeError:
			print("Invalid BuiltInCategory: {}".format(category_string))
			return None

	def select_all(self):
		"""
		Select all elements in the model.
		:return: List of elements.
		:rtype: list[Element]
		"""
		return FilteredElementCollector(doc).OfCategory(self.built_in_cat).WhereElementIsNotElementType().ToElements()

	def elem_select_manual(self):
		"""
		Select elements manually in the model.
		:return: List of elements.
		:rtype: list[Element]
		"""
		return selectElement_multiple_builtincategory(self.built_in_cat)


class RevitParameterCollection(object):
	def __init__(self, element_list):
		"""
		Prepares a list of parameters for WPF execution.
		:param element_list: List of elements.
		:type element_list: list[Element]
		"""
		self._element_list = element_list

	def _extract_parameters_from_elements(self):
		"""
		Extract parameters of a unique element from the list of elements
		:return: A dictionary having all parameters of an unique element.
		:rtype: dict
		"""
		unique_element = []
		param_dict = {}

		for elem in self._element_list:
			# From Revit 2024, IntegerValue is obsolete. Therefor, use Value for 2024+ .
			if rvt_year > 2023:
				elem_type_id = elem.GetTypeId().Value
			else:
				elem_type_id = elem.GetTypeId().IntegerValue
			if not elem_type_id in unique_element:
				unique_element.append(elem_type_id)
				param_map = elem.ParametersMap
				for pr in param_map:  # type: Parameter
					try:
						param_id = pr.Id	# It is used just for checking duplicate parameter ID.
						if param_id not in param_dict:
							if not pr.IsReadOnly and pr.StorageType not in (StorageType.ElementId, None):
								param_name = pr.Definition.Name
								param_storage_type = pr.StorageType
								if param_storage_type == StorageType.Double:
									param_value_unit_type = pr.GetUnitTypeId() if rvt_year > 2020 else pr.DisplayUnitType
								else:
									param_value_unit_type = None

								if rvt_year > 2022:
									# GetDataType() and GetTypeId() only exist from Revit 2022 onward.
									param_definition_forge_type = pr.Definition.GetDataType()
									get_forgetype_param_type_id = pr.GetTypeId()
									get_type = get_forgetype_param_type_id.TypeId
									get_type_name = get_type.split(":")[0]
									# Here, param_type_identify_object_store is used to store the parameter, which will
									# be useful for identification of getting parameters based on parameter type, such
									# as built-in / shared / project parameter.
									if get_type_name == "revit.local.shared":
										param_type_string = "Shared"
										shared_guid = pr.GUID
										param_type_identify_object_store = shared_guid		# GUID for shared parameter
									elif get_type_name == "revit.local.project":
										param_type_string = "Project"
										param_type_identify_object_store = pr.Definition
									else:
										param_type_string = "Built-In"
										param_type_identify_object_store = get_forgetype_param_type_id	# ForgeTypeId for built-in parameters.
								else:
									# Pre-2023 fallback - classify with the legacy IsShared / BuiltInParameter API.
									from Autodesk.Revit.DB import ParameterType
									is_yesno = False
									try:
										is_yesno = pr.Definition.ParameterType == ParameterType.YesNo
									except Exception:
										pass
									param_definition_forge_type = YES_NO_TYPE if is_yesno else None
									if pr.IsShared:
											param_type_string = "Shared"
											param_type_identify_object_store = pr.GUID
									else:
										bip = getattr(pr.Definition, "BuiltInParameter", BuiltInParameter.INVALID)
										if bip != BuiltInParameter.INVALID:
											param_type_string = "Built-In"
											param_type_identify_object_store = bip        # BuiltInParameter enum, used with get_Parameter()
										else:
											param_type_string = "Project"
											param_type_identify_object_store = pr.Definition

								if param_id not in param_dict:
									param_dict[param_id] = (param_name, param_type_string, param_storage_type, elem_type_id,
															pr, param_definition_forge_type, param_value_unit_type,
															param_type_identify_object_store)
					except Exception as ex:
						print("Skipping parameter due to error: {}".format(ex))
						continue
		return param_dict

	def list_making_from_dict(self):
		"""
		Creates a list from a dictionary.
		:return: List & dictionary for ComboBox and WPF row items.
		:rtype: dict | list
		"""
		param_dict = self._extract_parameters_from_elements()
		param_list = []
		combined_dic_params = {}

		for param_key, param_value in param_dict.items():
			param_name = param_value[0]
			combined_dic_params[param_name] = (
				param_value[1], param_value[2], param_value[3], param_value[4], param_key, param_value[5],
				param_value[6], param_value[7])
			param_list.append(param_name)

		return param_list, combined_dic_params

# ===============
# ---> METHODS <---
def get_builtin_category(category_object):
	# type: (Category) -> BuiltInCategory | None
	"""Get the Builtin category for Revit 2020 till Revit 2027.

	:param category_object: Category object
	:type category_object: Category
	"""
	if rvt_year > 2022:
		return category_object.BuiltInCategory
	else:
		category_id_value = category_object.Id.IntegerValue
		return System.Enum.ToObject(BuiltInCategory, category_id_value) if category_id_value < 0 else None

def category_in_model_list():
	"""
	List total available categories in model.
	:return: List of tuples (category_name, BuiltInCategory)
	:rtype: list
	"""
	fec01 = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()

	cat_dict = {}
	for elem in fec01:
		cat = elem.Category
		if cat:
			if cat.Name not in cat_dict:
				if (cat.CategoryType in (CategoryType.Model, CategoryType.Annotation)
				and not cat.IsTagCategory and cat.IsVisibleInUI and cat.AllowsBoundParameters):
					builtincat = get_builtin_category(cat)
					if builtincat is None: 
						continue
					instance_count = FilteredElementCollector(doc).WherePasses(
						ElementCategoryFilter(builtincat)).WhereElementIsNotElementType().GetElementCount()
					if instance_count > 1:
						cat_dict[cat.Name] = builtincat

	# Sort list by category name
	cat_dict_sort = sorted(cat_dict.items(), key=lambda item: item[0])
	return cat_dict_sort