---
name: proposal-analysis
description: Build and stress-test the quantitative scientific case of a research proposal in experimental nuclear physics or nuclear astrophysics — feasibility (count rates, beam time, uncertainty budgets), Bayesian design across measurement types, pre-registered decision rules and power simulations, back-tests of evaluations, covariance treatment of shared systematics, posterior-sampling checks, and a simulated-review cycle. Use when a proposal's claims rest on calculations, or when auditing those calculations before submission; use `proposal-style` for the prose and `proposal-project` for the directory and registers.
---
# Proposal analysis

A panel funds a proposal it believes; a specialist believes only numbers that survive an hour of checking. Build every quantitative claim so that it would survive that hour, and state its limits before a referee does.

## Route the task

- **Feasibility** (rates, beam time, backgrounds, uncertainty budgets): [feasibility.md](references/feasibility.md).
- **Design and decision rules** (expected information gain across measurement types, Bayes-factor rules, failure criteria, power simulations with realistic stresses): [design-and-decisions.md](references/design-and-decisions.md). Skeleton: `scripts/power_skeleton.py`.
- **Back-tests of evaluations** (did quoted uncertainties cover later measurements?): [backtests.md](references/backtests.md). Skeleton: `scripts/backtest_skeleton.py`.
- **Shared systematics and covariances** (multiplicative nuisance parameters, Peelle's puzzle, dilution, within- versus cross-system correlations): [covariances.md](references/covariances.md). Demonstration: `scripts/peelle_demo.py`.
- **Posterior sampling checks** (importance-weight degeneracy, MCMC autocorrelation growth, quantile stability): [sampling-checks.md](references/sampling-checks.md). Helpers: `scripts/sampling_checks.py`.
- **Simulated review cycle** (generalist panel member, specialist referee, style editor; convergence; what reviewers may and may not change): [review-cycle.md](references/review-cycle.md).
- Before quoting any result, read [lessons.md](references/lessons.md): a checklist of failure modes that have each overturned a headline number.

R-matrix calculations themselves use `azure2`; detector response uses `underground-gamma-simulation` or `agata-simulation`; yields use `yield-analysis`.

## Non-negotiable boundaries

1. **No invented numbers, citations or commitments.** Every number comes from a script and a result file, or from a verified source with its location (page, table, line). A reference is cited only after its DOI or arXiv identifier has been resolved.
2. **Write the decision rule before computing the outcome.** Thresholds, selection rules and failure criteria are fixed in a dated file before the comparison. If a rule was stated after a first look, say so.
3. **Report what the analysis cannot show.** Small samples, selection, model dependence, unconverged chains and assumptions go next to the number they qualify, not in an appendix.
4. **Effects are quoted in units that matter.** Give the change of the observable or of its uncertainty (in per cent and in standard deviations), not only a relative change of a width.
5. **Reviewers advise; they do not supply numbers.** A number proposed by a (simulated) reviewer enters the text only after it has been recomputed and stored.

## Working method

1. State the physics question, the observable, the energy frame and units, the decision the measurement should inform, and what would count as failure.
2. Compute feasibility and design with the simplest model that captures the decision; check it against an independent estimate (analytic limit, exact-observable floor, a second sampler).
3. Simulate the planned analysis on pseudo-data, including realistic correlated errors and gross failures; report power, false-pass and wrong-decision rates.
4. Run the review cycle until the reviewers' remaining points are wording or applicant-only inputs; log every change in the decision register.
5. Run `scripts/selftest.py` after changing any helper; it must print PASS.

Write results to the proposal project (`analysis/results/`), never into the skill directory.
