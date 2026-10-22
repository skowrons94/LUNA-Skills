# Validation ladder

Climb as far as the claim needs and record each rung in the study's `REPORT.md`. A run that finishes proves only that it finishes.

| Rung | Check | How | Proves | Does not prove |
|---|---|---|---|---|
| 0 | Engine | `scripts/selftest.py` prints PASS | ydot, Jacobian and energy equal pynucastro; decays, steady flow, detailed balance, tables, trajectories, fits, sampling | that your network or rates are right |
| 1 | Rates | `rates.py compare NAME --starlib … [--table …]` for every rate the claim rests on, at the site temperatures | the rate in the network is the one you meant (library, label, table, no unit slip) | that the evaluation is right |
| 2 | Convergence | `burn.py --check-tolerance`; no observable `UNRESOLVED` | the numbers are not solver noise | completeness |
| 3 | Completeness | set `network.extend: 1` and rerun; observables unchanged at the precision quoted | no missing nucleus or channel feeds the observable | that the site model is right |
| 4 | Reference result | reproduce a published one-zone result with the same inputs (a test case from the paper whose rates you change, or a textbook steady state) within its quoted precision | setup, units and conventions match the literature | that the literature model is adequate |
| 5 | Site robustness | scan the site's T, ρ, duration (`T_scale`, several trajectories) | the conclusion does not hinge on one condition | mixing, feedback |
| 6 | Stellar model | the conclusion survives in a stellar model with the changed rate (MESA) or a published model-based sensitivity study | the one-zone screening transfers to the star | — |

Rungs 0–3 are cheap and always required before a number leaves the study. Rung 4 is required before comparing with a published sensitivity. Rungs 5–6 are required before claiming an astrophysical impact in a paper or proposal.

## Review

The agent that ran the study does not approve its conclusion alone. Give `physics-referee` the configuration, `results.json` or `summary.json` and the claim, and ask it to recompute the key ratios from `abundances.csv` or `samples.csv`. Give it the claim, not the reasoning that led to it.
