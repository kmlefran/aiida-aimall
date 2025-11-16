# Developer Guide

(developer_guide)=

## Suggesting Improvements

### How Do I Submit a Good Enhancement Suggestion?


* Enhancement suggestions are tracked as GitHub issues.
* Use a clear and descriptive title for the issue to identify the suggestion.
* Provide a step-by-step description of the suggested enhancement in as many details as possible.
* Describe the current behavior and explain which behavior you expected to see instead and why. At this point you can also tell which alternatives do not work for you.
* You may want to include screenshots or screen recordings which help you demonstrate the steps or point out the part which the suggestion is related to. You can use LICEcap to record GIFs on macOS and Windows, and the built-in screen recorder in GNOME or SimpleScreenRecorder on Linux.
* Explain why this enhancement would be useful to most aiida-aimall users. You may also want to point out the other projects that solved it better and which could serve as inspiration.

### Before Submitting an Enhancement


* Make sure that you are using the latest version.
* Read the documentation carefully and find out if the functionality is already covered, maybe by an individual configuration.
* Perform a search to see if the enhancement has already been suggested. If it has, add a comment to the existing issue instead of opening a new one.
* Find out whether your idea fits with the scope and aims of the project. It's up to you to make a strong case to convince the project's developers of the merits of this feature. Keep in mind that we want features that will be useful to the majority of our users and not just a small subset. If you're just targeting a minority of users, consider writing an add-on/plugin library.
* Ensure that all `pytest` and `pre-commit` workflows succeed.

### Submitting an Enhancement

To submit an enhancement, create a pull request on Github. Enter a title for your pull request, describe the changes made, reference relevant Github issues (if necessary) and click "Create pull request". The editors will review the enhancement, discuss it, and ensure that all the tests and pre-commit workflows (described below) pass. Once the enhancement has been deemed acceptable, it will be merged into the `main` branch.


## Code Formatting


This project uses the [black](https://github.com/psf/black/) code formatter.

Any public functions and classes should be clearly documented with [google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) docstrings.


## Running the tests

The following will discover and run all unit test

```console
$ pip install --upgrade pip
$ pip install -e ".[testing]"
$ pytest -v
```

You can also run the tests in a virtual environment with [tox](https://tox.wiki/en/latest/)

    pip install tox tox-conda
    tox -e py38 -- -v

## Automatic coding style checks

Enable enable automatic checks of code sanity and coding style

```console
$ pip install -e ".[pre-commit]"
$ pre-commit install
```

After this, the [black](https://black.readthedocs.io) formatter,
the [pylint](https://www.pylint.org/) linter will
run at every commit.

If you ever need to skip these pre-commit hooks, just use

```console
$ git commit -n
```

You should also keep the pre-commit hooks up to date periodically, with

```console
$ pre-commit autoupdate
```

Or consider using [pre-commit.ci](https://pre-commit.ci).

## Continuous integration

`aiida-aimall` comes with a `.github` folder that contains continuous integration tests on every commit using [Github Actiongs](https://github.com/features/actions) It will:

1. run all tests
2. check coding style and version number (not required to pass by default)

## Building the documentation


 #. Install the ``docs`` extra

```console
$ pip install -e ".[docs]"
```

 #. Edit the individual documentation pages
    * docs/source/index.md
    * docs/source/developer_guide/index.md
    * docs/source/installation/index.md
    * docs/source/tutorials/index.md

 #. Use [Sphinx](https://www.sphinx-doc.org/en/master/) to generate the html documentation

```console
$ cd docs
$ make
```

Check the result by opening `build/html/index.html` in your browser.

## PyPI release

New package versions will be released on PyPI significant milestones/bug fixes by the owner by pushing a tag.
