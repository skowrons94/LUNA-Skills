# Neutron-counter template

A minimal, generic Geant4 application: a moderator box (polyethylene or water, hydrogen with thermal scattering), an axial source channel, a ring of 3He proportional tubes and an optional borated-polyethylene shell, with a point neutron source. One source file, serial run manager, no visualisation. Copy its contents into `simulation/<study>/` (giving `CMakeLists.txt`, `src/` and `macros/` at study level) and change it there; the numbers in the macros are placeholders, not a design.

## Build

`SKILL_DIR` below is the `geant4-simulation` skill directory.

```bash
# activate the Geant4 environment (conda: `conda activate ENV`; its activation scripts set G4*DATA)
python3 SKILL_DIR/scripts/check_g4_datasets.py --tsl         # must report "ok": true
cmake -S . -B /data/scratch/ncounter-build -DCMAKE_BUILD_TYPE=Release
cmake --build /data/scratch/ncounter-build -j 4          # cap the jobs on shared machines
```

Keep the build directory outside git (a scratch area on the data disk, or a git-ignored `build/`). With conda compilers, pass `-DCMAKE_CXX_COMPILER=$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-c++` (or the platform equivalent) so that the compiler matches the Geant4 libraries.

## Run

```bash
cd /data/runs/new-run-dir
/data/scratch/ncounter-build/ncounter /data/scratch/ncounter-build/macros/smoke.mac --seeds 12345 67890
# --seeds is required (non-negative integers; the macro must not set /random/ state)
# options: --phys NAME, an HP list: QGSP_BIC_HP (default), FTFP_BERT_HP, Shielding, or an _HPT variant
#          (QGSP_BIC_HPT, FTFP_BERT_HPT, Shielding_HPT), which already includes thermal scattering;
#          non-HP lists are refused · --no-tsl (free-gas hydrogen, for comparison only; refused with _HPT)
```

The program refuses to start if `G4NEUTRONHPDATA` or its `ThermalScattering/` directory is missing, if seeds are not given on the command line, if the macro sets random-engine state, if the physics list is not an HP list, or if the run manager is not serial (e.g. forced by `G4FORCE_RUN_MANAGER_TYPE`). The seeds and the run-manager type are written into every JSON summary. `/random/setSeeds` failing is fatal.

| Macro | Purpose |
|---|---|
| `macros/smoke.mac` | 3000 events, 1 MeV point source, eight tubes: completes, no overlaps, captures > 0, same seeds reproduce |
| `macros/diffusion.mac` | thermal point source in a 2 m water block without tubes: ⟨r²⟩ of absorption points = 6 L², mean absorption time = 1/(vΣ_a) (analytic checks) |
| `macros/energy_scan.mac` | one run per source energy plus a Watt spectrum: efficiency against energy and flatness |

## Commands

Geometry (before `/run/initialize`; with units): `/nc/geo/moderator PE|water`, `modX modY modZ`, `modDensity`, `holeR` (0 = no channel), `nTubes`, `ringR`, `ringPhase`, `tubeR`, `tubeWall`, `tubeActive`, `gasPressure`, `gasTemperature`, `bpeThick` (0 = none), `bpeBoron` (mass fraction), `bpeDensity`. Overlaps abort the run.

Source: `/nc/gun/spectrum mono|watt|thermal|hist|list`, `energy`, `wattA` (MeV), `wattB` (1/MeV), `kT`, `file`, `position`, `a2`, `a4` (W(θ) = 1 + a2 P2 + a4 P4 about +z; coefficients giving W < 0 anywhere are fatal; ignored by `list`, which carries its own directions).
- `hist` file: `E_low_MeV,E_high_MeV,weight` per line, sampled uniformly within each bin (use fine bins for steep spectra).
- `list` file: `E_MeV,ux,uy,uz[,weight]`, read in order; weights propagate to every tally. When more events are requested than rows, rows are reused (warning `nc013`, `list_wrapped: true` in the JSON) and the events are no longer independent: give at least as many rows as events. `scripts/kinematics.py --events` and `--spectrum` write both formats.

Output: `/nc/out/dir`, `tag`, `threshold` (per-tube deposit for a count), `csv true` (one row per event with a gas capture). Each `/run/beamOn` writes `DIR/TAG_rN.json` with the configuration, seeds, Geant4 version, physics list, TSL flag, generated events, Σw and Σw², gas captures (3He(n,p)t identified by its proton and triton secondaries) with Σw², counts above threshold with Σw², captures per tube, first-capture time histogram and mean, and the neutron absorptions anywhere (any hadronic end without an outgoing neutron) with their mean r² from the source and mean time. Strings are JSON-escaped.

## Build test

```bash
python3 SKILL_DIR/scripts/test_template.py --build-dir /data/scratch/ncounter-test --jobs 4
```

It checks the datasets, builds, runs the smoke macro three times through `run_checked.py` and requires: clean logs, outputs present, gas captures > 0, identical outputs for identical seeds, different outputs for different seeds.

Recorded on one machine (Geant4 11.2.2 from conda-forge, GCC 14, QGSP_BIC_HP + G4ThermalNeutrons): build without warnings (also with `-Wall -Wextra -Wshadow`); smoke test PASS in about 15 s per run; `diffusion.mac` gave a mean absorption time of 206 µs (1/(vΣ_a) ≈ 205 µs for thermal neutrons in water) and L ≈ 2.7 cm for water with thermal scattering and L ≈ 3.7 cm with `--no-tsl`, the free-gas treatment of hydrogen inflating ⟨r²⟩ by almost a factor two; with 3 × 10⁴ events of `smoke.mac`, `--no-tsl` raised the capture efficiency from about 0.20 to 0.24 and shortened the mean capture time by about 6 %. A 3000-event smoke run has a statistical uncertainty of about 0.007 on the efficiency, so it does not resolve such differences. These numbers describe the template and that installation only; they validate nothing about another geometry.

## Extending

- New detector or material: add it in `Detector::Construct`, keep `Place()` (overlap check) for every placement, and expose dimensions through the messenger rather than editing constants.
- New observable: accumulate it in `Event`/`Run`, reset it in `BeginOfEventAction`/`BeginOfRunAction`, and write it to the JSON with its unit in the key name.
- Macros: CMake re-copies an edited macro into `build/macros/` at the next build; or pass the source macro path.
- Multi-threading: switch to `G4RunManagerType::Default` only after moving the static accumulators into thread-local objects merged in the run action (G4Accumulable); the serial template is deliberate.
