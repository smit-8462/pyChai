# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import os, io, re
from string import Template
from pyrevit import script

# ===============
# ---> CLASSES <---
class SysOutput_Markdown(object):
	def __init__(self, parent_script_file_path, markdown_template_file_list, template_variables_dict):
		# type: (str, list, dict) -> None
		"""
		Show output in Markdown format. It supports variables mapping in .md file. `.md` files must be in `Markdown` folder.
		For file path, use `os.path.abspath(__file__)` in the file where the script is imported.

		:param template_variables_dict: Absolute file path of parent scipt, where the class `SysOutput_Markdown` is imported.
		:type template_variables_dict: str
		:param markdown_template_file_list: List of Markdown template files
		:type markdown_template_file_list: list
		:param parent_script_file_path: Dictionary of variables in markdown files.
		:type parent_script_file_path: dict
		"""
		self._py_script_path = parent_script_file_path
		self._file_list = markdown_template_file_list
		self._template_variables_dict = template_variables_dict
		self._md_path_list = self._load_file()
	
	def _load_file(self):
		"""Load template file."""
		md_path = []
		cur_dir = os.path.dirname(self._py_script_path)
		goback_dir = os.path.abspath(os.path.join(cur_dir, ".."))  # Go back to previous directory
		template_folder = os.path.join(goback_dir, "Markdown")
		for mds in self._file_list:
			md_path.append(os.path.join(template_folder, mds))
		return md_path
	
	def _process_markdown_output(self, md_absolute_file_path):
		# type: (str) -> None
		"""
		Print the Markdown output from a template file, along with any variables defined in Markdown template.
	
		Example of template_variables:
			template_vars = {"project_name": "Hospital Phase 2",
							"user": "Lead Architect",
							"status": "Approved"}
	
		:param md_absolute_file_path: Markdown template file path
		:type md_absolute_file_path: str
		:param template_variables: Dictionary of variables defined in Markdown template
		:type template_variables: dict
		"""
		pyrevit_output = script.get_output()
		pyrevit_output.show()  # ensures the output window is visible/reopened
	
		# Encoding is not available in Python2.7 , therefore we are using "io".
		with io.open(md_absolute_file_path, "r", encoding="utf-8") as md_file:
			raw_markdown = md_file.read()
	
		# Using regex "re" to catch missing variables early instead of silently leaving ${var} in output.
		required_vars = set(re.findall(r"\$\{(\w+)\}", raw_markdown))
		missing_vars = required_vars - set(self._template_variables_dict.keys())
		if missing_vars:
			pyrevit_output.print_md("**Warning:** missing template variables: {}".format(", ".join(missing_vars)))
	
		# Replacing the variables defined inside markdown template file with the template_variables key's value
		formatted_markdown = Template(raw_markdown).safe_substitute(self._template_variables_dict)
		pyrevit_output.print_md(formatted_markdown)		# Print markdown output

	def show_error_output(self):
		# type: () -> None
		"""Show the error output in print window."""
		for fl in self._md_path_list:
			self._process_markdown_output(fl)