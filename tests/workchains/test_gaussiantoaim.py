"""Tests for aiida_aimall.workchains.SubstituentParameterWorkchain"""

from aiida.common import LinkType
from aiida.orm import Dict
from plumpy.utils import AttributesFrozendict


def test_setup(generate_workchain_g16toaim):
    """Test creation of `AimReorWorkChain`."""
    process = generate_workchain_g16toaim()

    assert isinstance(process.inputs, AttributesFrozendict)


# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
def test_default(
    generate_workchain_g16toaim,
    fixture_localhost,
    generate_g16_inputs,
    generate_calc_job_node,
    fixture_code,
):
    """Test the default inputs of `SubstituentParameterWorkchain"""
    entry_point_calc_job_aim = "aimall.aimqb"
    entry_point_calc_job_gauss = "aimall.gaussianwfx"
    name = "default"
    # create the workchain node
    wkchain = generate_workchain_g16toaim()
    # test the first workchain step
    gaussian_inputs = wkchain.g16()
    assert isinstance(gaussian_inputs, AttributesFrozendict)
    # Generate mock CalcJobNodes and needed outputs for the gaussian optimization
    g16_node = generate_calc_job_node(
        entry_point_name=entry_point_calc_job_gauss,
        computer=fixture_localhost,
        test_name=name,
        inputs=generate_g16_inputs(fixture_code),
        test_folder_type="workchains",
    )
    g16_node.store()
    wkchain.ctx.g16 = g16_node

    assert wkchain.classify_wfx() is None
    assert "wfx" in wkchain.ctx
    # Run dry_run aim_reor

    # Generate mock aim_reor outputs

    # Test aim
    aim_inputs = wkchain.aim()
    assert isinstance(aim_inputs, AttributesFrozendict)
    # generate mock aim outputs
    aim_sp_node = generate_calc_job_node(
        entry_point_calc_job_aim,
        fixture_localhost,
        name,
        generate_g16_inputs(fixture_code),
        test_folder_type="workchains",
    )
    wkchain.ctx.aim = aim_sp_node
    out_dict = Dict(
        {"atomic_properties": {}, "bcp_properties": {}, "cc_properties": {}}
    )
    out_dict.base.links.add_incoming(
        aim_sp_node, link_type=LinkType.CREATE, link_label="output_parameters"
    )
    out_dict.store()
    # Test results of the workchain
    assert wkchain.result() is None
    assert "parameter_dict" in wkchain.outputs
