# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import re
from Models.mo_tokenizing_control import Token_TextManipulation_Control

# ===============
# ---> CLASSES <---
class ListPopulate(object):
	"""
	Every template will have different list population, but this class stays workflow-agnostic.
	Only depends on the leaf node contract: `.Header`, `.ParentGroupName`.
	"""
	def __init__(self, vm_treeviewer, richtextbox_string):
		self._vm_treeviewer = vm_treeviewer			# type: TreeViewerVM_Extender
		self._richtextbox_string = richtextbox_string		# type: str
		self._illegal_pattern = re.compile(r'[\\:{}\[\]|;<>?`~\x00-\x1F\x7F]')		# Regex set of illegal characters in Revit.
		self._text_manip_class = Token_TextManipulation_Control()
		# (family_name, old_name, new_name, has_error, error_message, element_id, substitute_dict)

	def collect_items(self):
		"""List of items for further use as value."""
		checked_items = self._vm_treeviewer.CheckedItems
		list_collected_items = []
		_list_new_type_names = []

		for item in (checked_items):			# We'll put serial number when adding in ObservableCollection
			old_name = item.Header
			group_name = item.ParentGroupName	# Family name, for grouping types
			element_id = item.ElementIDType		# Element ID, for managing treeview visibility
			substitute_dict = item.ParameterObjectsList		# moved up - needed for every branch now, incl. Pass 1

			# Pass 1 --> Check if naming template has same name as old type name
			if old_name == self._richtextbox_string:
				tuple_01 = (group_name, old_name, self._richtextbox_string, False, None, element_id, substitute_dict)
				list_collected_items.append(tuple_01)
				continue		# Do not kill the loop, just continue

			# Pass 2 --> Substitute tokens with actual parameter values first
			# substitute_dict = item.ParameterObjectsList
			new_name = self._text_manip_class.substitute_tokens(self._richtextbox_string, substitute_dict)

			# Pass 3 --> Now check the *substituted* name for illegal Revit characters
			if self._check_sanitized_string(new_name):
				tuple_02 = (group_name, old_name, new_name, True, "Illegal Revit characters found.", element_id, substitute_dict)
				list_collected_items.append(tuple_02)
				continue

			# Pass 4 --> Check if new name generated exists in list of new type name list
			if new_name in _list_new_type_names:
				tuple_03 = (group_name, old_name, new_name, True, "Type name already exists.", element_id, substitute_dict)
				list_collected_items.append(tuple_03)
			else:
				_list_new_type_names.append(new_name)
				tuple_04 = (group_name, old_name, new_name, False, None, element_id, substitute_dict)
				list_collected_items.append(tuple_04)
		return list_collected_items

	def substitute_and_validate(self, richtextbox_string, old_name, parameter_dict, seen_names):
		# type: (str, str, dict, set) -> tuple[str, bool, str|None]
		"""
		Reusable by GroupData_Renamer.update_template() to re-evaluate a single already-collected
		row against a *different* template string, without re-touching the tree.
		"""
		if old_name == richtextbox_string:
			return richtextbox_string, False, None
		new_name = self._text_manip_class.substitute_tokens(richtextbox_string, parameter_dict)
		if self._check_sanitized_string(new_name):
			return new_name, True, "Illegal Revit characters found."
		if new_name in seen_names:
			return new_name, True, "Type name already exists."
		return new_name, False, None

	def _check_sanitized_string(self, text_to_check):
		# type: (str) -> bool
		"""Check the given string (post-substitution) for illegal Revit characters."""
		return bool(re.search(self._illegal_pattern, text_to_check))