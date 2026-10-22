# Rate sensitivity studies

The question is usually one of these. *Which reactions control this observable at this site? How much would measuring reaction R to precision P reduce the model uncertainty of observable O?* The second question is the one a proposal needs. Answer the first only as a step toward it.

## Monte Carlo (`--mode mc`)

- **Convention.** Rates are lognormal: λ(T) = λ_med(T) · fu(T)^p, with one p ~ N(0,1) per sample and per rate group, constant in T (Iliadis et al. 2015, J. Phys. G 42, 034007, §3.1–3.2; the lognormal rate distribution itself is from Longland et al. 2010, Nucl. Phys. A 841, 1). A forward rate and its reverse form one group (Iliadis et al. 2015, §3). Sampling them independently would break detailed balance and inflate the spread. Putting branches in the same group is this skill's extension.
- **Which rates vary.** Only rates with an fu: STARLIB matches, table fu columns, explicit `uncertainty.fu`. Everything else is fixed and listed in `info.fixed`. A reaction absent from the ranking may be fixed, not unimportant. Check the list before saying a reaction does not matter.
- **Median vs recommended.** With `starlib.use: "uncertainty"` the network keeps REACLIB rates and borrows STARLIB's fu. Where the REACLIB rate lies outside STARLIB's 68 % band, the sampled distribution is shifted. Use `starlib.use: "rates"` for a self-consistent study, and `rates.py compare` to see where the two differ.
- **Reading the ranking.**
  - Spearman ρ between p and the observable (log-transformed when positive) measures monotonic influence. Its bootstrap interval shows sampling noise.
  - The noise threshold is the |ρ| a rate with no influence would exceed with 5 % probability after a Bonferroni correction over all varied groups. Rates below it are not distinguished from zero.
  - Variance share (β²/Var from regressing ln O on all p) is the fraction of the spread a rate explains, if effects are additive in ln λ. A linear R² well below 1 means interactions or non-linear response; then rely on ρ and look at scatter plots from `samples.csv`.
- **Sample size.** The noise floor of ρ is ~1/√N, so separating ρ = 0.1 effects needs N ≳ 1000. A ranking of the top few needs ~200–500. Report N and failed samples. A failed sample is recorded and never dropped silently.

## One-at-a-time (`--mode oat`)

Each group × and ÷ a factor f gives d ln O / d ln λ ≈ ln(O₊/O₋)/(2 ln f). It is fast and local. Choose f near the actual uncertainty (f = 2 overstates well-measured rates and understates unknown ones), and report f. OAT misses interactions and non-linear response. Use it to prune a large network before Monte Carlo, not as the final ranking.

## What a measurement buys (the proposal number)

1. Run Monte Carlo with the present uncertainties and record the observable's 68 % factor (`factor_68`).
2. Copy the configuration and set `uncertainty.fu` of the target rate to the projected uncertainty of the measurement (from `proposal-analysis` feasibility, at the temperatures that matter). Leave everything else as it was.
3. Rerun with the same seed and N, and compare `factor_68` and the target rate's variance share.

Quote the reduction together with the site conditions, N, the fixed-rate list and the observational uncertainty of the observable. A reduction from 1.40 to 1.35 is irrelevant if the observation is uncertain by a factor 2. Register the numbers as claims (`nuclear-research-project`) with the configuration and `summary.json` as evidence.

## Finding reactions nobody is looking at

A reaction is a candidate when its present uncertainty times its sensitivity is large *and* nothing in the literature already constrains it below the library's fu. The ranking supplies the first factor. The second needs a literature check (newer data than the library evaluation). Before proposing, check:

- the library label and year (`info.rates`);
- whether the uncertainty comes from an unmeasured resonance (an upper limit in the Gamow window: a lifetime, spectroscopic factor or ANC measurement may fix it);
- whether the effect survives a scan over the site's conditions and a stellar model.

Then hand the candidate to `azure2` (rate from R-matrix), `delta-beta-dsam` (widths from lifetimes) or `proposal-analysis` (feasibility).
