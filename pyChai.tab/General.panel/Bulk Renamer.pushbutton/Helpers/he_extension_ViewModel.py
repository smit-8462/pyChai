# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, traceback, clr
from abc import ABCMeta, abstractmethod		# Used for creating abstract method.

clr.AddReference("System")
from System.Collections.ObjectModel import ObservableCollection

from lib_WPF.Helpers.he_ViewModel_ViewModelBase import ViewModelBase
from lib_WPF.Helpers.he_RelayCommand import RelayCommand

from Helpers.he_extension_Model import ListPopulate
from Models.mo_tokenizing_control import extract_richtextbox_contents

# ===============
# ---> Helper Classes <---
# region TreeViewer
class TreeBuilderBase_Extender(object):
	"""Builds the node tree from any ItemsCollectionBase."""
	__metaclass__ = ABCMeta
	def __init__(self, items_collection):
		# type: (ItemsCollectionBase) -> None
		self._items_collection = items_collection

	@abstractmethod
	def _building_blocks(self, dictionary_type):
		# type: (dict) -> object
		"""Helper method for making dictionary into WPF TreeView list.

		:param dictionary_type: Either builtin or family dictionary.
		:type dictionary_type: dict
		"""
		pass

	# Common Helper Methods
	# -------------------
	def _sort_tree(self, node):
		# type: (RVT_TreeNodeBase) -> None
		"""Recursively sort a node's children alphabetically by Header."""
		if node is None:
			return
		if node.Children.Count == 0:
			return		# leaf node, nothing to sort
		sorted_children = sorted(node.Children, key=lambda c: c.Header.lower())		# Here, Header is a string
		node.Children.Clear()
		for child in sorted_children:
			node.Children.Add(child)
		for child in sorted_children:
			self._sort_tree(child)

