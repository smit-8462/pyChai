# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import os, clr

clr.AddReference("System")

from System.Windows import Window, ResourceDictionary
from System import Uri, UriKind

# ===============
# ---> CLASSES <---
class ThemeManager(object):
	def __init__(self, window_target, primary_theme_xaml, secondary_theme_xaml, extra_targets=None, use_lib_resources=False):
		"""
		Change between primary theme and secondary theme.
		:param window_target: Target Window.
		:type window_target: Window.
		:param primary_theme_xaml: Name of primary theme XAML file.
		:type primary_theme_xaml: str
		:param secondary_theme_xaml: Name of secondary theme XAML file.
		:type secondary_theme_xaml: str
		:param extra_targets: Extra targets.
		:type extra_targets: list
		:param use_lib_resources: Whether to use Resources folder location in lib or not.
		:type use_lib_resources: bool
		"""
		self._window_target = window_target		# Window target reference stored here
		self._extra_targets = extra_targets or []  # list of additional FrameworkElements
		self._primary_theme_xaml = primary_theme_xaml
		self._secondary_theme_xaml = secondary_theme_xaml
		self._use_lib_resources = use_lib_resources
		self.uri_primary, self.uri_secondary = self._uri_path()

		# Apply the primary (light) theme at the window launch, instead of waiting for user to press the toggle button.
		self._add_theme(self.uri_primary)
		self.is_primary = True

	def _all_targets(self):
		"""Combine MainWindow and other targets."""
		return [self._window_target] + self._extra_targets

	def _uri_path(self):
		"""
		Get Uri of primary and secondary theme XAML files.
		:return: Uri of XAML files.
		:rtype: Uri
		"""
		# Get file paths of XAML files
		if self._use_lib_resources:
			resource_dir = self._get_shared_lib_resource_path()
		else:
			cur_file = os.path.abspath(__file__)  # type: str
			cur_dir = os.path.dirname(cur_file)
			goback_dir = os.path.abspath(os.path.join(cur_dir, ".."))  # Go back to previous directory
			resource_dir = os.path.join(goback_dir, "Resources")  # Resource directory
		themes_dir = os.path.join(resource_dir, "Themes")  # Themes directory

		primary_path = os.path.join(themes_dir, self._primary_theme_xaml)
		secondary_path = os.path.join(themes_dir, self._secondary_theme_xaml)
		uri_primary = Uri(primary_path, UriKind.Absolute)
		uri_secondary = Uri(secondary_path, UriKind.Absolute)
		return uri_primary, uri_secondary

	def _add_theme(self, xaml_uri):
		"""Add theme XAML file."""
		for target in self._all_targets():
			rd = ResourceDictionary()
			rd.Source = xaml_uri
			target.Resources.MergedDictionaries.Add(rd)

	def _remove_theme(self, xaml_uri):
		"""Remove theme XAML file."""
		# Get same ResourceDictionary instance, we don't need to delete from new instance.
		uri_str = str(xaml_uri)
		for target in self._all_targets():
			to_remove = None	# Store Uri of MergedDictionary
			for rd in target.Resources.MergedDictionaries:
				if str(rd.Source) == uri_str:
					to_remove = rd		# type: Uri
					break
			if to_remove:
				target.Resources.MergedDictionaries.Remove(to_remove)

	def toggle(self):
		"""Toggle between primary and secondary themes."""
		uri_list = [str(md.Source) for md in self._window_target.Resources.MergedDictionaries]

		# Toggling between themes
		if str(self.uri_primary) in uri_list:
			self._remove_theme(self.uri_primary)
			self._add_theme(self.uri_secondary)
			self.is_primary = False
		elif str(self.uri_secondary) in uri_list:
			self._remove_theme(self.uri_secondary)
			self._add_theme(self.uri_primary)
			self.is_primary = True
		else:
			# Apply default primary theme
			self._add_theme(self.uri_primary)
			self.is_primary = True

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