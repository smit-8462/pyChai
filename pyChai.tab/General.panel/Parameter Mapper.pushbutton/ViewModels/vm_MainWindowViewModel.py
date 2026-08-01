# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback

from Autodesk.Revit.UI import TaskDialog

clr.AddReference("System")
from System.Collections.ObjectModel import ObservableCollection

from lib_WPF.Helpers.he_ViewModel_ViewModelBase import ViewModelBase

from ViewModels.vm_ChoicesViewModel import ChoicesViewModel_MainWindow

from Models.mo_elem_selecter import category_in_model_list, ElementSelecter
from Models.mo_fileiops import load_file

from Helpers.he_fileviewer import shorten_path

from lib_System.sys_output import SysOutput_Markdown

# ===============
# ---> VARIABLES <---
PY_SCRIPT_PATH = os.path.abspath(__file__)    # type: str

# ===============
# ---> CLASSES <---
class MainWindowViewModel(ViewModelBase):
	"""Main Window View Model."""
	def __init__(self):
		super(MainWindowViewModel, self).__init__()
		self.FileSelection = FileSelection_MainWindow()
		self.CategorySelection = CategorySelection_MainWindow()
		# Passing/injecting the shared instance reference of CategorySelection.
		self.ElementSelection = ElementSelection_MainWindow(self.CategorySelection)
		self.ChoicesVM = ChoicesViewModel_MainWindow(self.CategorySelection, self.ElementSelection, self.FileSelection)
		self._preview_window_vm = None		# We will pass the vm_PreviewWindowMainModel instance from MainWindow view.

		# Reset the SelectedElements count to None when there is change in SelectedCategory
		# We are doing this because ElementSelection is appearing after CategorySelection in orderwise.
		lambda_fucntion = lambda: setattr(self.ElementSelection, 'SelectedElements', None)
		self.CategorySelection.set_on_changed(lambda_fucntion)

	# Property
	# -------------------
	@property
	def PreviewWindowVMProperty(self):
		return self._preview_window_vm

	@PreviewWindowVMProperty.setter
	def PreviewWindowVMProperty(self, value):
		self._preview_window_vm = value

	# Method
	# -------------------
	def markdown_output(self):
		template_md_file_list = ["TemplateOutput01.md", "TemplateOutput02.md"]
		_errors_count = self.ElementSelection.ElementsErrorsValidated
		_skipped_params_count = self.ElementSelection.ReadOnlyParametersCount
		_skipped_elements_count = self.ElementSelection.SkippedElementsDueToErrorsCount
		template_variables = {
			"md_elem_total_count": self.ElementSelection.ElementsTotal,
			"md_elem_success_count": self.ElementSelection.ElementsSuccess,
			"md_elem_failed_count": self.ElementSelection.ElementsFailed,
			"md_file_spreadsheet": self.FileSelection.SelectedFilePath,
			"md_elem_errors_count": _errors_count,
			"md_elem_readonly_count": _skipped_params_count,
			"md_incompatible_elements_section": "",
			"md_skipped_parameters_section": "",
			"md_skipped_elements_section": ""
		}

		if _errors_count > 0:
			errors_list = self._preview_window_vm.ErrorTextBoxDataFill if self.ElementSelection.HasPreviewWindowOpened and self._preview_window_vm is not None else ""
			template_variables["md_incompatible_elements_section"] = (
				"### Incompatible Elements\n\n"
				"The following errors were raised for having incompatible values extracted from selected spreadsheet file -\n\n"
				"{}\n\n---\n".format(errors_list)
			)
		if _skipped_params_count > 0:
			skipped_readonly_list_string = self.ElementSelection.SkippedParametersReadonlyString if self.ElementSelection.HasPreviewWindowOpened and \
				self._preview_window_vm is not None and self._preview_window_vm.HasUserClickedOnFinalApplyButton is True else ""
			template_variables["md_skipped_parameters_section"] = (
				"### Skipped Parameters\n\n"
				"The following were skipped due to read-only parameter -\n\n"
				"{}\n\n---\n".format(skipped_readonly_list_string)
			)
		if _skipped_elements_count > 0:
			skipped_elements_string = self.ElementSelection.SkippedElementsDueToErrorsString if self.ElementSelection.HasPreviewWindowOpened and \
				self._preview_window_vm is not None and self._preview_window_vm.HasUserClickedOnFinalApplyButton is True else ""
			template_variables["md_skipped_elements_section"] = (
				"### Skipped Elements\n\n"
				"The following elements were skipped -\n\n"
				"{}\n\n---\n".format(skipped_elements_string)
			)

		sys_md = SysOutput_Markdown(PY_SCRIPT_PATH, template_md_file_list, template_variables)
		sys_md.show_error_output()

	def select_elements(self, mode):
		if not self.CategorySelection.SelectedCategory:
			TaskDialog.Show("Warning", "Category not selected.")
			return
		if not self.FileSelection.SelectedFilePath:		# Check if file is selected or not
			self.ElementSelection.SelectedElements = None
			TaskDialog.Show("Warning", "File not selected.")
			return

		# Selection of elements
		if mode == "manual":
			self.ElementSelection.select_elements_manual()
		else:
			self.ElementSelection.select_elements_all()
	
		if not self.ElementSelection.SelectedElements: 
			return
		self.ChoicesVM.choices_list_setup()
		if not self.ChoicesVM.ExcelColumnList:	# If Excel column list is empty, re-populate the list
			self.ChoicesVM.excel_dict_setup()

	def clear_main_things(self):
		self.ElementSelection.SelectedElements = None
		self.ElementSelection.HasPreviewWindowOpened = False
		self.ChoicesVM.RevitParameterList = None
		self.ChoicesVM.ExcelColumnList = None
		self.ChoicesVM.reset_to_default_row_collection()

	def clear_all_things(self):
		self.FileSelection.SelectedFilePath = None
		self.FileSelection.SelectedFileExtension = None
		self.FileSelection.SelectedFileText = "Pick File"
		self.CategorySelection.SelectedCategory = None
		self.clear_main_things()

	def pick_file_method(self):
		file_path = load_file()
		if file_path:
			file_extension = os.path.splitext(file_path)[1]
			self.FileSelection.SelectedFilePath = file_path
			self.FileSelection.SelectedFileExtension = file_extension
			self.FileSelection.SelectedFileText = shorten_path(file_path)
			self.ChoicesVM.excel_dict_setup()

