========
Tutorial
========

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
Having created the parameters for the program, we provide those parameters and a SinglefileData of an AIMQB input file (.fchk, .wfn, .wfx) to AimqbCalculation.
::

    AimqbCalculation = CalculationFactory('aimall.aimqb')
    builder = AimqbCalculation.get_builder()
    builder.parameters = aim_params
    builder.file = SinglefileData('/absolute/path/to/file')
    # Alternatively, if you have file stored as a string as some of the workchains do
    # builder.file = SinglefileData(io.BytesIO(wfx_file_string.encode()))
    builder.code = orm.load_code('aimall@localhost')
    builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 2}
    submit(builder)

Using the AimqbGroupParser
--------------------------
If you wish to extract group properties as defined by the authors, the steps are similar, but an additional option is provided to the builder.
::

    AimqbCalculation = CalculationFactory('aimall.aimqb')
    builder = AimqbCalculation.get_builder()
    builder.parameters = aim_params
    builder.file = SinglefileData('/absolute/path/to/file')
    builder.code = orm.load_code('aimall@localhost')
    builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 2}
    # set the parser to use to aimall.group
    builder.metadata.options.parser_name = "aimall.group"
    builder.group_atoms = List([x + 1 for x in range(0, num_atoms) if x != 1])
    submit(builder)

Workflow Usage
++++++++++++++

Calculating KLG's AIM properties for a single molecule
------------------------------------------------------
Author KLG defines some QTAIM group properties to be used in evaluating properties. This generally involves a multistep
calculation optimize, aim, reorient, single point, aim. The process can be automated on many files using controllers,
see "Running on a set of CML files", below. But, a Workchain is presented that you can use to run single molecules as needed
The code below shows this setup.

::

    from aiida_aimall.workchains import SubstituentParameterWorkChain
    from aiida.engine import submit
    from aiida import orm
    from aiida.plugins.factories import DataFactory
    AimqbParameters = DataFactory("aimall.aimqb")
    builder = SubstituentParameterWorkChain.get_builder()
    builder.g16_opt_params=Dict(dict={
            'link0_parameters': {
                '%chk':'aiida.chk',
                "%mem": "3200MB", # Currently set to use 8000 MB in .sh files
                "%nprocshared": 4,
            },
            'functional':'wb97xd',
            'basis_set':'aug-cc-pvtz',
            'charge': 0,
            'multiplicity': 1,
            'route_parameters': {'opt': None, 'Output':'WFX'},
            "input_parameters": {"output.wfx": None},
        })
    builder.g16_sp_params = Dict(dict={
            'link0_parameters': {
                '%chk':'aiida.chk',
                "%mem": "4000MB",
                "%nprocshared": 4,
            },
            'functional':'wb97xd',
            'basis_set':'aug-cc-pvtz',
            'charge': 0,
            'multiplicity': 1,
            'route_parameters': {'nosymmetry':None, 'Output':'WFX'},
            "input_parameters": {"output.wfx": None},
        })
    builder.aim_params = AimqbParameters(parameter_dict = {"naat": 2, "nproc": 2, "atlaprhocps": True})
    builder.structure_str = orm.Str("H 0.0 0.0 0.0\n H -1.0 0.0 0.0") # simple H2 molecule
    builder.g16_code = orm.load_code("gaussian@localhost")
    builder.aim_code = orm.load_code("aimall@localhost")
    submit(builder)

Running on a set SMILES
-----------------------
Coming soon!

.. _aimqbCMDLine: https://aim.tkgristmill.com/manual/aimqb/aimqb.html#AIMQBCommandLine

.. _groupdecomp: https://github.com/kmlefran/group_decomposition
.. _subproptools: https://github.com/kmlefran/subproptools
