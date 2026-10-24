---
name: nuclear-research-project
description: Structure, scaffold or reorganize a reproducible experimental nuclear-physics project, especially a feasibility study that combines external data, stopping powers, R-matrix evaluations, detector simulations, analysis code, LaTeX reports and scientific presentations, with a claims register that ties every quoted number to its evidence. Use for new project setup, project-structure audits or research handoffs; do not use for generic software repositories.
---

# Nuclear research project

A feasibility study or an analysis is only as credible as the path from its inputs to the numbers it quotes. This skill sets up and maintains a project in which every number in a report or presentation can be traced to an input, an assumption, a configuration and a reproducible calculation. You need the physics question, the inputs as received and the tools the study will use. You get a canonical directory layout, registers for assumptions, decisions, validation and claims, and a report and deck built only from the project's own result files. The layout and its placement rules are in [project-structure.md](references/project-structure.md).

## Where this fits

- Comes from: the researcher's question and the data as received from the DAQ, EXFOR, papers or collaborators.
- Goes to: every stage skill, which reads from and writes into this layout; `analysis-chain`, which runs multi-stage analyses inside it with its state file `docs/CHAIN.md`; `research-slides`, `proposal-project` and the writing skills of section 6 Telling people, which turn its results into documents.
- Checked by: `scripts/check_claims.py` before every build, the `data-auditor`, `physics-referee` and `citation-checker` subagents, and the edit guard of `settings/install_guard.py`.

## Routing

- New project: read [references/project-structure.md](references/project-structure.md), then run `scripts/create_research_project.py` unless the user requests a different layout.
- Existing project: inspect it first. Preserve user files and propose a mapping to the canonical structure; files are moved, renamed or deleted only when the user asks for the reorganization.
- LaTeX feasibility report: also read [references/report-style.md](references/report-style.md).
- Scientific deck: read [references/presentation-style.md](references/presentation-style.md) for the feasibility-deck narrative and use the `research-slides` skill to build, animate and check the deck.
- Reproducibility, validation or handoff work: also read [references/reproducibility.md](references/reproducibility.md).
- Grant proposal built on the project: `proposal-project` for the proposal directory and `proposal-analysis` for its quantitative case.
- Writing, building or validating a Geant4 application (neutron counters, shielding, sources, kinematics): `geant4-simulation`; LUNA-type gamma setups: `underground-gamma-simulation`.

## Rules and their reasons

1. `data/raw/` and `data/external/` are immutable evidence. They are normalized or converted into `data/processed/`, and the source files are never edited silently. Every file in `data/processed/` then has a generating script or a documented transformation, so that no second data truth appears in notebooks, report folders or R-matrix output (project-structure.md).
2. The authoritative R-matrix evaluation lives in `r-matrix/master/`. Alternative hypotheses go to `r-matrix/studies/` and all generated AZURE2 or other solver output to `r-matrix/runs/`, which is disposable. A temporary fit must never overwrite the master; a fit is promoted to `master/` only after validation, with the reason recorded in `docs/DECISIONS.md`.
3. Simulation source, geometry, macros and physics settings are kept separate from `simulation/runs/`. A run must be reproducible from a named configuration and seed policy, because a simulation result is interpretable only with its code revision, configuration, number of events, random-seed policy, geometry version and detector-response assumptions.
4. Reusable self-written code goes in `src/`, small executable entry points in `scripts/`, and exploratory work in `notebooks/`. A notebook must not be the only implementation of a result used downstream; accepted logic moves into `src/` or `scripts/` before the result is cited.
5. Numerical outputs are written to `results/` and visual outputs to `plots/`. Reports and presentations consume those outputs and must not hide manual corrections or private copies of the final numbers, since otherwise a polished report becomes the only record of how a conclusion was obtained.
6. Assumptions, decisions, provenance, validation and the current state are recorded in `docs/`. Every quantitative statement that leaves the project is registered in `docs/CLAIMS.toml`, and `scripts/check_claims.py` is run before building a report, talk or submission. The check reports evidence that changed since a claim was accepted, claims that depend on a stale or challenged claim, and quoted values that match no claim (see [references/reproducibility.md](references/reproducibility.md)). Units and energy-frame conventions are kept explicit.
7. Reports are LaTeX-first and use simple scientific language. They state the physics question, the quantitative assumptions, the validation, the uncertainty and a bounded feasibility conclusion, because a feasibility report is an options-and-decision document supported by physics, not a lab diary (report-style.md).

## Method

Before calculating, identify the reaction, projectile and target, energy frame, units, beam normalization, detector configuration, scientific question and decision criterion. An item that is unknown is recorded as an open assumption rather than guessed silently.

The dependency chain from evidence to conclusion is built explicitly:

`source data -> processed data -> physical model -> validation -> rates or spectra -> results and plots -> report and presentation`

We prefer one shared implementation for units, stopping powers, kinematics, yield integrals, rates and plotting conventions; thin workflow scripts call that implementation and write named outputs. Direct comparisons to measurements are preserved, and data or models are not rescaled merely to make plots agree. If a correction or normalization is scientifically justified, it is stated and the uncorrected comparison is retained.

Producing a result and judging it are separate. Before a result is used downstream or quoted, an agent that did not produce it checks it: the `data-auditor` subagent for new input data, `physics-referee` for results and `citation-checker` for references, all defined in the repository's `subagents/`. They receive the files and the claim, not the reasoning, and their findings and the responses are recorded in `docs/VALIDATION.md`.

1. When the analysis is ready, run the verification checks, compile the LaTeX report, render the PDF and inspect it visually.
2. For a PowerPoint deliverable, build it with the `research-slides` skill and inspect every rendered slide.
3. Update `docs/HANDOFF.md` last, so that it describes the actual state rather than the intended one.

## Scripts

```bash
python3 scripts/create_research_project.py /absolute/path/to/project \
  --title "Reaction feasibility study" \
  --author "Researcher name"
```

The evidence is then protected mechanically: `python3 <skills-repo>/settings/install_guard.py /absolute/path/to/project` installs a hook that denies edits to `data/raw/` and `data/external/` and asks before changes to `r-matrix/master/` or anything that leaves the machine.

The scaffold command refuses to overwrite files. `--merge` only adds missing scaffold pieces to an existing directory, and its dry-run is inspected first.

## What to deliver

- The project tree, or for an existing project the proposed mapping to the canonical structure.
- The registers in `docs/` kept current, with `check_claims.py` passing on the documents.
- The report and deck built from `results/` and `plots/`, rendered and inspected.
- `docs/HANDOFF.md` describing the actual state.
