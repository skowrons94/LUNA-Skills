# Standard analyses

`scripts/counting.py` implements the formulas below (standard library only); `python3 counting.py` runs its self-test.

## Efficiency

- Absolute efficiency ε = N_det / N_gen per source particle (or Σw_det / Σw_gen). Binomial uncertainty √(ε(1 − ε)/N_gen); for small counts or ε near 0 or 1 quote the Wilson interval. Weighted events: Var(ε) = [(1 − ε)² Σ_det w² + ε² Σ_fail w²] / (Σ_gen w)², which reduces to ε(1 − ε)/N for unit weights; √Σw²_det / Σw_gen is its small-ε limit (the template writes `sum_weights2` for this).
- Name the definition: captures, counts above threshold, coincidences, full-energy peak. Intrinsic efficiency (per particle entering the detector) is a different number; do not mix them.
- Choose the number of events from the target precision: σ_ε/ε = √((1 − ε)/(ε N)), so ε = 0.2 at 1 % needs N ≈ 4 × 10⁴.
- Merge batches by summing counts and weights, never by averaging ratios of unequal batches.

## Efficiency against energy and flatness

- Run monoenergetic points over the source energy range (logarithmic spacing for neutrons: thermal, keV, 0.1–10 MeV) with the same geometry and seeds policy; one summary per energy.
- Flatness: max/min ratio and relative spread over the range of interest, and χ² of the constant hypothesis with the statistical errors (a flat-looking curve with χ²/ndf ≫ 1 is not flat at that precision). For a ring counter the inner/outer ring ratio is a useful energy indicator.
- The efficiency for a spectrum is ∫ε(E)φ(E)dE / ∫φ(E)dE. Fold the monoenergetic curve with the spectrum and compare with a direct simulation of the spectrum once; the difference tests the energy grid.
- Report the sensitivity of the curve to moderator density, gas pressure, threshold and physics list; these are usually larger than the statistics.

## Die-away and time gates

- After a short thermalisation time, the capture-time distribution of a moderated counter is close to exponential with the die-away time τ. Fit it with the truncated maximum-likelihood estimator on [t_min, t_max] (`counting.py dieaway`); vary t_min to show that the early non-exponential part is excluded, and say if two components (moderator and shell, or inner and outer rings) are needed.
- Fraction of correlated captures in a gate [t₁, t₂] after the trigger: exp(−t₁/τ) − exp(−t₂/τ) for a single exponential; use the simulated distribution directly when it is not exponential.
- A pre-delay removes early correlated pulses and electronic ringing at the cost of correlated counts; the gate length trades signal against accidentals.

## Dead time, pile-up and accidentals from rates

- Non-paralyzable dead time τ: measured rate m = n/(1 + nτ), true rate n = m/(1 − mτ). Paralyzable: m = n exp(−nτ), maximum 1/(eτ); invert on the low-rate branch. Real systems are often in between; bracket the correction with both models.
- Pile-up probability within a resolving time τ_r at rate R: 1 − exp(−Rτ_r) ≈ Rτ_r for a following pulse within τ_r; for another pulse within ±τ_r use 1 − exp(−2Rτ_r). State the convention.
- Accidental counts in a gate of length G opened by each trigger: R·G per trigger; accidental coincidence rate between two channels: 2R₁R₂τ_c for a coincidence window ±τ_c (state the window convention).
- Use the rates expected in the measurement (signal, beam-induced and room background) and state which channel or system the dead time applies to (per tube, per preamplifier group, whole DAQ).

## Uncertainties

Separate statistical uncertainty (from the event counts) from model uncertainties (physics list, thermal scattering, cross-section data, geometry and material tolerances, threshold and resolution). Quote each with how it was obtained (variation run, comparison with data).
