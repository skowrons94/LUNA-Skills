---
name: uncertainty-audit
description: Audit whether the uncertainties of a nuclear-physics analysis support its conclusions: which sources are represented, correlated and propagated, and whether quoted errors are calibrated (pulls, chi-squared, structured or localised residuals, coverage on held-out or later data, parameter correlations and identifiability, profile scans, interpolation vs extrapolation). Use before quoting a yield, efficiency, S factor, resonance parameter, rate or evaluation, when chi-squared looks too good or too bad, or when asked whether an error budget or fit uncertainty can be trusted; proposal back-tests and sampler diagnostics belong to proposal-analysis.
---
# Uncertainty audit

A quoted result is only as useful as its uncertainty, and an analysis can get the central value right while its error bar says little about how far the truth may lie. This skill asks two questions and keeps them apart:

1. Assessment: does the analysis represent, correlate and propagate the uncertainties that matter for the conclusion it draws?
2. Calibration: do the quoted uncertainties behave like uncertainties when compared with data the analysis did not use, or with its own residuals?

A small error bar that fails the second question is worse than a large honest one. You need the code, configurations and result files of the analysis, its fit residuals and covariance, and where possible data it did not use. You get an uncertainty table, calibration checks with plots, and ranked findings with a fix for each.

## Where this fits

- Comes from: the results of the stages it checks, namely yields from `yield-analysis` and `peak-shape-analysis` (contract `yield-table`), efficiency curves from `efficiency-analysis` (`efficiency-curve`), target profiles and effective energies from `target-analysis`, R-matrix fits, S factors, resonance parameters and extrapolations from `r-matrix` and `resonance-search`, rate tables (`rate-table`), and simulation-based corrections from section 2 Simulating the experiment.
- Goes to: the `physics-referee` subagent, which uses these checks as its evidence, and the gate of the corresponding `analysis-chain` stage before the number is quoted.
- Checked by: `scripts/selftest.py`, and a look at the plotted residuals before any flag is turned into a conclusion.

The error propagation itself belongs to the stage skills; this skill audits it. Back-tests of evaluations against later measurements, Bayesian design, and MCMC or importance-sampling diagnostics are in `proposal-analysis` (backtests.md, sampling-checks.md). An independent review of a finished result is the job of `physics-referee`.

## Assessment

The checklist in [assessment.md](references/assessment.md) is worked through against the code and result files, not against the paper text, because the methods section and the code often disagree. For each uncertainty source, record whether it is represented, its size, how it was estimated, its correlation structure (point-to-point, common to a data set, common to all data sets), how it enters the fit, and whether it is in the quoted result. A mismatch between what the methods section claims and what the code does is a finding.

## Calibration checks

`scripts/uq_checks.py` needs NumPy and SciPy:

```bash
python3 scripts/uq_checks.py residuals fit.csv --data S --model S_fit --sigma dS --x E --group dataset --n-par 7
python3 scripts/uq_checks.py coverage heldout.csv --obs S --obs-err dS --pred S_pred --pred-err dS_pred
python3 scripts/uq_checks.py correlations covariance.csv --names E1 G_p1 G_g1 a_c
```

The `residuals` check gives χ²/ν with its p-value, the pull mean and width, a runs test, and a sliding-window scan for localised structure. The scan's p-value is calibrated against pure noise, so it accounts for searching many windows, and it catches a missed resonance or contaminant that a global χ² hides. It is run per data set with `--group`, because a good global χ² can hide one bad data set.

The `coverage` check compares predictions and their band with data not used in the fit, obtained by leaving one data set out or by fitting early runs and predicting later ones. The fraction within 1σ should be about 68%.

The `correlations` check flags |ρ| > 0.95 or a covariance that is not positive definite, which means the data do not separate those parameters. The remedy is to quote a combination, to fix one parameter with a stated reason, or to add data. A profile scan, χ² against the parameter with the others refitted, then tests the result: an asymmetric or flat profile means the Gaussian error is not the uncertainty.

On clean synthetic data about 3% of data sets raise some flag, since each test runs near the 1% level. A flag is therefore a reason to look, not a verdict, and the plotted residuals are inspected before concluding.

## Rules and their reasons

1. Errors are not tuned to the test. Inflating uncertainties until χ²/ν = 1 hides the problem the test found. If a scale factor is used, it is stated, given per data set, and the unscaled result is kept.
2. Held-out means held out. Data used to choose the model, the normalisation or the level scheme are not a coverage test, because the model was already adjusted to them.
3. Extrapolations are a separate class. Coverage inside the data range says nothing about S(0) or a rate outside it. The model dependence (channel radius, background poles, level assignments) is quoted separately from the fit uncertainty, since the fit covariance at one model does not contain it (assessment.md §3).
4. Correlated systematics are not statistics. A common normalisation error does not shrink with more points. Check that it was not divided by √N or added in quadrature per point, which is how it would shrink with the number of points in a fit (assessment.md §2).

## What to deliver

- An uncertainty table: source, size, correlation, how it was estimated, in the result or not.
- The calibration check outputs with plots of the pulls by region.
- Findings ranked by their effect on the conclusion, with the specific fix for each.
- What the quoted uncertainty does not cover.

Outputs are written to the user's project, never into the skill directory. `python3 scripts/selftest.py` must print PASS.
