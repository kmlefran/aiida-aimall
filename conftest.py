"""pytest fixtures for simplified testing."""
import pytest

from aiida.common import exceptions
from aiida.orm import Computer, InstalledCode, QueryBuilder

pytest_plugins = ["aiida.manage.tests.pytest_fixtures"]


@pytest.fixture(name="my_aim_code")
def aiida_local_code_factory2(aiida_localhost):
    """Get an AiiDA code on localhost.

    Searches in the PATH for a given executable and creates an AiiDA code with provided entry point.

    Usage::

      def test_1(aiida_local_code_factory):
          code = aiida_local_code_factory('quantumespresso.pw', '/usr/bin/pw.x')
          # use code for testing ...

    :return: A function get_code(entry_point, executable) that returns the `Code` node.
    :rtype: object
    """

    def get_code(
        entry_point, executable, computer=aiida_localhost, label=None, **kwargs
    ):
        """Get local code.

        Sets up code for given entry point on given computer.

        :param entry_point: Entry point of calculation plugin
        :param executable: name of executable; will be searched for in local system PATH.
        :param computer: (local) AiiDA computer
        :param label: Define the label of the code. By default the ``executable`` is taken. This can be useful if
            multiple codes need to be created in a test which require unique labels.
        :param kwargs: Additional keyword arguments that are passed to the code's constructor.
        :return: the `Code` either retrieved from the database or created if it did not yet exist.
        :rtype: :py:class:`~aiida.orm.Code`
        """

        if label is None:
            label = executable

        builder = QueryBuilder().append(
            Computer, filters={"uuid": computer.uuid}, tag="computer"
        )
        builder.append(
            InstalledCode,
            filters={"label": label, "attributes.input_plugin": entry_point},
            with_computer="computer",
        )

        try:
            code = builder.one()[0]
        except (exceptions.MultipleObjectsError, exceptions.NotExistent):
            code = None
        else:
            return code

        code = InstalledCode(
            label=label,
            description=label,
            default_calc_job_plugin=entry_point,
            computer=computer,
            filepath_executable=executable,
            **kwargs,
        )

        return code.store()

    return get_code


@pytest.fixture(scope="function", autouse=True)
def clear_database_auto(clear_database):  # pylint: disable=unused-argument
    """Automatically clear database in between tests."""


@pytest.fixture(scope="function")
def aimall_code(my_aim_code):
    """Get a aimall code."""
    return my_aim_code(
        executable="/Applications/AIMAll/AIMQB.app/Contents/MacOS/aimqb",
        entry_point="aimall",
        label="aimall2",
    )
