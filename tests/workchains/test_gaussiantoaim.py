"""Tests for aiida_aimall.workchains.SubstituentParameterWorkchain"""

from aiida.common import LinkType
from aiida.orm import Dict, StructureData
from plumpy.utils import AttributesFrozendict


def test_setup(generate_workchain_gausstoaim):
    """Test creation of `AimReorWorkChain`."""
    process = generate_workchain_gausstoaim()

    assert isinstance(process.inputs, AttributesFrozendict)


# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
def test_default_structure(
    generate_workchain_gausstoaim,
    fixture_localhost,
    generate_gauss_inputs,
    generate_calc_job_node,
    fixture_code,
):
    """Test the default inputs of `SubstituentParameterWorkchain"""
    entry_point_calc_job_aim = "aimall.aimqb"
    entry_point_calc_job_gauss = "aimall.gaussianwfx"
    name = "default"
    # create the workchain node
    wkchain = generate_workchain_gausstoaim(input_type="structure")
    # test the first workchain step
    assert wkchain.validate_input() is None
    assert wkchain.is_xyz_input() is False
    assert wkchain.is_smiles_input() is False
    assert wkchain.is_structure_input() is True
    assert wkchain.structure_in_context() is None
    assert "structure" in wkchain.ctx
    assert isinstance(wkchain.ctx.structure, StructureData)
    gaussian_inputs = wkchain.gauss()
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
    wkchain.ctx.gauss = gauss_node

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
        generate_gauss_inputs(fixture_code),
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


def test_default_xyz(
    generate_workchain_gausstoaim,
    fixture_localhost,
    generate_gauss_inputs,
    generate_calc_job_node,
    fixture_code,
):
    """Test the default inputs of `SubstituentParameterWorkchain"""
    entry_point_calc_job_aim = "aimall.aimqb"
    entry_point_calc_job_gauss = "aimall.gaussianwfx"
    name = "default"
    # create the workchain node
    wkchain = generate_workchain_gausstoaim(input_type="xyz")
    # test the first workchain step
    assert wkchain.validate_input() is None
    assert wkchain.is_xyz_input() is True
    assert wkchain.is_smiles_input() is False
    assert wkchain.is_structure_input() is False
    assert wkchain.create_structure_from_xyz() is None
    assert "structure" in wkchain.ctx
    assert isinstance(wkchain.ctx.structure, StructureData)
    gaussian_inputs = wkchain.gauss()
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
    wkchain.ctx.gauss = gauss_node

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
        generate_gauss_inputs(fixture_code),
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


def test_default_smiles(
    generate_workchain_gausstoaim,
    fixture_localhost,
    generate_gauss_inputs,
    generate_calc_job_node,
    fixture_code,
):
    """Test the default inputs of `SubstituentParameterWorkchain"""
    entry_point_calc_job_aim = "aimall.aimqb"
    entry_point_calc_job_gauss = "aimall.gaussianwfx"
    name = "default"
    # create the workchain node
    wkchain = generate_workchain_gausstoaim(input_type="smiles")
    # test the first workchain step
    assert wkchain.validate_input() is None
    assert wkchain.is_xyz_input() is False
    assert wkchain.is_smiles_input() is True
    assert wkchain.is_structure_input() is False
    assert wkchain.get_molecule_inputs_step() is None
    assert "smiles_geom" in wkchain.ctx
    assert isinstance(wkchain.ctx.smiles_geom, Dict)
    assert "xyz" in wkchain.ctx.smiles_geom
    assert "charge" in wkchain.ctx.smiles_geom
    assert "multiplicity" in wkchain.ctx.smiles_geom
    assert wkchain.string_to_StructureData() is None
    assert "structure" in wkchain.ctx
    assert isinstance(wkchain.ctx.structure, StructureData)
    gaussian_inputs = wkchain.gauss()
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
    wkchain.ctx.gauss = gauss_node

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
        generate_gauss_inputs(fixture_code),
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
