# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PKG_SRC = os.path.join(ROOT, "cooking_assistant")
sys.path.insert(0, ROOT)  # allow 'cooking_assistant' imports for autodoc

project = 'Cooking Assistant'
copyright = '2025, Leo Ivars, Lounis Hamroun, Alexandre Donnat, Omar Fekih'
author = 'Leo Ivars, Lounis Hamroun, Alexandre Donnat, Omar Fekih'
release = 'v1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autosummary_generate = True

autodoc_typehints = "description"
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True


myst_enable_extensions = ["linkify"]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_theme_options = {
    "description": "Bayesian ranking & multi-signal recipe classification",
    "github_user": "lounishamroun",
    "github_repo": "cooking-assistant",
    "github_banner": True,
    "fixed_sidebar": True,
    "show_related": False,
}
html_static_path = ['_static']
master_doc = "index"

# Build date (in case we want to surface it)
html_last_updated_fmt = "%Y-%m-%d"

# Strict warnings can be enabled later for CI discipline
nitpicky = False