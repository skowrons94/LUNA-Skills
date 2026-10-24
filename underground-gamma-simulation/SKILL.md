---
name: underground-gamma-simulation
description: Build, extend and validate the user's existing Geant4/ROOT simulation of gamma-ray detection setups at low-background (underground) accelerator laboratories such as LUNA, with BGO or HPGe detectors and in-beam (p,γ) or (α,γ) reactions. Use for geometry and detectors, reaction channels and kinematics, Doppler effects, cross-section bias and weights, nuclear-data edits, ROOT observables and reproducible runs of that application; a new general Geant4 application (neutron counters, shielding) is `geant4-simulation`, the official AGATA code is `agata-simulation`.
---

# Underground gamma simulation

An in-beam gamma-ray measurement at an underground accelerator needs a detector model for its efficiencies, summing and angular effects, and that model is the user's own Geant4/ROOT application in one of several variants. This skill produces reproducible, checked simulations with the user's actual variant: it runs a small baseline, extends geometry, generators, reactions or output, and edits nuclear data in private overrides. You need the path of the checkout and its build environment, the observable, and the description of the setup, beam or source and target. You get run directories with manifests, logs and `result.root`, the checks that were passed, and a statement of the scientific limits that remain. Throughout this skill, `APP` stands for the application's executable name and `APP.cc` for its main source file in the user's checkout. Successful execution, detector-response checks and experimentally validated physics are separate levels, and none implies the next.

## Where this fits

- Comes from: the user's application and macros; a physical target-layer model from `target-analysis` (model-and-fitting.md describes the conversion); cross sections, level and branching data from evaluated nuclear data (`evaluated-nuclear-data`), a cited measurement or the user's explicit model.
- Goes to: `efficiency-analysis`, as the validated detector model where the total efficiency is not measured; `proposal-analysis`, for the detector response in a feasibility case.
- Checked by: `scripts/test_physics_checks.py`, the smoke tests of [validation-record.md](references/validation-record.md), the production acceptance list in [physics-and-analysis.md](references/physics-and-analysis.md), and `physics-referee` before an efficiency or yield is quoted.

For a new or general Geant4 application (neutron counters, moderators, shielding, generic sources and validation), use `geant4-simulation` instead; AGATA work belongs to `agata-simulation`.

## Establish the variant

Read the project's instructions, `APP.cc`, `CMakeLists.txt`, the relevant messenger implementations and a nearby working macro. The upstream repository required authentication during skill development, so the local source was not verified against current upstream, and no answer should imply that it was.

On the user's machine there is a tested BGO checkout plus separate HPGe and 19F+p variants; ask for their paths. These are discovery hints, not portable dependencies, and the source and data specified by the user are the ones used. BGO, HPGe and six- or twelve-segment variants are not conflated, because storage, channel loops and event selection differ between them (setup-and-interface.md).

Read [setup-and-interface.md](references/setup-and-interface.md) when building or preparing macros, and [validation-record.md](references/validation-record.md) for the actual test coverage and the local defects. Original research files are preserved, and builds and runs go to separate directories. Record the source identity, build settings, executable, macros, actual dataset paths and relevant data-file hashes. `scripts/preflight.py --source CODE_DIR --main APP.cc --data-file FILE` emits a JSON inventory; its presence checks do not certify data completeness or compatibility.

## Method: a small, explicit baseline

1. Establish the requested observable, detector geometry and materials, projectile or source isotope, energy and frame, beam or source distribution, target composition, and normalisation. Infer these from the project inputs where possible, and ask only for scientifically consequential missing information.
2. Use a macro from the same variant. [assets/cs137-smoke.mac](assets/cs137-smoke.mac) is a stationary-source baseline for the tested local BGO variant; check the validation record before using it elsewhere. Verify command spelling, parameter units and allowed states against its messenger source. Geometry and physics are configured before `/run/initialize`, GPS and decay controls in their supported states, and output before `/run/beamOn`.
3. Start with roughly 100–1000 events, a new output directory and explicit random seeds. In the tested variant `-s` only creates an alias, so add `/random/setSeeds` before the run. Multiple `-s` values do not create independent batches.
4. Run one reviewed, flat macro through the checked runner:

   ```bash
   python3 SKILL_DIR/scripts/run_checked.py --exe /absolute/build/APP \
     --macro /absolute/macros/example.mac --out /absolute/new-run \
     --events 1000 --seeds 12345 67890 --timeout 300
   ```

   Replace `SKILL_DIR` with this skill directory. Initialise the chosen Geant4/ROOT environment and the project nuclear-data overrides in the calling shell first. The helper supplies `-m` and `-s`, redirects ROOT output to `result.root`, replaces the event count and random seeds, and captures a manifest and log. It rejects includes, loops, shell commands and aliases by design, so flatten and review these first. Other relative input paths must resolve inside the fresh run directory or be made absolute, and any other output commands are reviewed too.
