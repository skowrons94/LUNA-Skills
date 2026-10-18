# Tools in a proposal project

A proposal that runs its own feasibility calculations, R-matrix fits, Geant4 or transport simulations and samplers accumulates large, half-documented outputs quickly. Give each tool one place, keep only what reproduces a number in git, and feed the text through the numbers file. If the work grows beyond a few studies, move it into a separate project (`nuclear-research-project`) and link it from `analysis/README.md`; the placement rules below are the same in both.

## Where each tool's material goes

`scripts/create_proposal_project.py --tools` adds the tool directories below; `--study simulation/NAME` or `--study transport/NAME` adds one study with its `REPORT.md` and `results.json` (repeatable, also with `--merge` on an existing project).

```
ACRONYM/
├── analysis/
│   ├── scripts/              feasibility calculations: rates, beam time, budgets, design, power, figures
│   ├── results/              small JSON/CSV summaries; the only files numbers.tex reads
│   ├── data/                 small proposal-specific inputs (stopping tables, digitised points)
│   └── chains/               MCMC chains, posterior samples, large intermediate arrays (git-ignored)
├── r-matrix/
│   ├── master/               the authoritative AZURE2 evaluation (.azr, param.sav, version note)
│   ├── studies/<question>/   deliberate alternatives: radius scans, level schemes, excluded data
│   └── runs/                 generated AZURE2/pyazr output (git-ignored)
├── simulation/
│   └── <study>/              one directory per Geant4 study (e.g. counter-efficiency, gamma-background)
│       ├── src/  CMakeLists.txt
│       ├── build/            compiled code (git-ignored), or a scratch build on the data disk
│       ├── macros/           reviewed, flat macros; one per configuration
│       ├── scripts/          run drivers and analysis of this study
│       ├── runs/<config>/    per-run output, log and manifest (git-ignored; keep summary JSON)
│       ├── REPORT.md         question, configuration, validation, results, limits
│       └── results.json      the study's distilled numbers, consumed by analysis/ or numbers.tex
├── transport/
│   └── <study>/              OpenMC or other transport/reactor calculation
│       ├── scripts/          model builders (Python API) and post-processing
│       ├── model/            generated or hand-written model files (XML), small
│       ├── runs/<config>/    statepoints, summary.h5, tallies (git-ignored)
│       ├── REPORT.md
│       └── results.json
└── docs/
    └── ENVIRONMENT.md        conda envs, versions, data-library paths, build directories
```

- **Feasibility calculations** stay as thin scripts in `analysis/scripts/` that read inputs and simulation or R-matrix `results.json` files and write `analysis/results/`. A number computed in a notebook is not a result until a script reproduces it.
- **R-matrix (AZURE2)** follows `nuclear-research-project`: `master/` is the single authoritative evaluation; a study is promoted to `master/` only after validation and a dated entry in `docs/DECISIONS.md`. Never let a run overwrite the master.
- **Geant4** studies each own `src/`, `macros/`, `scripts/`, `runs/`, `REPORT.md` and `results.json`. The build directory lives outside git: `simulation/<study>/build/` (git-ignored) or a scratch area on the data disk. `geant4-simulation` covers the code, `underground-gamma-simulation` and `agata-simulation` the specialised setups.
- **Transport or reactor calculations (OpenMC)**: keep the scripts that build the model, the small model files and the post-processing; statepoints and HDF5 outputs go to `runs/`. Nuclear data libraries (cross-section HDF5 sets, thermal scattering tables) stay **outside** the project; record the library name, version and path (`OPENMC_CROSS_SECTIONS` or equivalent) in `docs/ENVIRONMENT.md` and in each run manifest.
- **MCMC chains and other large outputs** go to `analysis/chains/` or the study's `runs/`, never next to the results. Keep in git, in `analysis/results/`, the chain summary (quantiles, effective sample size, convergence diagnostics) as JSON, and the seed and settings that regenerate the chain.

## Studies, not trees

