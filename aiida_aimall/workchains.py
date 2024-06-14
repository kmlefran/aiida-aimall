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
import re
import sys
from functools import partial

import multiprocess as mp
import pandas as pd
from aiida.engine import ToContext, WorkChain, calcfunction
from aiida.orm import Code, Dict, Int, List, SinglefileData, Str, load_group
from aiida.orm.extras import EntityExtras
from aiida.plugins.factories import CalculationFactory, DataFactory
from group_decomposition.fragfunctions import (
    count_uniques,
    identify_connected_fragments,
    merge_uniques,
    output_ifc_dict,
)
from group_decomposition.utils import all_data_from_cml, list_to_str, xyz_list_to_str
from rdkit import Chem
from rdkit.Chem import AllChem, rdmolops, rdqueries
from rdkit.Chem.MolKey.MolKey import BadMoleculeException
from subproptools.sub_reor import rotate_substituent_aiida

old_stdout = sys.stdout

# load the needed calculations and data types
GaussianCalculation = CalculationFactory("aimall.gaussianwfx")
AimqbParameters = DataFactory("aimall.aimqb")
AimqbCalculation = CalculationFactory("aimall.aimqb")
DictData = DataFactory("core.dict")
PDData = DataFactory("dataframe.frame")


def parallel_frags(inp, bb_patt, input_type):
    """Generate list of dictionaries and unique frame for each cml file

    Args:
        inp: input for identify_connected_fragments, typically cml file name
        bb_patt: pattern for third bond break
        input_type: typically cml file

    Returns:
        list of dictionaries and unique frame

    """
    frame = identify_connected_fragments(
        inp, bb_patt=bb_patt, input_type=input_type, include_parent=True
    )
    done_smi = []
    dict_list = []
    unique_frame = pd.DataFrame()
    if frame is not None:
        frame["Smiles"] = frame["Smiles"].apply(
            lambda x: re.sub(r"\[[0-9]+\*\]", "*", x)
        )
        # frame_list.append(frame)
        mol = frame.at[0, "Parent"]
        frag_dict, done_smi = output_ifc_dict(mol, frame, done_smi)
        if frag_dict is not None:
            dict_list.append(frag_dict)
        unique_frame = count_uniques(frame, False, uni_smi_type=False)
    return [dict_list, unique_frame]


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


@calcfunction
def parse_cml_files(singlefiledata):
    """Extract needed data from cml

    Args:
        singlefiledata: cml file stored in database as SinglefileData"""
    return Dict(all_data_from_cml(singlefiledata.get_content().split("\n")))


