# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import clr

clr.AddReference("System")
from System.Diagnostics import ProcessStartInfo, Process

from lib_WPF.Models.mo_website import WebsiteModel

# ===============
# ---> CLASSES <---
class WindowBottomBarViewModel:
	def __init__(self):
		self._model = WebsiteModel()

	def visit_website(self):
		"""Opening the website in default browser."""
		psi = ProcessStartInfo()
		psi.FileName = self._model.linkedin_profile
		psi.UseShellExecute = True
		Process.Start(psi)