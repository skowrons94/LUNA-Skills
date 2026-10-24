---
name: geant4-simulation
description: Write, build, run and validate small Geant4 applications for nuclear-physics feasibility studies, with a validation ladder and a tested neutron-counter template (pressurised 3He, polyethylene, borated PE). Use for a new detector or shielding simulation or its audit: conda-forge environment and datasets, physics lists (EM options, neutron HP with thermal scattering, charged particles), sources (gun, GPS, Watt, AmBe), two-body kinematics, captures, deposits, die-away times, efficiency and flatness, time gates, dead time. LUNA-type gamma setups use `underground-gamma-simulation`, the official AGATA code `agata-simulation`.
---
# Geant4 simulation

A simulation result is an input to a decision, such as whether a counter is efficient enough or a shield thick enough, and it is only as good as the checks behind it. This skill writes or adapts a small Geant4 application for such a question, runs it reproducibly from a named configuration and seed, and checks it at the level the claim requires. You need the observable (efficiency, rate, time distribution, spectrum), its required precision and the decision it serves, a Geant4 environment with its datasets, and a description of the geometry and source. You get a study directory with the application, its run manifests, a `REPORT.md` and a `results.json` in which every number states the highest validation rung it has reached. A run that completes proves only that it completes.

## Where this fits

- Comes from: the geometry and source of the planned measurement; cross sections for generated reaction products from evaluated or measured data (`evaluated-nuclear-data`), CM angular distributions from `azure2`, stopping tables from `target-analysis`.
- Goes to: `efficiency-analysis`, for the simulated response that enters its `efficiency-curve`; `proposal-analysis`, for rates, beam time, uncertainty budgets and decisions, through the proposal's numbers file; `delta-beta-dsam`, for simulated events.
- Checked by: `scripts/selftest.py` (must print PASS), `scripts/test_template.py`, the validation ladder in [validation.md](references/validation.md), and `physics-referee` before a number is quoted.

Three Geant4 skills exist, and the right one depends on the application. LUNA-type gamma-detection setups with an existing application (BGO, HPGe, in-beam (p,γ) or (α,γ), Doppler, bias, ROOT output) belong to `underground-gamma-simulation`. AGATA geometry, event files, PSA and tracking belong to `agata-simulation`. Photopeak efficiency from calibration sources and summing corrections belong to `efficiency-analysis`, which uses this skill only for the simulated response. The directory layout of studies, the size policy and the environments of a proposal follow `proposal-project` (references/tools-layout.md). Everything else, a new or small Geant4 application, is done here with these guides:

| Task | Guide |
|---|---|
| build, environment, datasets | [build-and-environment.md](references/build-and-environment.md) |
| geometry and materials | [geometry.md](references/geometry.md) |
| physics lists | [physics-lists.md](references/physics-lists.md) |
| sources | [sources.md](references/sources.md) |
| reaction kinematics | [kinematics.md](references/kinematics.md) and `scripts/kinematics.py` |
| scoring and output | [scoring-and-output.md](references/scoring-and-output.md) |
| standard analyses | [analyses.md](references/analyses.md) and `scripts/counting.py` |
| validation | [validation.md](references/validation.md) and `scripts/run_checked.py` |

## Template

[assets/neutron-counter/](assets/neutron-counter/README.md) is a minimal tested application: a moderated 3He counter with configurable geometry, an optional borated-PE shell and a point source. The source can be mono, Watt, thermal, a histogram file or an event list, with an isotropic or Legendre angular distribution. The application scores gas captures, deposits, die-away times and capture positions, and writes one JSON summary per run. Copy its contents into `simulation/<study>/` of the project, which gives `CMakeLists.txt`, `src/` and `macros/` at study level, and build outside git. The geometry is changed through the messenger before the code is edited.

## Method

The method moves from the smallest running case to the claimed precision, and each step adds one thing that can be checked.

