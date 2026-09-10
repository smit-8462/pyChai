# -*- coding: utf-8 -*-
import re
from abc import ABCMeta, abstractmethod

from Autodesk.Revit.DB import ElementId
import System

# ===============
# ---> VARIABLES <---
uidoc = __revit__.ActiveUIDocument          #type: UIDocument
doc = __revit__.ActiveUIDocument.Document   #type: Document
app = __revit__.Application                 #type: UIApplication
rvt_year = int(app.VersionNumber)

# ===============
# ---> METHODS <---
def get_id_value(element_id):
	# type: (ElementId) -> int
	"""Extract the value from an ElementId."""
	if rvt_year > 2023:
		return element_id.Value
	else:
		return element_id.IntegerValue

def build_element_id(id_value):
	# type: (int) -> ElementId
	"""Get ElementId object from a value."""
	if rvt_year > 2023:
		return ElementId(System.Int64(id_value))
	else:
		return ElementId(id_value)
	
# ===============
# ---> CLASSES <---
class ItemsCollectionBase(object):
	"""
	Abstract base for gathering renamable Revit elements of any workflow.
	Subclasses implement `_gather_all_items()`, returning - 
		{ element_id: (group_lvl1, group_lvl2, item_name, classification, params_collection) }
	"""
	__metaclass__ = ABCMeta

	def __init__(self):
		super(ItemsCollectionBase, self).__init__()
		self._illegal_pattern = re.compile(r'[\\:{}\[\]|;<>?`~\x00-\x1F\x7F]')
		self._dict_items = self._gather_all_items()

	def get_dict_items(self):
		# type: () -> dict[int, tuple]
		"""Common method to get all dictionary items, from implementing `_gather_all_items` method."""
		return self._dict_items

	@abstractmethod
	def _gather_all_items(self):
		# type: () -> dict[int, tuple]
		"""Abstract method for gathering all items."""
		pass

	def _sanitize(self, value):
		# type: (object) -> str
		"""Remove Revit illegal characters, sanitizing them."""
		return self._illegal_pattern.sub('', str(value))

	def _read_parameter_value(self, param):
		# type: (Parameter) -> object
		from Autodesk.Revit.DB import StorageType
		if param and param.HasValue:
			param_stor_type = param.StorageType
			if param_stor_type == StorageType.String:
				val = param.AsString()
				return val if val else None
			elif param_stor_type == StorageType.Double:
				val = param.AsValueString()
				
				if not val:
					return None
				val = str(val)
				# Feet-inches length format (e.g. "2' 10"", "7' 0"") - don't truncate on the space.
				if val[-1] in ("'", '"'):
					return val
				
				tokens = val.split(" ")
				# e.g. "15 mm" -> "15", "70 A" -> "70"
				if len(tokens) > 1 and tokens[-1].isalpha():
					return " ".join(tokens[:-1])
				return val
			elif param_stor_type == StorageType.Integer:
				val = param.AsInteger()
				val_string = param.AsValueString()
				return val_string if val_string else val
			elif param_stor_type == StorageType.ElementId:
				val_string = param.AsValueString()
				return val_string if val_string != "-1" else None
			else:
				return None
 
	def _get_all_type_parameters(self, element):
		# type: (Element) -> dict[str, str]
		dict_parameters = {}
		for pr in element.Parameters:
			if pr.HasValue:
				param_name = pr.Definition.Name
				param_value = self._read_parameter_value(pr)
				if param_value and 'none' not in str(param_value).lower():
					dict_parameters[param_name] = self._sanitize(param_value)
		return dict_parameters