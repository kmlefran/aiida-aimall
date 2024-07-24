"""Tests for calcfunctions in aiida-aimall workchains"""
# pylint:disable=no-member
import pytest
from aiida.orm import Dict, Int, SinglefileData, Str, StructureData
from rdkit import Chem
from subproptools import qtaim_extract as qt

from aiida_aimall import workchains as aimw


def test_generate_structure_data():
    """Test generate_structure_data function"""
    test_Str = Str(
        "C 0.0 0.0 0.0\nH -1.0 0.0 0.0\nH 1.0 1.0 0.0\nH 1.0 -1.0 1.0\n H 1.0 -1.0 -1.0"
    )
    structure_data = aimw.generate_structure_data(test_Str)
    assert isinstance(structure_data, StructureData)


def test_calc_multiplicity():
    """Tests calc_multiplicity function"""
    mol1 = Chem.MolFromSmiles("C")
    assert aimw.calc_multiplicity(mol1) == 1
    mol2 = Chem.MolFromSmiles("[CH3]")
    assert aimw.calc_multiplicity(mol2) == 2
    mol3 = Chem.MolFromSmiles("[CH2][CH2]")
    assert aimw.calc_multiplicity(mol3) == 3


def test_find_attachment_atoms():
    """Tests find_attachment_atoms function"""
    mol = Chem.MolFromSmiles("*C")
    mol_rw, zero_at, attached_atom = aimw.find_attachment_atoms(mol)
    num_hs = 0
    # explicit hydrogens should have been added - check that
    for atom in mol_rw.GetAtoms():
        if atom.GetSymbol() == "H":
            num_hs += 1
    assert num_hs == 3
    # ensure the placeholder is zero_at
    assert zero_at.GetAtomicNum() == 0
    zbond = zero_at.GetBonds()[0]
    # ensure zero_at and attached_atom are bonded
    assert {attached_atom.GetIdx(), zero_at.GetIdx()} == {
        zbond.GetBeginAtom().GetIdx(),
        zbond.GetEndAtom().GetIdx(),
    }


def test_find_attachment_exceptions():
    """Ensures that find_attachment raises appropriate exceptions with incorrect input"""
    mol = Chem.MolFromSmiles("C")
    # Check that find_attachment returns errors with number of * != 1
    with pytest.raises(ValueError):
        aimw.find_attachment_atoms(mol)
    mol2 = Chem.MolFromSmiles("*C*")
    with pytest.raises(ValueError):
        aimw.find_attachment_atoms(mol2)


def test_reorder_molecule():
    """Test reorder_molecule"""
    mol = Chem.MolFromSmiles("CN*")
    mol_rw, zero_at, attached_atom = aimw.find_attachment_atoms(mol)
    reorder_mol = aimw.reorder_molecule(mol_rw, zero_at, attached_atom)
    # Atom 1 (index 0) should be N soince it is attached to *
    assert reorder_mol.GetAtomWithIdx(0).GetSymbol() == "N"
    # Atom 2 (index 1) was a *, should now be H
    assert reorder_mol.GetAtomWithIdx(1).GetSymbol() == "H"
    # Atom 1 should be bonded to atom 0 - check bond indexes
    at_bond = reorder_mol.GetAtomWithIdx(1).GetBonds()[0]
    assert {0, 1} == {at_bond.GetBeginAtom().GetIdx(), at_bond.GetEndAtom().GetIdx()}


def test_get_xyz():
    """Test get_xyz"""
    mol = Chem.MolFromSmiles("CN*")
    mol_rw, zero_at, attached_atom = aimw.find_attachment_atoms(mol)
    reorder_mol = aimw.reorder_molecule(mol_rw, zero_at, attached_atom)
    out_xyz = aimw.get_xyz(reorder_mol)
    # out_xyz should be a string that when split on newlines is equal in length to number of atoms
    assert isinstance(out_xyz, str)
    split_xyz = out_xyz.split("\n")
    num_atoms = len(split_xyz)
    assert num_atoms == reorder_mol.GetNumAtoms()


