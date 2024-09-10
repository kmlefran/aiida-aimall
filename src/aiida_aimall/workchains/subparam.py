"""`WorkChain` for calculating substituent parameters developed by authors"""
# pylint: disable=c-extension-no-member
# pylint:disable=no-member
# pylint:disable=too-many-lines
from aiida.engine import ToContext, if_
from aiida.orm import Bool, Code, Dict, List, Str, load_group
from aiida.orm.extras import EntityExtras
from aiida_gaussian.calculations import GaussianCalculation

from aiida_aimall.calculations import AimqbCalculation
from aiida_aimall.data import AimqbParameters
from aiida_aimall.workchains.calcfunctions import (
    create_wfx_from_retrieved,
    get_substituent_input,
)
from aiida_aimall.workchains.input import BaseInputWorkChain
from aiida_aimall.workchains.param_parts import AIMAllReorWorkChain


class SubstituentParameterWorkChain(BaseInputWorkChain):
    r"""A workchain to calculate properties of substituents, R, in R-H molecules.

    This is a multistep calculation, consisting of a Gaussian calculation, an AIMQB calculation,
    Python reorientation to the defined coordinate system, a Gaussian single point calculation,
    and a final AIMQB calculation on the single point wfx calculation. Substituent Properties are
    then extracted using the AimqbGroupParser.

    Attributes:
        gauss_opt_params (aiida.orm.Dict): Parameters for the Gaussian optimization calculations
        gauss_sp_params (aiida.orm.Dict): Parameters for the Gaussian single point calculations
        aim_params (AimqbParameters): Command line parameters for AIMQB
        gauss_code (aiida.orm.Code): Code for Gaussian software
        frag_label (aiida.orm.Str): Optional fragment label for the calculation
        opt_wfx_group (aiida.orm.Str): Optional group to put optimization wavefunctions in
        sp_wfx_group (aiida.orm.Str): Optional group to put single point wavefunctions in
        gaussian_opt_group (aiida.orm.Str): Optional group to put optimization GaussianCalculations in
        gaussian_sp_group (aiida.orm.Str): Optional group to put single point GaussianCalculations in
        wfx_filename (aiida.orm.Str): Optional wfx file name
        aim_code (aiida.orm.Code): Code for AIMQB software
        dry_run (aiida.orm.Bool): Whether or not this is a dry run of the WorkChain

    Note:
        Here, the group for a substiuent is defined in an R-H molecule. Atom 1 is the atom in
        the group R that is attached to the hydrogen, and the hydrogen should be atom 2. These
        align with the default settings of an AimqbCalculation using an AimqbGroupParser.

    Example:
        ::

            from aiida.plugins import WorkflowFactory, DataFactory
            from aiida.orm import Dict, StructureData, load_code
            from aiida.engine import submit
            from aiida import load_profile
            import io
            import ase.io

            load_profile()

            SubstituentParameterWorkchain = WorkflowFactory('aimall.subparam')
            AimqbParameters = DataFactory('aimall.aimqb')
            aim_input = AimqbParameters({'nproc':2,'naat':2,'atlaprhocps':True})
            gaussian_opt = Dict(
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
            gaussian_sp = Dict(
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
                            "route_parameters": {"nosymmetry": None, "Output": "WFX"},
                            "input_parameters": {"output.wfx": None},
                        }
            )
            f = io.StringIO(
                            "5\n\n C -0.1 2.0 -0.02\nH 0.3 1.0 -0.02\nH 0.3 2.5 0.8\nH 0.3 2.5 -0.9\nH -1.2 2.0 -0.02"
                        )
            struct_data = StructureData(ase=ase.io.read(f, format="xyz"))
            f.close()
            builder = SubstituentParameterWorkchain.get_builder()
            builder.g16_code = load_code('gaussian@localhost')
            builder.aim_code = load_code('aimall@localhost')
            builder.g16_opt_params = gaussian_opt
            builder.g16_sp_params = gaussian_sp
            builder.structure = struct_data
            builder.aim_params = aim_input
            submit(builder)

    """

    @classmethod
    def define(cls, spec):
        """Define workchain steps"""
        super().define(spec)
        spec.input("gauss_opt_params", valid_type=Dict, required=True)
        spec.input("gauss_sp_params", valid_type=Dict, required=True)
        spec.input("aim_params", valid_type=AimqbParameters, required=True)
        spec.input("gauss_code", valid_type=Code)
        spec.input(
            "frag_label",
            valid_type=Str,
            help="Label for substituent fragment, stored as extra",
            required=False,
        )
        spec.input("opt_wfx_group", valid_type=Str, required=False)
        spec.input("sp_wfx_group", valid_type=Str, required=False)
        spec.input("gaussian_opt_group", valid_type=Str, required=False)
        spec.input("gaussian_sp_group", valid_type=Str, required=False)
        spec.input(
            "wfx_filename",
            valid_type=Str,
            required=False,
            default=lambda: Str("output.wfx"),
        )
        # spec.input("file", valid_type=SinglefileData)
        # spec.output('aim_dict',valid_type=Dict)
        spec.input("aim_code", valid_type=Code)
        spec.input("dry_run", valid_type=Bool, default=lambda: Bool(False))
        # spec.input("frag_label", valid_type=Str)
        # spec.output("rotated_structure", valid_type=Str)
        spec.output("parameter_dict", valid_type=Dict)
        spec.outline(
            cls.validate_input,
            if_(cls.is_xyz_input)(cls.create_structure_from_xyz),
            if_(cls.is_smiles_input)(
                cls.get_substituent_inputs_step, cls.string_to_StructureData
            ),
            if_(cls.is_structure_input)(cls.structure_in_context),
            cls.gauss_opt,
            cls.classify_opt_wfx,
            cls.aim_reor,
            cls.gauss_sp,
            cls.classify_sp_wfx,
            cls.aim,
            cls.result,
        )

    def get_substituent_inputs_step(self):
        """Get a dictionary of the substituent input for a given SMILES"""
        self.ctx.smiles_geom = get_substituent_input(self.inputs.smiles)

    def gauss_opt(self):
        """Submit the Gaussian optimization"""
        builder = GaussianCalculation.get_builder()
        builder.structure = self.ctx.structure
        builder.parameters = self.inputs.gauss_opt_params
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
        if "gaussian_opt_group" in self.inputs:
            gauss_opt_group = load_group(self.inputs.gaussian_opt_group)
            gauss_opt_group.add_nodes(process_node)
        out_dict = {"opt": process_node}
        # self.ctx.standard_wfx = process_node.get_outgoing().get_node_by_label("wfx")
        return ToContext(out_dict)

    def classify_opt_wfx(self):
        """Add the wavefunction file from the previous step to the correct group and set the extras"""
        folder_data = self.ctx.opt.base.links.get_outgoing().get_node_by_label(
            "retrieved"
        )
        # later scan input parameters for filename
        wfx_file = create_wfx_from_retrieved(
            self.inputs.wfx_filename.value, folder_data
        )
        self.ctx.opt_wfx = wfx_file

        if "opt_wfx_group" in self.inputs:
            opt_wf_group = load_group(self.inputs.opt_wfx_group)
            opt_wf_group.add_nodes(wfx_file)
        if "frag_label" in self.inputs:
            struct_extras = EntityExtras(wfx_file)
            struct_extras.set("smiles", self.inputs.frag_label.value)

    def aim_reor(self):
        """Submit the Aimqb calculation and reorientation"""
        builder = AIMAllReorWorkChain.get_builder()
        builder.aim_params = self.inputs.aim_params
        builder.file = self.ctx.opt_wfx
        builder.aim_code = self.inputs.aim_code
        # builder.dry_run = self.inputs.dry_run
        if "frag_label" in self.inputs:
            builder.frag_label = self.inputs.frag_label
        if self.inputs.dry_run.value:
            return self.inputs
        process_node = self.submit(builder)
        out_dict = {"prereor_aim": process_node}
        return ToContext(out_dict)

    def gauss_sp(self):
        """Run Gaussian Single Point calculation"""
        builder = GaussianCalculation.get_builder()
        builder.structure = (
            self.ctx.prereor_aim.base.links.get_outgoing().get_node_by_label(
                "rotated_structure"
            )
        )
        builder.parameters = self.inputs.gauss_sp_params
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
        if "gaussian_sp_group" in self.inputs:
            gauss_sp_group = load_group(self.inputs.gaussian_sp_group)
            gauss_sp_group.add_nodes(process_node)
        out_dict = {"sp": process_node}
        # self.ctx.standard_wfx = process_node.get_outgoing().get_node_by_label("wfx")
        return ToContext(out_dict)

    def classify_sp_wfx(self):
        """Add the wavefunction file from the previous step to the correct group and set the extras"""
        folder_data = self.ctx.sp.base.links.get_outgoing().get_node_by_label(
            "retrieved"
        )
        # later scan input parameters for filename
        wfx_file = create_wfx_from_retrieved(
            self.inputs.wfx_filename.value, folder_data
        )
        self.ctx.sp_wfx = wfx_file

        if "sp_wfx_group" in self.inputs:
            sp_wf_group = load_group(self.inputs.sp_wfx_group)
            sp_wf_group.add_nodes(wfx_file)
        if "frag_label" in self.inputs:
            struct_extras = EntityExtras(wfx_file)
            struct_extras.set("smiles", self.inputs.frag_label.value)

    def aim(self):
        """Run Final AIM Calculation"""
        builder = AimqbCalculation.get_builder()
        builder.parameters = self.inputs.aim_params
        builder.file = self.ctx.sp_wfx
        builder.code = self.inputs.aim_code
        builder.metadata.options.parser_name = "aimall.group"
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 2}
        num_atoms = len(
            self.ctx.prereor_aim.base.links.get_outgoing()
            .get_node_by_label("rotated_structure")
            .sites
        )
        #  generalize for substrates other than H
        builder.group_atoms = List([x + 1 for x in range(0, num_atoms) if x != 1])
        if self.inputs.dry_run.value:
            return self.inputs
        process_node = self.submit(builder)
        out_dict = {"final_aim": process_node}
        return ToContext(out_dict)

    def result(self):
        """Put results in output node"""
        self.out(
            "parameter_dict",
            self.ctx.final_aim.base.links.get_outgoing().get_node_by_label(
                "output_parameters"
            ),
        )
