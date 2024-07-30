import sys
import os
from importlib import import_module
import locale
from datetime import datetime

sys.path.extend([os.path.abspath(".."), os.path.abspath("../benchstab")])

project = 'BenchStab'
copyright = str(datetime.now().year) + ', Loschmidt Laboratories'
author = 'Matej Berezny'
release = '0.1'
 
pygments_style = 'sphinx'
locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages'
]

predictor_dict = {
    v.header().name: v
    for k, v in import_module('benchstab.predictors.web').__dict__.items()
    if any(map(k.__contains__, ['Sequence', 'PdbID', 'PdbFile']))
}


predictor_availability = {
    k: "\n" + f".. |{k}| replace:: {v.is_available(v.url)} (as of {datetime.now().strftime('%b %d, %Y')})"
    for k, v in predictor_dict.items()
}

language = 'en'
exclude_patterns = []
templates_path = ['_templates']

autoclass_content = "init"

autodoc_default_options = {
    "member-order": "bysource",
    "undoc-members": False,
    "exclude-members": "also_needs, do_cleanup",
}

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

rst_epilog = f"""
.. role:: raw-html(raw)
   :format: html

{''.join(predictor_availability.values())}
"""

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']