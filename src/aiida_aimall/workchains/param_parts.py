"""Workchains that are smaller parts of SubstituenParamWorkChain"""
# pylint:disable=no-member
from aiida.engine import ToContext, WorkChain, if_
from aiida.orm import (
    Bool,
    Code,
    Dict,
    Int,
    SinglefileData,
    Str,
    StructureData,
    load_group,
)
from aiida.orm.extras import EntityExtras
from aiida_gaussian.calculations import GaussianCalculation

from aiida_aimall.calculations import AimqbCalculation
from aiida_aimall.data import AimqbParameters
from aiida_aimall.workchains.calcfunctions import (
    create_wfx_from_retrieved,
    dict_to_structure,
    generate_rotated_structure_aiida,
    generate_structure_data,
    get_substituent_input,
    get_wfxname_from_gaussianinputs,
    parameters_with_cm,
)


class SmilesToGaussianWorkChain(WorkChain):
    r"""Workchain to take a substituent SMILES, and run a Gaussian calculation on that SMILES

    Takes an input SMILES with one placeholder \*, generates a geometry with \* replaced with a hydrogen.
    U

    Attributes:
        smiles (aiida.orm.Str): SMILES of a substiuent. Must contain a single placeholder \*
        gaussian_parameters (aiida.orm.Dict): Gaussian calculation for generating a wfx
        gaussian_code (aiida.orm.Code): Gaussian Code
        wfxname (aiida.orm.Str): name of wfx file provided in gaussian_parameters
        wfxgroup (aiida.orm.Str): group to store the wfx file in
        mem_mb (aiida.orm.Int): amount of memory in MB for the Gaussian calculation
        nprocs (aiida.orm.Int): number of processors for the Gaussian calculation
        time_s (aiida.orm.Int): amount of time to run the Gaussian calculation

    Note:
        The SMILES provided should have a single \*.

    Note:
        Uses the charge and multiplicity of the provided SMILES, not that provided to gaussian_parameters

    Note:
        'output':'wfx' should be provided to `gaussian_parameters`. And a .wfx file name should be provided
        as well

    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input(
            "smiles",
            valid_type=Str,
            help="SMILES of a substiuent. Must contain a single placeholder *",
        )
        spec.input(
            "gaussian_parameters",
            valid_type=Dict,
            help="Gaussian calculation for generating a wfx",
        )
        spec.input("gaussian_code", valid_type=Code, help="Gaussian Code")
        spec.input(
            "wfxname",
            required=False,
            valid_type=Str,
            help="name of wfx file provided in gaussian_parameters",
        )
        spec.input(
            "wfxgroup",
            required=False,
            valid_type=Str,
            help="group to store the wfx file in",
        )
        spec.input("nprocs", default=lambda: Int(4))
        spec.input("mem_mb", default=lambda: Int(6400))
        spec.input("time_s", default=lambda: Int(24 * 7 * 60 * 60))
        spec.input("dry_run", default=lambda: Bool(False))
        spec.output("wfx", valid_type=SinglefileData, required=False)
        spec.output("output_parameters", valid_type=Dict)
        spec.outline(
            cls.get_substituent_inputs_step,  # , cls.results
            cls.update_parameters_with_cm,
            cls.string_to_StructureData,
            cls.get_wfx_name,
            cls.submit_gaussian,
            if_(cls.found_wfx_name)(cls.create_wfx_file),
            cls.results,
        )

    def get_substituent_inputs_step(self):
        """Given list of substituents and previously done smiles, get input"""
        self.ctx.smiles_geom = get_substituent_input(self.inputs.smiles)

    def update_parameters_with_cm(self):
        """Update provided Gaussian parameters with charge and multiplicity of substituent"""
        self.ctx.gaussian_cm_params = parameters_with_cm(
            self.inputs.gaussian_parameters, self.ctx.smiles_geom
        )

    def string_to_StructureData(self):
        """Convert an xyz string of molecule geometry to StructureData"""
        self.ctx.structure = generate_structure_data(self.ctx.smiles_geom)

    def get_wfx_name(self):
        """Find the wavefunction file in the retrieved node"""
        if "wfxname" in self.inputs:
            self.ctx.wfxname = self.inputs.wfxname
        else:
            self.ctx.wfxname = get_wfxname_from_gaussianinputs(
                self.inputs.gaussian_parameters
            )

    def submit_gaussian(self):
        """Submits the gaussian calculation"""
        builder = GaussianCalculation.get_builder()

        builder.structure = self.ctx.structure
        builder.parameters = self.ctx.gaussian_cm_params
        builder.code = self.inputs.gaussian_code
        builder.metadata.options.resources = {
            "num_machines": 1,
            "tot_num_mpiprocs": self.inputs.nprocs.value,
        }
        builder.metadata.options.max_memory_kb = (
            int(self.inputs.mem_mb.value * 1.25) * 1024
        )
        builder.metadata.options.max_wallclock_seconds = self.inputs.time_s.value
        if self.ctx.wfxname.value:
            builder.metadata.options.additional_retrieve_list = [
                self.ctx.wfxname.value.strip()
            ]

        if self.inputs.dry_run.value:
            return self.inputs
        node = self.submit(builder)
        out_dict = {"opt": node}
        return ToContext(out_dict)

    def found_wfx_name(self):
        """Check if we found a wfx or wfn file"""
        if self.ctx.wfxname.value:
            return True
        return False

    def create_wfx_file(self):
        """Create a wavefunction file from the retireved folder"""
        retrieved_folder = (
            self.ctx["opt"].base.links.get_outgoing().get_node_by_label("retrieved")
        )
        wfx_node = create_wfx_from_retrieved(self.ctx.wfxname, retrieved_folder)
        wfx_node.base.extras.set("smiles", self.inputs.smiles)
        self.ctx.wfxfile = wfx_node
        if "wfxgroup" in self.inputs:
            wfx_group = load_group(self.inputs.wfxgroup.value)
            wfx_group.add_nodes(wfx_node)

    def results(self):
        """Store our relevant information as output"""
        if "wfxfile" in self.ctx:
            self.out("wfx", self.ctx.wfxfile)
        self.out(
            "output_parameters",
            self.ctx["opt"]
            .base.links.get_outgoing()
            .get_node_by_label("output_parameters"),
        )


class AIMAllReorWorkChain(WorkChain):
    """Workchain to run AIM and then reorient the molecule using the results

    Often called in `aiida_aimall.controllers.AimReorSubmissionController`.
    Process continues in `aiida_aimall.controllers.GaussianSubmissionController`.

    Attributes:
        aim_params: (AimqbParameters): Command line parameters for aimqb
        file (aiida.orm.SinglefileData): .fchk, .wfn, or .wfx file for aimqb input
        aim_code (aiida.orm.Code): AIMQB code
        frag_label (aiida.orm.Str): Optional SMILES tag of the substituent
        aim_group (aiida.orm.Str): Optional group to put the AIM calculation node in
        reor_group (aiida.orm.Str): Optional group to put the reoriented structure in

    Example

        ::

            from aiida_aimall.data import AimqbParameters
            from aiida_aimall.workchains.param_parts import AIMAllReorWorkChain
            from aiida.orm import SinglefileData, load_code
            from aiida.engine import submit
            input_file = SinglefileData("/absolute/path/to/file")
            aim_code = load_code("aimall@localhost")
            aim_params = AimqbParameters({'nproc':2,'naat':2,'atlaprhocps':True})
            builder = AIMAllReorWorkChain.get_builder()
            builder.file = input_file
            builder.aim_code = aim_code
            builder.aim_params = aim_params
            submit(builder)

    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input(
            "aim_params",
            valid_type=AimqbParameters,
            help="Command line parameters for aimqb",
        )
        spec.input(
            "file",
            valid_type=SinglefileData,
            help="fchk, wfn, or wfx file for aimqb input",
        )
        # spec.output('aim_dict',valid_type=Dict)
        spec.input("aim_code", valid_type=Code, help="aimqb code")
        spec.input(
            "frag_label",
            valid_type=Str,
            required=False,
            help="Optional SMILES tag of the substituent",
        )
        spec.input(
            "aim_group",
            valid_type=Str,
            required=False,
            help="Optional group to put the AIM calculation node in",
        )
        spec.input(
            "reor_group",
            valid_type=Str,
            required=False,
            help="Optional group to put the reoriented structure in",
        )
        spec.input("dry_run", valid_type=Bool, default=lambda: Bool(False))
        spec.output("rotated_structure", valid_type=StructureData)
        spec.outline(cls.aimall, cls.rotate, cls.dict_to_struct_reor, cls.result)

    def aimall(self):
        """submit the aimall calculation"""
        builder = AimqbCalculation.get_builder()
        builder.code = self.inputs.aim_code
        builder.parameters = self.inputs.aim_params
        builder.file = self.inputs.file
        builder.metadata.options.resources = {
            "num_machines": 1,
            "tot_num_mpiprocs": 2,
        }
        if self.inputs.dry_run.value:
            return self.inputs
        aim_calc = self.submit(builder)
        aim_calc.store()
        if "aim_group" in self.inputs:
            aim_noreor_group = load_group(self.inputs.aim_group)
            aim_noreor_group.add_nodes(aim_calc)
        out_dict = {"aim": aim_calc}
        return ToContext(out_dict)

    def rotate(self):
        """perform the rotation"""
        aimfolder = (
            self.ctx["aim"].base.links.get_outgoing().get_node_by_label("retrieved")
        )
        output_dict = (
            self.ctx["aim"]
            .base.links.get_outgoing()
            .get_node_by_label("output_parameters")
            .get_dict()
        )
        atom_props = output_dict["atomic_properties"]
        cc_props = output_dict["cc_properties"]
        self.ctx.rot_struct_dict = generate_rotated_structure_aiida(
            aimfolder, atom_props, cc_props
        )

    def dict_to_struct_reor(self):
        """generate the gaussian input from rotated structure"""
        structure = dict_to_structure(self.ctx.rot_struct_dict)
        structure.store()
        if "reor_group" in self.inputs:
            reor_struct_group = load_group(self.inputs.reor_group.value)
            reor_struct_group.add_nodes(structure)
        if "frag_label" in self.inputs:
            struct_extras = EntityExtras(structure)
            struct_extras.set("smiles", self.inputs.frag_label.value)
        self.ctx.rot_structure = structure

    def result(self):
        """Parse results"""
        self.out("rotated_structure", self.ctx.rot_structure)
