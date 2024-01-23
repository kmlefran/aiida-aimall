"""Tests for AimReor Workchain"""
# import os

from aiida.orm import Dict, SinglefileData, Str
from plumpy.utils import AttributesFrozendict
from subproptools import qtaim_extract as qt

from aiida_aimall.workchains import dict_to_structure, generate_rotated_structure_aiida


def test_setup(generate_workchain_aimreor):
    """Test creation of `AimReorWorkChain`."""
    process = generate_workchain_aimreor()

    assert isinstance(process.inputs, AttributesFrozendict)


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
    rot_Dict = generate_rotated_structure_aiida(aim_folder, a_props, cc_dict)
    rot_dict = rot_Dict.get_dict()
    assert isinstance(rot_dict, Dict)
    assert "atom_symbols" in rot_dict
    assert "geom" in rot_dict


def test_dict_to_structure():
    """Test dict_to_structure"""
    str_dict = Dict(
        {"atom_symbols": ["H", "H"], "geom": [[-0.5, 0.0, 0.0], [0.5, 0.0, 0.0]]}
    )
    str_str = dict_to_structure(str_dict)
    assert isinstance(str_str, Str)