1. State the observable, its required precision, and the decision it serves, because the precision sets the number of events and the decision sets the rung of the validation ladder that must be reached.
2. Start from the template or the smallest existing application. Use one study directory per question, with one `REPORT.md` and one `results.json`.
3. Check the environment and datasets, build, and run a pilot of 10³–10⁴ events through `run_checked.py` with explicit seeds. Repeat it with the same seeds, then with different seeds.
4. Climb the validation ladder as far as the claim requires, and record each rung together with what it does not prove.
5. Scale up with distinct seeds per batch. Merge counts and weights, not ratios, because averaging the ratios of unequal batches weights them wrongly (analyses.md). Report statistical and model uncertainties separately.
6. Put the headline numbers in `results.json` with units, events, seeds, code revision and run directories; the proposal reads them through its numbers file.

## Rules and their reasons

1. Large software and data go on a data disk. Conda environments, Geant4 datasets, nuclear-data libraries, builds and run outputs never go on the system disk, because the `geant4` package alone pulls several GB of datasets and a full system disk stops every process on the machine (build-and-environment.md). The environment path and the versions are recorded in the project's `docs/ENVIRONMENT.md`.
2. Datasets must be shown to be found. Run `scripts/check_g4_datasets.py`, with `--tsl` for thermal neutrons, in the shell that runs the job, and record the paths in the run manifest. A batch job that only prepends the environment's `bin` to `PATH` has no dataset variables. Paths are not derived from `geant4-config --datasets`, because package directory names can differ from the paths compiled into the build.
3. Thermal neutrons need thermal scattering. Any simulation in which neutrons thermalise in hydrogenous material uses thermal-scattering data for bound hydrogen, through G4ThermalNeutrons and a matching material or element name, verified in the log. Free-gas hydrogen is a comparison case, never a result: in the template counter it raised the capture efficiency by about 20 % relative, and in water it gave a diffusion length of about 3.7 cm instead of 2.7 cm (physics-lists.md).
4. Seeds are explicit and recorded. The same seeds must reproduce the outputs, and different seeds must give a different sample. Every batch gets its own seeds and its own run directory, because batches that share seeds are not independent samples and their merged uncertainty would be wrong.
5. A run is judged on its log and outputs, not on its return code. Fatal exceptions, overlaps, refused commands and missing outputs are failures, and the number of generated events must match the request. An overlap makes the navigation, and hence every result, undefined even when the run completes (geometry.md); `run_checked.py` applies these criteria.
6. Physics generated outside Geant4 is stated as such. Reaction kinematics, angular distributions and source spectra fed in from files carry their provenance and assumptions, such as isotropy, a thick target or missing correlations. An angle-integrated spectrum with an isotropic source, for example, loses the correlation between energy and direction and is acceptable only for a detector that surrounds the source symmetrically (kinematics.md).
7. Jobs on shared machines are capped. Compile and run with an explicit job count chosen from the current load, at low priority (`nice`). A pilot comes first, to estimate time and disk.

## Scripts (standard library only)

```bash
python3 SKILL_DIR/scripts/selftest.py                       # pure-Python tests, must print PASS (no Geant4 needed)
python3 SKILL_DIR/scripts/check_g4_datasets.py --tsl        # are the datasets found? (exit 1 if not)
python3 SKILL_DIR/scripts/kinematics.py "13C(a,n)16O" --T1 5 --theta 0 90 --spectrum spec.csv
python3 SKILL_DIR/scripts/run_checked.py --out RUN --expect out/x_r0.json --json-min out/x_r0.json:gas_captures=1 \
  --require-log 'Element TS_H_of_' --nice 10 -- /path/to/app macro.mac --seeds 1 2
python3 SKILL_DIR/scripts/counting.py efficiency RUN/out/*.json
python3 SKILL_DIR/scripts/test_template.py --build-dir /data/scratch/ncounter-test --jobs 4   # needs Geant4
```

Replace `SKILL_DIR` with this skill directory. `test_template.py` builds the template and runs the smoke test: clean logs, captures > 0, same seeds reproduce, other seeds differ. It is separate from `selftest.py` because it needs a Geant4 installation.

## What to deliver

- The study directory `simulation/<study>/` with the application source, macros and the run directories with their manifests.
- `results.json` with each headline number, its units, events, seeds, code revision, run directories and highest validation rung.
- `REPORT.md` with the checks behind each number, the statistical uncertainty and the model variations, saying plainly when a number rests only on rungs 1–3.
- The environment path and versions in the project's `docs/ENVIRONMENT.md`.
