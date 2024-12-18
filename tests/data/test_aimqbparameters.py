""" Tests for calculations."""
# import os

import pytest

# from aiida.engine import run
# from aiida.orm import Dict, SinglefileData  # , load_code
# from aiida.plugins import CalculationFactory, DataFactory
from aiida.plugins import DataFactory

# This si where the test is
# from . import TEST_DIR


@pytest.mark.usefixtures("aiida_profile")
def test_data():
    # def test_process():
    """Test running a calculation
    note this does not test that the expected outputs are created of output parsing"""
    # load_profile()
    # Prepare input parameters
    AimqbParameters = DataFactory("aimall.aimqb")
    parameters = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})
    assert isinstance(parameters, AimqbParameters)
    assert isinstance(
        parameters.__str__(), str  # pylint:disable=unnecessary-dunder-call
    )  # pylint:disable=unnecessary-dunder-call
    # file = SinglefileData(
    #     file=os.path.join(TEST_DIR, "input_files", "water_wb97xd_augccpvtz_qtaim.wfx")
    # )
    # # code = load_code("aimall")
    # # set up calculation
    # builder = CalculationFactory("aimall").get_builder()
    # builder.code = aimall_code
    # builder.parameters = parameters
    # builder.file = file
    # builder.metadata.options.resources = {
    #     "num_machines": 1,
    #     "tot_num_mpiprocs": 2,
    # }

    # result = run(builder)
    # computed_atomic_props = result["atomic_properties"]
    # computed_bcp_props = result["bcp_properties"]

    # assert type(computed_atomic_props) is Dict
    # assert type(computed_bcp_props) is Dict
