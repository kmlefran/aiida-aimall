"""aiida_aimall.workchains
Workchains designed for a workflow starting from a set of cmls, then breaking off into fragment Gaussian Calculations
Needs to be run in part with aiida_aimall.controllers to control local traffic on lab Mac
Example in the works

Provided Workchains are
MultiFragmentWorkchain, entry point: multifrag
G16OptWorkChain, entry point: g16opt
AimAllReor WorkChain, entry point: aimreor
"""
# pylint: disable=c-extension-no-member
# pylint:disable=no-member
import sys

from aiida.engine import ToContext, WorkChain, calcfunction
from aiida.orm import Bool, Code, Dict, Int, List, SinglefileData, Str, load_group
from aiida.orm.extras import EntityExtras
from aiida.plugins.factories import CalculationFactory, DataFactory
from aiida_shell import launch_shell_job
from rdkit import Chem
from rdkit.Chem import AllChem, rdmolops, rdqueries
from rdkit.Chem.MolKey.MolKey import BadMoleculeException
from subproptools.sub_reor import rotate_substituent_aiida

old_stdout = sys.stdout

# load the needed calculations and data types
GaussianCalculation = CalculationFactory("aimall.gaussianwfx")
AimqbParameters = DataFactory("aimall.aimqb")
AimqbCalculation = CalculationFactory("aimall.aimqb")


@calcfunction
def generate_rotated_structure_aiida(FolderData, atom_dict, cc_dict):
    """Rotates the fragment to the defined coordinate system

    Args:
        FolderData: aim calculation folder
        atom_dict: AIM atom dict
        cc_dict: AIM cc_dict
    """
    return Dict(rotate_substituent_aiida(FolderData, atom_dict, cc_dict))


@calcfunction
def dict_to_structure(fragment_dict):
    """Generate a string of xyz coordinates for Gaussian input file

    :param fragment_dict:
    :param type fragment_dict: aiida.orm.nodes.data.dict.Dict
    """
    inp_dict = fragment_dict.get_dict()
    symbols = inp_dict["atom_symbols"]
    coords = inp_dict["geom"]
    outstr = ""
    for i, symbol in enumerate(symbols):
        if i != len(symbols) - 1:
            outstr = (
                outstr
                + symbol
                + "   "
                + str(coords[i][0])
                + "   "
                + str(coords[i][1])
                + "   "
                + str(coords[i][2])
                + "\n"
            )
        else:
            outstr = (
                outstr
                + symbol
                + "   "
                + str(coords[i][0])
                + "   "
                + str(coords[i][1])
                + "   "
                + str(coords[i][2])
            )
    return Str(outstr)


def calc_multiplicity(mol):
    """Calculate the multiplicity of a molecule as 2S +1"""
    num_radicals = 0
    for atom in mol.GetAtoms():
        num_radicals += atom.GetNumRadicalElectrons()
    multiplicity = num_radicals + 1
    return multiplicity


def find_attachment_atoms(mol):
    """Given molecule object, find the atoms corresponding to a * and the atom to which that is bound

    Args:
        mol: rdkit molecule object

    Returns:
        molecule with added hydrogens, the * atom object, and the atom object to which that is attached

    Note:
        Assumes that only one * is present in the molecule
    """
    # * has atomic number 0
    query = rdqueries.AtomNumEqualsQueryAtom(0)
    # add hydrogens now
    h_mol_rw = Chem.RWMol(mol)  # Change type of molecule object
    h_mol_rw = Chem.AddHs(h_mol_rw)
    query_ats = h_mol_rw.GetAtomsMatchingQuery(query)
    if len(query_ats) != 1:
        raise ValueError(
            f"Molecule should have one placeholder atom with atomic number 0, found {len(query_ats)}"
        )
    zero_at = query_ats[0]
    # this will be bonded to one atom - whichever atom in the bond is not *, is the one we are looking for
    bond = zero_at.GetBonds()[0]
    begin_atom = bond.GetBeginAtom()
    if begin_atom.GetSymbol() != "*":
        attached_atom = begin_atom
    else:
        attached_atom = bond.GetEndAtom()
    return h_mol_rw, zero_at, attached_atom


