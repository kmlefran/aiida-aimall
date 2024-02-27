"""Tests for aiida_aimall.controllers"""
import io

import pytest
from aiida.common.exceptions import NotExistent
from aiida.orm import Group, SinglefileData

# pylint:disable=no-name-in-module
from aiida_aimall.controllers import AimReorSubmissionController


def test_unstored_parentgrouplabel_returns_error():
    """Test that error returns when parent group are not defined"""
    with pytest.raises(NotExistent) as excinfo:
        AimReorSubmissionController(
            parent_group_label="empty",
            group_label="opt_workchain",
            max_concurrent=1,
            code_label="test.aimall.aimqb",
            reor_group="test",
        )
    assert str(excinfo.value) == "No result was found"


@pytest.mark.usefixtures("aiida_profile")
def test_aimreor_controller(fixture_code):
    """Test that error returns when groups are not defined"""

    gr = Group(label="opt_wfx")
    gr.store()
    code = fixture_code("aimall")
    # with pytest.raises(NotExistent) as excinfo:
    con = AimReorSubmissionController(
        parent_group_label="opt_wfx",
        group_label="prereor_aim",
        max_concurrent=1,
        code_label=code.label + "@" + code.computer.label,
        reor_group="test",
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
    assert "frag_label" in ins
    assert "aim_code" in ins
    assert "aim_params" in ins
    assert "file" in ins
    assert "reor_group" in ins
    assert wf.get_name() == "AIMAllReor"
