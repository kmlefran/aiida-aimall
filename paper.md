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
AIMAll calculations. Numerous features provided by `aiida-aimall` are described in full on the [documentation webpage hosted on ReadTheDocs](https://aiida-aimall.readthedocs.io/en/latest/). A brief description of main features is provided here.

## Running Simple AIMAll Calculations

The simplest functionality provided by `aiida-aimall` is running AIMAll calculations. All AIMAll calculations utilize the `AimqbParameters` `Data` type provided by `aiida-aimall`. The `AimqbParameters` datatype
is a validator for `AIMAll` command line input. Command line parameters are to be provided as a dictionary,
then `AimqbParameters` ensures that the parameters match options available for AIMAll software as
[defined on the software website](https://aim.tkgristmill.com/manual/aimqb/aimqb.html), and that the
correct data type is provided for each parameter. In this way, `AimqbParameters` verifies the provided input
to AIMAll calculations prior to launch of the calculation. These parameters, along with `SinglefileData` of a valid AIMAll input file, a `Code` object for AIMAll software, and relevant metadata are provided to an `AimqbCalculation`.

This functionality in itself is an overcomplication of the simple process of running the software normally. However, it does have some benefits. The output is already extracted and stored in the database in a readily useable manner. Related, it is now simple to see the history of the calculation.

## Integrations with Computational Chemistry Software

`aiida-aimall`'s main draw is that it enables automation to link the outputs of standard computational chemistry software directly to an AIMAll calculation. A list of provided workflows is shown in Table COMPLETE. The software with the most robust implementation is Gaussian software,[@gaussian] as Gaussian already has an implemented `aiida` package.

Table 1: Main workflows provided by `aiida-aimall`, their `aiida` entry points that can be used to load them by `aiida.plugins.WorkflowFactory`, and a brief description. These workflows all end with the output of an `AimqbCalculation` as their main output.[]{label="workflows"}

| Workflow                        | Entry Point     | Purpose                                                                                       |
|---------------------------------|-----------------|-----------------------------------------------------------------------------------------------|
|`QMToAIMWorkchain`               | aimall.qmtoaim  | Run a general computational<br><br> chemistry software andl<br><br> link it to an AIMAll <br>calculation   |
|`GenerateWFXToAIMWorkchain`      | aimall.wfxtoaim | Take non-standard AIMAlll<br><br>  input files,l<br><br>  and run AIMAll                                  |
|`GaussianToAIMWorkChain`         | aimall.g16toaim | Run a Gaussian calculationl<br><br>  and automatically runl<br><br>  an AIMAll calculation onl<br><br>  its outputs |
| `SubstituentParameterWorkChain` | aimall.subparam | Compute substituentl<br><br>  properties defined by<br><br> the authors automatically|

## Controllers to limit computer burden when running large numbers of jobs
The last main contribution of `aiida-aimall` is through the definition of `FromGroupSubmissionController`s from the `aiida-submission-controller` package. These controllers limit active processes and can be used together as
demonstrated in (the example notebook) to automate the entire `SubstituentParameterWorkchain`. These use a number of `Workchains` developed just for their use in these controllers. The process flows as `SmilesToGaussianController` -> `AIMAllReorController` -> `GaussianController` -> `AIMAllController`. The latter two controllers can also be seen and used as general use controllers wrapping `GaussianCalculations` and `AimqbCalculations`

# Acknowledgements

We acknowledge NSERC,

# References
