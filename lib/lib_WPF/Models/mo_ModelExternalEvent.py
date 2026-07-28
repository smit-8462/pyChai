# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback

from Autodesk.Revit.UI import TaskDialog, IExternalEventHandler

# ===============
# ---> VARIABLES <---

# ===============
# ---> HELPER CLASS <---
class BasicExEventHandler(IExternalEventHandler):
	def __init__(self, passable_method=None):
		super(BasicExEventHandler, self).__init__()
		self.passable_method = passable_method		# can be None initially, or reassigned later
		# optional callback(success: bool), set right before Raise()
		self.on_complete = None  # type: callable

	def Execute(self, uiapp):
		success = False
		try:
			if self.passable_method is not None:
				self.passable_method()
				success = True
		except Exception as e:
			try:
				print("An error occurred:\n\n{}\n\n{}".format(e, traceback.format_exc()))
				TaskDialog.Show("Failed", "Operation Failed")
			except Exception:
				pass  # Never let error-reporting itself crash the handler.
		finally:
			# Here, self.on_complete is the same object as self._on_apply_complete.
			# Calling self.on_complete(success) is functionally identical to calling
			# preview_window._on_apply_complete(success) directly - it is just reached indirectly through the variable.
			if self.on_complete is not None:
				try:
					self.on_complete(success)
				except Exception:
					pass  # Never let the completion callback itself crash the handler.

	def GetName(self):
		return "Basic External Event Handler"
