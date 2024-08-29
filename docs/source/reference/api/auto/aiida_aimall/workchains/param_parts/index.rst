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

   Workchain to take a SMILES, generate xyz, charge, and multiplicity

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

   Process continues in GaussianSubmissionController

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
