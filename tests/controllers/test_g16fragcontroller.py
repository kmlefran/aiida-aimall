"""Tests for aiida_aimall.controllers"""
import pytest
from aiida.common.exceptions import NotExistent
from aiida.orm import Group, Str

# pylint:disable=no-name-in-module
from aiida_aimall.controllers import G16FragController

# pylint:disable=no-name-in-module
from aiida_aimall.workchains import G16OptWorkchain  # pylint:disable=no-name-in-module


def test_unstored_parentgrouplabel_returns_error():
    """Test that error returns when groups are not defined"""
    with pytest.raises(NotExistent) as excinfo:
        G16FragController(
            parent_group_label="empty",
            group_label="opt_workchain",
            max_concurrent=1,
            code_label="test.aimall.aimqb",
            g16_opt_params={},
        )
    assert str(excinfo.value) == "No result was found"


@pytest.mark.usefixtures("aiida_profile")
def test_g16frag_controller():
    """Test that error returns when groups are not defined"""
    gr = Group(label="inp_frag")
    gr.store()
    # with pytest.raises(NotExistent) as excinfo:
    con = G16FragController(
        parent_group_label="inp_frag",
        group_label="opt_workchain",
        max_concurrent=1,
        code_label="test.aimall.aimqb",
        g16_opt_params={},
    )
    assert con.get_extra_unique_keys() == ("smiles",)
    struct = Str("C 0.0 0.0 0.0\nH -0.5,0.0,0.0\nC 0.5 0.0 0.0\n H 1.0, 0.0,0.0")
    struct.base.extras.set("smiles", "CtC")
    struct.store()
    ins, wfs = con.get_inputs_and_processclass_from_extras(extras_values="CtC")
    assert isinstance(ins, dict)
    assert "frag_label" in ins
    assert "fragment_dict" in ins
    assert "g16_code" in ins
    assert "g16_opt_params" in ins
    assert isinstance(wfs, G16OptWorkchain)
