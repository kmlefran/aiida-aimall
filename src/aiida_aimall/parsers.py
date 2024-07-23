# pylint:disable=too-many-function-args
"""
Parsers provided by aiida_aimall.

Register parsers via the "aiida.parsers" entry point in setup.json.
"""
import datetime
import io
import re

import ase  # pylint:disable=import-error
import cclib  # pylint:disable=import-error
import numpy as np
from aiida.common import NotExistent, exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict, Float, SinglefileData, StructureData, load_group
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory, DataFactory
from subproptools import qtaim_extract as qt  # pylint: disable=import-error

# from aiida.engine import ExitCode


AimqbCalculation = CalculationFactory("aimall.aimqb")


class AimqbBaseParser(Parser):
    """
    Parser class for parsing output of calculation.
    """

    def __init__(self, node):
        """
        Initialize Parser instance

        Checks that the ProcessNode being passed was produced by a AimqbCalculation.

        :param node: ProcessNode of calculation
        :param type node: :class:`aiida.orm.nodes.process.process.ProcessNode`
        """
        super().__init__(node)
        if not issubclass(node.process_class, AimqbCalculation):
            raise exceptions.ParsingError("Can only parse AimqbCalculation")

    def parse(self, **kwargs):
        """Parse outputs, store results in database.

        :returns: an exit code, if parsing fails (or nothing if parsing succeeds)
        """
        # convenience method to get filename of output file
        # output_filename = self.node.get_option("output_filename")
        input_parameters = self.node.inputs.parameters
        output_filename = self.node.process_class.OUTPUT_FILE

        # Check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = [
            output_filename.replace("out", "sum"),
            output_filename.replace(".out", "_atomicfiles"),
        ]
        # Note: set(A) <= set(B) checks whether A is a subset of B
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(
                f"Found files '{files_retrieved}', expected to find '{files_expected}'"
            )
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        # parse output file
        self.logger.info(f"Parsing '{output_filename}'")
        OutFolderData = self.retrieved
        with OutFolderData.open(output_filename.replace("out", "sum"), "rb") as handle:
            output_node = SinglefileData(file=handle)
            sum_lines = output_node.get_content()
            out_dict = {
                "atomic_properties": self._parse_atomic_props(sum_lines),
                "bcp_properties": self._parse_bcp_props(sum_lines),
                "ldm": self._parse_ldm(sum_lines),
            }
        # if laprhocps were calculated, get cc_properties
        if "-atlaprhocps=True" in input_parameters.cmdline_params("foo"):
            out_dict["cc_properties"] = self._parse_cc_props(
                out_dict["atomic_properties"]
            )
        # store in node
        self.outputs.output_parameters = Dict(out_dict)

        return ExitCode(0)

    def _parse_ldm(self, sum_lines):
        return qt.get_ldm(sum_lines.split("\n"))

    def _parse_cc_props(self, atomic_properties):
        """Extract VSCC properties from output files
        :param atomic_properties: dictionary of atomic properties from _parse_atomic_props
        :param type atomic_properties: dict
        """
        output_filename = self.node.process_class.OUTPUT_FILE
        atom_list = list(atomic_properties.keys())
        # for each atom, load the .agpviz file in the _atomicfiles folder and get cc props
        cc_dict = {
            x: qt.get_atom_vscc(
                filename=self.retrieved.get_object_content(
                    output_filename.replace(".out", "_atomicfiles")
                    + "/"
                    + x.lower()
                    + ".agpviz"
                ).split("\n"),
                atomLabel=x,
                atomicProps=atomic_properties,
                is_lines_data=True,
            )
            for x in atom_list
        }
        return cc_dict

    def _parse_atomic_props(self, sum_file_string):
        """Extracts atomic properties from .sum file

        :param sum_file_string: lines of .sum output file
        :param type sum_file_string: str
        """
        return qt.get_atomic_props(sum_file_string.split("\n"))

    def _parse_bcp_props(self, sum_file_string):
        """Extracts bcp properties from .sum file

        :param sum_file_string: lines of .sum output file
        :param type sum_file_string: str
        """
        bcp_list = qt.find_all_connections(sum_file_string.split("\n"))
        return qt.get_selected_bcps(sum_file_string.split("\n"), bcp_list)


NUM_RE = r"[-+]?(?:[0-9]*[.])?[0-9]+(?:[eE][-+]?\d+)?"

SinglefileData = DataFactory("core.singlefile")


