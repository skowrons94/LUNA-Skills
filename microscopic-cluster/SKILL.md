---
name: microscopic-cluster
description: Run antisymmetrized microscopic two-cluster calculations of light nuclei (RGM/GCM with Brink 0s clusters — n, p, d, t, 3He, alpha — the Minnesota nucleon-nucleon force and the microscopic R-matrix of Baye et al.) for bound states, phase shifts and scattering lengths with no parameter fitted to the quantity tested; fix the exchange parameter u on one datum of the other parity, scan the oscillator width, check norm-kernel eigenvalues, channel-radius and Pauli-cutoff stability, and compare with R-matrix eigenphases or effective-range parameters. Use when a task asks what an antisymmetrized calculation predicts for a cluster phase shift, scattering length, effective range or level, whether a large R-matrix width can come from the cluster continuum, or for a parameter-free test of a cluster potential; such predictions must be computed, not estimated from memory.
---
# Microscopic two-cluster calculations (GCM / RGM)

A local cluster potential cannot see exchange, so antisymmetrize everything. The calculation is small: two 0s clusters, a central force with one exchange parameter, and an R-matrix at the surface. That is enough to predict the other parity with nothing adjusted. Its value is the prediction: keep the adjusted quantities few and on the other side of the comparison.

## Route the task

- **Local two-body potential** (fast, node counting, ANCs, widths): `cluster-potential`. Do it first; this skill tests it.
- **a0, r0 from the phase shifts**: `effective-range` (same recipe for model, fit and data).
- **Intruder states with a nucleon outside a core** (6Li ⊗ sd): `shell-model`. This model contains only the cluster partition.
- **The R-matrix fit to compare with**: `azure2` (eigenphases from phase-shift grids).
- Everything else: model, numerics, conventions in [method.md](references/method.md); checks and lessons in [validation.md](references/validation.md).

## Non-negotiable boundaries

1. **Adjust one quantity, on the other parity.** The Minnesota exchange parameter u is fixed on a negative-parity bound state or resonance. Everything in positive parity is then a prediction, and stated as such. If u is fitted to the quantity you compare with, the comparison proves nothing.
2. **Scan what is not fixed by physics.** Repeat with at least three oscillator widths b and both choices of the u datum. Quote the spread, not one curve.
3. **Say what the model does not contain.** 0s clusters (³He is underbound: −3.3 MeV against −7.7 MeV), no spin-orbit force (J = l ± s degenerate), one partition (no p+⁶Li, no cluster distortion). Compare only below the next threshold.
4. **The threshold is the model's own.** Energies are relative to the sum of the model's cluster energies (`build_kernels` returns it), not the experimental threshold.
5. **Pauli-forbidden directions are removed numerically.** Check that the phases do not move when the norm-kernel cutoff eps (1e-6 vs 1e-7) and the channel radius (7–9 fm) change.
6. **Do not draw conclusions about states this model cannot contain.** A missing resonance in a cluster-only calculation says the cluster continuum has none. It says nothing about a state built on another partition.

## Working method

1. `gcm.configure(c1, c2)`; `selftest.py` must pass. For a new system, check the small-R norm kernel against mu_N (`check_structure`, nmin = N_min of the system).
2. Build kernels on a generator grid (0.8–12 fm, step 0.8) for the waves needed: `K, Ethr = build_kernels(Rs, ls, b)`. Kernels are linear in u: `H_of(K, l, u)`.
3. Fix u on one datum of the other parity: `fit_u_bound` for a bound centroid, or the 90° crossing of a resonance.
4. Phases: `phase_curve(rmatrix(K, Ethr, Rs, b, l, u), Es)` in degrees, referenced to threshold. ERE through `effective-range`.
5. Repeat over b and the u datum. Record u, the model threshold, a0, r0 and rms differences from the fit's eigenphases in a `results.json`.

## Scripts (Python with numpy, scipy, mpmath)

```bash
python3 SKILL_DIR/scripts/selftest.py          # must print PASS (mu_3, mu_4, large-R limit, E_alpha)
python3 SKILL_DIR/scripts/selftest.py --full   # + end to end: u = 0.9809, a0 = 40.6 fm (minutes)
```
```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts"); import gcm, numpy as np
gcm.configure("alpha", "3He")
Rs = np.round(np.arange(0.8, 12.01, 0.8), 3)
K, Et = gcm.build_kernels(Rs, [0, 1, 2, 3], b=1.36)
u  = gcm.fit_u_bound(K, Et, l=1, Etarget=-1.444)                 # p-wave bound-state centroid
d0 = gcm.phase_curve(gcm.rmatrix(K, Et, Rs, 1.36, 0, u), np.linspace(0.05, 4.0, 80))
```
