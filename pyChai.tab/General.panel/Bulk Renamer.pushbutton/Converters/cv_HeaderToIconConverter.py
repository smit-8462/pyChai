# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback

clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
clr.AddReference("WindowsBase")

from System.Windows.Data import IValueConverter
from System.Windows.Media import Geometry


class HeaderToIconConverter(IValueConverter):
	"""Converts a tree node instance into its corresponding icon Geometry."""
	# Cache parsed geometries once, shared across all instances/conversions.
	# Shared icons
	_icon_tree_shared_category = Geometry.Parse("M348 305.5c-17.5 31.6-57.4 54.5-96 54.5-56.6 0-104-47.4-104-104s47.4-104 104-104c38.6 0 78.5 22.9 96 54.5 13.7-50.9 41.7-93.3 87-117.8C389.7 39.1 324.5 8 252 8 115 8 4 119 4 256S115 504 252 504c72.5 0 137.7-31.1 183-80.7-45.3-24.5-73.3-66.9-87-117.8z")
	_icon_tree_shared_type = Geometry.Parse("M309.9 480.3c-13.6 14.5-50 31.7-97.4 31.7-120.8 0-147-88.8-147-140.6v-144H18c-5.5 0-10-4.5-10-10v-68c0-7.2 4.5-13.6 11.3-16 62-21.8 81.5-76 84.3-117.1.8-11 6.5-16.3 16.1-16.3h70.9c5.5 0 10 4.5 10 10V125.2h83c5.5 0 10 4.4 10 9.9v81.7c0 5.5-4.5 10-10 10H200.2V360c0 34.2 23.7 53.6 68 35.8 4.8-1.9 9-3.2 12.7-2.2 3.5.9 5.8 3.4 7.4 7.9l22 64.3c1.8 5 3.3 10.6-.4 14.5z")
	_icon_tree_shared_family = Geometry.Parse("M64 128a112 112 0 11224 0 112 112 0 11-224 0zM0 464c0-97.2 78.8-176 176-176s176 78.8 176 176v6c0 23.2-18.8 42-42 42H42c-23.2 0-42-18.8-42-42v-6zM432 64a96 96 0 110 192 96 96 0 110-192zm0 240c79.5 0 144 64.5 144 144v22.4c0 23-18.6 41.6-41.6 41.6H389.6c6.6-12.5 10.4-26.8 10.4-42v-6c0-51.5-17.4-98.9-46.5-136.7 22.6-14.7 49.6-23.3 78.5-23.3z")
	_icon_tree_shared_instance = Geometry.Parse("M100.3 448H7.4V148.9h92.9V448ZM53.8 108.1C24.1 108.1 0 83.5 0 53.8c0-14.3 5.7-27.9 15.8-38S39.6 0 53.8 0s27.9 5.7 38 15.8 15.8 23.8 15.8 38c0 29.7-24.1 54.3-53.8 54.3Z")
	# Family Type - related icons
	_icon_tree_familytype_builtin = Geometry.Parse("M335.1 16c20.7 0 40.1 10 52.1 26.8l48.9 68.5c7.7 10.8 11.9 23.9 11.9 37.2L448 416c0 35.3-28.7 64-64 64l-320 0-6.5-.3C25.2 476.4 0 449.1 0 416L0 148.5c0-11.7 3.2-23.1 9.2-33l2.7-4.2 48.9-68.5c10.5-14.7 26.7-24.2 44.4-26.3l7.7-.5 222.1 0zM248 128l121.3 0-34.3-48-87.1 0 0 48zM78.7 128l121.3 0 0-48-87.1 0-34.3 48z")
	_icon_tree_familytype_loaded = Geometry.Parse("m214.6 310.6-64 64c-12.5 12.5-32.8 12.5-45.3 0l-64-64c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l9.4 9.4V32c0-17.7 14.3-32 32-32s32 14.3 32 32V274.7l9.4-9.4c12.5-12.5 32.8-12.5 45.3 0s12.5 32.8 0 45.3zm256 0-64 64c-12.5 12.5-32.8 12.5-45.3 0l-64-64c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l9.4 9.4V32c0-17.7 14.3-32 32-32s32 14.3 32 32V274.7l9.4-9.4c12.5-12.5 32.8-12.5 45.3 0s12.5 32.8 0 45.3zM32 512c-17.7 0-32-14.3-32-32s14.3-32 32-32H480c17.7 0 32 14.3 32 32s-14.3 32-32 32H32z")
	# Level - related icons
	_icon_tree_level_active = Geometry.Parse("M192 64C86 64 0 150 0 256S86 448 192 448H384c106 0 192-86 192-192S490 64 384 64H192zm192 96a96 96 0 110 192 96 96 0 110-192z")
	_icon_tree_level_stray = Geometry.Parse("M192 336a80 80 0 110-160 80 80 0 110 160Zm384-80c0 106-86 192-192 192H192C86 448 0 362 0 256S86 64 192 64H384c106 0 192 86 192 192ZM384 128H192c-70.7 0-128 57.3-128 128s57.3 128 128 128H384c70.7 0 128-57.3 128-128S454.7 128 384 128Z")
	# Sheet - related icons
	_icon_tree_sheet_empty = Geometry.Parse("M0 64V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V186.6c0-17-6.7-33.3-18.7-45.3L242.8 18.7C230.8 6.7 214.5 0 197.5 0H64C28.7 0 0 28.7 0 64Zm316.1 96H248c-13.3 0-24-10.7-24-24V67.9L316.1 160ZM176 48v88c0 39.8 32.2 72 72 72h88V448c0 8.8-7.2 16-16 16H64c-8.8 0-16-7.2-16-16V64c0-8.8 7.2-16 16-16H176Z")
	_icon_tree_sheet_filled = Geometry.Parse("M325.5 176 208 58.5V152c0 13.3 10.7 24 24 24h93.5ZM64 0H213.5c17 0 33.2 6.7 45.2 18.7L365.3 125.2c12 12 18.7 28.3 18.7 45.3V448c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V64C0 28.7 28.7 0 64 0Z")
	# View - related icons
	_icon_tree_view_onsheet = Geometry.Parse("M232 296c-13.3 0-24 10.7-24 24s10.7 24 24 24H392c13.3 0 24-10.7 24-24s-10.7-24-24-24H232Zm0-128c-13.3 0-24 10.7-24 24s10.7 24 24 24H392c13.3 0 24-10.7 24-24s-10.7-24-24-24H232ZM128 224a32 32 0 100-64 32 32 0 100 64Zm32 96a32 32 0 10-64 0 32 32 0 1064 0ZM0 128V384c0 35.3 28.7 64 64 64H448c35.3 0 64-28.7 64-64V128c0-35.3-28.7-64-64-64H64C28.7 64 0 92.7 0 128Zm64-16H448c8.8 0 16 7.2 16 16V384c0 8.8-7.2 16-16 16H64c-8.8 0-16-7.2-16-16V128c0-8.8 7.2-16 16-16Z")
	_icon_tree_view_offsheet = Geometry.Parse("M384 80c8.8 0 16 7.2 16 16V416c0 8.8-7.2 16-16 16H64c-8.8 0-16-7.2-16-16V96c0-8.8 7.2-16 16-16H384zM64 32C28.7 32 0 60.7 0 96V416c0 35.3 28.7 64 64 64H384c35.3 0 64-28.7 64-64V96c0-35.3-28.7-64-64-64H64z")
	_icon_tree_view_classification_3d = Geometry.Parse("M243.6 91.6l80.1 46.8c2.9 1.6 3 6.2 0 7.8l-95.2 55.6c-2.9 1.7-6.3 1.6-9 0l-95.2-55.6c-2.9-1.6-3-6.3 0-7.8l80.1-46.8V-0L-0 119.4V358.2l78.4-45.8V218.8c-.1-3.3 3.8-5.7 6.7-3.9l95.2 55.6c2.9 1.7 4.5 4.7 4.5 7.8V389.5c.1 3.3-3.8 5.7-6.7 3.9L98 346.8 19.6 392.6 224 512 428.4 392.6 350 346.8l-80.1 46.8c-2.8 1.7-6.8-.5-6.7-3.9V278.5c0-3.3 1.8-6.3 4.5-7.8L362.9 215c2.8-1.7 6.8.5 6.7 3.9v93.6l78.4 45.8V119.5L243.6.1V91.7z")
	_icon_tree_view_classification_plan = Geometry.Parse("M658.5 324.6V95.4H387.6v41.7h229.2v375h-83.3v41.7h208.4v-41.7h-83.3V366.2h229.2v520.9H658.6V699.6h-41.7v187.5H137.7V553.7h145.9V512H137.7V137h145.9V95.3H96.1v833.4h833.4V324.5zm166.7 83.3v416.7H658.5v62.5H887.7V407.9zM554.3 824.7H137.6v62.5h479.2V741.3h-62.5zm0-646h62.5v333.4h-62.5z")
	_icon_tree_view_classification_section = Geometry.Parse("M304.1 7.6c0-11.1-7.6-20.7-18.4-23.3s-21.9 2.5-27 12.4L193.1 125.3 33.2 150.7c-8.9 1.4-16.3 7.7-19.1 16.3s-.5 18 5.8 24.4l114.4 114.5-25.2 159.9c-1.4 8.9 2.3 17.9 9.6 23.2s16.9 6.1 25 2L291 416.1c8-4.1 13.1-12.4 13.1-21.4V7.6z")
	_icon_tree_view_classification_elevation = Geometry.Parse("M277.8 8.6c-12.3-11.4-31.3-11.4-43.5 0l-224 208c-9.6 9-12.8 22.9-8 35.1S18.8 272 32 272H48V448c0 35.3 28.7 64 64 64H400c35.3 0 64-28.7 64-64V272h16c13.2 0 25-8.1 29.8-20.3s1.6-26.2-8-35.1l-224-208zM240 320h32c26.5 0 48 21.5 48 48v96H192V368c0-26.5 21.5-48 48-48z")

	def Convert(self, value, targetType, parameter, culture):
		try:
			# We can't import RVT_TypologyName etc. here without a circular import risk,
			# so match by class name string instead - safe and decoupled from the model module.
			type_name = value.__class__.__name__
			header = getattr(value, "Header", None)

			if type_name == "RVT_TypologyName":
				# Root level: differentiate "Built-In" vs "Loaded" typologies by header text.
				if header == "Loaded":
					return self._icon_tree_familytype_loaded
				elif header == "Built-In":
					return self._icon_tree_familytype_builtin
				elif header == "On Sheet":
					return self._icon_tree_view_onsheet
				elif header == "Off Sheet":
					return self._icon_tree_view_offsheet
				elif header == "Empty":
					return self._icon_tree_sheet_empty
				elif header == "Filled":
					return self._icon_tree_sheet_filled
				elif header == "Active":
					return self._icon_tree_level_active
				elif header == "Stray":
					return self._icon_tree_level_stray
			elif type_name == "RVT_CategoryName":
				return self._icon_tree_shared_category
			elif type_name == "RVT_FamilyName":
				return self._icon_tree_shared_family
			elif type_name == "RVT_TypeName":
				return self._icon_tree_shared_type
			elif type_name == "RVT_InstanceName":
				return self._icon_tree_shared_instance
			elif type_name == "RVT_ViewType_Type":
				if header == "3D View":
					return self._icon_tree_view_classification_3d
				elif header in ("Detail View", "Section View"):
					return self._icon_tree_view_classification_section
				elif header in ("Floor Plan", "Drafting View", "Ceiling Plan", "Engineering Plan", "Area Plan"):
					return self._icon_tree_view_classification_plan
				elif header == "Elevation View":
					return self._icon_tree_view_classification_elevation
			return None		# Needed something to return back as a converter
		except Exception as e:
			print("Transaction failed: {}\n{}\n{}".format(e, '-' * 25, traceback.format_exc()))
			return None

	def ConvertBack(self, value, targetType, parameter, culture):
		raise NotImplementedError("ConvertBack is not supported.")
