"""Tests for AimReor Workchain"""
from plumpy.utils import AttributesFrozendict


def test_setup(generate_workchain_aimreor):
    """Test creation of `AimReorWorkChain`."""
    process = generate_workchain_aimreor()

    assert isinstance(process.inputs, AttributesFrozendict)
