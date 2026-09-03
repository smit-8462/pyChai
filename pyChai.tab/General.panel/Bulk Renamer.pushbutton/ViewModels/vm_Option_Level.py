# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, traceback, clr

clr.AddReference("System")
from Helpers.he_extension_ViewModel import RVT_TreeNodeBase, TreeBuilderBase_Extender

from Models.mo_option_level import LevelsCollection

# ===============
# ---> CLASSES <---
class TreeCollection_Levels(TreeBuilderBase_Extender):
	"""Building tree for Levels."""
	def __init__(self):
		self._levels_collection = LevelsCollection()
		# `TreeBuilderBase_Extender` class has requirement of `items_collection`, therfore we have provided `self._levels_collection` collection.
		super(TreeCollection_Levels, self).__init__(self._levels_collection)
		
	# Property
	# -------------------
	@property
	def PopulateActiveLevel(self):
		return self._building_tree_active()
	
	@property
	def PopulateStrayLevel(self):
		return self._building_tree_stray()
	
	@property
	def PopulateBoth(self):
		return self._building_tree_both()
	
	# Methods
	# -------------------
	def _building_tree_active(self):
		dict_levels = self._levels_collection.get_levels_active()
		typology = self._building_blocks(dict_levels)
		self._sort_tree(typology)
		return typology

	def _building_tree_stray(self):
		dict_levels = self._levels_collection.get_levels_stray()
		typology = self._building_blocks(dict_levels)
		self._sort_tree(typology)
		return typology

	def _building_tree_both(self):
		dict_active, dict_stray = self._levels_collection.get_both_levels()
		lvl_active = self._building_blocks(dict_active)
		lvl_stray = self._building_blocks(dict_stray)
		self._sort_tree(lvl_active)
		self._sort_tree(lvl_stray)
		return [t for t in (lvl_active, lvl_stray) if t is not None]

	def _building_blocks(self, dictionary_type):
		# type: (dict) -> object
		"""Helper method for making dictionary into WPF TreeView list.
	
		:param dictionary_type: Levels dictionary.
		:type dictionary_type: dict
		"""
		typology = None		# Type typology, example active or stray.

		for dict_key, dict_value in dictionary_type.items():
			lvl_instance_name = dict_value[0]
			lvl_instance_classification = dict_value[1]
			lvl_parameters = dict_value[2]
			elemtype_id = dict_key

			if typology is None:
				typology = RVT_TypologyName(lvl_instance_classification)

			# Instance node
			rvt_instance_node = RVT_InstanceName(lvl_instance_name, parent=typology)
			rvt_instance_node.ParameterObjectsList = lvl_parameters
			rvt_instance_node.ElementIDType = elemtype_id
			typology.Children.Add(rvt_instance_node)
		return typology


# --------------------------
# Supporting classes, hierarchial order
# RVT_TypologyName --> RVT_InstanceName
# Typology --> Level Instance
class RVT_TypologyName(RVT_TreeNodeBase):
	"""Typology, such as Active Plan or Stray Plan."""
	pass

class RVT_InstanceName(RVT_TreeNodeBase):
	"""Instance name — leaf node, Children stays empty."""
	# pass
	def __init__(self, header, parent=None):
		super(RVT_InstanceName, self).__init__(header, parent)
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