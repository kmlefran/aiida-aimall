""" Tests for calculations."""
import os

from aiida import load_profile
from aiida.engine import run
from aiida.orm import Dict, SinglefileData  # , load_code
from aiida.plugins import CalculationFactory, DataFactory

from . import TEST_DIR


def test_process(aimall_code):
    # def test_process():
    """Test running a calculation
    note this does not test that the expected outputs are created of output parsing"""
    load_profile()
    # Prepare input parameters
    AimqbParameters = DataFactory("aimall")
    parameters = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})

    file = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files", "water_wb97xd_augccpvtz_qtaim.wfx")
    )
    # code = load_code("aimall")
    # set up calculation
    builder = CalculationFactory("aimall").get_builder()
    builder.code = aimall_code
    builder.parameters = parameters
    builder.file = file
    builder.metadata.options.resources = {
        "num_machines": 1,
        "tot_num_mpiprocs": 2,
    }

    # inputs = {
    #     "code": aimall_code,
    #     # "code": code,
    #     "parameters": parameters,
    #     "file": file,
    #     "metadata.options.resources": {
    #         "num_machines": 1,
    #         "tot_num_mpiprocs": 2,
    #     },
    # }

    result = run(builder)
    computed_atomic_props = result["atomic_properties"].get_dict()
    computed_bcp_props = result["bcp_properties"].get_dict()

    assert computed_atomic_props is Dict
    assert computed_bcp_props is Dict
