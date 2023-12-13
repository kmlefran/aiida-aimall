"""tests for AimqbCalculation"""

from aiida.common import datastructures
from aiida.orm import SinglefileData

from aiida_aimall.data import AimqbParameters


def test_aimqb_default(fixture_sandbox, generate_calc_job, fixture_code):
    """Tests that an aimcalculation can be instantiated"""
    entry_point_name = "aimall"
    parameters = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})
    inputs = {
        "code": fixture_code("aimall"),
        "parameters": parameters,
        "file": SinglefileData("inputs/water_wb97xd_augccpvtz_qtaim"),
        "metadata": {
            "options": {
                "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 2},
            }
        },
    }
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert isinstance(calc_info.codes_info[0], datastructures.CodeInfo)