def reorder_molecule(h_mol_rw, zero_at, attached_atom):
    """Reindexes the atoms in a molecule, setting attached_atom to index 0, and zero_at to index 1

    Args:
        h_mol_rw: RWMol rdkit object with explicit hydrogens
        zero_at: the placeholder * atom
        attached_atom: the atom bonded to *

    Returns:
        molecule with reordered indices
    """
    zero_at_idx = zero_at.GetIdx()
    zero_at.SetAtomicNum(1)

    attached_atom_idx = attached_atom.GetIdx()
    # Initialize the new index so that our desired atoms are at the indices we want
    first_two_atoms = [attached_atom_idx, zero_at_idx]
    # Add the rest of the indices in original order
    remaining_idx = [
        atom.GetIdx()
        for atom in h_mol_rw.GetAtoms()
        if atom.GetIdx() not in first_two_atoms
    ]
    out_atom_order = first_two_atoms + remaining_idx
    reorder_mol = rdmolops.RenumberAtoms(h_mol_rw, out_atom_order)
    return reorder_mol


def get_xyz(reorder_mol):
    """MMFF optimize the molecule to generate xyz coordiantes"""
    AllChem.EmbedMolecule(reorder_mol)
    # not_optimized will be 0 if done, 1 if more steps needed
    max_iters = 200
    for i in range(0, 6):
        not_optimized = AllChem.MMFFOptimizeMolecule(
            reorder_mol, maxIters=max_iters
        )  # Optimize with MMFF94
        # -1 is returned for molecules where there are no heavy atom-heavy atom bonds
        # for these, hopefully the embed geometry is good enough
        # 0 is returned on successful opt
        if not_optimized in [0, -1]:
            break
        if i == 5:
            return "Could not determine xyz coordinates"
        max_iters = max_iters + 200
    xyz_block = AllChem.rdmolfiles.MolToXYZBlock(
        reorder_mol
    )  # pylint:disable=no-member  # Store xyz coordinates
    split_xyz_block = xyz_block.split("\n")
    # first two lines are: number of atoms and blank. Last line is blank
    xyz_lines = split_xyz_block[2 : len(split_xyz_block) - 1]
    xyz_string = "\n".join([str(item) for item in xyz_lines])
    return xyz_string


@calcfunction
def get_substituent_input(smiles: str) -> dict:
    """For a given smiles, determine xyz structure, charge, and multiplicity

    Args:
        smiles: SMILEs of substituent to run

    Returns:
        Dict with keys xyz, charge, multiplicity

    """
    mol = Chem.MolFromSmiles(smiles.value)
    if not mol:
        raise ValueError(
            f"Molecule could not be constructed for substituent input SMILES {smiles.value}"
        )
    h_mol_rw, zero_at, attached_atom = find_attachment_atoms(mol)
    reorder_mol = reorder_molecule(h_mol_rw, zero_at, attached_atom)
    xyz_string = get_xyz(reorder_mol)
    if xyz_string == "Could not determine xyz coordinates":
        raise BadMoleculeException(
            "Maximum iterations exceeded, could not determine xyz coordinates for f{smiles.value}"
        )
    reorder_mol.UpdatePropertyCache()
    charge = Chem.GetFormalCharge(h_mol_rw)
    multiplicity = calc_multiplicity(h_mol_rw)
    out_dict = Dict({"xyz": xyz_string, "charge": charge, "multiplicity": multiplicity})
    return out_dict


@calcfunction
def parameters_with_cm(parameters, smiles_dict):
    """Add charge and multiplicity keys to Gaussian Input"""
    parameters_dict = parameters.get_dict()
    smiles_dict_dict = smiles_dict.get_dict()
    parameters_dict["charge"] = smiles_dict_dict["charge"]
    parameters_dict["multiplicity"] = smiles_dict_dict["multiplicity"]
    return Dict(parameters_dict)


def validate_shell_code(node, _):
    """Validate the shell code, ensuring that it is ShellCode or Str"""
    if node.node_type not in [
        "data.core.code.installed.shell.ShellCode.",
        "data.core.str.Str.",
    ]:
        return "the `shell_code` input must be either ShellCode or Str of the command."
    return None


def validate_file_ext(node, _):
    """Validates that the file extension provided for AIM is wfx, wfn or fchk"""
    if node.value not in ["wfx", "wfn", "fchk"]:
        return "the `aim_file_ext` input must be a valid file format for AIMQB: wfx, wfn, or fchk"
    return None


