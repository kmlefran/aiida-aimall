:py:mod:`aiida_aimall.controllers`
==================================

.. py:module:: aiida_aimall.controllers

.. autoapi-nested-parse::

   Subclasses of `FromGroupSubmissionController` designed to prevent too many running processes

   The entire :func:`aiida_aimall.workchains.subparam.SubstituentParameterWorkChain` can be replicated
   by linking these together.

   Provides controllers for the `AimReorWorkChain`, `AimqbCalculations`, `GaussianCalculation`
   and `SmilesToGaussianWorkChain`.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.controllers.SmilesToGaussianController
   aiida_aimall.controllers.AimReorSubmissionController
   aiida_aimall.controllers.AimAllSubmissionController
   aiida_aimall.controllers.GaussianSubmissionController




.. py:class:: SmilesToGaussianController(code_label: str, gauss_opt_params: dict, wfxgroup: str, nprocs: int, mem_mb: int, time_s: int, *args, **kwargs)


   Bases: :py:obj:`aiida_submission_controller.FromGroupSubmissionController`

   A controller for submitting :func:`aiida_aimall.workchains.param_parts.SmilesToGaussianWorkChain`

   :param parent_group_label: group label which contains various SMILES as orm.Str nodes
   :type parent_group_label: `str`
   :param group_label: group in which to put the GaussianCalculations
   :type group_label: `str`
   :param wfxgroup: group in which to store the resulting wfx files
   :type wfxgroup: `str`
   :param max_concurrent: maximum number of concurrent processes
   :type max_concurrent: `int`
   :param code_label: label of Gaussian code, e.g. gaussian@cedar
   :type code_label: `str`
   :param gauss_opt_params: Dict of Gaussian parameters to use
   :type gauss_opt_params: `Dict`
   :param nprocs: number of processors for gaussian calculation
   :type nprocs: `int`
   :param mem_mb: amount of memory in MB for Gaussian calculation
   :type mem_mb: `int`
   :param time_s: wallclock time in seconds for Gaussian calculation
   :type time_s: `int`

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
           wfxgroup = "opt_wfx",
           gauss_opt_params = Dict(dict={
               'link0_parameters': {
                   '%chk':'aiida.chk',
                   "%mem": "4000MB",
                   "%nprocshared": 4,
               },
               'functional':'wb97xd',
               'basis_set':'aug-cc-pvtz',
               'route_parameters': { 'opt':None, 'freq':None},
               }),
           nprocs = 4,
           mem_mb = 6400,
           time_s = 24*3600*7
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



   .. py:attribute:: gauss_opt_params
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
      :type: str
      :value: 'aimall.smitogauss'



   .. py:method:: get_extra_unique_keys()

      Returns a tuple of extras keys in the order needed


   .. py:method:: get_inputs_and_processclass_from_extras(extras_values)

      Constructs input for a GaussianCalculation from extra_values



.. py:class:: AimReorSubmissionController(code_label: str, reor_group: str, aimparameters, *args, **kwargs)


   Bases: :py:obj:`aiida_submission_controller.FromGroupSubmissionController`

   A controller for submitting :func:`aiida_aimall.workchains.param_parts.AIMAllReorWorkChain`.

   :param parent_group_label: the string of a group label which contains various structures as orm.Str nodes
   :param group_label: the string of the group to put the GaussianCalculations in
   :param max_concurrent: maximum number of concurrent processes.
   :param code_label: label of code, e.g. gaussian@cedar
   :param reor_group: group in which to place the reoriented structures.
   :param aimparameters: dict of parameters for running AimQB, to be converted to AimqbParameters by the controller

   :returns: Controller object, periodically use run_in_batches to submit new results

   .. note::

      A typical use case is using this as a controller on wfx files created by GaussianCalculation. In that case,
          match the `parent_group_label` here to the `wfxgroup` provided to the GaussianCalculation.
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
      :type: str
      :value: 'aimall.aimreor'



   .. py:method:: get_extra_unique_keys()

      Returns a tuple of extras keys in the order needed


   .. py:method:: get_inputs_and_processclass_from_extras(extras_values)

      Constructs input for a :func:`aiida_aimall.workchains.param_parts.AIMAllReorWorkChain` from extra_values



.. py:class:: AimAllSubmissionController(code_label: str, aim_parser: str, aimparameters: dict, *args, **kwargs)


   Bases: :py:obj:`aiida_submission_controller.FromGroupSubmissionController`

   A controller for submitting :func:`aiida_aimall.calculations.AimqbCalculation`.

   :param parent_group_label: the string of a group label which contains various structures as orm.Str nodes
   :param group_label: the string of the group to put the GaussianCalculations in
   :param max_concurrent: maximum number of concurrent processes. Expected behaviour is to set to a large number
                          since we will be submitting to Cedar which will manage
   :param code_label: label of code, e.g. gaussian@cedar
   :param aimparameters: dict of parameters for running AimQB, to be converted to
                         :func:`aiida_aimall.data.AimqbParameters` by the controller
   :param aimparser: str of which AIM parser to use: aimall.base for `AimqbBaseParser` or
                     aimall.group for `AimqbGroupParser`

   :returns: Controller object, periodically use run_in_batches to submit new results

   .. note::

      A typical use case is using this as a controller on wfx files created by `GaussianCalculation`. In that case,
          match the `parent_group_label` here to the `wfxgroup` provided to the `GaussianCalculation`.
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
      :type: str
      :value: 'aimall.aimqb'



   .. py:method:: get_extra_unique_keys()

      Returns a tuple of extras keys in the order needed


   .. py:method:: get_inputs_and_processclass_from_extras(extras_values)

      Constructs input for a AimQBCalculation from extra_values



.. py:class:: GaussianSubmissionController(code_label: str, gauss_sp_params: dict, wfxname: str, *args, **kwargs)


   Bases: :py:obj:`aiida_submission_controller.FromGroupSubmissionController`

   A controller for submitting `GaussianCalculation`.

   :param parent_group_label: the string of a group label which contains various structures as orm.Str nodes
   :param group_label: the string of the group to put the GaussianCalculations in
   :param max_concurrent: maximum number of concurrent processes. Expected behaviour is to set to a large number
                          since we will be submitting to Cedar which will manage
   :param code_label: label of code, e.g. gaussian@cedar
   :param gauss_sp_params: dictionary of parameters to use in gaussian calculation
   :param wfxname: Name of the wfx file

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
           wfxname='output.wfx'
           gauss_sp_params = Dict(dict={
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



   .. py:attribute:: gauss_sp_params
      :type: dict



   .. py:attribute:: wfxname
      :type: str



   .. py:attribute:: CALCULATION_ENTRY_POINT
      :type: str
      :value: 'gaussian'



   .. py:method:: get_extra_unique_keys()

      Returns a tuple of extras keys in the order needed


   .. py:method:: get_inputs_and_processclass_from_extras(extras_values)

      Constructs input for a GaussianWFXCalculation from extra_values

      Note: adjust the metadata options later for 6400MB and 7days runtime
