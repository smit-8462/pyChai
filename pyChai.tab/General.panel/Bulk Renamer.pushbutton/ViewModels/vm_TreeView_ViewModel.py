# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, traceback, clr

clr.AddReference("System")
from System.Windows.Controls import RadioButton

from lib_WPF.Helpers.he_ViewModel_ViewModelBase import ViewModelBase

from Helpers.he_extension_ViewModel import TreeViewerVM_Extender

# ===============
# ---> Helper Class <---
# region Sub-Classes
class TreeViewerVM_Option_FamilyType(TreeViewerVM_Extender):
	"""Tree Viewer VM when "Family Type" option is chosen. 3 tree variants (Built-In/Family/Both)."""
	def __init__(self):
		super(TreeViewerVM_Option_FamilyType, self).__init__()
		from ViewModels.vm_Option_FamilyType import TreeCollection_FamilyType
		self._tree_collection_cls = TreeCollection_FamilyType		# keep the class reference for refresh_data_source
		self._tree_collection = TreeCollection_FamilyType()
		self._current_filter = "both"		# remembers which radio choice is active, for refresh_data_source
		self.familytype_select_both()

	# Methods
	# -------------------
	def selection_type_changed(self, sender):
		# type: (RadioButton) -> None
		"""Process based on radio button selected option. Here, param is RadioButton itself."""
		radio_button_name = sender.Name
		if radio_button_name == "Choice_FamilyType_Builtin":
			self._current_filter = "builtin"
			self.refresh_tree(self._tree_collection.PopulateBuiltin)
		elif radio_button_name == "Choice_FamilyType_Loaded":
			self._current_filter = "loaded"
			self.refresh_tree(self._tree_collection.PopulateLoaded)
		elif radio_button_name == "Choice_FamilyType_Both":
			self.familytype_select_both()

	def familytype_select_both(self):
		"""Little helper wrapper for accessing in MainWindow."""
		self._current_filter = "both"
		return self.refresh_tree(self._tree_collection.PopulateBoth)

	def refresh_data_source(self):
		"""Refresh Tree viewer."""
		self._tree_collection = self._tree_collection_cls()		# re-run the Revit query, no re-import needed
		if self._current_filter == "builtin":
			self.refresh_tree(self._tree_collection.PopulateBuiltin)
		elif self._current_filter == "loaded":
			self.refresh_tree(self._tree_collection.PopulateLoaded)
		else:
			self.refresh_tree(self._tree_collection.PopulateBoth)

# ----------------
class TreeViewerVM_Option_View(TreeViewerVM_Extender):
	"""Tree Viewer VM when "Views" option is chosen."""
	def __init__(self):
		super(TreeViewerVM_Option_View, self).__init__()
		from ViewModels.vm_Option_Views import TreeCollection_Views
		self._tree_collection_cls = TreeCollection_Views		# keep the class reference for refresh_data_source
		self._tree_collection = TreeCollection_Views()
		self._current_filter = "both"		# remembers which radio choice is active, for refresh_data_source
		self.view_select_both()

	# Methods
	# -------------------
	def selection_type_changed(self, sender):
		# type: (RadioButton) -> None
		"""Process based on radio button selected option. Here, param is RadioButton itself."""
		radio_button_name = sender.Name
		if radio_button_name == "Choice_View_OnSheet":
			self._current_filter = "onsheet"
			self.refresh_tree(self._tree_collection.PopulateViewOnSheet)
		elif radio_button_name == "Choice_View_OffSheet":
			self._current_filter = "offsheet"
			self.refresh_tree(self._tree_collection.PopulateViewOffSheet)
		elif radio_button_name == "Choice_View_Both":
			self.view_select_both()

	def view_select_both(self):
		"""Little helper wrapper for accessing in MainWindow."""
		self._current_filter = "both"
		return self.refresh_tree(self._tree_collection.PopulateBoth)

	def refresh_data_source(self):
		"""Refresh Tree viewer."""
		self._tree_collection = self._tree_collection_cls()		# re-run the Revit query, no re-import needed
		if self._current_filter == "onsheet":
			self.refresh_tree(self._tree_collection.PopulateViewOnSheet)
		elif self._current_filter == "offsheet":
			self.refresh_tree(self._tree_collection.PopulateViewOffSheet)
		else:
			self.refresh_tree(self._tree_collection.PopulateBoth)

