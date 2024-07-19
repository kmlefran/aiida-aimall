"""Tests for AimReor Workchain"""
# import os

from aiida.common import LinkType
from aiida.orm import Dict, SinglefileData, Str

# from aiida.plugins import WorkflowFactory
from plumpy.utils import AttributesFrozendict
from subproptools import qtaim_extract as qt

# from aiida_aimall.workchains import dict_to_structure, generate_rotated_structure_aiida


def test_setup(generate_workchain_aimreor):
    """Test creation of `AimReorWorkChain`."""
    process = generate_workchain_aimreor()

    assert isinstance(process.inputs, AttributesFrozendict)


# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
def test_default(
    generate_workchain_aimreor,
    fixture_localhost,
    generate_workchain_folderdata,
    generate_aimqb_inputs,
    generate_calc_job_node,
    fixture_code,
    filepath_tests,
):
    """Test instantiating the WorkChain, then mock its process, by calling methods in the ``spec.outline``."""
    entry_point_name = "aimall.aimreor"
    entry_point_calc_job = "aimall.aimqb"
    test = "default"
    name = "default"
    wkchain = generate_workchain_aimreor()
    aim_inputs = wkchain.aimall()
    assert isinstance(aim_inputs, AttributesFrozendict)

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
    node = generate_calc_job_node(
        entry_point_calc_job,
        fixture_localhost,
        name,
        generate_aimqb_inputs(fixture_code, filepath_tests),
    )
    node.store()
    output_parameters = Dict({"atomic_properties": a_props, "cc_properties": cc_dict})
    output_parameters.base.links.add_incoming(
        node, link_type=LinkType.CREATE, link_label="output_parameters"
    )
    output_parameters.store()
    wkchain.ctx.aim = node
    # aim_folder.base.links.add_incoming(node,link_type=LinkType.CREATE,link_label='retrieved')
    assert wkchain.rotate() is None
    assert "rot_struct_dict" in wkchain.ctx
    assert isinstance(wkchain.ctx.rot_struct_dict, Dict)
    assert wkchain.dict_to_struct_reor() is None
    assert "rot_structure" in wkchain.ctx
    assert isinstance(wkchain.ctx.rot_structure, Str)
    assert wkchain.result() is None
    assert "rotated_structure" in wkchain.outputs
