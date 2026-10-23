---
name: effective-range
description: Extract and compare the low-energy scattering length a0, effective range r0 and shape parameter of a charged-particle s wave with the Coulomb-modified effective-range expansion — from measured phase shifts, from R-matrix eigenphases (AZURE2 phase-shift grids), or from a cluster or microscopic model — and translate between a scattering length and the R-matrix parameters of one level (the theta^2 a single 1/2+ level at E_lambda needs to reproduce a given a0, and why that can exceed the single-particle limit). Use when a task quotes or compares a0 and r0 (halo EFT analyses, 3He+alpha, t+alpha, p+alpha, alpha+alpha), asks whether a large R-matrix width is physical, or needs a model-independent comparison of two s waves; these must be computed, not estimated from memory.
---
# Effective-range analysis of a charged-particle s wave

A reduced width depends on the parameterization. The scattering length and effective range do not: they are properties of the phase shift near threshold. Quote them to compare an R-matrix fit, a model and halo-EFT analyses on the same footing.

## Route the task

- **The phase shift itself**: from data (published phase-shift analyses), from an R-matrix fit (`azure2`: phase-shift extrapolation grids, i.e. eigenphases), from a potential (`cluster-potential`) or from an antisymmetrized model (`microscopic-cluster`).
- **Widths, ANCs, R-matrix quantities of a potential**: `cluster-potential`.
- Everything else, the expansion and its use:
  - formulas, conventions, the one-level relation: [method.md](references/method.md);
  - validation and the lessons that changed results: [validation.md](references/validation.md).

## Non-negotiable boundaries

1. **Use the Coulomb-modified function K(E)**, not k cot δ. For charged particles the plain expansion has no finite-range limit.
2. **Fit range and order are part of the result.** Quote the energy window and the number of terms with every a0. On the same 7Be phases, 0.20–2.00 MeV with three terms gives a0 = 39.7 fm, and 0.30–4.02 MeV gives 35.5 fm. A two-term fit over a long window is biased (self-test: 40 → 55 fm). Compare numbers only when they come from the same recipe.
3. **Stay below the next threshold.** Above it the eigenphase is not a single-channel phase shift (3He+alpha: E_cm < 4.02 MeV, the p+6Li threshold).
4. **Reference phases to threshold and unwrap.** K is insensitive to δ → δ + π, but a curve with a jump is not, and the referencing hides forbidden-state offsets.
5. **A large a0 is a near-threshold pole of the S matrix, not a hidden resonance.** In a one-level R-matrix the level that reproduces it sits several MeV up and needs θ² of order one or more (`theta2_for_a0`). Say that the width encodes the scattering length; do not call it a spectroscopic factor.
6. **Published ranges are not one measurement.** Halo-EFT analyses of 3He+alpha give a0 = 22–60 fm from different data selections. Quote the spread and the sources, not an average.

## Working method

1. Get the phase on a fine grid from threshold to the window edge (AZURE2: a phase-shift test segment per J, L; see `azure2`). Unwrap and reference it (`unwrap_from_threshold`).
2. Fit `fit_ere(pair, E, δ, emin, emax, order=2)`. Repeat with a second window and order and report the spread.
3. Compare with published (a0, r0) using the same window, or convert theirs to a phase band with `delta_from_ere` and compare phases.
4. To connect to an R-matrix level, run `theta2_for_a0(pair, E_lam, a0, a)` over the measured a0 range at the fit's channel radius. Place the fitted level on that curve.
5. Record window, order, number of points and rms of the K fit with every number.

## Scripts (Python with numpy, scipy, mpmath)

```bash
python3 SKILL_DIR/scripts/selftest.py      # must print PASS (synthetic recovery, n*pi invariance, fit-range trap, 7Be one-level theta^2)
```
```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts"); import ere
pair = ere.Pair("alpha", "3He")
E, d = ere.unwrap_from_threshold(E_raw, delta_raw_deg)
fit  = ere.fit_ere(pair, E, d, 0.20, 2.00, order=2)            # a0, r0, P, rms, npts
t2   = ere.theta2_for_a0(pair, E_lam=6.80, a0_target=40.0, a=4.7) # 1.548
```
