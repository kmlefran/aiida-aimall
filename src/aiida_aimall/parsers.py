# pylint:disable=too-many-function-args
"""
Parsers provided by aiida_aimall.

Register parsers via the "aiida.parsers" entry point in pyproject.toml.
"""

import numpy as np
import pandas as pd
from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict, SinglefileData
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory, DataFactory
from subproptools import qtaim_extract as qt  # pylint: disable=import-error

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

        def make_serializeable(data):
            """Recursively go through the dictionary and convert unserializeable values in-place:

            1) In numpy arrays:
                * ``nan`` -> ``0.0``
                * ``inf`` -> large number

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
            elif (
                not isinstance(data, dict)
                and not isinstance(data, np.ndarray)
                and not isinstance(data, list)
                and not isinstance(data, pd.DataFrame)
            ):
                if np.isnan(data):
                    data = np.nan_to_num(data)
            return data

        make_serializeable(out_dict)
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
