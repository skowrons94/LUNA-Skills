# Posterior sampling checks

## Importance weights

- Kish effective sample size ESS = (Σw)² / Σw². When reweighting a pool with pseudo-data drives the ESS to tens, posterior widths are underestimated, sometimes dramatically. Report ESS (median and 5th percentile over pseudo-experiments) next to every reweighted number.
- Lower bound: the width left when the observables are known exactly (cross-validated regression residual, null-bias corrected). A reweighted width below that floor is an artefact.
- Never resample the same pool with replacement and cross-validate on it: duplicates leak across folds.

## Markov chains

- Estimate the integrated autocorrelation time τ with an automatic window (Sokal; Goodman–Weare ensemble estimators). Require chain length N ≳ 50 τ for tails, and check that τ is stable as N grows: if τ grows roughly in proportion to N, the chain has not converged, whatever the sampler (affine-invariant stretch moves and ensemble slice sampling can both fail on strongly correlated posteriors).
- Report split R̂ across walkers and across run halves.
- When convergence is not reachable in the time available, test the quoted quantities directly: compare their quantiles (16/50/84 and 2.5/97.5) across chain halves, walker subsets and different samplers, as a fraction of the 68% width, against the sampling-noise baseline. Quote the result in those terms (for example "68% intervals reproducible to a stated fraction of their width; tails indicative") and plan reparameterization (whitening with the posterior covariance) or nested sampling before publication.
- Multimodal posteriors (sign configurations, parity assignments): sample each mode, weight modes explicitly (state the method: evidence, best-fit χ², or equal), and report the sensitivity to the weighting.

`scripts/sampling_checks.py` provides ESS, τ and a quantile-stability function, with a synthetic self-test (AR(1) chain with known τ).
