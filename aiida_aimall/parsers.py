"""
Parsers provided by aiida_aimall.

Register parsers via the "aiida.parsers" entry point in setup.json.
"""

from subproptools import qtaim_extract as qt  # pylint: disable=import-error

from aiida.common import exceptions
from aiida.orm import Dict, SinglefileData
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory

# from aiida.engine import ExitCode


AimqbCalculation = CalculationFactory("aimall")


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
            # return self.exit_codes.ERROR_MISSING_OUTPUT_FILES
            return

        # parse output file
        self.logger.info(f"Parsing '{output_filename}'")
        OutFolderData = self.retrieved
        with OutFolderData.open(output_filename.replace("out", "sum"), "rb") as handle:
            output_node = SinglefileData(file=handle)
            sum_lines = output_node.get_content()
            out_dict = {
                "atomic_properties": self._parse_atomic_props(sum_lines),
                "bcp_properties": self._parse_bcp_props(sum_lines),
            }
        # if laprhocps were calculated, get cc_properties
        if "-atlaprhocps=True" in input_parameters.cmdline_params("foo"):
            out_dict["cc_properties"] = self._parse_cc_props(
                out_dict["atomic_properties"]
            )
        # store in node
        self.outputs.output_parameters = Dict(out_dict)

        return  # ExitCode(0)

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
