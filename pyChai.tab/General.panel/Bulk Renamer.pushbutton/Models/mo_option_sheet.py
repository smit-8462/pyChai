# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, ScheduleSheetInstance, ImageInstance, ViewType

from Helpers.he_extension_Collector import ItemsCollectionBase, get_id_value

# ===============
# ---> VARIABLES <---
uidoc = __revit__.ActiveUIDocument          #type: UIDocument
doc = __revit__.ActiveUIDocument.Document   #type: Document
app = __revit__.Application                 #type: UIApplication
rvt_year = int(app.VersionNumber)

# ===============
# ---> CLASSES <---
class SheetsCollection(ItemsCollectionBase):
	"""Collection class for sheets."""
	def __init__(self):
		self._sheets_list = FilteredElementCollector(doc).OfClass(ViewSheet).WhereElementIsNotElementType().ToElements()		# type: list[ViewSheet]
		self._dict_sheets_empty = {}		# type: dict[int, tuple]
		self._dict_sheets_filled = {}		# type: dict[int, tuple]
		super(SheetsCollection, self).__init__()

	def get_sheets_empty(self):
		# type: () -> dict[int, tuple]
		"""Get empty sheets."""
		return self._dict_sheets_empty

	def get_sheets_filled(self):
		# type: () -> dict[int, tuple]
		"""Get filled sheets."""
		return self._dict_sheets_filled

	def get_both_sheets(self):
		"""
		Get both filled and empty sheets.
		"""
		return self._dict_sheets_empty, self._dict_sheets_filled

	def _gather_all_items(self):
		# type: () -> dict[int, tuple]
		"""
		Collect all sheets.
		
		:return: Dictionary of sheets
		:rtype: dict[ElementId, tuple] , dict[ElementId, tuple]
		"""
		dict_combined = {}		# type: dict[int, tuple]
		for sht in self._sheets_list:
			sht_id = get_id_value(sht.Id)
			if sht.ViewType == ViewType.DrawingSheet and not sht.IsPlaceholder:
				sht_name = sht.Name
				# sht_id = sht.Id
				sht_number = sht.SheetNumber
				sht_combined_name = str(sht_number) + " - " + sht_name
				params_collection = self._get_all_type_parameters(sht)
				sht_count = sht.GetAllPlacedViews().Count
				if sht_count == 0:
					# Views placed on sheet are 0, so we'll count schedules in sheet first.
					sht_placed_schedule = FilteredElementCollector(doc, sht.Id).OfClass(ScheduleSheetInstance)
					sht_placed_schedule_count = sht_placed_schedule.GetElementCount()
					sht_placed_schedule_list = sht_placed_schedule.ToElements()		# type: list[ScheduleSheetInstance]
					sht_schedule_revisions_count = 0
					for st in sht_placed_schedule_list:
						if st.IsTitleblockRevisionSchedule:
							sht_schedule_revisions_count += 1
					if sht_placed_schedule_count - sht_schedule_revisions_count != 0:
						self._add_to_dict(sht_id, sht_combined_name, "Filled", params_collection, dict_combined)
					else:
						# The count is still 0, therefore we'll count images now, to confirm.
						sht_placed_image_count = FilteredElementCollector(doc, sht.Id).OfClass(ImageInstance).GetElementCount()
						if sht_placed_image_count > 0:
							self._add_to_dict(sht_id, sht_combined_name, "Filled", params_collection, dict_combined)
						else:
							# If not found, then it is an empty sheet.
							tuple_entry = (sht_combined_name, "Empty", params_collection)
							self._dict_sheets_empty[sht_id] = tuple_entry
							dict_combined[sht_id] = tuple_entry
				else:
					self._add_to_dict(sht_id, sht_combined_name, "Filled", params_collection, dict_combined)
		return dict_combined

	def _add_to_dict(self, sht_id, sht_name, sht_classification, params_collection, dict_combined):
		"""Helper method for repeating task."""
		tuple_entry = (sht_name, sht_classification, params_collection)
		self._dict_sheets_filled[sht_id] = tuple_entry
		dict_combined[sht_id] = tuple_entry
