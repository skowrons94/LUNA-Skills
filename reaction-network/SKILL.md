---
name: reaction-network
description: Run nuclear reaction networks with pynucastro for nucleosynthesis: one-zone burns at fixed T and rho or along a (t, T, rho) trajectory, rates from REACLIB, STARLIB or a table (e.g. an AZURE2 reactionrates.out), screening, detailed balance, 26Al isomer branches, Monte Carlo and one-at-a-time sensitivity, library comparisons and REACLIB 7-parameter fits. Use whenever a task asks how a rate changes an abundance, yield, isotopic ratio or energy generation at given conditions, which reactions dominate an observable, what a measurement's precision buys, or how to put a measured rate into a network; such impacts must be computed, not estimated from memory.
---
# Reaction network

A rate measured in the laboratory becomes an astrophysical statement only through a network calculation at stated conditions. This skill makes that calculation with pynucastro, reproducible from one configuration file, and checks that its rates are the ones meant and that its numbers are converged. You need the observable, the site with its temperature, density, duration and initial composition taken from a source, and the rates that matter as library labels or as tables with an uncertainty factor. You get abundances, ratios and energy generation at those conditions, rate comparisons between libraries, sensitivity rankings with noise thresholds, and the reduction in an observable's spread that a measurement of given precision buys. A one-zone model cannot answer every question, and the results say which ones it leaves open.

## Where this fits

- Comes from: rate tables from `azure2` (`rates.py from-azure`) or from REACLIB and STARLIB, in the `rate-table` contract; trajectories and compositions from `stellar-evolution` (`mesa.py trajectory`, `mesa.py composition`), in the `thermo-trajectory` contract; MACS from `evaluated-nuclear-data`.
- Goes to: `stellar-evolution` for the few rates that pass the one-zone screen; `stellar-observables` for the local equilibrium and transient values; `proposal-analysis` for what a measurement buys; `big-bang-nucleosynthesis` for tables made with `rates.py from-sfactor`; candidate reactions to `azure2` or `delta-beta-dsam`.
- Checked by: `scripts/selftest.py` and the validation ladder of [validation.md](references/validation.md); `physics-referee` recomputes the headline numbers; claims are registered with `nuclear-research-project`.

## Neighbouring tasks and references

The rate itself, from an R-matrix fit, an S factor, an extrapolation or an AZURE2 rate integration, belongs to `azure2`; this skill starts from the rate table. Stellar structure, mixing and trajectories come from stellar models (MESA). This skill post-processes their (t, T, ρ) output, whereas a rate's impact on a star's evolution, rather than on burning at given conditions, needs the stellar model itself. Proposal numbers, such as the projected precision, the beam time or "what this measurement buys" as a decision, belong to `proposal-analysis`, which is fed by the Monte Carlo here. Evaluated neutron cross sections and MACS belong to `evaluated-nuclear-data`. Everything else is a network calculation, documented in:

- configuration format: [config.md](references/config.md);
- rate conventions, screening, detailed balance, weak rates, isomers, one-zone limits: [physics.md](references/physics.md);
- Monte Carlo and OAT sensitivity, reading a ranking, the measurement-impact recipe: [sensitivity.md](references/sensitivity.md);
- validation ladder and review: [validation.md](references/validation.md).

## Rules and their reasons

