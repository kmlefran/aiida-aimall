[![ci](https://github.com/kmlefran/aiida-aimall/actions/workflows/ci.yml/badge.svg)](https://github.com/kmlefran/aiida-aimall/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/kmlefran/aiida-aimall/badge.svg?branch=main)](https://coveralls.io/github/kmlefran/aiida-aimall?branch=main)
[![Documentation Status](https://readthedocs.org/projects/aiida-aimall/badge/?version=latest)](https://aiida-aimall.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/aiida-aimall.svg)](https://badge.fury.io/py/aiida-aimall)

!This README and all documentation is a work in progress!

# Copyright notice

This repository contains modified versions of the calculations and parsers presented in [Aiida-Gaussian](https://github.com/nanotech-empa/aiida-gaussian). Copyright (c) 2020 Kristjan Eimre. The modifications basically amount to adding the wfx file to the retrieved nodes and adding some groups/extras to calculation output.

Also, the (incomplete) testing framework is heavily influenced by the infrastructure presented in [aiida-quantumespresso](https://github.com/aiidateam/aiida-quantumespresso).  Copyright (c), 2015-2020, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE
(Theory and Simulation of Materials (THEOS) and National Centre for
Computational Design and Discovery of Novel Materials (NCCR MARVEL))

# aiida-aimall

A plugin to interface AIMAll with AiiDA

This plugin is the default output of the
[AiiDA plugin cutter](https://github.com/aiidateam/aiida-plugin-cutter),
intended to help developers get started with their AiiDA plugins.

## Repository contents

* [`.github/`](.github/): [Github Actions](https://github.com/features/actions) configuration
  * [`workflows/`](.github/workflows/)
    * [`ci.yml`](.github/workflows/ci.yml): runs tests, checks test coverage and builds documentation at every new commit
    * [`publish-on-pypi.yml`](.github/workflows/publish-on-pypi.yml): automatically deploy git tags to PyPI - just generate a [PyPI API token](https://pypi.org/help/#apitoken) for your PyPI account and add it to the `pypi_token` secret of your github repository
  * [`config/`](.github/config) config files for testing/docs environment
    * [`code-aim.yaml`](.github/workflows/config/code-aim.yaml) config file for building precommit and test envs
    * [`code-gwfx.yaml`](.github/workflows/config/code-gwfx.yaml) config file for building precommit and test envs
    * [`profile.yaml`](.github/workflows/config/profile.yaml) config file for aiida profile
    * [`profile.yaml`](.github/workflows/config/localhost-config.yaml) config file for localhost computer
    * [`profile.yaml`](.github/workflows/config/localhost-setup.yaml) setup file for localhost computer
* [`aiida_aimall/`](aiida_aimall/): The main source code of the plugin package
  * [`data/`](aiida_aimall/data/): A new `AimqbParameters` data class, used as input to the `AimqbCalculation` `CalcJob` class
  * [`calculations.py`](aiida_aimall/calculations.py): A new `AimqbCalculation` `CalcJob` class, and `GaussianWFXCalculation`, a modified version of `GaussianCalculation` from [AiiDA Gaussian](https://github.com/nanotech-empa/aiida-gaussian)
  * [`parsers.py`](aiida_aimall/parsers.py): A new `Parser` for the `AimqbCalculation`, and `GaussianWFXParser`, a modified version of `GaussianBaseParser` from [AiiDA Gaussian](https://github.com/nanotech-empa/aiida-gaussian)
  * [`workchains.py`](aiida_aimall/workchains.py): New `WorkChains`.
    * `MultiFragmentWorkChain` to fragment molecules using cml files from the Retrievium database and submit Gaussian calculations for the fragments using functions in `frag_functions` from [subproptools Github](https:github.com/kmlefran/group_decomposition)
    * `G16OptWorkchain` to take output from `MultiFragmentWorkChain` and submit Gaussian optimization calculations
    * `AimAllReorWorkChain` to run `AimqbCalculation` on output from `GaussianWFXCalculations`, then reorient to coordinate systems defined in `subreor` from [subproptools Github](https:github.com/kmlefran/subproptools)
* [`controllers.py`](aiida_aimall/controllers.py): Workflow controllers to limit number of running jobs on localhost computers.
  * `AimReorSubmissionController` to control `AimReorWorkChain`s. These use `parent_group_label` for the wavefunction file nodes from `GaussianWFXCalculation`s
  * `AimAllSubmissionController` to control `AimqbCalculations``. These use `parent_group_label` for the wavefunction file nodes from `GaussianWFXCalculation`s
  * `GaussianSubmissionController` to control `GaussianWFXCalculations`. This is mostly intended to have a arbitrarily large number of max concurrents and scan for output structures of `AimReorWorkchain`s to submit to a remote cluster
* [`docs/`](docs/): Source code of documentation for [Read the Docs](http://aiida-diff.readthedocs.io/en/latest/)
* [`examples/`](examples/): An example of how to link the four controllers in an overall workflow
* [`tests/`](tests/): Basic regression tests using the [pytest](https://docs.pytest.org/en/latest/) framework (submitting a calculation, ...). Install `pip install -e .[testing]` and run `pytest`.
  * [`conftest.py`](conftest.py): Configuration of fixtures for [pytest](https://docs.pytest.org/en/latest/)
* [`.gitignore`](.gitignore): Telling git which files to ignore
* [`.pre-commit-config.yaml`](.pre-commit-config.yaml): Configuration of [pre-commit hooks](https://pre-commit.com/) that sanitize coding style and check for syntax errors. Enable via `pip install -e .[pre-commit] && pre-commit install`
* [`.readthedocs.yml`](.readthedocs.yml): Configuration of documentation build for [Read the Docs](https://readthedocs.org/)
* [`.isort.cfg`](.isort.cfg): Configuration to make isort and black precommit actions compatible
* [`LICENSE`](LICENSE): License for your plugin
* [`README.md`](README.md): This file
* [`pyproject.toml`](setup.json): Python package metadata for registration on [PyPI](https://pypi.org/) and the [AiiDA plugin registry](https://aiidateam.github.io/aiida-registry/) (including entry points)

## Features

 * Add input files using `SinglefileData`:
   ```python
   SinglefileData = DataFactory('singlefile')
   inputs['file1'] = SinglefileData(file='/path/to/file1')
   inputs['file2'] = SinglefileData(file='/path/to/file2')
   ```

 * Specify command line options via a python dictionary and `DiffParameters`:
   ```python
   d = { 'ignore-case': True }
   DiffParameters = DataFactory('aimall')
   inputs['parameters'] = DiffParameters(dict=d)
   ```

 * `DiffParameters` dictionaries are validated using [voluptuous](https://github.com/alecthomas/voluptuous).
   Find out about supported options:
   ```python
   DiffParameters = DataFactory('aimall')
   print(DiffParameters.schema.schema)
   ```

## Installation

```shell
pip install aiida-aimall
verdi quicksetup  # better to set up a new profile
verdi plugin list aiida.calculations  # should now show your calclulation plugins
```


## Usage

Here goes a complete example of how to submit a test calculation using this plugin.

A quick demo of how to submit a calculation:
```shell
verdi daemon start     # make sure the daemon is running
cd examples
./example_01.py        # run test calculation
verdi process list -a  # check record of calculation
```

The plugin also includes verdi commands to inspect its data types:
```shell
verdi data aimall list
verdi data aimall export <PK>
```

## Development

```shell
git clone https://github.com/kmlefran/aiida-aimall .
cd aiida-aimall
pip install --upgrade pip
pip install -e .[pre-commit,testing]  # install extra dependencies
pre-commit install  # install pre-commit hooks
pytest -v  # discover and run all tests
```

See the [developer guide](http://aiida-aimall.readthedocs.io/en/latest/developer_guide/index.html) for more information.

## License

MIT
## Contact

kgagnon@lakeheadu.ca


[ci-badge]: https://github.com/kmlefran/aiida-aimall/workflows/ci/badge.svg?branch=master
[ci-link]: https://github.com/kmlefran/aiida-aimall/actions
[cov-badge]: https://coveralls.io/repos/github/kmlefran/aiida-aimall/badge.svg?branch=master
[cov-link]: https://coveralls.io/github/kmlefran/aiida-aimall?branch=master
[docs-badge]: https://readthedocs.org/projects/aiida-aimall/badge
[docs-link]: http://aiida-aimall.readthedocs.io/
[pypi-badge]: https://badge.fury.io/py/aiida-aimall.svg
[pypi-link]: https://badge.fury.io/py/aiida-aimall
