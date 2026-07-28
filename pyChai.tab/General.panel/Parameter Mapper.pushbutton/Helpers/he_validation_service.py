class ValidationService:
	"""Validate rows with complete mapping rules."""
	@staticmethod
	def validate(rows):
		"""
		Validate rows with complete mapping rules.
		:param rows: list of rows
		:type rows: ObservableCollection[ChoiceRowViewModel]()
		:return: Dictionary of errors, having --> SerialNumber, string
		:rtype: dict
		"""
		errors = {}

		# Track first occurrences
		first_occurrence = {}  # (param, col) -> SerialNumber
		param_to_col = {}  # param -> first col
		col_to_param = {}  # col -> first param

		for row in rows:
			serial = row.SerialNumber
			has_param = row.RevitParameterValue and str(row.RevitParameterValue).strip()
			has_col = row.ExcelColumnValue and str(row.ExcelColumnValue).strip()

			# Rule 1 - Missing values = Invalid
			if not (has_param and has_col):
				errors[serial] = "Invalid"
				continue

			param = row.RevitParameterValue
			col = row.ExcelColumnValue
			pair_key = (param, col)

			# Rule 2 - Duplicate pair exists
			if pair_key in first_occurrence:
				first_serial = first_occurrence[pair_key]
				errors[serial] = "Duplicate - Already exists in Row {}".format(first_serial)
				continue

			# Rule 3 - Parameter already mapped to different column
			if param in param_to_col and param_to_col[param] != col:
				first_col = param_to_col[param]
				# Find the first row with this mapping
				for r in rows:
					if r.RevitParameterValue == param and r.ExcelColumnValue == first_col:
						errors[serial] = "Invalid - '{}' already mapped to '{}' in Row {}".format(
							param, first_col, r.SerialNumber)
						break
				continue

			# Rule 4 - Column already mapped to different parameter
			if col in col_to_param and col_to_param[col] != param:
				first_param = col_to_param[col]
				for r in rows:
					if r.ExcelColumnValue == col and r.RevitParameterValue == first_param:
						errors[serial] = "Invalid - '{}' already mapped to '{}' in Row {}".format(
							col, first_param, r.SerialNumber)
						break
				continue

			# Valid unique mapping
			first_occurrence[pair_key] = serial
			param_to_col[param] = col
			col_to_param[col] = param
		return errors