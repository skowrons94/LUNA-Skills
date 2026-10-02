---
name: delta-beta-dsam
description: Measure or simulate femtosecond nuclear lifetimes with the Doppler-velocity DSAM (Delta-beta) method — beta at the reaction from the detected ejectile (energy + angle, energy-loss corrected) minus beta at gamma emission from the Doppler shift, Delta-beta(theta) centroids in angular windows with energy/angle-offset nuisance fit, and a Delta-beta vs tau calibration (simulation, known lifetimes, d beta/dt from stopping powers). Use for AGATA/GRETA/HPGe lifetime analyses with a silicon ejectile detector, implanted or gas targets, inverse-kinematics transfer reactions, DSAM feasibility studies and lifetime sensitivity estimates, Bayesian Delta-beta–tau fits, or whenever someone mentions delta beta, beta_reac/beta_ems, Doppler-shift attenuation with ejectile tagging, or the 15O/22Na/27Si lifetime analyses.
---
# Doppler-velocity DSAM (Δβ) analysis

The excited recoil slows down in the backing; a longer lifetime means a smaller Doppler shift.
Δβ = β_reac − β_ems is measured event by event and, for τ up to a few tens of fs, is linear in τ:
Δβ ≈ (dβ/dt)·τ. References: Fougères et al., Nature Commun. 14, 4536 (2023); the 15O AGATA
lifetime paper (J. Skowronski et al., submitted 2026; analysis code github.com/skowrons94/15O_Lifetime);
worked simulation study: `~/Desktop/28Si` (scripts/analyse_agata.py, report Sect. 6).

Library: `scripts/dbeta.py` (import it; numpy + scipy). Run `python3 scripts/selftest.py` first: it
checks the inversion, unbiasedness without stopping, linearity in τ and recovery of an energy offset
on synthetic data. Formulas, systematics and the uncertainty budget: [references/method.md](references/method.md).

## Workflow

1. **β_reac from the ejectile** (`recoil_from_ejectile`). Correct the measured ejectile energy for
   the losses in the backing, target remainder, foils and detector dead layers (`energy_before` with
   SRIM or Geant4 dE/dx), placing the reaction at the mid-depth of the implanted/active layer. Use
   energy *and* angle (momentum conservation); the recoil direction is p_beam − p_ejectile.
   Correct the beam energy for its loss to the reaction depth.
2. **Check the kinematics**: reconstruct E_x by missing mass for every event. Its centroid must sit at
   the level energy (the 15O analysis: within 12 keV; this bounds coherent β_reac biases, since
   energy-scale errors shift β_reac and E_x together). Gate on E_x to reject punch-through and
   mis-identified ejectiles. E_x resolution is usually far too poor to separate neighbouring states:
   select the state with the γ line (and γγ gates on secondaries).
3. **β_ems** (`beta_ems`): invert E_obs = E0 √(1−β²)/(1−β cos θ) with θ the angle between the γ ray
   (first or main interaction point after PSA) and the reconstructed recoil. Choose the root closest
   to β_reac. Select events with `doppler_window` (between fully shifted and unshifted energies ±
   resolution) and, if needed, a Doppler-corrected-energy window.
4. **Δβ(θ)** (`dbeta_windows`, `fit_dbeta_theta`): 7° windows of θ, Gaussian-core centroid per window,
   bootstrap errors; fit Δβ(θ) = Δβ_true + distortion(θ; ΔE, Δθ) with ΔE free and Δθ fixed (the two
   are degenerate; Δθ is common to the setup, determined once from all transitions). Always report the
   ΔE-fixed result too: the ratio of the two uncertainties shows how much the angular coverage costs.
5. **Calibration** (`calibrate`, `dbeta_dt`): Δβ_true vs τ. Use a simulation with the same analysis
   and/or transitions of known lifetime; fit slope and intercept (priors: slope from the stopping-power
   uncertainty, intercept from the ejectile energy calibration). Compare with dβ/dt = c m²/E³ · dE/dx.
6. **Lifetimes / sensitivity**: τ from the calibration (Bayesian linear fit with literature priors in
   the 15O paper, emcee); for feasibility, `lifetime_sensitivity` scales the fitted Δβ error as 1/√N.

## Lessons that change results (validated)

- **Centroid ≠ mean.** The Gaussian-core centroid of an exponentially tailed Δβ distribution is ≈0.6–0.7
  of its mean (synthetic test 0.60; AGATA simulation of 27Si 0.66 against dβ/dt). The slope must be
  calibrated with the *same* estimator; dβ/dt is a cross-check, not the calibration. Near τ → 0 the
  centroid is not strictly proportional: keep the intercept free.
- **Edge windows bias the fit.** Angular smearing moves events across the acceptance edges
  asymmetrically (edge centroids off by 10⁻³); with ΔE free this propagates into Δβ_true.
  `dbeta_windows` drops the first and last window by default; also look at residuals near ring gaps.
- **Backward-only arrays.** With γ angles only at 110°–170° (Fougères 2023; AGATA LNL 2022
  configuration), ΔE and Δβ_true are strongly correlated: for the 27Si study the Δβ error grew ×5
  (0.3 → 1.4 ×10⁻⁴) when ΔE was freed. Coverage around 90° (40°–160° in the 15O run) separates them;
  otherwise constrain ΔE with the energy calibration (lines from stopped nuclei, sources).
- **Mean estimators are fragile.** A cos²-weighted mean of β_ems/β_reac was biased by 3 % in the 27Si
  simulation (tails); median or Gaussian-core centroids were unbiased (validated on a no-stopping run).
- **Backing thickness sets the linear range.** The recoil must still be in the stopper when it decays:
  with 1 µm Au a 27Si recoil (β ≈ 0.095) leaves after ≈35 fs and Δβ saturates above ≈30 fs; 5 µm keeps
  it growing to ≥100 fs. Check with transit time ≈ thickness/(β c).
- **Validate on a no-stopping reference** (thin target, no backing, or τ → 0): Δβ_true and ΔE must be
  zero within errors before quoting any lifetime.
- **Feeding**: use transitions without side feeding, or take the Δβ difference between feeding and fed
  transitions in coincidence (common β_reac cancels).
- **Geant4 lifetimes** come from G4ENSDFSTATE (mean life, ns), not from PhotonEvaporation; override with
  a private ENSDFSTATE copy (`G4ENSDFSTATEDATA`) for τ scans (see agata-simulation skill, 28Si project).

## Outputs to produce

Δβ(θ) plot with fit (and ΔE-fixed line), Δβ distributions for several τ, calibration plot with the
linear range and the full range (fits drawn across the axis), table of Δβ_true, ΔE, χ²/ndf, N and σ_τ.
Use the prc-figures skill for plots.
