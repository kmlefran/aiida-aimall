========
Tutorial
========

Basic Usage
+++++++++++

Create AimqbParameters instance
-------------------------------
aiida-aimall provides a Data class that validates the parameters you are supplying to AIMAll. You can  create such a data type as follows, referring to the list of command line parameters set out in aimqbCMDLine_:
::

    AimqbParameters = DataFactory('aimall.aimqb')
    aim_params = AimqbParameters(parameter_dict={"naat": 2, "nproc": 2, "atlaprhocps": True})

Create and Submit AimqbCalculation
----------------------------------
Having created the parameters for the program, we provide those parameters and a SinglefileData of an AIMQB input file (.fchk, .wfn, .wfx) to AimqbCalculation.
::

    AimqbCalculation = CalculationFactory('aimall.aimqb')
    builder = AimqbCalculation.get_builder()
    builder.parameters = aim_params
    builder.file = SinglefileData('/absolute/path/to/file')
    builder.code = orm.load_code('aimall@localhost')
    # Alternatively, if you have file stored as a string as some of the workchains do
    # builder.file = SinglefileData(io.BytesIO(wfx_file_string.encode()))
    submit(builder)

Using the AimqbGroupParser
--------------------------
If you wish to extract group properties as defined by the authors, the steps are similar, but an additional option is provided to the builder.
::

    AimqbCalculation = CalculationFactory('aimall.aimqb')
    builder = AimqbCalculation.get_builder()
    builder.parameters = aim_params
    builder.file = SinglefileData('/absolute/path/to/file')
    builder.code = orm.load_code('aimall@localhost')
    # set the parser to use to aimall.group
    builder.metadata.options.parser_name = "aimall.group"
    submit(builder)


Running on a set of CML files
-----------------------------
The original intent of the Workflows defined in this package is extracting groups from the Retrievium database (retrievium_) by parsing their CML files.
    In this example, I show the whole workflow enabled through the use of controllers. So this code will identify groups present in the 100 cml files, as defined by the group_decomposition package, (groupdecomp_) attach each group to a hydrogen atom, optimize the group-H molecules, reorient them to the coordinate system defined in subproptoolsp packge (subproptools_), run a Gaussian single point on the reoriented geometry, then run AIM on the final reoriented geometry

