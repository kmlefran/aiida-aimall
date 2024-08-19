# pylint: disable=redefined-outer-name,too-many-statements
"""Initialise a text database and profile for pytest."""
import io
import os

# import pathlib
import shutil
from collections.abc import Mapping

import ase.io
import pytest
from aiida.common import AttributeDict
from aiida.orm import (
    Bool,
    Dict,
    FolderData,
    Int,
    List,
    SinglefileData,
    Str,
    StructureData,
)
from aiida_shell import ShellCode

from aiida_aimall.data import AimqbParameters

# import tempfile
# from collections.abc import Mapping


pytest_plugins = ["aiida.tools.pytest_fixtures"]  # pylint: disable=invalid-name


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
def generate_workchain_folderdata():
    """Generate FolderData of an AIM calculation"""

    def _generate_workchain_folderdata(
        entry_point_name="base",
        test_name=None,
    ):
        filepath_folder = None

        if test_name is not None:
            basepath = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(entry_point_name, test_name)
            filepath_folder = os.path.join(basepath, "workchains", "fixtures", filename)
            print(filepath_folder)
        if filepath_folder:
            retrieved = FolderData()
            retrieved.base.repository.put_object_from_tree(filepath_folder)
        return retrieved

    return _generate_workchain_folderdata


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
        test_folder_type="parsers",
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
            filepath_folder = os.path.join(
                basepath, test_folder_type, "fixtures", filename
            )
            filepath_input = os.path.join(filepath_folder, "aiida.in")
        else:
            filepath_input = "notestname"
        entry_point = format_entry_point_string("aiida.calculations", entry_point_name)
        print(filepath_folder)
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
    generate_workchain, generate_calc_job_node, filepath_tests, fixture_code
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
        from plumpy import ProcessState

        entry_point = "aimall.aimreor"

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
                "dry_run": Bool(True),
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


@pytest.fixture
def generate_aimqb_inputs():
    """Generates inputs of a default aimqb calculation"""

    def _generate_aimqb_inputs(fixture_code, filepath_tests):
        """Return only those inputs the parser will expect to be there"""
        parameters = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})
        inputs = {
            "code": fixture_code("aimall"),
            "parameters": parameters,
            "file": SinglefileData(
                os.path.join(
                    filepath_tests,
                    "parsers/inputs",
                    "water_wb97xd_augccpvtz_qtaim.wfx",
                )
            ),
            "metadata": {
                "options": {
                    "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 2},
                }
            },
        }
        return AttributeDict(inputs)

    return _generate_aimqb_inputs


@pytest.fixture
def generate_shelljob_inputs():
    """Generates inputs of a default aimqb calculation"""

    def _generate_shelljob_inputs(fixture_localhost, filepath_tests):
        """Return only those inputs the parser will expect to be there"""
        input_file = SinglefileData(
            os.path.join(
                filepath_tests,
                "workchains/inputs",
                "orca.inp",
            )
        )
        inputs = {
            "code": ShellCode(
                label="orca",
                computer=fixture_localhost,
                filepath_executable="/Applications/orca/orca",
                default_calc_job_plugin="core.shell",
                with_mpi=False,
            ),
            "arguments": Str("{file}"),
            "nodes": {"file": input_file},
            "outputs": List(
                [
                    input_file.filename.replace("inp", "wfx"),
                    input_file.filename.replace("inp", "opt"),
                ]
            ),
            "submit": Bool(False),
            "metadata": {
                "options": {
                    "withmpi": False,
                    "prepend_text": "module load StdEnv/2020; module load gcc/10.3.0 module load openmpi/4.1.1",
                    "resources": {
                        "num_machines": 1,
                        "num_mpiprocs_per_machine": 4,
                    },
                    "max_memory_kb": int(3200 * 1.25) * 1024,
                    "max_wallclock_seconds": 3600,
                }
            },
        }
        return AttributeDict(inputs)

    return _generate_shelljob_inputs


