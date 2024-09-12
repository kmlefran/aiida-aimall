:py:mod:`aiida_aimall.data`
===========================

.. py:module:: aiida_aimall.data

.. autoapi-nested-parse::

   Data types provided by plugin



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_aimall.data.AimqbParameters




Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_aimall.data.cmdline_options


.. py:data:: cmdline_options



.. py:class:: AimqbParameters(parameter_dict=None, **kwargs)


   Bases: :py:obj:`aiida.orm.Dict`

   Command line options for aimqb.

   This class represents a python dictionary used to
   pass command line options to the executable.
   The class takes a dictionary of parameters and validates
   to ensure the aimqb command line parameters are correct

   :param parameters_dict: dictionary with commandline parameters
   :type parameters_dict: `dict`

   Usage:
       ``AimqbParameters(parameter_dict{'naat':2})``


   .. py:attribute:: schema



   .. py:method:: validate(parameters_dict)

      Validate command line options.

      Uses the voluptuous package for validation. Find out about allowed keys using::

          print(AimqbParameters).schema.schema

      :param parameters_dict: dictionary with commandline parameters
      :type parameters_dict: dict

      :returns: input dictionary validated against the allowed options for aimqb


   .. py:method:: cmdline_params(file_name)

      Synthesize command line parameters and add -nogui for use in `AimqbCalculation`.

      :param file_name: Name of wfx/fchk/wfn file
      :type file_name: str

      :returns:

                command line parameters for aimqb collected in a list
                    e.g. [ '-atlaprhocps=True',...,'-nogui', 'filename']


   .. py:method:: __str__()

      String representation of node. Append values of dictionary to usual representation.

      :returns: representation of node, including uuid, pk, and the contents of the dictionary
