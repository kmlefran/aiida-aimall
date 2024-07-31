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
substituentparameter.ipynb
quantumsoftware.ipynb
controllers.ipynb

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

Workflow to generate a Gaussian calculation from a Substituent SMILES

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

::::{grid} 2
:gutter: 3

:::{grid-item-card} {fa}`info-circle;mr-1` `One step Workflow`
:text-align: center
:shadow: md

Using `aiida-aimall` to compute group properties.

+++

```{button-ref} quantumsoftware
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:
```
:::

:::{grid-item-card} {fa}`info-circle;mr-1` `Multi Step Workflow`
:text-align: center
:shadow: md

Workflow to start at a Gaussian calculation, optimize a molecule, run AIM, reorient, run Gaussian single point, run AIM, and get resulting substituent properties.

+++

```{button-ref} substituentparameter
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

:::{grid-item-card} {fa}`info-circle;mr-1` `Breaking the process into controllers`
:text-align: center
:shadow: md

Use controllers to compute substituent properties for a large set of substituents.

+++

```{button-ref} controllers
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:
```
:::

:::{grid-item-card} {fa}`info-circle;mr-1` `Generating WFX from other calculations`
:text-align: center
:shadow: md

Workflow to generate .wfx files from MOLDEN, .fchk, or CP2K atom log files

+++

```{button-ref} makewfx
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:
```
:::
::::
