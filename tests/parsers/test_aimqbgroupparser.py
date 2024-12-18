"""Test aiida-aimall group parser"""
# pylint:disable=too-many-positional-arguments
import os

import pytest
from aiida.common import AttributeDict
from aiida.orm import Int, List, SinglefileData

from aiida_aimall.data import AimqbParameters


@pytest.fixture(name="generate_aimqb_group_inputs")
def fixture_generate_aimqb_group_inputs():
    """Generates inputs of a default aimqb calculation"""

    def _generate_aimqb_group_inputs(fixture_code, filepath_tests):
        """Return only those inputs the parser will expect to be there"""
        parameters = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})
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
            "attached_atom_int": Int(1),
            "group_atoms": List([1, 3]),
            "metadata": {
                "options": {
                    "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 2},
                }
            },
        }
        return AttributeDict(inputs)

    return _generate_aimqb_group_inputs


@pytest.fixture(name="generate_aimqb_group_inputs_no_groupatoms")
def fixture_generate_aimqb_group_inputs_no_groupatoms():
    """Generates inputs of a default aimqb calculation"""

    def _generate_aimqb_group_inputs_no_groupatoms(fixture_code, filepath_tests):
        """Return only those inputs the parser will expect to be there"""
        parameters = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})
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
            "group_atoms": List([]),
            "attached_atom_int": Int(1),
            "metadata": {
                "options": {
                    "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 2},
                }
            },
        }
        return AttributeDict(inputs)

    return _generate_aimqb_group_inputs_no_groupatoms


def test_aimqb_parser_group(  # pylint:disable=too-many-arguments
    fixture_localhost,
    generate_calc_job_node,
    generate_parser,
    generate_aimqb_group_inputs,
    fixture_code,
    filepath_tests,
):
    """Test an aimqb calculation"""
    name = "group"
    entry_point_calc_job = "aimall.aimqb"
    entry_point_parser = "aimall.group"
    node = generate_calc_job_node(
        entry_point_calc_job,
        fixture_localhost,
        name,
        generate_aimqb_group_inputs(fixture_code, filepath_tests),
    )
    parser = generate_parser(entry_point_parser)
    results, calcfunction = parser.parse_from_node(node, store_provenance=False)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_finished_ok, calcfunction.exit_message
    # assert not orm.Log.collection.get_logs_for(node), [
    #     log.message for log in orm.Log.collection.get_logs_for(node)
    # ]
    # check that all the expected output is parsed
    assert "output_parameters" in results
    results_dict = results["output_parameters"].get_dict()
    assert "atomic_properties" in results_dict
    assert "bcp_properties" in results_dict
    assert "cc_properties" in results_dict
    assert "graph_descriptor" in results_dict
    assert "group_descriptor" in results_dict


def test_aimqb_parser_group_no_groupatoms_input(  # pylint:disable=too-many-arguments
    fixture_localhost,
    generate_calc_job_node,
    generate_parser,
    generate_aimqb_group_inputs_no_groupatoms,
    fixture_code,
    filepath_tests,
):
    """Test an aimqb calculation"""
    name = "group"
    entry_point_calc_job = "aimall.aimqb"
    entry_point_parser = "aimall.group"
    node = generate_calc_job_node(
        entry_point_calc_job,
        fixture_localhost,
        name,
        generate_aimqb_group_inputs_no_groupatoms(fixture_code, filepath_tests),
    )
    parser = generate_parser(entry_point_parser)
    results, calcfunction = parser.parse_from_node(node, store_provenance=False)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_finished_ok, calcfunction.exit_message
    # assert not orm.Log.collection.get_logs_for(node), [
    #     log.message for log in orm.Log.collection.get_logs_for(node)
    # ]
    # check that all the expected output is parsed
    assert "output_parameters" in results
    results_dict = results["output_parameters"].get_dict()
    assert "atomic_properties" in results_dict
    assert "bcp_properties" in results_dict
    assert "cc_properties" in results_dict
    assert "graph_descriptor" in results_dict
    assert "group_descriptor" in results_dict


def test_group_empty_outfolder_returns_exitcode(  # pylint:disable=too-many-arguments
    fixture_localhost,
    generate_calc_job_node,
    generate_parser,
    generate_aimqb_group_inputs,
    fixture_code,
    filepath_tests,
):
    """Test an aimqb calculation"""

    name = "empty"
    entry_point_calc_job = "aimall.aimqb"
    entry_point_parser = "aimall.group"
    node = generate_calc_job_node(
        entry_point_calc_job,
        fixture_localhost,
        name,
        generate_aimqb_group_inputs(fixture_code, filepath_tests),
    )
    parser = generate_parser(entry_point_parser)
    _, calcfunction = parser.parse_from_node(node, store_provenance=False)

    assert (
        calcfunction.exit_status
        == node.process_class.exit_codes.ERROR_MISSING_OUTPUT_FILES.status
    )