::

    # imports
    from aiida.engine import submit # submit the workchain
    import time # delays the while loop
    from aiida.orm import Dict # Data type
    from aiida.plugins.factories import  WorkflowFactory # load workflows
    # load controllers
    from aiida_aimall.controllers import AimAllSubmissionController, AimReorSubmissionController, GaussianSubmissionController, G16FragController
    # load the first workchain
    MultiFragmentWorkChain = WorkflowFactory('aimall.multifrag')
    #Restart the daemons just to make sure they are on
    %verdi daemon stop
    %verdi daemon start 5
    # while running in a terminal, us verdi process list to see running workflows.
    # At the bottom of that report, see the usage of daemons. You may need to start some more daemons depending
    # on what you set as the number of chains to run
    %verdi status
    builder = MultiFragmentWorkChain.get_builder()
    cfd = {}
    #as an example, get 100 cml files in the cfd dictionary. Here, I have some cmls in /Users/chemlab/Documents/Coding/Testing AiiDA/Data/cml_files
    with open('/Users/chemlab/Documents/Coding/Testing AiiDA/Data/cml_files.txt','r') as file:
        file_string = file.readlines()
        for i,line in enumerate(file_string):
            if i < 100:
                line = line.replace('\n','')
                line = line.replace('cml_files','Data/cml_files')
                line = line.replace('./','/Users/chemlab/Documents/Coding/Testing AiiDA/')
                cfd[str(i)] = line
    cml_dict = Dict(dict = cfd)
    # create fragmenting parameters
    frag_params = Dict({'input':'/Users/chemlab/Documents/KLG Notes/Python Packages/klg_fragmentation_workchain/DUDE_03770066_mk14_decoys_C26H23FN4O4S_CIR.cml',
        'bb_patt':'[$([C;X4;!R]):1]-[$([R,!$([C;X4]);!#0;!#9;!#17;!#35;!#1]):2]','keep_only_children':True,'cml_file':'',
        'include_parent':True,'input_type':'cmlfile'})
    frag_dict = Dict(dict=frag_params)
    # pass the inputs to the fragmenting workchain
    builder.frag_params = frag_params
    builder.cml_file_dict = cml_dict
    submit(builder) # launch the fragmenting
    #IMPORTANT!!!
    # Wait until this workchain is DONE before continuing with the while loop
    #Gaussian optimization parameters
    parameters = Dict(dict={
            'link0_parameters': {
                '%chk':'aiida.chk',
                "%mem": "3200MB", # Currently set to use 8000 MB in .sh files
                "%nprocshared": 4,
            },
            'functional':'wb97xd',
            'basis_set':'aug-cc-pvtz',
            'charge': 0,
            'multiplicity': 1,
            'route_parameters': {'opt': None, 'Output':'WFX'},
            "input_parameters": {"output.wfx": None},
        })
    # Gaussian optimization controller
    g16opt_controller = G16FragController(
        parent_group_label = "inp_frag", # group to look for fragment structures
        group_label = "opt_workchain", # group to store opt workchains
        max_concurrent = 10, # number of concurrent calculations, dno't set too high, don't want to overload cluster
        code_label = "gaussian@cedar",
        g16_opt_params = parameters.get_dict() # for creating the Gaussian input file
        wfxgroup = "opt_wfx"
    )
    # AIM Reor Controller
    controller = AimReorSubmissionController(
        parent_group_label = 'opt_wfx',
        group_label = 'prereor_aim',
        max_concurrent = 1, # set to 1 since we will use 2 processors, and the second AIM controller will also use 2
        #So max 1 of each AIM  controller at a time=2 concurrent AIM
        code_label='aimall@localhost',
        reor_group = "reor_structs",
        aimparameters = {"naat": 2, "nproc": 2, "atlaprhocps": True}
    )
    # Gaussian Single Point parameters
    sp_parameters = Dict(dict={
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
    #Gaussian single point controller
    controller2 = GaussianSubmissionController(
        parent_group_label = 'reor_structs',
        group_label = 'gaussian_sp',
        max_concurrent = 10,
        code_label='gaussian@cedar',
        g16_sp_params=sp_parameters,
        wfxgroup = "reor_wfx"
    )
    # Final AIM Controller
    controller3 = AimAllSubmissionController(
        code_label='aimall@localhost',
        parent_group_label = 'reor_wfx',
        group_label = 'aim_reor',
        max_concurrent = 1,
        aim_parser = 'aimqb.group'
        aimparameters = {"naat": 2, "nproc": 2, "atlaprhocps": True}
    )
    # loop over submitting in batches every interval until all are run
    from aiida.engine.processes.control import play_processes
    while controller3.num_already_run < g16opt_controller.num_to_run + g16opt_controller.num_already_run:
        # Submit Gaussian batches every hour. 12 AIM loops * 5 min
        g16opt_controller.submit_new_batch()
        print(f'Opt Freq Controller {g16opt_controller.num_already_run}')
        i=0
        play_processes(all_entries=True)
        while i < 12:
            #submit AIM batches every 5 minutes
            i = i+1
            controller.submit_new_batch()
            print(f'AimReor Controller {controller.num_already_run}')
            controller2.submit_new_batch()
            print(f'Gaussian SP Controller {controller2.num_already_run}')
            print(f'Final AIM Controller {controller3.num_already_run}')
            controller3.submit_new_batch()
            time.sleep(300)

.. _aimqbCMDLine: https://aim.tkgristmill.com/manual/aimqb/aimqb.html#AIMQBCommandLine
.. _retrievium: https://retrievium.ca
.. _groupdecomp: https://github.com/kmlefran/group_decomposition
.. _subproptools: https://github.com/kmlefran/subproptools
