"""tests for AimqbCalculation"""


from aiida.common import datastructures
from aiida.engine import ExitCode
from aiida.orm import Dict, Str, StructureData


def test_gaussianwfx_default(fixture_sandbox, generate_calc_job, fixture_code):
    """Tests that a GaussianWFXCalculation can be instantiated"""
    entry_point_name = "aimall.gaussianwfx"
    g16_sp_params = {
        "functional": "PBE1PBE",
        "basis_set": "6-31g",
        "charge": 0,
        "multiplicity": 2,
        "link0_parameters": {
            "%chk": "aiida.chk",
            "%mem": "1024MB",
            "%nprocshared": 4,
        },
        "route_parameters": {
            "scf": {
                "maxcycle": 128,
                "cdiis": None,
            },
            "nosymm": None,
            "output": "wfx",
            "opt": "tight",
        },
        "input_parameters": {"output.wfx": None},  # appended at the end of the input
    }
    inputs = {
        "fragment_label": Str("H"),
        "code": fixture_code("gaussianwfx"),
        "parameters": Dict(g16_sp_params),
        "structure_str": Str("H 0.0 0.0 0.0"),
        "wfxgroup": Str("test"),
        "metadata": {
            "options": {
                "resources": {"num_machines": 1, "tot_num_mpiprocs": 1},
                "max_memory_kb": int(3200 * 1.25) * 1024,
                "max_wallclock_seconds": 604800,
            }
        },
    }

    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert isinstance(calc_info.codes_info[0], datastructures.CodeInfo)


def test_gaussianwfx_not_both_structure_and_structurestr(
    fixture_sandbox, generate_calc_job, fixture_code
):
    """Tests that a GaussianWFXCalculation can be instantiated"""
    entry_point_name = "aimall.gaussianwfx"
    unit_cell = [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]

    structure = StructureData(cell=unit_cell)
    g16_sp_params = {
        "functional": "PBE1PBE",
        "basis_set": "6-31g",
        "charge": 0,
        "multiplicity": 2,
        "link0_parameters": {
            "%chk": "aiida.chk",
            "%mem": "1024MB",
            "%nprocshared": 4,
        },
        "route_parameters": {
            "scf": {
                "maxcycle": 128,
                "cdiis": None,
            },
            "nosymm": None,
            "output": "wfx",
            "opt": "tight",
        },
        "input_parameters": {"output.wfx": None},  # appended at the end of the input
    }
    inputs = {
        "fragment_label": Str("H"),
        "code": fixture_code("gaussianwfx"),
        "parameters": Dict(g16_sp_params),
        "structure_str": Str("H 0.0 0.0 0.0"),
        "structure": structure,
        "wfxgroup": Str("test"),
        "metadata": {
            "options": {
                "resources": {"num_machines": 1, "tot_num_mpiprocs": 1},
                "max_memory_kb": int(3200 * 1.25) * 1024,
                "max_wallclock_seconds": 604800,
            }
        },
    }

    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert isinstance(calc_info, ExitCode)
    assert calc_info.status == 410


def test_gaussianwfx_structureinput(fixture_sandbox, generate_calc_job, fixture_code):
    """Tests that a GaussianWFXCalculation can be instantiated"""
    entry_point_name = "aimall.gaussianwfx"
    unit_cell = [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]

    structure = StructureData(cell=unit_cell)
    structure.append_atom(position=(0.0, 0.0, 0.0), symbols="Li")
    g16_sp_params = {
        "functional": "PBE1PBE",
        "basis_set": "6-31g",
        "charge": 0,
        "multiplicity": 2,
        "link0_parameters": {
            "%chk": "aiida.chk",
            "%mem": "1024MB",
            "%nprocshared": 4,
        },
        "route_parameters": {
            "scf": {
                "maxcycle": 128,
                "cdiis": None,
            },
            "nosymm": None,
            "output": "wfx",
            "opt": "tight",
        },
        "input_parameters": {"output.wfx": None},  # appended at the end of the input
    }
    inputs = {
        "fragment_label": Str("H"),
        "code": fixture_code("gaussianwfx"),
        "parameters": Dict(g16_sp_params),
        "structure": structure,
        "wfxgroup": Str("test"),
        "metadata": {
            "options": {
                "resources": {"num_machines": 1, "tot_num_mpiprocs": 1},
                "max_memory_kb": int(3200 * 1.25) * 1024,
                "max_wallclock_seconds": 604800,
            }
        },
    }

    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert isinstance(calc_info.codes_info[0], datastructures.CodeInfo)