class TreeViewerVM_Extender(ViewModelBase):
	"""
	The class is used as an extender for other class, related to TreeViewer_VM.
	It will be inherited to other class.
	In some places, "parent" and "group" are same, therefore interchangable. Need to make all words into "group" in future.
	"""
	__metaclass__ = ABCMeta

	def __init__(self):
		super(TreeViewerVM_Extender,self).__init__()
		self._command_selection_type = RelayCommand(lambda sender: self.selection_type_changed(sender))		# Typology selection changing
		# persistent collection, bind once
		self._root_items = ObservableCollection[object]()   # type: list
		self._processed_element_ids = set()	# persists across refresh_tree rebuilds (Built-In/Loaded/Both switches)

	# Common Property
	# -------------------
	@property
	def Command_SelectionType(self):
		"""
		If there are multiple option to be made, then this property will be used to
		bind the method for change in option, using `RelayCommand`.
		For example, if user choose "Family Type" option in ComboBox, it will be used 
		for changing selcetion, from Loaded to Built-In.
		"""
		return self._command_selection_type

	@property
	def RootItems(self):
		return self._root_items

	@property
	def CheckedItems(self):
		# type: () -> list[RVT_TreeNodeBase]
		"""Flat, non-persistent list of checked leaf nodes. Built fresh from the tree on every access."""
		results = []
		for root in self._root_items:
			self._collect_checked_items(root, results)
		return results

	# Abstract Methods
	# -------------------
	@abstractmethod
	def selection_type_changed(self, sender):
		"""
		It is an abstract method which will be implemented in inherited class, since the selection process might vary.
		The method is a process based on selected option. 
		Here, `sender` is the UI control which sent/executed this command (like RadioButton, Button, etc)."""
		pass

	# Common Methods
	# -------------------
	def tree_selection_invert(self):
		for root in self._root_items:
			self._invert_node(root)

	def tree_selection_all(self):
		for root in self._root_items:
			root.ItemIsChecked = True

	def tree_selection_clear(self):
		for root in self._root_items:
			root.ItemIsChecked = False

	def tree_search_expand_all_items(self):
		for root in self._root_items:
			self._set_expanded_recursive(root, True)

	def tree_search_collapse_all_items(self):
		for root in self._root_items:
			self._set_expanded_recursive(root, False)

	def tree_collapse_checked_items(self, element_ids):
		# type: (set) -> None
		"""Hide and uncheck every leaf node whose ElementIDType is in `element_ids`, so they
		disappear from view and are excluded from CheckedItems on any future template run.
		Also hides any branch whose children have all become hidden as a result."""
		if not element_ids:
			return
		self._processed_element_ids.update(element_ids)
		for root in self._root_items:
			self._hide_node_by_id(root, self._processed_element_ids)

	def _hide_node_by_id(self, node, element_ids):
		# type: (RVT_TreeNodeBase, set) -> bool
		"""Returns True if this node is still visible after the pass.
		Leaf: hides + unchecks itself if matched. Branch: visible only if at least one child remains visible."""
		if node.Children.Count == 0:
			if node.ElementIDType in element_ids:
				node.IsNodeVisible = False
				node.ItemIsChecked = False		# cascades up, so parent tri-state updates too
			return node.IsNodeVisible

		any_child_visible = False
		for child in node.Children:
			if self._hide_node_by_id(child, element_ids):
				any_child_visible = True
		node.IsNodeVisible = any_child_visible
		return any_child_visible
		
	def tree_search_filter_changed(self, search_text):
		text = (search_text or "").strip().lower()
		if not text:
			self.tree_search_clear_input()
			return
		for root in self._root_items:
			self._filter_node(root, text)

	def tree_search_clear_input(self):
		for root in self._root_items:
			self._reset_node_visibility(root)

	def tree_restore_hidden_items(self):
		"""Undo tree_collapse_checked_items(): reveal every previously-hidden node again, and forget which ones were processed."""
		self._processed_element_ids.clear()
		for root in self._root_items:
			self._reset_node_visibility(root)

	# Common Helper Methods
	# -------------------
	def refresh_tree(self, items):
		"""It is kept public, since it will be used after interitance."""
		self._root_items.Clear()
		if items is None:
			return
		if isinstance(items, list):
			for it in items:
				self._root_items.Add(it)
		else:
			self._root_items.Add(items)

		# Re-apply hide/uncheck for anything already processed in a previous template run,
		# since these are freshly-built node objects with no memory of prior state.
		if self._processed_element_ids:
			for root in self._root_items:
				self._hide_node_by_id(root, self._processed_element_ids)

	def _invert_node(self, node):
		# type: (RVT_TreeNodeBase) -> None
		"""Recursively invert only leaf nodes; parent states update themselves via the cascade logic."""
		if not node.IsNodeVisible:
			return		# skip already-processed/hidden nodes
		if node.Children.Count == 0:
			# Leaf node (RVT_TypeName) - toggle it. This setter cascades upward (update_parent=True) so ancestor tri-state checks recalculate automatically.
			node.ItemIsChecked = not node.ItemIsChecked
		else:
			for child in node.Children:
				self._invert_node(child)

	def _set_expanded_recursive(self, node, value):
		# type: (RVT_TreeNodeBase, bool) -> None
		if node.Children.Count == 0:
			return		# leaf nodes have nothing to expand
		node.IsNodeExpanded = value
		for child in node.Children:
			self._set_expanded_recursive(child, value)

	def _filter_node(self, node, text):
		# type: (RVT_TreeNodeBase, str) -> bool
		"""Returns True if this node or any descendant matches; sets IsNodeVisible/IsNodeExpanded accordingly."""
		self_match = text in node.Header.lower()
		child_match = False
		for child in node.Children:
			if self._filter_node(child, text):
				child_match = True

		is_match = self_match or child_match
		node.IsNodeVisible = is_match
		if child_match:
			node.IsNodeExpanded = True		# reveal matches nested under this node
		return is_match

	def _reset_node_visibility(self, node):
		node.IsNodeVisible = True
		for child in node.Children:
			self._reset_node_visibility(child)

	def _hide_node_by_id(self, node, element_ids):
		# type: (RVT_TreeNodeBase, set) -> bool
		"""Returns True if this node is still visible after the pass.
		Leaf: unchecks + hides itself if matched (uncheck first, while still 'visible', so
		the checkbox-lock in _set_is_checked doesn't block it). Branch: visible only if at
		least one child remains visible."""
		if node.Children.Count == 0:
			if node.ElementIDType in element_ids:
				node.ItemIsChecked = False		# must happen before hiding - see docstring
				node.IsNodeVisible = False
			return node.IsNodeVisible

		any_child_visible = False
		for child in node.Children:
			if self._hide_node_by_id(child, element_ids):
				any_child_visible = True
		node.IsNodeVisible = any_child_visible
		return any_child_visible
	
	def _collect_checked_items(self, node, results):
		# type: (RVT_TreeNodeBase, list) -> None
		"""Recursively collect leaf nodes (no children) that are checked."""
		if node.Children.Count == 0:
			if node.ItemIsChecked == True:
				results.append(node)
			return
		for child in node.Children:
			self._collect_checked_items(child, results)