@calcfunction
def generate_cml_fragments(params, cml_Dict, n_procs, prev_smi):
    """Fragment the molecule defined by a CML

    Args:
        params: parameters for the fragmenting
        cml_Dict: results of parse_cml_files
    Returns:
        dict
    """
    # pylint:disable=too-many-locals
    # pylint:disable=too-many-statements
    done_smi = prev_smi.get_list()
    cml_list = (
        cml_Dict.get_dict().values()
    )  # maybe just don't store cml files in database, just pass list to cgis here
    param_dict = params.get_dict()  # get dict from aiida node
    input_type = param_dict["input_type"]  # should set to cmldict
    bb_patt = param_dict["bb_patt"]

    # done_smi = []
    # dict_list = []
    fd = {}
    # out_frame = pd.DataFrame()
    with mp.Pool(n_procs.value) as pool:  # pylint:disable=not-callable no-member
        result_list = list(
            pool.map(
                partial(parallel_frags, bb_patt=bb_patt, input_type=input_type),
                cml_list,
            )
        )
    frame_list = [res[1] for res in result_list]
    for res in result_list:
        frag_dict = res[0]
        if frag_dict:
            for key in frag_dict[0].keys():
                if key not in done_smi:
                    done_smi.append(key)
                    # dict_list.append(frag_dict[0][key])
                    fd[key] = frag_dict[0][key]

    while len(frame_list) > 1:
        frame_list = frame_list[2:] + [merge_uniques(frame_list[0], frame_list[1])]
    out_frame = frame_list[0]
    out_frame = out_frame.drop("Molecule", axis=1)
    out_frame = out_frame.drop("Parent", axis=1)

    out_dict = {}
    # for fd in dict_list:
    for key, value in fd.items():
        rep_key = (
            key.replace("*", "Att")
            .replace("#", "t")
            .replace("(", "lb")
            .replace(")", "rb")
            .replace("-", "Neg")
            .replace("+", "Pos")
            .replace("[", "ls")
            .replace("]", "rs")
            .replace("=", "d")
        )
        if rep_key not in list(
            out_dict.keys()  # pylint:disable=consider-iterating-dictionary
        ):  # pylint:disable=consider-iterating-dictionary
            out_dict[rep_key] = DictData(value)
        else:
            with open("repeated_smiles.txt", "a", encoding="utf-8") as of:
                of.write(f"{rep_key} repeated\n")
    col_names = list(out_frame.columns)
    # Find indices of relevant columns
    xyz_idx = col_names.index("xyz")
    atom_idx = col_names.index("Atoms")
    label_idx = col_names.index("Labels")
    type_idx = col_names.index("atom_types")
    count_idx = col_names.index("count")
    nat_idx = col_names.index("numAttachments")
    out_frame["xyzstr"] = out_frame.apply(
        lambda row: xyz_list_to_str(row[xyz_idx]), axis=1
    )
    out_frame["atomstr"] = out_frame.apply(
        lambda row: list_to_str(row[atom_idx]), axis=1
    )
    out_frame["labelstr"] = out_frame.apply(
        lambda row: list_to_str(row[label_idx]), axis=1
    )
    out_frame["typestr"] = out_frame.apply(
        lambda row: xyz_list_to_str(row[type_idx]), axis=1
    )
    out_frame["countstr"] = out_frame.apply(lambda row: str(row[count_idx]), axis=1)
    out_frame["numatstr"] = out_frame.apply(lambda row: str(row[nat_idx]), axis=1)
    out_frame = out_frame.drop("xyz", axis=1)
    out_frame = out_frame.drop("Atoms", axis=1)
    out_frame = out_frame.drop("Labels", axis=1)
    out_frame = out_frame.drop("atom_types", axis=1)
    out_frame = out_frame.drop("count", axis=1)
    out_frame = out_frame.drop("numAttachments", axis=1)

    node_frame = PDData(out_frame)

    out_dict["cgis_frame"] = node_frame
    out_dict["done_smi"] = List(done_smi)
    return out_dict


@calcfunction
def update_g16_params(g16dict, fragdict):
    """Update input g16 params with charge and multiplicity

    :param g16dict:
    :param type g16dict: aiida.orm.nodes.data.dict.Dict
    """
    param_dict = g16dict.get_dict()
    frag_dict = fragdict.get_dict()
    param_dict.update({"charge": frag_dict["charge"]})
    param_dict.update({"multiplicity": 1})
    return Dict(dict=param_dict)


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

    zero_at = h_mol_rw.GetAtomsMatchingQuery(query)[0]
    # this will be bonded to one atom - whichever atom in the bond is not *, is the one we are looking for
    bond = zero_at.GetBonds()[0]
    begin_atom = bond.GetBeginAtom()
    if begin_atom.GetSymbol() != "*":
        attached_atom = begin_atom
    else:
        attached_atom = bond.GetEndAtom()
    return h_mol_rw, zero_at, attached_atom


