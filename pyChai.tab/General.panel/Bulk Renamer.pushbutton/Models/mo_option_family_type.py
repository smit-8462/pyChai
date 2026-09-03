# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from Autodesk.Revit.DB import FilteredElementCollector, ElementType, Element, FamilySymbol

from Helpers.he_extension_Collector import ItemsCollectionBase, get_id_value

# ===============
# ---> VARIABLES <---
uidoc = __revit__.ActiveUIDocument          #type: UIDocument
doc = __revit__.ActiveUIDocument.Document   #type: Document
app = __revit__.Application                 #type: UIApplication
rvt_year = int(app.VersionNumber)

# ===============
# ---> CLASSES <---
class TypesCollection(ItemsCollectionBase):
	"""Collection class for family types."""	
	def __init__(self):
		self._element_type_list = FilteredElementCollector(doc).WhereElementIsElementType().ToElements()	# type: list[ElementType]
		self._dict_types_builtin = {}			# type: dict[int, tuple]
		self._dict_types_loaded = {}			# type: dict[int, tuple]
		super(TypesCollection, self).__init__()

	def get_builtin_types(self):
		# type: () -> dict[int, tuple]
		"""Get all built-in family types."""
		return self._dict_types_builtin

	def get_loaded_types(self):
		# type: () -> dict[int, tuple]
		"""Get all loaded family types."""
		return self._dict_types_loaded

	def get_both_types(self):
		"""
		Get both built-in and loaded family types.
		"""
		return self._dict_types_builtin, self._dict_types_loaded

	def _gather_all_items(self):
		# type: () -> dict[int, tuple]
		"""
		Collect all element types.
		
		:return: Dictionary of built-in and loaded family element types
		:rtype: dict[ElementId, tuple] , dict[ElementId, tuple]
		"""
		dict_combined = {}		# type: dict[int, tuple]
		for et in self._element_type_list:
			et_id = get_id_value(et.Id)
			et_cat = et.Category
			et_family_name = et.FamilyName
			et_can_rename = et.CanBeRenamed
			et_name = Element.Name.__get__(et)
			if et_cat and et_can_rename and et_name:
				et_cat_name = et_cat.Name if et_cat else None
				params_collection = self._get_all_type_parameters(et)	# Has dictionary -> Parameter name : Parameter value
				if isinstance(et, FamilySymbol):
					et_classification = "Loaded"
					if et_id not in self._dict_types_loaded:
						entry = (et_cat_name, et_family_name, et_name, et_classification, params_collection)
						self._dict_types_loaded[et_id] = entry
						dict_combined[et_id] = entry
				else:
					et_classification = "Built-In"
					if et_id not in self._dict_types_builtin:
						entry = (et_cat_name, et_family_name, et_name, et_classification, params_collection)
						self._dict_types_builtin[et_id] = entry
						dict_combined[et_id] = entry
		return dict_combined