1. Every rate that carries the conclusion is named, by library and label (REACLIB `il10`, STARLIB `mc10`) or as a table with its provenance. A number whose rates are not named cannot be checked against the rate that was meant (validation rung 1). `results.json` lists the rates in `network.rates`, with every substitution, so quote them from there.
2. Rates entering the network are bare, because the network applies plasma screening itself. A rate fitted to data that still contain laboratory electron screening is therefore double-screened. Remove the laboratory screening upstream or state that it is there.
3. Forward and reverse rates stay consistent. A replaced forward rate gets a detailed-balance reverse, the default, because a forward rate without its reverse breaks equilibrium wherever the reverse matters (physics.md). In Monte Carlo both share one random variable, since sampling them independently would break detailed balance and inflate the spread (sensitivity.md). Keeping the library reverse is a recorded exception.
4. Uncertainties are explicit. Rates without an uncertainty factor are fixed, and the fixed list is reported with any ranking, because a reaction absent from the ranking may be fixed rather than unimportant. Never assume a default factor silently: an assumed factor shapes the ranking as much as a measured one does, so `default_fu` is logged on every use.
5. Numbers are converged and resolved. Run `--check-tolerance`, so that the numbers are known not to be solver noise. Never quote an observable flagged `UNRESOLVED`, which marks an abundance at the solver floor. Before quoting, confirm completeness with `network.extend: 1`, which shows that no missing nucleus or channel feeds the observable.
6. One-zone results are conditional. They hold for the stated (T, ρ, time, composition), because the model has no mixing and no feedback. For sites shaped by mixing or self-heating they screen candidate reactions and are not the star's answer. Say which, every time.
7. Isomers are not totals. pynucastro's REACLIB has total ²⁶Al, which decays with the ground-state half-life. Below ~0.15 GK the ground state and the isomer do not communicate thermally, so a total rate overestimates the ground-state yield (physics.md). Split the isomer feeding with a `branch` and a sourced fraction, or state that the ²⁶Al value is a total.
8. Large data stay outside the skill. Rate libraries (STARLIB) live under `$NUCLEAR_DATA_DIR`. Parsed copies are cached in `~/.cache/reaction-network`, and source files are never modified.

## Method

1. State the observable, the site and its conditions with a source, the precision that would matter, and the decision it serves.
2. Write the configuration in `studies/<question>/config.json`, starting from the template [assets/config-template.json](assets/config-template.json). Rate tables follow the `rate-table` contract (`T9,rate[,fu]`), trajectories the `thermo-trajectory` contract (`time_s,T_K,rho_cgs`). Check them with `analysis-chain/scripts/contracts.py check` and `scripts/trajectory.py check`.
3. Check the rates that matter with `scripts/rates.py compare` at the site temperatures.
4. Run `scripts/burn.py config.json --out run --check-tolerance`, then repeat with `network.extend: 1`.
5. For sensitivity, prune with OAT, then run Monte Carlo with enough samples for the noise threshold you need. For the value of a measurement, follow the two-run recipe in [sensitivity.md](references/sensitivity.md).
6. Put the headline numbers in the study's `results.json` and register them as claims. Have `physics-referee` recompute them from the outputs.

## Scripts

The scripts need Python with pynucastro, numpy and scipy.

```bash
python3 SKILL_DIR/scripts/selftest.py                                    # must print PASS
python3 SKILL_DIR/scripts/burn.py config.json --out run --check-tolerance
python3 SKILL_DIR/scripts/sensitivity.py config.json --out mc --mode mc --n 500 --seed 1 --jobs 4
python3 SKILL_DIR/scripts/sensitivity.py config.json --out oat --mode oat --factor 2
python3 SKILL_DIR/scripts/rates.py compare "mg25(p,g)al26" --starlib $NUCLEAR_DATA_DIR/STARLIB/starlib.dat
python3 SKILL_DIR/scripts/rates.py from-azure output/reactionrates.out --out rates/mg25pg.csv
python3 SKILL_DIR/scripts/rates.py fit rates/mg25pg.csv --rate "mg25(p,g)al26" --out fit.json --reaclib-out fit.reaclib
python3 SKILL_DIR/scripts/starlib.py show $NUCLEAR_DATA_DIR/STARLIB/starlib.dat "p n14 o15"
python3 SKILL_DIR/scripts/trajectory.py check traj.csv
```

Replace `SKILL_DIR` with this skill's directory. `netlib.py` (engine) and `build.py` (configuration to network) can be imported for custom studies. Extending them is preferred over writing a second network.

## What to deliver

- The study's `config.json` and run outputs, with `results.json` listing every rate and substitution in `network.rates`.
- The convergence check and the `network.extend: 1` rerun, with no observable `UNRESOLVED`.
- For a sensitivity study, the ranking with N, the noise threshold and the fixed-rate list.
- The headline numbers registered as claims, with the `physics-referee` recomputation.
