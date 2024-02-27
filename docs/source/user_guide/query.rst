====================
Querying for Results
====================

The following query will find the outputs of the AimqbCalculation on the reoriented structure, assuming that the AimqbCalculations are placed in the group "aim_reor".
Queries are built one step at a time. So, here, we find the group, then we find AimqbCalculations in the group, then we find the Dict outputs of the group, which are the outputs of the parser chosen in the AimqbCalculation:"aimall.base" or "aimall.group".
::

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
