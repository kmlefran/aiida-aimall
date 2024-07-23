"""
Data types provided by plugin

Upon pip install, AimqbParameters  is accessible in AiiDA.data plugins
Using the 'aimall' entry point
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
    """

    schema = Schema(cmdline_options)

    def __init__(self, parameter_dict=None, **kwargs):
        """Constructor for the data class

        Usage: ``AimqbParameters(parameter_dict{'ignore-case': True})``

        :param parameters_dict: dictionary with commandline parameters
        :param type parameters_dict: dict

        """
        parameter_dict = self.validate(parameter_dict)
        super().__init__(dict=parameter_dict, **kwargs)

    def validate(self, parameters_dict):
        """Validate command line options.

        Uses the voluptuous package for validation. Find out about allowed keys using::

            print(AimqbParameters).schema.schema

        :param parameters_dict: dictionary with commandline parameters
        :param type parameters_dict: dict
        :returns: validated dictionary
        """
        return AimqbParameters.schema(parameters_dict)

    def cmdline_params(self, file_name):
        """Synthesize command line parameters.

        e.g. [ '-atlaprhocps=True',...,'-nogui', 'filename']

        :param file_name: Name of wfx/fchk/wfn file
        :param type file_name: str

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
        """String representation of node.

        Append values of dictionary to usual representation. E.g.::

            uuid: b416cbee-24e8-47a8-8c11-6d668770158b (pk: 590)
            {'atlaprhocps': True}

        """
        string = super().__str__()
        string += "\n" + str(self.get_dict())
        return string
