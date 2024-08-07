# -----------------------------------------------------------------------------
# Modified version of the JAX documentation configuration file for the DiffCheck project.
# Modified by: The DiffCheck authors
# Copyright 2024, The DiffCheck Authors.
#
# The original copyright notice is included below.
# Copyright 2018 The JAX Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import inspect
import operator
import os
import sys

# FIXME: check if the sys paths are correct on clean build
# import package's modules path
sys.path.insert(0, os.path.abspath('./'))
sys.path.insert(0, os.path.abspath('./../src/gh/diffCheck'))
# check that the bindings pyd/dlls are copied and importable
try:
    import diffCheck.diffcheck_bindings as dfb
except ImportError as e:
    print(f"Failed to import diffcheck_bindings: {e}")
    print("Current sys.path directories:")
    for path in sys.path:
        print(path)
    print("Current files in the directory:")
    for file in os.listdir(extra_dll_dir):
        print(file)
    sys.exit(1)

# import diffCheck
# print(f"Current diffCheck imported: {diffCheck.__version__}")



# # Workaround to avoid expanding type aliases. See:
# # https://github.com/sphinx-doc/sphinx/issues/6518#issuecomment-589613836
# from typing import ForwardRef

# def _do_not_evaluate_in_diffCheck(
#     self, globalns, *args, _evaluate=ForwardRef._evaluate,
# ):
#   if globalns.get('__name__', '').startswith('diffCheck'):
#     return self
#   return _evaluate(self, globalns, *args)
# ForwardRef._evaluate = _do_not_evaluate_in_diffCheck

# -- Project information -----------------------------------------------------

project = 'DiffCheck'
copyright = '2024, The DiffCheck Authors. We use ReadTheDocs, SPhinx, SphinxBookTheme and Jax theme-flavoured which are copyright their respective authors.'
author = 'The DiffCheck authors'

# The short X.Y version
version = '0.1'
# The full version, including alpha/beta/rc tags
release = ''


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = '2.1'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
sys.path.append(os.path.abspath('sphinxext'))
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.linkcode',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
    # 'matplotlib.sphinxext.plot_directive',
    'myst_nb',
    "sphinx_remove_toctrees",
    'sphinx_copybutton',
    'jax_extensions',
    'sphinx_design',
    'sphinxext.rediraffe',
    'sphinxcontrib.mermaid',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/reference/', None),
}

suppress_warnings = [
    'ref.citation',  # Many duplicated citations in numpy/scipy docstrings.
    'ref.footnote',  # Many unreferenced footnotes in numpy/scipy docstrings
    'myst.header',
    # TODO(jakevdp): remove this suppression once issue is fixed.
    'misc.highlighting_failure', # https://github.com/ipython/ipython/issues/14142
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
source_suffix = ['.rst', '.md']

# The main toctree document.
main_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    # Sometimes sphinx reads its own outputs as inputs!
    'build/html',
    # 'build/jupyter_execute',
    # 'notebooks/README.md',
    'README.md',
    # Ignore markdown source for notebooks; myst-nb builds from the ipynb
    # These are kept in sync using the jupytext pre-commit hook.
    # 'notebooks/*.md',
    # 'pallas/quickstart.md',
    # 'pallas/tpu/pipelining.md',
    # 'pallas/tpu/matmul.md',
    # 'jep/9407-type-promotion.md',
    # 'autodidax.md',
    # 'sharded-computation.md',
    # 'ffi.ipynb',
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


autosummary_generate = True
napolean_use_rtype = False


# -- Mocking -----------------------------------------------------------------
autodoc_mock_imports = [
  # Rhino/gh specifics
  "Rhino",
  "rhinoscriptsyntax",
  "scriptcontext",
  "Grasshopper",

  # Windows specific
  "System",
  ]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_book_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    'show_toc_level': 2,
    'repository_url': 'https://github.com/diffCheckOrg/diffCheck',
    'use_repository_button': True,     # add a "link to repository" button
    'navigation_with_keys': False,
}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = '../logo.png'

# html_favicon = '_static/favicon.png'
html_favicon = '../favicon.png'


# Add any paths that contain custom 
# static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'style.css',
]

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}

# -- Options for myst ----------------------------------------------
myst_heading_anchors = 3  # auto-generate 3 levels of heading anchors
myst_enable_extensions = ['dollarmath']
nb_execution_mode = "force"
nb_execution_allow_errors = False
nb_merge_streams = True
nb_execution_show_tb = True

# Notebook cell execution timeout; defaults to 30.
nb_execution_timeout = 100

# # List of patterns, relative to source directory, that match notebook
# # files that will not be executed.
# nb_execution_excludepatterns = [
#     # Slow notebook: long time to load tf.ds
#     'notebooks/neural_network_with_tfds_data.*',
#     # Slow notebook
#     'notebooks/Neural_Network_and_Data_Loading.*',
#     # Has extra requirements: networkx, pandas, pytorch, tensorflow, etc.
#     'jep/9407-type-promotion.*',
#     # TODO(jakevdp): enable execution on the following if possible:
#     'notebooks/Distributed_arrays_and_automatic_parallelization.*',
#     'notebooks/autodiff_remat.*',
#     # Requires accelerators
#     'pallas/quickstart.*',
#     'pallas/tpu/pipelining.*',
#     'pallas/tpu/matmul.*',
#     'sharded-computation.*',
#     'distributed_data_loading.*'
# ]

# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'DFdoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (main_doc, 'DF.tex', 'DF Documentation',
     'The DF authors', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (main_doc, 'df', 'DF Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (main_doc, 'DF', 'DF Documentation',
     author, 'DF', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# Tell sphinx autodoc how to render type aliases.
autodoc_typehints = "description"
autodoc_typehints_description_target = "all"
autodoc_type_aliases = {
    'ArrayLike': 'jax.typing.ArrayLike',
    'DTypeLike': 'jax.typing.DTypeLike',
}

# Remove auto-generated API docs from sidebars. They take too long to build.
remove_from_toctrees = ["_autosummary/*"]

# Customize code links via sphinx.ext.linkcode

def linkcode_resolve(domain, info):
  import diffCheck

  if domain != 'py':
    return None
  if not info['module']:
    return None
  if not info['fullname']:
    return None
  if info['module'].split(".")[0] != 'df':
     return None
  try:
    mod = sys.modules.get(info['module'])
    obj = operator.attrgetter(info['fullname'])(mod)
    if isinstance(obj, property):
        obj = obj.fget
    while hasattr(obj, '__wrapped__'):  # decorated functions
        obj = obj.__wrapped__
    filename = inspect.getsourcefile(obj)
    source, linenum = inspect.getsourcelines(obj)
  except:
    return None
  filename = os.path.relpath(filename, start=os.path.dirname(diffCheck.__file__))
  lines = f"#L{linenum}-L{linenum + len(source)}" if linenum else ""
  return f"https://github.com/diffCheckOrg/diffCheck/blob/main/diffCheck/{filename}{lines}"
