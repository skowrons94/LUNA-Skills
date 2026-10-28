# Is the fit physical? Saturated levels, transformability, honest uncertainties

A good χ² does not make a level scheme physical. In the Brune parameterization the fitted (observed) widths
look ordinary even when a level has stopped being a compound-nucleus level. These checks come from the ⁷Be
evaluation (2026); the numbers quoted are from it.

## Park norm: find saturated levels

The observed reduced widths of a level are its formal ones times one factor,
J = 1 / (1 + Σ_c γ_c² dS_c/dE)  (T.-S. Park, PRC 104, 064612 (2021)).
- `scripts/park_norms.py model.azr param.sav` prints J for every unbound level from pyazr alone
  (J = theta2 / theta2_formal of `dimensionless_widths`, identical across the level's channels; it includes a
  hybrid exterior if the model has one).
- 1 − J is the share of the state outside the channel radius exactly for a bound state (Thomas normalization),
  and by analogy for a resonance. State it as an analogy in a paper.
- J well below 0.5 marks a saturated level. ⁷Be: a newly opened p+⁶Li(3⁺) channel of a 7/2⁻ took J from
  0.91 to 0.05 and moved its conventional pole from 9.3 to 120 MeV, with Brune widths θ² = 0.99 and 0.45 TW
  that looked unremarkable. A broad 5/2⁻ had J = 0.03–0.18 in every fit, including a published one.
- Background poles (far-away levels) are exempt; say so.

## Bounding J in a fit

- Add a penalty J ≥ J_min for every level below the background poles (not only the one you noticed: bounding
  two levels pushed a third to J = 0.49). ⁷Be adopted J_min = 0.5; J_min = 0.3 was the sensitivity variant
  (+0.7 % in S(0)).
- **The penalty must be stiff.** At J ≈ 0.05, J is nearly flat in the widths, so a soft penalty (weight 2000 on
  the residual) at J_min = 0.3 left the saturated solution as a local minimum (χ² unchanged); weight 1e6 moved
  every bounded level onto the bound.
- dS/dE: from the Coulomb functions (in the ⁷Be study `getCoulomb_PSdSW(..., True)` of Ferdinand; the
  `False` flag silently returns dS = 0 and made every J equal to 1). Check against finite differences.
- Report the cost. ⁷Be: Δχ² +83 on the fit without the new channel, +132 with it; the channel kept −270 of
  its −319.
- A level that sits on the bound has a width set by the bound, not by the data: do not quote its agreement
  with a structure prediction as independent evidence.

## Transformability to the conventional (ENDF) form

- Conventional poles from the Brune parameters: generalized eigenproblem of the level matrix; penalize
  |D| > 300 MeV and λ_max(K) > 0.7 (soft). AZURE2 prints "Denominator less than zero while transforming ...
  may not have been successful" for a level whose transformation fails: treat it as a finding, not noise.

## Covariance: check it, do not trust it

- The J^T J covariance (data + normalization priors) is wrong when the problem is near-singular. ⁷Be:
  cond(J^T J) = 5.6e15 with two saturated levels; the quoted θ²α of the 1/2⁺ was ±52 % while a profile scan
  (fix the width ±20 %, refit everything else) showed ±4.8 %: 11× too wide. After the J bound,
  cond = 2.8e9 and covariance and profile agree (4.2 % vs 4.5 %).
- Always profile the one or two parameters the paper's argument rests on.
- A covariance computed from the data rows only ignores active penalty bounds; say so when levels sit on a
  bound.

## Adding a channel a structure model predicts

- Open the channel, refit, and report where the gain sits (per dataset, per energy bin). ⁷Be: −319 almost
  entirely at the top edge of the data (E_cm 7–8 MeV, one elastic set and the analyzing powers): a real but
  edge-dominated gain.
- Then check J of the level and bound it if needed; compare the fitted width with the prediction at the
  fitted energy (the prediction moves with the energy).
- Degenerate channel spins add nothing (only their summed flux is observed); keep one.

## Practicalities that cost hours

- `level.set_active(False)` in pyazr leaves the level's rows in the .azr; a parameter/row pairing by position
  then misaligns every later group. Remove a pole by zeroing and fixing its widths and energy instead.
- Parallel runs: give every run its own output directory and unique temporary file names (two runs with the
  same tag in different folders deleted each other's temp .azr).
- A driver that skips tags with an existing result relaunches a run that is still going: check running
  processes before restarting a driver.
- `least_squares` with xtol = ftol = gtol = 1e-12 and fixed outer rounds wastes most of the time; 1e-9 and
  stopping the outer loop when χ² changes by < 0.01 reproduced the nominal χ² to 0.01.
- Fixing an observed width while its level energy moves re-reads it at the new energy: quote such variants
  with care.
- A free refit can stop in a local minimum (⁷Li mirror test: 10053 vs 8167 for the identical model from
  another start). Compare against the lowest minimum of the identical model and say so.
- Load on a shared machine: `pgrep`/load averages first; many-process runs slow by an order of magnitude.

## Interpreting an "internal" amplitude

The R-matrix splits capture at the channel radius. Microscopic calculations of ³He(α,γ)⁷Be find the low-energy
capture predominantly external (5–25 fm; Kajino NPA 460, 559 (1986); Walliser et al. NPA 419, 133 (1984)).
An "internal" amplitude in an R-matrix fit is a statement at the chosen radius, and part of it corrects the
external wave for the true s-wave phase (a broad 1/2⁺ level turns the 4.7 fm hard-sphere phase into the
measured ~3.3 fm one: `effective-range`). Do not write that the reaction "requires an internal amplitude" without
that qualifier.
