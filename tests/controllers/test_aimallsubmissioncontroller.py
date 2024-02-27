"""Tests for aiida_aimall.controllers"""
import io

import pytest
from aiida.common.exceptions import NotExistent
from aiida.orm import Group, SinglefileData

# pylint:disable=no-name-in-module
from aiida_aimall.controllers import AimAllSubmissionController


def test_unstored_parentgrouplabel_returns_error():
    """Test that error returns when parent group are not defined"""
    with pytest.raises(NotExistent) as excinfo:
        AimAllSubmissionController(
            parent_group_label="empty",
            group_label="opt_workchain",
            max_concurrent=1,
            code_label="test.aimall.aimqb",
            aim_parser="aimall.base",
            aimparameters={"naat": 2, "nproc": 2, "atlaprhocps": True},
        )
    assert str(excinfo.value) == "No result was found"


@pytest.mark.usefixtures("aiida_profile")
def test_aimreor_controller(fixture_code):
    """Test that error returns when groups are not defined"""

    gr = Group(label="reor_wfx")
    gr.store()
    code = fixture_code("aimall")
    # with pytest.raises(NotExistent) as excinfo:
    con = AimAllSubmissionController(
        parent_group_label="reor_wfx",
        group_label="reor_aim",
        max_concurrent=1,
        code_label=code.label + "@" + code.computer.label,
        aim_parser="aimall.base",
        aimparameters={"naat": 2, "nproc": 2, "atlaprhocps": True},
    )
    assert con.get_extra_unique_keys() == ("smiles",)
    wfx = SinglefileData(
        io.BytesIO(b"C 0.0 0.0 0.0\nH -0.5,0.0,0.0\nC 0.5 0.0 0.0\n H 1.0, 0.0,0.0")
    )
    wfx.store()
    wfx.base.extras.set("smiles", "unique")
    gr.add_nodes(wfx)
    ins, wf = con.get_inputs_and_processclass_from_extras(extras_values=["unique"])
    assert isinstance(ins, dict)
    assert "code" in ins
    assert "parameters" in ins
    assert "metadata" in ins
    assert "file" in ins
    assert wf.get_name() == "AimqbCalculation"
