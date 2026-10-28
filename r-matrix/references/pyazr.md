# pyazr reference

Session basics, installation and the minimal session are in SKILL.md.

### Two parameter conventions

- **`*_rwa` methods** (`calculate_rwa`, `calculate_chi2_rwa`,
  `calculate_sfactor_rwa`, `chi2_and_grad`, `residual_jacobian`) take the
  **reduced-width-amplitude** vector `m.params_rwa`. This is the natural fit
  space and the only one with analytic derivatives. **Default to it.**
- **plain methods** (`calculate`, `calculate_chi2`) take the transformed
  **physical** vector `m.params` (level energies in MeV, partial widths in eV).
- `m.transform_rwa(x)` maps rwa → physical; it takes either the full free
  vector or just the leading R-matrix block (energies + widths), so the
  norm/shift tail can be sliced off:
  `nR = 1 + max(p.free_index for p in m.parameters if p.kind in ("energy","width") and not p.fixed and p.free_index is not None)`.

Both vectors hold only the **free** parameters, in `.azr` order:
`p.free_index` is the position in that vector, `p.index` the position among all
parameters (`m.fixed_params`, `param.sav` lines).

### Data mode vs extrapolation mode

`m.data_mode()` (default) evaluates the `<segmentsData>` segments — this is what
χ² uses. `m.extrap_mode()` switches to the `<segmentsTest>` grids. Both
re-INITIALIZE every instance, so switch sparingly and batch the work.

**Segment indexing** (a frequent source of silent misalignment):

- data mode: segment `i` ↔ `m.datasets[i]` (the i-th `<segmentsData>` line);
  `m.nsegments` and `len(m.energies[i])` are its point count.
- extrap mode: **only ACTIVE test segments are returned**, in file order, so
  segment `i` ↔ `m.extrapolations.active[i]` — not `m.extrapolations[i]`.
  (7Be: 113 test segments declared, 108 active and returned.)

### Inspecting a model

```python
print(m.level_scheme)          # pairs → J-groups → levels → channels (read-only)
print(m.parameters.table())    # idx, name, kind, free, J^pi, E, L, S, pair, rad, value, wigner
print(m.datasets.table())      # per data segment: file, reaction, observable, E range, norm err
print(m.extrapolations.table())
m.pairs                        # PairSet: masses, charges, spins, sep/excitation E, channel radius
m.parameters.free / .widths / .energies / .norms / .shifts
m.parameters.by_physical_level()   # {LevelKey: ParameterSet} — one entry per resonance/pole
m.physical_levels()                # the LevelKeys, ordered (jgroup, level)
m.datasets.sys_errors(vary_only=True)   # per-segment normalization systematics (fractional)
```

A `LevelKey` prints as `5/2-#2@6.588MeV`; `(jgroup, level)` is its identity
(AZURE2 restarts level numbering inside every J-group).

### χ², residuals, per-dataset χ²

```python
chi2  = np.sum(m.calculate_chi2_rwa(x))     # total only
val, g = m.chi2_and_grad(x)                 # analytic gradient (energies/widths/norms)
r, J   = m.residual_jacobian(x)             # r_i standardized: sum(r**2) == chi2
```

`residual_jacobian` costs ~2 forward evaluations for the whole Jacobian
(reverse-mode adjoint) — use it for Gauss-Newton/LM fits *and* to get the
**per-segment χ² the API does not expose**:

```python
seglens = [len(m.energies[i]) for i in range(m.nsegments)]   # data mode
idx = np.cumsum([0] + seglens)
seg_chi2 = np.array([np.sum(r[idx[i]:idx[i+1]]**2) for i in range(m.nsegments)])
# aggregate by experiment: m.datasets[i].name
```

Energy-shift columns come back zero; an analytically unsupported segment raises.

**`chi2`/`residual_jacobian` are the DATA χ² only.** AZURE2's own fit objective
(`AZURECalc::operator()`) also carries a penalty per free normalization,
`((norm − nominal)/(nominal·sys_err))²`, and one per free energy shift. Minimize
the API's residuals alone and the norms drift to absorb every discrepancy — a
"better" χ² that AZURE2 would never have found (−480 on the 7Be model). Append
the penalty rows, with their constant Jacobian rows:

```python
pen = [(p.free_index, d.norm, d.norm * d.norm_error / 100.0)
       for p in m.parameters.norms
       for d in [m.datasets[p.segment_key - 1]] if d.norm_error > 0]
Jpen = np.zeros((len(pen), nfree))
for k, (fi, _, s) in enumerate(pen): Jpen[k, fi] = 1.0 / s
resid = np.concatenate([r, [(z[fi] - n0)/s for fi, n0, s in pen]])
```

