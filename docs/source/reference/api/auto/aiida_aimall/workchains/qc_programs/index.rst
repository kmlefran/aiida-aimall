:py:mod:`aiida_aimall.workchains.qc_programs`
=============================================

.. py:module:: aiida_aimall.workchains.qc_programs

.. autoapi-nested-parse::

   Workchains to interface various quantum software with AiiDA



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.workchains.qc_programs.QMToAIMWorkChain
   aiida_aimall.workchains.qc_programs.GaussianToAIMWorkChain
   aiida_aimall.workchains.qc_programs.GenerateWFXToAIMWorkChain




.. py:class:: QMToAIMWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   Workchain to link quantum chemistry jobs without plugins to AIMAll

   .. py:method:: define(spec)
      :classmethod:

      Define the specification of the process, including its inputs, outputs and known exit codes.

      A `metadata` input namespace is defined, with optional ports that are not stored in the database.



   .. py:method:: shell_job()

      Launch a shell job


   .. py:method:: aim()

      Launch an AIMQB calculation


   .. py:method:: result()

      Put results in output node



.. py:class:: GaussianToAIMWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida_aimall.workchains.input.BaseInputWorkChain`

   A workchain to submit a Gaussian calculation and automatically setup an AIMAll calculation on the output

   .. py:method:: define(spec)
      :classmethod:

      Define workchain steps


   .. py:method:: gauss()

      Run Gaussian calculation


   .. py:method:: classify_wfx()

      Add the wavefunction file from the previous step to the correct group and set the extras


   .. py:method:: aim()

      Run Final AIM Calculation


   .. py:method:: result()

      Put results in output node



.. py:class:: GenerateWFXToAIMWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   Workchain to generate a wfx file from computational chemistry output files and submit that to an AIMQB Calculation

   .. note::

      This workchain uses the IOData module of the Ayer's group Horton to generate the wfx files. Supported file formats
      include .fchk files, molden files (from Molpro, Orca, PSI4, Turbomole, and Molden), and CP2K atom log files. Further
      note that .fchk files can simply be provided directly to an `AimqbCalculation`.

      While IOData accepts other file formats, these formats are the ones available that contain the necessary information
      to generate wfc files

   .. py:method:: define(spec)
      :classmethod:

      Define the specification of the process, including its inputs, outputs and known exit codes.

      A `metadata` input namespace is defined, with optional ports that are not stored in the database.



   .. py:method:: generate_wfx()

      Given SinglefileData generates a wfx file if IOData is capable


   .. py:method:: aim()

      Run AIM on the generated wfx file


   .. py:method:: result()

      Put results in output node