- One directory per study under `simulation/` (and `transport/`). Never two parallel trees such as `simulation/` and `sim_new/` or `geant4/` for the same model; a new geometry or physics question is a new study or a new configuration inside the existing one.
- The flat `simulation/{geometry,macros,physics,runs,...}` tree of a `nuclear-research-project` is one study; with several studies, give each its own directory as above.
- A study that branches from another records its parent in `REPORT.md` (and copies, not links, the source it modified).
- Each study writes exactly one `REPORT.md` and one `results.json`. The JSON holds the headline values with units, uncertainties, event counts, seeds, code revision and the run directories they came from.

## Size policy

| In git | Ignored |
|---|---|
| source, CMakeLists, macros, model builders, analysis scripts | `build/`, executables, object files |
| `REPORT.md`, `results.json`, small run summaries (JSON/CSV, under ~1 MB) | ROOT files, per-event CSV, statepoints, `summary.h5`, tallies in HDF5 |
| run manifests (command, seeds, versions, hashes) | MCMC chains, posterior samples, `.npy`/`.npz` arrays |
| figures used in the text | AZURE2 `output/` and run directories, logs over ~1 MB (compress or drop) |

`.gitignore` additions for a project with tools:

```
# builds and large run products
simulation/*/build/
transport/*/build/
simulation/*/runs/**/*.root
simulation/*/runs/**/*.csv
simulation/*/runs/**/*.log
transport/*/runs/
r-matrix/runs/
analysis/chains/
*.h5
*.npy
*.npz
```

JSON is never ignored, so run summaries, manifests and `results.json` stay tracked; a `transport/*/runs/` or `r-matrix/runs/` directory is ignored whole, so its distilled numbers must reach the study's `results.json`.

Check with `git status --ignored` and `git check-ignore -v FILE` that summaries are tracked and bulk files are not. A results file that the text depends on must never sit only in an ignored directory.

## Results to the text

`simulation/<study>/results.json` → `analysis/scripts/` (if combined with rates or budgets) → `analysis/results/*.json` → `proposal/numbers.tex` → text. The numbers file names the result file and key for each macro; no number is copied by hand from a `REPORT.md` or a log.

## Environments and large data

- Conda environments, Geant4 datasets, nuclear-data libraries and scratch builds go on a data disk, never the system disk (a full root partition stops every process on the machine). Create environments with `conda create -p /data/disk/envs/NAME` and point package caches there (`CONDA_PKGS_DIRS`).
- `docs/ENVIRONMENT.md` records, per tool: environment path and how to activate it, code version (Geant4, OpenMC, AZURE2, Python packages), dataset or library names and paths, compiler, and the build directory. Update it when anything changes, and copy the relevant lines into each run manifest.

## Shared machines

- Cap parallel jobs explicitly (`make -j4`, `OMP_NUM_THREADS`, `--jobs N` in run drivers) and choose N from the current load (`nproc`, `uptime`), not from the core count. Run long jobs at low priority (`nice -n 10`).
- Write a pilot first, estimate wall time and disk from it, and check free space on the target disk before a campaign.

## Tidy-up checklist for an existing project

1. Inventory: list every directory with size (`du -sh */ | sort -h`) and find duplicate trees, stray builds, outputs outside `runs/`, and results only present in logs.
2. Map each item to the layout above and show the mapping to the user before moving anything.
3. Merge parallel simulation trees into `simulation/<study>/`; keep the history by moving, not copying, and note the old paths in `REPORT.md`.
4. Make sure every number in `numbers.tex` points to a `results.json` or `analysis/results/` file that exists and is tracked.
5. Add the `.gitignore` rules; remove large files from the index (`git rm --cached`), not from disk.
6. Fill `docs/ENVIRONMENT.md` and add a manifest to every run that feeds a result.
7. Archive superseded runs (below), then rerun one representative configuration per study from a clean build to show it still reproduces its `results.json`.

## Archiving superseded runs

- Move superseded runs to `simulation/<study>/runs/archive/YYYY-MM-DD_<reason>/` (or `analysis/chains/archive/...`) with a one-line `WHY.md`: what superseded them and the decision number in `docs/DECISIONS.md`.
- Keep their summaries and manifests; compress or delete bulk outputs only with the user's approval, and only when the manifest is enough to regenerate them.
- Never edit an archived run; a corrected run is a new run.
