"""aiida_aimall.controllers

Subclasses of FromGroupSubmissionController designed to manage local traffic on lab Macs to prevent to many running processes

Provides controllers for the AimReor WorkChain, AimQBCalculations, and GaussianWFXCalculations
"""

from aiida import orm
from aiida.orm import Dict, Str
from aiida.plugins import CalculationFactory, DataFactory, WorkflowFactory
from aiida_submission_controller import FromGroupSubmissionController
from pydantic import validator

AimqbParameters = DataFactory("aimall")
GaussianCalculation = CalculationFactory("gaussianwfx")
AimqbCalculation = CalculationFactory("aimall")


class AimReorSubmissionController(FromGroupSubmissionController):
    """A controller for submitting AIMReor Workchains.

    Args:
        parent_group_label: the string of a group label which contains various structures as orm.Str nodes
        group_label: the string of the group to put the GaussianCalculations in
        max_concurrent: maximum number of concurrent processes. Expected behaviour is to set to a large number
        since we will be submitting to Cedar which will manage
        code_label: label of code, e.g. gaussian@cedar


    Returns:
        Controller object, periodically use run_in_batches to submit new results
    """

    parent_group_label: str
    group_label: str
    max_concurrent: int
    code_label: str

    WORKFLOW_ENTRY_POINT = "AIMAllReor"

    def __init__(
        self,
        code_label: str,
        *args,
        **kwargs,
    ):
        """initialize class"""
        super().__init__(*args, **kwargs)
        self.code_label = code_label

    @validator("code_label")
    def _check_code_plugin(self, value):
        """validate provided code label:
        Note: unsure if works
        """
        plugin_type = orm.load_code(value).default_calc_job_plugin
        if plugin_type == "aiida_aimall.calculations:AimqbCalculation":
            return value
        raise ValueError(
            f"Code with label `{value}` has incorrect plugin type: `{plugin_type}`"
        )

    def get_extra_unique_keys(self):
        """Returns a tuple of extras keys in the order needed"""
        return ("smiles",)

    def get_inputs_and_processclass_from_extras(self, extras_values):
        """Constructs input for a AimReor Workchain from extra_values"""
        code = orm.load_code(self.code_label)
        # AimqbParameters = DataFactory("aimall")
        aimparameters = AimqbParameters(
            parameter_dict={"naat": 2, "nproc": 2, "atlaprhocps": True}
        )
        inputs = {
            "aim_code": code,
            "aim_params": aimparameters,
            "file": self.get_parent_node_from_extras(extras_values),
            "frag_label": extras_values[0],
        }
        return inputs, WorkflowFactory(self.WORKFLOW_ENTRY_POINT)


class AimAllSubmissionController(FromGroupSubmissionController):
    """A controller for submitting AimQB calculations.

    Args:
        parent_group_label: the string of a group label which contains various structures as orm.Str nodes
        group_label: the string of the group to put the GaussianCalculations in
        max_concurrent: maximum number of concurrent processes. Expected behaviour is to set to a large number
          since we will be submitting to Cedar which will manage
        code_label: label of code, e.g. gaussian@cedar


    Returns:
        Controller object, periodically use run_in_batches to submit new results
    """

    parent_group_label: str
    group_label: str
    max_concurrent: int
    code_label: str

    CALCULATION_ENTRY_POINT = "aimall"

    def __init__(
        self,
        code_label: str,
        *args,
        **kwargs,
    ):
        """Initialize the class, modifying with new values"""
        super().__init__(*args, **kwargs)
        self.code_label = code_label

    @validator("code_label")
    def _check_code_plugin(self, value):
        """Make sure code label works.

        Note: unsure this works"""
        plugin_type = orm.load_code(value).default_calc_job_plugin
        if plugin_type == "aiida_aimall.calculations:AimqbCalculation":
            return value
        raise ValueError(
            f"Code with label `{value}` has incorrect plugin type: `{plugin_type}`"
        )

    def get_extra_unique_keys(self):
        """Returns a tuple of extras keys in the order needed"""
        return ("smiles",)

    def get_inputs_and_processclass_from_extras(self, extras_values):
        """Constructs input for a AimQBCalculation from extra_values"""
        code = orm.load_code(self.code_label)
        # AimqbParameters = DataFactory("aimall")
        aimparameters = AimqbParameters(
            parameter_dict={"naat": 2, "nproc": 2, "atlaprhocps": True}
        )
        inputs = {
            "code": code,
            "frag_label": extras_values[0],
            "parameters": aimparameters,
            "file": self.get_parent_node_from_extras(extras_values),
            "metadata": {
                "options": {
                    "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 2},
                }
            },
        }
        return inputs, WorkflowFactory(self.CALCULATION_ENTRY_POINT)


class GaussianSubmissionController(FromGroupSubmissionController):
    """A controller for submitting Gaussian calculations.

    Args:
        parent_group_label: the string of a group label which contains various structures as orm.Str nodes
        group_label: the string of the group to put the GaussianCalculations in
        max_concurrent: maximum number of concurrent processes. Expected behaviour is to set to a large number
          since we will be submitting to Cedar which will manage
        code_label: label of code, e.g. gaussian@cedar
        g16_sp_params: dictionary of parameters to use in gaussian calculation

    Returns:
        Controller object, periodically use run_in_batches to submit new results

    Process continues and finishes in AimAllSubmissionController
    """

    parent_group_label: str
    group_label: str
    max_concurrent: int
    code_label: str
    g16_sp_params: dict
    # GaussianWFXCalculation entry point as defined in aiida-aimall pyproject.toml
    CALCULATION_ENTRY_POINT = "gaussianwfx"

    def __init__(
        self,
        code_label: str,
        g16_sp_params: dict,
        *args,
        **kwargs,
    ):
        """Initialize the class, modifying with new values"""
        super().__init__(*args, **kwargs)
        self.code_label = code_label
        self.g16_sp_params = g16_sp_params

    @validator("code_label")
    def _check_code_plugin(self, value):
        """validate that the code label is a GaussianWFXCalculation

        Note: unsure if this part works
        """
        plugin_type = orm.load_code(value).default_calc_job_plugin
        if plugin_type == "aiida_aimall.calculations:GaussianWFXCalculation":
            return value
        raise ValueError(
            f"Code with label `{value}` has incorrect plugin type: `{plugin_type}`"
        )

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
            "fragment_label": extras_values[0],
            "code": code,
            "parameters": Dict(self.g16_sp_params),
            "structure_str": structure,
            "wfxgroup": Str("reor_wfx"),
            "metadata": {
                "options": {
                    "resources": {"num_machines": 1, "tot_num_mpiprocs": 1},
                    "max_memory_kb": 384000,
                    "max_wallclock_seconds": 604800,
                }
            },
        }
        return inputs, CalculationFactory(self.CALCULATION_ENTRY_POINT)