"""Calculations provided by aiida_aimall.

Upon pip install, AimqbCalculation is accessible in AiiDA.calculations plugins
Using the 'aimall' entry point, and GaussianWFXCalculation is accessible with the 'gaussianwfx'
entry point

"""
from aiida.common import CalcInfo, CodeInfo, datastructures
from aiida.engine import CalcJob, ExitCode
from aiida.orm import (
    Dict,
    Float,
    Int,
    List,
    RemoteData,
    SinglefileData,
    Str,
    StructureData,
)
from aiida.plugins import DataFactory
from pymatgen.io.gaussian import GaussianInput  # pylint: disable=import-error

AimqbParameters = DataFactory("aimall.aimqb")


class AimqbCalculation(CalcJob):
    """AiiDA calculation plugin wrapping the aimqb executable.

    Attributes:
        parameters (AimqbParameters): command line parameters for the AimqbCalculation
        file (SinglefileData): the wfx, wfn, or fchk file to be run

    Example:
        ::

            code = orm.load_code('aimall@localhost')
            AimqbParameters = DataFactory("aimall.aimqb")
            aim_params = AimqbParameters(parameter_dict={"naat": 2, "nproc": 2, "atlaprhocps": True})
            file=SinglefileData(io.BytesIO(file_string.encode()))
            AimqbCalculation = CalculationFactory("aimall.aimqb")
            builder  = AimqbCalculation.get_builder()
            builder.parameters = aim_params
            builder.file = file
            builder.code = code
            builder.metadata.options.resources = {"num_machines": 1, "num_mpiprocs_per_machine": 2}
            builder.submit()

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
            default=Int(1),
        )
        spec.input(
            "group_atoms",
            valid_type=List,
            help="Integer ids of atoms in groups to include",
            default=List([]),
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


class GaussianWFXCalculation(CalcJob):
    """AiiDA calculation plugin wrapping Gaussian

    Adapted from aiida-gaussian https://github.com/nanotech-empa/aiida-gaussian, Copyright (c) 2020 Kristjan Eimre.
    """

    # Defaults
    INPUT_FILE = "aiida.inp"
    OUTPUT_FILE = "aiida.out"
    PARENT_FOLDER_NAME = "parent_calc"
    DEFAULT_PARSER = "aimall.gaussianwfx"

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # Input parameters
        spec.input(
            "structure",
            valid_type=StructureData,
            required=False,
            help="Input structure; will be converted to pymatgen object",
        )
        spec.input(
            "wfxgroup",
            valid_type=Str,
            required=True,
            help="Group label that output wfx will be a member of",
        )
        spec.input("structure_str", valid_type=Str, required=False)
        spec.input(
            "parameters", valid_type=Dict, required=True, help="Input parameters"
        )
        spec.input(
            "settings",
            valid_type=Dict,
            required=False,
            help="additional input parameters",
        )
        spec.input(
            "fragment_label", valid_type=Str, required=False, help="smiles of fragment"
        )
        spec.input(
            "parent_calc_folder",
            valid_type=RemoteData,
            required=False,
            help="the folder of a completed gaussian calculation",
        )

        # Turn mpi off by default
        spec.input("metadata.options.withmpi", valid_type=bool, default=False)

        spec.input(
            "metadata.options.parser_name",
            valid_type=str,
            default=cls.DEFAULT_PARSER,
            non_db=True,
        )

        # Outputs
        spec.output(
            "output_parameters",
            valid_type=Dict,
            required=True,
            help="The result parameters of the calculation",
        )
        spec.output(
            "output_structure",
            valid_type=StructureData,
            required=False,
            help="Final optimized structure, if available",
        )
        spec.output(
            "energy_ev",
            valid_type=Float,
            required=False,
            help="Final energy in electronvolts",
        )
        spec.output(
            "wfx",
            valid_type=SinglefileData,
            required=False,
            help="wfx file from calculation",
        )
        spec.default_output_node = "output_parameters"
        spec.outputs.dynamic = True

        # Exit codes
        spec.exit_code(
            200,
            "ERROR_NO_RETRIEVED_FOLDER",
            message="The retrieved folder data node could not be accessed.",
        )
        spec.exit_code(
            210,
            "ERROR_OUTPUT_MISSING",
            message="The retrieved folder did not contain the output file.",
        )
        spec.exit_code(
            211,
            "ERROR_OUTPUT_LOG_READ",
            message="The retrieved output log could not be read.",
        )
        spec.exit_code(
            220,
            "ERROR_OUTPUT_PARSING",
            message="The output file could not be parsed.",
        )
        spec.exit_code(
            301,
            "ERROR_SCF_FAILURE",
            message="The SCF did not converge and the calculation was terminated.",
        )
        spec.exit_code(
            302,
            "ERROR_ASYTOP",
            message="The calculation was terminated due to a logic error in ASyTop.",
        )
        spec.exit_code(
            303,
            "ERROR_INACCURATE_QUADRATURE_CALDSU",
            message="The calculation was terminated due to an inaccurate quadrature in CalDSu.",
        )
        spec.exit_code(
            390,
            "ERROR_TERMINATION",
            message="The calculation was terminated due to an error.",
        )
        spec.exit_code(
            391,
            "ERROR_NO_NORMAL_TERMINATION",
            message="The log did not contain 'Normal termination' (probably out of time).",
        )
        spec.exit_code(
            410,
            "ERROR_MULTIPLE_INPUT_STRUCTURES",
            message="structure and structure_str were both provided as inputs. provide only one",
        )

    # --------------------------------------------------------------------------
    def prepare_for_submission(self, folder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param folder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        """

        if "structure" in self.inputs and "structure_str" not in self.inputs:
            structure = self.inputs.structure.get_pymatgen_molecule()
        elif "structure" not in self.inputs and "structure_str" in self.inputs:
            structure = self.inputs.structure_str.value
        elif "structure" in self.inputs and "structure_str" in self.inputs:
            return ExitCode(410)
        else:
            # If structure is not specified, it is read from the chk file
            structure = None

        # Generate the input file
        input_string = GaussianWFXCalculation._render_input_string_from_params(
            self.inputs.parameters.get_dict(), structure
        )

        with open(
            folder.get_abs_path(self.INPUT_FILE), "w", encoding="utf-8"
        ) as out_file:
            out_file.write(input_string)

        settings = self.inputs.settings.get_dict() if "settings" in self.inputs else {}

        # create code info
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = settings.pop("cmdline", [])
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdin_name = self.INPUT_FILE
        codeinfo.stdout_name = self.OUTPUT_FILE
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # create calculation info
        calcinfo = CalcInfo()
        calcinfo.remote_copy_list = []
        calcinfo.local_copy_list = []
        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = codeinfo.cmdline_params
        calcinfo.stdin_name = self.INPUT_FILE
        calcinfo.stdout_name = self.OUTPUT_FILE
        calcinfo.codes_info = [codeinfo]
        calcinfo.retrieve_list = [self.OUTPUT_FILE, "output.wfx"]

        # symlink or copy to parent calculation
        calcinfo.remote_symlink_list = []
        calcinfo.remote_copy_list = []
        if "parent_calc_folder" in self.inputs:
            comp_uuid = self.inputs.parent_calc_folder.computer.uuid
            remote_path = self.inputs.parent_calc_folder.get_remote_path()
            copy_info = (comp_uuid, remote_path, self.PARENT_FOLDER_NAME)
            if self.inputs.code.computer.uuid == comp_uuid:
                # if running on the same computer - make a symlink
                # if not - copy the folder
                calcinfo.remote_symlink_list.append(copy_info)
            else:
                calcinfo.remote_copy_list.append(copy_info)

        return calcinfo

    @classmethod
    def _render_input_string_from_params(cls, parameters, structure_string):
        """Generate the Gaussian input file using pymatgen."""
        parameters.setdefault("dieze_tag", "#N")
        parameters.setdefault("spin_multiplicity", parameters.pop("multiplicity", None))
        parameters["title"] = "input generated by the aiida-gaussian plugin"
        gaussian_input = GaussianInput(structure_string, **parameters)
        return gaussian_input.to_str(cart_coords=True)
