# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "peak-acl"
copyright = "2025, Santiago Bossa"
author = "Santiago Bossa"

version = "0.5.4"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

# Enable extra MyST Markdown features
myst_enable_extensions = [
    "deflist",
    "colon_fence",
]

autosectionlabel_prefix_document = True

# Generate stub pages for autosummary directives
autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", "https://docs.python.org/3/objects.inv"),
    "aiohttp": (
        "https://docs.aiohttp.org/en/stable/",
        "https://docs.aiohttp.org/en/stable/objects.inv",
    ),
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_theme_options = {
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
}
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Make project modules importable
autodoc_typehints = "description"
