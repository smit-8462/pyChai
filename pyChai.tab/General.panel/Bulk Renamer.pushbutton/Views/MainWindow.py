# -*- coding: utf-8 -*-
# ---> IMPORTS <---
from pyrevit import forms, script
# wpf can be imported only after pyrevit.forms
import wpf, os, clr, traceback

clr.AddReference("System")
clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
from System.Windows.Controls import Control as WpfControl
from System.Windows import Visibility, RoutedEvent, WindowState
from System.Windows.Input import MouseWheelEventArgs

from Autodesk.Revit.UI import ExternalEvent, TaskDialog

from Converters.cv_HeaderToIconConverter import HeaderToIconConverter
from Converters.cv_TextToTokenConverter import StringToSegmentsConverter
from Converters.cv_ButtonToCheckedConverter import StringEqualsConverter, ObjectReferenceEqualsConverter
from Converters.cv_CombinedTokenPartConverter import CombinedTokenPartConverter

# Import from shared libs
from lib_WPF.ViewModels.vm_WindowBottomBarViewModel import WindowBottomBarViewModel

from lib_WPF.Helpers.he_View_WindowBase import WindowBase
from lib_WPF.Helpers.he_resdict_manager import ResDictManager
from lib_WPF.Helpers.he_userControlManager import UserControlManager
from lib_WPF.Helpers.he_theme_manager import ThemeManager

from lib_WPF.Models.mo_ModelExternalEvent import BasicExEventHandler

from ViewModels.vm_MainWindow_ViewModel import MainWindowViewModel

from Views.SingleChoiceWindow import SingleChoiceWindow

from Models.mo_tokenizing_control import TokenizingControl, pipe_token_matcher, pipe_token_matcher_combined

# ===============
# ---> VARIABLES <---
PATH_SCRIPT = os.path.dirname(__file__)    # type: str
RES_LIST = ["resourceDict_General.xaml", "Themes/Theme_Light.xaml", "Themes/Theme_Dark.xaml",
			"resourceDict_ComboBox.xaml", "resourceDict_Choices.xaml", "resourceDict_DataGrid.xaml",
			"resourceDict_TreeView.xaml"]

