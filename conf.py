# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = 'Cassandra Gemini'
copyright = '2026, Annika Klein & C. Gabriel David'
author = 'Annika Klein, C. Gabriel David'
release = '0.1.0'

extensions = ['sphinx.ext.mathjax', 'sphinx.ext.todo', 'sphinxcontrib.tikz']
todo_include_todos = True
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
master_doc = 'index'

# TikZ flowcharts are compiled at build time (needs LaTeX + pdf2svg, see readthedocs.yaml)
tikz_proc_suite = 'pdf2svg'
tikz_transparent = True
tikz_latex_preamble = r"""
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\newlength{\tw}\setlength{\tw}{16cm}
"""

html_theme = 'sphinx_rtd_theme'
html_title = 'Cassandra Gemini'
html_static_path = ['_static']
html_logo = '_static/logo.png'
html_css_files = ['custom.css']
