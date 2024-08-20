"""Workchains to interface with AiiDA"""
# pylint: disable=c-extension-no-member
# pylint:disable=no-member
from aiida.engine import ToContext, WorkChain, if_
from aiida.orm import Bool, Code, Dict, List, SinglefileData, Str, load_group
from aiida.orm.extras import EntityExtras
from aiida_gaussian.calculations import GaussianCalculation
from aiida_shell import launch_shell_job

from aiida_aimall.calculations import AimqbCalculation
from aiida_aimall.data import AimqbParameters
from aiida_aimall.workchains.calcfunctions import (
    get_wfx,
    validate_file_ext,
    validate_shell_code,
)
from aiida_aimall.workchains.input import BaseInputWorkChain


class QMToAIMWorkChain(WorkChain):
    """Workchain to link quantum chemistry jobs without plugins to AIMAll"""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input(
            "shell_code",
            validator=validate_shell_code,  # pylint:disable=expression-not-assigned
        )
        spec.input("shell_metadata", valid_type=Dict)
        spec.input("shell_retrieved", valid_type=List)
        spec.input("shell_input_file", valid_type=SinglefileData, required=False)
        spec.input("shell_cmdline", valid_type=Str, required=True)
        spec.input("wfx_filename", valid_type=Str, required=False)
        spec.input("aim_code", valid_type=Code, required=True)
        spec.input(
            "aim_file_ext",
            valid_type=Str,
            validator=validate_file_ext,  # pylint:disable=expression-not-assigned
            required=False,
            default=lambda: Str("wfx"),
        )
        spec.input("aim_params", valid_type=AimqbParameters, required=True)
        spec.input(
            "aim_parser",
            valid_type=Str,
            required=False,
            default=lambda: Str("aimall.base"),
        )
        spec.input("dry_run", valid_type=Bool, default=lambda: Bool(False))

        spec.output("parameter_dict", valid_type=Dict)
        spec.outline(cls.shell_job, cls.aim, cls.result)

    def shell_job(self):
        """Launch a shell job"""
        if self.inputs.dry_run.value:
            return self.inputs
        _, node = launch_shell_job(
            self.inputs.shell_code,
            arguments=self.inputs.shell_cmdline.value,
            nodes={"file": self.inputs.shell_input_file},
            outputs=self.inputs.shell_retrieved.get_list(),
            submit=True,
            metadata=self.inputs.shell_metadata.get_dict(),
        )
        out_dict = {"qm": node}
        return ToContext(out_dict)

    def aim(self):
        """Launch an AIMQB calculation"""
        builder = AimqbCalculation.get_builder()
        builder.parameters = self.inputs.aim_params

        if "wfx_filename" not in self.inputs:
            wfx_file = (
                self.inputs.shell_input_file.filename.split(".")[0]
                + f"_{self.inputs.aim_file_ext.value}"
            )
        else:
            wfx_file = self.inputs.wfx_filename.value.replace(".", "_")
        builder.file = self.ctx.qm.base.links.get_outgoing().get_node_by_label(wfx_file)
        builder.code = self.inputs.aim_code
        builder.metadata.options.parser_name = self.inputs.aim_parser.value
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 2}
        # future work, enable group
        # num_atoms = len(
        #     self.ctx.prereor_aim.get_outgoing()
        #     .get_node_by_label("rotated_structure")
        #     .value.split("\n")
        # )
        # #  generalize for substrates other than H
        # builder.group_atoms = List([x + 1 for x in range(0, num_atoms) if x != 1])
        if self.inputs.dry_run.value:
            return self.inputs
        process_node = self.submit(builder)
        out_dict = {"aim": process_node}
        return ToContext(out_dict)

    def result(self):
        """Put results in output node"""
        self.out(
            "parameter_dict",
            self.ctx.aim.base.links.get_outgoing().get_node_by_label(
                "output_parameters"
            ),
        )


