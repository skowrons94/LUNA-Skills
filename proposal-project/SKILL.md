---
name: proposal-project
description: Scaffold, maintain or tidy a grant-proposal project directory (ERC, MSCA, national or institutional calls, beam-time science cases): every quoted number traced to a result file, one place and a size policy per tool (feasibility scripts, R-matrix, Geant4, transport, MCMC), superseded drafts archived, PI-only facts as placeholders, and registers of reviewer objections, decisions and the pre-submission checklist. Use when starting a proposal, reorganising an existing one, or preparing it for submission; use `proposal-style` for the prose and `proposal-analysis` for the scientific case.
---
# Proposal project

A proposal is a small research project with a hard deadline and many revisions, and by the last revision nobody remembers where a number or a framing came from. This skill keeps it navigable, with one place for the current text, one for the evidence behind every number, and one for what is still open. You need the call text, the existing drafts if there are any, and the tools the scientific case uses. You get a directory in the layout of [layout.md](references/layout.md), its registers, and a pre-submission checklist.

## Where this fits

- Comes from: the call (copied into `docs/CALL.md`); a feasibility study or long analysis kept as a separate `nuclear-research-project`; Geant4 code written with `geant4-simulation`; the scientific case from `proposal-analysis`, kept in `analysis/results/`.
- Goes to: `proposal-analysis`, which writes the scientific case into `analysis/results/`; `proposal-style`, which writes the text against the registers; `prc-figures` for the figures and `research-slides` for the interview talk.
- Checked by: `scripts/test_create_proposal_project.py`, which must print PASS, and `docs/FINAL_CHECKLIST.md` before submission.

## Tasks

- New proposal: read [layout.md](references/layout.md), then run `scripts/create_proposal_project.py` (dry-run first).
- Existing proposal: inspect it first and propose a mapping to the layout. Do not move, rename or delete files unless the user asks for the reorganisation. Move superseded drafts to `proposal/archive/`; never delete them without explicit approval.
- Registers and checklists: [registers.md](references/registers.md) describes the decision log, objections register, PI-input sheet and final checklist.
- Proposal with its own tools (feasibility scripts, AZURE2, Geant4, OpenMC or other transport codes, MCMC): [tools-layout.md](references/tools-layout.md) says where each tool's material goes, what enters git, environments on a data disk, job caps on shared machines, and gives the tidy-up checklist. Scaffold with `--tools` and one `--study simulation/NAME` (or `transport/NAME`) per study; write Geant4 code with `geant4-simulation`.
- Feasibility study or long analysis behind the proposal: keep it as a separate project scaffolded with `nuclear-research-project` and link it from `analysis/README.md`. Its data are not duplicated, and `analysis/data/` holds only small inputs specific to the proposal.

## Rules and their reasons

1. The current version lives in place, and earlier versions live in `proposal/archive/vN/`. Each part (e.g. summary, scientific case, CV, budget) has one source of truth, and build products go to `proposal/build/`. Builds are named by part and version, so that a reviewer comment can be traced to the text it refers to (layout.md).
2. Every quoted number has a provenance. A number in the text comes from a file in `analysis/results/` (or a cited source), preferably through a macros file (`proposal/numbers.tex` or equivalent) generated or checked by a script. Never type a recomputed number by hand into one part only, because the other parts and the figures then keep the old value.
3. PI-only facts are placeholders, not guesses. Letters, quotes, CV dates, roles, contract types and personal statements are written as `[[PI: what is needed]]` and listed in `docs/FINAL_CHECKLIST.md`. Never invent them. Before submission, each placeholder is resolved or removed together with the claim that depended on it (layout.md).
4. Confidential material stays out of the text and out of shared repositories. Other people's proposals, internal collaboration reports, unpublished numbers that are not the applicant's own, and export-controlled software are kept in `private/` (git-ignored) and are summarised, never reproduced.
5. Objections and decisions are recorded, not remembered. Each reviewer point goes into `docs/OBJECTIONS.md` with its status and evidence, and each change of framing or number goes into `docs/DECISIONS.md` with the reason. An objection is closed only when both the text and the evidence exist (registers.md).
6. The funder's rules win. Page limits, templates, budget caps and eligibility are copied into `docs/CALL.md` with the call edition and date, and checked before each build.

## Method

1. Fill `docs/CALL.md` (call, edition, deadline, page limits, budget rules, evaluation criteria) before writing.
2. Write the scientific case (`proposal-analysis`) and the text (`proposal-style`) against the registers.
3. After each revision, rebuild, render every page, and check the page limits and that the numbers in all parts agree with the macros file; then update `docs/OBJECTIONS.md` and `docs/DECISIONS.md`.
4. Before submission, resolve or list every `[[...]]`, rerun all number-producing scripts from a clean state, and fill `docs/FINAL_CHECKLIST.md`.

## Scripts

```bash
python3 scripts/create_proposal_project.py /absolute/path/to/proposal --acronym ACRONYM --call "Call name and edition" --dry-run
python3 scripts/create_proposal_project.py /absolute/path/to/proposal --acronym ACRONYM --call "Call name and edition"
python3 scripts/create_proposal_project.py /absolute/path/to/proposal --acronym ACRONYM --merge \
  --tools --study simulation/counter-efficiency --study transport/shielding   # add tools to an existing project
python3 scripts/test_create_proposal_project.py    # must print PASS
```

The command refuses to overwrite files. `--merge` adds only missing pieces to an existing directory, so inspect the dry-run first.

## What to deliver

- The scaffolded or reorganised directory, with the mapping shown to the user before anything was moved.
- `docs/CALL.md`, `docs/DECISIONS.md`, `docs/OBJECTIONS.md` and `docs/FINAL_CHECKLIST.md` filled to the current state.