class RVT_TreeNodeBase(ViewModelBase):
	"""
	Base class for all TreeView node levels - shared shape means one XAML template can render every level with no per-type matching required.
	Source - https://www.thebestcsharpprogrammerintheworld.com/2020/05/26/treeview-with-checkbox-in-wpf/
	"""
	def __init__(self, header, parent=None):
		super(RVT_TreeNodeBase, self).__init__()
		self._header = header
		self._children = ObservableCollection[object]()		# type: list
		self._item_is_checked = False		# True / False / None (indeterminate)
		self._parent = parent
		self._is_node_expanded = False
		self._is_node_visible = True

	@property
	def Header(self):
		"""Here, header is the Header property of TreeViewItem."""
		return self._header

	@property
	def Children(self):
		return self._children

	@property
	def ItemIsChecked(self):
		return self._item_is_checked

	@ItemIsChecked.setter
	def ItemIsChecked(self, value):
		# Borrowing OnPropertyChanged from _set_is_checked method.
		self._set_is_checked(value, True, True)

	@property
	def IsNodeExpanded(self):
		return self._is_node_expanded

	@IsNodeExpanded.setter
	def IsNodeExpanded(self, value):
		if value == self._is_node_expanded:
			return
		self._is_node_expanded = value
		self.OnPropertyChanged("IsNodeExpanded")

	@property
	def IsNodeVisible(self):
		return self._is_node_visible

	@IsNodeVisible.setter
	def IsNodeVisible(self, value):
		if value == self._is_node_visible:
			return
		self._is_node_visible = value
		self.OnPropertyChanged("IsNodeVisible")
	
	# Methods
	# -------------------
	# Internal checkbox cascade logic
	def _set_is_checked(self, value, update_children, update_parent):
		if not self._is_node_visible:
			return		# hidden (already processed) nodes are locked out of selection
		if value == self._item_is_checked: return
		self._item_is_checked = value

		if update_children and self._item_is_checked is not None:
			for child in self._children:
				if child.IsNodeVisible:		# skip already-processed/hidden children
					child._set_is_checked(self._item_is_checked, True, False)
		if update_parent and self._parent is not None:
			self._parent._verify_checked_state()
		self.OnPropertyChanged("ItemIsChecked")

	def _verify_checked_state(self):
		visible_children = [c for c in self._children if c.IsNodeVisible]
		if not visible_children:
			return		# nothing left to consider; this node should already be hidden itself
		state = None
		for i, child in enumerate(visible_children):
			current = child.ItemIsChecked
			if i == 0:
				state = current
			elif state != current:
				state = None
				break
		self._set_is_checked(state, False, True)
# endregion