@pytest.fixture
def generate_g16_inputs():
    """Generates inputs of a default aimqb calculation"""

    def _generate_g16_inputs(fixture_code):
        """Return only those inputs the parser will expect to be there"""
        gaussian_input = Dict(
            {
                "link0_parameters": {
                    "%chk": "aiida.chk",
                    "%mem": "3200MB",  # Currently set to use 8000 MB in .sh files
                    "%nprocshared": 4,
                },
                "functional": "wb97xd",
                "basis_set": "aug-cc-pvtz",
                "charge": 0,
                "multiplicity": 1,
                "route_parameters": {"opt": None, "Output": "WFX"},
                "input_parameters": {"output.wfx": None},
            }
        )
        f = io.StringIO(
            "5\n\n C -0.1 2.0 -0.02\nH 0.3 1.0 -0.02\nH 0.3 2.5 0.8\nH 0.3 2.5 -0.9\nH -1.2 2.0 -0.02"
        )
        struct_data = StructureData(ase=ase.io.read(f, format="xyz"))
        f.close()
        inputs = {
            "structure": struct_data,
            "parameters": gaussian_input,
            "code": fixture_code("gaussian"),
            "wfxgroup": Str("testsmi"),
            "fragment_label": Str("*C"),
            "dry_run": Bool(True),
        }
        return AttributeDict(inputs)

    return _generate_g16_inputs


@pytest.fixture
def generate_workchain_smitog16(
    generate_workchain, generate_calc_job_node, fixture_code
):
    """Generate an instance of a ``SmilesToGaussianWorkchain``."""

    def _generate_workchain_smitog16(
        exit_code=None, inputs=None, return_inputs=False, g16_outputs=None
    ):
        """Generate an instance of a ``SmilesToGaussianWorkchain``.

        :param exit_code: exit code for the ``SmilesToGaussianWorkchain``.
        :param inputs: inputs for the ``SmilesToGaussianWorkchain``.
        :param return_inputs: return the inputs of the ``SmilesToGaussianWorkchain``.
        :param pw_outputs: ``dict`` of outputs for the ``GaussianWFXCalculation``. The keys must correspond to the link label
            and the values to the output nodes.
        """
        from aiida.common import LinkType
        from plumpy import ProcessState

        entry_point = "aimall.smitog16"

        if inputs is None:
            gaussian_input = Dict(
                {
                    "link0_parameters": {
                        "%chk": "aiida.chk",
                        "%mem": "3200MB",  # Currently set to use 8000 MB in .sh files
                        "%nprocshared": 4,
                    },
                    "functional": "wb97xd",
                    "basis_set": "aug-cc-pvtz",
                    "charge": 0,
                    "multiplicity": 1,
                    "route_parameters": {"opt": None, "Output": "WFX"},
                    "input_parameters": {"aiida.wfx": None},
                }
            )
            inputs = {
                "smiles": Str("*C"),
                "gaussian_parameters": gaussian_input,
                "gaussian_code": fixture_code("gaussian"),
                # "wfxgroup": Str("testsmi"),
                "nprocs": Int(4),
                "mem_mb": Int(3200),
                "time_s": Int(3600),
                "dry_run": Bool(True),
            }

        if return_inputs:
            return inputs

        process = generate_workchain(entry_point, inputs)

        gaussian_node = generate_calc_job_node(inputs={"parameters": Dict()})
        process.ctx.children = [gaussian_node]

        if g16_outputs is not None:
            for link_label, output_node in g16_outputs.items():
                output_node.base.links.add_incoming(
                    gaussian_node, link_type=LinkType.CREATE, link_label=link_label
                )
                output_node.store()

        if exit_code is not None:
            gaussian_node.set_process_state(ProcessState.FINISHED)
            gaussian_node.set_exit_status(exit_code.status)

        return process

    return _generate_workchain_smitog16


