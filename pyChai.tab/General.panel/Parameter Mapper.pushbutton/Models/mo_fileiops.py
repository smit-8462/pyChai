# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import os
from pyrevit import script, forms

# ===============
# ---> METHODS <---
def load_file():
	"""
	Load the file and return it as a file path.
	:return: File path
	:rtype: str
	"""
	source_file = forms.pick_file(title="Select File",
								  multi_file=False,
								  files_filter=('Excel file (*.xlsx;*.xls;*.xlsm;*.xlsb)|*.xlsx;*.xls;*.xlsm;*.xlsb|'
												'CSV file (*.csv)|*.csv|'
												'LibreOffice Calc (*.ods)|*.ods'))
	return source_file