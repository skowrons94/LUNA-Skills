---
name: rmatrix-posterior
description: Sample the Bayesian posterior of a multichannel R-matrix fit (AZURE2/pyazr, tens to hundreds of free energies, widths and normalizations) when emcee or other affine-invariant samplers mix poorly or earlier NUTS/HMC attempts failed — build the target (data chi-squared plus AZURE2's normalization and shift priors, Wigner-unit width priors with a broad scale for background poles, the ENDF-transformability constraint as a smooth prior), find the MAP and its exact Hessian, whiten, test the Laplace approximation, run checkpointed NUTS chains with an emcee baseline, compare effective samples per core-hour, and propagate draws to S(0) or a rate. Use when a task asks for posterior uncertainties, credible intervals or correlations of an R-matrix evaluation (7Be, 13C(a,n), 12C(a,g), ...), when an MCMC on an .azr does not converge, when autocorrelation times keep growing, or when deciding which priors make a fit physical.
---
# Posterior sampling of R-matrix fits

A multichannel R-matrix posterior is hard to sample for two separate reasons. The raw parameters are badly scaled, and that is a coordinate problem: whitening with the exact Hessian at the MAP removes it. Some directions are not closed by the data at all (background poles, levels at or above the data edge), and that is a modelling problem: only priors close them. Priors are how physicality enters the fit. A width prior in Wigner units and the transformability constraint are statements about what a physical level is; without them the sampler explores parameter sets nobody would adopt.

## Route the task

- **Running AZURE2, the pyazr API, the fit objective, parameter conventions:** `r-matrix`. This skill builds on its `chi2_and_grad`, `residual_jacobian` and `objective`.
- **Whether the quoted uncertainties are calibrated** (pulls, coverage, held-out data): `uncertainty-audit`. This skill produces the posterior; that one judges it.
- **Generic MCMC and importance-weight diagnostics** (τ growth, quantile stability, Pareto k̂): `proposal-analysis` (sampling-checks.md).
- **Whether a large width is physical** (θ² against the single-particle limit, scattering length): `cluster-potential`, `effective-range`.
- Everything else, the posterior and its sampling:
  - the target, priors, whitening, NUTS, costs: [method.md](references/method.md);
  - the validation ladder and the lessons that changed the method: [validation.md](references/validation.md).

## Non-negotiable boundaries

1. **Whiten with the exact Hessian at the MAP, not Gauss–Newton JᵀJ at the best fit.** On 7Be (202 parameters) JᵀJ has condition number 2×10⁹. Whitened with it, 14 axes deviate from the Gaussian by more than 1 in log p at 1σ, the worst by 34 000: JᵀJ drops the second-order curvature where widths of poorly constrained levels enter. With the exact Hessian at the MAP (2n analytic gradients, ~10 s) 200 of 202 axes deviate by less than 0.25 and the worst by 8.6.
2. **Priors are part of the model, not decoration.** With only AZURE2's normalization prior, Newton from the adopted 7Be fit lowered the objective by 13 and stalled on a ridge with a negative Hessian eigenvalue, where AZURE2 starts failing ("z is not finite in log_Gamma"). The adopted fit sat on its transformability hinge: penalty zero, gradient not. Put the width priors θ = γ/γ_W ~ N(0, 1) on physical levels and the transformability constraint into the target before sampling, and say in the paper that they are there.
3. **Bound the Park norm of physical levels.** Brune widths hide saturated levels: J = θ²/θ²_formal (pyazr) far below 0.5 means the state lives mostly outside the channel radius (`r-matrix`, physicality.md). Add J ≥ 0.5 as a stiff prior on levels below the background poles; it also removes flat directions that make the posterior hard to sample (7Be: cond 5.6e15 → 2.8e9).
4. **Background poles get their own prior scale.** They carry θ up to 6.7 by construction. A unit prior on them distorts the fit; use a broad scale (10) and let the transformability prior bound them. Declare them (`--bg-energy`); `find_map.py` warns when a unit prior meets |θ| > 3. Check the physical-level scale with 2 as well as 1.
5. **Hinges must be smooth and failures must be divergences.** Replace max(0, u) by a softplus before HMC sees it. A point where the model fails returns log p = −∞; it ends the trajectory as a divergence. It never raises, and it never returns a large finite penalty.
6. **The Laplace approximation is the initializer and the metric, not the answer.** Importance sampling from it gave a Kish ESS of 1 out of 1500 draws on 7Be, in the good metric. Small per-axis deviations add up in 202 dimensions. A sampler is needed.
7. **A dense metric needs at least ten draws per dimension per warm-up window.** Stan's warm-up windows hold 25 to 200 draws for 500 warm-up iterations; in 202 dimensions the dense estimate from them is rank-deficient. On a 202-dimensional toy with that schedule its condition number against the true covariance was 2.6×10⁵, and NUTS needed 914 gradients per draw against 15 with a diagonal update. On the real 7Be run the first window (25 draws) froze 178 of 202 directions at an inverse mass of 1.7×10⁻⁴ (Stan's 10⁻³ shrinkage); we stopped and restarted it. Self-test check 7 reproduces the trap in 60 dimensions (1008 gradients per draw, against 9 with `auto`). In whitened coordinates use `--metric auto` (diagonal unless the window holds 10 draws per dimension), shrunk towards 1, not 10⁻³.
8. **Compare samplers in effective samples per core-hour at measured one-thread costs.** On 7Be log p costs 30 ms and log p + analytic gradient 91 ms. Neither speeds up with threads, so run chains as separate single-thread processes. A repeated point is served from a cache: 12 ms there is an artefact. Report emcee's ESS as an upper bound unless the kept chain exceeds 50 τ.
9. **Do not judge an ensemble sampler by its own autocorrelation time in this dimension.** On 7Be emcee (416 walkers, acceptance 0.09) reported τ = 10, 15 and 29 stored steps after 0.95, 1.3 and 2.6 thousand steps: an estimate that grows with the run is not converged. Its ensemble contracted to 84 % of the posterior widths within minutes and after 4.4 h on four cores was still at 94 % (median) and 22 % (narrowest parameter) of the NUTS widths, with mean −2 ln p 12 below. Compare it with a reference posterior (`compare.py`, `make_figures.py` relaxation panel), not with itself.
10. **Fold the sign symmetry of each level before computing R̂, and start some chains wide.** Changing the sign of every width of one level (particle and photon) leaves the R matrix and the capture amplitude unchanged, so the posterior has exact mirror copies a chain cannot cross between. On 7Be, four chains started at three times the posterior width agreed on ln p (R̂ 1.001) but gave R̂ up to 1.66 in 14 parameters: one chain sat in the copy with the 3/2⁻ background pole's widths reversed. Folding each draw to the sign of the level's largest width at the MAP changed only that chain and brought R̂ to 1.09; its S34(0) was 0.5589 ± 0.0075 keV b, the same as the others. Without wide starts this is invisible; without the fold it looks like non-convergence. A multi-start Newton search is not a substitute: of four completed wide starts it converged to the MAP once, approached it once, stalled on a ridge once and ended far away once. Use `scripts/fold.py`.
11. **Every number traces to a run file.** The NUTS-against-emcee ratio, R̂, τ and the S(0) posterior come from `compare.json` and the derived-quantity caches of a named run directory. Leave a placeholder until they exist.