# ----------------
class TreeViewerVM_Option_Sheet(TreeViewerVM_Extender):
	"""Tree Viewer VM when "Sheet" option is chosen."""
	def __init__(self):
		super(TreeViewerVM_Option_Sheet, self).__init__()
		from ViewModels.vm_Option_Sheet import TreeCollection_Sheets
		self._tree_collection_cls = TreeCollection_Sheets		# keep the class reference for refresh_data_source
		self._tree_collection = TreeCollection_Sheets()
		self._current_filter = "both"		# remembers which radio choice is active, for refresh_data_source
		self.sheet_select_both()

	# Methods
	# -------------------
	def selection_type_changed(self, sender):
		# type: (RadioButton) -> None
		"""Process based on radio button selected option. Here, param is RadioButton itself."""
		radio_button_name = sender.Name
		if radio_button_name == "Choice_Sheet_Empty":
			self._current_filter = "empty"
			self.refresh_tree(self._tree_collection.PopulateEmptySheet)
		elif radio_button_name == "Choice_Sheet_Filled":
			self._current_filter = "filled"
			self.refresh_tree(self._tree_collection.PopulateFilledSheet)
		elif radio_button_name == "Choice_Sheet_Both":
			self.sheet_select_both()

	def sheet_select_both(self):
		"""Little helper wrapper for accessing in MainWindow."""
		self._current_filter = "both"
		return self.refresh_tree(self._tree_collection.PopulateBoth)

	def refresh_data_source(self):
		"""Refresh Tree viewer."""
		self._tree_collection = self._tree_collection_cls()		# re-run the Revit query, no re-import needed
		if self._current_filter == "empty":
			self.refresh_tree(self._tree_collection.PopulateEmptySheet)
		elif self._current_filter == "filled":
			self.refresh_tree(self._tree_collection.PopulateFilledSheet)
		else:
			self.refresh_tree(self._tree_collection.PopulateBoth)

# ----------------
class TreeViewerVM_Option_Level(TreeViewerVM_Extender):
	"""Tree Viewer VM when "Level" option is chosen."""
	def __init__(self):
		super(TreeViewerVM_Option_Level, self).__init__()
		from ViewModels.vm_Option_Level import TreeCollection_Levels
		self._tree_collection_cls = TreeCollection_Levels		# keep the class reference for refresh_data_source
		self._tree_collection = TreeCollection_Levels()
		self._current_filter = "both"		# remembers which radio choice is active, for refresh_data_source
		self.level_select_both()

	def selection_type_changed(self, sender):
		"""Process based on radio button selected option. Here, param is RadioButton itself."""
		radio_button_name = sender.Name
		if radio_button_name == "Choice_Level_Active":
			self._current_filter = "active"
			self.refresh_tree(self._tree_collection.PopulateActiveLevel)
		elif radio_button_name == "Choice_Level_Stray":
			self._current_filter = "stray"
			self.refresh_tree(self._tree_collection.PopulateStrayLevel)
		elif radio_button_name == "Choice_Level_Both":
			self.level_select_both()

	def level_select_both(self):
		"""Little helper wrapper for accessing in MainWindow."""
		self._current_filter = "both"
		return self.refresh_tree(self._tree_collection.PopulateBoth)

	def refresh_data_source(self):
		"""Refresh Tree viewer."""
		self._tree_collection = self._tree_collection_cls()		# re-run the Revit query, no re-import needed
		if self._current_filter == "active":
			self.refresh_tree(self._tree_collection.PopulateActiveLevel)
		elif self._current_filter == "stray":
			self.refresh_tree(self._tree_collection.PopulateStrayLevel)
		else:
			self.refresh_tree(self._tree_collection.PopulateBoth)
# endregion