def test_get_substituent_input():
    """Test get_substituent_input"""
    out_Dict = aimw.get_substituent_input(Str("*C"))
    out_dict = out_Dict.get_dict()
    # output should be Dict with xyz, charge, and multiplpcity keys
    assert isinstance(out_Dict, Dict)
    assert "xyz" in out_dict
    assert "charge" in out_dict
    assert "multiplicity" in out_dict


def test_parameters_with_cm():
    """Test parameters_with_cm"""
    parameter_dict = Dict({})
    smiles_dict = Dict({"charge": 0, "multiplicity": 1})
    out_Dict = aimw.parameters_with_cm(parameter_dict, smiles_dict)
    assert isinstance(out_Dict, Dict)
    out_dict = out_Dict.get_dict()
    # charge and multiplicity matching the smiles_dict should be in out_Dict
    assert "charge" in out_dict
    assert "multiplicity" in out_dict
    assert out_dict["charge"] == 0
    assert out_dict["multiplicity"] == 1


def test_validate_shell_code():
    """Test validate_shell_code"""
    str_node = Str("aimall")
    # Str node is valid input, should return None
    assert not aimw.validate_shell_code(str_node, "foo")
    int_node = Int(1)
    # Int node is invalid input, should return string error message
    res = aimw.validate_shell_code(int_node, "foo")
    assert (
        res == "the `shell_code` input must be either ShellCode or Str of the command."
    )


def test_validate_file_ext():
    """Test validate_file_ext - provided file extension should be wfx, wfn or fchk"""
    # these should all return None, so check for not None
    wfx_node = Str("wfx")
    assert not aimw.validate_file_ext(wfx_node, "foo")
    wfn_node = Str("wfn")
    assert not aimw.validate_file_ext(wfn_node, "foo")
    fchk_node = Str("fchk")
    assert not aimw.validate_file_ext(fchk_node, "foo")
    # log extension should result in error
    log_node = Str("log")
    err_str = "the `aim_file_ext` input must be a valid file format for AIMQB: wfx, wfn, or fchk"
    assert aimw.validate_file_ext(log_node, "log") == err_str


def test_generate_rotated_structure_aiida(generate_workchain_folderdata):
    """Test generate_rotated_structure_aiida"""
    entry_point_name = "aimall.aimreor"
    test = "default"
    aim_folder = generate_workchain_folderdata(entry_point_name, test)
    with aim_folder.open("aiida.sum", "rb") as handle:
        output_node = SinglefileData(file=handle)
        sum_lines = output_node.get_content()
    a_props = qt.get_atomic_props(sum_lines.split("\n"))
    atom_list = list(a_props.keys())
    cc_dict = {
        x: qt.get_atom_vscc(
            filename=aim_folder.get_object_content(
                "aiida_atomicfiles" + "/" + x.lower() + ".agpviz"
            ).split("\n"),
            atomLabel=x,
            atomicProps=a_props,
            is_lines_data=True,
        )
        for x in atom_list
    }
    rot_Dict = aimw.generate_rotated_structure_aiida(aim_folder, a_props, cc_dict)
    rot_dict = rot_Dict.get_dict()
    assert isinstance(rot_Dict, Dict)
    assert "atom_symbols" in rot_dict
    assert "geom" in rot_dict
    assert abs(rot_dict["geom"][0][0]) < 0.0001
    assert abs(rot_dict["geom"][0][1]) < 0.0001
    assert abs(rot_dict["geom"][0][2]) < 0.0001
    assert rot_dict["geom"][1][0] < 0
    assert abs(rot_dict["geom"][1][1]) < 0.0001
    assert abs(rot_dict["geom"][1][2]) < 0.0001


def test_dict_to_structure():
    """Test dict_to_structure"""
    str_dict = Dict(
        {"atom_symbols": ["H", "H"], "geom": [[-0.5, 0.0, 0.0], [0.5, 0.0, 0.0]]}
    )
    str_str = aimw.dict_to_structure(str_dict)
    assert isinstance(str_str, StructureData)