def reorder_molecule(h_mol_rw, zero_at, attached_atom):
    """Reindexes the atoms in a molecule, setting attached_atom to index 0, and zero_at to index 2

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
        AiiDA Dictionary of {'xyz':str, 'charge':int,'multiplicity':int}

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


# @calcfunction
# def get_previous_smiles(group_label):
#     """given lab  for group which we store them in, find all the lists of our done SMILES and combine them into one list"""
#     query = QueryBuilder()
#     # find the group aim_reor, assign it the tag group
#     query.append(Group, filters={"label": group_label.value}, tag="group")
#     # In that group, find AimqbCalculations
#     query.append(orm.List, tag="lists", with_group="group")
#     if query.all():
#         donesmi_lists = [lst[0] for lst in query.all()]
#     else:
#         donesmi_lists = []
#     smile_list = []
#     if donesmi_lists:
#         for lst in donesmi_lists:
#             smile_list = smile_list + lst.get_list()
#     return List(list(set(smile_list)))


# @calcfunction
# def get_substituent_inputs(smiles_list_List, done_smi_List):
#     """given smiles_list and previously dones SMILES, create inputs for all those not previously done"""
#     smiles_list = smiles_list_List.get_list()
#     done_smi = done_smi_List.get_list()
#     smiles_to_run = list(set(smiles_list) - set(done_smi))
#     res = {
#         smiles.replace("*", "Att")
#         .replace("#", "t")
#         .replace("(", "lb")
#         .replace(")", "rb")
#         .replace("-", "Neg")
#         .replace("+", "Pos")
#         .replace("[", "ls")
#         .replace("]", "rs")
#         .replace("=", "d"): get_substituent_input(smiles)
#         for smiles in smiles_to_run
#     }
#     if res:
#         res["done_smi"] = List(smiles_to_run)
#     return res


@calcfunction
def parameters_with_cm(parameters, smiles_dict):
    """Add charge and multiplicity keys to Gaussian Input"""
    parameters_dict = parameters.get_dict()
    smiles_dict_dict = smiles_dict.get_dict()
    parameters_dict["charge"] = smiles_dict_dict["charge"]
    parameters_dict["multiplicity"] = smiles_dict_dict["multiplicity"]
    return Dict(parameters_dict)


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
        node = self.submit(builder)
        out_dict = {"opt": node}
        return ToContext(out_dict)

    def results(self):
        """Store our relevant information as output"""
        self.out("wfx", self.ctx["opt"].get_outgoing().get_node_by_label("wfx"))
        self.out(
            "output_parameters",
            self.ctx["opt"].get_outgoing().get_node_by_label("output_parameters"),
        )


# class MultiFragmentWorkChain(WorkChain):
#     """Workchain to fragment a cml file and generate gaussian calculations on each fragment"""

#     @classmethod
#     def define(cls, spec):
#         super().define(spec)
#         spec.input("cml_file_dict", valid_type=Dict)
#         spec.input("frag_params", valid_type=Dict)
#         spec.input(
#             "prev_smi", valid_type=List, default=lambda: List([]), required=False
#         )
#         spec.input("frag_group", valid_type=Str, required=False)
#         spec.input("frame_group", valid_type=Str, required=False)
#         # spec.input("g16_code", valid_type=Code)
#         spec.input("procs", valid_type=Int, default=lambda: Int(8))
#         # spec.input('aim_code',valid_type=Code)
#         # spec.input('aim_params',valid_type=AimqbParameters)
#         # spec.input("g16_opt_params", valid_type=Dict)
#         # spec.input('g16_sp_params',valid_type=Dict)
#         spec.outline(cls.generate_fragments)

#     def generate_fragments(self):
#         """perform the fragmenting"""
#         fdict = generate_cml_fragments(
#             self.inputs.frag_params,
#             self.inputs.cml_file_dict,
#             self.inputs.procs,
#             self.inputs.prev_smi,
#         )
#         if "frag_group" in self.inputs:
#             g16_opt_group = load_group(self.inputs.frag_group)
#         for key, val in fdict.items():
#             if key not in ["done_smi", "cgis_frame"]:
#                 val.store()
#                 struct_extras = EntityExtras(val)
#                 struct_extras.set("smiles", key)
#                 if "frag_group" in self.inputs:
#                     g16_opt_group.add_nodes(val)
#             elif key == "cgis_frame" and "frame_group" in self.inputs:
#                 g = load_group(self.inputs.frame_group)
#                 g.add_nodes(val)
#         self.ctx.fragments = fdict

# def submit_fragmenting(self):
#     """submit all the fragmenting jobs as gaussian calculations"""
#     for key, molecule in self.ctx.fragments.items():
#         # print(molecule)
#         if isinstance(molecule, Dict):
#             self.submit(
#                 G16OptWorkchain,
#                 g16_opt_params=self.inputs.g16_opt_params,
#                 fragment_dict=molecule,
#                 frag_label=Str(key),
#                 g16_code=self.inputs.g16_code,
#             )
#         sleep(10)

# aim_code=self.inputs.aim_code,
# aim_params=self.inputs.aim_params,
# g16_sp_params = self.inputs.g16_sp_params)


# class G16OptWorkchain(WorkChain):
#     """Run G16 Calculation on a fragment produced by MultiFragmentWorkChain

