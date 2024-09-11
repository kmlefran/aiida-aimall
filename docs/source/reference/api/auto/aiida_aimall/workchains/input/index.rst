:py:mod:`aiida_aimall.workchains.input`
=======================================

.. py:module:: aiida_aimall.workchains.input

.. autoapi-nested-parse::

   Base input workchain



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.workchains.input.BaseInputWorkChain




.. py:class:: BaseInputWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   A workchain to generate and validate inputs.

   Provided an .xyz file as `SinglefileData`, molecule `StructureData`, or SMILES of the molecule
   validates that only one is provided. Then, prepares the input into a format for future GaussianCalculations.

   .. attribute:: structure

      StructureData of molecule to run

      :type: aiida.orm.StructureData

   .. attribute:: smiles

      smiles string of molecule

      :type: aiida.orm.Str

   .. attribute:: xyz_file

      file data of an xyz file

      :type: aiida.orm.SinglefileData

   .. note::

      This is a base class that is used by other WorkChains
          (:func:`aiida_aimall.workchains.subparam.SubstituentParameterWorkChain`, and
          :func:`aiida_aimall.workchains.qc_programs.GaussianToAIMWorkChain`)

   .. py:method:: define(spec)
      :classmethod:

      Define the specification of the process, including its inputs, outputs and known exit codes.

      A `metadata` input namespace is defined, with optional ports that are not stored in the database.



   .. py:method:: is_xyz_input()

      Validates if xyz_file was provided as input


   .. py:method:: is_smiles_input()

      Validates if smiles was provided as input


   .. py:method:: is_structure_input()

      Validates if structure was provided as input


   .. py:method:: validate_input()

      Check that only one of smiles, structure, or xyz_file was input


   .. py:method:: create_structure_from_xyz()

      Convert the xyzfile to StructureData. Calls
      :func:`aiida_aimall.workchains.calcfunctions.xyzfile_to_StructureData`


   .. py:method:: structure_in_context()

      Store the input structure in context, to make consistent with the results of xyz_file or SMILES input.


   .. py:method:: get_molecule_inputs_step()

      Given list of substituents and previously done smiles, get input.
      Calls :func:`aiida_aimall.workchains.calcfunctions.get_molecule_str_from_smiles`


   .. py:method:: string_to_StructureData()

      Convert an xyz string of molecule geometry to StructureData.
      Calls :func:`aiida_aimall.workchains.calcfunctions.generate_structure_data`