@pytest.fixture
def generate_workchain_subparam(
    generate_workchain, generate_calc_job_node, fixture_code
):
    """Generate an instance of a ``SubstituentParameterWorkChain``."""

    def _generate_workchain_subparam(
        generate_workchain_aimreor,
        exit_code=None,
        inputs=None,
        return_inputs=False,
        aim_outputs=None,
        input_type="structure",
    ):
        """Generate an instance of a ``SubstituentParameterWorkChain``.

        :param exit_code: exit code for the ``SubstituentParameterWorkChain``.
        :param inputs: inputs for the ``SubstituentParameterWorkChain``.
        :param return_inputs: return the inputs of the ``SubstituentParameterWorkChain``.
        :param pw_outputs: ``dict`` of outputs for the ``SubstituentParameterWorkChain``.
            The keys must correspond to the link labels and the values to the output nodes.
        """
        # pylint:disable=too-many-locals,too-many-arguments
        from aiida.common import LinkType
        from plumpy import ProcessState

        entry_point = "aimall.subparam"

        if inputs is None:
            gaussian_opt_input = Dict(
                {
                    "link0_parameters": {
                        "%chk": "aiida.chk",
                        "%mem": "3200MB",  # Currently set to use 8000 MB in .sh files
                        "%nprocshared": 4,
                    },
                    "functional": "wb97xd",
                    "basis_set": "aug-cc-pvtz",
                    "charge": 0,
                    "multiplicity": 1,
                    "route_parameters": {"opt": None, "Output": "WFX"},
                    "input_parameters": {"output.wfx": None},
                }
            )
            gaussian_sp_input = Dict(
                {
                    "link0_parameters": {
                        "%chk": "aiida.chk",
                        "%mem": "3200MB",  # Currently set to use 8000 MB in .sh files
                        "%nprocshared": 4,
                    },
                    "functional": "wb97xd",
                    "basis_set": "aug-cc-pvtz",
                    "charge": 0,
                    "multiplicity": 1,
                    "route_parameters": {"Output": "WFX"},
                    "input_parameters": {"output.wfx": None},
                }
            )
            aiminputs = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})
            inputs = {
                "g16_opt_params": gaussian_opt_input,
                "g16_sp_params": gaussian_sp_input,
                "aim_params": aiminputs,
                "g16_code": fixture_code("gaussian"),
                "frag_label": Str("*C"),
                # "opt_wfx_group": Str("group1"),
                # "sp_wfx_group": Str("group2"),
                # "gaussian_opt_group": Str("group3"),
                # "gaussian_sp_group": Str("group4"),
                "aim_code": fixture_code("aimall"),
                "dry_run": Bool(True),
            }
            if input_type == "structure":
                f = io.StringIO(
                    "5\n\n C -0.1 2.0 -0.02\nH 0.3 1.0 -0.02\nH 0.3 2.5 0.8\nH 0.3 2.5 -0.9\nH -1.2 2.0 -0.02"
                )
                struct_data = StructureData(ase=ase.io.read(f, format="xyz"))
                f.close()

                inputs["structure"] = struct_data
            elif input_type == "smiles":
                inputs["smiles"] = Str("*C")
            elif input_type == "xyz":
                wfx_string = "5\n\n C -0.1 2.0 -0.02\nH 0.3 1.0 -0.02\nH 0.3 2.5 0.8\nH 0.3 2.5 -0.9\nH -1.2 2.0 -0.02"
                xyz_data = SinglefileData(io.BytesIO(wfx_string.encode()))
                inputs["xyz_file"] = xyz_data

        if return_inputs:
            return inputs

        process = generate_workchain(entry_point, inputs)

        gaussian_node = generate_calc_job_node(inputs={"parameters": Dict()})
        gaussian_node2 = generate_calc_job_node(inputs={"parameters": Dict()})
        aim_node = generate_calc_job_node(inputs={"parameters": Dict()})
        aimallreor_node = generate_workchain_aimreor()
        process.ctx.children = [
            gaussian_node,
            aimallreor_node,
            gaussian_node2,
            aim_node,
        ]

        if aim_outputs is not None:
            for link_label, output_node in aim_outputs.items():
                output_node.base.links.add_incoming(
                    aim_node, link_type=LinkType.CREATE, link_label=link_label
                )
                output_node.store()

        if exit_code is not None:
            gaussian_node.set_process_state(ProcessState.FINISHED)
            gaussian_node.set_exit_status(exit_code.status)
            gaussian_node2.set_process_state(ProcessState.FINISHED)
            gaussian_node2.set_exit_status(exit_code.status)
            aimallreor_node.set_process_state(ProcessState.FINISHED)
            aimallreor_node.set_exit_status(exit_code.status)
            aim_node.set_process_state(ProcessState.FINISHED)
            aim_node.set_exit_status(exit_code.status)
        return process

    return _generate_workchain_subparam


