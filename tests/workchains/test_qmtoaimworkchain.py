"""Tests for aiida_aimall.workchains.QMToAIMWorkchain"""
from aiida.common import LinkType
from aiida.orm import Dict, SinglefileData
from plumpy.utils import AttributesFrozendict


def test_setup(generate_workchain_qmtoaim):
    """Test creation of `AimReorWorkChain`."""
    process = generate_workchain_qmtoaim()

    assert isinstance(process.inputs, AttributesFrozendict)


# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
def test_default(
    generate_workchain_qmtoaim,
    fixture_localhost,
    generate_workchain_folderdata,
    filepath_tests,
    generate_aimqb_inputs,
    generate_shelljob_inputs,
    generate_calc_job_node,
    fixture_code,
):
    """Test default running of QTMToAIMWorkchain using orca as an example"""
    entry_point_name = "aimall.qmtoaim"
    entry_point_calc_job = "core.shell"
    entry_point_calc_job_aim = "aimall.aimqb"
    name = "default"
    test = "default"
    wkchain = generate_workchain_qmtoaim()
    wkchain_inputs = wkchain.shell_job()
    assert isinstance(wkchain_inputs, AttributesFrozendict)
    node = generate_calc_job_node(
        entry_point_calc_job,
        fixture_localhost,
        name,
        generate_shelljob_inputs(fixture_localhost, filepath_tests),
        test_folder_type="workchains",
    )
    qm_folder = generate_workchain_folderdata(entry_point_name, test)
    with qm_folder.open("aiida.wfx", "rb") as handle:
        output_node = SinglefileData(file=handle)
    output_node.base.links.add_incoming(
        node, link_type=LinkType.CREATE, link_label="orca_wfx"
    )
    output_node.store()
    wkchain.ctx.qm = node
    inputs = wkchain.aim()
    assert isinstance(inputs, AttributesFrozendict)
    aim_node = generate_calc_job_node(
        entry_point_calc_job_aim,
        fixture_localhost,
        name,
        generate_aimqb_inputs(fixture_code, filepath_tests),
        test_folder_type="workchains",
    )
    wkchain.ctx.aim = aim_node
    out_dict = Dict(
        {"atomic_properties": {}, "bcp_properties": {}, "cc_properties": {}}
    )
    out_dict.base.links.add_incoming(
        aim_node, link_type=LinkType.CREATE, link_label="output_parameters"
    )
    out_dict.store()
    assert wkchain.result() is None
    assert "parameter_dict" in wkchain.outputs
