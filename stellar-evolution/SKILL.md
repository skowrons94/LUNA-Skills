---
name: stellar-evolution
description: Set up, run and check MESA stellar-evolution models for nuclear-astrophysics questions: installing MESA and its SDK without admin rights, test-suite templates (solar, AGB and 13C pocket, massive stars, pair instability), changed or tabulated rates (e.g. from AZURE2, 26Al isomers), and solar neutrino fluxes or trajectories for one-zone networks. Use when a rate's effect on a star is needed (structure, lifetimes, core masses, surface or wind abundances), when the burning conditions of a star or phase are asked for (these come from a model, not from memory), or when MESA must be installed, run or debugged.
---
# Stellar evolution (MESA)

A reaction rate reaches an astronomical observable only through a star, that is, through its structure and timescales, its mixing, and what it ejects or emits. This skill measures that effect in a MESA model. You need the observable (core mass, lifetime, surface ratio, yield, neutrino flux), the star or phase, and an idea of the precision that would matter. You get runs from a maintained template that differ by one named change, a check that each run reached its goal, and a comparison of the effect with the numerical and physics noise of the phase, through resolution and physics-degeneracy checks. Every run is reproducible from its spec, and its history and profile output, temperature–density histories and compositions can be handed to a one-zone network.

## Where this fits

- Comes from: rate tables from `r-matrix` or `reaction-network`, in the `rate-table` contract, converted with `mesa.py rate-table`; the candidate rates that passed the one-zone screen of `reaction-network`; the Population III starting composition from `big-bang-nucleosynthesis`; the model pairs (phase, mass, Z, mixing) that `stellar-observables` specifies for a rate-to-observable question.
- Goes to: trajectories and compositions for `reaction-network` (`mesa.py trajectory`, `mesa.py composition`, contract `thermo-trajectory`); surface, wind and grain values for interpretation in `stellar-observables`.
- Checked by: `scripts/selftest.py`, `mesa.py check-run` and the validation ladder of [validation.md](references/validation.md); `physics-referee` recomputes the comparison numbers.

Rate impact at fixed conditions, rankings over many rates and Monte Carlo belong to `reaction-network`, which is cheap; this skill gives the conditions and handles the few rates that pass that screen. The rate itself, from an R-matrix fit, an extrapolation or a rate integration, belongs to `r-matrix`, which hands it over in the `rate-table` contract. What physics sets a surface, wind or grain observable, which phase and levers matter, and how to compare a model with observed stars or grains belong to `stellar-observables`. The references of this skill hold:

- installation and the environment file: [install.md](references/install.md);
- templates (including carbon ignition), inlists, threads, output, run checks: [running.md](references/running.md);
- networks, reaction names, rate factors, rate tables, caches, screening, ²⁶Al isomers: [nuclear.md](references/nuclear.md);
- mixing prescriptions (thermohaline with the C_t ↔ `thermohaline_coeff` mapping and its resolution trap: scale the composition-term smoothing with the mesh, rotation, overshoot, third dredge-up, hot-bottom burning, ¹³C pocket) and how to cross them with rate changes: [mixing.md](references/mixing.md);
- solar models, neutrino fluxes, the B23/SF-III reference models and `ssm.py`: [solar.md](references/solar.md);
- trajectories and compositions for `reaction-network`: [trajectories.md](references/trajectories.md);
- validation ladder: [validation.md](references/validation.md).

## Rules and their reasons