# region Renamer List
class RenameRowViewModel(ViewModelBase):
	"""Row ViewModel for a collection of DataGrid items for a particular template."""
	def __init__(self):
		super(RenameRowViewModel, self).__init__()
		self._serial_number = 0
		self._has_error = False
		self._error_message = ""
		self._old_name = None
		self._new_name = None
		self._naming_template = None
		self._group_name = None
		self._elementid = None
		self._parameter_snapshot = {}		# item.ParameterObjectsList at collection time - needed to re-evaluate NewName later

	# Property
	# -------------------
	@property
	def ElementID(self):
		return self._elementid

	@ElementID.setter
	def ElementID(self, value):
		self._elementid = value
		self.OnPropertyChanged("ElementID")
		
	@property
	def SerialNumber(self):
		return self._serial_number

	@SerialNumber.setter
	def SerialNumber(self, value):
		self._serial_number = value
		self.OnPropertyChanged("SerialNumber")
	
	@property
	def HasError(self):
		return self._has_error

	@HasError.setter
	def HasError(self, value):
		self._has_error = value
		self.OnPropertyChanged("HasError")
	
	@property
	def ErrorMessage(self):
		return self._error_message

	@ErrorMessage.setter
	def ErrorMessage(self, value):
		self._error_message = value
		self.OnPropertyChanged("ErrorMessage")
	
	@property
	def OldName(self):
		return self._old_name

	@OldName.setter
	def OldName(self, value):
		self._old_name = value
		self.OnPropertyChanged("OldName")
	
	@property
	def NewName(self):
		return self._new_name

	@NewName.setter
	def NewName(self, value):
		self._new_name = value
		self.OnPropertyChanged("NewName")
	
	@property
	def NamingTemplate(self):
		return self._naming_template

	@NamingTemplate.setter
	def NamingTemplate(self, value):
		self._naming_template = value
		self.OnPropertyChanged("NamingTemplate")

	@property
	def GroupName(self):
		return self._group_name

	@GroupName.setter
	def GroupName(self, value):
		self._group_name = value
		self.OnPropertyChanged("GroupName")

	@property
	def ParameterSnapshot(self):
		return self._parameter_snapshot

	@ParameterSnapshot.setter
	def ParameterSnapshot(self, value):
		self._parameter_snapshot = value


