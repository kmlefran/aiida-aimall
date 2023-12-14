# pylint: disable=redefined-outer-name
"""Tests for the `AimqbParser"""

import os

import pytest
from aiida import orm
from aiida.common import AttributeDict
from aiida.orm import SinglefileData

from aiida_aimall.data import AimqbParameters


@pytest.fixture
def generate_aimqb_inputs():
    """Generates inputs of a default aimqb calculation"""

    def _generate_aimqb_inputs(fixture_code, filepath_tests):
        """Return only those inputs the parser will expect to be there"""
        parameters = AimqbParameters({"naat": 2, "nproc": 2})
        inputs = {
            "code": fixture_code("aimall"),
            "parameters": parameters,
            "file": SinglefileData(
                os.path.join(
                    filepath_tests,
                    "parsers/inputs",
                    "h2_opt.wfx",
                )
            ),
            "metadata": {
                "options": {
                    "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 2},
                }
            },
        }
        return AttributeDict(inputs)

    return _generate_aimqb_inputs


def test_aimqb_parser_default(  # pylint:disable=too-many-arguments
    fixture_localhost,
    generate_calc_job_node,
    generate_parser,
    generate_aimqb_inputs,
    fixture_code,
    filepath_tests,
):
    """Test an aimqb calculation"""
    name = "default"
    entry_point_calc_job = "aimall"
    entry_point_parser = "aimqb.base"
    node = generate_calc_job_node(
        entry_point_calc_job,
        fixture_localhost,
        name,
        generate_aimqb_inputs(fixture_code, filepath_tests),
    )
    parser = generate_parser(entry_point_parser)
    results, calcfunction = parser.parse_from_node(node, store_provenance=False)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_finished_ok, calcfunction.exit_message
    assert not orm.Log.collection.get_logs_for(node), [
        log.message for log in orm.Log.collection.get_logs_for(node)
    ]
    assert "atomic_properties" in results
    assert "bcp_properties" in results
