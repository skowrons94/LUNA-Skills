---
name: proposal-analysis
description: Build and stress-test the quantitative scientific case of a research proposal in experimental nuclear physics or nuclear astrophysics: feasibility (count rates, beam time, uncertainty budgets), Bayesian design across measurement types, pre-registered decision rules and power simulations, back-tests of evaluations, covariances of shared systematics, posterior-sampling checks and a simulated-review cycle. Use when a proposal's claims rest on calculations, or when auditing them before submission; use `proposal-style` for the prose and `proposal-project` for the directory and registers.
---
# Proposal analysis

A panel funds a proposal it believes, while a specialist believes only numbers that survive an hour of checking. This skill builds every quantitative claim of a proposal so that it would survive that hour, and states its limits before a referee does. You need the physics question, the observable and the decision the measurement should inform, with the facility's specifications and the current evaluation. You get feasibility and design numbers in result files, each with the script that made it, its independent cross-check and its stated limits.

## Where this fits

- Comes from: R-matrix calculations from `azure2`; detector response from `underground-gamma-simulation` or `agata-simulation` and other Geant4 work from `geant4-simulation`; yields from `yield-analysis`; stopping powers and target profiles from `target-analysis`; detection efficiency and summing from `efficiency-analysis`; rate impacts from the Monte Carlo of `reaction-network`. Back-tests and sampler diagnostics are routed here from `uncertainty-audit`.
- Goes to: `analysis/results/` of a `proposal-project`, and from there through its numbers file to the text written with `proposal-style`.
- Checked by: `scripts/selftest.py`, which must print PASS; the simulated review cycle, in which the `physics-referee` and `citation-checker` subagents act as specialist reviewers.

## Tasks

- Feasibility (rates, beam time, backgrounds, uncertainty budgets): [feasibility.md](references/feasibility.md).
- Design and decision rules (expected information gain across measurement types, Bayes-factor rules, failure criteria, power simulations with realistic stresses): [design-and-decisions.md](references/design-and-decisions.md). Skeleton: `scripts/power_skeleton.py`.
- Back-tests of evaluations, which ask whether quoted uncertainties covered later measurements: [backtests.md](references/backtests.md). Skeleton: `scripts/backtest_skeleton.py`.
- Shared systematics and covariances (multiplicative nuisance parameters, Peelle's puzzle, dilution, within- versus cross-system correlations): [covariances.md](references/covariances.md). Demonstration: `scripts/peelle_demo.py`.
- Posterior sampling checks (importance-weight degeneracy, MCMC autocorrelation growth, quantile stability): [sampling-checks.md](references/sampling-checks.md). Helpers: `scripts/sampling_checks.py`.
- Simulated review cycle (generalist panel member, specialist referee, style editor; convergence; what reviewers may and may not change): [review-cycle.md](references/review-cycle.md).
- Before quoting any result, read [lessons.md](references/lessons.md), a checklist of failure modes that have each overturned a headline number.

## Rules and their reasons

1. No invented numbers, citations or commitments. Every number comes from a script and a result file, or from a verified source with its location (page, table, line). A reference is cited only after its DOI or arXiv identifier has been resolved. A value "quoted by" an evaluation may turn out to be a single measurement, which is why the primary source is read (lessons.md).
2. The decision rule is written before the outcome is computed. Thresholds, selection rules and failure criteria are fixed in a dated file before the comparison, because a comparison without a stated rule invites the reply "selection" (lessons.md). If a rule was stated after a first look, say so.
3. Report what the analysis cannot show. Small samples, selection, model dependence, unconverged chains and assumptions go next to the number they qualify, not in an appendix.
4. Effects are quoted in units that matter. Give the change of the observable or of its uncertainty (in per cent and in standard deviations), not only a relative change of a width. A modest effect stated honestly is more credible than an inflated one (lessons.md).
5. Reviewers advise; they do not supply numbers. A number proposed by a (simulated) reviewer enters the text only after it has been recomputed and stored, since a reviewer may also be wrong in its re-derivation (review-cycle.md).

## Method

1. State the physics question, the observable, the energy frame and units, the decision the measurement should inform, and what would count as failure.
2. Compute feasibility and design with the simplest model that captures the decision. Check it against an independent estimate (analytic limit, exact-observable floor, a second sampler).
3. Simulate the planned analysis on pseudo-data, including realistic correlated errors and gross failures, and report power, false-pass and wrong-decision rates. Simulations with independent Gaussian errors only would overstate the power (design-and-decisions.md).
4. Run the review cycle until the reviewers' remaining points are wording or applicant-only inputs, and log every change in the decision register.
5. Run `scripts/selftest.py` after changing any helper (requirements: `requirements.txt`). It must print PASS, also with `--seed` set to a few other values.

## What to deliver

- Result files in the proposal project (`analysis/results/`), never in the skill directory, each with the script that made it.
- For each quoted number, its cross-check and the limits stated next to it.
- Entries in the decision register for every number that changed.