class GaussianWFXParser(Parser):
    """
    Basic AiiDA parser for the output of Gaussian

    Parses default cclib output as 'output_parameters' node and separates final SCF
    energy as 'energy_ev' and output structure as 'output_structure' (if applicable)

    Adapted from aiida-gaussian https://github.com/nanotech-empa/aiida-gaussian, Copyright (c) 2020 Kristjan Eimre.

    """

    def parse(self, **kwargs):
        """Receives in input a dictionary of retrieved nodes. Does all the logic here."""
        fname = self.node.process_class.OUTPUT_FILE

        try:
            out_folder = self.retrieved
            if fname not in out_folder.base.repository.list_object_names():
                return self.exit_codes.ERROR_OUTPUT_MISSING
            log_file_string = out_folder.base.repository.get_object_content(fname)
            log_file_string = log_file_string.replace("Apple", "")
            if "output.wfx" in out_folder.base.repository.list_object_names():
                wfx_file_string = out_folder.base.repository.get_object_content(
                    "output.wfx"
                )
                sfd = SinglefileData(io.BytesIO(wfx_file_string.encode()))
                sfd.store()
                if "wfxgroup" in self.node.inputs:
                    out_group = load_group(self.node.inputs.wfxgroup.value)
                    out_group.add_nodes(sfd)
                if "fragment_label" in self.node.inputs:
                    sfd.base.extras.set("smiles", self.node.inputs.fragment_label.value)
                self.out("wfx", sfd)
        except NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER
        except OSError:
            return self.exit_codes.ERROR_OUTPUT_LOG_READ

        exit_code = self._parse_log(log_file_string, self.node.inputs)

        if exit_code is not None:
            return exit_code

        return ExitCode(0)

    def _parse_log(self, log_file_string, inputs):

        # parse with cclib
        property_dict = self._parse_log_cclib(log_file_string)

        if property_dict is None:
            return self.exit_codes.ERROR_OUTPUT_PARSING

        property_dict.update(self._parse_electron_numbers(log_file_string))

        # set output nodes
        self.out("output_parameters", Dict(dict=property_dict))

        if "scfenergies" in property_dict:
            self.out("energy_ev", Float(property_dict["scfenergies"][-1]))

        self._set_output_structure(inputs, property_dict)

        exit_code = self._final_checks_on_log(log_file_string, property_dict, inputs)
        if exit_code is not None:
            return exit_code

        return None

    def _parse_electron_numbers(self, log_file_string):

        find_el = re.search(
            r"({0})\s*alpha electrons\s*({0}) beta".format(  # pylint:disable=consider-using-f-string
                NUM_RE
            ),  # pylint:disable=consider-using-f-string
            log_file_string,  # pylint:disable=consider-using-f-string
        )

        if find_el is not None:
            return {"num_electrons": [int(e) for e in find_el.groups()]}
        return {}

    def _parse_log_cclib(self, log_file_string):

        data = cclib.io.ccread(io.StringIO(log_file_string))

        if data is None:
            return None

        property_dict = data.getattributes()

        def make_serializeable(data):
            """Recursively go through the dictionary and convert unserializeable values in-place:

            1) In numpy arrays:
                * ``nan`` -> ``0.0``
                * ``inf`` -> large number
            2) datetime.timedelta (introduced in cclib v1.8) -> convert to seconds

            :param data: A mapping of data.
            """
            if isinstance(data, dict):
                for key, value in data.items():
                    data[key] = make_serializeable(value)
            elif isinstance(data, list):
                for index, item in enumerate(data):
                    data[index] = make_serializeable(item)
            elif isinstance(data, np.ndarray):
                np.nan_to_num(data, copy=False)
            elif isinstance(data, datetime.timedelta):
                data = data.total_seconds()
            return data

        make_serializeable(property_dict)

        return property_dict

    def _set_output_structure(self, inputs, property_dict):
        # in case of geometry optimization,
        # return the last geometry as a separated node
        if "atomcoords" in property_dict:
            if (
                "opt" in inputs.parameters["route_parameters"]
                or len(property_dict["atomcoords"]) > 1
            ):

                opt_coords = property_dict["atomcoords"][-1]

                # The StructureData output node needs a cell,
                # even though it is not used in gaussian.
                # Set it arbitrarily as double the bounding box + 10
                double_bbox = 2 * np.ptp(opt_coords, axis=0) + 10

                ase_opt = ase.Atoms(
                    property_dict["atomnos"],
                    positions=property_dict["atomcoords"][-1],
                    cell=double_bbox,
                )

                structure = StructureData(ase=ase_opt)
                self.out("output_structure", structure)

    def _final_checks_on_log(self, log_file_string, property_dict, inputs):
        # pylint:disable=too-many-return-statements
        # if opt and freq in route parameters
        # make an extra check that in log file string there should be normal termination
        # Error related to the symmetry identification (?).

        if "Logic error in ASyTop." in log_file_string:
            return self.exit_codes.ERROR_ASYTOP

        if "Inaccurate quadrature in CalDSu." in log_file_string:
            return self.exit_codes.ERROR_INACCURATE_QUADRATURE_CALDSU

        if "Convergence failure -- run terminated." in log_file_string:
            return self.exit_codes.ERROR_SCF_FAILURE

        if "Error termination" in log_file_string:
            return self.exit_codes.ERROR_TERMINATION

        if (
            "opt" in inputs.parameters["route_parameters"]
            and "freq" in inputs.parameters["route_parameters"]
        ):
            if log_file_string.count("Normal termination") != 2:
                return self.exit_codes.ERROR_NO_NORMAL_TERMINATION

        if (
            "success" not in property_dict["metadata"]
            or not property_dict["metadata"]["success"]
        ):
            return self.exit_codes.ERROR_NO_NORMAL_TERMINATION

        return None


