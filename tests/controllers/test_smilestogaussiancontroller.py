"""Tests for aiida_aimall.controllers"""
import io

import pytest
from aiida.common.exceptions import NotExistent
from aiida.orm import Group, SinglefileData

# pylint:disable=no-name-in-module
from aiida_aimall.controllers import SmilesToGaussianController


def test_unstored_parentgrouplabel_returns_error():
    """Test that error returns when parent group are not defined"""
    with pytest.raises(NotExistent) as excinfo:
        SmilesToGaussianController(
            parent_group_label="empty",
            group_label="opt_workchain",
            code_label="test.aimall.aimqb",
            max_concurrent=1,
            g16_opt_params={},
            wfxgroup="wfx",
            nprocs=4,
            mem_mb=6400,
            time_s=3600,
        )
    assert str(excinfo.value) == "No result was found"


@pytest.mark.usefixtures("aiida_profile")
def test_aimreor_controller(fixture_code):
    """Test that error returns when groups are not defined"""

    gr = Group(label="smitogaussian")
    gr.store()
    code = fixture_code("aimall")
    # with pytest.raises(NotExistent) as excinfo:
    con = SmilesToGaussianController(
        parent_group_label="smitogaussian",
        group_label="opt_workchain",
        code_label=code.label,
        max_concurrent=1,
        g16_opt_params={},
        wfxgroup="wfx",
        nprocs=4,
        mem_mb=6400,
        time_s=3600,
    )
    assert con.get_extra_unique_keys() == ("smiles",)
    wfx = SinglefileData(
        io.BytesIO(b"C 0.0 0.0 0.0\nH -0.5,0.0,0.0\nC 0.5 0.0 0.0\n H 1.0, 0.0,0.0")
    )
    wfx.store()
    wfx.base.extras.set("smiles", "unique")
    gr.add_nodes(wfx)
    ins, wf = con.get_inputs_and_processclass_from_extras(extras_values=["unique"])
    print(ins)
    assert isinstance(ins, dict)
    assert "smiles" in ins
    assert "gaussian_parameters" in ins
    assert "gaussian_code" in ins
    assert "wfxgroup" in ins
    assert "nprocs" in ins
    assert "mem_mb" in ins
    assert "time_s" in ins
    assert wf.get_name() == "SmilesToGaussianWorkchain"
