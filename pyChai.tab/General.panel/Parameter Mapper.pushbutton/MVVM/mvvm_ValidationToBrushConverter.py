# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import clr
clr.AddReference("System")
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

from System.Windows.Data import IValueConverter
from System.Data import DataRowView

# ===============
# ---> CLASSES <---
class CellValidityConverter(IValueConverter):
	"""
	Converts a DataRowView into a bool, True if cell is valid, else False if invalid. The colors are handled entirely in
	XAML via a DataTrigger (using code-behind) on ValidatedCellStyle. This keeps the converter dumb.

	value (DataRowView) - the row item for the cell being styled.
	parameter (string) - The column name, supplied per-column from PreviewWindow.OnAutoGeneratingColumn via ConverterParameter.
	"""
	def __init__(self, validity_map_provider):
		super(CellValidityConverter, self).__init__()
		self._get_validity_map = validity_map_provider

	def Convert(self, value, targetType, parameter, culture):
		try:
			row_view = value  # type: DataRowView
			column_name = parameter  # type: str
			if row_view is None or column_name is None:
				return True  # nothing to validate against -> don't flag as invalid

			validity_map = self._get_validity_map()
			if validity_map is None:
				return True

			first_col_name = row_view.Row.Table.Columns[0].ColumnName
			row_key = str(row_view[first_col_name])
			cell_key = "{}|{}".format(row_key, column_name)

			if validity_map.ContainsKey(cell_key):
				return validity_map[cell_key]
			return True
		except:		# Never let a converter exception break the DataGrid render, defaulting to "valid".
			return True

	def ConvertBack(self, value, targetType, parameter, culture):
		raise NotImplementedError()


class ValidationToTooltipConverter(IValueConverter):
	"""Returns the tooltip message string for an invalid cell, or None if valid."""
	def __init__(self, error_map_provider):
		super(ValidationToTooltipConverter, self).__init__()
		self._get_error_map = error_map_provider

	def Convert(self, value, targetType, parameter, culture):
		try:
			row_view = value  # type: DataRowView
			column_name = parameter  # type: str
			if row_view is None or column_name is None:
				return None

			error_map = self._get_error_map()
			if error_map is None:
				return None

			first_col_name = row_view.Row.Table.Columns[0].ColumnName
			row_key = str(row_view[first_col_name])
			cell_key = "{}|{}".format(row_key, column_name)

			if error_map.ContainsKey(cell_key):
				return error_map[cell_key]
			return None
		except:
			return None

	def ConvertBack(self, value, targetType, parameter, culture):
		raise NotImplementedError()