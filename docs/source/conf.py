# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import pathlib
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sphinx_rtd_theme
from aiida.manage.configuration import load_documentation_profile

load_documentation_profile()

project = "aiida-aimall"
copyright = "2023, Kevin Lefrancois-Gagnon, Robert Mawhinney"
author = "Kevin Lefrancois-Gagnon, Robert Mawhinney"
release = "0.2.0"


extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


templates_path = ["_templates"]
exclude_patterns = []


import os

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, pathlib.Path(__file__).parents[2].resolve().as_posix())
source_suffix = ".rst"
master_doc = "index"
pygments_style = "sphinx"
html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

intersphinx_mapping = {
    "python": ("https://docs.python.org/", None),
    "numpy": ("http://docs.scipy.org/doc/numpy/", None),
}

nitpick_ignore = [
    ("py:class", "Logger"),
]


def run_apidoc(_):
    """Runs sphinx-apidoc when building the documentation.

    Needs to be done in conf.py in order to include the APIdoc in the
    build on readthedocs.

    See also https://github.com/rtfd/readthedocs.org/issues/1139
    """
    source_dir = os.path.abspath(os.path.dirname(__file__))
    apidoc_dir = os.path.join(source_dir, "apidoc")
    package_dir = os.path.join(source_dir, os.pardir, os.pardir, "aiida_aimall")

    # In #1139, they suggest the route below, but this ended up
    # calling sphinx-build, not sphinx-apidoc
    # from sphinx.apidoc import main
    # main([None, '-e', '-o', apidoc_dir, package_dir, '--force'])

    import subprocess

    cmd_path = "sphinx-apidoc"
    if hasattr(sys, "real_prefix"):  # Check to see if we are in a virtualenv
        # If we are, assemble the path manually
        cmd_path = os.path.abspath(os.path.join(sys.prefix, "bin", "sphinx-apidoc"))

    options = [
        "-o",
        apidoc_dir,
        package_dir,
        "--private",
        "--force",
        "--no-toc",
    ]

    # See https://stackoverflow.com/a/30144019
    env = os.environ.copy()
    env[
        "SPHINX_APIDOC_OPTIONS"
    ] = "members,special-members,private-members,undoc-members,show-inheritance"
    subprocess.check_call([cmd_path] + options, env=env)


def setup(app):
    app.connect("builder-inited", run_apidoc)
