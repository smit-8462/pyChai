# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
import os, sys, traceback

from Models.mo_tokenizing_control import pipe_token_matcher

# ===============
# ---> VARIABLES <---

# ===============
# ---> CLASSES <---
class TemplateIOPS(object):
	"""Class related to Template operations."""
	def __init__(self, main_information_vm):
		self._imported_txt_file_path = None		# type: str
		self._main_information_vm = main_information_vm

	def template_import(self):
		"""Import templates from `.txt` file, returning a list of valid templates."""
		try:
			import_file_path = forms.pick_file(title="Select File", multi_file=False, file_ext='txt')
		except Exception:
			return None
		if not import_file_path: 
			return None
		self._imported_txt_file_path = import_file_path		# So that reload function can access file path.
		self._main_information_vm.TemplateImportFilePath = import_file_path

		valid_templates = self._populate_templates(import_file_path)
		return valid_templates

	def template_reload(self):
		"""Reload existing loaded template file from path."""
		if self._imported_txt_file_path:
			valid_templates = self._populate_templates(self._imported_txt_file_path)
			return valid_templates

	def template_export(self, richtextbox_str_text):
		"""Export the RichTextBox string text."""
		opt_append = "Append template in loaded file"
		opt_new_file  = "Save template in new file"
		opt_cancel = "Cancel"

		opt = [opt_new_file , opt_cancel]
		if self._imported_txt_file_path:
			msg_00 = "Template file\n{}\n".format(self._imported_txt_file_path)
			opt.insert(0, opt_append)
		else:
			msg_00 = ""

		msg_01 = "{} Select from following options - ".format(msg_00)
		res = forms.alert(msg_01, title="Save template", options=opt)

		if res == opt_new_file:
			already_imported_file_dir = os.path.dirname(self._imported_txt_file_path) if self._imported_txt_file_path else None
			save_file_path = forms.save_file(file_ext='txt', 
							  init_dir=already_imported_file_dir, 
							  default_name='Template 1', 
							  restore_dir=True, 
							  title='Save template file')
			if not save_file_path:
				return

			# Check if the string already exists as a line in the target file (if it exists)
			if os.path.exists(save_file_path):
				with open(save_file_path, "rt") as check_file:
					existing_lines = [ln.rstrip("\n").rstrip("\r") for ln in check_file]
				if richtextbox_str_text in existing_lines:
					return
			
			with open(save_file_path, "w") as text_file:
				text_file.write(richtextbox_str_text)
		elif res == opt_append and self._imported_txt_file_path:
			with open(self._imported_txt_file_path, "a") as text_file:
				new_str = "{}\n".format(richtextbox_str_text)
				text_file.write(new_str)
		else:
			return

	# ---------------------
	# Helper methods
	def _line_has_token(self, line):
		# type: (str) -> bool
		"""Return True if line contains at least one |token| span, reusing pipe_token_matcher."""
		for i, ch in enumerate(line):
			if ch == "|":
				result = pipe_token_matcher(line[:i + 1])
				if result is not None:
					return True
		return False

	def _populate_templates(self, txt_file_path):
		"""Populate templates."""
		valid_templates = []
		try:
			with open(txt_file_path, "rt") as file:
				for ln in file:
					line = ln.rstrip("\n").rstrip("\r")
					if self._line_has_token(line):
						valid_templates.append(line)
		except Exception as e:
			print("Failed to generate preview:\n\n{}\n\n{}".format(e, traceback.format_exc()))
			return None
		return valid_templates

	def check_if_exist(self):
		"""Check if template exists in file before appending."""
		pass