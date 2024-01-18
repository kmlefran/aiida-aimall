====================
Querying for Results
====================

The following query will find the outputs of the AimqbCalculation on the reoriented structure::

    query = QueryBuilder()
    query.append(
        Group,
        filters={
            'label': 'aim_reor'
        },
        tag='group'
    )
    query.append(
        AimqbCalculation,
        tag = 'calculation',
        with_group = 'group'
    )
    query.append(
        Dict,
        with_incoming = 'calculation'
    )
