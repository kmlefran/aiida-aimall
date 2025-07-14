"""Subclasses of `FromGroupSubmissionController` designed to prevent too many running processes

The entire :func:`aiida_aimall.workchains.subparam.SubstituentParameterWorkChain` can be replicated
by linking these together.

Provides controllers for the `AimReorWorkChain`, `AimqbCalculations`, `GaussianCalculation`
and `SmilesToGaussianWorkChain`.

"""
# pylint:disable=too-many-positional-arguments
from aiida import orm
from aiida.orm import Dict, Int, Str
from aiida.plugins import CalculationFactory, WorkflowFactory
from aiida_submission_controller import FromGroupSubmissionController

from aiida_aimall.data import AimqbParameters


class SmilesToGaussianController(FromGroupSubmissionController):
    """A controller for submitting :func:`aiida_aimall.workchains.param_parts.SmilesToGaussianWorkChain`

    Args:
        parent_group_label (`str`): group label which contains various SMILES as orm.Str nodes
        group_label (`str`): group in which to put the GaussianCalculations
        wfxgroup (`str`): group in which to store the resulting wfx files
        max_concurrent (`int`): maximum number of concurrent processes
        code_label (`str`): label of Gaussian code, e.g. gaussian@cedar
        gauss_opt_params(`Dict`): Dict of Gaussian parameters to use
        nprocs (`int`): number of processors for gaussian calculation
        mem_mb (`int`): amount of memory in MB for Gaussian calculation
        time_s (`int`): wallclock time in seconds for Gaussian calculation

    Returns:
        Controller object, periodically use run_in_batches to submit new results

    Example:
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

    """

    # pylint:disable=too-many-arguments
    parent_group_label: str
    group_label: str
    code_label: str
    max_concurrent: int
    gauss_opt_params: dict
    wfxgroup: str
    nprocs: int
    mem_mb: int
    time_s: int

    WORKFLOW_ENTRY_POINT: str = "aimall.smitogauss"

    def __init__(
        self,
        code_label: str,
        gauss_opt_params: dict,
        wfxgroup: str,
        nprocs: int,
        mem_mb: int,
        time_s: int,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.code_label = code_label
        self.gauss_opt_params = gauss_opt_params
        self.wfxgroup = wfxgroup
        self.nprocs = nprocs
        self.mem_mb = mem_mb
        self.time_s = time_s

    def get_extra_unique_keys(self):
        """Returns a tuple of extras keys in the order needed"""
        return ("smiles",)

    def get_inputs_and_processclass_from_extras(self, extras_values):
        """Constructs input for a GaussianCalculation from extra_values"""
        code = orm.load_code(self.code_label)
        smiles = self.get_parent_node_from_extras(extras_values)
        inputs = {
            "smiles": smiles,
            "gaussian_code": code,
            "gaussian_parameters": Dict(self.gauss_opt_params),
            "wfxgroup": Str(self.wfxgroup),
            "nprocs": Int(self.nprocs),
            "mem_mb": Int(self.mem_mb),
            "time_s": Int(self.time_s),
        }
        return inputs, WorkflowFactory(self.WORKFLOW_ENTRY_POINT)


class AimReorSubmissionController(FromGroupSubmissionController):
    """A controller for submitting :func:`aiida_aimall.workchains.param_parts.AIMAllReorWorkChain`.

    Args:
        parent_group_label: the string of a group label which contains various structures as orm.Str nodes
        group_label: the string of the group to put the GaussianCalculations in
        max_concurrent: maximum number of concurrent processes.
        code_label: label of code, e.g. gaussian@cedar
        reor_group: group in which to place the reoriented structures.
        aimparameters: dict of parameters for running AimQB, to be converted to AimqbParameters by the controller

    Returns:
        Controller object, periodically use run_in_batches to submit new results

    Note:
        A typical use case is using this as a controller on wfx files created by GaussianCalculation. In that case,
            match the `parent_group_label` here to the `wfxgroup` provided to the GaussianCalculation.
            In GaussianOptWorkchain, this is `opt_wfx` by default

    Example:
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

    """

    parent_group_label: str
    group_label: str
    max_concurrent: int
    code_label: str
    reor_group: str
    aimparameters: dict

    WORKFLOW_ENTRY_POINT: str = "aimall.aimreor"

    def __init__(
        self,
        code_label: str,
        reor_group: str,
        aimparameters,
        *args,
        **kwargs,
    ):
        """initialize class"""
        super().__init__(*args, **kwargs)
        self.code_label = code_label
        self.reor_group = reor_group
        self.aimparameters = aimparameters

    # @validator("code_label")
    # # def _check_code_plugin(self, value):
    # #     """validate provided code label:
    # #     Note: unsure if works
    # #     """
    # #     plugin_type = orm.load_code(value).default_calc_job_plugin
    # #     if plugin_type == "aiida_aimall.calculations:AimqbCalculation":
    # #         return value
    # #     raise ValueError(
    # #         f"Code with label `{value}` has incorrect plugin type: `{plugin_type}`"
    # #     )

    def get_extra_unique_keys(self):
        """Returns a tuple of extras keys in the order needed"""
        return ("smiles",)

    def get_inputs_and_processclass_from_extras(self, extras_values):
        """Constructs input for a :func:`aiida_aimall.workchains.param_parts.AIMAllReorWorkChain` from extra_values"""
        code = orm.load_code(self.code_label)
        # AimqbParameters = DataFactory("aimall")

        inputs = {
            "aim_code": code,
            "aim_params": AimqbParameters(parameter_dict=self.aimparameters),
            "file": self.get_parent_node_from_extras(extras_values),
            "frag_label": Str(extras_values[0]),
            "reor_group": Str(self.reor_group),
        }
        return inputs, WorkflowFactory(self.WORKFLOW_ENTRY_POINT)


class AimAllSubmissionController(FromGroupSubmissionController):
    """A controller for submitting :func:`aiida_aimall.calculations.AimqbCalculation`.

    Args:
        parent_group_label: the string of a group label which contains various structures as orm.Str nodes
        group_label: the string of the group to put the GaussianCalculations in
        max_concurrent: maximum number of concurrent processes. Expected behaviour is to set to a large number
            since we will be submitting to Cedar which will manage
        code_label: label of code, e.g. gaussian@cedar
        aimparameters: dict of parameters for running AimQB, to be converted to
            :func:`aiida_aimall.data.AimqbParameters` by the controller
        aimparser: str of which AIM parser to use: aimall.base for `AimqbBaseParser` or
            aimall.group for `AimqbGroupParser`

    Returns:
        Controller object, periodically use run_in_batches to submit new results

    Note:
        A typical use case is using this as a controller on wfx files created by `GaussianCalculation`. In that case,
            match the `parent_group_label` here to the `wfxgroup` provided to the `GaussianCalculation`.
            In GaussianSubmissionController, this is `reor_wfx`

    Example:
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

    """

    parent_group_label: str
    group_label: str
    max_concurrent: int
    code_label: str
    aim_parser: str
    aimparameters: dict

    CALCULATION_ENTRY_POINT: str = "aimall.aimqb"

    def __init__(
        self,
        code_label: str,
        aim_parser: str,
        aimparameters: dict,
        *args,
        **kwargs,
    ):
        """Initialize the class, modifying with new values"""
        super().__init__(*args, **kwargs)
        self.code_label = code_label
        self.aim_parser = aim_parser
        self.aimparameters = aimparameters

    # @validator("code_label")
    # def _check_code_plugin(self, value):
    #     """Make sure code label works.

    #     Note: unsure this works"""
    #     plugin_type = orm.load_code(value).default_calc_job_plugin
    #     if plugin_type == "aiida_aimall.calculations:AimqbCalculation":
    #         return value
    #     raise ValueError(
    #         f"Code with label `{value}` has incorrect plugin type: `{plugin_type}`"
    #     )

    def get_extra_unique_keys(self):
        """Returns a tuple of extras keys in the order needed"""
        return ("smiles",)

    def get_inputs_and_processclass_from_extras(self, extras_values):
        """Constructs input for a AimQBCalculation from extra_values"""
        code = orm.load_code(self.code_label)
        # AimqbParameters = DataFactory("aimall")
        inputs = {
            "code": code,
            # "frag_label": Str(extras_values[0]),
            "parameters": AimqbParameters(parameter_dict=self.aimparameters),
            "file": self.get_parent_node_from_extras(extras_values),
            "metadata": {
                "options": {
                    "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 2},
                    "parser_name": self.aim_parser,
                }
            },
        }
        return inputs, CalculationFactory(self.CALCULATION_ENTRY_POINT)


class GaussianSubmissionController(FromGroupSubmissionController):
    """A controller for submitting `GaussianCalculation`.

    Args:
        parent_group_label: the string of a group label which contains various structures as orm.Str nodes
        group_label: the string of the group to put the GaussianCalculations in
        max_concurrent: maximum number of concurrent processes. Expected behaviour is to set to a large number
            since we will be submitting to Cedar which will manage
        code_label: label of code, e.g. gaussian@cedar
        gauss_sp_params: dictionary of parameters to use in gaussian calculation
        wfxname: Name of the wfx file


    Returns:
        Controller object, periodically use run_in_batches to submit new results

    Note:
        A typical use case is using this as a controller on Str structures generated by AIMAllReor workchain. These are by
            default assigned to the `reor_structs` group, so have `parent_group_label` match that

    Note:
        In overall workchain(fragment->optimize->aim+rotate->single point->aim), this is the single point step.
        Process continues and finishes in AimAllSubmissionController

    Example:
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

    """

    parent_group_label: str
    group_label: str
    max_concurrent: int
    code_label: str
    gauss_sp_params: dict
    wfxname: str
    # GaussianWFXCalculation entry point as defined in aiida-aimall pyproject.toml
    CALCULATION_ENTRY_POINT: str = "gaussian"

    def __init__(
        self,
        code_label: str,
        gauss_sp_params: dict,
        wfxname: str,
        *args,
        **kwargs,
    ):
        """Initialize the class, modifying with new values"""
        super().__init__(*args, **kwargs)
        self.code_label = code_label
        self.gauss_sp_params = gauss_sp_params
        self.wfxname = wfxname

    # @validator("code_label")
    # def _check_code_plugin(self, value):
    #     """validate that the code label is a GaussianWFXCalculation

    #     Note: unsure if this part works
    #     """
    #     plugin_type = orm.load_code(value).default_calc_job_plugin
    #     if plugin_type == "aiida_aimall.calculations:GaussianWFXCalculation":
    #         return value
    #     raise ValueError(
    #         f"Code with label `{value}` has incorrect plugin type: `{plugin_type}`"
    #     )

    def get_extra_unique_keys(self):
        """Returns a tuple of extras keys in the order needed"""
        return ("smiles",)

    def get_inputs_and_processclass_from_extras(self, extras_values):
        """Constructs input for a GaussianWFXCalculation from extra_values

        Note: adjust the metadata options later for 6400MB and 7days runtime
        """
        code = orm.load_code(self.code_label)
        structure = self.get_parent_node_from_extras(extras_values)
        inputs = {
            "code": code,
            "parameters": Dict(self.gauss_sp_params),
            "structure": structure,
            "metadata": {
                "options": {
                    "resources": {"num_machines": 1, "tot_num_mpiprocs": 1},
                    "max_memory_kb": int(3200 * 1.25) * 1024,
                    "max_wallclock_seconds": 604800,
                    "additional_retrieve_list": [self.wfxname.strip()],
                }
            },
        }
        return inputs, CalculationFactory(self.CALCULATION_ENTRY_POINT)