## Working method

1. Fix the adopted fit (.azr + param.sav) and the run directory. Record the free-parameter count, the data count and the objective at the best fit. `laplace_check.py` confirms that data + AZURE2 priors equal pyazr's `objective`.
2. Decide the priors: physical-level θ scale, background-pole energy and scale, and the transformability prior (`--poles`, optional; see method.md). Write them down before sampling.
3. `find_map.py`: damped Newton to the MAP with the exact Hessian. It reports the objective parts, the largest moves from the best fit in MAP σ, and any non-positive eigenvalue. A non-positive eigenvalue means a direction is still open: revisit step 2.
4. `laplace_check.py` (and `--gauss-newton` to see what the cheap metric would have done): gradient against finite differences, one-thread costs at fresh points, per-axis scans, Pareto k̂. If k̂ < 0.7, reweighted Laplace draws are the posterior and you can stop here.
5. `run_all.sh`: four NUTS chains (`run_chain.py`) and the emcee baseline (`run_emcee.py`), one thread each, checkpointed. Stop and resume freely.
6. `compare.py`: R̂ < 1.01, no unexplained divergences, bulk and tail ESS, emcee τ with the 50τ rule, ESS per core-hour for both samplers, and posterior means and widths side by side.
7. `derive_sfactor.py` (or your own derived quantity) on thinned draws from both samplers, with the paper's extrapolation recipe. Quote the posterior with the sampler, chain lengths, R̂ and ESS.

## Scripts (Python with numpy, scipy; arviz-stats, emcee, h5py for the AZURE2 runs)

```bash
python3 SKILL_DIR/scripts/selftest.py      # must print PASS; no AZURE2 needed (~30 s)
```
```bash
S=SKILL_DIR/scripts; FIT="--azr 7Be.azr --sav output/param.sav --cwd . --bg-energy 25 --poles poles.py"
python3 $S/find_map.py      $FIT --out runs/nominal
python3 $S/laplace_check.py $FIT --out runs/nominal
sh      $S/run_all.sh "$FIT" runs/nominal 500 1000 4000
python3 $S/compare.py --out runs/nominal --t-grad 0.091 --t-logp 0.030 --key '@7.65'
python3 $S/derive_sfactor.py --azr 7Be.azr --cwd . --out runs/nominal --key 113 --emax 0.30 --scale 1e3
```

`target.py` (posterior, priors, whitening), `fold.py` (exact level-sign symmetry, before R̂), `nuts.py` (multinomial NUTS, dense or diagonal metric, dual averaging, Stan windows) and `chain.py` (atomic checkpoint and resume) are generic: `run_chain(logp_grad, dim, dir, ...)` samples any target with a gradient.

Write runs to the user's project, never into the skill directory.

## Result on 7Be (runs/nominal of analysis/posterior; one night, four cores per sampler)

- NUTS, 4 chains × (500 warm-up + 1000 draws), 47 gradients per draw, 4.1 h: R̂ max 1.08, bulk ESS median 1809 and min 48 of 4000 draws, ESS(log p) 1003, 76 divergences (1.9 %, mostly one excursion of two chains). The slowest parameters are the background-pole widths at 30 MeV, which the priors, not the data, set.
- emcee, 416 walkers, 2615 steps, 4.4 h: not equilibrated (boundary 8); its ESS is not defined.
- S34(0), 800 NUTS and 1000 emcee draws: 0.5584 (+0.0081 −0.0080) and 0.5590 (+0.0079 −0.0083) keV b; adopted best fit 0.5608, MAP 0.5596. The well-constrained quantity agrees between the samplers; emcee's failure is in the non-Gaussian, prior-dominated directions, where its widths are 22–34 % of the NUTS widths. A sampler that is wrong there can still give the right S(0): check which kind of quantity you quote.

