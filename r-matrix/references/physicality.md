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
- A shell loop that waits with `until ! pgrep -f "<pattern>"` never ends when the pattern also appears in the
  loop's own command line, because `pgrep -f` then finds the loop itself. Wait on the run's final log line
  ("wrote ...") or on a recorded process id instead.
- When the channel radius changes, every hard-coded radius in the helper scripts must change with it, because
  a θ² ↔ Γ conversion uses the Wigner width γ_W² = ħ²/μa² at one radius. A one-level script that kept
  γ_W² at 4.70 fm while the fit moved to 4.87 fm returned θ² 7 % low; search the scripts for the old radius
  (`grep -n "4\.70"`) before quoting widths at a new one.
- A comparison script that finds "the same level" in a new fit by an energy window drops a level silently once a
  refit moves it out of the window. In the ⁷Be comparison with the shell model the windows were ±1.5 MeV around
  the old nominal's energies; at a = 5.07 fm the 3/2⁺ had moved 1.53 MeV and vanished from the table without a
  warning. After every change of radius or model, count the rows of such a comparison against the previous one,
  and make the script report the levels it could not match.
- Plotting and table scripts that read a fit's `output/` folder (chiSquared.out, the .out segment files) fail on
  a new fit until that folder exists. A model rebuilt from a parameter vector has no outputs until they are
  written (`write_outputs.py <azr> <sav>` in the ⁷Be project); put that step at the top of the product chain,
  not after the plots, and check that its χ² equals the fit's before anything else runs.

## Model choices: test "add" as well as "replace", and distrust a fixed variant that wins

A variant with a parameter held fixed can never fit better than the same model with that parameter free, if the free fit has converged. When the fixed variant wins, the free fit has stopped in a different minimum, and it should be restarted from the fixed solution (pyazr refit scripts can take a start vector from a previous run). In the ⁷Be evaluation (a = 4.87 fm) the second 1/2⁺ term, started at 12.5 MeV with its energy free, ran to about 480 MeV and gained Δχ² = −14, while the same term held at 12.5 MeV gained −42. Freed from the fixed solution, it stayed at 12.45 MeV with −42, so both minima were real and the free fit had simply missed the better one.

A "replace" test answers a narrower question than it seems to. The 12.5 MeV variant had removed the 30 MeV α background pole, and the new term carried almost no α width: it was a proton level, not a relocated background. Keeping the pole and adding the proton level gave Δχ² = −134 for four parameters and moved S(0) by −2.5 %, which made it the nominal model. Before a better-fitting alternative is booked as a systematic error, we therefore check whether it describes different physics and test it added to the nominal model as well as in its place. A variant that fits better than the nominal by more than the information-criterion charge is a new nominal, not an uncertainty.

A removal test is only valid if no other free term can take the removed level's place. In the ⁷Be evaluation at a = 5.07 fm the model had a second, free 1/2⁺ level at 12.5 MeV. Removing the main 1/2⁺ level (all widths zeroed) cost Δχ² = +947, and removing only its proton widths +638. Both numbers went into the Letter. A per-dataset breakdown made later showed that only 0.2 % of the first cost fell on the ⁶Li(p,α) data, and that is what gave the test away. The 12.5 MeV level had moved down to 7.0–7.3 MeV and taken over the α width (and, in the second test, the proton widths) of the removed level. The tests had measured the loss of one term, not of the level. Removing every 1/2⁺ level below the background pole gave +3590, and removing the proton widths of both gave +2086, with 70 % of the cost on the (p,α) and (α,p) data, the physical picture the earlier numbers only appeared to show. After every removal or constrained test, we list where each remaining level of the same Jπ ended up before quoting the cost. Two levels that trade places are one term from the data's point of view.

The same check applies to removal tests, which are nested: removing all widths of a level is a special case of removing only its proton widths, so the second refit can never end worse than the first. In the ⁷Be evaluation it did (+2170 against +1036), because the proton-only removal had stopped in a poorer minimum. We restart the less constrained test from the solution of the more constrained one, which guarantees the ordering, and quote a removal cost only after this check.

A test that holds one width at a structure-model value is a constrained refit, and it lands in whichever minimum is nearest its start. In the ⁷Be evaluation we held the 1/2⁺ α width at three shell-model values (θ² = 0.074, 0.176 and 0.296 Teichmann–Wigner units), each started from the nominal fit. The costs came out as Δχ² = +896, +2570 (stopped at χ² 7546 and killed) and +911. A larger allowed width cannot cost more than a smaller one when both are near the same solution, so this non-monotonic sequence already showed that the starts were the problem, not the physics. Restarting each test from the best neighbouring solution gave +870, +796 and +768, a smooth sequence, and a third start of the middle value returned the same minimum to 0.2. In all of them the held level moved up to 10 MeV as a proton level, and the free 12.5 MeV level moved down to 7 MeV and took the large α width. We now scan a fixed parameter over at least three values, restart each from its neighbours until the costs vary smoothly, and quote the lowest minimum together with where the freed strength went.

## The exterior potential and the channel radius trade against each other

Carrying a nuclear potential outside the channel radius (AZURE2 hybrid exterior) and moving the radius outward are two ways of describing the same nuclear tail, so their effects must be judged together. In the ⁷Be fit the cluster-model tail at 4.87 fm is still −2.8 MeV against +1.2 MeV Coulomb. There the potential improved the fit by Δχ² ≈ −200 and brought the 1/2⁺ α width from 1.29 to 0.83 of the Teichmann–Wigner limit. At 5.07 fm, near the χ² minimum of a radius scan, the same potential was worth only −14, and a pure-Coulomb fit gave 0.97 of the limit, while its 30 MeV background pole took up a large α width instead. What an analysis calls "level" and what it calls "continuum" thus depends on where the boundary is drawn. A statement such as "the width is below the single-state limit once the exterior potential is included" holds at one radius and should be quoted with that radius, together with the radius scan of both versions of the model. The energy of a broad level moves with the radius too (7.6 to 6.7 MeV for the ⁷Be 1/2⁺ between 4.83 and 5.25 fm), so its fit uncertainty at fixed radius understates what is known about it.

## Interpreting an "internal" amplitude

The R-matrix splits capture at the channel radius. Microscopic calculations of ³He(α,γ)⁷Be find the low-energy
capture predominantly external (5–25 fm; Kajino NPA 460, 559 (1986); Walliser et al. NPA 419, 133 (1984)).
An "internal" amplitude in an R-matrix fit is a statement at the chosen radius, and part of it corrects the
external wave for the true s-wave phase (a broad 1/2⁺ level turns the 4.7 fm hard-sphere phase into the
measured ~3.3 fm one: `effective-range`). Do not write that the reaction "requires an internal amplitude" without
that qualifier.
