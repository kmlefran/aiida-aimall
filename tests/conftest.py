# pylint: disable=redefined-outer-name,too-many-statements
"""Initialise a text database and profile for pytest."""
import io
import os

# import pathlib
import shutil
from collections.abc import Mapping

import pytest
from aiida.orm import SinglefileData, Str

from aiida_aimall.data import AimqbParameters

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


@pytest.fixture
def generate_calc_job():
    """Fixture to construct a new `CalcJob` instance and call `prepare_for_submission` for testing `CalcJob` classes.

    The fixture will return the `CalcInfo` returned by `prepare_for_submission` and the temporary folder that was passed
    to it, into which the raw input files will have been written.
    """

    def _generate_calc_job(folder, entry_point_name, inputs=None):
        """Fixture to generate a mock `CalcInfo` for testing calculation jobs."""
        from aiida.engine.utils import instantiate_process
        from aiida.manage.manager import get_manager
        from aiida.plugins import CalculationFactory

        manager = get_manager()
        runner = manager.get_runner()

        process_class = CalculationFactory(entry_point_name)
        process = instantiate_process(runner, process_class, **inputs)

        calc_info = process.prepare_for_submission(folder)

        return calc_info

    return _generate_calc_job


@pytest.fixture(scope="session")
def generate_parser():
    """Fixture to load a parser class for testing parsers."""

    def _generate_parser(entry_point_name):
        """Fixture to load a parser class for testing parsers.

        :param entry_point_name: entry point name of the parser class
        :return: the `Parser` sub class
        """
        from aiida.plugins import ParserFactory

        return ParserFactory(entry_point_name)

    return _generate_parser


