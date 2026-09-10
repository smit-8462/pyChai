# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, traceback, clr

clr.AddReference("System")
from System.Collections.ObjectModel import ObservableCollection

from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.DB import Transaction, Element

from lib_WPF.Helpers.he_ViewModel_ViewModelBase import ViewModelBase

from Models.mo_tokenizing_control import extract_richtextbox_contents, Token_TextManipulation_Control

from Helpers.he_extension_ViewModel import GroupData_Renamer
from Helpers.he_extension_Collector import build_element_id

# ===============
# ---> VARIABLES <---
uidoc = __revit__.ActiveUIDocument          #type: UIDocument
doc = __revit__.ActiveUIDocument.Document   #type: Document
app = __revit__.Application                 #type: UIApplication
rvt_year = int(app.VersionNumber)

# ===============
# ---> CLASSES <---
class RenamerListVM_MainWindow(ViewModelBase):
	"""Class related to Renamer."""
	def __init__(self, vm_tree_viewer, vm_information, main_window_view):
		super(RenamerListVM_MainWindow,self).__init__()
		self._vm_tree_viewer = vm_tree_viewer
		self._vm_information = vm_information		# type: InformationVM_MainWindow
		self._main_window_view = main_window_view
		self._text_manip_class = Token_TextManipulation_Control()
		self._error_list = []
		# Bind ListView's ItemsControl to the below
		self._grouped_templates = ObservableCollection[object]()   # type: list[GroupData_Renamer]
		self._template_lookup = {}   # richtextbox_text -> GroupData_Renamer, just for de-dupe/refresh
		self._rename_collection = {}

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

	@property
	def RenameCollection(self):
		"""Dictionary collection for storing old name and new name for renaming."""
		return self._rename_collection

	@RenameCollection.setter
	def RenameCollection(self, value):
		self._rename_collection = value
		self.OnPropertyChanged("RenameCollection")

	# Methods
	# -------------------
	def _recalculate_total_errors(self):
		"""Recompute total error count across all grouped templates and push it to InformationVM."""
		total = 0
		for gdr in self._grouped_templates:
			total += len(gdr.TemplateErrorList)
		self._vm_information.TotalErrorCaptured = total
		self._vm_information.IsListGenerated = len(self._grouped_templates) > 0

	def populate_data_in_groups(self, richtextbox_object):
		"""Method of invoking populating the groups when clicked apply."""
		richtextbox_text = extract_richtextbox_contents(richtextbox_object)
		if not richtextbox_text: return

		extracted_token_list, extracted_params_set = self._text_manip_class.extract_variables(richtextbox_text)
		if not extracted_token_list: 
			TaskDialog.Show("Invalid", "Parameter not found.\nPlease add Parameter from collection.")
			self._main_window_view.restore_window()
			return

		# Check whether the extracted parameters are in sync with parameters collection or not.
		params_collection = self._vm_information.DynamicParameterSet
		check_part = extracted_params_set.issubset(params_collection)
		if not check_part:
			set_difference = extracted_params_set.difference(params_collection)
			msg00 = ""
			for idx, item in enumerate(set_difference):
				msg00 += "\n{}. {}".format((idx + 1), item)
			msg01 = "Following Parameters are either invalid or not present -\n\n{}".format(msg00)
			TaskDialog.Show("Invalid", msg01)
			return

		compiled_list = []
		name_dict = {}
		# `clear()` for clearing python list was introduced in Python 3, therefore we'll need to use slicing for clearing the list.
		self._error_list[:] = []		
		existing = self._template_lookup.get(richtextbox_text)
		if existing is None:
			# Substitute parameters value in template
			gdr = GroupData_Renamer(self._vm_tree_viewer, richtextbox_text)
			rename_list, checked_elements = gdr.get_item_collection()
			
			# Add it in a dictionary
			for item in rename_list:
				name_dict[item[0]] = (item[1], item[2])

			compiled_list.extend(rename_list)	# Extending the compiled list having tuple (old name, new name)
			self._error_list.extend(gdr.TemplateErrorList)	# Extending the error list
			self._vm_tree_viewer.ElementsChecked.update(checked_elements)
			self._template_lookup[richtextbox_text] = gdr
			self._grouped_templates.Add(gdr)
		else:
			rename_list, checked_elements = existing.get_item_collection()   # re-run against current tree selection
			self._vm_tree_viewer.ElementsChecked.update(checked_elements)
			for item in rename_list:
				if item[0] not in self._rename_collection:
					self._rename_collection[item[0]] = (item[1], item[2])

		self._vm_tree_viewer.tree_collapse_checked_items()
		self._rename_collection = name_dict
		self._recalculate_total_errors()

	def clear_all_groups(self):
		"""
		Clear both the binded collection and the template lookup dictionary, since it looks for unique items.
		If template lookup dictionary is not cleared, it will not add the items in the list the next time it is 
		switched back & forth the combobox choices.
		"""
		self._grouped_templates.Clear()
		self._template_lookup.clear()
		self._recalculate_total_errors()

	def update_template_group(self, group_data, richtextbox_object):
		# type: (GroupData_Renamer, RichTextBox) -> bool
		"""Re-evaluate an already-held template group against edited RichTextBox text. Returns False on validation failure."""
		new_text = extract_richtextbox_contents(richtextbox_object)
		if not new_text:
			return False

		extracted_token_list, extracted_params_set = self._text_manip_class.extract_variables(new_text)
		if not extracted_token_list:
			TaskDialog.Show("Invalid", "Parameter not found.\nPlease add Parameter from collection.")
			self._main_window_view.restore_window()
			return False

		params_collection = self._vm_information.DynamicParameterSet
		if not extracted_params_set.issubset(params_collection):
			set_difference = extracted_params_set.difference(params_collection)
			msg00 = ""
			for idx, item in enumerate(set_difference):
				msg00 += "\n{}. {}".format((idx + 1), item)
			TaskDialog.Show("Invalid", "Following Parameters are either invalid or not present -\n\n{}".format(msg00))
			return False

		old_text = group_data.TemplateName
		if old_text == new_text:
			return True		# nothing changed - still a "success" so the caller releases the hold

		if new_text in self._template_lookup:
			TaskDialog.Show("Invalid", "A template with this exact text already exists.")
			return False

		group_data.update_template(new_text)
		for row in group_data.DataGridCollection:
			if row.HasError:
				self._rename_collection.pop(row.OldName, None)		# stale/invalid - drop it, don't rename
			else:
				self._rename_collection[row.OldName] = (row.NewName, row.ElementID)
		
		del self._template_lookup[old_text]
		self._template_lookup[new_text] = group_data

		self._error_list[:] = []
		for gdr in self._grouped_templates:
			self._error_list.extend(gdr.TemplateErrorList)
		self._recalculate_total_errors()
		return True

	def rename_final_elements(self):
		"""Rename final elements by applying staged old->new names to the Revit model."""
		if not self._rename_collection: return
		count_success = 0
		count_failed = 0
		failed = []
		t = Transaction(doc, "Bulk Rename Elements")
		t.Start()
		for old_name, (new_name, element_id) in self._rename_collection.items():
			elem_id_obj = build_element_id(element_id)
			element = doc.GetElement(elem_id_obj)
			if element is None:
				failed.append((old_name, "Element no longer exists."))
				continue
			try:
				Element.Name.__set__(element, new_name)
				count_success += 1
			except Exception as e:
				failed.append((old_name, str(e)))
				count_failed += 1
		t.Commit()
		self._vm_information.CountSuccess = count_success
		self._vm_information.CountFailed = count_failed
		self._vm_information.ErrorListCombined = failed
