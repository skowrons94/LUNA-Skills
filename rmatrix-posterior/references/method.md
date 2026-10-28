# Method

## The target

log p(x) = −objective(x) / (2T), with x the free reduced-width-amplitude vector of pyazr (`params_rwa`: level energies, γ in MeV^½, normalizations, shifts) and

objective = χ²_data + Σ AZURE2 prior terms + Σ width priors + transformability prior.

- **χ²_data** is pyazr `calculate_chi2_rwa` (value) and `chi2_and_grad` (value and analytic gradient). The adjoint gradient costs about two forward evaluations.
- **AZURE2 prior terms** are the ones its own fit adds, mirrored from pyazr `penalties`: ((n − n₀)/(n₀ σ_n))² per free normalization, once per normalization group; (shift/σ)² per free energy shift, √E shift and shift-function term; the screening prior. Minimizing χ²_data alone lets the normalizations drift. `laplace_check.py` checks that χ²_data plus these terms equals pyazr `objective` at the best fit.
- **Width priors.** θ_c = γ_c/γ_W,c ~ N(0, s²) for each particle channel of each level, with γ²_W = `Parameter.wigner_limit`. That is the energy-independent Wigner limit in MeV, already squared. Use s = 1 for physical levels and check s = 2. Background poles get s = 10. Gamma widths get no width prior.
- **Transformability prior.** An evaluation that must convert to ENDF (conventional, B = −L, R-matrix) constrains each J^π group: λ_max(K_g) ≤ τ, with K_ab = Σ_c γ_ac γ_bc W_ab,c and W_ab,c = [S_c(E_a) − S_c(E_b)]/(E_a − E_b), and for each level |D_l| ≤ E_target, with D_l = E_l + Σ_c γ²_lc (S_c(E_l) − B_c). As a fit penalty these are hinges, w (max(0, u))². For HMC each hinge becomes w (s log(1 + e^{u/s}))² with s = 0.01. The shift functions are frozen at the reference parameters. The 7Be values are τ = 0.70, E_target = 300 MeV, w_λ = 2000 and w_pole = 200.
- **Temperature.** T = 1 is the posterior of the quoted uncertainties. T = χ²/ν is the Bayesian analogue of scaling the covariance by √(χ²/ν). Quote which one you used.

### The poles module

`SoftTransformability.from_poles` loads a user-supplied `poles.py` that provides

- `structure(azr, parameters) → {jpi: {level: {"ch": {c: {"fi": free index or None, ...}}}}}`, and
- `shifts(grp, x, epar) → (S, B, E)`: S_c at each level energy, B_c = −L, and c.m. level energies.

The 7Be evaluation's module (`analysis/brune-physicality/scripts/poles.py`) reads the `<levels>` block of the .azr and computes S_c with Ferdinand's `getCoulomb_PSdSW` (fudge and Ferdinand on the path). Without `--poles` the prior is off and every script says so. The 7Be choice keeps only J^π groups with more than one level, as `refit_physical.py` does. A single-level group then has no |D_l| bound either; `single_level_groups=True` keeps them.

## Whitening

x = x_ref + L z, L = V diag(λ^−½) √T, with H = V diag(λ) Vᵀ the Hessian of objective/2 at x_ref. Eigenvalues are floored at 10⁻⁸ max|λ|. The map is linear, so log p needs no Jacobian term. The sampler sees z, which is close to N(0, I) wherever the Laplace approximation holds.

- **Bootstrap:** JᵀJ of the standardized residuals (data and prior rows) at the best fit. It is cheap (one `residual_jacobian`) and good enough for a Newton start, but not as a metric (validation.md).
- **Reference:** `find_map.py` runs damped Newton in the bootstrap coordinates. Each iteration computes the Hessian by central differences of the analytic gradient (2n gradients), reflects and floors its eigenvalues so that each step is a descent step, and backtracks through model failures. It stops when the gain is below 10⁻⁵ and |∇| below 10⁻². It writes `map.npz`: x, H in x (independent of T), the best fit and the labels.
- A non-positive eigenvalue at the MAP means an open direction. Add or fix a prior; do not floor it away.

## NUTS

`nuts.py` is multinomial NUTS (Betancourt 2017) with Stan's extra U-turn checks across subtrees, biased progressive sampling at the top level, a maximum energy error of 1000 for divergences, and a dense or diagonal metric. Step size: dual averaging (γ = 0.05, t₀ = 10, κ = 0.75, target acceptance 0.85). Warm-up: Stan's windows (initial buffer 75, terminal 50, first slow window 25, doubling). The metric is updated at the end of each slow window and the step size is restarted.

- In whitened coordinates the identity is already a good metric. A noisy dense estimate is worse than none: use `--metric auto`.
- `--max-depth 8` caps a trajectory at 255 gradients (23 s at 91 ms). Hitting the cap often means the metric is wrong, not that the posterior is hard.
- Start points: z ~ N(0, I), i.e. draws from the Laplace approximation, one per chain.

## Checkpointing

`chain.py` keeps the whole state (position, step size, metric, dual-averaging state, warm-up buffer, RNG bit-generator state, iteration, chunk counter, target fingerprint) in `state.pkl`. Each `--every` iterations, and on SIGINT or SIGTERM, it writes the draws of the chunk (`draws_NNNNN.npz`), then the state, each atomically (temporary file and `os.replace`). A kill between the two leaves the old state, which re-runs the same iterations from the same RNG state and rewrites the same chunk. Resuming means running the same command again. The fingerprint (hash of x_ref and L, plus T) refuses a state from another fit.

emcee uses its HDF5 backend with `thin_by`. With 416 walkers and 202 parameters one stored step is 416 × 202 × 8 B = 672 kB; storing every fifth step keeps a 20 000-step run at 2.7 GB. Resume from `backend.get_last_sample()`: emcee's `sample(None)` does not resume.

## Costs and parallelism

Measure on one thread, at fresh points (`laplace_check.py` does this). On 7Be (2960 data points, 202 parameters) log p took 30 ms and log p with its gradient 91 ms. A repeated point is served from a cache, so 12 ms there is an artefact. Threads do not speed up log p, so run each NUTS chain as its own process with `OMP_NUM_THREADS=1`. emcee gets the same number of single-thread workers.

ESS per core-hour: NUTS core-seconds = gradient calls × t_grad; emcee = log-p calls × t_logp. Count warm-up and burn-in separately and quote both.

## Derived quantities

Evaluate on thinned draws of each sampler with the paper's own recipe. For S(0) that means the same test grid, fit window and polynomial order; S(0) differs at the 0.2 % level between extrapolation grids on 7Be. Cache per draw so the run can be stopped. The R-matrix block (energies, widths) must come first in the free vector; `derive_sfactor.py` asserts it.
