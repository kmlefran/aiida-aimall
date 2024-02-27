"""Tests for aiida_aimall.controllers"""
import pytest
from aiida.common.exceptions import NotExistent
from aiida.orm import Group, Str

# pylint:disable=no-name-in-module
from aiida_aimall.controllers import GaussianSubmissionController

# import aiida_aimall


def test_unstored_parentgrouplabel_returns_error():
    """Test that error returns when groups are not defined"""
    with pytest.raises(NotExistent) as excinfo:
        GaussianSubmissionController(
            parent_group_label="empty",
            group_label="opt_workchain",
            max_concurrent=1,
            code_label="test.aimall.aimqb",
            wfxgroup="test",
            g16_sp_params={},
        )
    assert str(excinfo.value) == "No result was found"


@pytest.mark.usefixtures("aiida_profile")
def test_gaussiansubmission_controller(fixture_code):
    """Test that error returns when groups are not defined"""

    gr = Group(label="reor_structs")
    gr.store()
    code = fixture_code("aimall")
    # with pytest.raises(NotExistent) as excinfo:
    con = GaussianSubmissionController(
        parent_group_label="reor_structs",
        group_label="gaussian_sp",
        max_concurrent=1,
        code_label=code.label + "@" + code.computer.label,
        g16_sp_params={},
        wfxgroup="test",
    )
    assert con.get_extra_unique_keys() == ("smiles",)
    struct = Str("C 0.0 0.0 0.0\nH -0.5,0.0,0.0\nC 0.5 0.0 0.0\n H 1.0, 0.0,0.0")
    struct.store()
    struct.base.extras.set("smiles", "unique")
    gr.add_nodes(struct)
    ins, wf = con.get_inputs_and_processclass_from_extras(extras_values=["unique"])
    assert isinstance(ins, dict)
    assert "fragment_label" in ins
    assert "wfxgroup" in ins
    assert "code" in ins
    assert "parameters" in ins
    assert "structure_str" in ins
    assert "metadata" in ins
    assert "wfxgroup" in ins
    assert wf.get_name() == "GaussianWFXCalculation"
