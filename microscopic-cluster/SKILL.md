---
name: microscopic-cluster
description: Run antisymmetrized RGM/GCM two-cluster calculations of light nuclei (Brink 0s clusters n, p, d, t, 3He, alpha, Minnesota force, microscopic R-matrix of Baye et al.) for bound states, phase shifts and scattering lengths, with the exchange parameter u fixed on the other parity, none on the quantity tested. Use when a task asks what an antisymmetrized calculation predicts for a phase shift, scattering length, effective range or level, whether a large R-matrix width can come from the cluster continuum, or for a parameter-free test of a cluster potential; such predictions must be computed, not estimated from memory.
---
# Microscopic two-cluster calculations (GCM / RGM)

A local cluster potential cannot see exchange, so the parity dependence of the effective interaction has to come from a calculation that antisymmetrizes all nucleons. This skill does that with a small model: two 0s clusters, a central nucleon-nucleon force with one exchange parameter, and an R-matrix at the surface. That is enough to predict the other parity with nothing adjusted, and the prediction is the value of the calculation. The adjusted quantities are therefore kept few and on the other side of the comparison. You need the two clusters, one datum of the other parity on which the exchange parameter u is fixed, and the phase shifts or R-matrix eigenphases to compare with. You get bound states, phase shifts, a0 and r0, with a spread over the oscillator width and the choice of datum. The model, the numerics and the conventions are described in [method.md](references/method.md).

## Where this fits

- Comes from: the local potential of `cluster-potential`, which is fast (node counting, ANCs, widths), is done first and is tested here; the R-matrix fit to compare with from `azure2`, as eigenphases from phase-shift grids; partitions outside the cluster model from `shell-model`; scattering lengths to compare with from `effective-range`.
- Goes to: `effective-range` for a0 and r0 from the phase shifts, with the same recipe for model, fit and data. Intruder states with a nucleon outside a core (6Li ⊗ sd) belong to `shell-model`, because this model contains only the cluster partition.
- Checked by: `scripts/selftest.py` (must print PASS, and `--full` end to end) and the validation ladder in [validation.md](references/validation.md), which also records the lessons that changed results.

## Method

The kernels are built once on a generator grid; because they are linear in u, the exchange parameter can then be fitted and varied at no extra cost.

1. Call `gcm.configure(c1, c2)`; `selftest.py` must pass. For a new system, check the small-R norm kernel against mu_N with `check_structure` and nmin = N_min of the system, because mu_N = 0 below N_min is the cleanest correctness test of a new system (method.md).
2. Build kernels on a generator grid (0.8–12 fm, step 0.8) for the waves needed: `K, Ethr = build_kernels(Rs, ls, b)`. Kernels are linear in u, `H_of(K, l, u)`.
3. Fix u on one datum of the other parity, with `fit_u_bound` for a bound centroid or the 90° crossing of a resonance.
4. Compute the phases with `phase_curve(rmatrix(K, Ethr, Rs, b, l, u), Es)`, in degrees and referenced to threshold. The ERE goes through `effective-range`.
5. Repeat over b and the u datum. Record u, the model threshold, a0, r0 and the rms differences from the fit's eigenphases in a `results.json`.

## Rules and their reasons

1. One quantity is adjusted, on the other parity. The Minnesota exchange parameter u is fixed on a negative-parity bound state or resonance, and everything in positive parity is then a prediction and stated as such. If u is fitted to the quantity it is compared with, the comparison proves nothing.
2. What physics does not fix is scanned. The calculation is repeated with at least three oscillator widths b and both choices of the u datum, and the spread is quoted, not one curve. The two data bracket the systematic of u (method.md).
3. The results say what the model does not contain. The clusters are 0s, so ³He is underbound (−3.3 MeV against −7.7 MeV); there is no spin-orbit force, so J = l ± s are degenerate; and there is one partition, so no p+⁶Li and no cluster distortion. The comparison is therefore made only below the next threshold.
4. The threshold is the model's own. Energies are relative to the sum of the model's cluster energies, which `build_kernels` returns, not to the experimental threshold, because the underbound ³He would otherwise shift every energy.
5. Pauli-forbidden directions are removed numerically, by a cutoff on the eigenvalues of the norm kernel. The phases must therefore be checked not to move when the norm-kernel cutoff eps (1e-6 vs 1e-7) and the channel radius (7–9 fm) change.
6. No conclusion is drawn about states this model cannot contain. A missing resonance in a cluster-only calculation says that the cluster continuum has none. It says nothing about a state built on another partition.

## Scripts

The code needs Python with numpy, scipy and mpmath. Replace SKILL_DIR with this skill's directory.

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

## What to deliver

- A `results.json` with u, the datum it was fixed on, the model threshold, a0, r0 and the rms differences from the fit's eigenphases, for each b and u datum.
- The spread over at least three b values and both u data, quoted as the model uncertainty.
- The numerical checks: eps and channel-radius stability of the phases.
- A statement of what the model does not contain and the energy range below the next threshold in which the comparison holds.
