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

   A workchain to calculate properties of substituents, R, in R-H molecules.

   This is a multistep calculation, consisting of a Gaussian calculation, an AIMQB calculation,
   Python reorientation to the defined coordinate system, a Gaussian single point calculation,
   and a final AIMQB calculation on the single point wfx calculation. Substituent Properties are
   then extracted using the AimqbGroupParser.

   .. attribute:: gauss_opt_params

      Parameters for the Gaussian optimization calculations

      :type: aiida.orm.Dict

   .. attribute:: gauss_sp_params

      Parameters for the Gaussian single point calculations

      :type: aiida.orm.Dict

   .. attribute:: aim_params

      Command line parameters for AIMQB

      :type: AimqbParameters

   .. attribute:: gauss_code

      Code for Gaussian software

      :type: aiida.orm.Code

   .. attribute:: frag_label

      Optional fragment label for the calculation

      :type: aiida.orm.Str

   .. attribute:: opt_wfx_group

      Optional group to put optimization wavefunctions in

      :type: aiida.orm.Str

   .. attribute:: sp_wfx_group

      Optional group to put single point wavefunctions in

      :type: aiida.orm.Str

   .. attribute:: gaussian_opt_group

      Optional group to put optimization GaussianCalculations in

      :type: aiida.orm.Str

   .. attribute:: gaussian_sp_group

      Optional group to put single point GaussianCalculations in

      :type: aiida.orm.Str

   .. attribute:: wfx_filename

      Optional wfx file name

      :type: aiida.orm.Str

   .. attribute:: aim_code

      Code for AIMQB software

      :type: aiida.orm.Code

   .. attribute:: dry_run

      Whether or not this is a dry run of the WorkChain

      :type: aiida.orm.Bool

   .. note::

      Here, the group for a substiuent is defined in an R-H molecule. Atom 1 is the atom in
      the group R that is attached to the hydrogen, and the hydrogen should be atom 2. These
      align with the default settings of an AimqbCalculation using an AimqbGroupParser.

   .. rubric:: Example

   ::

       from aiida.plugins import WorkflowFactory, DataFactory
       from aiida.orm import Dict, StructureData, load_code
       from aiida.engine import submit
       from aiida import load_profile
       import io
       import ase.io

       load_profile()

       SubstituentParameterWorkchain = WorkflowFactory('aimall.subparam')
       AimqbParameters = DataFactory('aimall.aimqb')
       aim_input = AimqbParameters({'nproc':2,'naat':2,'atlaprhocps':True})
       gaussian_opt = Dict(
                   {
                       "link0_parameters": {
                           "%chk": "aiida.chk",
                           "%mem": "3200MB",  # Currently set to use 8000 MB in .sh files
                           "%nprocshared": 4,
                       },
                       "functional": "wb97xd",
                       "basis_set": "aug-cc-pvtz",
                       "charge": 0,
                       "multiplicity": 1,
                       "route_parameters": {"opt": None, "Output": "WFX"},
                       "input_parameters": {"output.wfx": None},
                   }
       )
       gaussian_sp = Dict(
                   {
                       "link0_parameters": {
                           "%chk": "aiida.chk",
                           "%mem": "3200MB",  # Currently set to use 8000 MB in .sh files
                           "%nprocshared": 4,
                       },
                       "functional": "wb97xd",
                       "basis_set": "aug-cc-pvtz",
                       "charge": 0,
                       "multiplicity": 1,
                       "route_parameters": {"nosymmetry": None, "Output": "WFX"},
                       "input_parameters": {"output.wfx": None},
                   }
       )
       f = io.StringIO(
                       "5\n\n C -0.1 2.0 -0.02\nH 0.3 1.0 -0.02\nH 0.3 2.5 0.8\nH 0.3 2.5 -0.9\nH -1.2 2.0 -0.02"
                   )
       struct_data = StructureData(ase=ase.io.read(f, format="xyz"))
       f.close()
       builder = SubstituentParameterWorkchain.get_builder()
       builder.g16_code = load_code('gaussian@localhost')
       builder.aim_code = load_code('aimall@localhost')
       builder.g16_opt_params = gaussian_opt
       builder.g16_sp_params = gaussian_sp
       builder.structure = struct_data
       builder.aim_params = aim_input
       submit(builder)

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