5. Check the completed-event summary, the warnings, ROOT integrity and schema, and nonzero relevant signals. A return code of zero is insufficient, because `APP.cc` ignores the status of failed commands and returns zero (setup-and-interface.md). For the tested BGO schema:

   ```bash
   python SKILL_DIR/scripts/inspect_root.py /absolute/new-run/result.root \
     --expected-entries 1000 --require-hits
   ```

   Use a Python with PyROOT. `--expected-entries` is appropriate only for all-event storage. The helper assumes BGO `Tree1/Edep` in keV, so adapt the analysis to other schemas. Its Cs-window count is diagnostic, not an efficiency estimate.
6. Repeat with the same seeds to check that the observables reproduce, and change the seeds to check independence. Compare branches, not whole ROOT file hashes, because the metadata differ. Run explicit overlap checks and resolve material or geometry problems before interpreting results. Then perform the physics checks in [physics-and-analysis.md](references/physics-and-analysis.md).

## Extending the simulation

An extension is traced along the complete path from producer to output, with the guide for its part:

- [Geometry and new detectors](references/geometry-and-detectors.md): solids and materials, coordinates and placements, messengers, sensitive detectors, hit collections, channel mapping, event readout and geometry checks.
- [ROOT output and observables](references/root-output.md): define the row and quantity, add persistent storage and branches, populate and reset buffers correctly, update event selection, save provenance and validate the stored values.
- [Event generation](references/event-generation.md): GPS configuration, custom primary generators, external event inputs, seeds and source–geometry coupling.
- [Geometry scans](references/geometry-scans.md): detector distance and angle conventions, target surfaces, dead layers, rebuilds and uncertainty scans.
- [Different reactions](references/reaction-workflows.md): choose capture, inelastic or prescribed-product routes, and update material, cross section, final states and channel diagnostics together.
- [Kinematics and Doppler effects](references/kinematics-and-doppler.md): exact two-body reference calculations, excited-state recoil, CM and lab angles, lifetime and stopping effects, and local implementation traps.
- [Cross-section bias and weights](references/bias-and-weights.md): select a rare-event strategy, distinguish physical tables from bias, preserve history weights and validate absolute or coincidence observables.

Interface guidance stays specific to the inspected checkout. Code changes are rebuilt, and the new behaviour is tested together with an existing baseline in isolated runs. The bundled smoke tests validate the recorded BGO variant; they do not certify an untested detector, generator or ROOT schema.

## Independent physics checks

`scripts/physics_checks.py` needs only Python's standard library. It provides `two-body` (masses and lab beam energy from JSON), `doppler` (fixed recoil speed and lab angle) and `slab` (analytic single-process bias) reference calculations; the units and limits are in the corresponding guides. The synthetic equal-mass example runs with:

```bash
python3 SKILL_DIR/scripts/physics_checks.py two-body SKILL_DIR/assets/synthetic-two-body.json
python3 SKILL_DIR/scripts/test_physics_checks.py
```

The example uses artificial masses and is not a nuclear reaction dataset. These checks complement transport tests: they neither modify the application nor supply missing nuclear data. Kinematics is compared on emitted-particle truth, and detector comparisons on deposited or reconstructed energy.

## Nuclear-data files

Data files sometimes need to be changed for the requested reaction, because cross sections, capture-state populations, gamma branching, level schemes, angular coefficients or decay data may be missing or unsuitable. Read [data-files.md](references/data-files.md) when choosing or editing these inputs. Guide the user to the exact file and the model that consumes it, verify units and coupled level indices, create a private override, record the change and its evidence, restart the simulation, and demonstrate that the modified data are actually used. The restart is needed because the models cache data, so a file changed while the application runs may not change the loaded tables (data-files.md). Never mistake changing a macro for changing the underlying nuclear model, or treat an unexplained numerical scale as a physical cross section: the examined `proton/cap9` values of 5.3e-6 correspond to 5.3e16 barns under the local reader.

## Rules for reaction and production work

1. Read [physics-and-analysis.md](references/physics-and-analysis.md) before preparing reaction inputs, changing nuclear data, applying bias factors or reporting efficiencies or yields. Trace the selected cross-section and final-state implementations, because selecting an isotope or enabling a process does not prove that the required reaction data exist.
2. Scale up only after the small baseline and the relevant validation pass. Each batch gets distinct explicit seeds and output paths, and the runtime is estimated from the pilot.
3. This local executable uses a serial `G4RunManager`, so there is no thread option to invent.
4. Generated-event denominators, event selection and weighting are preserved across merges, because a selected tree cannot supply an absolute-efficiency denominator by itself (physics-and-analysis.md). Statistical uncertainty is reported separately from geometry, nuclear-data and detector-model uncertainty.
5. Any test-only source patch is described explicitly. Never claim that the smoke tests establish experiment-quality accuracy: they are execution and response tests, not experimental validation (validation-record.md).

## What to deliver

- The actual build and run outcome, with inputs, seeds, event counts and output locations.
- The meaningful checks that were passed and those that were not run.
- For data edits, the private files, environment overrides, diff and hashes, and before/after results.
- The remaining scientific limitations.
