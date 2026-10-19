# ENDF-6 cheat sheet (what you need to pull a cross section)

## Files (MF)
| MF | Content |
|---|---|
| 1 | header: MT451 description, ZA, AWR, sublibrary NSUB, temperature |
| 2 | resonance parameters (MT151): ranges with LRU (0 none, 1 resolved, 2 unresolved) and LRF (formalism) |
| 3 | cross sections σ(E) per MT, **lab energy in eV, barns** |
| 4 / 5 / 6 | angular / energy / correlated energy–angle distributions (MF6 also holds multiplicities) |
| 8, 9, 10 | decay and isomer production: MF9 = multiplicities to final states, MF10 = σ to final states |
| 12–15 | photon production |
| 31–40 | covariances (MF33 for MF3 cross sections, MF32 for resonance parameters) |

NSUB: 10 neutron, 10010 proton, 10020 deuteron, 20040 alpha, 0 photo.

LRF in MF2 (resolved range): 1 SLBW, 2 MLBW, 3 Reich–Moore, 7 R-matrix limited (multichannel, convertible with Ferdinand). Most light-element neutron files in ENDF/B-VIII.1 have **no** resolved parameters (LRU=0, scattering radius only): their σ is pointwise in MF3.

## Reaction numbers (MT), neutron sublibrary
| MT | Reaction | Note |
|---|---|---|
| 1 | total | redundant |
| 2 | elastic | |
| 3 | nonelastic | redundant |
| 4 | inelastic (n,n') total | sum of 51–91; **not stored in OpenMC HDF5**, rebuild |
| 16, 17 | (n,2n), (n,3n) | |
| 18 | fission (19–21, 38 chances) | |
| 22, 28 | (n,nα), (n,np) | |
| 51–90, 91 | (n,n') to level 1..40, continuum | |
| 102 | (n,γ) | isomer split, if any, in MF9/MF10 |
| 103–107 | (n,p), (n,d), (n,t), (n,³He), (n,α) | sums of 600–649, 650–699, 700–749, 750–799, 800–849 |
| 600, 601, … | (n,p₀), (n,p₁), … | |
| 800, 801, … | (n,α₀), (n,α₁), … | e.g. ¹⁶O(n,α₀)¹³C is MT800 |
| 201–207 | n, p, d, t, ³He, α production | |
| 452, 455, 456 | ν total, delayed, prompt (MF1) | |

Charged-particle sublibraries: elastic is MT2 (often with nuclear+Coulomb in MF6); reactions follow the same pattern with the *ejectile* defining the MT: (α,n) is MT50 (to g.s.) and MT51–91 (to excited states) or MT4 for the sum; **MT201 = total neutron production** (counts multiplicity, so (α,2n) counts twice). For an (α,n) source term use MT201 or the sum of neutron-emitting channels and state which.

## Temperatures and processing
- Raw ENDF is at 0 K (TEMP in MF1). Doppler broadening and resonance reconstruction are done by the processing code (NJOY RECONR/BROADR, or `openmc.data.IncidentNeutron.from_njoy(file, temperatures=[...])`).
- OpenMC HDF5 stores each temperature on its own energy grid (`n.energy['294K']`); 0 K data are usually absent.
- The OpenMC transport total is built from non-redundant reactions; when you modify a partial (e.g. scale MT51–91), the total follows automatically.

## Python access
```python
import endf                                   # raw ENDF-6
mat = endf.Material("8-O-16.endf")
s = mat.section_data[3, 107]["sigma"]          # Tabulated1D: s.x (eV), s.y (b)
mf2 = mat.section_data[2, 151]["isotopes"][0]["ranges"]   # LRU, LRF, EL, EH per range

import openmc.data as od                      # processed HDF5
n = od.IncidentNeutron.from_hdf5("O16.h5")
E = n.energy["294K"]; sig = n.reactions[107].xs["294K"](E)
```
