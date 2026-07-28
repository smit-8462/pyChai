# -*- coding: utf-8 -*-

# ---> IMPORTS <---
import traceback, contextlib

from Autodesk.Revit.DB import Transaction, Document

# ===============

# ---> VARIABLES <---

# ===============

# ---> FUNCTIONS <---

@contextlib.contextmanager
def transac(doc, title):
	"""
	Context manager for transaction.
	:param doc: Document of transaction
	:type doc: Document
	:param title: Transaction title
	:type title: str
	:return: Sometimes
	:rtype: any
	"""
	tr = Transaction(doc, title)
	tr.Start()
	try:
		yield tr
		tr.Commit()
	except Exception as e:
		tr.RollBack()
		print("Transaction failed: {}\n{}\n{}".format(e, '-' * 25, traceback.format_exc()))

