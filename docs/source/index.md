---
myst:
  substitutions:
    README.md of the repository: '`README.md` of the repository'
    aiida-core documentation: '`aiida-core` documentation'
    aiida-aimall: '`aiida-aimall`'
---

```{toctree}
:hidden: true

installation/index
```

```{toctree}
:hidden: true

tutorials/index
```

```{toctree}
:hidden: true

developer_guide/index
```

```{toctree}
:hidden: true
:caption: Reference
reference/api/auto/aiida_aimall/index
```

# aiida-aimall

An AiiDA plugin package to integrate the [AIMAll](https://aim.tkgristmill.com) software suite. Automate
workflows integrating Gaussian calculations with AIMAll, or with any computational chemistry software
that can be run through the command line. Workflows and controllers are provided to enable automation,
starting with even just a SMILES string to generate geometries using RDKit, then perform
Gaussian calculations, then AIMAll. Workflows to generate substituent parameters as defined by the authors
are also provided.

[![ci](https://github.com/kmlefran/aiida-aimall/actions/workflows/ci.yml/badge.svg)](https://github.com/kmlefran/aiida-aimall/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/kmlefran/aiida-aimall/badge.svg?branch=main)](https://coveralls.io/github/kmlefran/aiida-aimall?branch=main)
[![Documentation Status](https://readthedocs.org/projects/aiida-aimall/badge/?version=latest)](https://aiida-aimall.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/aiida-aimall.svg)](https://badge.fury.io/py/aiida-aimall)


______________________________________________________________________


::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} {fa}`rocket;mr-1` Get started
:text-align: center
:shadow: md

Instructions to install, configure and setup the plugin package.

+++

```{button-ref} installation/index
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

To the installation guides
```
:::

:::{grid-item-card} {fa}`info-circle;mr-1` Tutorials
:text-align: center
:shadow: md

Easy examples to take the first steps with the plugin package.

+++

```{button-ref} tutorials/index
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

To the tutorials
```
:::
::::

[aiida]: http://aiida.net
[aiida-core documentation]: https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/get_started.html
[subproptools documentation]: https://subproptools.readthedocs.io/
