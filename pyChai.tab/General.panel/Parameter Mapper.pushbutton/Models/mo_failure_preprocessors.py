# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms, script
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback

from Autodesk.Revit.DB import IFailuresPreprocessor, FailureDefinition, FailureProcessingResult, FailureSeverity, BuiltInFailures

# ===============
# ---> VARIABLES <---

# ===============
# ---> CLASSES <---
class GroupEditPreProcessor(IFailuresPreprocessor):
	"""
	Remove group edit warnings during Revit transaction.
	"""
	def PreprocessFailures(self, failuresAccessor):
		try:
			failures = failuresAccessor.GetFailureMessages()
			if failures.Count == 0:
				return FailureProcessingResult.Continue
			
			transac_name = failuresAccessor.GetTransactionName()
			if transac_name == "Setting Multiple Parameters":
				for fls in failures:
					fail_id = fls.GetFailureDefinitionId()
					severity = fls.GetSeverity()
					description = fls.GetDescriptionText()
					if severity == FailureSeverity.Warning:
						failuresAccessor.DeleteWarning(fls)		# Removing warnings from list
				return FailureProcessingResult.Continue
		except:
			print(traceback.format_exc())
			return FailureProcessingResult.Continue
