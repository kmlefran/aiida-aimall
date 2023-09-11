""" Tests for calculations."""
import os

from aiida.engine import run
from aiida.orm import Dict, SinglefileData
from aiida.plugins import CalculationFactory, DataFactory

from . import TEST_DIR


def test_process(aimall_code):
    """Test running a calculation
    note this does not test that the expected outputs are created of output parsing"""

    # Prepare input parameters
    AimqbParameters = DataFactory("aimall")
    parameters = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})

    file = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files", "water_wb97xd_augccpvtz_qtaim.wfx")
    )

    # set up calculation
    inputs = {
        "code": aimall_code,
        "parameters": parameters,
        "file": file,
    }

    result = run(CalculationFactory("aimall"), **inputs)
    computed_atomic_props = result["atomic_properties"].get_dict()
    computed_bcp_props = result["bcp_properties"].get_dict()

    assert computed_atomic_props is Dict
    assert computed_bcp_props is Dict