`chiSquared.out`'s `Total-Chi-Squared` is likewise the data part; the penalty is
the separate `Total-Norm-Chi-Squared`.

### Calculating observables

```python
m.calculate_rwa(x)                  # cross section per segment (b or b/sr)
m.calculate_sfactor_rwa(x)          # S-factor per segment (MeV b)
m.calculate_energies(x)             # c.m. energies of the calculated points
m.calculate_excitation_energy(x)    # compound-nucleus Ex — the common axis across channels
m.calculate_angles(x)               # c.m. angles (differ from the lab angles in the .azr)
m.calculate_analyzing_power_rwa(x)  # vector A_y, for analyzing-power segments
m.calculate_angular_dists_rwa(x)    # Legendre coefficients, for ang-dist segments
```

Plot different reaction channels against **excitation energy**; it is the only
axis shared by all entrance pairs. `E_cm = Ex − threshold`.

### Analyzing power (observable 7)

The vector analyzing power `A_y` for a spin-1/2 projectile. Declare a segment
with `observable="analyzing-power"` (code 7 in the raw `.azr`); it is reported
**in place of** the cross section, so χ², fitting, plotting and output files
need no special handling.

```python
ay = m.calculate_analyzing_power_rwa(m.params_rwa)
```

Works for a spin-1/2 **projectile** on a target of any spin. The amplitudes come
out of the R-matrix in the channel-spin basis, so for a target with spin the
entrance index is decomposed into projectile and target projections before
`sigma_y` is applied to the projectile alone. For a spin-0 target (¹²C) the
channel spin *is* the projectile's and no decomposition is needed; for a
spin-1/2 target (¹⁵N) the channel spins are 0 and 1 and never 1/2.

Four things that will bite:

- **Angles are centre-of-mass** in the data file, unlike an ordinary
  differential segment. Columns are `E_lab · theta_cm · A_y · dA_y`.
- **A_y is a dimensionless ratio in [-1,1] and is often negative.** Do not put a
  relative uncertainty on it — a point near a zero crossing does not have a
  small uncertainty, and doing so gives those points enormous weight and wrecks
  the fit. Use a roughly constant absolute uncertainty.
- **Leave `vary_norm` off.** A normalization factor is meaningless for a ratio.
- **Use segments with no target integration** when comparing against
  thin-target data. `A_y` averaged over a target is cross-section weighted,
  `<A_y> = ∫A_y σ dE / ∫σ dE`, and since Rutherford σ diverges at low energy
  where A_y ≈ 0, a thick target drives the average to ~1e-6. That is physics,
  not a bug.

Analytic derivatives cover A_y, *except* for a point that also carries target
integration — that one reports itself unsupported, which drops the analytic
Jacobian for the whole fit back to numerical. Never wrong, just slower.

Worked comparison against measured data: `tests/13N`, segments 11–16 (Baumann
1992). Formalism and implementation: `docs/source/theory/polarization_*.rst`.

## Fitting from Python

Minuit (CLI mode 2) fits everything free in the `.azr`. For evaluation work you
usually want to fit a **subset** at frozen everything-else, which pyazr does with
`scipy.optimize.least_squares` and the analytic Jacobian:

```python
from scipy.optimize import least_squares

fit = np.array([p.free_index for p in m.parameters.widths
                if not p.fixed and p.radiation_type in ("E", "M")], int)

def resid(z):
    v = np.array(best, float); v[fit] = z
    return m.residual_jacobian(v)[0]

def jac(z):
    v = np.array(best, float); v[fit] = z
    return np.asarray(m.residual_jacobian(v)[1])[:, fit]

sol = least_squares(resid, best[fit], jac=jac, method="lm",
                    xtol=1e-14, ftol=1e-14, max_nfev=2000)
x = np.array(best, float); x[fit] = sol.x
```

Fit in **rwa space** (that is where the Jacobian is exact) and convert for
reporting with `transform_rwa`. Free the relevant normalizations too
(`m.parameters.norms`, `p.segment_key - 1` indexes `m.datasets`) when a subset
fit would otherwise be absorbed by them.

Sanity-check the fit space: `transform_rwa(best[:nR])[p.free_index]` must equal
`p.value` for every width.

For MCMC, `pyazr/examples/fit_emcee.py` and `fit_zeus.py` show the pattern —
`nprocs` instances, one per pool worker, priors chosen per `p.kind`, and
`log_prob = -0.5*(chi2 + offset) + log_prior` with
`offset = Σ log(2π σ²)`.
