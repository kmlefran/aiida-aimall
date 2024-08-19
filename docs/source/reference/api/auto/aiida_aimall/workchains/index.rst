:py:mod:`aiida_aimall.workchains`
=================================

.. py:module:: aiida_aimall.workchains

.. autoapi-nested-parse::

   aiida_aimall.workchains
   Workchains designed for a workflow starting from a set of cmls, then breaking off into fragment Gaussian Calculations
   Needs to be run in part with aiida_aimall.controllers to control local traffic on lab Mac
   Example in the works

   Provided Workchains are
   MultiFragmentWorkchain, entry point: multifrag
   G16OptWorkChain, entry point: g16opt
   AimAllReor WorkChain, entry point: aimreor



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.workchains.QMToAIMWorkchain
   aiida_aimall.workchains.GenerateWFXToAIMWorkchain
   aiida_aimall.workchains.SmilesToGaussianWorkchain
   aiida_aimall.workchains.AIMAllReor
   aiida_aimall.workchains.BaseInputWorkChain
   aiida_aimall.workchains.GaussianToAIMWorkChain
   aiida_aimall.workchains.SubstituentParameterWorkChain



Functions
~~~~~~~~~

.. autoapisummary::

   aiida_aimall.workchains.generate_rotated_structure_aiida
   aiida_aimall.workchains.remove
   aiida_aimall.workchains.dict_to_structure
   aiida_aimall.workchains.calc_multiplicity
   aiida_aimall.workchains.find_attachment_atoms
   aiida_aimall.workchains.reorder_molecule
   aiida_aimall.workchains.get_xyz
   aiida_aimall.workchains.get_substituent_input
   aiida_aimall.workchains.generate_structure_data
   aiida_aimall.workchains.parameters_with_cm
   aiida_aimall.workchains.get_wfxname_from_gaussianinputs
   aiida_aimall.workchains.create_wfx_from_retrieved
   aiida_aimall.workchains.validate_shell_code
   aiida_aimall.workchains.validate_file_ext
   aiida_aimall.workchains.get_wfx
   aiida_aimall.workchains.get_molecule_str_from_smiles
   aiida_aimall.workchains.xyzfile_to_StructureData



Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_aimall.workchains.GaussianCalculation
   aiida_aimall.workchains.AimqbParameters
   aiida_aimall.workchains.AimqbCalculation


.. py:data:: GaussianCalculation



.. py:data:: AimqbParameters



.. py:data:: AimqbCalculation



.. py:function:: generate_rotated_structure_aiida(FolderData, atom_dict, cc_dict)

   Rotates the fragment to the defined coordinate system

   :param FolderData: aim calculation folder
   :param atom_dict: AIM atom dict
   :param cc_dict: AIM cc_dict


.. py:function:: remove(in_list)

   Remove digits from a list of strings. e.g. ['O1','H2','H3'] -> ['O','H','H']


.. py:function:: dict_to_structure(fragment_dict)

   Generate a string of xyz coordinates for Gaussian input file

   :param fragment_dict:
   :param type fragment_dict: aiida.orm.nodes.data.dict.Dict


.. py:function:: calc_multiplicity(mol)

   Calculate the multiplicity of a molecule as 2S +1


.. py:function:: find_attachment_atoms(mol)

   Given molecule object, find the atoms corresponding to a * and the atom to which that is bound

   :param mol: rdkit molecule object

   :returns: molecule with added hydrogens, the * atom object, and the atom object to which that is attached

   .. note:: Assumes that only one * is present in the molecule


.. py:function:: reorder_molecule(h_mol_rw, zero_at, attached_atom)

   Reindexes the atoms in a molecule, setting attached_atom to index 0, and zero_at to index 1

   :param h_mol_rw: RWMol rdkit object with explicit hydrogens
   :param zero_at: the placeholder * atom
   :param attached_atom: the atom bonded to *

   :returns: molecule with reordered indices


.. py:function:: get_xyz(reorder_mol)

   MMFF optimize the molecule to generate xyz coordiantes


.. py:function:: get_substituent_input(smiles: str) -> dict

   For a given smiles, determine xyz structure, charge, and multiplicity

   :param smiles: SMILEs of substituent to run

   :returns: Dict with keys xyz, charge, multiplicity


.. py:function:: generate_structure_data(smiles_dict)

   Take an input xyz string and convert it to StructureData


.. py:function:: parameters_with_cm(parameters, smiles_dict)

   Add charge and multiplicity keys to Gaussian Input


.. py:function:: get_wfxname_from_gaussianinputs(gaussian_parameters)

   Look for wfx or wfn objects in the retrieved Folder


.. py:function:: create_wfx_from_retrieved(wfxname, retrieved_folder)

   Create wavefunciton Singlefildata from retrieved folder


.. py:function:: validate_shell_code(node, _)

   Validate the shell code, ensuring that it is ShellCode or Str


.. py:function:: validate_file_ext(node, _)

   Validates that the file extension provided for AIM is wfx, wfn or fchk


