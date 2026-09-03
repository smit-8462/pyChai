# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms
# wpf can be imported only after pyrevit.forms
import wpf, os, traceback, clr, re

clr.AddReference("System")
clr.AddReference("PresentationCore")
from System.Windows import DataObject, DataObjectPastingEventArgs, DataFormats, BaselineAlignment
from System.Windows.Controls import RichTextBox, ContentPresenter
from System.Windows.Documents import Run, InlineUIContainer, TextRange, Paragraph
from System.Windows.Threading import DispatcherPriority
from System import Action

# ===============
# ---> VARIABLES <---
# Matches: |Param Name|<case:side:value> -> case/side/value may each be empty, e.g. |Param|<::>
_combined_token_pattern = re.compile(r'\|([^|]+)\|<([^:>]*):([^:>]*):([^:>]*)>')

# ===============
# ---> METHODS <---
def extract_richtextbox_contents(richtextbox):
	# type: (RichTextBox) -> str
	"""
	For extracting RichTextBox content to simple string text. \n
	Extract contents from RichTextBox in string form, expanding token chips (InlineUIContainer/ContentPresenter) back into 
	their |Token| or |Token|<case:side:value> text form.
	"""
	paragraphs_text = []

	for block in richtextbox.Document.Blocks:
		if not isinstance(block, Paragraph):
			continue
		parts = []
		for inline in block.Inlines:
			if isinstance(inline, Run):
				parts.append(inline.Text)
			elif isinstance(inline, InlineUIContainer):
				token_text = _extract_token_text(inline)
				if token_text is not None:
					parts.append(_format_token_text(token_text))
		paragraphs_text.append(u"".join(parts))

	full_text = u"\n".join(paragraphs_text)		# "u" is Unicode string literal
	return full_text if full_text.strip() else None

def _format_token_text(token_content):
	# type: (str) -> str
	"""
	Reconstruct the plain-text |token| form from a chip's stored Content string.
	- Simple tokens store just the param name (no pipes) -> "|Name|"
	- Combined tokens store "Name|case|side|value" (pipe_token_matcher_combined's inner format) -> "|Name|<case:side:value>"
	"""
	parts = token_content.split("|")
	if len(parts) == 4:
		name, case_choice, slicing_side, slicing_value = parts
		return u"|{}|<{}:{}:{}>".format(name, case_choice, slicing_side, slicing_value)
	return u"|{}|".format(token_content)

def _extract_token_text(inline_ui_container):
	# type: (InlineUIContainer) -> str | None
	"""Pull the token string back out of an InlineUIContainer's ContentPresenter."""
	child = inline_ui_container.Child
	if isinstance(child, ContentPresenter):
		content = child.Content
		return content if content is not None else None
	return None

def check_if_richtextbox_empty(rtb):
	# type: (RichTextBox) -> bool
	"""Check if RichTextBox is empty or not. Returns True if empty, False if text is present."""
	# Extract text from the start to the end of the FlowDocument
	text_range = TextRange(rtb.Document.ContentStart, rtb.Document.ContentEnd)
	extracted_text = text_range.Text.strip()
	return not bool(extracted_text)		# Returns True if empty, False if text is present

def pipe_token_matcher(text):
	# type: (str) -> tuple[str, str]|None
	"""
	Finds the 1st |Type Name| span anywhere in `text`. Used only by the bulk-sweep path (paste / programmatic set_text), 
	never per-keystroke, since live matching caused visible typing lag.

	:param text: Text object.
	:type text: str
	:return: Tuple (matched_span, e.g. "|Type Name|"), (inner text, e.g. "Type Name")
	:rtype: tuple[str, str]|None
	"""
	start = text.find("|")
	if start == -1:
		return None
	end = text.find("|", start + 1)
	if end == -1:
		return None
	inner = text[start + 1:end].strip()
	if not inner:
		return None
	return (text[start:end + 1], inner)