@pytest.fixture
def generate_workchain_g16toaim(
    generate_workchain, generate_calc_job_node, fixture_code
):
    """Generate an instance of a ``GaussianToAIMWorkChain``."""

    def _generate_workchain_g16toaim(
        exit_code=None,
        inputs=None,
        return_inputs=False,
        aim_outputs=None,
        input_type="structure",
    ):
        """Generate an instance of a ``GaussianToAIMWorkChain``.

        :param exit_code: exit code for the ``GaussianToAIMWorkChain``.
        :param inputs: inputs for the ``GaussianToAIMWorkChain``.
        :param return_inputs: return the inputs of the ``GaussianToAIMWorkChain``.
        :param pw_outputs: ``dict`` of outputs for the ``GaussianToAIMWorkChain``.
            The keys must correspond to the link labels and the values to the output nodes.
        """
        # pylint:disable=too-many-locals
        from aiida.common import LinkType
        from plumpy import ProcessState

        entry_point = "aimall.g16toaim"

        if inputs is None:
            gaussian_input = Dict(
                {
                    "link0_parameters": {
                        "%chk": "aiida.chk",
                        "%mem": "3200MB",  # Currently set to use 8000 MB in .sh files
                        "%nprocshared": 4,
                    },
                    "functional": "wb97xd",
                    "basis_set": "aug-cc-pvtz",
                    "charge": 0,
                    "multiplicity": 1,
                    "route_parameters": {"opt": None, "Output": "WFX"},
                    "input_parameters": {"output.wfx": None},
                }
            )
            aiminputs = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})
            if input_type == "structure":
                f = io.StringIO(
                    "5\n\n C -0.1 2.0 -0.02\nH 0.3 1.0 -0.02\nH 0.3 2.5 0.8\nH 0.3 2.5 -0.9\nH -1.2 2.0 -0.02"
                )
                struct_data = StructureData(ase=ase.io.read(f, format="xyz"))
                f.close()
                inputs = {
                    "g16_params": gaussian_input,
                    "aim_params": aiminputs,
                    "structure": struct_data,
                    "g16_code": fixture_code("gaussian"),
                    "frag_label": Str("*C"),
                    # "opt_wfx_group": Str("group1"),
                    # "sp_wfx_group": Str("group2"),
                    # "gaussian_opt_group": Str("group3"),
                    # "gaussian_sp_group": Str("group4"),
                    "aim_code": fixture_code("aimall"),
                    "dry_run": Bool(True),
                }
            elif input_type == "xyz":
                wfx_string = "5\n\n C -0.1 2.0 -0.02\nH 0.3 1.0 -0.02\nH 0.3 2.5 0.8\nH 0.3 2.5 -0.9\nH -1.2 2.0 -0.02"
                xyz_data = SinglefileData(io.BytesIO(wfx_string.encode()))
                inputs = {
                    "g16_params": gaussian_input,
                    "aim_params": aiminputs,
                    "xyz_file": xyz_data,
                    "g16_code": fixture_code("gaussian"),
                    "frag_label": Str("*C"),
                    # "opt_wfx_group": Str("group1"),
                    # "sp_wfx_group": Str("group2"),
                    # "gaussian_opt_group": Str("group3"),
                    # "gaussian_sp_group": Str("group4"),
                    "aim_code": fixture_code("aimall"),
                    "dry_run": Bool(True),
                }
            elif input_type == "smiles":
                inputs = {
                    "g16_params": gaussian_input,
                    "aim_params": aiminputs,
                    "smiles": Str("C"),
                    "g16_code": fixture_code("gaussian"),
                    "frag_label": Str("*C"),
                    # "opt_wfx_group": Str("group1"),
                    # "sp_wfx_group": Str("group2"),
                    # "gaussian_opt_group": Str("group3"),
                    # "gaussian_sp_group": Str("group4"),
                    "aim_code": fixture_code("aimall"),
                    "dry_run": Bool(True),
                }
        if return_inputs:
            return inputs

        process = generate_workchain(entry_point, inputs)

        gaussian_node = generate_calc_job_node(inputs={"parameters": Dict()})

        aim_node = generate_calc_job_node(inputs={"parameters": Dict()})

        process.ctx.children = [
            gaussian_node,
            aim_node,
        ]

        if aim_outputs is not None:
            for link_label, output_node in aim_outputs.items():
                output_node.base.links.add_incoming(
                    aim_node, link_type=LinkType.CREATE, link_label=link_label
                )
                output_node.store()

        if exit_code is not None:
            gaussian_node.set_process_state(ProcessState.FINISHED)
            gaussian_node.set_exit_status(exit_code.status)
            aim_node.set_process_state(ProcessState.FINISHED)
            aim_node.set_exit_status(exit_code.status)
        return process

    return _generate_workchain_g16toaim


