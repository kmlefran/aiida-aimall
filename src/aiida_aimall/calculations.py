"""`CalcJob` implementation for the aimqb executable of AIMAll."""
from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import Dict, Int, List, SinglefileData
from aiida.plugins import DataFactory

AimqbParameters = DataFactory("aimall.aimqb")


class AimqbCalculation(CalcJob):
    """AiiDA calculation plugin wrapping the aimqb executable.

    Attributes:
        parameters (AimqbParameters): command line parameters for the AimqbCalculation
        file (SinglefileData): the wfx, wfn, or fchk file to be run
        code (Code): code of the AIMQB executable
        attached_atom_int (Int): the integer label of the atom in the group that is attached to the rest of the molecule
        group_atoms (List(Int)): integer ids of atoms comprising the group for AimqbGroupParser

    Example:
        ::

            code = orm.load_code('aimall@localhost')
            AimqbParameters = DataFactory("aimall.aimqb")
            aim_params = AimqbParameters(parameter_dict={"naat": 2, "nproc": 2, "atlaprhocps": True})
            file = SinglefileData("/absolute/path/to/file")
            # Alternatively, if you have the file as a string, you can build the file with:
            # file=SinglefileData(io.BytesIO(file_string.encode()))
            AimqbCalculation = CalculationFactory("aimall.aimqb")
            builder  = AimqbCalculation.get_builder()
            builder.parameters = aim_params
            builder.file = file
            builder.code = code
            builder.metadata.options.resources = {"num_machines": 1, "num_mpiprocs_per_machine": 2}
            builder.submit()

    Note:
        By default, the AimqbBaseParser is used, getting atomic, BCP, and (if applicable) LapRhoCps.
            You can opt to use the AimqbGroupParser, which also returns the integrated group properties model
            of a group, as well as the atomic graph descriptor of the group. This is done by providing this to the builder:

        ::

            builder.metadata.options.parser_name = "aimall.group"

    """

    INPUT_FILE = "aiida.wfx"
    OUTPUT_FILE = "aiida.out"
    PARENT_FOLDER_NAME = "parent_calc"
    DEFAULT_PARSER = "aimall.base"

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation"""
        super().define(spec)

        # set default values for AiiDA options
        spec.inputs["metadata"]["options"]["resources"].defaults = {
            "num_machines": 1,
            "tot_num_mpiprocs": 2,
        }

        spec.inputs["metadata"]["options"]["parser_name"].default = "aimall.base"
        # new ports
        # spec.input(
        #     'metadata.options.output_filename', valid_type=str, default='aiida.out'
        # )
        spec.input(
            "attached_atom_int",
            valid_type=Int,
            help="id # of attached atom for graph descriptor",
            default=lambda: Int(1),
        )
        spec.input(
            "group_atoms",
            valid_type=List,
            help="Integer ids of atoms in groups to include",
            default=lambda: List([]),
        )
        spec.input(
            "parameters",
            valid_type=AimqbParameters,
            help="Command line parameters for aimqb",
        )
        spec.input(
            "file",
            valid_type=SinglefileData,
            help="fchk, wfn, or wfx to run AimQB on",
        )

        spec.output(
            "output_parameters",
            valid_type=Dict,
            required=True,
            help="The computed parameters of an AIMAll calculation",
        )

        spec.default_output_node = "output_parameters"
        spec.exit_code(
            210,
            "ERROR_MISSING_OUTPUT_FILES",
            message="The retrieved folder did not contain the output file.",
        )
        spec.outputs.dynamic = True

        # would put error codes here

    # ---------------------------------------------------

    def prepare_for_submission(self, folder):
        """Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily
            place all files needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        # copy wfx file to input file
        input_string = self.inputs.file.get_content()
        with open(
            folder.get_abs_path(self.INPUT_FILE), "w", encoding="utf-8"
        ) as out_file:
            out_file.write(input_string)
        codeinfo = datastructures.CodeInfo()
        # generate command line params
        codeinfo.cmdline_params = self.inputs.parameters.cmdline_params(
            file_name=self.INPUT_FILE
        )
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.OUTPUT_FILE

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]  # list since can involve more than one
        # Retrieve the sum file and the folder with atomic files
        calcinfo.retrieve_list = [
            self.OUTPUT_FILE.replace("out", "sum"),
            self.OUTPUT_FILE.replace(".out", "_atomicfiles"),
        ]

        return calcinfo