# ===============
# ---> Helper Classes <---
class FileSelection_MainWindow(ViewModelBase):
	"""Class related to file selection."""
	def __init__(self):
		super(FileSelection_MainWindow, self).__init__()
		self._selectedFilePath = None
		self._selectedFileText = "Pick File"
		self._selectedFileExtension = None

	# Property
	# -------------------
	@property
	def SelectedFilePath(self):
		return self._selectedFilePath

	@SelectedFilePath.setter
	def SelectedFilePath(self, value):
		self._selectedFilePath = value
		self.OnPropertyChanged("SelectedFilePath")

	@property
	def SelectedFileText(self):
		return self._selectedFileText

	@SelectedFileText.setter
	def SelectedFileText(self, value):
		self._selectedFileText = value
		self.OnPropertyChanged("SelectedFileText")

	@property
	def SelectedFileExtension(self):
		return self._selectedFileExtension

	@SelectedFileExtension.setter
	def SelectedFileExtension(self, value):
		self._selectedFileExtension = value
		self.OnPropertyChanged("SelectedFileExtension")


class CategoryItem(object):
	"""Wrapper class category selection so WPF can bind to properties."""
	def __init__(self, cat_name, cat_builtincat):
		self._cat_name = cat_name
		self._cat_builtincat = cat_builtincat

	@property
	def CatName(self):
		return self._cat_name

	@property
	def CatBuiltinCat(self):
		return self._cat_builtincat

	def ToString(self):
		"""Overriding .NET ToString() to display CatName instead of IronPython string error."""
		return self._cat_name


class CategorySelection_MainWindow(ViewModelBase):
	"""Class related to category selection."""
	def __init__(self):
		super(CategorySelection_MainWindow, self).__init__()
		self._on_changed = lambda: None  # It is an empty function defined by using lambda.
		self.category_dict = category_in_model_list()
		self._selected_category = None
		self.category_items = ObservableCollection[CategoryItem]()	# Initialise ObservableCollection of type CategoryItem
		for cat_name, cat_bic in self.category_dict:
			self.category_items.Add(CategoryItem(cat_name, cat_bic))

	@property
	def CategoryItems(self):
		"""ItemsSource for the ComboBox."""
		return self.category_items

	@property
	def SelectedCategory(self):
		return self._selected_category

	@SelectedCategory.setter
	def SelectedCategory(self, value):
		self._selected_category = value
		self.OnPropertyChanged("SelectedCategory")
		self._on_changed()		# Function created using lambda in __init__.

	@property
	def SelectedBuiltInCategory(self):
		"""Returns the BuiltInCategory of the selected item."""
		if self._selected_category:
			return self._selected_category.CatBuiltinCat
		return None

	def set_on_changed(self, callback_function):
		self._on_changed = callback_function  # Store the function defined using lambda


