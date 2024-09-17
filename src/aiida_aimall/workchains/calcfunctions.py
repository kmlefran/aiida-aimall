"""Calcfunctions used throughout workchains"""
# pylint: disable=c-extension-no-member
# pylint:disable=no-member
import io
from string import digits

import ase.io
from aiida.engine import calcfunction
from aiida.orm import Dict, SinglefileData, Str, StructureData
from rdkit import Chem
from rdkit.Chem import AllChem, rdmolops, rdqueries
from rdkit.Chem.MolKey.MolKey import BadMoleculeException
from subproptools.sub_reor import rotate_substituent_aiida


@calcfunction
def generate_rotated_structure_aiida(FolderData, atom_dict, cc_dict):
    """Rotates the fragment to the defined coordinate system

    Args:
        FolderData (aiida.orm.FolderData): aim calculation folder
        atom_dict: AIM atom dict
        cc_dict: AIM cc_dict

    Returns:
        Dict with keys 'atom_symbols' and 'geom' containing atomic symbols and the
            the rotated geometry.

    """
    return Dict(rotate_substituent_aiida(FolderData, atom_dict, cc_dict))


def remove_numcharss_from_strlist(in_list):
    """Remove digits from a list of strings. e.g. ['O1','H2','H3'] -> ['O','H','H']

    Args:
        in_list: input list to remove digits from

    Returns:
        output list with the numerical digits removed from each element

    Note:
        The intention for this list is to convert numered atomic symbols, e.g. from Gaussian
            to just symbols

    """
    remove_digits = str.maketrans("", "", digits)
    out_list = [i.translate(remove_digits) for i in in_list]
    return out_list


@calcfunction
def dict_to_structure(fragment_dict):
    """Generate a StructureData for Gaussian inputs

    Args:
        fragment_dict (aiida.orm.Dict): AiiDA orm.Dict with keys 'atom_symbols' and 'geom'

    Returns:
        aiida.orm.StructureData for the molecule

    Note:
        input can be generated, for example, by
            :func:`aiida_aimall.workchains.calcfunctions.generate_rotated_structure_aiida`

    """
    inp_dict = fragment_dict.get_dict()
    symbols = inp_dict["atom_symbols"]
    symbols = remove_numcharss_from_strlist(symbols)
    coords = inp_dict["geom"]
    # outstr is xyz file contents
    outstr = ""
    # numatoms then blank line, then coordinates and symbols for each atom
    outstr += f"{len(symbols)}\n\n"
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
    # create StructureData from .xyz file string
    f = io.StringIO(outstr)
    struct_data = StructureData(ase=ase.io.read(f, format="xyz"))
    f.close()
    return struct_data


