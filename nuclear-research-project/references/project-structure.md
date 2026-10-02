# Canonical project structure

Use the smallest subset that fits the study, but preserve the same meaning for each directory across projects.

```text
project/
|-- README.md
|-- project.yaml
|-- configs/
|-- environment/
|-- data/
|   |-- raw/
|   |-- external/
|   |   |-- exfor/
|   |   |-- literature/
|   |   `-- collaborators/
|   |-- stopping-power/
|   |   |-- raw/
|   |   `-- processed/
|   |-- calibration/
|   |-- processed/
|   `-- metadata/
|-- r-matrix/
|   |-- master/
|   |-- data/
|   |-- studies/
|   |-- runs/
|   `-- validation/
|-- simulation/
|   |-- geometry/
|   |-- macros/
|   |-- physics/
|   |-- runs/
|   |-- analysis/
|   `-- validation/
|-- src/
|   |-- physics/
|   |-- utilities/
|   `-- plotting/
|-- scripts/
|-- notebooks/
|-- tests/
|-- results/
|   |-- tables/
|   |-- summaries/
|   |-- model-exports/
|   |-- manifests/
|   `-- validation/
|-- plots/
|   |-- diagnostics/
|   |-- report/
|   `-- presentations/
|-- report/
|   |-- main.tex
|   |-- sections/
|   |-- references.bib
|   `-- build/
|-- presentations/
|   |-- animations/      # Manim scene sources, README with render commands, final MP4s + posters
|   |-- assets/
|   `-- build/
|-- docs/
|   |-- ASSUMPTIONS.md
|   |-- DECISIONS.md
|   |-- PROVENANCE.md
|   |-- VALIDATION.md
|   `-- HANDOFF.md
`-- work/
```

## Placement rules

### Data

- `data/raw/`: measurements produced by the project, exactly as received from the DAQ or instrument.
- `data/external/exfor/`: downloaded EXFOR tables and their query or entry identifiers.
- `data/external/literature/`: digitized tables or supplementary material from papers. Store citation keys and extraction notes in provenance.
- `data/external/collaborators/`: files, maps, spectra, and notes received from collaborators. Preserve the received filename; explain it in provenance rather than renaming away context.
- `data/stopping-power/raw/`: original SRIM, ATIMA, PSTAR, or equivalent exports, including version and material definition.
- `data/stopping-power/processed/`: machine-readable, unit-normalized stopping tables used by the code.
- `data/calibration/`: detector, target, beam, and efficiency calibration inputs.
- `data/processed/`: derived analysis-ready tables. Every file here must have a generating script or documented transformation.
- `data/metadata/`: schemas, column dictionaries, checksums, run lists, and data-quality flags.

Do not create a second data truth inside notebooks, report folders, or R-matrix output directories.

### R-matrix

- `r-matrix/master/` is the authoritative evaluation: the canonical project file, saved parameters, channel definitions, and a short version note. It is the source of truth even when a fit is evaluated in a sandbox.
- `r-matrix/data/` holds solver-formatted datasets and normalization metadata. If these are transformed from `data/external/`, keep the transform reproducible.
- `r-matrix/studies/` contains deliberate alternatives such as channel-radius scans, level schemes, excluded datasets, or sensitivity cases. Name each study by the question it tests.
- `r-matrix/runs/` contains generated fit and extrapolation output. It is disposable and normally ignored by version control.
- `r-matrix/validation/` contains data-versus-fit comparisons, residuals, chi-squared summaries, and independent checks.

Never let a temporary fit overwrite the master. Promote a fit to `master/` only after validation and record the reason in `docs/DECISIONS.md`.

### Simulation

Keep geometry, macro/configuration, physics-list settings, source distributions, and analysis code distinct. A simulation result must identify code revision, configuration, number of events, random-seed policy, geometry version, and detector-response assumptions. Large run products belong in `simulation/runs/`; stable distilled response matrices or efficiency tables belong in `results/model-exports/`.

### Code and workflows

- `src/physics/`: reusable domain calculations: cross sections, stopping, kinematics, thick-target integrals, detector response, branching, and uncertainty propagation.
- `src/utilities/`: I/O, unit conversion, configuration, provenance, and run-manifest helpers.
- `src/plotting/`: shared figure identity and plot builders.
- `scripts/`: thin, named workflows such as `run_rates.py`, `run_rmatrix_validation.py`, `run_simulation_analysis.py`, and `verify.py`.
- `notebooks/`: exploration and diagnostic views. Move accepted logic into `src/` or `scripts/` before citing the result.
- `tests/`: numerical invariants, unit conversions, reference cases, and regression checks.

### Outputs and deliverables

- `results/tables/`: final numerical tables consumed downstream.
- `results/summaries/`: machine-readable or text summaries of headline quantities.
- `results/model-exports/`: compact R-matrix or simulation products used by other stages.
- `results/manifests/`: configurations, hashes, software versions, and seeds associated with results.
- `results/validation/`: numerical QA output.
- `plots/diagnostics/`: working plots that test the analysis.
- `plots/report/` and `plots/presentations/`: publication-ready figures tailored to each medium.
- `report/` and `presentations/`: source and compiled deliverables, not hidden analysis logic.
- `work/`: disposable rendering, conversion, cache, and scratch files.

## What this adds beyond a basic analysis tree

The important missing pieces in many feasibility projects are `configs/`, environment capture, `tests/`, run manifests, explicit provenance, decision and assumption logs, validation areas for both R-matrix and simulation, and a scratch boundary. These make the study reviewable and prevent a polished report from becoming the only record of how a conclusion was obtained.
