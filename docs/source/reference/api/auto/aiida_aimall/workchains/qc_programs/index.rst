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

   .. attribute:: shell_metadata

      Metadata for the shell calculation

      :type: aiida.orm.Dict

   .. attribute:: shell_retrieved

      List of files to store in database

      :type: aiida.orm.List

   .. attribute:: shell_input_file

      Input file for the calculation software

      :type: aiida.orm.SinglefileData

   .. attribute:: shell_cmdline

      Command line terminal command

      :type: aiida.orm.Str

   .. attribute:: wfx_filename

      Filename of the wfx file

      :type: aiida.orm.Str

   .. attribute:: aim_code

      Code for AIMQB

      :type: aiida.orm.Code

   .. attribute:: aim_file_ext



      :type: aiida.orm.Str

   .. attribute:: aim_parser

      Entry point for parser to use.

      :type: aiida.orm.Str

   .. attribute:: dry_run

      Whether or not this is a trial run

      :type: aiida.orm.Bool

   .. rubric:: Example

   ::

       # ORCA Example
       from aiida_shell import ShellCode
       from aiida.orm import load_computer, List, SinglefileData, Str, load_code
       QMToAIMWorkchain = WorkflowFactory('aimall.qmtoaim')
       # already have an orca code setup,  you can use the codeblock above to do so
       code = load_code('orca@cedar')
       builder = QMToAIMWorkchain.get_builder()
       builder.shell_code = code
       pre_str = 'module load StdEnv/2020; module load gcc/10.3.0; module load openmpi/4.1.1; module load orca/5.0.4'
       builder.shell_metadata = Dict(
           {
               'options': {
                   'withmpi': False,
                   # modules for the compute cluster to load
                   'prepend_text': pre_str,
                   'resources': {
                       'num_machines': 1,
                       'num_mpiprocs_per_machine': 4,
                   },
                   'max_memory_kb': int(3200 * 1.25) * 1024,
                   'max_wallclock_seconds': 3600
               }
           }
       )
       # again, for tutorial, using a string parsed as file in place of providing an input file
       file_string = '! B3LYP def2-SVP Opt AIM PAL4\n*xyz 0 1\nH 0.0 0.0 0.0\nH 0.0 0.0 1.0\n*'
       input_file = SinglefileData(io.BytesIO(file_string.encode()))
       builder.shell_input_file = input_file
       # get the resulting wfx and opt file, the above command creates a file file.txt
       # so we replace the txt with the output extensions we want
       shell_list = List([input_file.filename.replace('txt','wfx'),input_file.filename.replace('txt','opt'),])
       builder.shell_retrieved = shell_list
       builder.shell_cmdline = Str('{file}')
       builder.aim_code = load_code('aimall@localhost')
       builder.aim_params = AimqbParameters({'nproc':2,'naat':2,'atlaprhocps':True})
       submit(builder)

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

   .. attribute:: gauss_params

      Parameters for the Gaussian calculation

      :type: aiida.orm.Dict

   .. attribute:: aim_params

      Parameters for the AIMQB calculation

      :type: AimqbParameters

   .. attribute:: gauss_code

      Code for Gaussian software

      :type: aiida.orm.Code

   .. attribute:: frag_label

      Label of the fragment

      :type: aiida.orm.Str

   .. attribute:: wfx_group

      Group to put the wfx file in

      :type: aiida.orm.Str

   .. attribute:: gaussian_group

      Group to put the GaussianCalculation in

      :type: aiida.orm.Str

   .. attribute:: aim_code

      Code for AIMQB software

      :type: aiida.orm.Code

   .. attribute:: dry_run

      Whether the run is a dry run

      :type: aiida.orm.Bool

   .. attribute:: wfx_filename

      Name of the wfx file produced in the calculation

      :type: aiida.orm.Str

   .. rubric:: Example

   .. code-block:: python

       from aiida import load_profile
       from aiida.plugins import WorkflowFactory, DataFactory
       from aiida.orm import Dict, StructureData, load_code
       import io
       import ase.io
       from aiida.engine import submit
       load_profile()
       GaussianToAIMWorkChain = WorkflowFactory('aimall.gausstoaim')
       AimqbParameters = DataFactory('aimall.aimqb')
       gaussian_input = Dict(
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
                       })
       aim_input = AimqbParameters({'nproc':2,'naat':2,'atlaprhocps':True})
       # For tutorial purpose, representing a xyz file as a string, and parsing it to get strcutre data
       f = io.StringIO(
                       "5\n\n C -0.1 2.0 -0.02\nH 0.3 1.0 -0.02\nH 0.3 2.5 0.8\nH 0.3 2.5 -0.9\nH -1.2 2.0 -0.02"
                   )
       struct_data = StructureData(ase=ase.io.read(f, format="xyz"))
       f.close()
       builder = GaussianToAIMWorkChain.get_builder()
       builder.g16_params = gaussian_input
       builder.aim_params = aim_input
       builder.structure = struct_data
       builder.gauss_code = load_code('gaussian@localhost')
       builder.aim_code = load_code('aimall@localhost')
       submit(builder)

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

   .. attribute:: input_file

      File to convert to a wfx file. Should be .cp2k.out or .molden

      :type: aiida.orm.SinglefileData

   .. attribute:: aim_params

      Command line parameters for AIMQB

      :type: AimqbParameters

   .. attribute:: aim_code

      AIMQB code

      :type: aiida.orm.Code

   .. rubric:: Example

   ::

       from aiida import load_profile
       from aiida.plugins import WorkflowFactory, DataFactory
       from aiida.orm import load_node, load_code, SinglefileData
       from aiida.engine import submit

       load_profile()
       GenerateWFXToAIMWorkChain = WorkflowFactory("aimall.wfxtoaim")
       AimqbParameters = DataFactory("aimall.aimqb")
       # predefined Molden input file in database
       single_file = SinglefileData('/absolute/path/to/file')
       aim_params = AimqbParameters({"naat": 2, "nproc": 2, "atlaprhocps": True})
       aim_code = load_code("aimall@localhost")
       builder = GenerateWFXToAIMWorkChain.get_builder()
       builder.input_file = single_file
       builder.aim_params = aim_params
       builder.aim_code = aim_code
       submit(builder)

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
