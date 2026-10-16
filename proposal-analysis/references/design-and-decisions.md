# Design and decision rules

## Expected information gain across measurement types

- Use the posterior of the current evaluation as the prior. For each candidate measurement (a cross section at an energy, a transfer-reaction ANC, a spin observable, an absolute yield), simulate pseudo-data from posterior draws with the candidate's realistic uncertainty, including the model error of indirect methods, and compute the expected posterior width of the quantity that matters (a rate, an amplitude sign, a ratio) or the expected information gain.
- Include today's knowledge of every input in the prior (for example published ANC ranges); otherwise a measurement is credited with information the literature already has.
- Importance reweighting of posterior samples is cheap but optimistic when the effective sample size collapses (see sampling-checks.md). Cross-check with a second estimator: a regression on the observables (cross-fitted) and the residual width with the observables known exactly, which no noisy measurement can beat in expectation. A regression residual is an upper estimate of that floor (see sampling-checks.md).
- Report a range between estimators rather than a single optimistic number, and calibrate each estimator on a null observable (pure noise should give no gain).
- Check the design result against what the evaluation actually depends on: a design built on an incomplete evaluation (for example one that omits a reaction channel) can rank measurements in the opposite order.

## Pre-registered decision rules

- Decide between hypotheses with a Bayes factor threshold fixed in advance (for example 100), and report the fractions of simulated experiments that decide right, wrong or not at all under each hypothesis. State the priors of the parameters that distinguish the hypotheses and report the decision fractions for at least one alternative prior width; a Bayes factor computed with a very wide prior favours the simpler hypothesis automatically.
- Separate the evidence that is model-free (new data compared directly with earlier data at the same energies and under matched conditions) from the evidence that depends on a model extrapolation; state which test governs which claim if they disagree.
- Calibrate instruments independently of the hypothesis under test: never calibrate on, or gate on, the data point where the hypotheses differ most.
- Quote separations from posterior samples (predictive spread included), not from best fits only.

## Power simulations with realistic stresses

A power analysis that only simulates independent Gaussian errors will overstate power. Simulate at least:

- clustered errors: a random effect per campaign and an error shared by all items of a run;
- gross errors that affect a whole run (a wrong efficiency file or geometry), not only isolated outliers;
- campaign-level shifts of realistic size (a fraction of σ, not several σ);
- under-reported uncertainties for coverage endpoints;
- a non-zero true bias for equivalence tests;
- uncertainty in thresholds estimated from a small development set (draw the threshold per trial).

For each endpoint report the power and the false-pass rate, and report the probability that all endpoints pass together. Count gross-error endpoints per run (or per cluster), not per item, and use cluster-aware bounds. If a confirmation step is part of the protocol, simulate it with its own errors; a confirmation that knows the truth is not a simulation. Report the simulated false-pass rate of the complete protocol, outlier rejection included; it can exceed the nominal α, so calibrate α, the critical value or the margin by simulation. `scripts/power_skeleton.py` shows the structure and the calibration.
