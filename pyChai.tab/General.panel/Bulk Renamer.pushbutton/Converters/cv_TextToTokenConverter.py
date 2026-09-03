# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import clr, re
clr.AddReference("PresentationFramework")
clr.AddReference("System")
from System.Windows.Data import IValueConverter
from System.Collections.ObjectModel import ObservableCollection

# ===============
# ---> VARIABLES <---
# Mirrors _combined_token_pattern in mo_tokenizing_control.py. We are not importing into it, to avoid circular import dependency.
_combined_pattern = re.compile(r'\|([^|]+)\|<([^:>]*):([^:>]*):([^:>]*)>')

# ===============
# ---> CLASSES <---
class Segment(object):
	"""
	A single piece of a rename-pattern string.
	- Plain text:      Segment("Hello ", False, False)
	- Simple token:    Segment("How", True, False)
	- Combined token:  Segment("Category|title|left|2", True, True) - pipe-delimited payload shape TokenTagCombined/CombinedTokenPartConverter expect.

	:param is_combined: True only for combined tokens, so XAML can switch between the TokenTag and TokenTagCombined styles via a DataTrigger.
	"""
	def __init__(self, text, is_token, is_combined=False):
		self.Text = text
		self.IsToken = is_token
		self.IsCombined = is_combined

class StringToSegmentsConverter(IValueConverter):
	"""
	Splits a plain string containing |token| and |token|<case:side:value> spans into an ObservableCollection 
	of `Segment` objects, so a nested ItemsControl inside ListBox.ItemTemplate can render plain text and 
	token chips inline, the same way TokenizingControl renders chips in a RichTextBox.

	Usage in XAML:
		ItemsSource="{Binding Converter={StaticResource StringToSegmentsConverter}}"
	"""
	def Convert(self, value, targetType, parameter, culture):
		segments = ObservableCollection[object]()
		if not value:
			return segments

		text = value
		pos = 0
		length = len(text)
		while pos < length:
			# Try combined token first at this position - otherwise simple scan below would grab "|Category|" and leave "<title:left:2>" stranded as plain text.
			combined_match = _combined_pattern.match(text, pos)
			if combined_match:
				name = combined_match.group(1).strip()
				case_choice, slicing_side, slicing_value = combined_match.group(2), combined_match.group(3), combined_match.group(4)
				if name:
					payload = u"{}|{}|{}|{}".format(name, case_choice or "", slicing_side or "", slicing_value or "")
					segments.Add(Segment(payload, True, True))
				pos = combined_match.end()
				continue

			start = text.find("|", pos)
			if start == -1:
				# No more pipes - remainder is plain text
				segments.Add(Segment(text[pos:], False))
				break

			if start > pos:				
				# Plain text before the pipe. Re-check for a combined token starting exactly at `start`, 
				# since the loop-top check above only ran at the old `pos` (before this plain text) and 
				# would otherwise miss a combined token that comes right after some plain text, 
				# e.g. "|Type Name|-|Category|<title:left:2>".
				segments.Add(Segment(text[pos:start], False))
				combined_match = _combined_pattern.match(text, start)
				if combined_match:
					name = combined_match.group(1).strip()
					case_choice, slicing_side, slicing_value = combined_match.group(2), combined_match.group(3), combined_match.group(4)
					if name:
						payload = u"{}|{}|{}|{}".format(name, case_choice or "", slicing_side or "", slicing_value or "")
						segments.Add(Segment(payload, True, True))
					pos = combined_match.end()
					continue

			end = text.find("|", start + 1)
			if end == -1:
				# Unmatched trailing pipe - treat rest as plain text (including the pipe itself)
				segments.Add(Segment(text[start:], False))
				break

			token = text[start + 1:end].strip()
			if token:
				segments.Add(Segment(token, True, False))
			# else: empty "||" - just skip it, nothing meaningful to render
			pos = end + 1
		return segments

	def ConvertBack(self, value, targetType, parameter, culture):
		raise NotImplementedError("StringToSegmentsConverter is one-way only.")