class ElementSelection_MainWindow(ViewModelBase):
	"""Class related to element selection."""
	def __init__(self, category_selection):
		super(ElementSelection_MainWindow, self).__init__()
		self._category_selection = category_selection	# reference to shared instance
		self.element_list = None

		self._elements_skipped = 0				# Elements skipped based on Excel rows mapping. Also include elements skipped duting transaction.
		self._elements_errors_validated = 0		# Elements which are shown as error based on WPF DataTable validation.
		self._has_preview_window_opened = False  # Cheking if PreviewWindow is opened
		self._readonly_parameters = []
		self._skipped_elements_due_to_errors = []

	# Property
	# -------------------
	@property
	def ReadOnlyParameters(self):
		return self._readonly_parameters

	@ReadOnlyParameters.setter
	def ReadOnlyParameters(self, value):
		self._readonly_parameters = value
		self.OnPropertyChanged("ReadOnlyParameters")
		self.OnPropertyChanged("ReadOnlyParametersCount")
		self.OnPropertyChanged("SkippedParametersReadonlyString")

	@property
	def SkippedElementsDueToErrors(self):
		return self._skipped_elements_due_to_errors

	@SkippedElementsDueToErrors.setter
	def SkippedElementsDueToErrors(self, value):
		self._skipped_elements_due_to_errors = value
		self.OnPropertyChanged("SkippedElementsDueToErrors")
		self.OnPropertyChanged("SkippedElementsDueToErrorsCount")
		self.OnPropertyChanged("SkippedElementsDueToErrorsString")
		self.OnPropertyChanged("ElementsFailed")   # depends on ElementsSkipped
		self.OnPropertyChanged("ElementsSuccess")  # depends on ElementsFailed

	@property
	def SkippedParametersReadonlyString(self):
		combined_string = ""
		for idx, items in enumerate(self.ReadOnlyParameters):
			combined_string += "{}. {}".format(idx + 1, items) + "\n"
		return combined_string

	@property
	def SkippedElementsDueToErrorsString(self):
		combined_string = ""
		for idx, items in enumerate(self.SkippedElementsDueToErrors):
			combined_string += "{}. {}".format(idx + 1, items) + "\n"
		return combined_string

	@property
	def ReadOnlyParametersCount(self):
		return len(self.ReadOnlyParameters)

	@property
	def SkippedElementsDueToErrorsCount(self):
		return len(self.SkippedElementsDueToErrors)

	@property
	def HasPreviewWindowOpened(self):
		return self._has_preview_window_opened

	@HasPreviewWindowOpened.setter
	def HasPreviewWindowOpened(self, value):
		self._has_preview_window_opened = value
		self.OnPropertyChanged("HasPreviewWindowOpened")

	@property
	def SelectedBuiltInCategory(self):
		"""Delegates to CategorySelection to get the current BuiltInCategory."""
		return self._category_selection.SelectedBuiltInCategory

	@property
	def ElementsTotal(self):
		if self.element_list is None:
			return 0
		return len(self.element_list)

	@property
	def ElementsSuccess(self):
		if self.ElementsTotal and self.ElementsFailed:
			return self.ElementsTotal - self.ElementsFailed
		else:
			return 0

	@property
	def ElementsFailed(self):
		return self.ElementsSkipped + self.ElementsErrorsValidated + self.SkippedElementsDueToErrorsCount

	@property
	def SelectedElements(self):
		return self.element_list

	@SelectedElements.setter
	def SelectedElements(self, value):
		self.element_list = value
		if value is None:
			self._elements_skipped = 0
			self._elements_errors_validated = 0
		self.OnPropertyChanged("SelectedElements")
		self.OnPropertyChanged("ElementsTotal")  	# Notify WPF to re-read the computed property
		self.OnPropertyChanged("ElementsSuccess")   # ElementsTotal changed, so this did too
		self.OnPropertyChanged("ElementsSkipped")
		self.OnPropertyChanged("ElementsErrorsValidated")
		self.OnPropertyChanged("ElementsFailed")

	@property
	def ElementsSkipped(self):
		return self._elements_skipped

	@ElementsSkipped.setter
	def ElementsSkipped(self, value):
		self._elements_skipped = value
		self.OnPropertyChanged("ElementsSkipped")
		self.OnPropertyChanged("ElementsFailed")   # depends on ElementsSkipped
		self.OnPropertyChanged("ElementsSuccess")  # depends on ElementsFailed

	@property
	def ElementsErrorsValidated(self):
		return self._elements_errors_validated

	@ElementsErrorsValidated.setter
	def ElementsErrorsValidated(self, value):
		self._elements_errors_validated = value
		self.OnPropertyChanged("ElementsErrorsValidated")
		self.OnPropertyChanged("ElementsFailed")   # depends on ElementsErrorsValidated
		self.OnPropertyChanged("ElementsSuccess")  # depends on ElementsFailed

	# Methods
	# -------------------
	def select_elements_all(self):
		bic = self.SelectedBuiltInCategory
		if bic is None:
			return
		elem_selector = ElementSelecter(bic)
		self.element_list = elem_selector.select_all()
		self.SelectedElements = self.element_list		# Updating the SelectedElements list property

	def select_elements_manual(self):
		bic = self.SelectedBuiltInCategory
		if bic is None:
			return
		elem_selector = ElementSelecter(bic)
		self.element_list = elem_selector.elem_select_manual()
		if self.element_list is None:
			TaskDialog.Show("Warning", "Elements not selected.")
			return
		self.SelectedElements = self.element_list  # Updating the SelectedElements list property