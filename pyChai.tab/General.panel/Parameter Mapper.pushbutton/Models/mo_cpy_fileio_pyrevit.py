# NOTE = Use CPython 3.12+
# ---> IMPORTS <---
import os, sys, json, traceback, tempfile, datetime

# ===============
# ---> CLASSES <---
class NumpyEncoder(json.JSONEncoder):
	def default(self, obj):
		import numpy as np		# Lazy import, so that it can be imported after sys.append external lib path.

		if isinstance(obj, np.integer):
			return int(obj)
		if isinstance(obj, np.floating):
			return float(obj)
		if isinstance(obj, np.ndarray):
			return obj.tolist()
		return super(NumpyEncoder, self).default(obj)

# ===============
# ---> METHODS <---
def _file_to_dataframe(file_path, ext):
	"""
	Read the selected file and return a pandas dataframe.
	:param file_path: File path
	:type file_path: str
	:param ext: File extension
	:type ext: str
	:return: Pandas dataframe
	:rtype: pandas.DataFrame
	"""
	import pandas as pd			# Lazy import, so that it can be imported after sys.append external lib path.

	file_encoding = "utf-8"
	engine_map = {".xlsx" : "openpyxl",
				  ".xlsm" : "openpyxl",
				  ".xls" : "xlrd",
				  ".xlsb" : "pyxlsb",
				  ".ods" : "odf"}

	# While reading the empty cells of Excel / LibreOffice Calc / CSV, pandas convert the empty cells into
	# a 'NaN' (Not a Number) string. So, to avoid converting the empty cells, we are using keep_default_na as False.
	ext = ext.lower()
	if ext == ".csv":
		return pd.read_csv(file_path, encoding=file_encoding, keep_default_na=False)
	if ext not in engine_map:
		raise ValueError("Unsupported file format: {}".format(ext))
	return pd.read_excel(file_path, engine=engine_map[ext], keep_default_na=False)

def _extract_values(pandas_dataframe):
	"""
	Extract values from a pandas dataframe.
	:param pandas_dataframe: Pandas Dataframe
	:type pandas_dataframe: pandas.DataFrame
	"""
	dict_values = pandas_dataframe.to_dict(orient="list")
	return dict_values

def _log_failure(context, args_list):
	"""
	Write failure details (traceback + context) to a log file in the temp folder.
	:param context: Log context
	:type context: str
	:param args_list: List of arguments
	:type args_list: list
	"""
	# The debug log file is written to the system temp folder - only created if something fails.
	# The pyRevit's CPython engine has a bug where only 1 print output is printed, so rest of the code lines are ignored.
	# Therefore, the error log is dumped in log file created in temp folder.
	debug_log = os.path.join(tempfile.gettempdir(), "pyChai_cpy_debug.log")

	with open(debug_log, "a", encoding="utf-8") as f:
		f.write("[{}] FAILURE\n".format(datetime.datetime.now().isoformat()))
		f.write("Context: {}\n".format(context))
		f.write("Args: {}\n".format(args_list))
		f.write(traceback.format_exc())
		f.write("\n" + ("-" * 60) + "\n")
	return debug_log

def main():
	# The system arguments are passed from subprocess, which are attached to 4 variables.
	picked_file_path = sys.argv[1]
	picked_file_ext  = sys.argv[2]
	plugin_lib_path = sys.argv[3]
	cpython_external_lib_path = sys.argv[4]

	# Adding "lib" folder to CPython path for accessing lib files, by appending library to script
	sys.path.append(plugin_lib_path)
	sys.path.append(cpython_external_lib_path)

	file_output = _file_to_dataframe(picked_file_path, picked_file_ext)
	dict_val = _extract_values(file_output)

	# Return output back to pyrevit script
	print(json.dumps(dict_val, cls=NumpyEncoder))

if __name__ == "__main__":
	try:
		main()
	except Exception:
		log_path = _log_failure("Error occurred in main()", sys.argv)
		# Write to stderr so that the error-return mechanism keeps working.
		sys.stderr.write(traceback.format_exc())
		sys.stderr.write("\nFull details logged to: {}\n".format(log_path))
		sys.exit(1)