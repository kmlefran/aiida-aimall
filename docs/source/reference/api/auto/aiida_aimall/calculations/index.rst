:py:mod:`aiida_aimall.calculations`
===================================

.. py:module:: aiida_aimall.calculations

.. autoapi-nested-parse::

   Calculations provided by aiida_aimall.

   Upon pip install, AimqbCalculation is accessible in AiiDA.calculations plugins
   Using the 'aimall' entry point, and GaussianWFXCalculation is accessible with the 'gaussianwfx'
   entry point



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.calculations.AimqbCalculation
   aiida_aimall.calculations.GaussianWFXCalculation




Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_aimall.calculations.AimqbParameters


.. py:data:: AimqbParameters



.. py:class:: AimqbCalculation(*args, **kwargs)


   Bases: :py:obj:`aiida.engine.CalcJob`

   AiiDA calculation plugin wrapping the aimqb executable.

   .. attribute:: parameters

      command line parameters for the AimqbCalculation

      :type: AimqbParameters

   .. attribute:: file

      the wfx, wfn, or fchk file to be run

      :type: SinglefileData

   .. attribute:: code

      code of the AIMQB executable

      :type: Code

   .. attribute:: attached_atom_int

      the integer label of the atom in the group that is attached to the rest of the molecule

      :type: Int

   .. attribute:: group_atoms

      integer ids of atoms comprising the group for AimqbGroupParser

      :type: List(Int)

   .. rubric:: Example

   ::

       code = orm.load_code('aimall@localhost')
       AimqbParameters = DataFactory("aimall.aimqb")
       aim_params = AimqbParameters(parameter_dict={"naat": 2, "nproc": 2, "atlaprhocps": True})
       file = SinglefileData("/absolute/path/to/file")
       # Alternatively, if you have the file as a string, you can build the file with:
       # file=SinglefileData(io.BytesIO(file_string.encode()))
       AimqbCalculation = CalculationFactory("aimall.aimqb")
       builder  = AimqbCalculation.get_builder()
       builder.parameters = aim_params
       builder.file = file
       builder.code = code
       builder.metadata.options.resources = {"num_machines": 1, "num_mpiprocs_per_machine": 2}
       builder.submit()

   .. note::

      By default, the AimqbBaseParser is used, getting atomic, BCP, and (if applicable) LapRhoCps.
          You can opt to use the AimqbGroupParser, which also returns the integrated group properties model
          of a group, as well as the atomic graph descriptor of the group. This is done by providing this to the builder:

      ::

          builder.metadata.options.parser_name = "aimall.group"

   .. py:attribute:: INPUT_FILE
      :value: 'aiida.wfx'



   .. py:attribute:: OUTPUT_FILE
      :value: 'aiida.out'



   .. py:attribute:: PARENT_FOLDER_NAME
      :value: 'parent_calc'



   .. py:attribute:: DEFAULT_PARSER
      :value: 'aimall.base'



   .. py:method:: define(spec)
      :classmethod:

      Define inputs and outputs of the calculation


   .. py:method:: prepare_for_submission(folder)

      Create input files.

      :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily
          place all files needed by the calculation.
      :return: `aiida.common.datastructures.CalcInfo` instance



.. py:class:: GaussianWFXCalculation(*args, **kwargs)


   Bases: :py:obj:`aiida.engine.CalcJob`

   AiiDA calculation plugin wrapping Gaussian. Adapted from aiida-gaussian
          https://github.com/nanotech-empa/aiida-gaussian, Copyright (c) 2020 Kristjan Eimre.
          Additions made to enable providing molecule input as orm.Str,
          and wfx files are retrieved by default. We further define another input wfxgroup in which you can provide an
          optional group to store the wfx file in and fragment_label as an optional extra to add on the output.

      Args:
          structure: StructureData for molecule to be run. Do not provide structure AND structure_str, but provide
          at least one
          structure_str: Str for molecule to be run. e.g. orm.Str(H 0.0 0.0 0.0
   H -1.0 0.0 0.0)
          Do not provide structure AND structure_str, but provide at least one
          wfxgroup: Str of a group to add the .wfx files to
          parameters: required: Dict of Gaussian parameters, same as from aiida-gaussian. Note that the options provided should
          generate a wfx file. See Example
          settings: optional, additional input parameters
          fragment_label: Str, optional: an extra to add to the wfx file node. Involved in the controllers,
          which check extras
          parent_calc_folder: RemoteData, optional: the folder of a completed gaussian calculation

      Example:
      ::

          builder = GaussianCalculation.get_builder()
          builder.structure_str = orm.Str("H 0.0 0.0 0.0 -1.0 0.0 0.0") # needs newline but docs doesn't like
          builder.parameters = orm.Dict(dict={
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
          builder.code = orm.load_code("g16@localhost")
          builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 4}
          builder.metadata.options.max_memory_kb = int(6400 * 1.25) * 1024
          builder.metadata.options.max_wallclock_seconds = 604800
          submit(builder)



   .. py:attribute:: INPUT_FILE
      :value: 'aiida.inp'



   .. py:attribute:: OUTPUT_FILE
      :value: 'aiida.out'



   .. py:attribute:: PARENT_FOLDER_NAME
      :value: 'parent_calc'



   .. py:attribute:: DEFAULT_PARSER
      :value: 'aimall.gaussianwfx'



   .. py:method:: define(spec)
      :classmethod:

      Define the process specification, including its inputs, outputs and known exit codes.

      Ports are added to the `metadata` input namespace (inherited from the base Process),
      and a `code` input Port, a `remote_folder` output Port and retrieved folder output Port
      are added.

      :param spec: the calculation job process spec to define.


   .. py:method:: prepare_for_submission(folder)

      This is the routine to be called when you want to create
      the input files and related stuff with a plugin.

      :param folder: a aiida.common.folders.Folder subclass where
                         the plugin should put all its files.


   .. py:method:: _render_input_string_from_params(parameters, structure_string)
      :classmethod:

      Generate the Gaussian input file using pymatgen.
