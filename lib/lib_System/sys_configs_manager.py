# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import os
from pyrevit.userconfig import user_config
from pyrevit import ROOT_BIN_DIR

# ===============
# ---> CLASSES <---
class PyRevitConfigs(object):
	"""Create use configs for plugin-wide use."""
	SECTION_NAME = 'pyChaiConfigs'
	OPTION_NAME_01 = 'cpython_exe_location'
	OPTION_NAME_02 = 'cpython_plugin_lib_location'
	OPTION_NAME_03 = 'cpython_external_location'

	def __init__(self):
		self._cpy_location = self._get_cpy_location_from_ipy()
		self._plugin_extension_location = self._get_extension_root_path()

	def read_cpy_external_lib_location(self):
		"""Get the python3 external 'lib' location which will be used externally, from .ini configuration file."""
		external_lib_location = os.path.join(self._plugin_extension_location, "site-packages")
		self._add_property(self.OPTION_NAME_03, external_lib_location)
		return self._read_property(self.OPTION_NAME_03, external_lib_location)

	def read_cpy_plugin_lib_location(self):
		"""Get the pyChai plugin 'lib' location from .ini configuration file."""
		plugin_lib_path = os.path.join(self._plugin_extension_location, "lib")
		self._add_property(self.OPTION_NAME_02, plugin_lib_path)
		return self._read_property(self.OPTION_NAME_02, plugin_lib_path)

	def read_cpy_location(self):
		"""Get the pyRevit CPython engine .exe location from .ini configuration file."""
		self._add_property(self.OPTION_NAME_01, self._cpy_location)
		return self._read_property(self.OPTION_NAME_01, self._cpy_location)

	def _read_property(self, property_name, property_value):
		"""Read property which are stored in pyRevit .ini configuration file."""
		section = user_config.get_section(self.SECTION_NAME)
		return section.get_option(property_name, property_value)

	def _add_property(self, property_name, property_value):
		"""Add property to .ini file, only if it doesn't already exist."""
		if not user_config.has_section(self.SECTION_NAME):
			user_config.add_section(self.SECTION_NAME)
		section = user_config.get_section(self.SECTION_NAME)
		if not section.has_option(property_name):
			section.set_option(property_name, property_value)
			user_config.save_changes()

	def purge_all_properties(self):
		"""Remove all the pyChai section header and its properties from pyRevit .ini configuration files."""
		if user_config.has_section(self.SECTION_NAME):
			user_config.remove_section(self.SECTION_NAME)
			user_config.save_changes()

	@staticmethod
	def _get_cpy_location_from_ipy():
		"""Get CPython engine location from IronPython process."""
		root_bin_directory = ROOT_BIN_DIR
		cengine_dir = os.path.join(root_bin_directory, "cengines")
		folders_list = os.listdir(cengine_dir)
		latest_folder = sorted(folders_list, reverse=True)[0]
		return os.path.join(cengine_dir, latest_folder, "python.exe")

	@staticmethod
	def _get_extension_root_path():
		"""
		Get the extension root path.
		:return: Extension root path
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
		return pychai_extension_folder