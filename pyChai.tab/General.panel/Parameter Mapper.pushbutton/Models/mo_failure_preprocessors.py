# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms, script
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback

from Autodesk.Revit.DB import IFailuresPreprocessor, FailureDefinition, FailureProcessingResult, FailureSeverity, BuiltInFailures

# ===============
# ---> CLASSES <---
class GroupEditPreProcessor(IFailuresPreprocessor):
	"""Remove group edit warnings during Revit transaction, and silently roll back when an Error-severity hits."""
	def PreprocessFailures(self, failuresAccessor):
		try:
			failures = failuresAccessor.GetFailureMessages()
			if len(failures) == 0:
				return FailureProcessingResult.Continue

			has_error = False
			for fls in failures:
				severity = fls.GetSeverity()
				if severity == FailureSeverity.Warning:
					failuresAccessor.DeleteWarning(fls)
				elif severity in (FailureSeverity.Error, FailureSeverity.DocumentCorruption):	# If Error-severity, then roll back the pending change.
					has_error = True

			# Cancels whatever changed since the start of sub-transaction. Caller must check Commit() status afterwards and treat non-Committed as "skipped".
			if has_error:
				return FailureProcessingResult.ProceedWithRollBack
			return FailureProcessingResult.Continue
		except:
			print(traceback.format_exc())
			return FailureProcessingResult.ProceedWithRollBack	# Fail safe - don't let an exception here leave a dialog hanging.