---
name: nuclear-research-project
description: Structure, scaffold, or reorganize reproducible experimental nuclear-physics projects, especially feasibility studies combining external data, stopping powers, R-matrix evaluations, detector simulations, analysis code, LaTeX reports, and scientific presentations. Use for new project setup, project-structure audits, or research handoffs; do not use for generic software repositories.
---

# Nuclear Research Project

Create a project in which every number in a report or presentation can be traced to an input, assumption, configuration, and reproducible calculation.

## Route the task

- For a new project, read [references/project-structure.md](references/project-structure.md), then run `scripts/create_research_project.py` unless the user requests a different layout.
- For an existing project, inspect it first. Preserve user files and propose a mapping to the canonical structure. Do not move, rename, or delete files unless the user asks for the reorganization.
- For a LaTeX feasibility report, also read [references/report-style.md](references/report-style.md).
- For a scientific deck, read [references/presentation-style.md](references/presentation-style.md) for the feasibility-deck narrative and use the `research-slides` skill to build, animate and check the deck.
- For reproducibility, validation, or handoff work, also read [references/reproducibility.md](references/reproducibility.md).

## Non-negotiable boundaries

1. Treat `data/raw/` and `data/external/` as immutable evidence. Normalize or convert them into `data/processed/`; never silently edit the source files.
2. Keep the authoritative R-matrix evaluation in `r-matrix/master/`. Put alternative hypotheses in `r-matrix/studies/` and all generated AZURE2 or other solver output in `r-matrix/runs/`.
3. Keep simulation source, geometry, macros, and physics settings separate from `simulation/runs/`. A run must be reproducible from a named configuration and seed policy.
4. Put reusable self-written code in `src/`, small executable entry points in `scripts/`, and exploratory work in `notebooks/`. A notebook must not be the only implementation of a result used downstream.
5. Write numerical outputs to `results/` and visual outputs to `plots/`. Reports and presentations consume those outputs; they must not hide manual corrections or private copies of the final numbers.
6. Record assumptions, decisions, provenance, validation, and the current state in `docs/`. Keep units and energy-frame conventions explicit.
7. Reports are LaTeX-first and use simple scientific language. State the physics question, quantitative assumptions, validation, uncertainty, and bounded feasibility conclusion.

## Working method

Before calculating, identify the reaction, projectile and target, energy frame, units, beam normalization, detector configuration, scientific question, and decision criterion. If any is unknown, record it as an open assumption rather than guessing silently.

Build the dependency chain from evidence to conclusion:

`source data -> processed data -> physical model -> validation -> rates or spectra -> results and plots -> report and presentation`

Prefer one shared implementation for units, stopping powers, kinematics, yield integrals, rates, and plotting conventions. Thin workflow scripts should call that implementation and write named outputs. Preserve direct comparisons to measurements; do not rescale data or models merely to make plots agree. If a correction or normalization is scientifically justified, state it and retain the uncorrected comparison.

When the analysis is ready, run the verification checks, compile the LaTeX report, render the PDF, and inspect it visually. For a PowerPoint deliverable, build it with the `research-slides` skill and inspect every rendered slide. Update `docs/HANDOFF.md` last so it describes the actual state rather than the intended state.

## Scaffold command

```bash
python3 scripts/create_research_project.py /absolute/path/to/project \
  --title "Reaction feasibility study" \
  --author "Researcher name"
```

The command refuses to overwrite files. Use `--merge` only to add missing scaffold pieces to an existing directory, and inspect the dry-run first.
