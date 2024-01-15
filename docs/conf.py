# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

from pathlib import Path
import sys
import importlib.metadata
from gmprocess.apps.gmrecords import GMrecordsApp

sys.path.insert(0, str(Path(__file__).parent / ".."))


# -- Create processing steps markdown ----------------------------------------
app = GMrecordsApp()
app.load_subcommands()
args = {
    "debug": False,
    "quiet": True,
    "eventid": None,
    "textfile": None,
    "overwrite": False,
    "num_processes": 0,
    "label": None,
    "subcommand": "processing_steps",
    "func": app.classes["processing_steps"]["class"],
    "log": None,
    "output_markdown": str(
        Path(__file__).parent / "contents" / "manual" / "processing_steps_output.md"
    ),
}
app.main(**args)

# -- Project information -----------------------------------------------------

project = "gmprocess"
copyright = "Unlicense"

# The full version, including alpha/beta/rc tags
release = importlib.metadata.version("gmprocess")
release = ".".join(release.split(".")[:3])
version = release

nb_execution_mode = "force"
execution_mode = "force"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # "autoapi.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinxcontrib.programoutput",
    "myst_nb",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

# autoapi_dirs = ["../src/gmprocess"]
# autoapi_add_toctree_entry = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_static_path = [str(Path("_static").resolve())]

todo_include_todos = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"
# html_logo = "_static/gmprocess_icon_small.png"

base_url = "https://code.usgs.gov/ghsc/esi/groundmotion-processing/-/raw/main/docs/"

announcement_html = """
    <a href='https://www.usgs.gov/' style='text-decoration: none'>
        <img id="announcement_left_img" valign="middle" src="%s_static/usgs.png""></a>
    Ground-Motion Processing Software
    <a href='https://code.usgs.gov/ghsc/esi/groundmotion-processing' style='text-decoration: none'>
        <img id="announcement_right_img" valign="middle"
            src="%s_static/GitHub-Mark/PNG/GitHub-Mark-Light-120px-plus.png"></a>
""" % (
    base_url,
    base_url,
)

html_theme_options = {"sidebar_hide_name": False, "announcement": announcement_html}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".

source_suffix = [".rst", ".md"]


def setup(app):
    app.add_css_file("css/custom.css")
