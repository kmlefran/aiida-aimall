# pylint: disable=redefined-outer-name
"""Tests for the `AimqbParser"""
# pylint:disable=too-many-positional-arguments


import pytest

# from aiida import orm
from aiida.common import exceptions


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
    entry_point_calc_job = "aimall.aimqb"
    entry_point_parser = "aimall.base"

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
    # assert not orm.Log.collection.get_logs_for(node), [
    #     log.message for log in orm.Log.collection.get_logs_for(node)
    # ]
    assert "output_parameters" in results
    results_dict = results["output_parameters"].get_dict()
    assert "atomic_properties" in results_dict
    assert "bcp_properties" in results_dict
    assert "cc_properties" in results_dict


def test_empty_outfolder_returns_exitcode(  # pylint:disable=too-many-arguments
    fixture_localhost,
    generate_calc_job_node,
    generate_parser,
    generate_aimqb_inputs,
    fixture_code,
    filepath_tests,
):
    """Test an aimqb calculation"""
    name = "empty"
    entry_point_calc_job = "aimall.aimqb"
    entry_point_parser = "aimall.base"

    node = generate_calc_job_node(
        entry_point_calc_job,
        fixture_localhost,
        name,
        generate_aimqb_inputs(fixture_code, filepath_tests),
    )

    parser = generate_parser(entry_point_parser)

    _, calcfunction = parser.parse_from_node(node, store_provenance=False)
    assert (
        calcfunction.exit_status
        == node.process_class.exit_codes.ERROR_MISSING_OUTPUT_FILES.status
    )


def test_gaussiannode_returns_error(  # pylint:disable=too-many-arguments
    fixture_localhost,
    generate_calc_job_node,
    fixture_code,
    filepath_tests,
    generate_parser,
    generate_aimqb_inputs,
):
    """Test that a Gaussian node returns error on parser"""
    entry_point_calc_job = "gaussian"
    entry_point_parser = "aimall.base"
    name = "default"
    node = generate_calc_job_node(
        entry_point_calc_job,
        fixture_localhost,
        name,
        generate_aimqb_inputs(fixture_code, filepath_tests),
    )
    parser = generate_parser(entry_point_parser)
    with pytest.raises(exceptions.ParsingError) as excinfo:
        parser.parse_from_node(node, store_provenance=False)
    assert str(excinfo.value) == "Can only parse AimqbCalculation"
