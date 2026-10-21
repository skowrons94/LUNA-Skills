---
name: uncertainty-audit
description: Audit whether the uncertainties of a nuclear-physics analysis support its conclusions — which sources are represented, how they are correlated and propagated, and whether quoted errors are calibrated against data (pulls, chi-squared, structured or localised residuals, coverage on held-out or later data, parameter correlations and identifiability, profile scans, interpolation vs extrapolation). Use before quoting a yield, efficiency, S factor, resonance parameter, rate or evaluation; when chi-squared looks too good or too bad; or when asked whether an error budget or fit uncertainty can be trusted. For proposal back-tests and sampler diagnostics use proposal-analysis.
---
# Uncertainty audit

Two questions, kept apart:

1. **Assessment:** does the analysis represent, correlate and propagate the uncertainties that matter for the conclusion it draws?
2. **Calibration:** do the quoted uncertainties behave like uncertainties when compared with data the analysis did not use, or with its own residuals?

A small error bar that fails the second question is worse than a large honest one.

## Route the task

- Back-tests of evaluations against later measurements, Bayesian design, MCMC or importance-sampling diagnostics: `proposal-analysis` (backtests.md, sampling-checks.md).
- Yield or efficiency error propagation itself: the stage skills. This skill audits it.
- Independent review of a finished result: the `physics-referee` subagent. Use this skill's checks as its evidence.

## Assessment

Read [assessment.md](references/assessment.md) and work through it against the code and result files, not the paper text. For each uncertainty source record: represented or not, size, how it was estimated, correlation structure (point-to-point, common to a data set, common to all data sets), how it enters the fit, and whether it is in the quoted result. Compare what the methods section claims with what the code does; a mismatch is a finding.

## Calibration checks

`scripts/uq_checks.py` (NumPy, SciPy):

```bash
python3 scripts/uq_checks.py residuals fit.csv --data S --model S_fit --sigma dS --x E --group dataset --n-par 7
python3 scripts/uq_checks.py coverage heldout.csv --obs S --obs-err dS --pred S_pred --pred-err dS_pred
python3 scripts/uq_checks.py correlations covariance.csv --names E1 G_p1 G_g1 a_c
```

- **residuals:** χ²/ν with p-value, pull mean and width, a runs test, and a sliding-window scan for localised structure. The scan's p-value is calibrated against pure noise, so it accounts for searching many windows; it catches a missed resonance or contaminant that a global χ² hides. Run it per data set (`--group`). A good global χ² can hide one bad data set.
- **coverage:** predictions with their band against data not used in the fit. Leave one data set out, or fit early runs and predict later ones. The fraction within 1σ should be about 68%.
- **correlations:** |ρ| > 0.95 or a covariance that is not positive definite means the data do not separate those parameters. Quote a combination, fix one with a stated reason, or add data. Then check with a profile scan (χ² against the parameter with the others refitted): an asymmetric or flat profile means the Gaussian error is not the uncertainty.

On clean synthetic data about 3% of data sets raise some flag (each test runs near the 1% level). A flag is a reason to look, not a verdict. Look at the plotted residuals before concluding.

## Non-negotiable boundaries

1. **Do not tune errors to the test.** Inflating uncertainties until χ²/ν = 1 hides the problem the test found. If a scale factor is used, say so, give it per data set, and keep the unscaled result.
2. **Held-out means held out.** Data used to choose the model, the normalisation or the level scheme are not a coverage test.
3. **Extrapolations are a separate class.** Coverage inside the data range says nothing about S(0) or a rate outside it. Quote the model dependence (channel radius, background poles, level assignments) separately from the fit uncertainty.
4. **Correlated systematics are not statistics.** A common normalisation error does not shrink with more points. Check that it was not divided by √N or added in quadrature per point.

## Deliver

- An uncertainty table: source, size, correlation, how it was estimated, in the result or not.
- The calibration check outputs with plots of the pulls by region.
- Findings ranked by their effect on the conclusion, with the specific fix for each.
- What the quoted uncertainty does not cover.

Write outputs to the user's project, never into the skill directory. `python3 scripts/selftest.py` must print PASS.
