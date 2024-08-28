:py:mod:`aiida_aimall.parsers`
==============================

.. py:module:: aiida_aimall.parsers

.. autoapi-nested-parse::

   Parsers provided by aiida_aimall.

   Register parsers via the "aiida.parsers" entry point in pyproject.toml.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.parsers.AimqbBaseParser
   aiida_aimall.parsers.AimqbGroupParser




Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_aimall.parsers.AimqbCalculation
   aiida_aimall.parsers.NUM_RE
   aiida_aimall.parsers.SinglefileData


.. py:data:: AimqbCalculation



.. py:class:: AimqbBaseParser(node)


   Bases: :py:obj:`aiida.parsers.parser.Parser`

   Parser class for parsing output of calculation.

   .. py:method:: parse(**kwargs)

      Parse outputs, store results in database.

      :returns: an exit code, if parsing fails (or nothing if parsing succeeds)


   .. py:method:: _parse_ldm(sum_lines)


   .. py:method:: _parse_cc_props(atomic_properties)

      Extract VSCC properties from output files
      :param atomic_properties: dictionary of atomic properties from _parse_atomic_props
      :param type atomic_properties: dict


   .. py:method:: _parse_atomic_props(sum_file_string)

      Extracts atomic properties from .sum file

      :param sum_file_string: lines of .sum output file
      :param type sum_file_string: str


   .. py:method:: _parse_bcp_props(sum_file_string)

      Extracts bcp properties from .sum file

      :param sum_file_string: lines of .sum output file
      :param type sum_file_string: str



.. py:data:: NUM_RE
   :value: '[-+]?(?:[0-9]*[.])?[0-9]+(?:[eE][-+]?\\d+)?'



.. py:data:: SinglefileData



.. py:class:: AimqbGroupParser(node)


   Bases: :py:obj:`AimqbBaseParser`

   Parser class for parsing output of calculation.

   .. py:method:: parse(**kwargs)

      Parse outputs, store results in database.

      :returns: an exit code, if parsing fails (or nothing if parsing succeeds)


   .. py:method:: _parse_graph_descriptor(out_dict)

      Get atomic, BCP, and VSCC properties of atom 1


   .. py:method:: _parse_group_descriptor(atomic_properties, sub_atom_ints)

      Convert atomic properties to group properties given atoms in group to use
