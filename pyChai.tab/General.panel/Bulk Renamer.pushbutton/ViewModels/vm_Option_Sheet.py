# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, traceback, clr

clr.AddReference("System")
from Helpers.he_extension_ViewModel import RVT_TreeNodeBase, TreeBuilderBase_Extender

from Models.mo_option_sheet import SheetsCollection

# ===============
# ---> CLASSES <---
class TreeCollection_Sheets(TreeBuilderBase_Extender):
	"""Building tree for sheets."""
	def __init__(self):
		self._sheets_collection = SheetsCollection()
		# `TreeBuilderBase_Extender` class has requirement of `items_collection`, therfore we have provided `self._sheets_collection` collection.
		super(TreeCollection_Sheets, self).__init__(self._sheets_collection)
		
	# Property
	# -------------------
	@property
	def PopulateEmptySheet(self):
		return self._building_tree_empty()
	
	@property
	def PopulateFilledSheet(self):
		return self._building_tree_filled()
	
	@property
	def PopulateBoth(self):
		return self._building_tree_both()
	
	# Methods
	# -------------------
	def _building_tree_empty(self):
		dict_sheets = self._sheets_collection.get_sheets_empty()
		typology = self._building_blocks(dict_sheets)
		self._sort_tree(typology)
		return typology
	
	def _building_tree_filled(self):
		dict_sheets = self._sheets_collection.get_sheets_filled()
		typology = self._building_blocks(dict_sheets)
		self._sort_tree(typology)
		return typology
	
	def _building_tree_both(self):
		dict_empty, dict_filled = self._sheets_collection.get_both_sheets()
		sheet_empty = self._building_blocks(dict_empty)
		sheet_filled = self._building_blocks(dict_filled)
		self._sort_tree(sheet_empty)
		self._sort_tree(sheet_filled)
		return [t for t in (sheet_empty, sheet_filled) if t is not None]

	def _building_blocks(self, dictionary_type):
		# type: (dict) -> object
		"""Helper method for making dictionary into WPF TreeView list.
	
		:param dictionary_type: Sheets dictionary.
		:type dictionary_type: dict
		"""
		typology = None		# Type typology, example builtin or family.
		
		for dict_key, dict_value in dictionary_type.items():
			sheet_instance_name = dict_value[0]
			sheet_instance_classification = dict_value[1]
			sheet_parameters = dict_value[2]
			elemtype_id = dict_key

			if typology is None:
				typology = RVT_TypologyName(sheet_instance_classification)

			# Instance node
			rvt_instance_node = RVT_InstanceName(sheet_instance_name, parent=typology)
			rvt_instance_node.ParameterObjectsList = sheet_parameters
			rvt_instance_node.ElementIDType = elemtype_id
			typology.Children.Add(rvt_instance_node)
		return typology


# --------------------------
# Supporting classes, hierarchial order
# RVT_TypologyName --> RVT_InstanceName
# Typology --> Sheet Instance
class RVT_TypologyName(RVT_TreeNodeBase):
	"""Typology, such as Empty or Filled sheets."""
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