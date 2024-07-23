:py:mod:`aiida_aimall.controllers`
==================================

.. py:module:: aiida_aimall.controllers

.. autoapi-nested-parse::

   aiida_aimall.controllers

   Subclasses of FromGroupSubmissionController designed to manage local traffic on lab Macs to prevent to many running processes

   Provides controllers for the AimReor WorkChain, AimQBCalculations, and GaussianWFXCalculations



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.controllers.SmilesToGaussianController
   aiida_aimall.controllers.AimReorSubmissionController
   aiida_aimall.controllers.AimAllSubmissionController
   aiida_aimall.controllers.GaussianSubmissionController




Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_aimall.controllers.AimqbParameters
   aiida_aimall.controllers.GaussianCalculation
   aiida_aimall.controllers.AimqbCalculation


.. py:data:: AimqbParameters



.. py:data:: GaussianCalculation



.. py:data:: AimqbCalculation



.. py:class:: SmilesToGaussianController(code_label: str, g16_opt_params: dict, wfxgroup: str, nprocs: int, mem_mb: int, time_s: int, *args, **kwargs)


   Bases: :py:obj:`aiida_submission_controller.FromGroupSubmissionController`

   A controller for submitting SmilesToGaussianWorkchain

   :param parent_group_label: the string of a group label which contains various SMILES as orm.Str nodes
   :param group_label: the string of the group to put the GaussianCalculations in
   :param max_concurrent: maximum number of concurrent processes.
   :param code_label: label of code, e.g. gaussian@cedar
   :param g16_opt_params: Dict of Gaussian parameters to use
   :param wfxgroup: group in which to store the resulting wfx files
   :param nprocs: number of processors for gaussian calculation
   :param mem_mb: amount of memory in MB for Gaussian calculation
   :param time_s: wallclock time in seconds for Gaussian calculation

   :returns: Controller object, periodically use run_in_batches to submit new results

   .. rubric:: Example

   In a typical use case of controllers, it is beneficial to check for new jobs periodically to submit.
       Either there may be new members of the parent_group to run, or some of the currently running jobs have run.
       So once a controller is defined, we can run it in a loop.

   ::

       controller = SmilesToGaussianController(
           code_label='gaussian@localhost',
           parent_group_label = 'input_smiles', # Add structures to run to input_smiles group
           group_label = 'gaussianopt', # Resulting nodes will be in the gaussianopt group
           max_concurrent = 1,
           wfxgroup = "opt_wfx"
           g16_opt_params = Dict(dict={
               'link0_parameters': {
                   '%chk':'aiida.chk',
                   "%mem": "4000MB",
                   "%nprocshared": 4,
               },
               'functional':'wb97xd',
               'basis_set':'aug-cc-pvtz',
               'route_parameters': { 'opt':None, 'freq':None},
               })
       )

       while True:
           #submit Gaussian batches every hour
           controller.submit_new_batch()
           time.sleep(3600)

   .. py:attribute:: parent_group_label
      :type: str



   .. py:attribute:: group_label
      :type: str



   .. py:attribute:: code_label
      :type: str



   .. py:attribute:: max_concurrent
      :type: int



   .. py:attribute:: g16_opt_params
      :type: dict



   .. py:attribute:: wfxgroup
      :type: str



   .. py:attribute:: nprocs
      :type: int



   .. py:attribute:: mem_mb
      :type: int



   .. py:attribute:: time_s
      :type: int



   .. py:attribute:: WORKFLOW_ENTRY_POINT
      :value: 'aimall.smitog16'



   .. py:method:: get_extra_unique_keys()

      Returns a tuple of extras keys in the order needed


   .. py:method:: get_inputs_and_processclass_from_extras(extras_values)

      Constructs input for a GaussianWFXCalculation from extra_values



.. py:class:: AimReorSubmissionController(code_label: str, reor_group: str, aimparameters, *args, **kwargs)


   Bases: :py:obj:`aiida_submission_controller.FromGroupSubmissionController`

   A controller for submitting AIMReor Workchains.

   :param parent_group_label: the string of a group label which contains various structures as orm.Str nodes
   :param group_label: the string of the group to put the GaussianCalculations in
   :param max_concurrent: maximum number of concurrent processes.
   :param code_label: label of code, e.g. gaussian@cedar
   :param reor_group: group in which to place the reoriented structures.
   :param aimparameters: dict of parameters for running AimQB, to be converted to AimqbParameters by the controller

   :returns: Controller object, periodically use run_in_batches to submit new results

   .. note::

      A typical use case is using this as a controller on wfx files created by GaussianWFXCalculation. In that case,
          match the `parent_group_label` here to the `wfxgroup` provided to the GaussianWFXCalculation.
          In GaussianOptWorkchain, this is `opt_wfx` by default

   .. rubric:: Example

   In a typical use case of controllers, it is beneficial to check for new jobs periodically to submit.
       Either there may be new members of the parent_group to run, or some of the currently running jobs have run.
       So once a controller is defined, we can run it in a loop.

   ::

       controller = AimReorSubmissionController(
           code_label='aimall@localhost',
           parent_group_label = 'wfx', # Add wfx files to run to group wfx
           group_label = 'aim',
           max_concurrent = 1,
           reor_group = "reor_str"
           aimparameters = {"naat": 2, "nproc": 2, "atlaprhocps": True}
       )

       while True:
           #submit AIM batches every 5 minutes
           i = i+1
           controller.submit_new_batch()
           time.sleep(300)

   .. py:attribute:: parent_group_label
      :type: str



   .. py:attribute:: group_label
      :type: str



   .. py:attribute:: max_concurrent
      :type: int



   .. py:attribute:: code_label
      :type: str



   .. py:attribute:: reor_group
      :type: str



   .. py:attribute:: aimparameters
      :type: dict



   .. py:attribute:: WORKFLOW_ENTRY_POINT
      :value: 'aimall.aimreor'



   .. py:method:: get_extra_unique_keys()

      Returns a tuple of extras keys in the order needed


   .. py:method:: get_inputs_and_processclass_from_extras(extras_values)

      Constructs input for a AimReor Workchain from extra_values



