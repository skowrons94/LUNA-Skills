---
name: delta-beta-dsam
description: Measure or simulate femtosecond nuclear lifetimes with the Doppler-velocity DSAM (Delta-beta) method, Δβ = β_reac − β_ems, with the reaction velocity from the detected ejectile and the emission velocity from the Doppler shift, Δβ(θ) centroids with an energy/angle-offset nuisance fit, and a Δβ–τ calibration. Use for AGATA/GRETA/HPGe lifetime analyses with a silicon ejectile detector, implanted or gas targets, inverse-kinematics transfer reactions, DSAM feasibility and lifetime sensitivity studies, Bayesian Δβ–τ fits, or whenever someone mentions delta beta, beta_reac/beta_ems, Doppler-shift attenuation with ejectile tagging, or the 15O/22Na/27Si lifetime analyses.
---
# Doppler-velocity DSAM (Δβ) analysis

An excited recoil slows down in the backing before it decays, so a longer lifetime gives a smaller Doppler shift. The method measures, event by event, the difference Δβ = β_reac − β_ems between the recoil velocity at the reaction, reconstructed from the detected ejectile, and the velocity at gamma emission, obtained from the Doppler shift. For τ up to a few tens of fs the difference is linear in the lifetime, Δβ ≈ (dβ/dt)·τ. You need ejectile energies and angles, gamma energies with interaction points, and the stopping powers of the backing. You get Δβ(θ) fits, a Δβ–τ calibration, and lifetimes or, for a feasibility study, the expected lifetime sensitivity.

The method follows Fougères et al., Nature Commun. 14, 4536 (2023) and the 15O AGATA lifetime paper (J. Skowronski et al., submitted 2026; analysis code github.com/skowrons94/15O_Lifetime). The worked example is the 28Si(3He,α)27Si AGATA feasibility study.

## Where this fits

- Comes from: measured ejectile and gamma data, or simulated events from `agata-simulation` and `geant4-simulation`; stopping powers from SRIM or Geant4.
- Goes to: lifetimes and widths of the levels, for example for an R-matrix evaluation in `azure2`; plots through `prc-figures`.
- Checked by: `python3 scripts/selftest.py`, the no-stopping reference described below, and `uncertainty-audit`.

## Library

`scripts/dbeta.py` is imported as a library (numpy and scipy). Run `python3 scripts/selftest.py` first: on synthetic data it checks the inversion, the absence of bias without stopping, the linearity in τ and the recovery of an energy offset. The formulas, the systematics and the uncertainty budget are in [references/method.md](references/method.md).

## Method

1. β_reac from the ejectile (`recoil_from_ejectile`). Correct the measured ejectile energy for its losses in the backing, the target remainder, foils and detector dead layers (`energy_before`, with SRIM or Geant4 dE/dx), placing the reaction at the mid-depth of the implanted or active layer. Energy and angle are both used, through momentum conservation: the recoil direction is p_beam − p_ejectile. The beam energy is corrected for its loss on the way to the reaction depth.
2. Check the kinematics by reconstructing E_x from the missing mass of every event. Its centroid must sit at the level energy; in the 15O analysis it did so within 12 keV. This bounds coherent biases of β_reac, because an energy-scale error shifts β_reac and E_x together. Gate on E_x to reject punch-through and misidentified ejectiles. The E_x resolution is usually far too poor to separate neighbouring states, so the state is selected with its gamma line, and with γγ gates on secondaries.
3. β_ems (`beta_ems`). Invert E_obs = E0 √(1−β²)/(1−β cos θ), with θ the angle between the gamma ray (first or main interaction point after PSA) and the reconstructed recoil, and take the root closest to β_reac. Select events with `doppler_window`, between the fully shifted and the unshifted energy ± the resolution, and if needed with a window on the Doppler-corrected energy.
4. Δβ(θ) (`dbeta_windows`, `fit_dbeta_theta`). Use 7° windows of θ, a Gaussian-core centroid per window and bootstrap errors. Fit Δβ(θ) = Δβ_true + distortion(θ; ΔE, Δθ) with ΔE free and Δθ fixed: the two offsets are degenerate, and Δθ is common to the setup, so it is determined once from all transitions. The result with ΔE fixed is reported too, because the ratio of the two uncertainties shows how much the angular coverage costs.
5. Calibration (`calibrate`, `dbeta_dt`). Relate Δβ_true to τ with a simulation analysed in the same way, with transitions of known lifetime, or both. Fit slope and intercept, with priors on the slope from the stopping-power uncertainty and on the intercept from the ejectile energy calibration, and compare with dβ/dt = c m²/E³ · dE/dx.
6. Lifetimes and sensitivity. τ follows from the calibration; the 15O paper used a Bayesian linear fit with literature priors (emcee). For a feasibility study, `lifetime_sensitivity` scales the fitted Δβ error as 1/√N.

## Lessons that change results (validated)

The centroid is not the mean. The Gaussian-core centroid of an exponentially tailed Δβ distribution is about 0.6–0.7 of its mean: 0.60 in a synthetic test and 0.66 against dβ/dt in the AGATA simulation of 27Si. The slope must therefore be calibrated with the same estimator, and dβ/dt is a cross-check, not the calibration. Near τ → 0 the centroid is not strictly proportional to τ, so the intercept is kept free.

Edge windows bias the fit. Angular smearing moves events across the acceptance edges asymmetrically, which shifts the edge centroids by about 10⁻³; with ΔE free this propagates into Δβ_true. `dbeta_windows` drops the first and last window by default, and the residuals near ring gaps deserve a look as well.

Backward-only arrays correlate ΔE with Δβ_true. With gamma angles only at 110°–170° (Fougères 2023; the AGATA LNL 2022 configuration) the correlation is strong: in the 27Si study the Δβ error grew by a factor 5, from 0.3 to 1.4 ×10⁻⁴, when ΔE was freed. Coverage around 90°, 40°–160° in the 15O run, separates them; otherwise ΔE is constrained with the energy calibration, from lines of stopped nuclei or sources.

Mean estimators are fragile. A cos²-weighted mean of β_ems/β_reac was biased by 3 % in the 27Si simulation because of the tails, while median and Gaussian-core centroids were unbiased, as validated on a run without stopping.

The backing thickness sets the linear range, because the recoil must still be in the stopper when it decays. With 1 µm Au a 27Si recoil (β ≈ 0.095) leaves after about 35 fs, and Δβ saturates above about 30 fs; with 5 µm it keeps growing to at least 100 fs. Check with the transit time, about thickness/(β c).

A no-stopping reference validates the analysis: a thin target without backing, or τ → 0. Δβ_true and ΔE must be zero within errors before any lifetime is quoted.

Feeding is avoided by using transitions without side feeding, or by taking the Δβ difference between feeding and fed transitions in coincidence, where the common β_reac cancels.

Geant4 takes lifetimes from G4ENSDFSTATE (mean life, ns), not from PhotonEvaporation. For τ scans, override them with a private ENSDFSTATE copy (`G4ENSDFSTATEDATA`), as described in the `agata-simulation` skill and the 28Si project.

## What to deliver

- The Δβ(θ) plot with the fit and the ΔE-fixed line.
- Δβ distributions for several τ.
- The calibration plot with the linear range and the full range, fits drawn across the axis.
- A table of Δβ_true, ΔE, χ²/ndf, N and σ_τ.

Plots follow the `prc-figures` skill.