class GroupData_Renamer(ViewModelBase):
	"""Collect all row items for DataGrid under 1 roof, in an expander"""
	def __init__(self, vm_tree_viewer, richtextbox_string):
		super(GroupData_Renamer, self).__init__()
		self._vm_tree_viewer = vm_tree_viewer
		self._richtextbox_string = richtextbox_string
		self._datagrid_collection = ObservableCollection[RenameRowViewModel]()		# type: list[RenameRowViewModel]
		self._list_populate = ListPopulate(self._vm_tree_viewer, self._richtextbox_string)
		self._count_total = 0
		self._count_error = 0
		self._error_list = []

	# Property
	# -------------------
	@property
	def TemplateName(self):
		return self._richtextbox_string

	@property
	def DataGridCollection(self):
		return self._datagrid_collection

	@DataGridCollection.setter
	def DataGridCollection(self, value):
		self._datagrid_collection = value
		self.OnPropertyChanged("DataGridCollection")

	@property
	def CountTotal(self):
		return self._count_total

	@CountTotal.setter
	def CountTotal(self, value):
		self._count_total = value
		self.OnPropertyChanged("CountTotal")

	@property
	def CountError(self):
		return self._count_error

	@CountError.setter
	def CountError(self, value):
		self._count_error = value
		self.OnPropertyChanged("CountError")

	@property
	def TemplateErrorList(self):
		return self._error_list

	@TemplateErrorList.setter
	def TemplateErrorList(self, value):
		self._error_list = value
		self.OnPropertyChanged("TemplateErrorList")

	# Methods
	# -------------------
	def get_item_collection(self):
		"""Populate DataGridCollection with RenameRowViewModel rows, appending newly-checked
		items on top of whatever this template already has (previously-processed items are
		hidden/unchecked, so CheckedItems only ever returns the new batch - no duplicates)."""		
		list01 = self._list_populate.collect_items()
		count_error = 0
		rename_list = []	# list will have tuple (old name, new name)
		checked_elements = set()	# element_ids of every row processed this pass

		# `clear()` for clearing python list was introduced in Python 3, therefore we'll need to use slicing for clearing the list.
		self._error_list[:] = []	# Clear existing list - it gets fully repopulated below to match this pass
		starting_serial = self._datagrid_collection.Count		# continue numbering, don't restart at 1
		for idx, (group_name, old_name, new_name, has_error, error_message, element_id, param_dict) in enumerate(list01):
			row = RenameRowViewModel()		# New instance of row data
			row.SerialNumber = starting_serial + idx + 1
			row.GroupName = group_name
			row.OldName = old_name
			row.NewName = new_name
			row.HasError = has_error
			row.ErrorMessage = error_message
			row.NamingTemplate = self._richtextbox_string
			row.ParameterSnapshot = param_dict
			row.ElementID = element_id
			self._datagrid_collection.Add(row)
			if has_error:
				self._error_list.append((old_name, error_message))
				count_error += 1
			rename_list.append((old_name, new_name, element_id))
			checked_elements.add(element_id)
		self.CountTotal = self._datagrid_collection.Count		# reflect the full accumulated grid, not just this pass
		self.CountError = self.CountError + count_error		# accumulate, since previous rows' errors are still in the grid
		return rename_list, checked_elements

	def update_template(self, new_richtextbox_string):
		"""
		Re-evaluate every row already in DataGridCollection against a new template string.
		Does NOT touch the tree - by the time a row can be "held" for editing, its tree items
		are already hidden/unchecked, so this reuses each row's cached ParameterSnapshot instead.
		"""
		if not new_richtextbox_string:
			return False

		count_error = 0
		self._error_list[:] = []
		seen_new_names = set()
		for row in self._datagrid_collection:
			new_name, has_error, error_message = self._list_populate.substitute_and_validate(
				new_richtextbox_string, row.OldName, row.ParameterSnapshot, seen_new_names
			)
			if not has_error:
				seen_new_names.add(new_name)
			row.NewName = new_name
			row.HasError = has_error
			row.ErrorMessage = error_message
			row.NamingTemplate = new_richtextbox_string
			if has_error:
				self._error_list.append((row.OldName, error_message))
				count_error += 1

		self._richtextbox_string = new_richtextbox_string		# TemplateName now reflects the edited text
		self.CountError = count_error		# full recount - every row was just re-validated, not accumulated
		self.OnPropertyChanged("TemplateName")
		return True
	

class RenamerListVM_Extender(ViewModelBase):
	"""Class related to Renamer."""
	def __init__(self, vm_tree_viewer, vm_information):
		super(RenamerListVM_Extender,self).__init__()
		self._vm_tree_viewer = vm_tree_viewer
		self._vm_information = vm_information
		self._error_list = []
		# Bind ListView's ItemsControl to the below
		self._grouped_templates = ObservableCollection[object]()   # type: list[GroupData_Renamer]
		self._template_lookup = {}   # richtextbox_text -> GroupData_Renamer, just for de-dupe/refresh

	# Property
	# -------------------
	@property
	def ErrorExist(self):
		return True if len(self._error_list) > 0 else False

	@property
	def ErrorList(self):
		return self._error_list

	@property
	def GroupedTemplates(self):
		return self._grouped_templates

	# Methods
	# -------------------
	def populate_data_in_groups(self, richtextbox_object):
		"""Method of invoking populating the groups when clicked apply."""
		richtextbox_text = extract_richtextbox_contents(richtextbox_object)
		if not richtextbox_text: return
		existing = self._template_lookup.get(richtextbox_text)
		if existing is None:
			gdr = GroupData_Renamer(self._vm_tree_viewer, richtextbox_text)
			gdr.get_item_collection()
			self._template_lookup[richtextbox_text] = gdr
			self._grouped_templates.Add(gdr)
		else:
			existing.get_item_collection()   # re-run against current tree selection

	def reset_groups(self):
		"""Call when the active workflow changes, so stale groups don't linger."""
		self._grouped_templates.Clear()
		self._template_lookup.clear()
		self._error_list = []
# endregion