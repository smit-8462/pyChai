# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, traceback, clr

clr.AddReference("System")
from Models.mo_option_family_type import TypesCollection

from Helpers.he_extension_ViewModel import RVT_TreeNodeBase, TreeBuilderBase_Extender

# ===============
# ---> CLASSES <---
class TreeCollection_FamilyType(TreeBuilderBase_Extender):
	"""Building tree for Family Types."""
	def __init__(self):
		self._types_collection = TypesCollection()
		# `TreeBuilderBase_Extender` class has requirement of `items_collection`, therfore we have provided `self._types_collection` collection.
		super(TreeCollection_FamilyType, self).__init__(self._types_collection)

	# Property - Family Type
	# -------------------
	@property
	def PopulateBuiltin(self):
		return self._building_tree_builtin()
	
	@property
	def PopulateLoaded(self):
		return self._building_tree_loaded()
	
	@property
	def PopulateBoth(self):
		return self._building_tree_both()

	# Methods
	# -------------------
	def _building_tree_builtin(self):
		dict_builtin = self._types_collection.get_builtin_types()
		typology = self._building_blocks(dict_builtin)
		self._sort_tree(typology)
		return typology

	def _building_tree_loaded(self):
		dict_loaded = self._types_collection.get_loaded_types()
		typology = self._building_blocks(dict_loaded)
		self._sort_tree(typology)
		return typology

	def _building_tree_both(self):
		dict_builtin, dict_loaded = self._types_collection.get_both_types()
		built = self._building_blocks(dict_builtin)
		loaded = self._building_blocks(dict_loaded)
		self._sort_tree(built)
		self._sort_tree(loaded)
		return [t for t in (built, loaded) if t is not None]

	def _building_blocks(self, dictionary_type):
		# type: (dict) -> object
		"""Helper method for making dictionary into WPF TreeView list.

		:param dictionary_type: Either builtin or family dictionary.
		:type dictionary_type: dict
		"""
		typology = None		# Type typology, example builtin or family.

		for dict_key, dict_value in dictionary_type.items():
			elemtype_cat = dict_value[0]
			elemtype_family = dict_value[1]
			elemtype_type = dict_value[2]
			elemtype_type_classification = dict_value[3]
			elemtype_parameters = dict_value[4]
			elemtype_id = dict_key

			if typology is None:
				typology = RVT_TypologyName(elemtype_type_classification)

			# Find or create the Category node
			category_node = None
			for cat in typology.Children:
				if cat.Header == elemtype_cat:
					category_node = cat
					break
			if category_node is None:
				category_node = RVT_CategoryName(elemtype_cat, parent=typology)
				typology.Children.Add(category_node)

			# Find or create the Family node
			family_node = None
			for fam in category_node.Children:
				if fam.Header == elemtype_family:
					family_node = fam
					break
			if family_node is None:
				family_node = RVT_FamilyName(elemtype_family, parent=category_node)
				category_node.Children.Add(family_node)

			# Type node
			rvt_type_node = RVT_TypeName(elemtype_type, parent=family_node)
			rvt_type_node.ParameterObjectsList = elemtype_parameters
			rvt_type_node.ElementIDType = elemtype_id
			family_node.Children.Add(rvt_type_node)
		return typology


# --------------------------
# Supporting classes, hierarchial order
# RVT_TypologyName --> RVT_CategoryName --> RVT_FamilyName --> RVT_TypeName
# Typology --> Category --> Family --> Type
class RVT_TypologyName(RVT_TreeNodeBase):
	"""Typology, such as Built-In or Loaded Family."""
	pass

class RVT_CategoryName(RVT_TreeNodeBase):
	"""Category name."""
	pass

class RVT_FamilyName(RVT_TreeNodeBase):
	"""Family name."""
	pass

class RVT_TypeName(RVT_TreeNodeBase):
	"""Type name — leaf node, Children stays empty."""
	# pass
	def __init__(self, header, parent=None):
		super(RVT_TypeName, self).__init__(header, parent)
		self._parameter_object_list = []
		self._parent_family_node = parent
		self._element_id = None

	# -----------------
	# Property
	@property
	def ElementIDType(self):
		return self._element_id

	@ElementIDType.setter
	def ElementIDType(self, value):
		self._element_id = value
		self.OnPropertyChanged("ElementIDType")

	@property
	def ParameterObjectsList(self):
		return self._parameter_object_list

	@ParameterObjectsList.setter
	def ParameterObjectsList(self, value):
		self._parameter_object_list = value
		self.OnPropertyChanged("ParameterObjectsList")

	@property
	def ParentGroupName(self):
		return self._parent_family_node.Header if self._parent_family_node is not None else None