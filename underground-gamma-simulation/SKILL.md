---
name: underground-gamma-simulation
description: Build, extend and validate SimLUNA Geant4/ROOT simulations for LUNA. Use for geometry and detectors, reaction channels and kinematics, Doppler effects, cross-section bias and weights, nuclear-data edits, ROOT observables and reproducible runs.
---

# SimLUNA

Produce reproducible, checked simulations using the user's actual SimLUNA variant. Separate successful execution, detector-response checks, and experimentally validated physics; none implies the next.

## Establish the variant

Read the project's instructions, `SimLUNA.cc`, `CMakeLists.txt`, relevant messenger implementations, and a nearby working macro. The upstream repository is <https://baltig.infn.it/LUNA/simluna-open>. It required authentication during skill development; do not imply the local source was verified against current upstream.

On this user's machine, a tested starting point is `/Users/kuba/Desktop/LUNA/Simulations/SimLUNA`, with other variants under `SimLUNA_HPGe` and `19F + p`. These are discovery hints, not portable dependencies. Use the source and data specified by the user. Do not conflate BGO, HPGe or six/twelve-segment variants.

Read [setup-and-interface.md](references/setup-and-interface.md) when building or preparing macros, and [validation-record.md](references/validation-record.md) for actual test coverage and local defects. Preserve original research files; use a separate build and run directory. Record source identity, build settings, executable, macros, actual dataset paths and relevant data-file hashes. `scripts/preflight.py --source CODE_DIR --data-file FILE` emits a JSON inventory; its presence checks do not certify data completeness or compatibility.

## Run a small, explicit baseline

1. Establish the requested observable, detector geometry/materials, projectile or source isotope, energy/frame, beam/source distribution, target composition, and normalization. Infer these from project inputs where possible; ask only for scientifically consequential missing information.
2. Use a macro from the same variant. [assets/cs137-smoke.mac](assets/cs137-smoke.mac) is a stationary-source baseline for the tested local BGO variant; check the validation record before using it elsewhere. Verify command spelling, parameter units and allowed states against its messenger source. Configure geometry and physics before `/run/initialize`, GPS/decay controls in their supported states, and output before `/run/beamOn`.
3. Start with roughly 100–1000 events, a new output directory and explicit random seeds. In the tested variant, `-s` only creates an alias; add `/random/setSeeds` before the run. Do not assume multiple `-s` values create independent batches.
4. Use the checked runner for one reviewed, flat macro:

   ```bash
   python3 SKILL_DIR/scripts/run_checked.py --exe /absolute/build/SimLUNA \
     --macro /absolute/macros/example.mac --out /absolute/new-run \
     --events 1000 --seeds 12345 67890 --timeout 300
   ```

   Replace `SKILL_DIR` with this skill directory. Initialize the chosen Geant4/ROOT environment and project nuclear-data overrides in the calling shell first. The helper supplies `-m` and `-s`, redirects ROOT output to `result.root`, replaces the event count and random seeds, and captures a manifest/log. It intentionally rejects includes, loops, shell commands and aliases; flatten and review these first. Other relative input paths must resolve inside the fresh run directory or be made absolute. Review any other output commands too.
5. Check the completed-event summary, warnings, ROOT integrity/schema and nonzero relevant signals. A return code of zero is insufficient. For the tested BGO schema:

   ```bash
   python SKILL_DIR/scripts/inspect_root.py /absolute/new-run/result.root \
     --expected-entries 1000 --require-hits
   ```

   Use a Python with PyROOT. `--expected-entries` is appropriate only for all-event storage. Adapt analysis to other schemas; the helper assumes BGO `Tree1/Edep` in keV. Its Cs-window count is diagnostic, not an efficiency estimate.
6. Repeat with the same seeds to check observable reproducibility; change seeds to check independence. Compare branches, not whole ROOT file hashes (metadata differs). Run explicit overlap checks and resolve material/geometry problems before interpreting results. Then perform the physics checks in [physics-and-analysis.md](references/physics-and-analysis.md).

## Extend the simulation

Choose the relevant implementation guide and trace the complete producer-to-output path:

- [Geometry and new detectors](references/geometry-and-detectors.md): solids/materials, coordinates and placements, messengers, sensitive detectors, hit collections, channel mapping, event readout and geometry checks.
- [ROOT output and observables](references/root-output.md): define the row/quantity, add persistent storage and branches, populate/reset buffers correctly, update event selection, save provenance and validate actual stored values.
- [Event generation](references/event-generation.md): GPS configuration, custom primary generators, external event inputs, seeds and source/geometry coupling.
- [Geometry scans](references/geometry-scans.md): detector distance/angle conventions, target surfaces, dead layers, rebuilds and uncertainty scans.
- [Different reactions](references/reaction-workflows.md): choose capture, inelastic or prescribed-product routes; update material, cross section, final states and channel diagnostics together.
- [Kinematics and Doppler effects](references/kinematics-and-doppler.md): exact two-body reference calculations, excited-state recoil, CM/lab angles, lifetime/stopping effects and local implementation traps.
- [Cross-section bias and weights](references/bias-and-weights.md): select a rare-event strategy, distinguish physical tables from bias, preserve history weights and validate absolute or coincidence observables.

Keep interface guidance specific to the inspected checkout. Rebuild code changes and test the new behavior plus an existing baseline in isolated runs. The bundled smoke tests validate the recorded BGO variant; they do not certify an untested detector, generator or ROOT schema.

## Independent physics checks

`scripts/physics_checks.py` needs only Python's standard library. It provides `two-body` (masses and lab beam energy from JSON), `doppler` (fixed recoil speed and lab angle), and `slab` (analytic single-process bias) reference calculations. Read the corresponding guides above for units and limits. Run the synthetic equal-mass example:

```bash
python3 SKILL_DIR/scripts/physics_checks.py two-body SKILL_DIR/assets/synthetic-two-body.json
python3 SKILL_DIR/scripts/test_physics_checks.py
```

The example uses artificial masses and is not a nuclear reaction dataset. These checks complement transport tests; they neither modify SimLUNA nor supply missing nuclear data. Use emitted-particle truth for kinematics and deposited/reconstructed energy for detector comparisons.

## Nuclear-data files

Data files sometimes need to be changed for the requested reaction: cross sections, capture-state populations, gamma branching, level schemes, angular coefficients or decay data may be missing or unsuitable. Read [data-files.md](references/data-files.md) when choosing or editing these inputs. Guide the user to the exact file and consuming model, verify units and coupled level indices, create a private override, record the change and evidence, restart the simulation, and demonstrate the modified data are actually used. Never mistake changing a macro for changing the underlying nuclear model, or treat an unexplained numerical scale as a physical cross section.

## Reaction and production work

Read [physics-and-analysis.md](references/physics-and-analysis.md) before preparing reaction inputs, changing nuclear data, applying bias factors or reporting efficiencies/yields. Trace the selected cross-section and final-state implementations; selecting an isotope or enabling a process does not prove the required reaction data exist.

Scale up only after the small baseline and relevant validation pass. Give each batch distinct explicit seeds and output paths; estimate runtime from the pilot. This local executable uses serial `G4RunManager`; do not invent a thread option. Preserve generated-event denominators, event selection and weighting across merges. Report statistical uncertainty separately from geometry, nuclear-data and detector-model uncertainty.

Finish with the actual build/run outcome, inputs and seeds, event counts, output locations, meaningful checks, and remaining scientific limitations. Describe any test-only source patch explicitly. Never claim that the smoke tests establish experiment-quality accuracy.
