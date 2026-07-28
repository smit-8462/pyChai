# -*- coding: utf-8 -*-
import Autodesk
# ---> IMPORTS <---
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import Selection, ISelectionFilter, ObjectType
from Autodesk.Revit.Exceptions import OperationCanceledException

# ===============

# ---> VARIABLES <---
uidoc = __revit__.ActiveUIDocument                      # type:  UIDocument
doc = uidoc.Document               						# type:  Document
app = __revit__.Application                             # type:  UIApplication
selection = uidoc.Selection        						# type:  Selection

# ===============

# ---> CLASSES <---
class ISelection_Class(ISelectionFilter):
	"""
	Filter by Revit Element subclass 
	(e.g. Wall, Grid) using ISelectionFilter.
	
	## Example:
	
	    ISelection_Class(Wall)
	"""
	def __init__(self, type_name):
		# type: (Element) -> None
		self.type_name = type_name

	def AllowElement(self, elem):
		# type: (Element) -> bool
		if type(elem) == self.type_name:
			return True
		else:
			return False

	def AllowReference(self, ref, point):
		# type: (Reference, XYZ) -> bool
		return False


class ISelection_BuiltInCategory(ISelectionFilter):
	"""
	Filter by BuiltInCategory (example OST_Walls) using ISelectionFilter.

	## Example:

		ISelection_Category("BuiltInCategory.OST_Walls")
	"""
	def __init__(self, bic_category_name):
		"""
		:param bic_category_name: BuiltInCategory (example OST_Walls)
		:type bic_category_name: BuiltInCategory
		"""
		self.bic_category_name = bic_category_name

	def AllowElement(self, elem):
		# type: (Element) -> bool
		if elem.Category.Id == ElementId(self.bic_category_name) :
			return True
		else:
			return False

	def AllowReference(self, ref, point):
		# type: (Reference, XYZ) -> bool
		return False

# ===============

# ---> FUNCTIONS <---

def selectElement_rectangle(type_name):
	# type:  (type) -> list[Element]
	"""Select multiple elements by type class, by using rectangle box as selection."""
	# "__name__" is used because "type_name" is a class, not an instance element.
	if type_name:
		selected_object = selection.PickElementsByRectangle(ISelection_Class(type_name), "Select {}".format(type_name.__name__))     # type:  list[Element]
		return selected_object
	else:
		return None


def selectElement_single(type_name):
	# type:  (type) -> Element | None
	"""Select single element by type class."""
	# "__name__" is used because "type_name" is a class, not an instance element.
	if type_name:
		ref_object = selection.PickObject(ObjectType.Element, ISelection_Class(type_name), "Select {}".format(type_name.__name__))  # type:  Reference
		selected_object = doc.GetElement(ref_object)
		return selected_object
	else:
		return None


def selectElement_multiple(type_name):
	# type:  (type) -> list[Element]
	"""Select multiple elements by type class."""
	# "__name__" is used because "type_name" is a class, not an instance element.
	if type_name:
		ref_object = selection.PickObjects(ObjectType.Element, ISelection_Class(type_name), "Select {}".format(type_name.__name__))  # type:  list[Reference]
		selected_objects = [doc.GetElement(ref) for ref in ref_object]
		return selected_objects
	else:
		return None


def selectElement_single_builtincategory(builtincategory_name):
	# type:  (BuiltInCategory) -> Element | None
	"""Select single element by BuiltInCategory category name."""
	# "__name__" is used because "type_name" is a class, not an instance element.
	if builtincategory_name:
		ref_object = selection.PickObject(ObjectType.Element, ISelection_BuiltInCategory(builtincategory_name),
										  "Select {}".format(builtincategory_name))  # type:  Reference
		selected_object = doc.GetElement(ref_object)
		return selected_object
	else:
		return None


def selectElement_multiple_builtincategory(builtincategory_name):
	# type:  (BuiltInCategory) -> list[Element] | None
	"""Select multiple elements by BuiltInCategory category name."""
	if builtincategory_name:
		try:
			ref_object = selection.PickObjects(ObjectType.Element, ISelection_BuiltInCategory(builtincategory_name),
											   "Select {}".format(builtincategory_name))  # type:  list[Reference]
			selected_objects = [doc.GetElement(ref) for ref in ref_object]
			return selected_objects
		except OperationCanceledException:
			return None
	else:
		return None
