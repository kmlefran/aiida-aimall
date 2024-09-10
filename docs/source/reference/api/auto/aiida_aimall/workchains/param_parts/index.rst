:py:mod:`aiida_aimall.workchains.param_parts`
=============================================

.. py:module:: aiida_aimall.workchains.param_parts

.. autoapi-nested-parse::

   Workchains that are smaller parts of SubstituenParamWorkChain



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.workchains.param_parts.SmilesToGaussianWorkChain
   aiida_aimall.workchains.param_parts.AIMAllReorWorkChain




.. py:class:: SmilesToGaussianWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   Workchain to take a substituent SMILES, and run a Gaussian calculation on that SMILES

   Takes an input SMILES with one placeholder \*, generates a geometry with \* replaced with a hydrogen.
   U

   .. attribute:: smiles

      SMILES of a substiuent. Must contain a single placeholder \*

      :type: aiida.orm.Str

   .. attribute:: gaussian_parameters

      Gaussian calculation for generating a wfx

      :type: aiida.orm.Dict

   .. attribute:: gaussian_code

      Gaussian Code

      :type: aiida.orm.Code

   .. attribute:: wfxname

      name of wfx file provided in gaussian_parameters

      :type: aiida.orm.Str

   .. attribute:: wfxgroup

      group to store the wfx file in

      :type: aiida.orm.Str

   .. attribute:: mem_mb

      amount of memory in MB for the Gaussian calculation

      :type: aiida.orm.Int

   .. attribute:: nprocs

      number of processors for the Gaussian calculation

      :type: aiida.orm.Int

   .. attribute:: time_s

      amount of time to run the Gaussian calculation

      :type: aiida.orm.Int

   .. note:: The SMILES provided should have a single \*.

   .. note:: Uses the charge and multiplicity of the provided SMILES, not that provided to gaussian_parameters

   .. note::

      'output':'wfx' should be provided to `gaussian_parameters`. And a .wfx file name should be provided
      as well

   .. py:method:: define(spec)
      :classmethod:

      Define the specification of the process, including its inputs, outputs and known exit codes.

      A `metadata` input namespace is defined, with optional ports that are not stored in the database.



   .. py:method:: get_substituent_inputs_step()

      Given list of substituents and previously done smiles, get input


   .. py:method:: update_parameters_with_cm()

      Update provided Gaussian parameters with charge and multiplicity of substituent


   .. py:method:: string_to_StructureData()

      Convert an xyz string of molecule geometry to StructureData


   .. py:method:: get_wfx_name()

      Find the wavefunction file in the retrieved node


   .. py:method:: submit_gaussian()

      Submits the gaussian calculation


   .. py:method:: found_wfx_name()

      Check if we found a wfx or wfn file


   .. py:method:: create_wfx_file()

      Create a wavefunction file from the retireved folder


   .. py:method:: results()

      Store our relevant information as output



.. py:class:: AIMAllReorWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   Workchain to run AIM and then reorient the molecule using the results

   Often called in `aiida_aimall.controllers.AimReorSubmissionController`.
   Process continues in `aiida_aimall.controllers.GaussianSubmissionController`.

   .. attribute:: aim_params

      (AimqbParameters): Command line parameters for aimqb

   .. attribute:: file

      .fchk, .wfn, or .wfx file for aimqb input

      :type: aiida.orm.SinglefileData

   .. attribute:: aim_code

      AIMQB code

      :type: aiida.orm.Code

   .. attribute:: frag_label

      Optional SMILES tag of the substituent

      :type: aiida.orm.Str

   .. attribute:: aim_group

      Optional group to put the AIM calculation node in

      :type: aiida.orm.Str

   .. attribute:: reor_group

      Optional group to put the reoriented structure in

      :type: aiida.orm.Str

   Example

       ::

           from aiida_aimall.data import AimqbParameters
           from aiida_aimall.workchains.param_parts import AIMAllReorWorkChain
           from aiida.orm import SinglefileData, load_code
           from aiida.engine import submit
           input_file = SinglefileData("/absolute/path/to/file")
           aim_code = load_code("aimall@localhost")
           aim_params = AimqbParameters({'nproc':2,'naat':2,'atlaprhocps':True})
           builder = AIMAllReorWorkChain.get_builder()
           builder.file = input_file
           builder.aim_code = aim_code
           builder.aim_params = aim_params
           submit(builder)


   .. py:method:: define(spec)
      :classmethod:

      Define the specification of the process, including its inputs, outputs and known exit codes.

      A `metadata` input namespace is defined, with optional ports that are not stored in the database.



   .. py:method:: aimall()

      submit the aimall calculation


   .. py:method:: rotate()

      perform the rotation


   .. py:method:: dict_to_struct_reor()

      generate the gaussian input from rotated structure


   .. py:method:: result()

      Parse results