def pipe_token_matcher_combined(text):
	# type: (str) -> tuple[str, str]|None
	"""
	Finds a combined `|Param Name|<case:side:value>` span anywhere in `text`. Used only by `rtb_transform_text`'s TokenizingControl 
	(bulk-sweep path). Kept fully separate from `pipe_token_matcher` so the two token flavors never cross-match or share a style.

	:param text: Text object.
	:type text: str
	:return: Tuple (matched_span, e.g. "|Ceiling Height|<upper:left:4>"), (inner payload, pipe-delimited)
	:rtype: tuple[str, str]|None
	"""
	match = _combined_token_pattern.search(text)
	if match is None:
		return None
	matched_span = match.group(0)
	param_name = match.group(1).strip()
	case_choice = match.group(2)
	slicing_side = match.group(3)
	slicing_value = match.group(4)
	if not param_name:
		return None
	inner = u"{}|{}|{}|{}".format(param_name, case_choice or "", slicing_side or "", slicing_value or "")
	return (matched_span, inner)

# ===============
# ---> CLASSES <---
class Token_TextManipulation_Control(object):
	"""Class related to tokens for text manipulation."""
	def __init__(self):
		# Combined token: |Param Name|<case:side:value> - matched anywhere in the string, not anchored.
		self.pattern_combined = re.compile(r'\|([^|]+)\|<([^:>]*):([^:>]*):([^:>]*)>')
		# Simple token: |Param Name| - text between pipes, no pipe chars inside.
		self.pattern_simple = re.compile(r'\|([^|]+)\|')

	def extract_variables(self, richtextbox_text_string):
		# type: (str) -> tuple[list[tuple], set|None]
		"""
		Extract every token found in `richtextbox_text_string`, in two passes - 
			- 1st pass - combined tokens: `|Param Name|<case:side:value>`
			- 2nd pass - simple tokens: `|Param Name|` (leftover after 1st pass)

		Args:
			richtextbox_text_string (str): RichTextBox string

		Returns:
			list[tuple]: List of tuple having `(parameter_variable, text_case, slicing_side, slicing_value)`
			set : A set of extracted parameters. Used for comparing with existing parameter collection, 
				and for creating dictionary of parameter name as key, and  parameter value as value of dictionary.
		"""
		if not richtextbox_text_string:
			return [], None

		results = []
		params_extracted_set = set()

		# 1st pass - combined tokens
		combined_matches = list(self.pattern_combined.finditer(richtextbox_text_string))
		for match in combined_matches:
			parameter_variable = match.group(1).strip()
			text_case = match.group(2) or None
			slicing_side = match.group(3) or None
			slicing_value = match.group(4) or None
			if not parameter_variable:
				continue
			# `match.start()` ==> returns the integer index, the character position in the string, where that match begins.
			results.append((match.start(), (parameter_variable, text_case, slicing_side, slicing_value)))
			params_extracted_set.add(parameter_variable)

		# Replace the combined-token spans with " " blank temporarily (keeping string length/positions intact), 
		# so the simple-token pass below can never re-match a combined token's "|Name|" portion.
		remaining_text_chars = list(richtextbox_text_string)
		for match in combined_matches:
			for i in range(match.start(), match.end()):
				remaining_text_chars[i] = " "
		remaining_text = u"".join(remaining_text_chars)

		# 2nd pass - simple tokens
		for match in self.pattern_simple.finditer(remaining_text):
			parameter_variable = match.group(1).strip()
			if not parameter_variable:
				continue
			# `match.start()` ==> returns the integer index, the character position in the string, where that match begins.
			results.append((match.start(), (parameter_variable, None, None, None)))
			params_extracted_set.add(parameter_variable)

		# Sort by original position in the string so results come back in left-to-right order.
		results.sort(key=lambda item: item[0])
		return [item[1] for item in results], params_extracted_set		# return set, so that we can compare with existing set

	def text_case_helper(self, text_string, case_choice, slicing_side, slicing_value):
		# type: (str, str, str, int) -> str|None
		"""
		Helper method to manipulate the input text and return back the text string.

		Args:
			text_string (str): The text string input.
			case_choice (str): The choice of text case manipulation. Must be "lower", "upper" or "title".
			slicing_side (str): The side which should be used for slicing of text. Must be "left" or "right"
			slicing_value (int): The number of characters which should be kept while slicing.
				Coz the workflow demands keeping some number of characters of text. Must be an integer

		Returns:
			str: The manipulated text string.
		"""
		if text_string is None:
			return

		text_01 = text_string

		if slicing_side and slicing_value:
			# Step 1 - Keep only the required text characters.
			slicing_side = slicing_side.lower()
			slicing_value = int(slicing_value)
			if slicing_side == "left":
				text_01 = text_string[:slicing_value]
			elif slicing_side == "right":
				text_01 = text_string[-slicing_value:]
			else:
				text_01 = text_string

			# Step 2 - Change the text case, if requested.
			if case_choice:
				case_choice = case_choice.lower()
				if case_choice == "lower":
					text_01 = text_01.lower()
				elif case_choice == "upper":
					text_01 = text_01.upper()
				elif case_choice == "title":
					text_01 = text_01.title()

		elif case_choice:
			# Case change only, no slicing.
			case_choice = case_choice.lower()
			if case_choice == "lower":
				text_01 = text_string.lower()
			elif case_choice == "upper":
				text_01 = text_string.upper()
			elif case_choice == "title":
				text_01 = text_string.title()
		return text_01

	def substitute_tokens(self, richtextbox_text_string, substitute_dict):
		# type: (str, dict) -> str
		"""
		Replace every token in RichTextBox with appropriate parameter value with text manipulation.

		Args:
			richtextbox_text_string (str): Text containing |Param| and/or |Param|<case:side:value> tokens.
			substitute_dict (dict): Maps parameter_variable -> raw string value.

		Returns:
			str: Text with every recognized token replaced.
		"""
		if not richtextbox_text_string:
			return richtextbox_text_string

		# 1st pass - combined tokens
		def _replace_combined(match):
			parameter_variable = match.group(1).strip()
			text_case = match.group(2) or None
			slicing_side = match.group(3) or None
			slicing_value = match.group(4) or None

			# Just for protection, although we are detecting the availability of parameters beforehand,
			# by checking the extracted parameters set with parameters collection.
			if parameter_variable not in substitute_dict:
				raise KeyError(u"Unrecognized token '{}' - no matching entry in substitute_dict".format(parameter_variable))

			raw_value = substitute_dict[parameter_variable]
			return self.text_case_helper(raw_value, text_case, slicing_side, slicing_value)		# type: ignore

		# Running 1st pass, so that the remaining simple tokens can be kept.
		text_after_combined = self.pattern_combined.sub(_replace_combined, richtextbox_text_string)

		# 2nd pass - simple tokens
		def _replace_simple(match):
			parameter_variable = match.group(1).strip()
			if parameter_variable not in substitute_dict:
				raise KeyError(u"Unrecognized token '{}' - no matching entry in substitute_dict".format(parameter_variable))

			raw_value = substitute_dict[parameter_variable]
			return self.text_case_helper(raw_value, None, None, None) # type: ignore

		# Running 2nd pass
		text_after_simple = self.pattern_simple.sub(_replace_simple, text_after_combined)

		# Returning final substituted text
		return text_after_simple


