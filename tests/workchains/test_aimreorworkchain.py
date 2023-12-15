"""Tests for AimReor Workchain"""
from aiida.common import AttributeDict


def test_setup(generate_workchain_aimreor):
    """Test `AimReorWorkChain.setup`."""
    process = generate_workchain_aimreor()

    assert isinstance(process.inputs, AttributeDict)
