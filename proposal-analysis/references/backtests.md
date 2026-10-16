# Back-tests of evaluations

Question: did the uncertainties quoted by an evaluation cover what was measured later?

## Selection

- State the selection rule before comparing, in words a referee can apply: which evaluations (and the tie-breaker when two were in force), which later measurements (independent of the evaluation's inputs), which quantity (S(0), S at a stated energy, a resonance strength, a rate at a stated temperature).
- Apply the rule to every candidate and keep an exclusion table with a reason for each exclusion (no recommended value with a quoted uncertainty; earlier value only an upper limit; the evaluation already used the later data; quantity not the same; value not verifiable in a primary source).
- Treat derived quantities consistently: if a ratio derived from evaluated rates is excluded for one reaction, exclude it for all.
- Report evaluation-to-evaluation pairs (one evaluation against its successor) separately; they share data and understate pulls.
- If a first look preceded the rule, say so and report sensitivity variants (alternative tie-breakers, excluded borderline cases).

## Statistics

- Pull = (later − earlier) / sqrt(σ_earlier² + σ_later²); report it as primary. The ratio (later − earlier)/σ_earlier exaggerates shifts when the later measurement is less precise.
- Report coverage at both 1σ and 2σ, each with its exact binomial probability under calibration, so that no threshold is chosen after the comparison. Coverage of the combined pull tests the earlier and later uncertainties together; a miscalibrated later measurement is indistinguishable from a miscalibrated evaluation.
- Root-mean-square pull is not a mean; give mean |pull| and median as well, and say which cases drive the result.
- Pairs that share a lineage (same evaluation group, same reference data) are not independent; a bootstrap over lineages needs more than a handful of lineages to give a meaningful interval.
- A small back-test motivates; only a pre-registered, outcome-blind selection over many pairs tests.

`scripts/backtest_skeleton.py` implements the pull, coverage and binomial probabilities with a synthetic self-test.
