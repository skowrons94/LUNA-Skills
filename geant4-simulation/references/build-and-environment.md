# Building and environment

## Install (conda-forge)

```bash
conda create -p /data/disk/envs/g4 -c conda-forge geant4 cmake cxx-compiler make   # on a data disk
conda activate /data/disk/envs/g4
geant4-config --version
```

- The `geant4` package pulls the dataset packages (`geant4-data-*`); together they take several GB. Put the environment and the package cache (`CONDA_PKGS_DIRS`) on a data disk; a full system disk stops every process on the machine.
- Use the environment's own compiler (`cxx-compiler`) so that the C++ runtime matches the Geant4 libraries; pass it explicitly to CMake if another compiler comes first on `PATH`.
- Record in `docs/ENVIRONMENT.md`: environment path, Geant4 version (`geant4-config --version`, and the `G4Version` string the application prints), compiler version, dataset names and paths, build directory.

## Dataset environment variables

Geant4 finds each dataset through an environment variable:

| Variable | Dataset | Needed for |
|---|---|---|
| `G4NEUTRONHPDATA` | G4NDL (with `ThermalScattering/`) | neutron transport below 20 MeV in `_HP` lists |
| `G4LEDATA` | G4EMLOW | low-energy EM, Livermore/Penelope, fluorescence |
| `G4LEVELGAMMADATA` | PhotonEvaporation | nuclear de-excitation |
| `G4RADIOACTIVEDATA` | RadioactiveDecay | decay of ions |
| `G4PARTICLEXSDATA` | G4PARTICLEXS | hadronic cross sections |
| `G4ENSDFSTATEDATA` | G4ENSDFSTATE | nuclide states |
| `G4PIIDATA`, `G4REALSURFACEDATA`, `G4SAIDXSDATA`, `G4ABLADATA`, `G4INCLDATA` | PII, RealSurface, SAID, ABLA, INCL | specific models |
| `G4PARTICLEHPDATA` | TENDL-based charged-particle HP (optional) | `_AllHP` lists |

Newer releases add datasets; take the list for your version from `geant4-config --datasets` and its release notes.

- With conda, `conda activate` runs the environment's activation scripts (`$CONDA_PREFIX/etc/conda/activate.d/`), which set these variables. `geant4.sh` is not used (the conda build says so). A batch job that only prepends `$CONDA_PREFIX/bin` to `PATH` has **no** dataset variables: activate the environment in the job, or source the activation scripts, or export the variables explicitly in an `env.sh` kept with the study.
- `geant4-config --datasets` prints the paths compiled into the build. These can differ from the directories the package installed (e.g. a `G4`-prefixed name in `geant4-config` and an unprefixed directory on disk). Never build the environment from that output without checking the directory exists; `scripts/check_g4_datasets.py` reports such mismatches.
- An application built against one Geant4 version needs the dataset versions of that release; mixing versions fails or, worse, runs with different data.

## Checks that datasets are actually found

1. `python3 scripts/check_g4_datasets.py --tsl` in the same shell (or job script) that runs the application: every required variable set, directory non-empty, expected content present, `ThermalScattering/` present for thermal neutrons. Exit code 1 otherwise.
2. The application itself fails early when a required variable is missing (the template checks `G4NEUTRONHPDATA` and its `ThermalScattering/`).
3. In the log: Geant4 aborts with a fatal G4Exception when a dataset is absent at initialisation; warnings that a material or isotope has no HP data mean the data are incomplete for that isotope. Count warnings, do not ignore them (`run_checked.py` records the number).
4. For thermal scattering: at initialisation the log prints "Neutron HP Thermal Scattering Data: Following material-element pairs and/or elements are registered." followed by one line per element (e.g. "Element TS_H_of_Polyethylene"), at any verbose level. Your moderator's element or material must appear there; if it does not, hydrogen is treated as a free gas. `run_checked.py --require-log 'Element TS_H_of_'` enforces it; `/process/had/verbose 1` also shows the thermal-scattering model below 4 eV.
5. Record the dataset paths in the run manifest (`run_checked.py` copies all `G4*` variables).

## Build

```bash
cmake -S path/to/app -B /data/scratch/app-build -DCMAKE_BUILD_TYPE=Release
cmake --build /data/scratch/app-build -j 4        # explicit job cap
```

- Out-of-source builds only, outside git (scratch on the data disk, or a git-ignored `build/`). Keep the configure and build logs with the study when they document a result.
- `find_package(Geant4 REQUIRED)` with `include(${Geant4_USE_FILE})` is enough for a serial application without visualisation; request `ui_all vis_all` components only when needed (they add dependencies). CMake deprecation messages from Geant4's own config files and pkg-config noise about optional graphics libraries are harmless; compiler warnings in your code are not (`-Wall -Wextra -Wshadow`: Geant4's unit symbols such as `s`, `m`, `g` are easily shadowed by local variables).
- Rebuild after every source change and record the source revision (`git rev-parse HEAD`, dirty flag) in the run manifest (`run_checked.py --source`).

## Serial or multi-threaded

- `G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial)` gives one event stream, simple accumulators and a reproducible event order. The environment variable `G4FORCE_RUN_MANAGER_TYPE` can override the factory's choice; check and print the type actually created (the template refuses anything but serial). Prefer it for small studies; run several processes with different seeds for throughput, within the job cap.
- Multi-threaded mode needs thread-local accumulators merged at end of run (`G4AccumulableManager`) and output written per thread or merged by the master. Event seeds are drawn by the master, but the order of per-event output varies; check reproducibility on merged quantities.
