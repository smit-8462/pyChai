# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import clr
clr.AddReference("PresentationFramework")

from System.Windows import DependencyProperty
from System.Windows.Data import IValueConverter, IMultiValueConverter

class StringEqualsConverter(IValueConverter):
	def Convert(self, value, targetType, parameter, culture):
		if value is None or parameter is None:
			return False
		return str(value) == str(parameter)

	def ConvertBack(self, value, targetType, parameter, culture):
		raise NotImplementedError("ConvertBack not supported for OneWay binding.")

class ObjectReferenceEqualsConverter(IMultiValueConverter):
	"""
	MultiBinding converter for the per-row Expander-header ToggleButton.
	values[0] = InformationVM.EditingTemplate (the one row currently held, or None)
	values[1] = this row's own DataContext (the GroupData_Renamer for that row)
	True only for the row that matches - so checking one row automatically
	shows every other row as unchecked, since they all share the same values[0].
	"""
	def Convert(self, values, targetType, parameter, culture):
		if values is None or len(values) < 2:
			return False
		editing_item, this_item = values[0], values[1]
		if editing_item is None or this_item is None:
			return False
		return editing_item is this_item

	def ConvertBack(self, value, targetTypes, parameter, culture):
		# OneWay is enough - Click handler in code-behind is the source of truth for EditingTemplate.
		return [DependencyProperty.UnsetValue, DependencyProperty.UnsetValue]