---
name: proposal-project
description: Scaffold, maintain or tidy a grant-proposal project directory (ERC, MSCA, national or institutional calls, beam-time science cases) in which every quoted number traces to a result file, superseded drafts are archived, PI-only facts are marked as placeholders, and reviewer objections, decisions and the pre-submission checklist are kept as registers. Use when starting a proposal, reorganising an existing one, or preparing it for submission; use `proposal-style` for the prose and `proposal-analysis` for the scientific case.
---
# Proposal project

A proposal is a small research project with a hard deadline and many revisions. Keep it navigable: one place for the current text, one for the evidence behind every number, one for what is still open.

## Route the task

- **New proposal.** Read [layout.md](references/layout.md), then run `scripts/create_proposal_project.py` (dry-run first).
- **Existing proposal.** Inspect it first and propose a mapping to the layout. Do not move, rename or delete files unless the user asks for the reorganisation. Move superseded drafts to `proposal/archive/`; never delete them without explicit approval.
- **Registers and checklists.** Read [registers.md](references/registers.md) for the decision log, objections register, PI-input sheet and final checklist.
- **Feasibility study or long analysis behind the proposal.** Keep it as a separate project scaffolded with `nuclear-research-project` and link it from `analysis/README.md`; do not duplicate its data (`analysis/data/` holds only small inputs specific to the proposal).

## Non-negotiable boundaries

1. **The current version lives in place; earlier versions live in `proposal/archive/vN/`.** One source of truth per part (e.g. summary, scientific case, CV, budget). Build products go to `proposal/build/`.
2. **Every quoted number has a provenance.** A number in the text comes from a file in `analysis/results/` (or a cited source), preferably through a macros file (`proposal/numbers.tex` or equivalent) generated or checked by a script. Never type a recomputed number by hand into one part only.
3. **PI-only facts are placeholders, not guesses.** Letters, quotes, CV dates, roles, contract types and personal statements are written as `[[PI: what is needed]]` and listed in `docs/FINAL_CHECKLIST.md`. Never invent them.
4. **Confidential material stays out of the text and out of shared repositories.** Other people's proposals, internal collaboration reports, unpublished numbers that are not the applicant's own, and export-controlled software are kept in `private/` (git-ignored) and are summarised, never reproduced.
5. **Objections and decisions are recorded, not remembered.** Each reviewer point goes into `docs/OBJECTIONS.md` with its status and evidence; each change of framing or number goes into `docs/DECISIONS.md` with the reason.
6. **The funder's rules win.** Page limits, templates, budget caps and eligibility are copied into `docs/CALL.md` with the call edition and date and checked before each build.

## Working method

1. Fill `docs/CALL.md` (call, edition, deadline, page limits, budget rules, evaluation criteria) before writing.
2. Write the scientific case (`proposal-analysis`) and the text (`proposal-style`) against the registers.
3. After each revision: rebuild, render every page, check page limits and that the numbers in all parts agree with the macros file; update `docs/OBJECTIONS.md` and `docs/DECISIONS.md`.
4. Before submission: resolve or list every `[[...]]`, rerun all number-producing scripts from a clean state, and fill `docs/FINAL_CHECKLIST.md`.

## Scaffold command

```bash
python3 scripts/create_proposal_project.py /absolute/path/to/proposal --acronym ACRONYM --call "Call name and edition" --dry-run
python3 scripts/create_proposal_project.py /absolute/path/to/proposal --acronym ACRONYM --call "Call name and edition"
python3 scripts/test_create_proposal_project.py    # must print PASS
```

The command refuses to overwrite files. `--merge` adds only missing pieces to an existing directory; inspect the dry-run first.
