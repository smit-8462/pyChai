# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import System 	# needed for `System.Type` generics
from System.Collections.Generic import List

from Autodesk.Revit.DB import (FilteredElementCollector, View3D, ViewDrafting, ViewPlan, ViewSection, ElementMulticlassFilter, 
							   ElementId, Element, Viewport, ScheduleSheetInstance)

from Helpers.he_extension_Collector import ItemsCollectionBase, get_id_value

# ===============
# ---> VARIABLES <---
uidoc = __revit__.ActiveUIDocument          #type: UIDocument
doc = __revit__.ActiveUIDocument.Document   #type: Document
app = __revit__.Application                 #type: UIApplication
rvt_year = int(app.VersionNumber)

# ===============
# ---> CLASSES <---
class ViewsCollection(ItemsCollectionBase):
	"""Collection class for views."""
	def __init__(self):
		# Creating an empty .NET Generic List of System.Type and making it multi-class filter
		self._viewtype_dict = {
			"ThreeD" : "3D View",
			"DraftingView" : "Drafting View",
			"FloorPlan" : "Floor Plan",
			"CeilingPlan" : "Ceiling Plan",
			"EngineeringPlan" : "Engineering Plan",
			"AreaPlan" : "Area Plan",
			"Detail" : "Detail View",
			"Section" : "Section View",
			"Elevation" : "Elevation View"
		}
		type_list = List[System.Type]()
		type_list.Add(View3D)
		type_list.Add(ViewDrafting)
		type_list.Add(ViewPlan)
		type_list.Add(ViewSection)
		multi_class_filter = ElementMulticlassFilter(type_list)		# A multi class filter list

		self._views_list = FilteredElementCollector(doc).WherePasses(multi_class_filter).WhereElementIsNotElementType().ToElements()	# type: list[ViewPlan]
		self._dict_views_on_sheet = {}		# type: dict[int, tuple]
		self._dict_views_off_sheet = {}		# type: dict[int, tuple]

		# Pre-2023 fallback: build set of placed view ids from Viewports + ScheduleSheetInstances
		if rvt_year <= 2022:
			self._placed_view_ids = set(get_id_value(vp.ViewId) for vp in FilteredElementCollector(doc).OfClass(Viewport))
			self._placed_view_ids.update(get_id_value(ssi.ScheduleId) for ssi in FilteredElementCollector(doc).OfClass(ScheduleSheetInstance))
		else:
			self._placed_view_ids = None
		super(ViewsCollection, self).__init__()

	def get_views_onsheet(self):
		# type: () -> dict[int, tuple]
		"""Get views on sheet."""
		return self._dict_views_on_sheet

	def get_views_offsheet(self):
		# type: () -> dict[int, tuple]
		"""Get views off sheet."""
		return self._dict_views_off_sheet

	def get_both_views(self):
		"""
		Get both on sheet and off sheet views.
		"""
		return self._dict_views_on_sheet, self._dict_views_off_sheet

	def _gather_all_items(self):
		# type: () -> dict[int, tuple]
		"""
		Collect all views.
		
		:return: Dictionary of views
		:rtype: dict[ElementId, tuple] , dict[ElementId, tuple]
		"""
		dict_combined = {}		# type: dict[int, tuple]
		for vw in self._views_list:
			if not vw.IsTemplate:
				vw_id = get_id_value(vw.Id)
				view_name = vw.Name		# View name
				# View type name
				view_type_id = vw.GetTypeId()
				view_type_elem = doc.GetElement(view_type_id) if view_type_id != ElementId.InvalidElementId else None
				vw_type_name = Element.Name.__get__(view_type_elem) if view_type_elem else "Unknown"

				# Get view types of view
				view_type_key = vw.ViewType.ToString()
				if view_type_key not in self._viewtype_dict: continue  	# skip views not in viewtype_dict
				viewtype_type = self._viewtype_dict[view_type_key]

				params_collection = self._get_all_type_parameters(vw)
				# Get views placed on sheets
				if rvt_year > 2022:
					from Autodesk.Revit.DB import ViewPlacementOnSheetStatus	# 2023+ only, import locally
					status = vw.GetPlacementOnSheetStatus()		# Only available from Revit 2023+
					is_on_sheet = (status == ViewPlacementOnSheetStatus.CompletelyPlaced or status == ViewPlacementOnSheetStatus.PartiallyPlaced)
				else:
					is_on_sheet = vw_id in self._placed_view_ids

				if is_on_sheet:
					view_classification = "On Sheet"
					if vw_id not in self._dict_views_on_sheet:
						tuple_entry = (view_name, vw_type_name, viewtype_type, view_classification, params_collection)
						self._dict_views_on_sheet[vw_id] = tuple_entry
						dict_combined[vw_id] = tuple_entry
				else:
					view_classification = "Off Sheet"
					if vw_id not in self._dict_views_off_sheet:
						tuple_entry = (view_name, vw_type_name, viewtype_type, view_classification, params_collection)
						self._dict_views_off_sheet[vw_id] = tuple_entry
						dict_combined[vw_id] = tuple_entry
		return dict_combined
