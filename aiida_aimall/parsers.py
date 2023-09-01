"""
Parsers provided by aiida_aimall.

Register parsers via the "aiida.parsers" entry point in setup.json.
"""
from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import SinglefileData
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory
import io
import re
from subproptools import qtaimExtract as qt

AimqbCalculation = CalculationFactory("aimall")


class AimqbBaseParser(Parser):
    """
    Parser class for parsing output of calculation.
    """
    #before parser called, self.retrieved - isntance of FolderData of output files that CalcJob instructed to receive
    #provides means to open any file it contains
    #self.node - the calcjobNode representing the finished calculation
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
        """
        Parse outputs, store results in database.

        :returns: an exit code, if parsing fails (or nothing if parsing succeeds)
        """
        #convenience method to get filename of output file
        # output_filename = self.node.get_option("output_filename")
        
        output_filename = self.node.process_class.OUTPUT_FILE

        # Check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = [output_filename.replace('out','sum'),output_filename.replace('.out','_atomicfiles')]
        # Note: set(A) <= set(B) checks whether A is a subset of B
        print(files_retrieved)
        print(files_expected)
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(
                f"Found files '{files_retrieved}', expected to find '{files_expected}'"
            )
            # return self.exit_codes.ERROR_MISSING_OUTPUT_FILES
            return

        # add output file
        self.logger.info(f"Parsing '{output_filename}'")
        with self.retrieved.open(output_filename.replace('out','sum'), "rb") as handle:
            output_node = SinglefileData(file=handle)
            sum_lines = output_node.get_content()
            self.outputs.atomic_properties = self._parse_atomic_props(sum_lines)
            self.outputs.bcp_properties = self._parse_bcp_props(sum_lines)
        #first argument is name for link that connects calculation and data node
        #second argument is node that should be recorded as output
        # self.out("aimall", output_node)

        return ExitCode(0)
    
    def _parse_atomic_props(self, sum_file_string):
        return qt.get_atomic_props(sum_file_string.split('\n'))
    
    def _parse_bcp_props(self, sum_file_string):
        bcp_list = qt._find_all_connections(sum_file_string)
        return qt.get_bcp_properties(sum_file_string,bcp_list)
        
