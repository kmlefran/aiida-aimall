========
Tutorial
========

This page can contain a simple tutorial for your code.

Basic Usage
+++++++++++

Create AimqbParameters instance
-------------------------------
aiida-aimall provides a Data class that validates the parameters you are supplying to AIMAll. You can  create such a data type as follows, referring to the list of command line parameters set out in aimqbCMDLine_:
::

    AimqbParameters = DataFactory('aimall.aimqb')
    aim_params = AimqbParameters(parameter_dict={"naat": 2, "nproc": 2, "atlaprhocps": True})

Create and Submit AimqbCalculation
----------------------------------
Having created the parameters for the program, we provide those parameters and a SinglefileData of a AIMQB input file (.fchk, .wfn, .wfx) to AimqbCalculation.
::

    AimqbCalculation = CalculationFactory('aimall.aimqb')
    builder = AimqbCalculation.get_builder()
    builder.parameters = aim_params
    builder.file = SinglefileData('/absolute/path/to/file')
    builder.code = orm.load_code('aimall@localhost')
    # Alternatively, if you have file stored as a string:
    # builder.file = SinglefileData(io.BytesIO(wfx_file_string.encode()))
    submit(builder)

Using the AimqbGroupParser
--------------------------
If you wish to extract, group properties as defined by the authors, the steps are similar, but an additional option is provided to the builder.
::

    AimqbCalculation = CalculationFactory('aimall.aimqb')
    builder = AimqbCalculation.get_builder()
    builder.parameters = aim_params
    builder.file = SinglefileData('/absolute/path/to/file')
    builder.code = orm.load_code('aimall@localhost')
    builder.metadata.options.parser_name = "aimall.group"
    submit(builder)

.. _aimqbCMDLine: https://aim.tkgristmill.com/manual/aimqb/aimqb.html#AIMQBCommandLine
