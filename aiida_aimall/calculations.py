"""
Calculations provided by aiida_aimall.

Register calculations via the "aiida.calculations" entry point in setup.json.
"""
from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import Dict, SinglefileData
from aiida.plugins import DataFactory

AimqbParameters = DataFactory("aimall")


class AimqbCalculation(CalcJob):
    """
    AiiDA calculation plugin wrapping the aimqb executable.

    AiiDA plugin wrapper for running aimqb on a file
    """

    INPUT_FILE = "aiida.wfx"
    OUTPUT_FILE = "aiida.out"
    PARENT_FOLDER_NAME = "parent_calc"
    DEFAULT_PARSER = "aimqb.base"

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation"""
        super().define(spec)

        # set default values for AiiDA options
        spec.inputs["metadata"]["options"]["resources"].defaults = {
            "num_machines": 1,
            "tot_num_mpiprocs": 2,
        }
        # commented out parser to see default folder structure
        spec.inputs["metadata"]["options"]["parser_name"].default = "aimqb.base"
        # new ports
        # spec.input(
        #     'metadata.options.output_filename', valid_type=str, default='aiida.out'
        # )
        spec.input(
            "parameters",
            valid_type=AimqbParameters,
            help="Command line parameters for aimqb",
        )
        spec.input(
            "file", valid_type=SinglefileData, help="fchk, wfn, or wfx to run AimQB on"
        )
        # commented these to see
        spec.output(
            "atomic_properties",
            valid_type=Dict,
            required=True,
            help="The result parameters of the calculation",
        )
        spec.output(
            "bcp_properties",
            valid_type=Dict,
            required=True,
            help="The properties of all BCPs in the molecule",
        )
        spec.output(
            "cc_properties",
            valid_type=Dict,
            required=False,
            help="The properties of VSCC in the molecule",
        )

        # spec.default_output_node = "output_parameters"
        spec.outputs.dynamic = True

        # would put error codes here

    # ---------------------------------------------------

    def prepare_for_submission(self, folder):
        """Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily
            place all files needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        input_string = self.inputs.file.get_content()
        with open(
            folder.get_abs_path(self.INPUT_FILE), "w", encoding="utf-8"
        ) as out_file:
            out_file.write(input_string)
        codeinfo = datastructures.CodeInfo()
        # probably modify the next line
        codeinfo.cmdline_params = self.inputs.parameters.cmdline_params(
            file_name=self.INPUT_FILE
        )
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.OUTPUT_FILE

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]  # list since can involve more than one

        calcinfo.retrieve_list = [
            self.OUTPUT_FILE.replace("out", "sum"),
            self.OUTPUT_FILE.replace(".out", "_atomicfiles"),
        ]

        return calcinfo
