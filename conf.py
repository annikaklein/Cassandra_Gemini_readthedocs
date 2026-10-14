# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
project = 'Cassandra Gemini'
copyright = '2026, Annika Klein & C. Gabriel David'
author = 'Annika Klein, C. Gabriel David'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
extensions = ['sphinx.ext.mathjax', 'sphinx.ext.todo']
todo_include_todos = True
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_title = 'Cassandra Gemini'
html_static_path = ['_static']
html_logo = '_static/logo.png'
html_css_files = ['custom.css']