def calc_multiplicity(mol):
    """Calculate the multiplicity of a molecule as 2S +1

    Loops over the atoms in the molecule and gets number of radical electrons,
    then converts that number to the multiplicity.

    Args:
        mol: rdkit.Chem molecule object

    Returns:
        integer number of multiplicity

    """
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
    """MMFF optimize the molecule to generate xyz coordiantes

    Args:
        reorder_mol: rdkit.Chem molecule output, output of :func:`aiida_aimall.workchains.calcfunctions.reorder_molecule`

    Returns:
        string of the geometry block of an .xyz file

    """
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
        smiles (str): SMILEs of substituent to run

    Returns:
        Dict with keys xyz, charge, multiplicity

    Raise:
        ValueError: if molecule cannot be built from SMILES

    """
    mol = Chem.MolFromSmiles(smiles.value)
    # If the mol could not be built, mol will be None
    if not mol:
        raise ValueError(
            f"Molecule could not be constructed for substituent input SMILES {smiles.value}"
        )
    # add hydrogens to the molecule, and find the atom to put at origin and the atom attached to it
    h_mol_rw, zero_at, attached_atom = find_attachment_atoms(mol)
    # Set zero_at to be the first atom, and attached atom as the second, by number
    reorder_mol = reorder_molecule(h_mol_rw, zero_at, attached_atom)
    xyz_string = get_xyz(reorder_mol)
    if xyz_string == "Could not determine xyz coordinates":
        raise BadMoleculeException(
            "Maximum iterations exceeded, could not determine xyz coordinates for f{smiles.value}"
        )
    # get store charge, multiplicity and geometry
    reorder_mol.UpdatePropertyCache()
    charge = Chem.GetFormalCharge(h_mol_rw)
    multiplicity = calc_multiplicity(h_mol_rw)
    out_dict = Dict({"xyz": xyz_string, "charge": charge, "multiplicity": multiplicity})
    return out_dict


@calcfunction
def generate_structure_data(smiles_dict):
    """Take an input xyz string and convert it to StructureData

    Args:
        smiles_dict: output of :func:`aiida_aimall.workchains.calcfunctions.get_substituent_input`

    Returns:
        StructureData of the molecule

    """
    structure_Str = smiles_dict["xyz"]
    structure_str = structure_Str
    # Use the geometry string and create the xyz string for a full .xyz file
    num_atoms = len(structure_str.split("\n"))
    xyz_string = f"{num_atoms}\n\n" + structure_str
    # Convert string to StructureData by encoding it as a file
    f = io.StringIO(xyz_string)
    struct_data = StructureData(ase=ase.io.read(f, format="xyz"))
    f.close()
    return struct_data


@calcfunction
def parameters_with_cm(parameters, smiles_dict):
    """Add charge and multiplicity keys to Gaussian Input

    Args:
        parameters: dictionary to be provided to GaussianCalculation
        smiles_dict: `aiida_aimall.workchains.calcfunctions.get_substituent_input`

    Returns:
        Dict of Gaussian parameters updated with charge and multiplicity

    """
    parameters_dict = parameters.get_dict()
    smiles_dict_dict = smiles_dict.get_dict()
    parameters_dict["charge"] = smiles_dict_dict["charge"]
    parameters_dict["multiplicity"] = smiles_dict_dict["multiplicity"]
    return Dict(parameters_dict)


@calcfunction
def get_wfxname_from_gaussianinputs(gaussian_parameters):
    """Find the .wfx filename from gaussian_parameters

    Check if input parameters was provided to gaussian_parameters, and if so, look for
    .wfx file names supplied. If it was, return the first .wfx filename found

    Args:
        gaussian_parameters: input dictionary to be provided to GaussianCalculation

    Returns:
        Str of .wfx filename

    """
    gaussian_dict = gaussian_parameters.get_dict()
    if "input_parameters" not in gaussian_dict:
        return Str("")
    object_names = list(gaussian_dict["input_parameters"].keys())
    wfx_files = [x for x in object_names if "wfx" in x]
    if len(wfx_files) >= 1:
        return Str(wfx_files[0])
    if len(wfx_files) == 0:
        wfn_files = [x for x in object_names if "wfn" in x]
        if len(wfn_files) >= 1:
            return Str(wfn_files[0])
        if len(wfn_files) == 0:
            return Str("")
    # should not get here
    return Str("")


@calcfunction
def create_wfx_from_retrieved(wfxname, retrieved_folder):
    """Create wavefunction SinglefileData from retrieved folder

    Args:
        wfxname: Str of the name of a .wfx file to get from the retrieved folder
        retrieved_folder: FolderData of a completed GaussianCalculation

    Returns:
        SinglefileData of the .wfx file to find in the FolderData

    """
    wfx_file_string = retrieved_folder.get_object_content(wfxname.value.strip())
    return SinglefileData(io.BytesIO(wfx_file_string.encode()))


def validate_shell_code(node, _):
    """Validate the shell code, ensuring that it is ShellCode or Str

    Args:
        node: input node to check the type for ShellCode or Str

    Returns:
        None if the type is ShellCode or Str, or error string if node is not

    """
    if node.node_type not in [
        "data.core.code.installed.shell.ShellCode.",
        "data.core.str.Str.",
    ]:
        return "the `shell_code` input must be either ShellCode or Str of the command."
    return None


def validate_parser(node, _):
    """Validate the parser, ensuring that the provided value is one of the accepted values.

    Args:
        node: input node to check the type for ShellCode or Str

    Returns:
        None if the value is aimall.base or aimall.group, or an error string if it is not
    """

    if node.value not in ["aimall.base", "aimall.group"]:
        return "the `aim_parser` input must be either aimall.base or aimall.group"
    return None


def validate_file_ext(node, _):
    """Validates that the file extension provided for AIM is wfx, wfn or fchk

    Args:
        node: node to check the value of to ensure it is in a supported format

    Returns:
        None if the type is ShellCode or Str, or error string if node is not

    """
    if node.value not in ["wfx", "wfn", "fchk"]:
        return "the `aim_file_ext` input must be a valid file format for AIMQB: wfx, wfn, or fchk"
    return None


@calcfunction
def get_molecule_str_from_smiles(smiles):
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
    h_mol_rw = Chem.RWMol(mol)  # Change type of molecule object
    h_mol_rw = Chem.AddHs(h_mol_rw)
    xyz_string = get_xyz(h_mol_rw)
    if xyz_string == "Could not determine xyz coordinates":
        raise BadMoleculeException(
            "Maximum iterations exceeded, could not determine xyz coordinates for f{smiles.value}"
        )
    h_mol_rw.UpdatePropertyCache()
    charge = Chem.GetFormalCharge(h_mol_rw)
    multiplicity = calc_multiplicity(h_mol_rw)
    out_dict = Dict({"xyz": xyz_string, "charge": charge, "multiplicity": multiplicity})
    return out_dict


@calcfunction
def xyzfile_to_StructureData(xyz_SFD):
    """Convert the xyz file provided as SinglefileData to StructureData"""
    with xyz_SFD.as_path() as filepath:
        return StructureData(ase=ase.io.read(filepath, format="xyz"))