#     Process continues through the use of AimReorSubmissionController
#     """

#     @classmethod
#     def define(cls, spec):
#         super().define(spec)
#         spec.input("g16_opt_params", valid_type=Dict)
#         spec.input("fragment_dict", valid_type=Dict)
#         spec.input("frag_label", valid_type=Str)
#         spec.input("g16_code", valid_type=Code)
#         spec.input("wfxgroup", valid_type=Str, required=False)
#         spec.output("output", valid_type=Dict)
#         spec.outline(
#             cls.dict_to_struct,
#             cls.update_g16_param,
#             cls.g16_opt,
#             cls.result,
#         )  # ,cls.aimall)#, cls.aimall,cls.reorient,cls.aimall)

#     def dict_to_struct(self):
#         """Generate the structure input in Gaussian Format"""
#         self.ctx.structure = dict_to_structure(self.inputs.fragment_dict)

#     def update_g16_param(self):
#         """Update parameters with correct charge and multiplicity"""
#         self.ctx.params_with_cm = update_g16_params(
#             self.inputs.g16_opt_params, self.inputs.fragment_dict
#         )

#     def g16_opt(self):
#         """Submit the Gaussian optimization"""
#         builder = GaussianCalculation.get_builder()
#         builder.structure_str = self.ctx.structure
#         builder.parameters = self.ctx.params_with_cm
#         builder.fragment_label = self.inputs.frag_label
#         builder.code = self.inputs.g16_code
#         if "wfxgroup" in self.inputs:
#             builder.wfxgroup = self.inputs.wfxgroup
#             g16_opt_group = load_group(self.inputs.wfxgroup)
#         builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 4}
#         builder.metadata.options.max_memory_kb = int(6400 * 1.25) * 1024
#         builder.metadata.options.max_wallclock_seconds = 604800
#         process_node = self.submit(builder)
#         if "wfxgroup" in self.inputs:
#             g16_opt_group.add_nodes(process_node)
#         out_dict = {"opt": process_node}
#         # self.ctx.standard_wfx = process_node.get_outgoing().get_node_by_label("wfx")
#         return ToContext(out_dict)

#     def result(self):
#         """Parse the results"""
#         self.out("output", self.ctx.opt.outputs.output_parameters)


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
        aim_calc = self.submit(builder)
        aim_calc.store()
        if "aim_group" in self.inputs:
            aim_noreor_group = load_group(self.inputs.aim_group)
            aim_noreor_group.add_nodes(aim_calc)
        out_dict = {"aim": aim_calc}
        return ToContext(out_dict)

    def rotate(self):
        """perform the rotation"""
        aimfolder = self.ctx["aim"].get_outgoing().get_node_by_label("retrieved")
        output_dict = (
            self.ctx["aim"]
            .get_outgoing()
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
        builder.file = self.ctx.opt.get_outgoing().get_node_by_label("wfx")
        builder.aim_code = self.inputs.aim_code
        if "frag_label" in self.inputs:
            builder.frag_label = self.inputs.frag_label
        process_node = self.submit(builder)
        out_dict = {"prereor_aim": process_node}
        return ToContext(out_dict)

    def g16_sp(self):
        """Run Gaussian Single Point calculation"""
        builder = GaussianCalculation.get_builder()
        builder.structure_str = self.ctx.prereor_aim.get_outgoing().get_node_by_label(
            "rotated_structure"
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
        builder.file = self.ctx.sp.get_outgoing().get_node_by_label("wfx")
        builder.code = self.inputs.aim_code
        # if "frag_label" in self.inputs:
        #     builder.frag_label = self.inputs.frag_label
        builder.metadata.options.parser_name = "aimall.group"
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 2}
        num_atoms = len(
            self.ctx.prereor_aim.get_outgoing()
            .get_node_by_label("rotated_structure")
            .value.split("\n")
        )
        #  generalize for substrates other than H
        builder.group_atoms = List([x + 1 for x in range(0, num_atoms) if x != 1])
        process_node = self.submit(builder)
        out_dict = {"final_aim": process_node}
        return ToContext(out_dict)

    def result(self):
        """Put results in output node"""
        self.out(
            "parameter_dict",
            self.ctx.final_aim.get_outgoing().get_node_by_label("output_parameters"),
        )