class TokenizingControl(object):
	"""
	Create token from text in RichTextBox, wrapping it as a plain RichTextBox string text.
	Tokenizing only fires on paste (OnPaste) or programmatic insert (set_text) — never live while
	typing, since a per-keystroke regex pass caused visible lag.
	Source - https://blog.pixelingene.com/2010/10/tokenizing-control-convert-text-to-tokens

	:param richtextbox: A RichTextBox object.
	:type richtextbox: RichTextBox
	:param token_template_key: Assigning TokenTemplate control to ContentTemplate from XAML.
	:type token_template_key: str
	:param token_matcher: Method that scans a Run's text for a token span anywhere within it (not caret-relative). 
		Called only during the paste/bulk sweep.
	:type token_matcher: callable
	"""
	def __init__(self, richtextbox, matchers):
		# type: (RichTextBox, list[tuple[str, callable]]) -> None
		"""
		:param matchers: ordered list of (template_key, token_matcher) tuples. Put more specific patterns first (e.g. combined |Name|<c:s:v>)
		  - otherwise a general |..| matcher will partially match inside a combined span before the combined matcher gets a chance.
		"""
		super(TokenizingControl, self).__init__()
		self._rtb = richtextbox
		self._matchers = matchers

		# Intercept paste so we can tokenize the whole pasted string
		DataObject.AddPastingHandler(self._rtb, self.OnPaste)

	def OnPaste(self, sender, event):
		"""Inserts plain text, then `_tokenize_all_pending` sweeps the whole paragraph for token spans."""
		# type: (object, DataObjectPastingEventArgs) -> None
		if not event.DataObject.GetDataPresent(DataFormats.Text):
			return
		pasted_text = event.DataObject.GetData(DataFormats.Text)
		event.CancelCommand()          # stop default paste, we will insert it ourselves
		self._insert_plain_text_at_caret(pasted_text)

	def set_text(self, text, replace_existing=True, user_caret_position=None):
		# type: (str, bool, object) -> None
		"""
		Insert text into the RichTextBox, then run it through the same tokenizing sweep as a real paste.

		:param text: Plain text, optionally containing |token| spans, e.g. "Prefix_|Family Name|_Suffix".
		:type text: str
		:param replace_existing: If True, clears the whole document first, then insert text, else inserts at current caret position.
		:type replace_existing: bool
		:param user_caret_position: Optional TextPointer specifying exactly where to insert. If None, falls back to replace_existing logic or current CaretPosition.
		:type user_caret_position: TextPointer
		"""
		if text is None:
			return

		if replace_existing:
			self._rtb.Document.Blocks.Clear()
			self._rtb.Document.Blocks.Add(Paragraph())
			insert_position = self._rtb.Document.ContentEnd
		elif user_caret_position is not None:
			insert_position = user_caret_position
		else:
			insert_position = self._rtb.CaretPosition
		self._insert_plain_text_at_caret(text, insert_position)

	def _insert_plain_text_at_caret(self, text, insert_position=None):
		# type: (str, object) -> None
		"""Insert plain text at the given position (or current caret position), then defer a token sweep."""
		pos = insert_position if insert_position is not None else self._rtb.CaretPosition	# caret position
		pos.InsertTextInRun(text)
		self._rtb.CaretPosition = pos

		# Now sweep the paragraph and tokenize every |..| pair found, independent of caret.
		self._rtb.Dispatcher.BeginInvoke(DispatcherPriority.Background, Action(self._tokenize_all_pending))

	def _tokenize_all_pending(self):
		"""
		Repeatedly scan the current paragraph's Runs with `self.token_matcher` and convert matches, until a full pass finds 
		nothing left to tokenize. Safe to call after any bulk text insertion (paste, drag-drop, programmatic set_text), 
		since it re-scans the paragraph rather than relying on caret position.
		"""
		try:
			para = self._rtb.CaretPosition.Paragraph
			if para is None:
				return
			while True:
				found = False
				for inline in list(para.Inlines):  # snapshot - we mutate Inlines below
					if isinstance(inline, Run):
						for template_key, matcher in self._matchers:
							match = matcher(inline.Text)
							if match is not None:
								matched_span, token = match
								self._replace_run_span_with_token(para, inline, matched_span, token, template_key)
								found = True
								break
						if found:
							break
				if not found:
					break
			self._rtb.UpdateLayout()   # <-- force layout NOW, inside the try
		except Exception as e:
			print("Tokenizing sweep failed:\n\n{}\n\n{}".format(e, traceback.format_exc()))

	def _replace_run_span_with_token(self, para, run, matched_span, token, template_key):
		# type: (Paragraph, Run, str, str, str) -> None
		"""Split a single Run around matched_span and insert a token container in its place."""
		full_text = run.Text
		split_at = full_text.index(matched_span)
		head = full_text[:split_at]
		tail = full_text[split_at + len(matched_span):]

		container = self._create_token_container(token, template_key)

		if head:
			para.Inlines.InsertBefore(run, Run(head))
		para.Inlines.InsertBefore(run, container)
		if tail:
			para.Inlines.InsertAfter(run, Run(tail))
		para.Inlines.Remove(run)
		self._rtb.CaretPosition = container.ElementEnd		# land right after the token, not document end

	def _create_token_container(self, token, template_key):
		# type: (object, object) -> object
		"""Create a token container."""
		presenter = ContentPresenter()
		presenter.Content = token
		presenter.ContentTemplate = self._rtb.FindResource(template_key)		# Assigning TokenTemplate control to ContentTemplate from XAML.
		
		# BaselineAlignment=Center keeps the chip vertically centered against the surrounding text line.
		container = InlineUIContainer(presenter)
		container.BaselineAlignment = BaselineAlignment.Center
		return container