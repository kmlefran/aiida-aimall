"""Tests for aiida_aimall.workchains.SubstituentParameterWorkchain"""
# pylint:disable=too-many-positional-arguments
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
def test_default_structure(
    generate_workchain_subparam,
    fixture_localhost,
    generate_workchain_aimreor,
    generate_gauss_inputs,
    generate_calc_job_node,
    fixture_code,
):
    """Test the default inputs of `SubstituentParameterWorkchain"""
    entry_point_calc_job_aim = "aimall.aimqb"
    entry_point_calc_job_gauss = "aimall.gaussianwfx"
    name = "default"
    # create the workchain node
    wkchain = generate_workchain_subparam(
        generate_workchain_aimreor, input_type="structure"
    )
    # test the first workchain step
    assert wkchain.validate_input() is None
    assert wkchain.is_xyz_input() is False
    assert wkchain.is_smiles_input() is False
    assert wkchain.is_structure_input() is True
    assert wkchain.structure_in_context() is None
    assert "structure" in wkchain.ctx
    assert isinstance(wkchain.ctx.structure, StructureData)
    gaussian_inputs = wkchain.gauss_opt()
    assert isinstance(gaussian_inputs, AttributesFrozendict)
    # Generate mock CalcJobNodes and needed outputs for the gaussian optimization
    gauss_node = generate_calc_job_node(
        entry_point_name=entry_point_calc_job_gauss,
        computer=fixture_localhost,
        test_name=name,
        inputs=generate_gauss_inputs(fixture_code),
        test_folder_type="workchains",
    )
    gauss_node.store()
    wkchain.ctx.opt = gauss_node
    # gaussian_folder = generate_workchain_folderdata(entry_point_name, gaussianopttest)
    # gaussian_folder.base.links.add_incoming(
    #     gauss_node, link_type=LinkType.CREATE, link_label="retrieved"
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
    gauss_sp_inputs = wkchain.gauss_sp()
    assert isinstance(gauss_sp_inputs, AttributesFrozendict)
    # generate mock gaussian singlepoint outputs
    gauss_sp_node = generate_calc_job_node(
        entry_point_calc_job_gauss,
        fixture_localhost,
        name,
        generate_gauss_inputs(fixture_code),
        test_folder_type="workchains",
    )
    wkchain.ctx.sp = gauss_sp_node

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
        generate_gauss_inputs(fixture_code),
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


def test_default_xyz(
    generate_workchain_subparam,
    fixture_localhost,
    generate_workchain_aimreor,
    generate_gauss_inputs,
    generate_calc_job_node,
    fixture_code,
):
    """Test the default inputs of `SubstituentParameterWorkchain"""
    entry_point_calc_job_aim = "aimall.aimqb"
    entry_point_calc_job_gauss = "aimall.gaussianwfx"
    name = "default"
    # create the workchain node
    wkchain = generate_workchain_subparam(generate_workchain_aimreor, input_type="xyz")
    # test the first workchain step
    assert wkchain.validate_input() is None
    assert wkchain.is_xyz_input() is True
    assert wkchain.is_smiles_input() is False
    assert wkchain.is_structure_input() is False
    assert wkchain.create_structure_from_xyz() is None
    assert "structure" in wkchain.ctx
    assert isinstance(wkchain.ctx.structure, StructureData)
    gaussian_inputs = wkchain.gauss_opt()
    assert isinstance(gaussian_inputs, AttributesFrozendict)
    # Generate mock CalcJobNodes and needed outputs for the gaussian optimization
    gauss_node = generate_calc_job_node(
        entry_point_name=entry_point_calc_job_gauss,
        computer=fixture_localhost,
        test_name=name,
        inputs=generate_gauss_inputs(fixture_code),
        test_folder_type="workchains",
    )
    gauss_node.store()
    wkchain.ctx.opt = gauss_node
    # gaussian_folder = generate_workchain_folderdata(entry_point_name, gaussianopttest)
    # gaussian_folder.base.links.add_incoming(
    #     gauss_node, link_type=LinkType.CREATE, link_label="retrieved"
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
    gauss_sp_inputs = wkchain.gauss_sp()
    assert isinstance(gauss_sp_inputs, AttributesFrozendict)
    # generate mock gaussian singlepoint outputs
    gauss_sp_node = generate_calc_job_node(
        entry_point_calc_job_gauss,
        fixture_localhost,
        name,
        generate_gauss_inputs(fixture_code),
        test_folder_type="workchains",
    )
    wkchain.ctx.sp = gauss_sp_node

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
        generate_gauss_inputs(fixture_code),
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


def test_default_smiles(
    generate_workchain_subparam,
    fixture_localhost,
    generate_workchain_aimreor,
    generate_gauss_inputs,
    generate_calc_job_node,
    fixture_code,
):
    """Test the default inputs of `SubstituentParameterWorkchain"""
    entry_point_calc_job_aim = "aimall.aimqb"
    entry_point_calc_job_gauss = "aimall.gaussianwfx"
    name = "default"
    # create the workchain node
    wkchain = generate_workchain_subparam(
        generate_workchain_aimreor, input_type="smiles"
    )
    assert wkchain.validate_input() is None
    assert wkchain.is_xyz_input() is False
    assert wkchain.is_smiles_input() is True
    assert wkchain.is_structure_input() is False
    assert wkchain.get_substituent_inputs_step() is None
    assert "smiles_geom" in wkchain.ctx
    assert isinstance(wkchain.ctx.smiles_geom, Dict)
    assert "xyz" in wkchain.ctx.smiles_geom
    assert "charge" in wkchain.ctx.smiles_geom
    assert "multiplicity" in wkchain.ctx.smiles_geom
    assert wkchain.string_to_StructureData() is None
    assert "structure" in wkchain.ctx
    assert isinstance(wkchain.ctx.structure, StructureData)
    gaussian_inputs = wkchain.gauss_opt()
    assert isinstance(gaussian_inputs, AttributesFrozendict)
    # Generate mock CalcJobNodes and needed outputs for the gaussian optimization
    gauss_node = generate_calc_job_node(
        entry_point_name=entry_point_calc_job_gauss,
        computer=fixture_localhost,
        test_name=name,
        inputs=generate_gauss_inputs(fixture_code),
        test_folder_type="workchains",
    )
    gauss_node.store()
    wkchain.ctx.opt = gauss_node
    # gaussian_folder = generate_workchain_folderdata(entry_point_name, gaussianopttest)
    # gaussian_folder.base.links.add_incoming(
    #     gauss_node, link_type=LinkType.CREATE, link_label="retrieved"
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
    gauss_sp_inputs = wkchain.gauss_sp()
    assert isinstance(gauss_sp_inputs, AttributesFrozendict)
    # generate mock gaussian singlepoint outputs
    gauss_sp_node = generate_calc_job_node(
        entry_point_calc_job_gauss,
        fixture_localhost,
        name,
        generate_gauss_inputs(fixture_code),
        test_folder_type="workchains",
    )
    wkchain.ctx.sp = gauss_sp_node

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
        generate_gauss_inputs(fixture_code),
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
