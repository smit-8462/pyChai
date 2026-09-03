# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from Autodesk.Revit.DB import FilteredElementCollector, Level

from Helpers.he_extension_Collector import ItemsCollectionBase, get_id_value

# ===============
# ---> VARIABLES <---
uidoc = __revit__.ActiveUIDocument          #type: UIDocument
doc = __revit__.ActiveUIDocument.Document   #type: Document
app = __revit__.Application                 #type: UIApplication
rvt_year = int(app.VersionNumber)

# ===============
# ---> CLASSES <---
class LevelsCollection(ItemsCollectionBase):
	"""Collection class for levels."""
	def __init__(self):
		self._levels_list = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType().ToElements()		# type: list[Level]
		self._dict_levels_active = {}		# type: dict[int, tuple]
		self._dict_levels_stray = {}		# type: dict[int, tuple]
		super(LevelsCollection, self).__init__()

	def get_levels_active(self):
		# type: () -> dict[int, tuple]
		"""Get active levels."""
		return self._dict_levels_active

	def get_levels_stray(self):
		# type: () -> dict[int, tuple]
		"""Get stray levels."""
		return self._dict_levels_stray

	def get_both_levels(self):
		"""
		Get both active and stray levels.
		"""
		return self._dict_levels_active, self._dict_levels_stray

	def _gather_all_items(self):
		# type: () -> dict[int, tuple]
		"""
		Collect all levels.
		
		:return: Dictionary of levels
		:rtype: dict[ElementId, tuple] , dict[ElementId, tuple]
		"""
		dict_combined = {}		# type: dict[int, tuple]
		for lvl in self._levels_list:
			lvl_id = get_id_value(lvl.Id)
			if not lvl.Document.IsLinked:
				lvl_name = lvl.Name
				params_collection = self._get_all_type_parameters(lvl)
				if lvl.FindAssociatedPlanViewId:
					lvl_classification = "Active"
					if lvl_id not in self._dict_levels_active:
						tuple_entry = (lvl_name, lvl_classification, params_collection)
						self._dict_levels_active[lvl_id] = tuple_entry
						dict_combined[lvl_id] = tuple_entry
				else:
					lvl_classification = "Stray"
					if lvl_id not in self._dict_levels_stray:
						tuple_entry = (lvl_name, lvl_classification, params_collection)
						self._dict_levels_stray[lvl_id] = tuple_entry
						dict_combined[lvl_id] = tuple_entry
		return dict_combined
