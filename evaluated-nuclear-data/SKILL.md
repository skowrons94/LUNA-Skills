---
name: evaluated-nuclear-data
description: Obtain and compare evaluated nuclear cross sections (ENDF/B-VIII, JEFF-3.3/4.0, JENDL-5, TENDL, FENDL) — pointwise sigma(E) from OpenMC HDF5 libraries or raw ENDF-6 files, NJOY processing at temperature, thermal values, resonance integrals, MACS and fission-spectrum averages, library-spread tables, resonance-parameter checks with SAMMY and R-matrix (LRF=7) conversion with Ferdinand. Use whenever a task needs an evaluated cross section, a comparison between libraries, an ENDF MF/MT lookup, a charged-particle (p, alpha) sublibrary, or evaluated data next to EXFOR or an R-matrix fit.
---
# Evaluated nuclear data

Get an evaluated cross section quickly, from a source you can name, at the temperature and energy frame you intend, and know what the number does and does not mean.

## Choose the route

| Need | Route |
|---|---|
| Neutron σ(E) at 294 K (or another processed temperature), any library with an OpenMC build | **HDF5**: `scripts/xs.py get --lib <LIB> --nuc O16 --mt 107` |
| Same reaction in several libraries + spread | `scripts/xs.py compare --nuc Na23 --mt 102` |
| Thermal value, resonance integral, MACS, fission-spectrum average | `scripts/xs.py windows ...` |
| Charged-particle (p, α, d) sublibrary, or a library without an HDF5 build | **raw ENDF-6**: `scripts/xs.py get --endf FILE --mt 201` (MF3 as tabulated) |
| Raw ENDF-6 with resolved resonances, at a chosen temperature | `scripts/xs.py get --endf FILE --mt 102 --njoy --temp 600K` (NJOY2016 through OpenMC) |
| What is in a file (sublibrary, MTs, resonance formalism LRU/LRF, isomer data MF9/10) | `scripts/xs.py info --endf FILE` |
| Independent check of a resonance reconstruction | SAMMY with `INPUT IS ENDF/B FILE` (see [pitfalls.md](references/pitfalls.md)) |
| R-matrix parameters of a light-element evaluation into AZURE2 | Ferdinand, only if MF2 has LRF=7 (check with `info` first) |

Read [sources.md](references/sources.md) before downloading anything (what each library and build contains, where to get it, which servers refuse scripts). Read [endf-format.md](references/endf-format.md) for MF/MT numbers, sums and sublibraries. Read [pitfalls.md](references/pitfalls.md) before comparing libraries or quoting a number.

## Setup

- Python with `numpy`, `openmc` (for HDF5 and NJOY routes) and `endf` (raw files): `mamba create -n nucdata -c conda-forge python=3.12 openmc endf numpy` (NJOY2016 comes with conda-forge OpenMC).
- Put HDF5 libraries under `~/nuclear-data/<LIBRARY>/` and edit the `LIBRARIES` dictionary at the top of `scripts/xs.py` if your layout differs. Partial libraries (only the nuclides you need) work.
- Run `python3 scripts/selftest.py`: it checks the window integrals analytically and, if a library is found, the thermal $^{10}$B$(n,\alpha)$ value; it must print `PASS`.

## Rules

1. **Name the source exactly**: library and version, the build (OpenMC HDF5 from openmc.org, own NJOY run, raw ENDF), temperature, and the MT. "ENDF" alone is not a source.
2. **Energies are laboratory projectile energies** in all ENDF products. Convert explicitly before comparing with c.m. quantities (R-matrix, S factors): $E_\text{cm} = E_\text{lab}\,m_T/(m_p+m_T)$.
3. **Check what the library actually contains** before calling a difference "library spread": builds substitute files (the OpenMC JEFF-3.3 build uses TENDL-2019 for $^{13}$C and $^{17}$O), and libraries adopt each other's evaluations. Identical values mean shared evaluation, not small uncertainty.
4. **Compare like with like**: partial vs total channels (MT800 vs MT107), the same temperature, the same averaging window and spectrum. Sum channels from partials when the sum is not stored.
5. **Never rescale an evaluation** to match data or a model. State ratios instead.
6. **Keep raw files immutable** and record URL, date and checksum for every downloaded file.