.. py:class:: AimAllSubmissionController(code_label: str, aim_parser: str, aimparameters: dict, *args, **kwargs)


   Bases: :py:obj:`aiida_submission_controller.FromGroupSubmissionController`

   A controller for submitting AimQB calculations.

   :param parent_group_label: the string of a group label which contains various structures as orm.Str nodes
   :param group_label: the string of the group to put the GaussianCalculations in
   :param max_concurrent: maximum number of concurrent processes. Expected behaviour is to set to a large number
                          since we will be submitting to Cedar which will manage
   :param code_label: label of code, e.g. gaussian@cedar
   :param aimparameters: dict of parameters for running AimQB, to be converted to AimqbParameters by the controller

   :returns: Controller object, periodically use run_in_batches to submit new results

   .. note::

      A typical use case is using this as a controller on wfx files created by GaussianWFXCalculation. In that case,
          match the `parent_group_label` here to the `wfxgroup` provided to the GaussianWFXCalculation.
          In GaussianSubmissionController, this is `reor_wfx`

   .. rubric:: Example

   In a typical use case of controllers, it is beneficial to check for new jobs periodically to submit.
       Either there may be new members of the parent_group to run, or some of the currently running jobs have run.
       So once a controller is defined, we can run it in a loop.

   ::

       controller = AimAllSubmissionController(
           code_label='aimall@localhost',
           parent_group_label = 'wfx', # Add wfx files to run to group wfx
           group_label = 'aim_reor',
           max_concurrent = 1,
           aim_parser = 'aimqb.group'
           aimparameters = {"naat": 2, "nproc": 2, "atlaprhocps": True}
       )

       while True:
           #submit AIM batches every 5 minutes
           i = i+1
           controller.submit_new_batch()
           time.sleep(300)

   .. py:attribute:: parent_group_label
      :type: str



   .. py:attribute:: group_label
      :type: str



   .. py:attribute:: max_concurrent
      :type: int



   .. py:attribute:: code_label
      :type: str



   .. py:attribute:: aim_parser
      :type: str



   .. py:attribute:: aimparameters
      :type: dict



   .. py:attribute:: CALCULATION_ENTRY_POINT
      :value: 'aimall.aimqb'



   .. py:method:: get_extra_unique_keys()

      Returns a tuple of extras keys in the order needed


   .. py:method:: get_inputs_and_processclass_from_extras(extras_values)

      Constructs input for a AimQBCalculation from extra_values



.. py:class:: GaussianSubmissionController(code_label: str, g16_sp_params: dict, wfxgroup: str, *args, **kwargs)


   Bases: :py:obj:`aiida_submission_controller.FromGroupSubmissionController`

   A controller for submitting Gaussian calculations.

   :param parent_group_label: the string of a group label which contains various structures as orm.Str nodes
   :param group_label: the string of the group to put the GaussianCalculations in
   :param max_concurrent: maximum number of concurrent processes. Expected behaviour is to set to a large number
                          since we will be submitting to Cedar which will manage
   :param code_label: label of code, e.g. gaussian@cedar
   :param g16_sp_params: dictionary of parameters to use in gaussian calculation

   :returns: Controller object, periodically use run_in_batches to submit new results

   .. note::

      A typical use case is using this as a controller on Str structures generated by AIMAllReor workchain. These are by
          default assigned to the `reor_structs` group, so have `parent_group_label` match that

   .. note::

      In overall workchain(fragment->optimize->aim+rotate->single point->aim), this is the single point step.
      Process continues and finishes in AimAllSubmissionController

   .. rubric:: Example

   In a typical use case of controllers, it is beneficial to check for new jobs periodically to submit.
       Either there may be new members of the parent_group to run, or some of the currently running jobs have run.
       So once a controller is defined, we can run it in a loop.

   ::

       controller = GaussianSubmissionController(
           code_label='gaussian@localhost',
           parent_group_label = 'struct', # Add structures to run to struct group
           group_label = 'gaussiansp', # Resulting nodes will be in the gaussiansp group
           max_concurrent = 1,
           g16_sp_params = Dict(dict={
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
       )

       while True:
           #submit Gaussian batches every hour
           controller.submit_new_batch()
           time.sleep(3600)

   .. py:attribute:: parent_group_label
      :type: str



   .. py:attribute:: group_label
      :type: str



   .. py:attribute:: max_concurrent
      :type: int



   .. py:attribute:: code_label
      :type: str



   .. py:attribute:: g16_sp_params
      :type: dict



   .. py:attribute:: wfxgroup
      :type: str



   .. py:attribute:: CALCULATION_ENTRY_POINT
      :value: 'aimall.gaussianwfx'



   .. py:method:: get_extra_unique_keys()

      Returns a tuple of extras keys in the order needed


   .. py:method:: get_inputs_and_processclass_from_extras(extras_values)

      Constructs input for a GaussianWFXCalculation from extra_values

      Note: adjust the metadata options later for 6400MB and 7days runtime
