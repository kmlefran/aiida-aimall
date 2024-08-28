:py:mod:`aiida_aimall.workchains.subparam`
==========================================

.. py:module:: aiida_aimall.workchains.subparam

.. autoapi-nested-parse::

   `WorkChain` for calculating substituent parameters developed by authors



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.workchains.subparam.SubstituentParameterWorkChain




.. py:class:: SubstituentParameterWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida_aimall.workchains.input.BaseInputWorkChain`

   A workchain to perform the full suite of KLG's substituent parameter determining

   .. py:method:: define(spec)
      :classmethod:

      Define workchain steps


   .. py:method:: get_substituent_inputs_step()

      Get a dictionary of the substituent input for a given SMILES


   .. py:method:: gauss_opt()

      Submit the Gaussian optimization


   .. py:method:: classify_opt_wfx()

      Add the wavefunction file from the previous step to the correct group and set the extras


   .. py:method:: aim_reor()

      Submit the Aimqb calculation and reorientation


   .. py:method:: gauss_sp()

      Run Gaussian Single Point calculation


   .. py:method:: classify_sp_wfx()

      Add the wavefunction file from the previous step to the correct group and set the extras


   .. py:method:: aim()

      Run Final AIM Calculation


   .. py:method:: result()

      Put results in output node
