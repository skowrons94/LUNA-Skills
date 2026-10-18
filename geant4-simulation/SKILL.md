---
name: geant4-simulation
description: Write, build, run and validate small Geant4 applications for nuclear-physics feasibility studies — environment and datasets (conda-forge), simple geometries and materials (polyethylene, borated PE, pressurised 3He), physics-list choice (EM options, neutron HP with thermal scattering, charged particles), sources (gun, GPS, Watt, AmBe, angular distributions), two-body reaction kinematics, scoring (captures, deposits, die-away times) and standard analyses (efficiency and flatness, time gates, dead time), with a validation ladder and a tested neutron-counter template. Use for a new detector or shielding simulation, or to audit one; use `underground-gamma-simulation` for LUNA-type gamma setups and `agata-simulation` for AGATA.
---
# Geant4 simulation

A simulation result is an input to a decision. Make it reproducible from a named configuration and seed, check it at the level it claims, and say which levels it has not reached. A run that completes proves only that it completes.

## Route the task

- **LUNA-type gamma-detection setups** (BGO, HPGe, in-beam (p,γ) or (α,γ), Doppler, bias, ROOT output of an existing application): `underground-gamma-simulation`.
- **AGATA** geometry, event files, PSA, tracking: `agata-simulation`.
- **Photopeak efficiency from calibration sources, summing corrections**: `efficiency-analysis`; use this skill only for the simulated response that enters it.
- **Rates, beam time, uncertainty budgets and decisions built on the simulation**: `proposal-analysis`; directory layout of studies, size policy and environments: `proposal-project` (references/tools-layout.md).
- Everything else, a new or small Geant4 application:
  - build, environment, datasets: [build-and-environment.md](references/build-and-environment.md);
  - geometry and materials: [geometry.md](references/geometry.md);
  - physics lists: [physics-lists.md](references/physics-lists.md);
  - sources: [sources.md](references/sources.md);
  - reaction kinematics: [kinematics.md](references/kinematics.md) and `scripts/kinematics.py`;
  - scoring and output: [scoring-and-output.md](references/scoring-and-output.md);
  - standard analyses: [analyses.md](references/analyses.md) and `scripts/counting.py`;
  - validation: [validation.md](references/validation.md) and `scripts/run_checked.py`.

## Template

[assets/neutron-counter/](assets/neutron-counter/README.md) is a minimal tested application: a moderated 3He counter with configurable geometry, an optional borated-PE shell and a point source (mono, Watt, thermal, histogram file or event list; isotropic or Legendre angular distribution), with gas-capture, deposit, die-away and capture-position scoring and one JSON summary per run. Copy it into `simulation/<study>/src/` of the project; build outside git; change the geometry through the messenger before editing the code.

## Non-negotiable boundaries

1. **Large software and data on a data disk.** Conda environments, Geant4 datasets, nuclear-data libraries, builds and run outputs never go on the system disk. Record the environment path and versions in the project's `docs/ENVIRONMENT.md`.
2. **Datasets must be shown to be found.** Run `scripts/check_g4_datasets.py` (with `--tsl` for thermal neutrons) in the shell that runs the job, and record the paths in the run manifest. Do not derive paths from `geant4-config --datasets`; package directory names can differ.
3. **Thermal neutrons need thermal scattering.** Any simulation in which neutrons thermalise in hydrogenous material uses thermal-scattering data for bound hydrogen (G4ThermalNeutrons and a matching material or element name), verified in the log. Free-gas hydrogen is a comparison case, never a result.
4. **Seeds are explicit and recorded.** Same seeds must reproduce the outputs; different seeds must give a different sample. Every batch gets its own seeds and its own run directory.
5. **Judge a run on its log and outputs, not its return code.** Fatal exceptions, overlaps, refused commands and missing outputs are failures; the number of generated events must match the request.
6. **Physics generated outside Geant4 is stated as such.** Reaction kinematics, angular distributions and source spectra fed in from files carry their provenance and assumptions (isotropy, thick target, missing correlations).
7. **Shared machines: cap the jobs.** Compile and run with an explicit job count chosen from the current load, at low priority (`nice`). Pilot first and estimate time and disk.

## Working method

1. State the observable (efficiency, rate, time distribution, spectrum), its required precision, and what decision it serves.
2. Start from the template or the smallest existing application; one study directory per question, one `REPORT.md` and one `results.json`.
3. Check the environment and datasets, build, run a pilot of 10³–10⁴ events through `run_checked.py` with explicit seeds, repeat with the same seeds, then with different seeds.
4. Climb the validation ladder as far as the claim requires; record each rung and what it does not prove.
5. Scale up with distinct seeds per batch; merge counts and weights, not ratios; report statistical and model uncertainties separately.
6. Put headline numbers in `results.json` with units, events, seeds, code revision and run directories; the proposal reads them through its numbers file.

## Scripts (standard library only)

```bash
python3 SKILL_DIR/scripts/selftest.py                       # pure-Python tests, must print PASS (no Geant4 needed)
python3 SKILL_DIR/scripts/check_g4_datasets.py --tsl        # datasets found? (exit 1 if not)
python3 SKILL_DIR/scripts/kinematics.py "13C(a,n)16O" --T1 5 --theta 0 90 --spectrum spec.csv
python3 SKILL_DIR/scripts/run_checked.py --out RUN --expect out/x_r0.json --json-min out/x_r0.json:gas_captures=1 \
  --nice 10 -- /path/to/app macro.mac --seeds 1 2
python3 SKILL_DIR/scripts/counting.py efficiency RUN/out/*.json
python3 SKILL_DIR/scripts/test_template.py --build-dir /data/scratch/ncounter-test --jobs 4   # needs Geant4
```

Replace `SKILL_DIR` with this skill directory. `test_template.py` builds the template and runs the smoke test (clean logs, captures > 0, same seeds reproduce, other seeds differ); it is separate from `selftest.py` because it needs a Geant4 installation.
