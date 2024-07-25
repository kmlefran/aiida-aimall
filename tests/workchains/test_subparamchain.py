"""Tests for aiida_aimall.workchains.SubstituentParameterWorkchain"""
import io

import ase.io
from aiida.common import LinkType
from aiida.orm import Dict, StructureData
from plumpy.utils import AttributesFrozendict


def test_setup(generate_workchain_subparam, generate_workchain_aimreor):
    """Test creation of `AimReorWorkChain`."""
    process = generate_workchain_subparam(generate_workchain_aimreor)

    assert isinstance(process.inputs, AttributesFrozendict)


# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
def test_default(
    generate_workchain_subparam,
    fixture_localhost,
    generate_workchain_aimreor,
    generate_g16_inputs,
    generate_calc_job_node,
    fixture_code,
):
    """Test the default inputs of `SubstituentParameterWorkchain"""
    entry_point_calc_job_aim = "aimall.aimqb"
    entry_point_calc_job_gauss = "aimall.gaussianwfx"
    name = "default"
    # create the workchain node
    wkchain = generate_workchain_subparam(generate_workchain_aimreor)
    # test the first workchain step
    gaussian_inputs = wkchain.g16_opt()
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
    wkchain.ctx.opt = g16_node
    # gaussian_folder = generate_workchain_folderdata(entry_point_name, gaussianopttest)
    # gaussian_folder.base.links.add_incoming(
    #     g16_node, link_type=LinkType.CREATE, link_label="retrieved"
    # )
    # gaussian_folder.store()
    assert wkchain.classify_opt_wfx() is None
    assert "opt_wfx" in wkchain.ctx
    # Run dry_run aim_reor
    aim_reor_inputs = wkchain.aim_reor()
    assert isinstance(aim_reor_inputs, AttributesFrozendict)
    # Generate mock aim_reor outputs
    aim_reor_node = generate_workchain_aimreor()
    wkchain.ctx.prereor_aim = aim_reor_node.node
    # dummy roughly tetrahedral methane string
    f = io.StringIO(
        "5\n\n C -0.1 2.0 -0.02\nH 0.3 1.0 -0.02\nH 0.3 2.5 0.8\nH 0.3 2.5 -0.9\nH -1.2 2.0 -0.02"
    )
    structure_node = StructureData(ase=ase.io.read(f, format="xyz"))
    f.close()
    structure_node.store()
    structure_node.base.links.add_incoming(
        aim_reor_node.node, link_type=LinkType.RETURN, link_label="rotated_structure"
    )

    # Test gaussian single point
    g16_sp_inputs = wkchain.g16_sp()
    assert isinstance(g16_sp_inputs, AttributesFrozendict)
    # generate mock gaussian singlepoint outputs
    g16_sp_node = generate_calc_job_node(
        entry_point_calc_job_gauss,
        fixture_localhost,
        name,
        generate_g16_inputs(fixture_code),
        test_folder_type="workchains",
    )
    wkchain.ctx.sp = g16_sp_node

    assert wkchain.classify_sp_wfx() is None
    assert "sp_wfx" in wkchain.ctx
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
    wkchain.ctx.final_aim = aim_sp_node
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
