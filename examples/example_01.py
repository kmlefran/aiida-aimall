#!/usr/bin/env python
"""Run a test calculation on localhost.

Usage: ./example_01.py
"""
from os import path
import sys

import click

from aiida import engine
from aiida.common import NotExistent
from aiida.orm import Code
from aiida.plugins import CalculationFactory, DataFactory

# from aiida_aimall import helpers

INPUT_DIR = path.join(path.dirname(path.realpath(__file__)), "input_files")


def test_run(aimall_code):
    """Run a calculation on the localhost computer.

    Uses test helpers to create AiiDA Code on the fly.
    """
    # if not aimall_code:
    #     # get code
    #     computer = helpers.get_computer()
    #     aimall_code = helpers.get_code(entry_point="aimall", computer=computer)

    # Prepare input parameters
    AimqbParameters = DataFactory("aimall")
    parameters = AimqbParameters()

    SinglefileData = DataFactory("singlefile")
    file = SinglefileData(file=path.join(INPUT_DIR, "file1.txt"))

    # set up calculation
    inputs = {
        "code": aimall_code,
        "parameters": parameters,
        "file": file,
        "metadata": {
            "description": "Test job submission with the aiida_aimall plugin",
        },
    }

    # Note: in order to submit your calculation to the aiida daemon, do:
    # from aiida.engine import submit
    # future = submit(CalculationFactory('aimall'), **inputs)
    result = engine.run(CalculationFactory("aimall"), **inputs)
    at_result = list(result["atomic_properties"].get_dict().keys())[0]
    print(f"Calculation ran, first atom is {at_result}")
    # computed_aimqb = result["aimall"].get_content()
    # print(f"Computed aimqb: \n{computed_aimqb}")


@click.command()
@click.argument("codelabel", default="aimall2@localhost")
# @cmdline.utils.decorators.with_dbenv()
# @cmdline.params.options.CODE()
def cli(codelabel):
    """Run example.

    Example usage: $ ./example_01.py --code aimqb@localhost

    Alternative (creates aimall2@localhost-test code): $ ./example_01.py

    Help: $ ./example_01.py --help
    """
    try:
        code = Code.get_from_string(codelabel)
        if code:
            print(f"The code {codelabel} does exist")
    except NotExistent:
        print(f"The code {codelabel} does not exist")
        sys.exit(1)
    test_run(codelabel)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
