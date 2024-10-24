---
myst:
  substitutions:
    pip: '[`pip`](https://pip.pypa.io/en/stable/index.html)'
    PyPI: '[PyPI](https://pypi.org/)'
---

# Get started

(installation-requirements)=

## Requirements

To work with `aiida-aimall`, you should have:

- installed `aiida-core`
- configured an AiiDA profile.

Please refer to the [documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/get_started.html) of `aiida-core` for detailed instructions.

(installation-installation)=

## Installation

The Python package can be installed from the Python Package index {{ PyPI }} or directly from the source:

::::{tab-set}

:::{tab-item} PyPI
The recommended method of installation is to use the Python package manager {{ pip }}:

```console
$ pip install aiida-aimall
```

This will install the latest stable version that was released to {{ PyPI }}.
:::

:::{tab-item} Source
To install the package from source, first clone the repository and then install using {{ pip }}:

```console
$ git clone https://github.com/aiidateam/aiida-quantumespresso
$ pip install -e aiida-aimall
```

The ``-e`` flag will install the package in editable mode, meaning that changes to the source code will be automatically picked up.
:::

::::

If you are using `WorkChain`s that run `GaussianCalculation`s on some computers like Apple M1s, the current release of the dependency cclib (v1.8.1) may result in an error due to a space in the computer name. The master branch of cclib has been updated to fix this bug. The direct dependency is not allowed on PyPi. If you are in the situation, you can fix it by installing the current version of cclib from the master branch after installing aiida-aimall.

```shell
(env) pip install git+https://github.com/cclib/cclib
```

(installation-setup)=

## Setup

(installation-setup-computer)=

### Computer

To run AIMAll calculations on a compute resource, the computer should first be set up in AiiDA.
This can be done from the command line interface (CLI) or the Python application programming interface (API).
In this example, we will set up the `localhost`, the computer where AiiDA itself is running:

::::{tab-set}

:::{tab-item} CLI

To set up a computer, use the ``verdi`` CLI of ``aiida-core``.

```console
$ verdi computer setup -n -L localhost -H localhost -T core.local -S core.direct -w ~/aiida_work_dir
```

After creating the localhost computer, configure the `core.local` transport using:

```console
$ verdi computer configure core.local localhost -n --safe-interval 0
```

Verify that the computer was properly setup by running:

```console
$ verdi computer test localhost
```
:::

:::{tab-item} API

To setup a computer using the Python API, run the following code in a Python script with `verdi run` or in the `verdi` shell:

```python
from aiida.orm import Computer
from pathlib import Path

computer = Computer(
    label='localhost',
    hostname='localhost',
    transport_type='core.local',
    scheduler_type='core.direct',
    workdir=Path('~/aiida_work_dir').resolve()
).store()
computer.configure()
```
:::
::::

For more detailed information, please refer to the documentation [on setting up compute resources](https://aiida.readthedocs.io/projects/aiida-core/en/latest/howto/run_codes.html#how-to-set-up-a-computer).

(installation-setup-code)=

### Code

To run an AIMAll code, it should first be setup in AiiDA.
This can be done from the command line interface (CLI) or the Python application programming interface (API).
In this example, we will setup the `aimqb` code that is installed on the computer where AiiDA is running:

::::{tab-set}

:::{tab-item} CLI

To setup a particular AIMAll code, use the ``verdi`` CLI of ``aiida-core``.

```console
$ verdi code create core.code.installed -n --computer localhost --label aimall --default-calc-job-plugin aimall.aimqb --filepath-executable aimqb
```
:::

:::{tab-item} API

To setup particular AIMAll code using the Python API, run the following code in a Python script with `verdi run` or in the `verdi` shell:

```python
from aiida.orm import InstalledCode

computer = load_computer('localhost')
code = InstalledCode(
label='aimall',
computer=computer,
filepath_executable='aimqb',
default_calc_job_plugin='aimall.aimqb',
).store()
```
:::

::::

:::{important}
Using the commands above, you will set up a code that uses the first `aimqb` binary your `PATH`.
You can find out the absolute path to this binary using the `which` command:

```console
which aimqb
```

If this is not the AIMQB version you want to run, pass the correct absolute path as the filepath executable.
:::

`aiida-aimall` also provides workflows to automatically interface with electronic structure programs. Many workflows, by default, interface with [Gaussian Software](https://gaussian.com). To use Gaussian software in these workflows, an
AiiDA code instance must also be setup for Gaussian Software, following similar steps to the above setup of AIMAll software.

::::{tab-set}

:::{tab-item} CLI

To setup a particular Gaussian code, use the ``verdi`` CLI of ``aiida-core``.

```console
$ verdi code create core.code.installed -n --computer localhost --label gaussian --default-calc-job-plugin aimall.gaussianwfx --filepath-executable g16
```
:::

:::{tab-item} API

To setup particular AIMAll code using the Python API, run the following code in a Python script with `verdi run` or in the `verdi` shell:

```python
from aiida.orm import InstalledCode

computer = load_computer('localhost')
code = InstalledCode(
label='gaussian',
computer=computer,
filepath_executable='g16',
default_calc_job_plugin='aimall.gaussianwfx',
).store()
```
:::

::::

Any electronic structure software that can be run through the command line can be used through workflows that utilise the `aiida-shell` package. For these calculations, either a string label of the command or a `ShellCode` object can be provided. To setup a `ShellCode`, you can also either create that via the command line, or a Python API. An example is given here for [ORCA](https://www.faccts.de/orca/).

::::{tab-set}

:::{tab-item} CLI

To setup a particular ShellCode, (ORCA as an example here) use the ``verdi`` CLI of ``aiida-core``.

```console
$ verdi code create core.code.installed.shell -n --computer localhost --label orca --default-calc-job-plugin core.shell --filepath-executable orca
```
:::

:::{tab-item} API

To setup particular AIMAll code using the Python API, run the following code in a Python script with `verdi run` or in the `verdi` shell:

```python
from aiida_shell import ShellCode

computer = load_computer('localhost')
code = ShellCode(
label='orca',
computer=computer,
filepath_executable='orca',
default_calc_job_plugin='core.shell',
).store()
```
:::

::::

For more detailed information, please refer to the documentation [on setting up codes](https://aiida.readthedocs.io/projects/aiida-core/en/latest/howto/run_codes.html#how-to-setup-a-code).