@pytest.fixture
def generate_calc_job_node(fixture_localhost):
    """Generate a mock `CalcJobNode` for testing parsers"""

    def flatten_inputs(inputs, prefix=""):
        flat_inputs = []
        for key, value in inputs.items():
            if isinstance(value, Mapping):
                flat_inputs.extend(flatten_inputs(value, prefix=prefix + key + "__"))
            else:
                flat_inputs.append((prefix + key, value))
        return flat_inputs

    def _generate_calc_job_node(  # pylint:disable=too-many-arguments
        entry_point_name="base",
        computer=None,
        test_name=None,
        inputs=None,
        attributes=None,
        retrieve_temporary=None,
    ):
        """Fixture to generate a mock `CalcJobNode` for testing parsers.

        :param entry_point_name: entry point name of the calculation class
        :param computer: a `Computer` instance
        :param test_name: relative path of directory with test output files in the `fixtures/{entry_point_name}` folder.
        :param inputs: any optional nodes to add as input links to the corrent CalcJobNode
        :param attributes: any optional attributes to set on the node
        :param retrieve_temporary: optional tuple of an absolute filepath of a temporary directory and a list of
            filenames that should be written to this directory, which will serve as the `retrieved_temporary_folder`.
            For now this only works with top-level files and does not support files nested in directories.
        :return: `CalcJobNode` instance with an attached `FolderData` as the `retrieved` node.
        """
        # pylint:disable=too-many-locals too-many-branches
        from aiida import orm
        from aiida.common import LinkType
        from aiida.plugins.entry_point import format_entry_point_string

        if computer is None:
            computer = fixture_localhost

        filepath_folder = None

        if test_name is not None:
            basepath = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(entry_point_name, test_name)
            filepath_folder = os.path.join(basepath, "parsers", "fixtures", filename)
            filepath_input = os.path.join(filepath_folder, "aiida.in")

        entry_point = format_entry_point_string("aiida.calculations", entry_point_name)

        node = orm.CalcJobNode(computer=computer, process_type=entry_point)
        node.base.attributes.set("input_filename", "aiida.in")
        node.base.attributes.set("output_filename", "aiida.out")
        node.base.attributes.set("error_filename", "aiida.err")
        node.set_option("resources", {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        node.set_option("max_wallclock_seconds", 1800)

        if attributes:
            node.base.attributes.set_many(attributes)

        if filepath_folder:

            try:
                with open(filepath_input, encoding="utf-8") as input_file:
                    wfxstr = input_file.readlines()
                    strtoencode = ""
                    for line in wfxstr:
                        strtoencode = strtoencode + line
            except FileNotFoundError:
                pass
            else:
                inputs["structure"] = orm.SinglefileData(
                    io.BytesIO(strtoencode.encode())
                )

        if inputs:
            metadata = inputs.pop("metadata", {})
            options = metadata.get("options", {})

            for name, option in options.items():
                node.set_option(name, option)

            for link_label, input_node in flatten_inputs(inputs):
                input_node.store()
                node.base.links.add_incoming(
                    input_node, link_type=LinkType.INPUT_CALC, link_label=link_label
                )

        node.store()

        if retrieve_temporary:
            dirpath, filenames = retrieve_temporary
            for filename in filenames:
                try:
                    shutil.copy(
                        os.path.join(filepath_folder, filename),
                        os.path.join(dirpath, filename),
                    )
                except FileNotFoundError:
                    pass  # To test the absence of files in the retrieve_temporary folder

        if filepath_folder:
            retrieved = orm.FolderData()
            retrieved.base.repository.put_object_from_tree(filepath_folder)

            # Remove files that are supposed to be only present in the retrieved temporary folder
            if retrieve_temporary:
                for filename in filenames:
                    try:
                        retrieved.base.repository.delete_object(filename)
                    except OSError:
                        pass  # To test the absence of files in the retrieve_temporary folder

            retrieved.base.links.add_incoming(
                node, link_type=LinkType.CREATE, link_label="retrieved"
            )
            retrieved.store()

            remote_folder = orm.RemoteData(computer=computer, remote_path="/tmp")
            remote_folder.base.links.add_incoming(
                node, link_type=LinkType.CREATE, link_label="remote_folder"
            )
            remote_folder.store()

        return node

    return _generate_calc_job_node


@pytest.fixture
def generate_workchain():
    """Generate an instance of a `WorkChain`."""

    def _generate_workchain(entry_point, inputs):
        """Generate an instance of a `WorkChain` with the given entry point and inputs.

        :param entry_point: entry point name of the work chain subclass.
        :param inputs: inputs to be passed to process construction.
        :return: a `WorkChain` instance.
        """
        from aiida.engine.utils import instantiate_process
        from aiida.manage.manager import get_manager
        from aiida.plugins import WorkflowFactory

        process_class = WorkflowFactory(entry_point)
        runner = get_manager().get_runner()
        process = instantiate_process(runner, process_class, **inputs)

        return process

    return _generate_workchain


@pytest.fixture
def generate_workchain_aimreor(
    generate_workchain, generate_calc_job_node, filepath_tests
):
    """Generate an instance of a ``AimReorWorkChain``."""

    def _generate_workchain_aimreor(
        exit_code=None, inputs=None, return_inputs=False, aimqb_outputs=None
    ):
        """Generate an instance of a ``AimReorWorkChain``.

        :param exit_code: exit code for the ``AimqbCalculation``.
        :param inputs: inputs for the ``AimReorWorkChain``.
        :param return_inputs: return the inputs of the ``PwBaseWorkChain``.
        :param pw_outputs: ``dict`` of outputs for the ``PwCalculation``. The keys must correspond to the link labels
            and the values to the output nodes.
        """
        from aiida.common import LinkType
        from aiida.orm import Dict
        from plumpy import ProcessState

        entry_point = "aimreor"

        if inputs is None:
            aimreor_inputs = AimqbParameters({"naat": 2, "nproc": 2})
            inputs = {
                "aim_params": aimreor_inputs,
                "file": SinglefileData(
                    os.path.join(
                        filepath_tests,
                        "workchains/inputs",
                        "water_wb97xd_augccpvtz_qtaim.wfx",
                    )
                ),
                "aim_code": fixture_code("aimall"),
                "frag_label": Str("Water"),
            }

        if return_inputs:
            return inputs

        process = generate_workchain(entry_point, inputs)

        aimqb_node = generate_calc_job_node(inputs={"parameters": Dict()})
        process.ctx.children = [aimqb_node]

        if aimqb_outputs is not None:
            for link_label, output_node in aimqb_outputs.items():
                output_node.base.links.add_incoming(
                    aimqb_node, link_type=LinkType.CREATE, link_label=link_label
                )
                output_node.store()

        if exit_code is not None:
            aimqb_node.set_process_state(ProcessState.FINISHED)
            aimqb_node.set_exit_status(exit_code.status)

        return process

    return _generate_workchain_aimreor
