---
name: stellar-evolution
description: Install, set up, run and validate MESA stellar-evolution models for nuclear-astrophysics questions — the MESA SDK on macOS or Linux without admin rights, test-suite cases as templates (solar model, low-mass and AGB stars, 13C pocket, massive stars to collapse, carbon ignition, pair instability), networks and reaction names, rate factors and tabulated rates (e.g. from AZURE2) with run-local rate caches, 26Al isomer species, run checks, history and profile output, solar neutrino fluxes from per-cell rates, trajectories and compositions for one-zone networks, and resolution and physics-degeneracy checks. Use when a reaction rate's effect on a star (structure, lifetimes, core masses, surface or wind abundances, neutrino fluxes) is needed, when temperature–density histories or burning conditions of a star or phase are asked for (these must come from a model, not from memory), when a network needs a trajectory or composition from a stellar model, or when MESA must be installed, run or debugged.
---
# Stellar evolution (MESA)

A rate change matters to astronomy through a star: its structure, timescales, mixing and what it ejects or emits. Run that star from a maintained template with one named change, check that the run reached its goal and that the effect is larger than the numerical and physics noise of the phase, and keep every run reproducible from a spec.

## Route the task

- **Rate impact at fixed conditions, rankings over many rates, Monte Carlo**: `reaction-network` (cheap). Use this skill for the conditions and for the few rates that pass that screen.
- **The rate itself** (R-matrix, extrapolation, rate integration): `azure2`. Hand it over in the `rate-table` contract.
- Everything here:
  - installation and the environment file: [install.md](references/install.md);
  - templates, inlists, threads, output, run checks: [running.md](references/running.md);
  - networks, reaction names, rate factors, rate tables, caches, screening, ²⁶Al isomers: [nuclear.md](references/nuclear.md);
  - solar models and neutrino fluxes: [solar.md](references/solar.md);
  - trajectories and compositions for `reaction-network`: [trajectories.md](references/trajectories.md);
  - validation ladder: [validation.md](references/validation.md).

## Non-negotiable boundaries

1. **MESA, its SDK and caches live outside the skill and outside `$MESA_DIR` edits.** Copy cases to a run directory. Never edit the installation. Record the MESA and SDK versions (`run.py` writes them to `manifest.json`).
2. **One change per comparison.** A rate study compares runs that differ only in the rate (same template, inputs, version, resolution). Two changes in one run cannot be separated afterwards.
3. **A changed rate gets a run-local cache** (`rates_cache_dir = './rates_cache'`) and a net in which the reaction is explicit. A factor on a reaction the net lacks does nothing. Confirm it in the run's reaction list.
4. **Tabulated rates are resampled densely** (`mesa.py rate-table`). MESA interpolates tables linearly in rate vs T8. Rates are bare (MESA screens).
5. **Judge a run by its termination code and energy error** (`mesa.py check-run`), not by the existence of output. A solver-limit termination is a failed run.
6. **The effect must exceed the noise.** Show the resolution check, and before claiming astrophysical impact, the effect of the phase's dominant mixing or mass-loss uncertainty (validation rungs 2 and 4).
7. **Long runs are planned.** Pilot with a small `max_model_number`, estimate the wall time, run with `nice` and an explicit `OMP_NUM_THREADS`, and ask before runs longer than about an hour or several in parallel on a shared machine.

## Working method

1. State the observable (core mass, lifetime, surface ratio, yield, neutrino flux), the star or phase, and what precision would matter.
2. Pick the template ([running.md](references/running.md)) and write a spec for `run.py` (template, inlist edits, extra columns, files). Nominal and varied runs differ only in the rate entry.
3. Pilot, then run, then `mesa.py check-run`; compare runs at the same evolutionary phase with `mesa.py compare` or `final`.
4. Climb the validation ladder as far as the claim needs. Hand trajectories to `reaction-network` for cheap extensions.
5. Put the headline numbers in the study's `results.json` with the run directories and manifests, and register them as claims.

## Scripts (Python 3 with numpy)

```bash
python3 SKILL_DIR/scripts/selftest.py                                   # must print PASS (no MESA needed)
python3 SKILL_DIR/scripts/run.py run spec.json                          # setup + mk + rn + check + manifest
python3 SKILL_DIR/scripts/mesa.py check-run runs/solar_nominal
python3 SKILL_DIR/scripts/mesa.py set inlist_solar star_job "special_rate_factor(1)=1.1d0"
python3 SKILL_DIR/scripts/mesa.py rate-table rates/mg25pg.csv --out r_mg25_pg_al26_lu.dat --reaction r_mg25_pg_al26
python3 SKILL_DIR/scripts/mesa.py neutrinos runs/solar_nominal/final.profile --json neutrinos.json
python3 SKILL_DIR/scripts/mesa.py trajectory LOGS/history.data --center --out traj.csv
python3 SKILL_DIR/scripts/mesa.py composition LOGS/profile5.data --mass 0.0 --out X0.json
python3 SKILL_DIR/scripts/mesa.py compare runA/LOGS/history.data runB/LOGS/history.data star_age log_L
```

Replace `SKILL_DIR` with this skill's directory.
