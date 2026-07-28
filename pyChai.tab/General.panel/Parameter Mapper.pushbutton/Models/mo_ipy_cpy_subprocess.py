# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import os, json, subprocess
from collections import OrderedDict

from lib_System.sys_terminal import subprocess_script_output_pyrevit
from lib_System.sys_configs_manager import PyRevitConfigs

# ===============
# ---> CLASSES <---
class PySubprocess(object):
	"""A helper class for python subprocess."""
	def launch_pipeline_pyrevit(self, file_path, file_ext):
		"""
		Process the command terminal output further, to make it usable for further development.
		:param file_path: File path
		:type file_path: str
		:param file_ext: File extension
		:type file_ext: str
		:return: Dictionary containing spreadsheet rows and columns
		:rtype: dict
		"""
		# Reading properties from pyrevit .ini configuration file.
		pyrevit_configs = PyRevitConfigs()
		pyrevit_cpy_path = pyrevit_configs.read_cpy_location()
		plugin_lib_path = pyrevit_configs.read_cpy_plugin_lib_location()
		cpython_external_lib_path = pyrevit_configs.read_cpy_external_lib_location()
		cpy_script_path = self._get_script_file_location("mo_cpy_fileio_pyrevit.py")

		# Running python subprocess
		output_01, errors_01 = subprocess_script_output_pyrevit(cpy_script_path, pyrevit_cpy_path,
																args=[file_path,
																	  file_ext,
																	  plugin_lib_path,
																	  cpython_external_lib_path])
		if errors_01:
			print(errors_01)
			return None
		dict_val = json.loads(output_01, object_pairs_hook=OrderedDict)  # type: dict
		return dict_val

	@staticmethod
	def _get_script_file_location(file_name):
		"""
		The file should be in same folder.
		:param file_name: File name
		:type file_name: str
		"""
		current_script_dir = os.path.dirname(__file__)  # type: str
		return os.path.join(current_script_dir, file_name)