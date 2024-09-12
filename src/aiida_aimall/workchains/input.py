"""Base input workchain"""
from aiida.engine import WorkChain, if_
from aiida.engine.processes import ExitCode
from aiida.orm import SinglefileData, Str, StructureData

from aiida_aimall.workchains.calcfunctions import (
    generate_structure_data,
    get_molecule_str_from_smiles,
    xyzfile_to_StructureData,
)


class BaseInputWorkChain(WorkChain):
    """A workchain to generate and validate inputs.

    Provided an .xyz file as `SinglefileData`, molecule `StructureData`, or SMILES of the molecule
    validates that only one is provided. Then, prepares the input into a format for future GaussianCalculations.

    Attributes:
        structure (aiida.orm.StructureData): StructureData of molecule to run
        smiles (aiida.orm.Str): smiles string of molecule
        xyz_file (aiida.orm.SinglefileData): file data of an xyz file

    Note:
        This is a base class that is used by other WorkChains
            (:func:`aiida_aimall.workchains.subparam.SubstituentParameterWorkChain`, and
            :func:`aiida_aimall.workchains.qc_programs.GaussianToAIMWorkChain`)
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input(
            "structure",
            valid_type=StructureData,
            required=False,
            help="StructureData of molecule to run",
        )
        spec.input(
            "smiles", valid_type=Str, required=False, help="smiles string of molecule"
        )
        spec.input(
            "xyz_file",
            valid_type=SinglefileData,
            required=False,
            help="file data of an xyz file",
        )
        spec.exit_code(
            200,
            "ERROR_MULTIPLE_INPUTS",
            "the process received two or more of the following inputs: structure, smiles, xyz_file",
        )
        spec.exit_code(
            201,
            "ERROR_NO_INPUTS",
            "None of structure, smiles, xyz_file were provided, at least one must be",
        )
        spec.outline(
            cls.validate_input,
            if_(cls.is_xyz_input)(cls.create_structure_from_xyz),
            if_(cls.is_smiles_input)(
                cls.get_molecule_inputs_step, cls.string_to_StructureData
            ),
            if_(cls.is_structure_input)(cls.structure_in_context),
        )

    def is_xyz_input(self):
        """Validates if xyz_file was provided as input"""
        if "xyz_file" in self.inputs:
            return True
        return False

    def is_smiles_input(self):
        """Validates if smiles was provided as input"""
        if "smiles" in self.inputs:
            return True
        return False

    def is_structure_input(self):
        """Validates if structure was provided as input"""
        if "structure" in self.inputs:
            return True
        return False

    # pylint:disable=inconsistent-return-statements
    def validate_input(self):
        """Check that only one of smiles, structure, or xyz_file was input"""
        if "smiles" in self.inputs and (
            "xyz_file" in self.inputs or "structure" in self.inputs
        ):
            return ExitCode(200)
        if "xyz_file" in self.inputs and (
            "smiles" in self.inputs or "structure" in self.inputs
        ):
            return ExitCode(200)
        if "structure" in self.inputs and (
            "xyz_file" in self.inputs or "smiles" in self.inputs
        ):
            return ExitCode(200)
        if (
            "structure" not in self.inputs
            and "xyz_file" not in self.inputs
            and "smiles" not in self.inputs
        ):
            return ExitCode(201)

    def create_structure_from_xyz(self):
        """Convert the xyzfile to StructureData. Calls
        :func:`aiida_aimall.workchains.calcfunctions.xyzfile_to_StructureData`"""
        self.ctx.structure = xyzfile_to_StructureData(self.inputs.xyz_file)

    def structure_in_context(self):
        """Store the input structure in context, to make consistent with the results of xyz_file or SMILES input."""
        self.ctx.structure = self.inputs.structure

    def get_molecule_inputs_step(self):
        """Given list of substituents and previously done smiles, get input.
        Calls :func:`aiida_aimall.workchains.calcfunctions.get_molecule_str_from_smiles`"""
        self.ctx.smiles_geom = get_molecule_str_from_smiles(self.inputs.smiles)

    def string_to_StructureData(self):
        """Convert an xyz string of molecule geometry to StructureData.
        Calls :func:`aiida_aimall.workchains.calcfunctions.generate_structure_data`"""
        self.ctx.structure = generate_structure_data(self.ctx.smiles_geom)
