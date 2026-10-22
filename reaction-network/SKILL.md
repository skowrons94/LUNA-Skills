---
name: reaction-network
description: Run nuclear reaction networks with pynucastro for nucleosynthesis and rate-impact studies — one-zone burns at constant temperature and density or along a (t, T, rho) trajectory, rates from REACLIB, STARLIB (median and factor uncertainty) or a table (e.g. an AZURE2 reactionrates.out), detailed-balance reverse rates, isomer branches (26Al), screening, energy generation, Monte Carlo and one-at-a-time rate sensitivity with noise thresholds, what a measurement's precision buys for an observable, rate comparisons between libraries and fits to the REACLIB 7-parameter form. Use whenever a task asks how a reaction rate changes an abundance, a yield, an isotopic ratio or the energy generation, which reactions dominate an observable, or for putting a new or measured rate into a network; such impacts must be computed, not estimated from memory.
---
# Reaction network

A rate measured in the laboratory becomes an astrophysical statement only through a network calculation at stated conditions. Make that calculation reproducible from one configuration file, check that its rates are the ones you meant and that its numbers are converged, and say which questions a one-zone model cannot answer.

## Route the task

- **The rate itself** (R-matrix fit, S factor, extrapolation, AZURE2 rate integration): `azure2`. This skill starts from the rate table.
- **Stellar structure, mixing, trajectories from stellar models** (MESA): this skill post-processes their (t, T, ρ) output. A rate's impact on a star's evolution, rather than on burning at given conditions, needs the stellar model itself.
- **Proposal numbers** (projected precision, beam time, "what this measurement buys" as a decision): `proposal-analysis`, fed by the Monte Carlo here.
- **Evaluated neutron cross sections, MACS**: `evaluated-nuclear-data`.
- Everything else, a network calculation:
  - configuration format: [config.md](references/config.md);
  - rate conventions, screening, detailed balance, weak rates, isomers, one-zone limits: [physics.md](references/physics.md);
  - Monte Carlo and OAT sensitivity, reading a ranking, the measurement-impact recipe: [sensitivity.md](references/sensitivity.md);
  - validation ladder and review: [validation.md](references/validation.md).

## Non-negotiable boundaries

1. **Every rate that carries the conclusion is named**: library and label (REACLIB `il10`, STARLIB `mc10`) or table with provenance. `results.json` lists them in `network.rates`, with every substitution, so quote from there.
2. **Rates entering the network are bare.** The network screens. A rate fitted to data still containing laboratory electron screening is double-screened. Remove it upstream or state it.
3. **Forward and reverse stay consistent.** A replaced forward rate gets a detailed-balance reverse (the default), and in Monte Carlo both share one random variable. Keeping the library reverse is a recorded exception.
4. **Uncertainties are explicit.** Rates without an uncertainty factor are fixed. Report the fixed list with any ranking. Never assume a default factor silently; `default_fu` is logged on every use.
5. **Numbers are converged and resolved.** Run `--check-tolerance`. Never quote an observable flagged `UNRESOLVED` (abundance at the solver floor). Confirm completeness with `network.extend: 1` before quoting.
6. **One-zone results are conditional.** They hold for the stated (T, ρ, time, composition). For sites shaped by mixing or self-heating they screen candidate reactions; they are not the star's answer. Say which, every time.
7. **Isomers are not totals.** pynucastro's REACLIB has total ²⁶Al. Below ~0.15 GK split the isomer feeding with a `branch` and a sourced fraction, or state that the ²⁶Al value is a total.
8. **Large data stay outside the skill.** Rate libraries (STARLIB) live under `$NUCLEAR_DATA_DIR`. Parsed copies are cached in `~/.cache/reaction-network`, and source files are never modified.

## Working method

1. State the observable, the site and its conditions with a source, the precision that would matter, and the decision it serves.
2. Write the configuration in `studies/<question>/config.json` (template: [assets/config-template.json](assets/config-template.json)). Rate tables follow the `rate-table` contract (`T9,rate[,fu]`), trajectories the `thermo-trajectory` contract (`time_s,T_K,rho_cgs`). Check them with `analysis-chain/scripts/contracts.py check` and `scripts/trajectory.py check`.
3. Check the rates that matter: `scripts/rates.py compare` at the site temperatures.
4. Run `scripts/burn.py config.json --out run --check-tolerance`, then repeat with `network.extend: 1`.
5. For sensitivity: OAT to prune, then Monte Carlo with enough samples for the noise threshold you need. For a measurement's value, the two-run recipe in [sensitivity.md](references/sensitivity.md).
6. Put headline numbers in the study's `results.json` and register them as claims. Have `physics-referee` recompute them from the outputs.

## Scripts (Python with pynucastro, numpy, scipy)

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

Replace `SKILL_DIR` with this skill's directory. `netlib.py` (engine) and `build.py` (configuration to network) can be imported for custom studies. Prefer extending them over writing a second network.
