# pylint: disable=redefined-outer-name,too-many-statements
"""Initialise a text database and profile for pytest."""
# import io
import os

import pytest

# import pathlib
# import shutil
# import tempfile
# from collections.abc import Mapping


pytest_plugins = ["aiida.manage.tests.pytest_fixtures"]  # pylint: disable=invalid-name


@pytest.fixture(scope="session")
def filepath_tests():
    """Return the absolute filepath of the `tests` folder.

    .. warning:: if this file moves with respect to the `tests` folder, the implementation should change.

    :return: absolute filepath of `tests` folder which is the basepath for all test resources.
    """
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="function")
def fixture_sandbox():
    """Return a `SandboxFolder`."""
    # pylint:disable=import-outside-toplevel
    from aiida.common.folders import (
        SandboxFolder,  # pylint:disable=import-outside-toplevel
    )

    # pylint:disable=import-outside-toplevel

    with SandboxFolder() as folder:
        yield folder


@pytest.fixture
def fixture_localhost(aiida_localhost):
    """Return a localhost `Computer`."""
    localhost = aiida_localhost
    localhost.set_default_mpiprocs_per_machine(1)
    return localhost


@pytest.fixture
def fixture_code(fixture_localhost):
    """Return an ``InstalledCode`` instance configured to run calculations of given entry point on localhost."""

    def _fixture_code(entry_point_name):
        from aiida.common import exceptions  # pylint:disable=import-outside-toplevel
        from aiida.orm import InstalledCode  # pylint:disable=import-outside-toplevel
        from aiida.orm import load_code  # pylint:disable=import-outside-toplevel

        label = f"test.{entry_point_name}"

        try:
            return load_code(label=label)
        except exceptions.NotExistent:
            return InstalledCode(
                label=label,
                computer=fixture_localhost,
                filepath_executable="/bin/true",
                default_calc_job_plugin=entry_point_name,
            )

    return _fixture_code
