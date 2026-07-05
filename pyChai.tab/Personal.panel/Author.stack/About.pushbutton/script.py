# -*- coding: utf-8 -*-

# ---> IMPORTS <---
import os
from pyrevit import script

# ===============

# ---> SCRIPT <---

# Load markdown file
bundle_dir = os.path.dirname(os.path.realpath(__file__))
markdown_file = os.path.join(bundle_dir, "about.md")

with open(markdown_file, 'r') as f:
    md_read = f.read()

# Pyrevit output
output = script.get_output()
output.print_md(md_read)