# ===============
# ---> Dictionary Class <---
# Mapping ComboBox choice to particular workflow's TreeViewerVM_Option_<Workflow> class.
WORKFLOW_CLASSES = {
	"combo_pick_family_type": TreeViewerVM_Option_FamilyType,
	"combo_pick_view": TreeViewerVM_Option_View,
	"combo_pick_sheet": TreeViewerVM_Option_Sheet,
	"combo_pick_level": TreeViewerVM_Option_Level
}

# ===============
# ---> Main Class <---
class TreeViewerVM_MainWindow(ViewModelBase):
	"""
	Top-level Tree Viewer VM that MainWindowViewModel and XAML bind against.
	Holds one `TreeViewerVM_Option_<Workflow>` instance per workflow (built lazily, cached after first visit, so switching 
	back preserves that workflow's tree/checked state) and forwards binding-relevant properties/methods to whichever is active.
	"""
	def __init__(self, combo_pick_choice="combo_pick_family_type"):
		super(TreeViewerVM_MainWindow, self).__init__()
		self._workflow_instances = {}		# type: dict[str, TreeViewerVM_Extender]
		self._selected_class = None			# type: TreeViewerVM_Extender|None
		self.set_workflow(combo_pick_choice)
		self._elements_checked = set()

	# Property
	# -------------------
	@property
	def SelectedClass(self):
		return self._selected_class

	@property
	def RootItems(self):
		return self._selected_class.RootItems if self._selected_class else None

	@property
	def CheckedItems(self):
		return self._selected_class.CheckedItems if self._selected_class else []

	@property
	def Command_SelectionType(self):
		return self._selected_class.Command_SelectionType if self._selected_class else None

	@property
	def ElementsChecked(self):
		"""Set collection for items checked when "Apply" button is clicked."""
		return self._elements_checked

	@ElementsChecked.setter
	def ElementsChecked(self, value):
		self._elements_checked = value
		self.OnPropertyChanged("ElementsChecked")

	# Methods
	# -------------------
	def set_workflow(self, workflow_key):
		# type: (str) -> None
		instance = self._workflow_instances.get(workflow_key)
		if instance is None:
			workflow_cls = WORKFLOW_CLASSES.get(workflow_key)
			if workflow_cls is None:
				return
			instance = workflow_cls()
			self._workflow_instances[workflow_key] = instance
		
		self._selected_class = instance
		self.OnPropertyChanged("SelectedClass")
		self.OnPropertyChanged("RootItems")
		self.OnPropertyChanged("CheckedItems")
		self.OnPropertyChanged("Command_SelectionType")

	# -------------------
	def selection_type_changed(self, sender):
		# type: (RadioButton) -> None
		if self._selected_class is not None:
			self._selected_class.selection_type_changed(sender)

	def tree_selection_invert(self):
		if self._selected_class is not None:
			self._selected_class.tree_selection_invert()

	def tree_selection_all(self):
		if self._selected_class is not None:
			self._selected_class.tree_selection_all()

	def tree_selection_clear(self):
		if self._selected_class is not None:
			self._selected_class.tree_selection_clear()

	def tree_search_expand_all_items(self):
		if self._selected_class is not None:
			self._selected_class.tree_search_expand_all_items()

	def tree_search_collapse_all_items(self):
		if self._selected_class is not None:
			self._selected_class.tree_search_collapse_all_items()

	def tree_collapse_checked_items(self):
		if self._selected_class is not None:
			self._selected_class.tree_collapse_checked_items(self._elements_checked)

	def tree_refresh_from_source(self):
		"""Re-query Revit and rebuild the currently active workflow's tree, respecting already-processed items."""
		if self._selected_class is not None:
			self._selected_class.refresh_data_source()
			
	def tree_search_filter_changed(self, search_text):
		if self._selected_class is not None:
			self._selected_class.tree_search_filter_changed(search_text)

	def tree_search_clear_input(self):
		if self._selected_class is not None:
			self._selected_class.tree_search_clear_input()

	def tree_restore_hidden_items(self):
		if self._selected_class is not None:
			self._selected_class.tree_restore_hidden_items()
		self.ElementsChecked = set()		# forget which elements were staged for the next Apply pass, too
