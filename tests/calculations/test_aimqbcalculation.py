"""tests for AimqbCalculation"""

import os

from aiida.common import datastructures
from aiida.orm import SinglefileData

from aiida_aimall.data import AimqbParameters


def test_aimqb_default(
    fixture_sandbox, generate_calc_job, fixture_code, filepath_tests
):
    """Tests that an aimcalculation can be instantiated"""
    entry_point_name = "aimall"
    parameters = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})
    inputs = {
        "code": fixture_code("aimall"),
        "parameters": parameters,
        "file": SinglefileData(
            os.path.join(
                filepath_tests(),
                "calculations/inputs",
                "water_wb97xd_augccpvtz_qtaim.wfx",
            )
        ),
        "metadata": {
            "options": {
                "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 2},
            }
        },
    }
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert isinstance(calc_info.codes_info[0], datastructures.CodeInfo)
