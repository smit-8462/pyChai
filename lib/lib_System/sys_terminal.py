# -*- coding: utf-8 -*-
# ---> IMPORTS <---
import os, subprocess

# ===============
def subprocess_script_output_pyrevit(script_file_path, python_engine_path, args=None):
	# type: (str, str, None | list) -> str
	"""
	Runs Python script externally on Windows, and returns the result back to original script process.
    :param script_file_path: Path to the script file
    :type script_file_path: str
    :param python_engine_path: Path to the Python engine executable
    :type python_engine_path: str
    :param args: Arguments to pass to subprocess.Popen
    :type args: list
    :return: Output
    :rtype: str
	"""
	if not os.path.isfile(script_file_path):
		return None, "Script file not found: {}".format(script_file_path) # type: ignore

	# Suppressing Command Terminal window
	si = subprocess.STARTUPINFO()
	si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	si.wShowWindow = subprocess.SW_HIDE		# SW_HIDE is typically the default when STARTF_USESHOWWINDOW is set

	# Setting Python output to UTF-8
	env = os.environ.copy()
	env["PYTHONIOENCODING"] = "utf-8"

	if not os.path.isfile(python_engine_path):
		return None, "Python engine not found: {}".format(python_engine_path)	# type: ignore

	# Using the specified Python engine executable directly. Here, /c tells cmd.exe to run the command and then exit
	command_prompt = ["cmd.exe", "/c", python_engine_path, script_file_path]

	# Starting subprocess, and append extra arguments to pass to the script
	if args is not None:
		command_prompt.extend([str(a) for a in args])
	external_process = subprocess.Popen(command_prompt, stdout=subprocess.PIPE,
										stderr=subprocess.PIPE, startupinfo=si, env=env)

	try:
		output, errors = external_process.communicate()
	except Exception as e:
		return str(e)
	finally:
		external_process.stdout.close()	# type: ignore
		external_process.stderr.close()	# type: ignore

	output = output.decode("utf-8")
	errors = errors.decode("utf-8")
	return output, errors	