.. py:class:: QMToAIMWorkchain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   Workchain to link quantum chemistry jobs without plugins to AIMAll

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



.. py:class:: GenerateWFXToAIMWorkchain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   Workchain to generate a wfx file from computational chemistry output files and submit that to an AIMQB Calculation

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



.. py:class:: SmilesToGaussianWorkchain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   Workchain to take a SMILES, generate xyz, charge, and multiplicity

   .. py:method:: define(spec)
      :classmethod:

      Define the specification of the process, including its inputs, outputs and known exit codes.

      A `metadata` input namespace is defined, with optional ports that are not stored in the database.



   .. py:method:: get_substituent_inputs_step()

      Given list of substituents and previously done smiles, get input


   .. py:method:: update_parameters_with_cm()

      Update provided Gaussian parameters with charge and multiplicity of substituent


   .. py:method:: string_to_StructureData()

      Convert an xyz string of molecule geometry to StructureData


   .. py:method:: get_wfx_name()

      Find the wavefunction file in the retrieved node


   .. py:method:: submit_gaussian()

      Submits the gaussian calculation


   .. py:method:: found_wfx_name()

      Check if we found a wfx or wfn file


   .. py:method:: create_wfx_file()

      Create a wavefunction file from the retireved folder


   .. py:method:: results()

      Store our relevant information as output



.. py:class:: AIMAllReor(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   Workchain to run AIM and then reorient the molecule using the results

   Process continues in GaussianSubmissionController

   .. py:method:: define(spec)
      :classmethod:

      Define the specification of the process, including its inputs, outputs and known exit codes.

      A `metadata` input namespace is defined, with optional ports that are not stored in the database.



   .. py:method:: aimall()

      submit the aimall calculation


   .. py:method:: rotate()

      perform the rotation


   .. py:method:: dict_to_struct_reor()

      generate the gaussian input from rotated structure


   .. py:method:: result()

      Parse results



.. py:function:: get_wfx(retrieved_folder, wfx_filename)

   Get a wfx file from retrieved folder


.. py:class:: BaseInputWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`aiida.engine.WorkChain`

   A workchain to generate and validate inputs. One of SinglefileData, Smiles as Str or StructureData should be
   provided

   .. py:method:: define(spec)
      :classmethod:

      Define the specification of the process, including its inputs, outputs and known exit codes.

      A `metadata` input namespace is defined, with optional ports that are not stored in the database.



   .. py:method:: is_xyz_input()

      Validates if xyz_file was provided as input


   .. py:method:: is_smiles_input()

      Validates if smiles was provided as input


   .. py:method:: is_structure_input()

      Validates if structure was provided as input


   .. py:method:: validate_input()

      Check that only one of smiles, structure, or xyz_file was input


   .. py:method:: create_structure_from_xyz()

      Convert the xyzfile to StructureData


   .. py:method:: structure_in_context()

      Store the input structure in context, to make consistent with the results of xyz_file or SMILES input


   .. py:method:: get_molecule_inputs_step()

      Given list of substituents and previously done smiles, get input


   .. py:method:: string_to_StructureData()

      Convert an xyz string of molecule geometry to StructureData



.. py:function:: get_molecule_str_from_smiles(smiles)

   For a given smiles, determine xyz structure, charge, and multiplicity

   :param smiles: SMILEs of substituent to run

   :returns: Dict with keys xyz, charge, multiplicity


.. py:class:: GaussianToAIMWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`BaseInputWorkChain`

   A workchain to submit a Gaussian calculation and automatically setup an AIMAll calculation on the output

   .. py:method:: define(spec)
      :classmethod:

      Define workchain steps


   .. py:method:: g16()

      Run Gaussian calculation


   .. py:method:: classify_wfx()

      Add the wavefunction file from the previous step to the correct group and set the extras


   .. py:method:: aim()

      Run Final AIM Calculation


   .. py:method:: result()

      Put results in output node



.. py:function:: xyzfile_to_StructureData(xyz_SFD)

   Convert the xyz file provided as SinglefileData to StructureData


.. py:class:: SubstituentParameterWorkChain(inputs: dict | None = None, logger: logging.Logger | None = None, runner: aiida.engine.runners.Runner | None = None, enable_persistence: bool = True)


   Bases: :py:obj:`BaseInputWorkChain`

   A workchain to perform the full suite of KLG's substituent parameter determining

   .. py:method:: define(spec)
      :classmethod:

      Define workchain steps


   .. py:method:: get_substituent_inputs_step()

      Get a dictionary of the substituent input for a given SMILES


   .. py:method:: g16_opt()

      Submit the Gaussian optimization


   .. py:method:: classify_opt_wfx()

      Add the wavefunction file from the previous step to the correct group and set the extras


   .. py:method:: aim_reor()

      Submit the Aimqb calculation and reorientation


   .. py:method:: g16_sp()

      Run Gaussian Single Point calculation


   .. py:method:: classify_sp_wfx()

      Add the wavefunction file from the previous step to the correct group and set the extras


   .. py:method:: aim()

      Run Final AIM Calculation


   .. py:method:: result()

      Put results in output node
