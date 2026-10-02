# @@PROJECT_TITLE@@

Created on @@DATE@@ using the canonical nuclear-research project structure.

## Scientific question

State the reaction, energy range, observable, and decision this project must support.

## Project rules

- `data/raw/` and `data/external/` are immutable evidence.
- `r-matrix/master/` contains the authoritative evaluation; generated solver output goes to `r-matrix/runs/`.
- Simulation definitions are separated from generated runs.
- Reusable code belongs in `src/`; workflow entry points belong in `scripts/`.
- Numerical outputs go to `results/`; visual outputs go to `plots/`.
- The scientific report is LaTeX-based and lives in `report/`.
- Assumptions, decisions, provenance, validation, and handoff state live in `docs/`.

## Start here

1. Complete `project.yaml` with the reaction, energy frame, beam convention, and detector configuration.
2. Record the reproducible software and solver environment in `environment/ENVIRONMENT.md`.
3. Register uncertain inputs in `docs/ASSUMPTIONS.md`.
4. Register every external dataset in `docs/PROVENANCE.md` before transforming it.
5. Put the canonical R-matrix evaluation in `r-matrix/master/`.
6. Define named analysis configurations in `configs/`.
7. Add a reproducible verification entry point under `scripts/` and record its checks in `docs/VALIDATION.md`.
8. Update `docs/HANDOFF.md` after producing results, plots, the report, or a presentation.