class GaussianToAIMWorkChain(BaseInputWorkChain):
    """A workchain to submit a Gaussian calculation and automatically setup an AIMAll calculation on the output"""

    @classmethod
    def define(cls, spec):
        """Define workchain steps"""
        super().define(spec)
        spec.input("gauss_params", valid_type=Dict, required=True)
        spec.input("aim_params", valid_type=AimqbParameters, required=True)
        spec.input("gauss_code", valid_type=Code)
        spec.input(
            "frag_label",
            valid_type=Str,
            help="Label for substituent fragment, stored as extra",
            required=False,
        )
        spec.input("wfx_group", valid_type=Str, required=False)
        spec.input("gaussian_group", valid_type=Str, required=False)
        spec.input("aim_code", valid_type=Code)
        spec.input("dry_run", valid_type=Bool, default=lambda: Bool(False))
        spec.input("wfx_filename", valid_type=Str, default=lambda: Str("output.wfx"))
        spec.output("parameter_dict", valid_type=Dict)
        spec.outline(
            cls.validate_input,
            if_(cls.is_xyz_input)(cls.create_structure_from_xyz),
            if_(cls.is_smiles_input)(
                cls.get_molecule_inputs_step, cls.string_to_StructureData
            ),
            if_(cls.is_structure_input)(cls.structure_in_context),
            cls.gauss,
            cls.classify_wfx,
            cls.aim,
            cls.result,
        )

    def gauss(self):
        """Run Gaussian calculation"""
        builder = GaussianCalculation.get_builder()
        builder.structure = self.ctx.structure
        builder.parameters = self.inputs.gauss_params
        builder.code = self.inputs.gauss_code
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 4}
        builder.metadata.options.max_memory_kb = int(6400 * 1.25) * 1024
        builder.metadata.options.max_wallclock_seconds = 604800
        builder.metadata.options.additional_retrieve_list = [
            self.inputs.wfx_filename.value
        ]
        if self.inputs.dry_run.value:
            return self.inputs
        process_node = self.submit(builder)
        if "gaussian_group" in self.inputs:
            gauss_group = load_group(self.inputs.gaussian_sp_group)
            gauss_group.add_nodes(process_node)
        out_dict = {"gauss": process_node}
        # self.ctx.standard_wfx = process_node.get_outgoing().get_node_by_label("wfx")
        return ToContext(out_dict)

    def classify_wfx(self):
        """Add the wavefunction file from the previous step to the correct group and set the extras"""
        folder_data = self.ctx.gauss.base.links.get_outgoing().get_node_by_label(
            "retrieved"
        )
        self.ctx.wfx = get_wfx(folder_data, self.inputs.wfx_filename)
        # later scan input parameters for filename

        if "wfx_group" in self.inputs:
            wf_group = load_group(self.inputs.wfx_group)
            wf_group.add_nodes(self.ctx.wfx)
        if "frag_label" in self.inputs:
            struct_extras = EntityExtras(self.ctx.wfx)
            struct_extras.set("smiles", self.inputs.frag_label.value)

    def aim(self):
        """Run Final AIM Calculation"""
        builder = AimqbCalculation.get_builder()
        builder.parameters = self.inputs.aim_params
        builder.file = self.ctx.wfx
        builder.code = self.inputs.aim_code
        # if "frag_label" in self.inputs:
        #     builder.frag_label = self.inputs.frag_label
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 2}
        num_atoms = len(self.ctx.structure.sites)
        #  generalize for substrates other than H
        builder.group_atoms = List([x + 1 for x in range(0, num_atoms) if x != 1])
        if self.inputs.dry_run.value:
            return self.inputs
        process_node = self.submit(builder)
        out_dict = {"aim": process_node}
        return ToContext(out_dict)

    def result(self):
        """Put results in output node"""
        self.out(
            "parameter_dict",
            self.ctx.aim.base.links.get_outgoing().get_node_by_label(
                "output_parameters"
            ),
        )


class GenerateWFXToAIMWorkChain(WorkChain):
    """Workchain to generate a wfx file from computational chemistry output files and submit that to an AIMQB Calculation

    Note:
        This workchain uses the IOData module of the Ayer's group Horton to generate the wfx files. Supported file formats
        include .fchk files, molden files (from Molpro, Orca, PSI4, Turbomole, and Molden), and CP2K atom log files. Further
        note that .fchk files can simply be provided directly to an `AimqbCalculation`.

        While IOData accepts other file formats, these formats are the ones available that contain the necessary information
        to generate wfc files
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input("input_file", valid_type=SinglefileData)
        spec.input("aim_params", valid_type=AimqbParameters)
        spec.input("aim_code")
        spec.output("output_parameters", valid_type=Dict)
        spec.outline(cls.generate_wfx, cls.aim, cls.result)

    def generate_wfx(self):
        """Given SinglefileData generates a wfx file if IOData is capable"""
        _, node = launch_shell_job(
            "iodata-convert",
            arguments="{file} output.wfx",
            nodes={"file": self.inputs.input_file},
            outputs=["output.wfx"],
            submit=True,
        )
        out_dict = {"shell_wfx": node}
        return ToContext(out_dict)

    def aim(self):
        """Run AIM on the generated wfx file"""
        builder = AimqbCalculation.get_builder()
        builder.parameters = self.inputs.aim_params
        builder.file = self.ctx.shell_wfx.base.links.get_outgoing().get_node_by_label(
            "output_wfx"
        )
        builder.code = self.inputs.aim_code
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 2}
        #  generalize for substrates other than H
        process_node = self.submit(builder)
        out_dict = {"aim": process_node}
        return ToContext(out_dict)

    def result(self):
        """Put results in output node"""
        self.out(
            "output_parameters",
            self.ctx.aim.base.links.get_outgoing().get_node_by_label(
                "output_parameters"
            ),
        )
