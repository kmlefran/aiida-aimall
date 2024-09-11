"""
Data types provided by plugin
"""

from aiida.orm import Dict
from voluptuous import Optional, Schema

# AIMQB's command line options and their expected type
cmdline_options = {
    Optional("bim"): str,
    Optional("iasmesh"): str,
    Optional("capture"): str,
    Optional("boaq"): str,
    Optional("ehren"): int,
    Optional("feynman"): bool,
    Optional("iasprops"): bool,
    Optional("magprops"): str,
    Optional("source"): bool,
    Optional("iaswrite"): bool,
    Optional("atidsprop"): str,
    Optional("encomp"): int,
    Optional("warn"): bool,
    Optional("scp"): str,
    Optional("delmog"): bool,
    Optional("skipint"): bool,
    Optional("f2w"): str,
    Optional("f2wonly"): bool,
    Optional("atoms"): str,
    Optional("mir"): float,
    Optional("cpconn"): str,
    Optional("intveeaa"): str,
    Optional("atlaprhocps"): bool,
    Optional("wsp"): bool,
    Optional("nproc"): int,
    Optional("naat"): int,
    Optional("shm_lmax"): int,
    Optional("maxmem"): int,
    Optional("verifyw"): str,
    Optional("saw"): bool,
    Optional("autonnacps"): bool,
}


class AimqbParameters(Dict):  # pylint: disable=too-many-ancestors
    """
    Command line options for aimqb.

    This class represents a python dictionary used to
    pass command line options to the executable.
    The class takes a dictionary of parameters and validates
    to ensure the aimqb command line parameters are correct

    Args:
        parameters_dict (`dict`): dictionary with commandline parameters

    Usage:
        ``AimqbParameters(parameter_dict{'naat':2})``

    """

    schema = Schema(cmdline_options)

    def __init__(self, parameter_dict=None, **kwargs):
        """Constructor for the data class

        Args:
            parameters_dict (`dict`): dictionary with commandline parameters

        Usage:
            ``AimqbParameters(parameter_dict{'naat':2})``
        """
        parameter_dict = self.validate(parameter_dict)
        super().__init__(dict=parameter_dict, **kwargs)

    def validate(self, parameters_dict):
        """Validate command line options.

        Uses the voluptuous package for validation. Find out about allowed keys using::

            print(AimqbParameters).schema.schema

        Args:
            parameters_dict (dict): dictionary with commandline parameters

        Returns:
            input dictionary validated against the allowed options for aimqb

        """
        return AimqbParameters.schema(parameters_dict)

    def cmdline_params(self, file_name):
        """Synthesize command line parameters and add -nogui for use in `AimqbCalculation`.

        Args:
            file_name (str): Name of wfx/fchk/wfn file

        Returns:
            command line parameters for aimqb collected in a list
                e.g. [ '-atlaprhocps=True',...,'-nogui', 'filename']

        """
        # parameters = []

        pm_dict = self.get_dict()
        parameters = [f"-{key}={value}" for key, value in pm_dict.items()]
        # for key, value in pm_dict.items():
        #     parameters += [f"-{key}={value}"]
        parameters += ["-nogui"]  # use no gui when running in aiida
        parameters += [file_name]  # input file

        return [str(p) for p in parameters]

    def __str__(self):
        """String representation of node. Append values of dictionary to usual representation.

        Returns:
            representation of node, including uuid, pk, and the contents of the dictionary

        """
        string = super().__str__()
        string += "\n" + str(self.get_dict())
        return string
