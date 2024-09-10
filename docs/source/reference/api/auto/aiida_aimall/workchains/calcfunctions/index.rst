:py:mod:`aiida_aimall.workchains.calcfunctions`
===============================================

.. py:module:: aiida_aimall.workchains.calcfunctions

.. autoapi-nested-parse::

   Calcfunctions used throughout workchains



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   aiida_aimall.workchains.calcfunctions.generate_rotated_structure_aiida
   aiida_aimall.workchains.calcfunctions.remove_numcharss_from_strlist
   aiida_aimall.workchains.calcfunctions.dict_to_structure
   aiida_aimall.workchains.calcfunctions.calc_multiplicity
   aiida_aimall.workchains.calcfunctions.find_attachment_atoms
   aiida_aimall.workchains.calcfunctions.reorder_molecule
   aiida_aimall.workchains.calcfunctions.get_xyz
   aiida_aimall.workchains.calcfunctions.get_substituent_input
   aiida_aimall.workchains.calcfunctions.generate_structure_data
   aiida_aimall.workchains.calcfunctions.parameters_with_cm
   aiida_aimall.workchains.calcfunctions.get_wfxname_from_gaussianinputs
   aiida_aimall.workchains.calcfunctions.create_wfx_from_retrieved
   aiida_aimall.workchains.calcfunctions.validate_shell_code
   aiida_aimall.workchains.calcfunctions.validate_parser
   aiida_aimall.workchains.calcfunctions.validate_file_ext
   aiida_aimall.workchains.calcfunctions.get_molecule_str_from_smiles
   aiida_aimall.workchains.calcfunctions.xyzfile_to_StructureData



.. py:function:: generate_rotated_structure_aiida(FolderData, atom_dict, cc_dict)

   Rotates the fragment to the defined coordinate system

   :param FolderData: aim calculation folder
   :type FolderData: aiida.orm.FolderData
   :param atom_dict: AIM atom dict
   :param cc_dict: AIM cc_dict

   :returns:

             Dict with keys 'atom_symbols' and 'geom' containing atomic symbols and the
                 the rotated geometry.


.. py:function:: remove_numcharss_from_strlist(in_list)

   Remove digits from a list of strings. e.g. ['O1','H2','H3'] -> ['O','H','H']

   :param in_list: input list to remove digits from

   :returns: output list with the numerical digits removed from each element

   .. note::

      The intention for this list is to convert numered atomic symbols, e.g. from Gaussian
          to just symbols


.. py:function:: dict_to_structure(fragment_dict)

   Generate a StructureData for Gaussian inputs

   :param fragment_dict: AiiDA orm.Dict with keys 'atom_symbols' and 'geom'
   :type fragment_dict: aiida.orm.Dict

   :returns: aiida.orm.StructureData for the molecule

   .. note::

      input can be generated, for example, by
          :func:`aiida_aimall.workchains.calcfunctions.generate_rotated_structure_aiida`


.. py:function:: calc_multiplicity(mol)

   Calculate the multiplicity of a molecule as 2S +1

   Loops over the atoms in the molecule and gets number of radical electrons,
   then converts that number to the multiplicity.

   :param mol: rdkit.Chem molecule object

   :returns: integer number of multiplicity


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

   :param reorder_mol: rdkit.Chem molecule output, output of :func:`aiida_aimall.workchains.calcfunctions.reorder_molecule`

   :returns: string of the geometry block of an .xyz file


.. py:function:: get_substituent_input(smiles: str) -> dict

   For a given smiles, determine xyz structure, charge, and multiplicity

   :param smiles: SMILEs of substituent to run

   :returns: Dict with keys xyz, charge, multiplicity

   :raises ValueError: if molecule cannot be built from SMILES


.. py:function:: generate_structure_data(smiles_dict)

   Take an input xyz string and convert it to StructureData

   :param smiles_dict: output of :func:`aiida_aimall.workchains.calcfunctions.get_substituent_input`

   :returns: StructureData of the molecule


.. py:function:: parameters_with_cm(parameters, smiles_dict)

   Add charge and multiplicity keys to Gaussian Input

   :param parameters: dictionary to be provided to GaussianCalculation
   :param smiles_dict: `aiida_aimall.workchains.calcfunctions.get_substituent_input`

   :returns: Dict of Gaussian parameters updated with charge and multiplicity


.. py:function:: get_wfxname_from_gaussianinputs(gaussian_parameters)

   Find the .wfx filename from gaussian_parameters

   Check if input parameters was provided to gaussian_parameters, and if so, look for
   .wfx file names supplied. If it was, return the first .wfx filename found

   :param gaussian_parameters: input dictionary to be provided to GaussianCalculation

   :returns: Str of .wfx filename


.. py:function:: create_wfx_from_retrieved(wfxname, retrieved_folder)

   Create wavefunction SinglefileData from retrieved folder

   :param wfxname: Str of the name of a .wfx file to get from the retrieved folder
   :param retrieved_folder: FolderData of a completed GaussianCalculation

   :returns: SinglefileData of the .wfx file to find in the FolderData


.. py:function:: validate_shell_code(node, _)

   Validate the shell code, ensuring that it is ShellCode or Str

   :param node: input node to check the type for ShellCode or Str

   :returns: None if the type is ShellCode or Str, or error string if node is not


.. py:function:: validate_parser(node, _)

   Validate the parser, ensuring that the provided value is one of the accepted values.

   :param node: input node to check the type for ShellCode or Str

   :returns: None if the value is aimall.base or aimall.group, or an error string if it is not


.. py:function:: validate_file_ext(node, _)

   Validates that the file extension provided for AIM is wfx, wfn or fchk

   :param node: node to check the value of to ensure it is in a supported format

   :returns: None if the type is ShellCode or Str, or error string if node is not


.. py:function:: get_molecule_str_from_smiles(smiles)

   For a given smiles, determine xyz structure, charge, and multiplicity

   :param smiles: SMILEs of substituent to run

   :returns: Dict with keys xyz, charge, multiplicity


.. py:function:: xyzfile_to_StructureData(xyz_SFD)

   Convert the xyz file provided as SinglefileData to StructureData
