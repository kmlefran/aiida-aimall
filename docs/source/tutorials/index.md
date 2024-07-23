(tutorials)=

# Tutorials

`aiida-aimall` provides numerous `CalcFunctions`, `WorkChain`s, `FromGroupSubmissionController`s. Explore the documents below to learn how to use the numerous features provided.

```{toctree}
:hidden: true
:maxdepth: 1

aimqbparameters.ipynb
aimqbcalculation.ipynb
aimqbgroupcalculation.ipynb
aimtogaussian.ipynb

```
::::{grid} 2
:gutter: 3

:::{grid-item-card} {fa}`rocket;mr-1` `AimqbParameters`
:text-align: center
:shadow: md

Instructions to create the `AimqbParameters` datatype used throughout `aiida-aimall`

+++

```{button-ref} aimqbparameters
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:
```

:::

:::{grid-item-card} {fa}`rocket;mr-1` `AimqbCalculation`
:text-align: center
:shadow: md

Instructions to setup, launch, and analyze the results of the `AimqbCalculation` `CalcJob` class.

+++

```{button-ref} aimqbcalculation
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:
```

:::

::::


::::{grid} 2
:gutter: 3

:::{grid-item-card} {fa}`info-circle;mr-1` `Group Properties`
:text-align: center
:shadow: md

Using `aiida-aimall` to compute group properties.

+++

```{button-ref} aimqbgroupcalculation
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:
```
:::

:::{grid-item-card} {fa}`info-circle;mr-1` Workflow
:text-align: center
:shadow: md

The simplest workflow, linking a electronic structure software and AIMQB

+++

```{button-ref} aimtogaussian
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:
```
:::
::::
