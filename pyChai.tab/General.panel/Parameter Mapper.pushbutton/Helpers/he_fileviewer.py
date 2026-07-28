# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import os

# ===============
# ---> METHODS <---
def shorten_path(file_path):
	"""
	Shortens the file path, if the path is greater than 50 characters.
	:param file_path: File path
	:type file_path: str
	:return: Shortened file path
	:rtype: str
	"""
	max_chars = 50
	if len(file_path) <= max_chars:
		return file_path

	parts = file_path.split("\\")
	return "...\\" + parts[-2] + "\\" + parts[-1]