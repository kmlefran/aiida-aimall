"""Tests for AimReor Workchain"""
from aiida.common import AttributeDict


def test_setup(generate_workchain_aimreor):
    """Test `AimReorWorkChain.setup`."""
    process = generate_workchain_aimreor()
    process.setup()

    assert isinstance(process.ctx.inputs, AttributeDict)
