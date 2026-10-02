# Setup and interface: source-verified local variant

The observations below come from the local BGO code examined on 2026-09-25, not from a fetched upstream revision. Recheck when using another checkout.

## Build

Dependencies: shared Geant4 libraries, ROOT 6, CMake and a compatible C++ compiler. The local CMake exposes `WITH_GEANT4_UIVIS`, recursively collects `.cc`/`.hh` and produces `SimLUNA`. Prefer a build directory outside the source tree because of recursive file collection. The existing `build.sh` deletes its old build; use explicit CMake commands instead.

```bash
cmake -S /path/to/code -B /path/to/new-build \
  -DGeant4_DIR=/chosen/prefix/lib/cmake/Geant4 \
  -DROOT_DIR=/chosen/root/cmake -DWITH_GEANT4_UIVIS=OFF
cmake --build /path/to/new-build -j 4
```

Find actual package paths before using this example. `OFF` avoids requesting all UI drivers, but this source still constructs `G4VisExecutive`; it is not proof of a fully visualization-free link. Use the same dependency environment for build and run.

On the development Mac, the active Conda `main` environment supplied Geant4 11.2.2 and ROOT 6.34.04. An isolated build succeeded with `/usr/bin/clang`, `/usr/bin/clang++` and `-DCMAKE_EXE_LINKER_FLAGS=`; the previously built executable failed with duplicate `LC_RPATH`. Rebuild in an isolated directory rather than patching installed libraries. An older local Geant4 install named `11.0.4` failed configuration on a XercesC dependency mismatch and had stale dataset paths. Directory names do not prove a usable installation.

Geant4's generated `geant4.sh` may require sourcing from its own directory under zsh; bash supports its self-location logic. Inspect the environment afterwards. Do not indiscriminately source a different Geant4 installation over an already selected build.

## Data

Read the project's launch script and physics source. Standard Geant4 datasets are necessary but may lack LUNA-specific additions. For this local setup the project overrides are:

| Variable | Directory relative to project `data/` | Role |
|---|---|---|
| `G4PARTICLEXSDATA` | `G4PARTICLEXS4.0` | Custom capture/inelastic cross sections |
| `G4LEVELGAMMADATA` | `PhotonEvaporation5.7` | Level and gamma-cascade data |
| `G4RADIOACTIVEDATA` | `RadioactiveDecay5.6` | Decay data |
| `G4RADIATIVECAPTURE` | `RadiativeCapture` | Custom capture populations/angular coefficients |
| `G4PARTICLEHPDATA` | `G4TENDL1.4` | Particle HP database |
| `G4LENDDATA` | `LEND_GND1.3_ENDF.BVII.1` | LEND database |

These names are observed paths, not a universal version recipe. Preserve standard datasets from the chosen runtime, and deliberately override project data. Check existence, applicable nuclides and formats, not just exported variable names. Record all `G4*DATA` paths and `G4RADIATIVECAPTURE`; hash files relevant to the simulated reaction. Avoid copying large dataset trees unnecessarily.

## Interface pitfalls

- Batch invocation: `SimLUNA -m input.mac -s 12345`. Omitting `-s` in this variant reaches `stoi("")`; arguments are consumed as pairs without robust validation. Do not probe it with an invented `--help` flag.
- `-s` expands `/control/alias seed VALUE`; it never calls the random engine directly. Use `/random/setSeeds 12345 67890` explicitly before `/run/beamOn`.
- Output command is exactly `/analysis/filename` (lowercase `n`). Older presentations show different spelling; follow the installed messenger.
- `AnalysisManager` opens outputs with `RECREATE`. Existing results can be overwritten. Many supplied macros use `/workdir/rootfiles/SimLUNA.root`, and the default is a historic cluster path. Create the parent directory or use a fresh run-local filename.
- `SimLUNA.cc` ignores the return status of `ApplyCommand` and returns zero. Inspect logs for interrupted batches, unknown commands, invalid states and failed output creation.
- `/DetectorConstruction/Physics S` selects source geometry/generation; `R` selects reaction generation. These flags are not substitutes for physics-list configuration.
- Source mode re-applies `/DetectorConstruction/SourcePos` to the GPS position for every event. Editing only `/gps/pos/centre` will not move the source in this variant.
- The supplied Cs macro was observed to generate ions at 1000 keV by default. Explicitly configure radioactive ions at rest (`/gps/ene/mono 0 keV`), ion Z/A and angular/source distribution. For long-lived calibration sources, verify the supported radioactive-decay time threshold; supplied macros use `/process/had/rdm/thresholdForVeryLongDecayTime 1.0e+60 year` after initialization.
- `/analysis/CapFragIonA`, etc., select analysis bookkeeping; they do not define a nuclear reaction or target.
- Macros contain copied comments naming unrelated reactions. Read active commands and implementations, not comments alone.

## Geometry changes

Follow `DetectorConstruction` → component `Construct()` → sensitive detector → hit → `EventAction` → `AnalysisManager`. Check names and copy numbers at every step. A change from six to twelve BGO segments must update storage, zeroing loops, detector selection, noise treatment, multiplicity and event-selection logic together. A null sensitive-volume lookup can crash initialization. Out-of-bounds hit storage can silently corrupt physics results.

Use `/geometry/test/run` after initialization in a separate diagnostic macro. In this local BGO component, turning on its internal `checkOverlaps` flag also constructs extra test placements; do not use that flag as a harmless check without reviewing the implementation.

Additional local findings: `TargetBackingThickness` is accepted by a messenger but the holder implementation hard-codes 0.25 mm. Verify geometry code before claiming a macro scan changes backing thickness. The target centre used `GetTargetPosition()+thickness/2`, embedding it in the backing. For the tested beam direction and holder, the corrected reaction layer is placed in `WorldLog` at `SourceThickness-thickness/2`, just upstream of the backing. Moving it upstream while keeping it a daughter of the holder instead protruded outside the mother solid. In source mode the layer is omitted so it does not overlap the source holder. This is a variant-specific correction, not a universal coordinate convention.
