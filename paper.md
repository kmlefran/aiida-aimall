---
title: 'aiida-aimall: A Python package for automating workflows for AIMAll software'
tags:
  - Python
  - AiiDA
  - Quantum Theory of Atoms in Molecules
  - AIMAll
  - Computational chemistry
authors:
  - name: Kevin M. Lefrancois-Gagnon
    orcid: 0000-0001-5291-1795
    equal-contrib: true
    affiliation: 1 # (Multiple affiliations must be quoted)
  - name: Robert C. Mawhinney
  - orcid: 0000-0002-6077-2403
    equal-contrib: true # (This is how you can denote equal contributions between multiple authors)
    affiliation: 1
affiliations:
 - name: Lakehead University, Thunder Bay, ON, Canada
   index: 1
date: 14 July 2024
bibliography: paper.bib

---

# Summary

Since its introduction by Richard Bader, the Quantum Theory of Atoms in Molecules
(QTAIM) has become a useful tool for computational chemists. This Python package
provides plugins for a common QTAIM software, AIMAll, for the AiiDA Python
infrastructure. `aiida-aimall` is an essential tool for ensuring reproducible
calculations, with full generation history. Workflows are also provided to interface
`AIMAll` software with any quantum chemistry package that can be run through the command line,
so long as it generates the input files required by `AIMAll`.

# Statement of need

`aiida-aimall` is a Python package based on the AiiDA [@aiida] infrastructure designed
to assist users with generating inputs for AIMAll software [@AIMAll]. The goal of
the AiiDA infrastructure are, in part, to ensure data provenance and calculation
reproducibility. While `aiida-aimall` has been developed primarily for interface
with Gaussian software outputs [@gaussian], through modification of classes provided
by `aiida-gaussian` [@aiidagaussian], a versatile workflow enabling interface with
other quantum chemistry packages is also made available.

Through a variety of workflows that can start with Cartesian coordinates, or even with
a SMILES string of a molecule, `aiida-aimall` provides a variety of use cases for automating
and complex workflows. Additionally tools to ensure that computers are not overloaded through
too many simultaneous processes are made availabe through classes of `FromGroupSubmissionController`s
from `aiida-submission-controller` to limit active processes.

# Features
`aiida-aimall` contains many different classes from `aiida` tailored to ensure ease of use of
AIMAll calculations. Numerous features provided by `aiida-aimall` are provided in the documentation webpage hosted on ReadTheDocs. Select features are highlighted here.

Apart from the  `AimqbCalculation` that provides the functionality, to run
AIMAll calculations, a key feature is the `AimqbParameters` data type. The `AimqbParameters` datatype
is a validator for `AIMAll` command line input. Command line parameters are to be provided as a dictionary,
then `AimqbParameters` ensures that the parameters match options available for AIMAll software as
[defined on the software website](https://aim.tkgristmill.com/manual/aimqb/aimqb.html), and that the
correct data type is provided for each parameter. In this way, `AimqbParameters` verifies the provided input
to AIMAll calculations prior to launch of the calculation.

Further, AiiDA workchains are provided to automate routine workflows associated with AIMAll calculations.
The simplest workchain takes links a Gaussian calculation to an AIMAll calculation through a .wfx file produced by
the Gaussian calculation. More complex workchains exist to produce substituent parameters as defined by the authors in a series of publications. To not limit the usefulness of `aiida-aimall` to only users who use Gaussian software,
an additional WorkChain is provided using `aiida-shell` to interface with any quantum chemistry package that can
be run through the command line.

The last main contribution of `aiida-aimall` is through the definition of `FromGroupSubmissionController`s from the `aiida-submission-controller` package. These controllers limit active processes and can be used together as
demonstrated in (the example notebook) to automate the entire process of generating the author's substituent
parameters for numerous inputs without overloading local or remote computers.

# Mathematics

Single dollars ($) are required for inline mathematics e.g. $f(x) = e^{\pi/x}$

Double dollars make self-standing equations:

$$\Theta(x) = \left\{\begin{array}{l}
0\textrm{ if } x < 0\cr
1\textrm{ else}
\end{array}\right.$$

You can also use plain \LaTeX for equations
\begin{equation}\label{eq:fourier}
\hat f(\omega) = \int_{-\infty}^{\infty} f(x) e^{i\omega x} dx
\end{equation}
and refer to \autoref{eq:fourier} from text.

# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from Brigitta Sipocz, Syrtis Major, and Semyeong
Oh, and support from Kathryn Johnston during the genesis of this project.

# References
