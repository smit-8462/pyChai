# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, traceback, clr

clr.AddReference("System")
from Helpers.he_extension_ViewModel import RVT_TreeNodeBase, TreeBuilderBase_Extender

from Models.mo_option_views import ViewsCollection

# ===============
# ---> CLASSES <---
class TreeCollection_Views(TreeBuilderBase_Extender):
	"""Building tree for Views."""
	def __init__(self):
		self._views_collection = ViewsCollection()
		# `TreeBuilderBase_Extender` class has requirement of `items_collection`, therfore we have provided `self._views_collection` collection.
		super(TreeCollection_Views, self).__init__(self._views_collection)
		
	# Property
	# -------------------
	@property
	def PopulateViewOnSheet(self):
		return self._building_tree_onsheet()
	
	@property
	def PopulateViewOffSheet(self):
		return self._building_tree_offsheet()
	
	@property
	def PopulateBoth(self):
		return self._building_tree_both()
	
	# Methods
	# -------------------
	def _building_tree_onsheet(self):
		dict_views = self._views_collection.get_views_onsheet()
		typology = self._building_blocks(dict_views)
		self._sort_tree(typology)
		return typology

	def _building_tree_offsheet(self):
		dict_views = self._views_collection.get_views_offsheet()
		typology = self._building_blocks(dict_views)
		self._sort_tree(typology)
		return typology

	def _building_tree_both(self):
		dict_onsheet, dict_offsheet = self._views_collection.get_both_views()
		view_onsheet = self._building_blocks(dict_onsheet)
		view_offsheet = self._building_blocks(dict_offsheet)
		self._sort_tree(view_onsheet)
		self._sort_tree(view_offsheet)
		return [t for t in (view_onsheet, view_offsheet) if t is not None]

	def _building_blocks(self, dictionary_type):
		# type: (dict) -> object
		"""Helper method for making dictionary into WPF TreeView list.
	
		:param dictionary_type: Views dictionary.
		:type dictionary_type: dict
		"""
		typology = None		# Type typology, example on sheet or off sheet.

		for dict_key, dict_value in dictionary_type.items():
			# (view_name, vw_type_name, viewtype_type, view_classification, params_collection)
			view_name = dict_value[0]
			vw_type_name = dict_value[1]
			viewtype_type = dict_value[2]
			view_classification = dict_value[3]
			view_parameters = dict_value[4]
			elemtype_id = dict_key

			if typology is None:
				typology = RVT_TypologyName(view_classification)

			# Find or create the ViewType Type node
			viewtype_node = None
			for vwtyp in typology.Children:
				if vwtyp.Header == viewtype_type:
					viewtype_node = vwtyp
					break
			if viewtype_node is None:
				viewtype_node = RVT_ViewType_Type(viewtype_type, parent=typology)
				typology.Children.Add(viewtype_node)

			# Find or create the Family Type node
			familytype_node = None
			for tp in viewtype_node.Children:
				if tp.Header == vw_type_name:
					familytype_node = tp
					break
			if familytype_node is None:
				familytype_node = RVT_TypeName(vw_type_name, parent=viewtype_node)
				viewtype_node.Children.Add(familytype_node)

			# View instance node
			rvt_view_node = RVT_InstanceName(view_name, parent=familytype_node)
			rvt_view_node.ParameterObjectsList = view_parameters
			rvt_view_node.ElementIDType = elemtype_id
			familytype_node.Children.Add(rvt_view_node)
		return typology


# --------------------------
# Supporting classes, hierarchial order
# RVT_TypologyName --> RVT_ViewType_Type --> RVT_TypeName --> RVT_InstanceName
# Typology --> ViewType Type --> View Family Type --> View Name
class RVT_TypologyName(RVT_TreeNodeBase):
	"""Typology, such as Built-In or Loaded Family."""
	pass

class RVT_ViewType_Type(RVT_TreeNodeBase):
	"""Typology, such as Built-In or Loaded Family."""
	pass

class RVT_TypeName(RVT_TreeNodeBase):
	"""Typology, such as Built-In or Loaded Family."""
	pass

class RVT_InstanceName(RVT_TreeNodeBase):
	"""Type name — leaf node, Children stays empty."""
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