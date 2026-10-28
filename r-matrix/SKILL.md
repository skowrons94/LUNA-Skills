---
name: r-matrix
description: Run and check R-matrix evaluations of reaction and scattering data with AZURE2 (charged-particle reactions, radiative capture, Brune parameterization, pyazr) or SAMMY (neutron-induced resonances with Doppler and resolution broadening, Reich–Moore, Bayes fitting, ENDF output): choose the code, fit levels and widths, add or remove levels and channels, decompose, extrapolate, compute rates, convert through ENDF, and test that a fit is physical (Park norm and saturated levels, transformability, covariance against profile scans). Use whenever a task involves an .azr or SAMMY file, R-matrix levels, channels or segments, S factors, extrapolations, or whether fitted widths and their uncertainties are physical.
---

# R-matrix evaluations: AZURE2 and SAMMY

An R-matrix evaluation turns measured cross sections, scattering data and S factors into a level scheme of the compound nucleus, and through it into an S factor at stellar energies, a reaction rate or an evaluated file. The physics is the same in the two codes this skill covers, but the data they are built for are not: AZURE2 is the code for charged-particle reactions and radiative capture, with external capture and the Brune parameterization, and SAMMY is the code for neutron-induced resonances, with Doppler and resolution broadening, Bayes fitting and ENDF output. This skill says which code to use, how to run each, and how to check that a fit is physical before its numbers are quoted. You need the data and a model file (an `.azr` project, or a SAMMY input, parameter and data file). You get χ² per data set, fitted parameters with their convention stated, extrapolations, decompositions, rates or ENDF files, and the physicality checks of the adopted model.

## Where this fits

- Comes from: `yield-analysis` and cross-section tables through the `to-azure` adapter of `analysis-chain` (contract `azure-dat`); effective energies and target thickness from `target-analysis`; lifetimes and widths from `delta-beta-dsam`; the structure behind a level or width from `shell-model`, `cluster-potential`, `microscopic-cluster` and `mirror-nucleus`, and scattering lengths from `effective-range`; repaired level schemes from `resonance-search`; evaluated data to compare with from `evaluated-nuclear-data`; the reactions that matter most, from the sensitivity runs of `reaction-network`.
- Goes to: `reaction-network` (contract `rate-table`, converted with `rates.py from-azure`) and `stellar-evolution`; cross sections for `target-analysis`; phase-shift grids for `effective-range`; fits to compare with in `cluster-potential`, `microscopic-cluster` and `mirror-nucleus`; repairs of the level scheme in `resonance-search`; posterior sampling in `rmatrix-posterior`; ENDF files for `evaluated-nuclear-data`.
- Checked by: the run checks of each code, `scripts/park_norms.py` on the adopted AZURE2 model, and `uncertainty-audit` or `physics-referee` before a fit, S factor or rate is quoted.

## Choosing the code

| Task | Code | Read |
|---|---|---|
| Charged-particle reactions and elastic scattering, radiative capture with external capture, γ branchings, analyzing powers, THM; S factors and astrophysical rates | AZURE2 with pyazr | [azure2.md](references/azure2.md) |
| Neutron-induced resonances: transmission, capture and fission yields with Doppler and resolution broadening, resolved-resonance evaluation with covariance, ENDF File 2 and 32; charged incident particles only for angle-differential cross sections | SAMMY | [sammy.md](references/sammy.md) |
| Moving parameters between the codes and ENDF; there is no direct AZURE2–SAMMY converter, so the route is ENDF File 2 LRF=7 with Ferdinand, minding the boundary conditions | Ferdinand, SAMMY with ENDF input | [sammy.md](references/sammy.md), `evaluated-nuclear-data` |
| Whether the fit is physical: saturated levels, transformability, honest uncertainties | either | [physicality.md](references/physicality.md) |

The local SAMMY build of the 7Be project does not run (Debug libraries with AddressSanitizer that hang at start-up); sammy.md records the state and what a clean rebuild needs.

## Rules and their reasons

1. Energies are given with their frame, because the codes use different ones. AZURE2 takes the laboratory energy with forward kinematics and returns everything in the centre of mass, while SAMMY works in the laboratory energy of the incident particle.
2. The channel radius is part of every width. A reduced width is meaningful only with its radius and its unit, θ² in Teichmann–Wigner units (3ħ²/(2μa²), the `theta2` of pyazr) or in ħ²/μa² (1.5 times larger), so both are stated, and the conclusion is tested against the radius.
3. The parameter convention is stated, because Brune, Reich–Moore and formal widths are not interchangeable. In the Brune parameterization the observed widths are the formal ones times one factor per level, the Park norm J, and for a saturated level (J ≪ 1) they still look ordinary. `scripts/park_norms.py` is therefore run on every adopted AZURE2 model; in the 7Be evaluation it found a level at J = 0.05 whose widths looked unremarkable.
4. A fitted width is not a spectroscopic factor. A large width can encode a scattering length (a hard core, see `effective-range`) or background, so it is compared with structure from `shell-model` or `cluster-potential` at the fitted energy and radius before it is called a property of a state.
5. The covariance is checked against a profile scan for the parameters the conclusion rests on. A near-singular problem, caused by saturated levels or unconstrained background poles, gave a 7Be width error eleven times too wide.
6. "Internal" and "external" capture are statements at the channel radius. Microscopic models of 3He(α,γ)7Be find the low-energy capture external, so a paper does not say that a reaction "requires an internal amplitude" without that qualifier.
7. The total χ² of every adopted model is recorded and reproduced after any file change, because stale external-capture caches, merged levels and misaligned parameters show up there first.

## Where to read next

| Task | Read |
|---|---|
| AZURE2: CLI and pyazr, rules, runs, verification | [azure2.md](references/azure2.md) |
| Parameter conventions, χ² per dataset, observables, least-squares fits | [pyazr.md](references/pyazr.md) |
| Adding, removing and moving levels, `AzrModel`, extrapolation grids | [model-editing.md](references/model-editing.md) |
| Decomposition, S factor, significance tests, radius changes, evaluation recipes | [decomposition-and-recipes.md](references/decomposition-and-recipes.md) |
| Trojan Horse (THM/HOES) segments | [thm.md](references/thm.md) |
| `.azr` anatomy, `.dat` format, output files | [files.md](references/files.md) |
| Ready-made 7Be scripts, pyazr examples | [scripts-and-examples.md](references/scripts-and-examples.md) |
| Park norm, stiff bounds, transformability, covariance against profile, structure-predicted channels, pitfalls | [physicality.md](references/physicality.md) |
| SAMMY: input, parameters, broadening, Bayes fitting, ENDF, local installation | [sammy.md](references/sammy.md) |

## Scripts

```bash
python SKILL_DIR/scripts/park_norms.py model.azr output/param.sav    # J per level from pyazr; flags J < 0.5
```
Replace SKILL_DIR with this skill's directory; the script runs from the directory the `.azr` expects.

## What to deliver

- The model file and parameters of the reported fit, with the total χ² recorded for it, the code and its version or build, and the flags used.
- Every quoted width with its channel radius, unit and parameter convention.
- The Park norm of every level below the background poles, and the cost of any bound applied to it.
- For the parameters a conclusion rests on, the covariance error next to a profile scan.
- Extrapolated S factors, rates or ENDF files, with the frame of every quoted energy stated.
