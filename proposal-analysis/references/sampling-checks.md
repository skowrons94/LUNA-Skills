# Posterior sampling checks

## Importance weights

- Kish effective sample size ESS = (Σw)² / Σw². When reweighting a pool with pseudo-data drives the ESS to tens, posterior widths are underestimated, sometimes dramatically. Report ESS (median and 5th percentile over pseudo-experiments) next to every reweighted number.
- Kish ESS is necessary, not sufficient: it can look healthy when no sample lies in the important region. Also report the Pareto-k̂ diagnostic of the weights (PSIS; k̂ > 0.7 unreliable).
- Reference floor: the expected width left when the observables are known exactly, estimated by a flexible, cross-fitted regression residual (null-bias corrected). The residual of an imperfect regression lies above the true floor, so treat an expected reweighted width clearly below it as an artefact, and a marginal one as a sign that the regression should be made more flexible. The comparison holds in expectation over pseudo-experiments, not for each one.
- Never resample the same pool with replacement and cross-validate on it: duplicates leak across folds.

## Markov chains

- Estimate the integrated autocorrelation time τ with an automatic window (Sokal; Goodman–Weare ensemble estimators). Require chain length N ≳ 50 τ for tails, and check that τ is stable as N grows: if τ grows roughly in proportion to N, the chain has not converged, whatever the sampler (affine-invariant stretch-move and ensemble-slice samplers are insensitive to linear correlations but can fail on curved or funnel-shaped degeneracies and in high dimension). The prefix test is meaningful only once the shortest prefix is already ≳ 50 τ; below that, τ̂ grows even for a converged chain.
- Report rank-normalized split R̂ (Vehtari et al. 2021, threshold 1.01) across independent runs (separate ensembles with dispersed starts) and across run halves; walkers of one ensemble are not independent chains.
- When convergence is not reachable in the time available, test the quoted quantities directly: compare their quantiles (16/50/84 and 2.5/97.5) across chain halves, walker subsets and different samplers, as a fraction of the 68% width, against the sampling-noise baseline (the expected standard error of each quantile difference, which grows with τ). Quote the result in those terms (for example "68% intervals reproducible to a stated fraction of their width; tails indicative") and plan a reparameterization that removes the non-linear degeneracy (products or ratios of correlated widths, log scales), a gradient-based sampler, or nested sampling before publication. Linear whitening helps non-affine-invariant samplers only.
- Multimodal posteriors (sign configurations, parity assignments): sample each mode, weight modes explicitly (state the method: evidence, best-fit χ², or equal; only evidence weights are posterior probabilities, χ²-based weights ignore the mode volume), and report the sensitivity to the weighting.

`scripts/sampling_checks.py` provides Kish ESS, Pareto k̂, τ and its growth, rank-normalized split R̂ and a quantile-stability function with its noise baseline, with a synthetic self-test (AR(1) chain with known τ, Pareto weights with known k).
