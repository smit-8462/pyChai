# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import clr
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
from System.Windows import Visibility
from System.Windows.Data import IValueConverter

# ===============
# ---> VARIABLES <---
_CASE_ABBREV = {"title": "Tt", "upper": "UP", "lower": "lw"}
_SIDE_ABBREV = {"left": "L", "right": "R"}

# ===============
# ---> CLASSES <---
class CombinedTokenPartConverter(IValueConverter):
	"""
	Splits the pipe-delimited combined-token content string - "Param Name|case|side|value"
	(as produced by `pipe_token_matcher_combined` in mo_tokenizing_control.py) - into the
	individual display parts used by the `TokenTagCombined` Label template.
	"""
	def Convert(self, value, targetType, parameter, culture):
		if not value:
			return "" if parameter != "HasTransform" else Visibility.Collapsed

		parts = str(value).split("|")
		while len(parts) < 4:		# defensive padding, in case content is malformed
			parts.append("")
		param_name, case_choice, slicing_side, slicing_value = parts[0], parts[1], parts[2], parts[3]

		part_key = str(parameter) if parameter else ""
		if part_key == "Name":
			return param_name
		elif part_key == "Case":
			return _CASE_ABBREV.get(case_choice.lower(), "") if case_choice else ""
		elif part_key == "Side":
			return _SIDE_ABBREV.get(slicing_side.lower(), "") if slicing_side else ""
		elif part_key == "Value":
			return slicing_value if slicing_value and slicing_value != "0" else ""
		elif part_key == "HasSideAndValue":		# Side and Value are shown as a pair - both or neither.
			has_side = bool(slicing_side)
			has_value = bool(slicing_value) and slicing_value != "0"
			return Visibility.Visible if (has_side and has_value) else Visibility.Collapsed
		elif part_key == "HasTransform":		# Hide the right-hand pill unless there's a Case, or a complete Side+Value pair.
			has_case = bool(case_choice)
			has_side_and_value = bool(slicing_side) and bool(slicing_value) and slicing_value != "0"
			has_data = has_case or has_side_and_value
			return Visibility.Visible if has_data else Visibility.Collapsed
		return ""

	def ConvertBack(self, value, targetType, parameter, culture):
		raise NotImplementedError("CombinedTokenPartConverter is one-way only.")