class QMToAIMWorkchain(WorkChain):
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
        # if "frag_label" in self.inputs:
        #     builder.frag_label = self.inputs.frag_label
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


class SmilesToGaussianWorkchain(WorkChain):
    """Workchain to take a SMILES, generate xyz, charge, and multiplicity"""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input("smiles")
        spec.input("gaussian_parameters")
        spec.input("gaussian_code")
        spec.input("wfxgroup", required=False)
        spec.input("nprocs", default=lambda: Int(4))
        spec.input("mem_mb", default=lambda: Int(6400))
        spec.input("time_s", default=lambda: Int(24 * 7 * 60 * 60))
        spec.input("dry_run", default=lambda: Bool(False))
        spec.output("wfx", valid_type=SinglefileData)
        spec.output("output_parameters", valid_type=Dict)
        # spec.output("g_input")
        # spec.output("done_smiles")
        spec.outline(
            cls.get_substituent_inputs_step,  # , cls.results
            cls.update_parameters_with_cm,
            cls.submit_gaussian,
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

    def submit_gaussian(self):
        """Submits the gaussian calculation"""
        builder = GaussianCalculation.get_builder()
        builder.structure_str = Str(self.ctx.smiles_geom["xyz"])
        builder.parameters = self.ctx.gaussian_cm_params
        builder.fragment_label = self.inputs.smiles
        builder.code = self.inputs.gaussian_code
        builder.metadata.options.resources = {
            "num_machines": 1,
            "tot_num_mpiprocs": self.inputs.nprocs.value,
        }
        builder.metadata.options.max_memory_kb = (
            int(self.inputs.mem_mb.value * 1.25) * 1024
        )
        builder.metadata.options.max_wallclock_seconds = self.inputs.time_s.value
        if "wfxgroup" in self.inputs:
            builder.wfxgroup = self.inputs.wfxgroup
        if self.inputs.dry_run.value:
            return self.inputs
        node = self.submit(builder)
        out_dict = {"opt": node}
        return ToContext(out_dict)

    def results(self):
        """Store our relevant information as output"""
        self.out(
            "wfx", self.ctx["opt"].base.links.get_outgoing().get_node_by_label("wfx")
        )
        self.out(
            "output_parameters",
            self.ctx["opt"]
            .base.links.get_outgoing()
            .get_node_by_label("output_parameters"),
        )


class AIMAllReor(WorkChain):
    """Workchain to run AIM and then reorient the molecule using the results

    Process continues in GaussianSubmissionController"""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input("aim_params", valid_type=AimqbParameters)
        spec.input("file", valid_type=SinglefileData)
        # spec.output('aim_dict',valid_type=Dict)
        spec.input("aim_code", valid_type=Code)
        spec.input("frag_label", valid_type=Str, required=False)
        spec.input("aim_group", valid_type=Str, required=False)
        spec.input("reor_group", valid_type=Str, required=False)
        spec.input("dry_run", valid_type=Bool, default=lambda: Bool(False))
        spec.output("rotated_structure", valid_type=Str)
        spec.outline(
            cls.aimall, cls.rotate, cls.dict_to_struct_reor, cls.result
        )  # ,cls.aimall)#, cls.aimall,cls.reorient,cls.aimall)

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
        aim_calc = self.submit(builder, dry_run=self.inputs.dry_run)
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
        struct_str = dict_to_structure(self.ctx.rot_struct_dict)
        struct_str.store()
        if "reor_group" in self.inputs:
            reor_struct_group = load_group(self.inputs.reor_group.value)
            reor_struct_group.add_nodes(struct_str)
        if "frag_label" in self.inputs:
            struct_extras = EntityExtras(struct_str)
            struct_extras.set("smiles", self.inputs.frag_label.value)
        self.ctx.rot_structure = struct_str

    def result(self):
        """Parse results"""
        self.out("rotated_structure", self.ctx.rot_structure)


class SubstituentParameterWorkChain(WorkChain):
    """A workchain to perform the full suite of KLG's substituent parameter determining"""

    @classmethod
    def define(cls, spec):
        """Define workchain steps"""
        super().define(spec)
        spec.input("g16_opt_params", valid_type=Dict, required=True)
        spec.input("g16_sp_params", valid_type=Dict, required=True)
        spec.input("aim_params", valid_type=AimqbParameters, required=True)
        spec.input("structure_str", valid_type=Str, required=True)
        spec.input("g16_code", valid_type=Code)
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
        # spec.input("file", valid_type=SinglefileData)
        # spec.output('aim_dict',valid_type=Dict)
        spec.input("aim_code", valid_type=Code)
        spec.input("dry_run", valid_type=Bool, default=lambda: Bool(False))
        # spec.input("frag_label", valid_type=Str)
        # spec.output("rotated_structure", valid_type=Str)
        spec.output("parameter_dict", valid_type=Dict)
        spec.outline(cls.g16_opt, cls.aim_reor, cls.g16_sp, cls.aim, cls.result)

    def g16_opt(self):
        """Submit the Gaussian optimization"""
        builder = GaussianCalculation.get_builder()
        builder.structure_str = self.inputs.structure_str
        builder.parameters = self.inputs.g16_opt_params
        if "frag_label" in self.inputs:
            builder.fragment_label = self.inputs.frag_label
        builder.code = self.inputs.g16_code
        if "opt_wfx_group" in self.inputs:
            builder.wfxgroup = self.inputs.opt_wfx_group
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 4}
        builder.metadata.options.max_memory_kb = int(6400 * 1.25) * 1024
        builder.metadata.options.max_wallclock_seconds = 604800
        if self.inputs.dry_run.value:
            return self.inputs
        process_node = self.submit(builder)
        if "gaussian_opt_group" in self.inputs:
            g16_opt_group = load_group(self.inputs.gaussian_opt_group)
            g16_opt_group.add_nodes(process_node)
        out_dict = {"opt": process_node}
        # self.ctx.standard_wfx = process_node.get_outgoing().get_node_by_label("wfx")
        return ToContext(out_dict)

    def aim_reor(self):
        """Submit the Aimqb calculation and reorientation"""
        builder = AIMAllReor.get_builder()
        builder.aim_params = self.inputs.aim_params
        builder.file = self.ctx.opt.base.links.get_outgoing().get_node_by_label("wfx")
        builder.aim_code = self.inputs.aim_code
        builder.dry_run = self.inputs.dry_run
        if "frag_label" in self.inputs:
            builder.frag_label = self.inputs.frag_label
        if self.inputs.dry_run.value:
            return self.inputs
        process_node = self.submit(builder)
        out_dict = {"prereor_aim": process_node}
        return ToContext(out_dict)

    def g16_sp(self):
        """Run Gaussian Single Point calculation"""
        builder = GaussianCalculation.get_builder()
        builder.structure_str = (
            self.ctx.prereor_aim.base.links.get_outgoing().get_node_by_label(
                "rotated_structure"
            )
        )
        builder.parameters = self.inputs.g16_sp_params
        if "frag_label" in self.inputs:
            builder.fragment_label = self.inputs.frag_label
        builder.code = self.inputs.g16_code
        if "sp_wfx_group" in self.inputs:
            builder.wfxgroup = self.inputs.sp_wfx_group
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 4}
        builder.metadata.options.max_memory_kb = int(6400 * 1.25) * 1024
        builder.metadata.options.max_wallclock_seconds = 604800
        if self.inputs.dry_run.value:
            return self.inputs
        process_node = self.submit(builder)
        if "gaussian_sp_group" in self.inputs:
            g16_sp_group = load_group(self.inputs.gaussian_sp_group)
            g16_sp_group.add_nodes(process_node)
        out_dict = {"sp": process_node}
        # self.ctx.standard_wfx = process_node.get_outgoing().get_node_by_label("wfx")
        return ToContext(out_dict)

    def aim(self):
        """Run Final AIM Calculation"""
        builder = AimqbCalculation.get_builder()
        builder.parameters = self.inputs.aim_params
        builder.file = self.ctx.sp.base.links.get_outgoing().get_node_by_label("wfx")
        builder.code = self.inputs.aim_code
        # if "frag_label" in self.inputs:
        #     builder.frag_label = self.inputs.frag_label
        builder.metadata.options.parser_name = "aimall.group"
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 2}
        num_atoms = len(
            self.ctx.prereor_aim.base.links.get_outgoing()
            .get_node_by_label("rotated_structure")
            .value.split("\n")
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