class AimqbGroupParser(AimqbBaseParser):
    """
    Parser class for parsing output of calculation.
    """

    def parse(self, **kwargs):
        """Parse outputs, store results in database.

        :returns: an exit code, if parsing fails (or nothing if parsing succeeds)
        """
        # convenience method to get filename of output file
        # output_filename = self.node.get_option("output_filename")
        input_parameters = self.node.inputs.parameters
        output_filename = self.node.process_class.OUTPUT_FILE

        # Check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = [
            output_filename.replace("out", "sum"),
            output_filename.replace(".out", "_atomicfiles"),
        ]
        # Note: set(A) <= set(B) checks whether A is a subset of B
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(
                f"Found files '{files_retrieved}', expected to find '{files_expected}'"
            )
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES
            # return

        # parse output file
        self.logger.info(f"Parsing '{output_filename}'")
        OutFolderData = self.retrieved
        with OutFolderData.open(output_filename.replace("out", "sum"), "rb") as handle:
            output_node = SinglefileData(file=handle)
            sum_lines = output_node.get_content()
            out_dict = {
                "atomic_properties": self._parse_atomic_props(sum_lines),
                "bcp_properties": self._parse_bcp_props(sum_lines),
                # "ldm": self._parse_ldm(sum_lines),
            }
        # if laprhocps were calculated, get cc_properties
        if "-atlaprhocps=True" in input_parameters.cmdline_params("foo"):
            out_dict["cc_properties"] = self._parse_cc_props(
                out_dict["atomic_properties"]
            )
        out_dict["graph_descriptor"] = self._parse_graph_descriptor(out_dict)
        # store in node
        if self.node.inputs.group_atoms.get_list():
            group_nums = self.node.inputs.group_atoms.get_list()

            out_dict["group_descriptor"] = self._parse_group_descriptor(
                out_dict["atomic_properties"], group_nums
            )
        else:  # default to using only atom # 2 as the substrate
            num_ats = len(out_dict["atomic_properties"])
            group_nums = [x + 1 for x in range(num_ats) if x != 1]
            out_dict["group_descriptor"] = self._parse_group_descriptor(
                out_dict["atomic_properties"], group_nums
            )
        self.outputs.output_parameters = Dict(out_dict)

        return ExitCode(0)

    def _parse_graph_descriptor(self, out_dict):
        """Get atomic, BCP, and VSCC properties of atom 1"""
        graph_dict = {}
        at_id = self.node.inputs.attached_atom_int.value
        # Find the atom property dictionary corresponding to the attached atom
        # Also add the atomic symbol to the property dictionary
        for key, value in out_dict["atomic_properties"].items():
            at_num = int("".join(x for x in key if x.isdigit()))
            if at_num == at_id:
                graph_dict["attached_atomic_props"] = value
                graph_dict["attached_atomic_props"]["symbol"] = "".join(
                    x for x in key if not x.isdigit()
                )
                break
        graph_dict["attached_bcp_props"] = {}
        for key, value in out_dict["bcp_properties"].items():
            num_bond = "".join(x for x in key if x.isdigit() or x == "-")
            at_nums = num_bond.split("-")
            if str(at_id) in at_nums:
                graph_dict["attached_bcp_props"][key] = value
        if "cc_properties" in list(out_dict.keys()):
            for key, value in out_dict["cc_properties"].items():
                at_num = int("".join(x for x in key if x.isdigit()))
                if at_num == at_id:
                    graph_dict["attached_cc_props"] = value
                    graph_dict["attached_cc_props"]["symbol"] = "".join(
                        x for x in key if not x.isdigit()
                    )
                    break
        return graph_dict

    def _parse_group_descriptor(self, atomic_properties, sub_atom_ints):
        """Convert atomic properties to group properties given atoms in group to use"""
        atoms = list(atomic_properties.keys())
        return qt.get_sub_props(atomic_properties, sub_atom_ints, atoms)
