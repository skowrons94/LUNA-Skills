---
name: effective-range
description: Extract and compare the scattering length a0, effective range r0 and shape parameter of a charged-particle s wave with the Coulomb-modified effective-range expansion, from measured phase shifts, R-matrix eigenphases (AZURE2 phase-shift grids) or a cluster or microscopic model, and the theta^2 a single 1/2+ level at E_lambda needs for a given a0. Use when a task quotes or compares a0 and r0 (halo EFT, 3He+alpha, t+alpha, p+alpha, alpha+alpha), asks whether a large R-matrix width above the single-particle limit is physical, or needs a model-independent comparison of two s waves; these must be computed, not estimated from memory.
---
# Effective-range analysis of a charged-particle s wave

A reduced width depends on the parameterization, whereas the scattering length and the effective range do not: they are properties of the phase shift near threshold. They are therefore the quantities to quote when an R-matrix fit, a model and halo-EFT analyses are compared on the same footing. This skill fits the Coulomb-modified effective-range expansion to an s-wave phase and translates a scattering length into the R-matrix parameters of one level, i.e. the θ² that a single 1/2+ level at E_λ needs to reproduce a given a0, and explains why that θ² can exceed the single-particle limit. You need the phase shift on a fine grid from threshold, from data, an R-matrix fit or a model. You get a0, r0 and the shape parameter P with the fit window, order, number of points and rms of the K fit, and, where asked, the θ² curve against a0.

## Where this fits

- Comes from: published phase-shift analyses; R-matrix eigenphases from `r-matrix` phase-shift extrapolation grids; phases of a potential from `cluster-potential` or of an antisymmetrized model from `microscopic-cluster`; the mirror s waves of `mirror-nucleus`.
- Goes to: `cluster-potential`, `microscopic-cluster` and `mirror-nucleus`, which compare their s waves through a0 and r0, and the interpretation of a large width in an `r-matrix` fit. Widths, ANCs and the R-matrix quantities of a potential are computed in `cluster-potential`.
- Checked by: `scripts/selftest.py` (must print PASS) and the validation ladder in [validation.md](references/validation.md).

Formulas, conventions and the one-level relation are in [method.md](references/method.md); the validation and the lessons that changed results are in [validation.md](references/validation.md).

## Rules and their reasons

1. The fit uses the Coulomb-modified function K(E), not k cot δ, because for charged particles the plain expansion has no finite-range limit.
2. Fit range and order are part of the result, so the energy window and the number of terms are quoted with every a0. On the same 7Be phases, 0.20–2.00 MeV with three terms gives a0 = 39.7 fm, and 0.30–4.02 MeV gives 35.5 fm. A two-term fit over a long window is biased (self-test: 40 → 55 fm). Numbers are compared only when they come from the same recipe.
3. The window stays below the next threshold, because above it the eigenphase is not a single-channel phase shift (3He+alpha: E_cm < 4.02 MeV, the p+6Li threshold).
4. Phases are referenced to threshold and unwrapped. K is insensitive to δ → δ + π, but a curve with a jump is not, and the referencing hides forbidden-state offsets.
5. A large a0 is first compared with a charged hard sphere, because with Coulomb a scattering length of tens of fm needs no attraction and no near-threshold pole. For 3He+alpha a hard sphere of 3.3 fm gives a0 = 36.1 fm and r0 = 1.053 fm (`ere_hard_sphere`), the values of the 7Be fit, and the equivalent radius of a phase (`core_radius`) tells whether the s wave is one hard sphere at all energies or a core that shrinks with energy, as a Pauli core does. In a one-level R-matrix the level that reproduces a0 sits several MeV up and needs θ² of order one (`theta2_for_a0`), since it supplies the difference between a hard sphere of the channel radius and the actual core. The report says that the width encodes the scattering length and does not call it a spectroscopic factor.
6. Published ranges are not one measurement. Halo-EFT analyses of 3He+alpha give a0 = 22–60 fm from different data selections, so the spread and the sources are quoted, not an average.

## Method

1. Get the phase on a fine grid from threshold to the window edge; in AZURE2 this is a phase-shift test segment per J, L, as described in `r-matrix`. Unwrap and reference it (`unwrap_from_threshold`).
2. Fit `fit_ere(pair, E, δ, emin, emax, order=2)`. Repeat with a second window and order and report the spread, which measures how much the number depends on the recipe.
3. Compare with published (a0, r0) using the same window, or convert theirs to a phase band with `delta_from_ere` and compare phases.
4. To connect to an R-matrix level, run `theta2_for_a0(pair, E_lam, a0, a)` over the measured a0 range at the channel radius of the fit, and place the fitted level on that curve. The radius must be passed through to the Wigner unit as well as to the penetrability and shift: a script that converted θ² with γ_W² fixed at 4.70 fm returned widths 7 % low for a fit at 4.87 fm, and nothing in its output showed it.
5. Record window, order, number of points and rms of the K fit with every number.

## Scripts

The scripts are Python with numpy, scipy and mpmath. Replace SKILL_DIR with this skill's directory.

```bash
python3 SKILL_DIR/scripts/selftest.py      # must print PASS (synthetic recovery, n*pi invariance, fit-range trap, 7Be one-level theta^2, hard sphere)
```
```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts"); import ere
pair = ere.Pair("alpha", "3He")
E, d = ere.unwrap_from_threshold(E_raw, delta_raw_deg)
fit  = ere.fit_ere(pair, E, d, 0.20, 2.00, order=2)            # a0, r0, P, rms, npts
t2   = ere.theta2_for_a0(pair, E_lam=6.80, a0_target=40.0, a=4.7) # 1.548
hs   = ere.ere_hard_sphere(pair, R=3.3)                           # a0 36.1 fm, r0 1.053 fm
Rc   = ere.core_radius(pair, 1.0, -9.0)                           # 3.2 fm
```

## What to deliver

- a0, r0 and P with the window, order, number of points and rms of the K fit.
- The same quantities from a second window and order, as the recipe systematic.
- For a width question, the θ² curve against a0 at the channel radius of the fit, with the fitted level placed on it.
- For a large a0, the hard-sphere radius that reproduces it and the equivalent core radius at a few energies.
