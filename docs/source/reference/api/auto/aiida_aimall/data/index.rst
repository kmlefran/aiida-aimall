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

   .. py:attribute:: schema



   .. py:method:: validate(parameters_dict)

      Validate command line options.

      Uses the voluptuous package for validation. Find out about allowed keys using::

          print(AimqbParameters).schema.schema

      :param parameters_dict: dictionary with commandline parameters
      :param type parameters_dict: dict
      :returns: validated dictionary


   .. py:method:: cmdline_params(file_name)

      Synthesize command line parameters.

      e.g. [ '-atlaprhocps=True',...,'-nogui', 'filename']

      :param file_name: Name of wfx/fchk/wfn file
      :param type file_name: str



   .. py:method:: __str__()

      String representation of node.

      Append values of dictionary to usual representation. E.g.::

          uuid: b416cbee-24e8-47a8-8c11-6d668770158b (pk: 590)
          {'atlaprhocps': True}