# ===============
# ---> MAIN CLASS <---
class MainWindow(WindowBase):
	def __init__(self):
		super(MainWindow, self).__init__()

		# To avoid modifying inside Revit API directly (unsafe), we use External Events (official way).
		# The External Event is created only once, at the starting of script.
		self.ext_event_handler = BasicExEventHandler()
		self.ext_event = ExternalEvent.Create(self.ext_event_handler)

		# ViewModel initialise once
		self.vm_windowBottomBar = WindowBottomBarViewModel()
		self.vm_mainWindow = MainWindowViewModel(self.ext_event, self.ext_event_handler)

		self._is_loaded = False		# To check whether the `Loaded` event is loaded or not.

		# Track last caret position before focus leaves the RichTextBox (e.g. clicking a token button)
		self._last_caret_position = None

		# Data Context
		self.DataContext = self.vm_mainWindow

		# Register converters BEFORE loading any resource dictionaries, since resourceDict_General.xaml (TokenTagCombined style) 
		# resolves StaticResource converters at dictionary-load time, not at first bind.
		self.Resources["HeaderToIconConverter"] = HeaderToIconConverter()
		self.Resources["StringEqualsConverter"] = StringEqualsConverter()
		self.Resources["CombinedTokenPartConverter"] = CombinedTokenPartConverter()
		self.Resources["StringToSegmentsConverter"] = StringToSegmentsConverter()
		self.Resources["ObjectReferenceEqualsConverter"] = ObjectReferenceEqualsConverter()

		# Load Resource Dictionary files
		res_manager = ResDictManager(True)
		res_manager.apply_to(self, RES_LIST)  # Now, it populates shared list
		
		# Connect to .XAML file in the same folder
		xml_file_path = os.path.join(PATH_SCRIPT, 'MainWindow.xaml')
		wpf.LoadComponent(self, xml_file_path)

		# Load tokenizing text box (simple |Param| tokens) — paste/bulk-insert only, no live typing.
		# Simple |Param| tokens and finished combined |Param|<case:side:value> tokens land here.
		# Combined must be tried first - otherwise the simple matcher grabs "|Param|" and leaves "<...>" as plain text.
		self.rename_tokenizer = TokenizingControl(self.tbx_rename_box, 
											[("TokenTemplateCombined", pipe_token_matcher_combined), ("TokenTemplate", pipe_token_matcher),])

		# Plain |Param| preview only, before case/slice is attached.
		self.transform_tokenizer = TokenizingControl(self.rtb_transform_text, 
											   [("TokenTemplate", pipe_token_matcher)])

		# Tracks which RichTextBox should receive the next Parameter button click.
		self._active_richtextbox = "tbx_rename_box"		# default, matches existing behavior
		self._last_caret_position_rename = None
		self._last_caret_position_transform = None

		# All the UserControls wirings are handled here. Attaching to the existing main window
		self.usercontrol_manager = UserControlManager(self, title="pyChai - Bulk Renamer")
		extra_targets_usercontrols = [self.usercontrol_manager.top_bar, self.usercontrol_manager.bottom_bar]
		self.theme_manager = ThemeManager(self,
										  "Theme_Light.xaml",
										  "Theme_Dark.xaml",
										  extra_targets_usercontrols, use_lib_resources=True)

		# Dictionary for changing the selection RadioButton group, along with choosing "Both" button as default
		self._choice_panel_dict = {
			"combo_pick_family_type": ("Pick_FamilyType", "Choice_FamilyType_Both"),
			"combo_pick_view": ("Pick_View", "Choice_View_Both"),
			"combo_pick_sheet": ("Pick_Sheet", "Choice_Sheet_Both"),
			"combo_pick_level": ("Pick_Level", "Choice_Level_Both"),
		}

		# Initialize the tree at the launch of window
		self.Loaded += self.OnLoaded

		# Subscribing at the closing event of Window
		self.Closing += self.OnMainWindowClosing  # Event is disposed only when the whole tool closes.

	# ===============
	# ---> EVENTS <---
	# General window events (applicable to all windows)
	def ButtonEvent_Window_Minimize(self, sender, event):
		self.minimize_window()

	def ButtonEvent_Window_Resize(self, sender, event):
		self.toggle_fullscreen()

	def ButtonEvent_Window_Close(self, sender, event):
		self.close_window()

	def ButtonEvent_Window_Theme(self, sender, event):
		self.theme_manager.toggle()

	def ButtonEvent_Window_VisitProfile(self, sender, event):
		self.vm_windowBottomBar.visit_website()

	# ********************************
	# Top Event
	def ComboBoxEvent_ToolPick_SelectionChanged(self, sender, event):
		"""Event triggered after changed in selection."""
		if not self._is_loaded: return 		# ignore selection changes fired during XAML parsing
		selected_item = sender.SelectedItem
		if selected_item is not None:
			self._update_visibility(selected_item.Tag)
		self._reset_extended()		# Reset back to default

	# ********************************
	# Tree View
	def ButtonEvent_TreeViewer_Invert(self, sender, event):
		self.vm_mainWindow.TreeViewerVM.tree_selection_invert()
	
	def ButtonEvent_TreeViewer_SelectAll(self, sender, event):
		self.vm_mainWindow.TreeViewerVM.tree_selection_all()

	def ButtonEvent_TreeViewer_ClearAll(self, sender, event):
		self.vm_mainWindow.TreeViewerVM.tree_selection_clear()

	def TextBoxEvent_TreeView_Searchbox_TextChanged(self, sender, event):
		self.vm_mainWindow.TreeViewerVM.tree_search_filter_changed(sender.Text)

	def ButtonEvent_TreeViewer_Refresh(self, sender, event):
		self.vm_mainWindow.TreeViewerVM.tree_refresh_from_source()

	def ButtonEvent_TreeViewer_ExpandAllItems(self, sender, event):
		self.vm_mainWindow.TreeViewerVM.tree_search_expand_all_items()

	def ButtonEvent_TreeViewer_CollapseAllItems(self, sender, event):
		self.vm_mainWindow.TreeViewerVM.tree_search_collapse_all_items()

	def ButtonEvent_TreeViewer_ClearSearch(self, sender, event):
		self.vm_mainWindow.TreeViewerVM.tree_search_clear_input()
		self.TreeView_Searchbox.Text = ""		# triggers TextChanged -> filter reset automatically

	def ButtonEvent_TreeViewer_Next(self, sender, event):
		self.vm_mainWindow.InformationVM.make_parameter_button_set()

	# ********************************
	# Information
	def ButtonEvent_Information_TemplateReload(self, sender, event):
		self.vm_mainWindow.InformationVM.template_reload()

	def ButtonEvent_Information_LoadTemplate(self, sender, event):
		self.vm_mainWindow.InformationVM.template_import()

	def ButtonEvent_Information_SaveTemplate(self, sender, event):
		self.vm_mainWindow.InformationVM.template_export(self.tbx_rename_box)

	def ButtonEvent_Information_PickTemplate(self, sender, event):
		try:
			single_choice_window = SingleChoiceWindow(self, self.vm_mainWindow, self.tbx_rename_box)
			single_choice_window.ShowDialog()
		except Exception as e:
			print("Failed to generate preview:\n\n{}\n\n{}".format(e, traceback.format_exc()))

	def ButtonEvent_Information_ShowError(self, sender, event):
		self.vm_mainWindow.InformationVM.error_output_show()

	def ButtonEvent_Information_TextBoxApply(self, sender, event):
		try:
			self.vm_mainWindow.RenamerListVM.populate_data_in_groups(self.tbx_rename_box)
		except Exception as e:
			print("Failed to generate preview:\n\n{}\n\n{}".format(e, traceback.format_exc()))
	
	def ButtonEvent_Information_TextBoxClear(self, sender, event):
		self._clear_richtextbox_main()

	def ButtonEvent_Information_TextBoxCancel(self, sender, event):
		self._reset_tree_selection()

	def ButtonEvent_Information_UpdateCancel(self, sender, event):
		self.vm_mainWindow.InformationVM.release_template_edit()
		self._clear_richtextbox_main()

	def ButtonEvent_Information_Update(self, sender, event):
		try:
			info_vm = self.vm_mainWindow.InformationVM
			group_data = info_vm.EditingTemplate
			if group_data is None: return
			success = self.vm_mainWindow.RenamerListVM.update_template_group(group_data, self.tbx_rename_box)
			if success:
				info_vm.release_template_edit()
				self._clear_richtextbox_main()
		except Exception as e:
			print("Failed to update template:\n\n{}\n\n{}".format(e, traceback.format_exc()))
			
	def ButtonEvent_Parameter_InsertText(self, sender, event):
		"""Event for inserting text based on name of Button. Routes to whichever RichTextBox the caret was last in."""
		try:
			button_text = sender.Content		# Here, 'sender' is the button ,i.e, the control which fired the event.
			token_text = "|{}|".format(button_text)
			# Prefer the live CaretPosition first (correct even mid-typing, no click/focus-change needed).
			# Only fall back to the cached position if the live one is somehow invalid.
			if self._active_richtextbox == "rtb_transform_text":
				custom_caret_position = self.rtb_transform_text.CaretPosition
				try:
					_ = custom_caret_position.Paragraph
				except Exception:
					custom_caret_position = self._last_caret_position_transform or self.rtb_transform_text.CaretPosition
				self.transform_tokenizer.set_text(token_text, replace_existing=True, user_caret_position=custom_caret_position)
			else:
				custom_caret_position = self.tbx_rename_box.CaretPosition
				try:
					_ = custom_caret_position.Paragraph
				except Exception:
					custom_caret_position = self._last_caret_position_rename or self.tbx_rename_box.CaretPosition
				self.rename_tokenizer.set_text(token_text, replace_existing=False, user_caret_position=custom_caret_position)
		except Exception as e:
			print("Failed to generate preview:\n\n{}\n\n{}".format(e, traceback.format_exc()))

	def RichTextBoxEvent_LostFocus(self, sender, event):
		"""Cache caret position before focus moves elsewhere (e.g. to a parameter button)."""
		self._last_caret_position_rename = self.tbx_rename_box.CaretPosition
	
	def RichTextBoxEvent_RenameBox_GotFocus(self, sender, event):
		self._active_richtextbox = "tbx_rename_box"

	def RichTextBoxEvent_TransformBox_GotFocus(self, sender, event):
		self._active_richtextbox = "rtb_transform_text"

	def RichTextBoxEvent_TransformBox_LostFocus(self, sender, event):
		self._last_caret_position_transform = self.rtb_transform_text.CaretPosition

	def RichTextBoxEvent_RenameBox_PreviewMouseUp(self, sender, event):
		"""Cache caret position immediately after every real click inside the box - more reliable than LostFocus."""
		self._last_caret_position_rename = self.tbx_rename_box.CaretPosition

	def RichTextBoxEvent_TransformBox_PreviewMouseUp(self, sender, event):
		self._last_caret_position_transform = self.rtb_transform_text.CaretPosition

	def ButtonEvent_Number_Increment(self, sender, event):
		"""Increment number in textbox."""
		if self.vm_mainWindow.InformationVM.SlicingValue >= 0:
			self.vm_mainWindow.InformationVM.SlicingValue += 1

	def ButtonEvent_Number_Decrement(self, sender, event):
		"""Decrement number in textbox."""
		if self.vm_mainWindow.InformationVM.SlicingValue > 0:
			self.vm_mainWindow.InformationVM.SlicingValue -= 1

	def ButtonEvent_Information_TextTransformClear(self, sender, event):
		"""Clear all text transform done."""
		self._reset_all_text_transformation()

	def ButtonEvent_Information_TextTransformApply(self, sender, event):
		"""Apply parameter with text transform."""
		try:
			token_text = self.vm_mainWindow.InformationVM._add_text_transform_token_text(self.rtb_transform_text)
			if not token_text: return

			# Check if either of text manipulation option is selected. If not, then it will not be considered.
			info_vm = self.vm_mainWindow.InformationVM
			if not (info_vm.TextCase or info_vm.SlicingSide or info_vm.SlicingValue):
				return
			elif bool(info_vm.SlicingSide) != bool(info_vm.SlicingValue):
				missing_message = "Slicing value not found." if info_vm.SlicingSide else "Slicing side not selected."
				TaskDialog.Show("Missing data", missing_message)
				return

			insert_position = self._last_caret_position_rename or self.tbx_rename_box.CaretPosition
			# Prefer the live CaretPosition first - this is what stays correct while the user is
			# continuously typing (no click / focus-change needed to refresh it). Only fall back to
			# the cached position (populated on LostFocus / PreviewMouseUp) if the live one is invalid.
			insert_position = self.tbx_rename_box.CaretPosition
			try:
				_ = insert_position.Paragraph   # cheap validity probe, just for checking
			except Exception:
				insert_position = self._last_caret_position_rename or self.tbx_rename_box.CaretPosition
			self.rename_tokenizer.set_text(token_text, replace_existing=False, user_caret_position=insert_position)
			self._reset_all_text_transformation()
		except Exception as e:
			print("Failed to load template into RichTextBox:\n\n{}\n\n{}".format(e, traceback.format_exc()))
	
	# ********************************
	# List View
	def ButtonEvent_ListPreview_Reset(self, sender, event):
		"""Reset the Precheck Renamer list - clear all template groups and give their tree items back for reselection."""
		self.vm_mainWindow.reset_renamer_list()
		self._clear_richtextbox_main()		# avoid leaving stale/half-edited text behind after the groups it referred to are gone
	
	def ButtonEvent_ListPreview_Close(self, sender, event):
		self.close_window()

	def ButtonEvent_ListPreview_Apply(self, sender, event):
		self.pakka_apply_values()

	def ButtonEvent_ExpanderHeader_LoadTemplate(self, sender, event):
		"""Toggle the Update/Cancel 'hold' state for this row, loading its text into the Rename box."""
		try:
			group_data = sender.DataContext		# type: GroupData_Renamer
			if group_data is None: return
			info_vm = self.vm_mainWindow.InformationVM
			if sender.IsChecked:
				info_vm.EditingTemplate = group_data		# store the object, not just TemplateName
				self.rename_tokenizer.set_text(group_data.TemplateName, replace_existing=True)
			else:
				if info_vm.EditingTemplate is group_data:
					info_vm.release_template_edit()
		except Exception as e:
			print("Failed to load template into RichTextBox:\n\n{}\n\n{}".format(e, traceback.format_exc()))

	def ButtonEvent_ListItem_ShowError(self, sender, event):
		"""Show error of list item."""
		self._print_error_outputs(sender)

	def ListViewEvent_PreviewMouseWheel(self, sender, event):
		"""
		Forward mouse wheel scroll from inner ListView to the outer ScrollViewer, since the ListView's own 
		internal ScrollViewer (no scrollbars) otherwise swallows the event without bubbling it up.
		"""
		if not event.Handled:
			event.Handled = True
			new_event = MouseWheelEventArgs(event.MouseDevice, event.Timestamp, event.Delta)
			new_event.RoutedEvent = WpfControl.MouseWheelEvent
			self.list_scrollview.RaiseEvent(new_event)
			
	# ===============
	# ---> METHODS <---	
	def OnMainWindowClosing(self, sender, event):
		"""Disposing events after closing of window."""
		if self.ext_event is not None:
			self.ext_event.Dispose()
			self.ext_event = None
			self.ext_event_handler = None

	def OnLoaded(self, sender, event):
		"""Event triggering based on choices selected in ComboBox."""
		self._is_loaded = True
		self._update_visibility(self.PickChoiceComboBox.SelectedValue)		# set initial panel visibility
		# Reset tree first, then proceed further
		self._reset_tree_selection()
		self.Choice_FamilyType_Both.IsChecked = True
		self.vm_mainWindow.TreeViewerVM.SelectedClass.familytype_select_both()

	# Helper methods
	# ----------------------------------
	def _reset_all_text_transformation(self):
		self._clear_richtextbox_readonly()
		self.vm_mainWindow.InformationVM.reset_text_manip()

	def _clear_richtextbox_main(self):
		"""Clear main RichTextBox."""
		self.tbx_rename_box.Document.Blocks.Clear()
		self._last_caret_position_rename = None

	def _clear_richtextbox_readonly(self):
		"""Clear read-only RichTextBox."""
		self.rtb_transform_text.Document.Blocks.Clear()
		self._last_caret_position_transform = None

	def _reset_tree_selection(self):
		self._clear_richtextbox_main()		# Clear RichTextBox (since rich text box element is easily accessible in View of MVVM).
		self.vm_mainWindow.cancel_all_process()						# Rest of cancelling process

	def _reset_extended(self):
		self.vm_mainWindow.reset_renamer_list()
		self._clear_richtextbox_main()		# Clear RichTextBox (since rich text box element is easily accessible in View of MVVM).
		self.vm_mainWindow.cancel_when_combobox_switch()

	def _update_visibility(self, combobox_item_tag):
		"""Update the visibility based on ComboBox selected choice."""
		for key, tuple_value in self._choice_panel_dict.items():
			panel = getattr(self, tuple_value[0], None)		# get the real XAML element. It will be shown as self.panel_name, else
			both_button = getattr(self, tuple_value[1])
			if panel is not None:
				panel.Visibility = (Visibility.Visible if key == combobox_item_tag else Visibility.Collapsed)
				both_button.IsChecked = (True if key == combobox_item_tag else False)

	def _print_error_outputs(self, sender):
		"""
		In this, we are accessing individual error report of an item in listview.
		"""
		group_data = sender.DataContext		# type: GroupData_Renamer
		if group_data is None: return
		error_list = group_data.TemplateErrorList		# list[(old_name, error_message)]
		if not error_list: return

		# Build table
		output = script.get_output()
		table_data_build = [[idx + 1, old_name, error_message] for idx, (old_name, error_message) in enumerate(error_list)]		# Building data
		output.print_html_table(table_data=table_data_build, 
		                        title="The following items failed - ", 
								columns=["S. No.", "Existing Type Name", "Error"], 
								formats=['', '', ''], 
								column_head_align_styles=["center", "left", "left"], 
								column_data_align_styles=["center", "left", "left"], 
								table_width_style="100%", 
								row_striping=True)

	def pakka_apply_values(self):
		try:
			# self._on_apply_complete has no parentheses. This doesn't call the method, it passes the method itself as a value. Now 
			# self.m_ExternalEventHandler.on_complete is self._on_apply_complete - same function object, just reachable from a 
			# different place (the handler). apply_final_name is already wired as the ExternalEventHandler's passable_method, 
			# so Raise() is what actually triggers it, inside a valid API context. on_complete only needs to handle what happens once that's done.
			self.vm_mainWindow.finally_apply_values(on_complete=self._on_apply_complete)
		except Exception as e:
			print("Failed to apply values:\n\n{}\n\n{}".format(e, traceback.format_exc()))
			TaskDialog.Show("Error", "Failed to apply values.")

	def _on_apply_complete(self, success):
		# type: (bool) -> None
		"""Called by BasicExEventHandler.Execute() after apply_final_name() finishes process."""
		if success:
			self.vm_mainWindow.InformationVM.IsFinalApplyButtonClicked = True
			# Show options after successful run of script
			mesa = "Rename successful!\nSuccess: {}\nFailed: {}\n\nPick following options - ".format(self.vm_mainWindow.InformationVM.CountSuccess, 
			                                                                                         self.vm_mainWindow.InformationVM.CountFailed)
			res = forms.alert(msg=mesa, title="Success", footer="Success", warn_icon=None,
							options=["Continue working with tool", "Exit"])
			if res == "Continue working with tool":
				self.vm_mainWindow.TreeViewerVM.tree_refresh_from_source()
				self._reset_tree_selection()
				self.vm_mainWindow.reset_renamer_list()

				# Restore window on top after manual selection, since it used to go behind.
				if self.WindowState == WindowState.Minimized:
					self.WindowState = WindowState.Normal
				self.Activate()
			else:
				self.Close()
		else:
			TaskDialog.Show("Error", "Rename failed.")