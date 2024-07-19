"""Tests for SmilesToGaussianWorkchain"""
import os

import cclib
from aiida.common import LinkType
from aiida.orm import Dict, SinglefileData
from plumpy.utils import AttributesFrozendict


def test_setup(generate_workchain_aimreor):
    """Test creation of `AimReorWorkChain`."""
    process = generate_workchain_aimreor()

    assert isinstance(process.inputs, AttributesFrozendict)


# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
def test_default(
    generate_workchain_smitog16,
    fixture_localhost,
    generate_workchain_folderdata,
    generate_g16_inputs,
    generate_calc_job_node,
    fixture_code,
    filepath_tests,
):
    """Test the default inputs of `SmilesToGaussianWorkchain"""
    entry_point_name = "aimall.smitog16"
    entry_point_calc_job = "aimall.gaussianwfx"
    test = "default"
    name = "default"
    # create the workchain node
    wkchain = generate_workchain_smitog16()
    # Run the first step - this should put the smiles_geom Dict in context
    # Note that calling the function in the assert statement does run it
    assert wkchain.get_substituent_inputs_step() is None
    assert "smiles_geom" in wkchain.ctx
    assert isinstance(wkchain.ctx.smiles_geom, Dict)
    # Run the second step - this should add charge and multiplicity from the previous Dict
    # to the gaussian parameters, putting a gaussian_cm_params in Dict
    assert wkchain.update_parameters_with_cm() is None
    assert "gaussian_cm_params" in wkchain.ctx
    assert isinstance(wkchain.ctx.gaussian_cm_params, Dict)
    # Try the submit gaussian step, as dry_run which returns the inputs
    gaussian_inputs = wkchain.submit_gaussian()
    assert isinstance(gaussian_inputs, AttributesFrozendict)
    # Generate a mock gaussian node for the workchain and store it in the expected context
    node = generate_calc_job_node(
        entry_point_calc_job,
        fixture_localhost,
        name,
        generate_g16_inputs(fixture_code),
        test_folder_type="workchains",
    )
    node.store()
    wkchain.ctx.opt = node
    # Get a wavefunction file to link to the gaussian calculation as output for use in next step
    gaussian_folder = generate_workchain_folderdata(entry_point_name, test)
    with gaussian_folder.open("aiida.wfx", "rb") as handle:
        output_node = SinglefileData(file=handle)
    output_node.base.links.add_incoming(
        node, link_type=LinkType.CREATE, link_label="wfx"
    )
    output_node.store()
    # parse the log file and add the resulting dictionary to outputs
    filepath_input = os.path.join(
        filepath_tests,
        "workchains/fixtures",
        entry_point_name,
        test,
        "aiida.log",
    )
    parsed_file_dict = cclib.io.ccread(filepath_input).getattributes()
    # this contains unserialized information that we don't need to worry about here
    # this information is normally serialized in the GaussianWFXParser, but don't need it for tests at all
    del parsed_file_dict["metadata"]
    output_parameters = Dict(parsed_file_dict)
    output_parameters.base.links.add_incoming(
        node, link_type=LinkType.CREATE, link_label="output_parameters"
    )
    output_parameters.store()
    # Finish the workchain, adding the wfx and cclib parsed dictionary as workchain outputs
    assert wkchain.results() is None
    assert "wfx" in wkchain.outputs
    assert "output_parameters" in wkchain.outputs
