---
name: cluster-potential
description: Build and use two-body cluster models of light nuclei (alpha+3He, alpha+t, alpha+d, alpha+alpha, alpha+n, ...) with deep local potentials that bind the Pauli-forbidden states — Wildermuth node counting, depths fixed on known levels, bound states, ANCs, phase shifts and resonances, the R-matrix quantities a potential implies (penetrability, shift function, Wigner unit, single-particle reduced width, theta^2 of a fitted width), RGM norm-kernel eigenvalues mu_N of two 0s clusters, parity-dependent (Majorana) potentials, and two-channel coupled-partition checks. Use whenever a task asks what a cluster model predicts for a level, width, ANC, phase shift or scattering length, whether an R-matrix width is above the single-particle limit, which relative-motion shells are forbidden, or how a mirror system behaves with the same potential; these must be computed, not estimated from memory.
---
# Two-body cluster potentials

A cluster model is the cheapest structure calculation that knows about the continuum. It gives widths, ANCs and phase shifts, which a bound-state shell model cannot. It is also local, so it misses the exchange that makes the effective interaction depend on parity. Use it for what it can carry and state what it cannot.

## Route the task

- **Fits to measured cross sections** (R-matrix, AZURE2): `azure2`. This skill supplies the physics behind a fitted width or energy.
- **Scattering length and effective range** of a phase shift (data, R-matrix eigenphases, or this model): `effective-range`.
- **Antisymmetrized calculation** with no adjusted positive-parity parameter: `microscopic-cluster`.
- **Energies and configurations of intruder states**, without widths: `shell-model`.
- **Mirror comparisons** (same potential, mirror spectrum, ANC ratio, width transfer): `mirror-nucleus` (built on this library).
- Everything else, the cluster model:
  - Pauli bookkeeping, potentials, observables and their conventions: [physics.md](references/physics.md);
  - validation ladder and the lessons that changed results: [validation.md](references/validation.md).

## Non-negotiable boundaries

1. **The potential binds exactly the forbidden states.** Count them with `n_forbidden` (Wildermuth: N = 2n + l < N_min) and check every fitted depth with `pauli_ok`. A shallow potential with the right level energy and the wrong node count is a different model.
2. **Fix the range once, on one band; fit depths per partial wave on known levels.** Every other number is then a prediction. Say which numbers were fitted and which were predicted.
3. **A local potential has no exchange.** It cannot produce the parity dependence that antisymmetrization gives (mu_N differs between odd and even N). A positive-parity prediction from depths fitted to negative parity is a test of locality, not of the data. The 7Be case gave a scattering length of the wrong sign (-31 fm against +22 to +60 fm measured).
4. **Report widths in the R-matrix convention you compare with.** `theta2_from_width` assumes an isolated level with Gamma = 2 P gamma^2 at radius a. A fit in the Brune parameterization or with overlapping levels needs its own observed widths. State the radius and the Wigner unit (hbar^2/mu a^2, or the Teichmann–Wigner 3/2 of it).
5. **Phase shifts are defined modulo pi.** Compare unwrapped curves referenced to threshold. The resonance criterion is delta(E) - delta(E_low) rising through pi/2, not the maximum of d delta/dE alone.
6. **A finite Coulomb radius changes the phase.** A uniform sphere differs from a point charge inside R_c (0.008 rad at 1 MeV for alpha+3He with R_c = 3.1 fm). Keep R_c fixed between models you compare.

## Working method

1. Define the `System` (clusters, threshold E_x, N_min from `s_shell_n_min` or the shell-model ground configuration, R_c).
2. Fix the Gaussian range on the lowest allowed band (fit the band members, or take it from the literature), then fit one depth per partial wave on its known level (`fit_V0_bound`, `fit_V0_resonance`). Check `pauli_ok` for each.
3. Predict what was not fitted: other levels, widths (`first_resonance`), ANCs (`anc`), phase shifts (`delta_curve`). Compare with data before using the model for anything else.
4. For R-matrix comparisons: `PS`, `gamma2_W`, `sp_reduced_width`, `theta2_from_width` at the fit's channel radius.
5. For exchange effects: the norm-kernel eigenvalues (`norm_kernel_mu`, `alpha_x_weights`) and, if needed, a parity-dependent depth fixed on one datum of the other parity (physics.md).
6. Record fitted depths, ranges, R_c and N_min in the study's `results.json`, with the levels they were fitted on.

## Scripts (Python with numpy, scipy, mpmath)

```bash
python3 SKILL_DIR/scripts/selftest.py        # must print PASS (7Be/7Li known answers, mu_N, Coulomb limit)
```
```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts"); import cluster as cl
s   = cl.System("alpha", "3He", thr_ex=1.5866, n_min=cl.s_shell_n_min("alpha", "3He"))
V   = cl.fit_V0_bound(s, l=1, nodes=1, Etarget=-1.5866, a=2.6883)      # 75.24 MeV
pot = cl.Pot(s, V, 2.6883); C = cl.anc(pot, 1, -1.5866)                 # C^2 = 23.0 fm^-1
d   = cl.delta_curve(pot, 0, np.linspace(0.2, 4.0, 60))                 # s-wave phase (rad)
```
Replace `SKILL_DIR` with this skill's directory. Extend `cluster.py` rather than writing a second solver.
