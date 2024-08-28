:py:mod:`aiida_aimall.calculations`
===================================

.. py:module:: aiida_aimall.calculations

.. autoapi-nested-parse::

   `CalcJob` implementation for the aimqb executable of AIMAll.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.calculations.AimqbCalculation




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
