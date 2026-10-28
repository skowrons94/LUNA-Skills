# Validation ladder

| Rung | Check | How | Proves | Does not prove |
|---|---|---|---|---|
| 0 | Library | `scripts/selftest.py` prints PASS | NUTS recovers an ill-conditioned Gaussian once whitened; checkpoint/resume is bit-identical; the soft prior's gradient; failures become divergences; the dense-window trap is avoided | anything about your fit |
| 1 | Target | `laplace_check.py`: data + AZURE2 priors = pyazr `objective` at the best fit; z-gradient against finite differences (relative error ≤ 10⁻³) | the posterior is the fit's objective plus the stated priors | that the priors are right |
| 2 | Mode | `find_map.py`: \|∇\| → 0, all Hessian eigenvalues positive, objective parts and largest moves reported | the priors close every direction | that the posterior is Gaussian |
| 3 | Metric | per-axis scans at ±1σ, ±2σ; MAP Hessian against `--gauss-newton` | where the Laplace approximation fails, by parameter | the global shape |
| 4 | Laplace | Pareto k̂ and Kish ESS of importance weights | whether a sampler is needed (k̂ > 0.7 or nan: yes) | — |
| 5 | Chains | `compare.py`: R̂ < 1.01 over ≥ 4 chains, divergences, bulk and tail ESS ≥ 400 for quoted quantities, step size and tree depth | the chains agree and mix | that a mode was not missed by all of them |
| 6 | Second sampler | emcee from the same start: means and widths within MC error, τ with the 50τ rule | the result does not depend on the sampler | — |
| 7 | Derived quantity | S(0) or a rate from both samplers with the paper's recipe; the MAP and best-fit values alongside | the quoted interval | model dependence (radius, background poles, level scheme) |

## Lessons that changed the method (7Be study: 202 free parameters = 75 R-matrix + 127 normalizations, 2960 data points)

- **The conditioning was a coordinate problem.** cond(JᵀJ) = 2.11×10⁹ in the raw parametrization. Whitening reduces the sampler's problem to a near-identity Gaussian along most axes. No sampler change was needed for that part.
- **The cheap metric is wrong exactly where it matters.** Whitened with JᵀJ at the best fit, a 1σ step along 14 of 202 axes cost more than 1 in log p, and up to 34 250 along the axis made of the 11.52 MeV widths. Gauss–Newton drops the second-order term Σ rᵢ ∇²rᵢ, which is large where widths of poorly constrained levels enter non-linearly. With the exact Hessian at the MAP, 200 of 202 axes stay within 0.25 at 1σ; the worst (the 30 MeV background-pole widths) is 8.6.
- **Non-identifiability, not conditioning, is the obstacle.** The background poles at 30 MeV and the levels at and above the data edge (11.52, 15.67 MeV) are directions the data do not close. Newton from the adopted fit, with no physicality constraint, lowered the objective by 13 and stalled on a ridge with a negative Hessian eigenvalue, where AZURE2 began to fail ("z is not finite in log_Gamma"). The adopted fit sat on its transformability hinge, with zero penalty but a non-zero gradient.
- **The priors move the fit a little and close it.** With unit θ priors on the physical levels, scale 10 on the background poles and the soft transformability prior, the MAP has χ²_data = 5061.7 against 5057.4 at the adopted fit. The prior moved mainly the 11.52 MeV widths, by about 2σ (−2.27, −2.24, +1.96 in MAP σ). All Hessian eigenvalues at the MAP are positive. At the adopted best fit the width priors contributed 26.6 (physical) and 2.0 (background) and the transformability prior 0.85.
- **Background poles are not levels.** Their θ reaches 6.7. A unit prior would pull them into the data.
- **Laplace importance sampling fails in 202 dimensions.** A Student-t (ν = 7) proposal on the MAP metric gave a Kish ESS of 1 out of 1500, with no model failures. The median of log p minus the Laplace log p was −40 over the draws. With the JᵀJ metric (an earlier target without width priors, 2000 draws) it was −1922, again with an ESS of 1. Self-test check 6 reproduces the mechanism: per-axis deviations of 0.09 in log p at 1σ leave a Kish ESS/N of 0.89 in 5 dimensions and 0.03 in 202.
- **PSIS can return k̂ = nan** when the log weights span thousands. Treat nan as failure.
- **Dense metrics from short windows.** A 202-dimensional toy with the default 500-iteration warm-up (windows of 25, 50, 100 and 200 draws) gave a dense metric with condition 2.6×10⁵ against the truth and 914 gradients per draw, against 15 with a diagonal update. Use `--metric auto`.
- **Timing.** At fresh points on one thread, log p took 30 ms and log p with its gradient 91 ms. A repeated point took 12 ms (cache). Threads do not help log p.

## Comparison on 7Be (one night, four cores per sampler)

| Quantity | NUTS | emcee |
|---|---|---|
| wall-clock, model evaluations | 4.1 h, 2.8×10⁵ gradients | 4.4 h, 1.1×10⁶ values |
| bulk ESS median / min (4000 NUTS draws) | 1809 / 48 | not defined (not equilibrated) |
| R̂ max / τ (50τ rule met?) | 1.08 | 29 stored steps and growing; no |
| widths relative to NUTS, median / min | 1 | 0.94 / 0.22 |
| mean −2 ln p (Gaussian expectation 5597) | 5601.2 | 5589.2 |
| S34(0) median and 68 % interval (keV b) | 0.5584 +0.0081 −0.0080 | 0.5590 +0.0079 −0.0083 |

## Overdispersed starts on 7Be (runs/wide)

Four chains from z ~ N(0, 3² I), with the metric of a main-run chain, 150 + 500 iterations. ln p agreed with the main run (R̂ 1.001; mean −2 ln p 5600.8 in both). Fourteen background-pole widths gave R̂ up to 1.66: one chain sat in the copy with every width of the 3/2⁻ background pole reversed, an exact symmetry. After `fold.fold_level_signs` R̂ was 1.09 (wide chains) and 1.15 (pooled with the main run), the means agreed within 0.22σ, and S34(0) was 0.5579 ± 0.0082 keV b (0.5589 ± 0.0075 in the mirror chain alone). The remaining R̂ ≈ 1.1 is slow mixing along the background-pole widths, which the data do not determine.
