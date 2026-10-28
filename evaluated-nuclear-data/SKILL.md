---
name: evaluated-nuclear-data
description: Obtain and compare evaluated nuclear cross sections (ENDF/B-VIII, JEFF-3.3/4.0, JENDL-5, TENDL, FENDL): pointwise sigma(E) from OpenMC HDF5 libraries or raw ENDF-6 files, NJOY processing at temperature, thermal values, resonance integrals, MACS and fission-spectrum averages, SAMMY resonance checks and Ferdinand R-matrix (LRF=7) conversion. Use whenever a task needs an evaluated cross section, a comparison between libraries, an ENDF MF/MT lookup, a charged-particle (p, alpha) sublibrary, or evaluated data next to EXFOR or an R-matrix fit; gamma-line and decay data for efficiencies use `efficiency-analysis`.
---
# Evaluated nuclear data

An evaluated cross section is often the reference against which a measurement, an R-matrix fit or a simulation input is compared, and a comparison is only meaningful if the number comes from a source that can be named, at the intended temperature and energy frame. This skill retrieves such cross sections and the quantities derived from them, and states what each number does and does not mean. You need the nuclide, the reaction (MT number), the temperature and the energy range, and either an OpenMC HDF5 library or a raw ENDF-6 file. You get σ(E) tables, window quantities (thermal value, resonance integral, MACS, fission-spectrum average) and library-spread tables, each labelled with library, version, build, temperature and MT.

## Where this fits

- Comes from: OpenMC HDF5 builds and raw ENDF-6 files from the distributors listed in [sources.md](references/sources.md); EXFOR data for comparison.
- Goes to: `reaction-network` for evaluated neutron cross sections and MACS; `r-matrix` for R-matrix parameters converted with Ferdinand and for comparisons with an R-matrix fit; `efficiency-analysis` and the Geant4 skills (`geant4-simulation`, `underground-gamma-simulation`) for cross sections used as inputs.
- Checked by: `scripts/selftest.py` (must print `PASS`), an independent SAMMY reconstruction where resonances matter, and `physics-referee` before a number is quoted.

## Choose the route

| Need | Route |
|---|---|
| Neutron σ(E) at 294 K (or another processed temperature), any library with an OpenMC build | HDF5: `scripts/xs.py get --lib <LIB> --nuc O16 --mt 107` |
| Same reaction in several libraries + spread | `scripts/xs.py compare --nuc Na23 --mt 102` |
| Thermal value, resonance integral, MACS, fission-spectrum average | `scripts/xs.py windows ...` |
| Charged-particle (p, α, d) sublibrary, or a library without an HDF5 build | raw ENDF-6: `scripts/xs.py get --endf FILE --mt 201` (MF3 as tabulated) |
| Raw ENDF-6 with resolved resonances, at a chosen temperature | `scripts/xs.py get --endf FILE --mt 102 --njoy --temp 600K` (NJOY2016 through OpenMC) |
| What is in a file (sublibrary, MTs, resonance formalism LRU/LRF, isomer data MF9/10) | `scripts/xs.py info --endf FILE` |
| Independent check of a resonance reconstruction | SAMMY with `INPUT IS ENDF/B FILE`, as described in [pitfalls.md](references/pitfalls.md) |
| R-matrix parameters of a light-element evaluation into AZURE2 | Ferdinand, only if MF2 has LRF=7 (check with `info` first) |

Three references hold the detail. [sources.md](references/sources.md) says what each library and build contains, where to get it and which servers refuse scripts, and is read before anything is downloaded. [endf-format.md](references/endf-format.md) gives the MF/MT numbers, sums and sublibraries. [pitfalls.md](references/pitfalls.md) is read before libraries are compared or a number is quoted.

## Setup

- Python with `numpy`, `openmc` (for HDF5 and NJOY routes) and `endf` (raw files): `mamba create -n nucdata -c conda-forge python=3.12 openmc endf numpy` (NJOY2016 comes with conda-forge OpenMC).
- Put HDF5 libraries in one folder, one subfolder per library (`ENDF-B-VIII.1/`, `JEFF-3.3/`, …), and point the environment variable `NUCLEAR_DATA_DIR` to that folder (e.g. `export NUCLEAR_DATA_DIR=/path/to/nuclear-data` in the shell profile). Edit the `LIBRARIES` dictionary at the top of `scripts/xs.py` if your subfolder names differ, or pass `--lib PATH` for a one-off library. Partial libraries with only the nuclides you need work.
- Run `python3 scripts/selftest.py`. It checks the window integrals analytically and, if a library is found, the thermal $^{10}$B$(n,\alpha)$ value; it must print `PASS`.

## Rules and their reasons

1. The source is named exactly: library and version, the build (OpenMC HDF5 from openmc.org, own NJOY run, raw ENDF), temperature, and the MT. "ENDF" alone is not a source, because builds of the same library differ in their contents and in the NJOY version used to process them (sources.md).
2. Energies are laboratory projectile energies in all ENDF products. They are converted explicitly before a comparison with c.m. quantities such as R-matrix fits and S factors: $E_\text{cm} = E_\text{lab}\,m_T/(m_p+m_T)$.
3. What the library actually contains is checked before a difference is called "library spread". Builds substitute files, for example the OpenMC JEFF-3.3 build uses TENDL-2019 for $^{13}$C and $^{17}$O, and libraries adopt each other's evaluations. Identical values therefore mean a shared evaluation, not a small uncertainty.
4. Like is compared with like: partial against total channels (MT800 vs MT107), the same temperature, the same averaging window and spectrum. Channels are summed from partials when the sum is not stored, because processed files may lack MT4, MT103–107 and MT1, and an R-matrix fit with only α₀ must be compared with MT800, not MT107 (pitfalls.md).
5. Never rescale an evaluation to match data or a model. State ratios instead.
6. Raw files are kept immutable, and the URL, date and checksum of every downloaded file are recorded.

## What to deliver

- The σ(E) table or window quantity with library, version, build, temperature and MT.
- For comparisons, the library-spread table with the number of independent evaluations rather than the number of libraries.
- The URL, date and checksum of every downloaded file.
