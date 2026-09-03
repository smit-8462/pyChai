# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import os
from pyrevit import ROOT_BIN_DIR
from pyrevit.userconfig import user_config

# ===============
# ---> CLASSES <---
class PyRevitConfigs(object):
	"""Create use configs for plugin-wide use."""
	SECTION_NAME = "pyChaiConfigs"
	OPTION_NAME_01 = "cpython_exe_location"
	OPTION_NAME_02 = "cpython_plugin_lib_location"
	OPTION_NAME_03 = "cpython_external_location"

	def __init__(self):
		self._cpy_location = None
		self._plugin_extension_location = None

	@property
	def plugin_extension_location(self):
		if not self._plugin_extension_location:
			self._plugin_extension_location = _get_extension_root_path()
		return self._plugin_extension_location

	@property
	def cpy_location(self):
		if not self._cpy_location:
			self._cpy_location = _get_cpy_location_from_ipy()
		return self._cpy_location

	def read_cpy_external_lib_location(self):
		"""Get the python3 external 'lib' location which will be used externally, from .ini configuration file."""
		path = self._read_property(self.OPTION_NAME_03)
		if not path:
			path = os.path.join(self.plugin_extension_location, "site-packages")
			self._add_property(self.OPTION_NAME_03, path)
		return path

	def read_cpy_plugin_lib_location(self):
		"""Get the pyChai plugin 'lib' location from .ini configuration file."""
		path = self._read_property(self.OPTION_NAME_02)
		if not path:
			path = os.path.join(self.plugin_extension_location, "lib")
			self._add_property(self.OPTION_NAME_02, path)
		return path

	def read_cpy_location(self):
		"""Get the pyRevit CPython engine .exe location from .ini configuration file."""
		path = self._read_property(self.OPTION_NAME_01)
		if not path:
			path = self.cpy_location
			self._add_property(self.OPTION_NAME_01, path)
		return path

	def _read_property(self, property_name):
		"""Read property which are stored in pyRevit .ini configuration file."""
		section = user_config.get_section(self.SECTION_NAME)
		return section.get_option(property_name, None)

	def _add_property(self, property_name, property_value):
		"""Add property to .ini file, only if it doesn't already exist."""
		if not user_config.has_section(self.SECTION_NAME):
			user_config.add_section(self.SECTION_NAME)
		section = user_config.get_section(self.SECTION_NAME)
		section.set_option(property_name, property_value)
		user_config.save_changes()

	def purge_all_properties(self):
		"""Remove all the pyChai section header and its properties from pyRevit .ini configuration files."""
		if user_config.has_section(self.SECTION_NAME):
			user_config.remove_section(self.SECTION_NAME)
			user_config.save_changes()


def _get_cpy_location_from_ipy():
	"""Get CPython engine location from IronPython process."""
	root_bin_directory = ROOT_BIN_DIR
	cengine_dir = os.path.join(root_bin_directory, "cengines")
	folders_list = os.listdir(cengine_dir)
	latest_folder = sorted(folders_list, reverse=True)[0]
	return os.path.join(cengine_dir, latest_folder, "python.exe")

def _get_extension_root_path():
	"""
	Get the extension root path.
	:return: Extension root path
	:rtype: str
	"""
	path = os.path.dirname(__file__)
	while not path.endswith(".extension"):
		path = os.path.dirname(path)
		if len(path) <= 3:  # "C:\"
			raise FileNotFoundError("Cannot find the extension root folder")
	return