"""
Calculations provided by aiida_aimall.

Register calculations via the "aiida.calculations" entry point in setup.json.
"""
from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import SinglefileData, Dict
from aiida.plugins import DataFactory


AimqbParameters = DataFactory('aimall')

class AimqbCalculation(CalcJob):
    """
    AiiDA calculation plugin wrapping the aimqb executable.

    AiiDA plugin wrapper for running aimqb on a file
    """
    INPUT_FILE = "aiida.inp"
    OUTPUT_FILE = "aiida.out"
    PARENT_FOLDER_NAME = "parent_calc"
    DEFAULT_PARSER = "aimqb.base"

    @classmethod
    def define(cls,spec):
        """Define inputs and outputs of the calculation"""
        super().define(spec)

        #set default values for AiiDA options
        spec.inputs['metadata']['options']['resources'].defaults = {
            'num_machines':1,
            'num_mpiprocs_per_machine': 1,
        }
        #commented out parser to see default folder structure
        # spec.inputs["metadata"]["options"]["parser_name"].default = "aimall.base"
        #new ports
        spec.input(
            'metadata.options.output_filename', valid_type=str, default='aiida.out'
        )
        spec.input(
            'parameters',
            valid_type=AimqbParameters,
            help='Command line parameters for aimqb'
        )
        spec.input(
            "file", valid_type=SinglefileData, help="fchk, wfn, or wfx to run AimQB on"
        )
        #commented these to see
        # spec.output(
        #     'output_parameters',
        #     valid_type=Dict,
        #     required=True,
        #     help="The result parameters of the calculation",
        # )
        # spec.default_output_node = "output_parameters"
        spec.outputs.dynamic = True

        #would put error codes here
    # ---------------------------------------------------
    
    def prepare_for_submission(self, folder):
        """
        Create input files.
        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
            needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """

        codeinfo = datastructures.CodeInfo()
        #probably modify the next line
        codeinfo.cmdline_params = self.inputs.parameters.cmdline_params(
            file_name=self.inputs.file.filename
        )
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.metadata.options.output_filename

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo] #list since can involve more than one
        #files are already stored in AiiDA file repository, can use local_copy_list to pass the along
        # calcinfo.local_copy_list = [
        #     (
        #         self.inputs.file.uuid,
        #         self.inputs.file.filename,
        #     ),
        # ]
        #which files to retrieve from directory where job ran
        calcinfo.retrieve_list = [self.metadata.options.output_filename]

        return calcinfo
    
    # def cli_options(parameters):
    #  """Return command line options for parameters dictionary.

    #  :param dict parameters: dictionary with command line parameters
    #  """
    #  options = [f'-{key}={value}' for key,value in parameters.items()]
    #  for key, value in parameters.items():
    #      # Could validate: is key a known command-line option?
    #      options.append(f'-{key}={value}')
        #  elif isinstance(value, str):
        #      # Could validate: is value a valid regular expression?
        #      options.append(f'--{key}')
        #      options.append(value)

    #  return options

# class DiffCalculation(CalcJob):
#     """
#     AiiDA calculation plugin wrapping the diff executable.

#     Simple AiiDA plugin wrapper for 'diffing' two files.
#     """

#     @classmethod
#     def define(cls, spec):
#         """Define inputs and outputs of the calculation."""
#         super().define(spec)

#         # set default values for AiiDA options
#         spec.inputs["metadata"]["options"]["resources"].default = {
#             "num_machines": 1,
#             "num_mpiprocs_per_machine": 1,
#         }
#         spec.inputs["metadata"]["options"]["parser_name"].default = "aimall"

#         # new ports
#         spec.input(
#             "metadata.options.output_filename", valid_type=str, default="patch.diff"
#         )
#         spec.input(
#             "parameters",
#             valid_type=DiffParameters,
#             help="Command line parameters for diff",
#         )
#         spec.input(
#             "file1", valid_type=SinglefileData, help="First file to be compared."
#         )
#         spec.input(
#             "file2", valid_type=SinglefileData, help="Second file to be compared."
#         )
#         spec.output(
#             "aimall",
#             valid_type=SinglefileData,
#             help="diff between file1 and file2.",
#         )

#         spec.exit_code(
#             300,
#             "ERROR_MISSING_OUTPUT_FILES",
#             message="Calculation did not produce all expected output files.",
#         )

#     def prepare_for_submission(self, folder):
#         """
#         Create input files.

#         :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
#             needed by the calculation.
#         :return: `aiida.common.datastructures.CalcInfo` instance
#         """
#         codeinfo = datastructures.CodeInfo()
#         codeinfo.cmdline_params = self.inputs.parameters.cmdline_params(
#             file1_name=self.inputs.file1.filename, file2_name=self.inputs.file2.filename
#         )
#         codeinfo.code_uuid = self.inputs.code.uuid
#         codeinfo.stdout_name = self.metadata.options.output_filename

#         # Prepare a `CalcInfo` to be returned to the engine
#         calcinfo = datastructures.CalcInfo()
#         calcinfo.codes_info = [codeinfo]
#         calcinfo.local_copy_list = [
#             (
#                 self.inputs.file1.uuid,
#                 self.inputs.file1.filename,
#                 self.inputs.file1.filename,
#             ),
#             (
#                 self.inputs.file2.uuid,
#                 self.inputs.file2.filename,
#                 self.inputs.file2.filename,
#             ),
#         ]
#         calcinfo.retrieve_list = [self.metadata.options.output_filename]

#         return calcinfo
