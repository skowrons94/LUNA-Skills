---
name: cluster-potential
description: Build two-body cluster models of light nuclei (alpha+3He, alpha+t, alpha+d, alpha+alpha, alpha+n) with deep local potentials binding the Pauli-forbidden states (Wildermuth node counting): levels, resonances, ANCs, phase shifts, mu_N of two 0s clusters, Majorana potentials and R-matrix quantities (penetrability, shift function, Wigner unit, single-particle width, theta^2). Use when a task asks what a cluster model predicts for a level, width, ANC, phase shift or scattering length, whether an R-matrix width is above the single-particle limit, or which relative-motion shells are forbidden; these must be computed, not estimated from memory.
---
# Two-body cluster potentials

A cluster model is the cheapest structure calculation that knows about the continuum. Two clusters move in a deep local potential, and the model gives level energies, widths, ANCs and phase shifts, which a bound-state shell model cannot. It also implies the R-matrix quantities of a level, so it tells whether a fitted width is above the single-particle limit. The model is local, however, and therefore misses the exchange that makes the effective interaction depend on parity; it is used for what it can carry, and what it cannot is stated. You need the two clusters, the threshold, the known levels on which the depths are fixed and a Coulomb radius. You get fitted depths, predicted levels, widths, ANCs and phase shifts, and the R-matrix quantities at a stated channel radius. Two-channel coupled-partition checks are described as a method in [physics.md](references/physics.md).

## Where this fits

- Comes from: known levels from evaluated data; the fitted width or energy to interpret from `r-matrix`, whose fits to measured cross sections this skill does not replace; intruder energies from `shell-model`; scattering lengths to compare with from `effective-range`.
- Goes to: `effective-range` for the scattering length and effective range of a phase shift; `mirror-nucleus`, which is built on this library, for the same potential in the mirror system, the ANC ratio and width transfer; `microscopic-cluster` for the antisymmetrized test with no adjusted positive-parity parameter. Energies and configurations of intruder states, without widths, come from `shell-model`.
- Checked by: `scripts/selftest.py` (must print PASS) and the validation ladder in [validation.md](references/validation.md), which also records the lessons that changed results. Pauli bookkeeping, potentials, observables and their conventions are in [physics.md](references/physics.md).

## Method

The Gaussian range is fixed once on one band, one depth per partial wave is fitted on a known level, and every other number is a prediction that is compared with data before the model is used further.

1. Define the `System`: the clusters, the threshold E_x, N_min from `s_shell_n_min` or the shell-model ground configuration, and R_c.
2. Fix the Gaussian range on the lowest allowed band, by fitting the band members or taking it from the literature. Then fit one depth per partial wave on its known level with `fit_V0_bound` or `fit_V0_resonance`, and check `pauli_ok` for each.
3. Predict what was not fitted: other levels, widths (`first_resonance`), ANCs (`anc`) and phase shifts (`delta_curve`). Compare them with data before using the model for anything else.
4. For R-matrix comparisons, evaluate `PS`, `gamma2_W`, `sp_reduced_width` and `theta2_from_width` at the fit's channel radius.
5. For exchange effects, compute the norm-kernel eigenvalues with `norm_kernel_mu` and `alpha_x_weights`. If needed, add a parity-dependent depth fixed on one datum of the other parity, as described in physics.md. To see how much of a repulsive s wave the Pauli principle alone produces, run the orthogonality-condition model of Saito with Coulomb and no attraction (`ocm_phase`) and compare its phase with a charged hard sphere from `effective-range`.
6. Record the fitted depths, ranges, R_c and N_min in the study's `results.json`, with the levels they were fitted on.

## What the model assumes

1. A deep potential respects the Pauli principle only if it binds exactly the forbidden states, which in Wildermuth's counting are those with N = 2n + l < N_min. Count them with `n_forbidden` and check every fitted depth with `pauli_ok`. A shallow potential that gives the right level energy with the wrong number of nodes is not a cheaper version of the same model but a different model.
2. The Gaussian range is fixed once, on one band, and one depth per partial wave is then fitted on a known level. Every other number the model gives is a prediction, and only the predictions test the model. The results must therefore say which numbers were fitted and which were predicted.
3. A local potential contains no exchange, so it cannot produce the parity dependence that antisymmetrization introduces (Tang, LeMere and Thompson, Phys. Rep. 47, 167 (1978)). The norm-kernel eigenvalues mu_N alternate between odd and even N, but they are normalizations of the allowed shells and not strengths of an interaction: neither Horiuchi nor Saito reads mu_N > 1 or < 1 as a stronger or weaker force, and a report does not either. When depths fitted to negative-parity levels predict a positive-parity quantity, the comparison tests the locality assumption, not the data. In 7Be this test fails: the predicted scattering length has the wrong sign, -31 fm against +22 to +60 fm measured.
4. Widths are reported in the R-matrix convention they are compared with. `theta2_from_width` assumes an isolated level with Gamma = 2 P gamma^2 at radius a. A fit in the Brune parameterization or with overlapping levels has observed widths that are not this simple, so θ² is taken from the fit code itself (AZURE2 `dimensionless_widths`, physics.md). The radius and the Wigner unit, hbar^2/mu a^2 or the Teichmann–Wigner 3/2 of it, are always stated.
5. Phase shifts are defined modulo pi, so curves are compared unwrapped and referenced to threshold. The resonance criterion is delta(E) - delta(E_low) rising through pi/2, not the maximum of d delta/dE alone.
6. A finite Coulomb radius changes the phase. A uniform sphere differs from a point charge inside R_c, by 0.008 rad at 1 MeV for alpha+3He with R_c = 3.1 fm. R_c is therefore kept fixed between models that are compared.

## Scripts

The library needs Python with numpy, scipy and mpmath.

```bash
python3 SKILL_DIR/scripts/selftest.py        # must print PASS (7Be/7Li known answers, mu_N, Coulomb limit, OCM)
```
```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts"); import cluster as cl
s   = cl.System("alpha", "3He", thr_ex=1.5866, n_min=cl.s_shell_n_min("alpha", "3He"))
V   = cl.fit_V0_bound(s, l=1, nodes=1, Etarget=-1.5866, a=2.6883)      # 75.24 MeV
pot = cl.Pot(s, V, 2.6883); C = cl.anc(pot, 1, -1.5866)                 # C^2 = 23.0 fm^-1
d   = cl.delta_curve(pot, 0, np.linspace(0.2, 4.0, 60))                 # s-wave phase (rad)
d0  = cl.ocm_phase(s, 0, 1.0, b_nuc=1.36)                               # Pauli only: -6.83 deg
```
Replace `SKILL_DIR` with this skill's directory. New functionality goes into `cluster.py` rather than into a second solver, so that `mirror-nucleus` and the selftest keep testing the code that is used.

## What to deliver

- The fitted depths, the range, R_c and N_min, with the levels they were fitted on, in `results.json`.
- The `pauli_ok` check for every fitted wave and the node number of each physical state.
- The predictions, labelled as predictions: levels, widths, ANCs and phase shifts, with their comparison to data.
- For an R-matrix comparison: P, S, the Wigner unit used, the single-particle reduced width and θ² at the stated channel radius.
- For a statement that the Pauli principle makes a repulsive s wave: the orthogonality-only phase and its equivalent hard-sphere radius, next to the data.