@pytest.fixture
def generate_workchain_qmtoaim(
    generate_workchain, generate_calc_job_node, filepath_tests, fixture_code
):
    """Generate an instance of a ``QMToAIMWorkchain``."""

    def _generate_workchain_qmtoaim(
        exit_code=None, inputs=None, return_inputs=False, shell_outputs=None
    ):
        """Generate an instance of a ``QMToAIMWorkchain``.

        :param exit_code: exit code for the ``QMToAIMWorkchain``.
        :param inputs: inputs for the ``QMToAIMWorkchain``.
        :param return_inputs: return the inputs of the ``QMToAIMWorkchain``.
        :param pw_outputs: ``dict`` of outputs for the ``QMToAIMWorkchain``. The keys must correspond to the link labels
            and the values to the output nodes.
        """
        from aiida.common import LinkType
        from plumpy import ProcessState

        entry_point = "aimall.qmtoaim"

        if inputs is None:
            shell_metadata = Dict(
                {
                    "options": {
                        "withmpi": False,
                        "prepend_text": "module load StdEnv/2020; module load gcc/10.3.0 module load openmpi/4.1.1",
                        "resources": {
                            "num_machines": 1,
                            "num_mpiprocs_per_machine": 4,
                        },
                        "max_memory_kb": int(3200 * 1.25) * 1024,
                        "max_wallclock_seconds": 3600,
                    }
                }
            )

            aimreor_inputs = AimqbParameters({"naat": 2, "nproc": 2})
            input_file = SinglefileData(
                os.path.join(
                    filepath_tests,
                    "workchains/inputs",
                    "orca.inp",
                )
            )
            inputs = {
                "shell_metadata": shell_metadata,
                "shell_retrieved": List(
                    [
                        input_file.filename.replace("inp", "wfx"),
                        input_file.filename.replace("inp", "opt"),
                    ]
                ),
                "shell_input_file": input_file,
                "shell_cmdline": Str("{file}"),
                "shell_code": Str("orca"),
                "aim_code": fixture_code("aimall"),
                "aim_params": aimreor_inputs,
                "dry_run": Bool(True),
            }

        if return_inputs:
            return inputs

        process = generate_workchain(entry_point, inputs)

        shell_node = generate_calc_job_node(inputs={"parameters": Dict()})
        process.ctx.children = [shell_node]

        if shell_outputs is not None:
            for link_label, output_node in shell_outputs.items():
                output_node.base.links.add_incoming(
                    shell_node, link_type=LinkType.CREATE, link_label=link_label
                )
                output_node.store()

        if exit_code is not None:
            shell_node.set_process_state(ProcessState.FINISHED)
            shell_node.set_exit_status(exit_code.status)

        return process

    return _generate_workchain_qmtoaim
