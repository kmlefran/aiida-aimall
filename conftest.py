"""pytest fixtures for simplified testing."""
import sys

import pytest

pytest_plugins = ["aiida.manage.tests.pytest_fixtures"]


@pytest.fixture(scope="function", autouse=True)
def clear_database_auto(clear_database):  # pylint: disable=unused-argument
    """Automatically clear database in between tests."""


@pytest.fixture(scope="function")
def aimall_code(aiida_local_code_factory):
    """Get a aimall code."""
    with open("test.txt", "w", encoding="utf-8") as ofile:
        ofile.write(f"{sys.path}")
    return aiida_local_code_factory(
        executable="aimqb",
        entry_point="aimall",
        label="aimall2",
    )
