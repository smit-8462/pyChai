# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import os, clr

clr.AddReference("System")

# from System.Windows import Window, ResourceDictionary
from System.Windows import ResourceDictionary
from System import Uri, UriKind
# import System

# ===============
# ---> VARIABLES <---
SHARED_RESOURCES = []

# ===============
# ---> CLASSES <---
class ResDictManager(object):
	def __init__(self,use_lib_resources=False):
		"""
		Wheter the script should use Resources folder located in lib or not.
		:param use_lib_resources: True for shared lib, False for getting Resources in pushbutton folder.
		:type use_lib_resources: bool
		"""
		cur_file = os.path.abspath(__file__)  # type: str
		cur_dir = os.path.dirname(cur_file)
		self._use_lib_resources = use_lib_resources
		if self._use_lib_resources:
			self.resource_dir = self._get_shared_lib_resource_path()
		else:
			self.resource_dir = os.path.abspath(os.path.join(cur_dir, "..", "Resources"))

	def apply_to(self, target, xaml_list):
		"""Works for any FrameworkElement - Window, UserControl, etc. Call before wpf.LoadComponent on UserControls."""
		if not xaml_list:
			raise ValueError("The provided list cannot be None or empty.")

		SHARED_RESOURCES[:] = []						# reset in-place, preserving the reference
		target.Resources.MergedDictionaries.Clear()		# Clear existing xaml files

		for xaml_file in xaml_list:
			rd = ResourceDictionary()
			file_path = os.path.join(self.resource_dir, xaml_file)
			rd.Source = Uri(file_path, UriKind.Absolute)
			target.Resources.MergedDictionaries.Add(rd)
			SHARED_RESOURCES.append(rd.Source)

	@staticmethod
	def apply_shared(target):
		"""Apply already-collected SHARED_RESOURCES to a target."""
		if not SHARED_RESOURCES:
			raise RuntimeError("SHARED_RESOURCES is empty. Call apply_to() on MainWindow first.")
		target.Resources.MergedDictionaries.Clear()		# Clear existing xaml files
		for uri in SHARED_RESOURCES:
			rd = ResourceDictionary()
			rd.Source = uri
			target.Resources.MergedDictionaries.Add(rd)

	@staticmethod
	def _get_shared_lib_resource_path():
		"""
		Get the shared lib Resources path.
		:return: Shared lib Resources path
		:rtype: str
		"""
		file_path = os.path.dirname(__file__)
		file_list = file_path.split(os.sep)
		pychai_extension_folder = None
		for item in file_list:
			if item.endswith(".extension"):
				chai_index = file_list.index(item)
				new_list = file_list[:(chai_index + 1)]  # type: list
				new_list.insert(1, "\\")  # inserting '\' after the drive letter "D:\".
				pychai_extension_folder = os.path.join(*new_list)  # Unpacking list items.
				break
		lib_resources_path = os.path.join(pychai_extension_folder, "lib", "lib_WPF", "Resources")
		return lib_resources_path

# ===============
# ---> METHODS <---
def add_resource_dict(target, resource_dict_list):
	"""
	Add Resource Dictionary to XAML UI.
	:param target: Attach to target Window reference. It will act as "self" function in python.
	:type target: self
	:param resource_dict_list: List of Resource Dictionary to add.
	:type resource_dict_list: list
	"""
	# Get file paths of XAML files
	cur_file = os.path.abspath(__file__)	# type: str
	cur_dir = os.path.dirname(cur_file)
	goback_dir = os.path.abspath(os.path.join(cur_dir, ".."))  # Go back to previous directory
	resource_dir = os.path.join(goback_dir, "Resources")  # Resource directory

	# Get absolute path for files
	resdict_list_absolute = [os.path.join(resource_dir, fil) for fil in resource_dict_list]

	# Add to resource directory
	for abs_file_path in resdict_list_absolute:
		rd = ResourceDictionary()
		rd.Source = Uri(abs_file_path, UriKind.Absolute)
		target.Resources.MergedDictionaries.Add(rd)