1. MESA, its SDK and its caches live outside the skill, and `$MESA_DIR` is not edited. Cases are copied to a run directory, because the test-suite cases are maintained, run with every release and document their physics choices (running.md). Never edit the installation. The MESA and SDK versions are recorded, because defaults change between versions (nuclear.md); `run.py` writes them to `manifest.json`.
2. A rate study compares runs that differ only in the rate, with the same template, inputs, version and resolution. Two changes in one run cannot be separated afterwards.
3. A changed rate needs a run-local rate cache, set with `rates_cache_dir = './rates_cache'`, because the shared cache does not know that the rate changed (nuclear.md). The reaction must also be explicit in the net, since a rate factor on a reaction the net lacks does nothing. Confirm the reaction in the run's reaction list.
4. MESA interpolates rate tables linearly in rate against T8. Tabulated rates are therefore resampled densely with `mesa.py rate-table`, onto 2000 log-spaced points (nuclear.md). The tables contain bare rates, because MESA applies the screening itself.
5. MESA's built-in rates are not all modern. Sixteen charged-particle reactions, ¹⁴N(p,γ) and ¹²C(α,γ) among them, are hard-coded NACRE (r26.04.1). The difference is not small: the NACRE ¹⁴N(p,γ) is 1.68× the LUNA-based REACLIB rate at solar-core temperature and doubles the solar CNO neutrino fluxes ([nuclear.md](references/nuclear.md)). Current rates are therefore supplied as tables for every rate the conclusion depends on.
6. A run is judged by its termination code and its energy error, both reported by `mesa.py check-run`, not by the existence of output. A run that stopped at a solver limit has failed, even if it wrote histories and profiles, because it did not reach the physical stopping condition of its case (running.md).
7. The effect must exceed the noise. A result shows the resolution check and, before it claims an astrophysical impact, the effect of the phase's dominant mixing or mass-loss uncertainty (validation rungs 2 and 4). Rung 4 is the one most often skipped, and a referee will ask for it (validation.md).
8. Long runs are planned. Pilot with a small `max_model_number`, estimate the wall time, and run with `nice` and an explicit `OMP_NUM_THREADS`. Ask before runs longer than about an hour or several in parallel on a shared machine, because memory caps a grid as well as cores, and an overcommitted grid is killed by the OOM killer, not slowed (running.md).

## Method

1. State the observable (core mass, lifetime, surface ratio, yield, neutrino flux), the star or phase, and what precision would matter.
2. Pick the template ([running.md](references/running.md)) and write a spec for `run.py` with the template, inlist edits, extra columns and files. Nominal and varied runs differ only in the rate entry.
3. Pilot, then run, then check with `mesa.py check-run`. Compare runs at the same evolutionary phase with `mesa.py compare` or `final`.
4. Climb the validation ladder as far as the claim needs. For thermohaline mixing, the resolution rung refines the composition-term smoothing together with the mesh, and the profiles are checked for non-mixing gaps ([mixing.md](references/mixing.md#thermohaline-runs-and-the-mesh-refine-the-smoothing-with-the-mesh)). Hand trajectories to `reaction-network` for cheap extensions.
5. Put the headline numbers in the study's `results.json` with the run directories and manifests, and register them as claims.

## Scripts

The scripts need Python 3 with numpy.

```bash
python3 SKILL_DIR/scripts/selftest.py                                   # must print PASS (no MESA needed)
python3 SKILL_DIR/scripts/run.py run spec.json                          # setup + mk + rn + check + manifest
SKILL_DIR/scripts/detach.sh grid --env ENVFILE -- bash run_grid.sh          # long jobs: own systemd unit, survives the session
SKILL_DIR/scripts/memlog.sh memlog.tsv 60                                 # RSS / swap / zram per run vs model number
ls specs/*.json | xargs -P 18 -I{} SKILL_DIR/scripts/memgate.sh 5 -- python3 SKILL_DIR/scripts/run.py run {}   # grid: cores x memory
python3 SKILL_DIR/scripts/run.py restart spec.json --photo x8100 --set inlist_x:controls:key=value   # resume with overrides
python3 SKILL_DIR/scripts/mesa.py check-run runs/solar_nominal
python3 SKILL_DIR/scripts/mesa.py set inlist_solar star_job "special_rate_factor(1)=1.1d0"
python3 SKILL_DIR/scripts/mesa.py rate-table rates/mg25pg.csv --out r_mg25_pg_al26_lu.dat --reaction r_mg25_pg_al26
python3 SKILL_DIR/scripts/mesa.py neutrinos runs/solar_nominal/final.profile --json neutrinos.json
python3 SKILL_DIR/scripts/ssm.py budget --model GS98 S114=0.084 --what-if S114=0.03   # B23/SF-III solar models
python3 SKILL_DIR/scripts/ssm.py compare --model GS98 --profile RUN/final.profile --neutrinos RUN/neutrinos.json
python3 SKILL_DIR/scripts/mesa.py trajectory LOGS/history.data --center --out traj.csv
python3 SKILL_DIR/scripts/mesa.py composition LOGS/profile5.data --mass 0.0 --out X0.json
python3 SKILL_DIR/scripts/mesa.py compare runA/LOGS/history.data runB/LOGS/history.data star_age log_L
```

Replace `SKILL_DIR` with this skill's directory.

## What to deliver

- The specs, one run directory per configuration with its `manifest.json`, and the `mesa.py check-run` result of each run.
- The comparison at a stated evolutionary phase, with the resolution check and, for an impact claim, the dominant-lever check.
- The list of rates replaced by tables, with their sources.
- The headline numbers in `results.json`, registered as claims.
