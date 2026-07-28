# -*- coding: utf-8 -*-
import traceback

# ---> IMPORTS <---
from Autodesk.Revit.DB import BuiltInParameter, StorageType, Parameter, ElementId, Transaction

from pyrevit import forms

from lib_Snippets.snip_transaction import transac
# ===============

# ---> VARIABLES <---
uidoc = __revit__.ActiveUIDocument          #type: UIDocument
doc = __revit__.ActiveUIDocument.Document   #type: Document
app = __revit__.Application                 #type: UIApplication

# ===============

# ---> CLASSES <---
class ParamsBuiltIn(object):
	"""
	The element parameter class for getting and setting values.
	"""
	MAP_DICT = {
		'offset': BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM,
		'room_bounding': BuiltInParameter.WALL_ATTR_ROOM_BOUNDING,
		'is_structural': BuiltInParameter.FLOOR_PARAM_IS_STRUCTURAL,
		'image': BuiltInParameter.ALL_MODEL_IMAGE,
		'comments': BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS,
		'mark': BuiltInParameter.ALL_MODEL_MARK,
		'phase_created': BuiltInParameter.PHASE_CREATED,
		'phase_demolished': BuiltInParameter.PHASE_DEMOLISHED,
		'slope_angle': BuiltInParameter.ROOF_SLOPE,
		'base_constraint': BuiltInParameter.WALL_BASE_CONSTRAINT,
		'top_constraint': BuiltInParameter.WALL_HEIGHT_TYPE
	}

	def __init__(self, floor_elem):
		self.floor_elem = floor_elem

	@staticmethod
	def _param(floor, bip):
		return floor.get_Parameter(bip) or None

	@property
	def offset(self):
		return self._param(self.floor_elem, self.MAP_DICT['offset'])

	@property
	def room_bounding(self):
		return self._param(self.floor_elem, self.MAP_DICT['room_bounding'])

	@property
	def is_structural(self):
		return self._param(self.floor_elem, self.MAP_DICT['is_structural'])

	@property
	def image(self):
		return self._param(self.floor_elem, self.MAP_DICT['image'])

	@property
	def comments(self):
		return self._param(self.floor_elem, self.MAP_DICT['comments'])

	@property
	def mark(self):
		return self._param(self.floor_elem, self.MAP_DICT['mark'])

	@property
	def phase_created(self):
		return self._param(self.floor_elem, self.MAP_DICT['phase_created'])

	@property
	def phase_demolished(self):
		return self._param(self.floor_elem, self.MAP_DICT['phase_demolished'])

	@property
	def slope_angle(self):
		return self._param(self.floor_elem, self.MAP_DICT['slope_angle'])


class TransferParams(object):
	def __init__(self, element1, element2, ignore_list=None):
		"""
		Transfer parameters from one element to another using Parameter Map.
		The ignore list must have same name as displayed in the UI.

		Example => ignore_list = ['Height Offset from Level', 'Mark']
		:param element1: Source element
		:type element1: any
		:param element2: Target element
		:type element2: any
		:param ignore_list: List of parameters to ignore.
		:type ignore_list: list
		"""
		self.element1 = element1
		self.element2 = element2
		self.ignore_list = [item.lower() for item in ignore_list] if ignore_list is not None else []

		if type(self.element1) != type(self.element2):
			forms.alert("The two elements are not equal", exitscript=True)


	@staticmethod
	def _param_storage(parameter):
		# type: (Parameter) -> any
		if parameter and parameter.HasValue:
			if parameter.StorageType == StorageType.String:
				return parameter.AsString()
			elif parameter.StorageType == StorageType.Double:
				return parameter.AsDouble()
			elif parameter.StorageType == StorageType.Integer:
				return parameter.AsInteger()
			elif parameter.StorageType == StorageType.ElementId:
				return parameter.AsElementId()
		return None


	def get_all_params(self):
		"""
		Get all parameters.
		:return: Dictionary having primary element parameters.
		:rtype: dict
		"""
		param_dict = {}
		pr_map = self.element1.ParametersMap
		for pr in pr_map:		# type: Parameter
			if not pr.IsReadOnly:
				p_builtin = pr.Definition.BuiltInParameter
				p_name = pr.Definition.Name
				if p_name.lower() in self.ignore_list:
					continue
				key = p_builtin
				param_dict[key] = self._param_storage(pr)
		return param_dict


	def set_all_params(self, transaction_assign = None):
		"""
		Set all parameters.
		:param transaction_assign: Attach existing parameter, else it uses transaction of itself. Default value is None.
		:type transaction_assign: Transaction
		:return: No return.
		:rtype: None
		"""
		get_dict = self.get_all_params()

		def _execute():
			for key, value in get_dict.items():
				if value is None:
					continue	# It will skip the current iteration and move to next one

				param = self.element2.get_Parameter(key)
				if param is None or param.IsReadOnly:
					continue	# It will skip the current iteration and move to next one

				if type(value) == ElementId:
					param.Set(ElementId(value.Value))
				elif type(value) == str:
					param.Set(str(value))
				else:
					param.Set(value)

		if transaction_assign is None:
			with transac(doc, "Set all Parameters"):
				_execute()
		else:
			_execute()


# ===============

# ---> FUNCTIONS <---
def param_output(param):
	"""
	Return the value of a given parameter.
	:param param: Parameter object.
	:type param: Parameter
	:return: Based on the given parameter.
	:rtype: str | int | float | ElementId | None
	"""
	if param and param.HasValue:
		if param.StorageType == StorageType.String:
			val = param.AsString()
			return val if val else None   # treat empty string as None
		elif param.StorageType == StorageType.Integer:
			return param.AsInteger() if param.HasValue else None
		elif param.StorageType == StorageType.Double:
			return param.AsDouble() if param.HasValue else None
		elif param.StorageType == StorageType.ElementId:
			return param.AsElementId() if param.HasValue else None
	return None

