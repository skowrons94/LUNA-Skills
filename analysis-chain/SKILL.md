---
name: analysis-chain
description: Run a multi-skill nuclear-astrophysics analysis (data audit, spectra to yields, efficiency, target and effective energy, cross section or S factor, R-matrix fit and extrapolation, review, write-up) as gated stages with contract-checked handoffs, unit and frame adapters, provenance sidecars, a resumable state file, human checkpoints with decision briefs, bounded retries and parallel independent attempts. Use when a task crosses stage boundaries (yields into target-analysis or AZURE2, an efficiency curve into yields), to plan, run or resume an end-to-end campaign, or to split analysis work between agents; one stage alone uses its own skill.
---
# Analysis chain

An analysis is a chain of stages, each owned by one skill. The errors that cost weeks usually happen between stages: a unit that changes meaning, a shared uncertainty that becomes independent, a lab energy read as centre of mass, or a stage rerun while the next one keeps the old numbers. This skill therefore runs the chain as fixed stages with checked handoffs rather than as one long improvised session. You need a project in the layout of `nuclear-research-project` and the question the chain should answer. You get stage outputs that satisfy named contracts, provenance sidecars, a state file `docs/CHAIN.md` from which any session can resume, and decision briefs wherever the researcher has to choose. Why the stages are fixed and how agents share them is explained in [orchestration.md](references/orchestration.md); what each handoff must carry is in [contracts.md](references/contracts.md).

## Where this fits

- Comes from: a project scaffolded by `nuclear-research-project`, and its claims register; the outputs of every stage skill (for example `yield-analysis`, `efficiency-analysis`), checked at each boundary, and the audits of `uncertainty-audit`.
- Goes to: the stage skills of the table below, through the contracts `spectrum-csv`, `yield-table`, `efficiency-curve`, `excitation-curve`, `azure-dat`, `rate-table` and `thermo-trajectory`.
- Checked by: `scripts/contracts.py` at every boundary, `scripts/selftest.py`, the `data-auditor` and `physics-referee` subagents, and `uncertainty-audit` before a stage result is quoted.

One stage only is handled by that stage's skill directly. Several stages, a handoff between them, or a campaign to plan or resume belong here. Project layout, the claims register and handoff notes are `nuclear-research-project`; proposal feasibility chains are `proposal-analysis`.

## Stages

| Stage | Skill | Output | Contract | Gate (stage is done only when) |
|---|---|---|---|---|
| 0 Data audit | `data-auditor` subagent | audit table | — | blocking issues resolved or recorded as assumptions |
| 1 Yields | `yield-analysis`, `peak-shape-analysis` | `yields.csv`, `covariance.csv`, `result.json` | `yield-table` | every ROI overlay reviewed; negative areas kept; shared systematics named |
| 2 Efficiency | `efficiency-analysis` | fit `result.json` | `efficiency-curve` | line energies inside the validity range; summing treated for the real geometry |
| 3 Target, effective energy | `target-analysis` | profile, effective energies | `excitation-curve` in | stopping table and composition stated; profile validated on a resonance |
| 4 Cross section / S factor → R-matrix | `azure2`, `resonance-search` | `.dat` segments, fit | `azure-dat` | lab frame and MeV checked; normalisation priors equal quoted systematics |
| 5 Extrapolation, rates | `azure2` | S(E), rate tables | `rate-table` out | registered as `extrapolated` claims with model dependence |
| 5b Astrophysical impact | `reaction-network` | burns, sensitivity rankings | `rate-table`, `thermo-trajectory` in | rates compared at site temperatures; tolerance and completeness checks pass; site conditions sourced |
| 5c Stellar models | `stellar-evolution` | MESA runs with `manifest.json`, `results.json`, trajectories | `rate-table` in, `thermo-trajectory` out | `mesa.py check-run` passes on every run; effect larger than the resolution and dominant mixing or mass-loss noise |
| 6 Review | `physics-referee` subagent | findings | — | blocking findings resolved; responses in `docs/VALIDATION.md` |
| 7 Write-up | writing skills, `prc-figures`, `research-slides` | text, figures | claims register | `check_claims.py` passes on the documents |

Stages that do not apply are skipped, but dependencies are never reordered, because the order is set by the physics: efficiency before yields, yields before cross sections.

## At every stage boundary

1. Check the input contract before reading, with `python3 scripts/contracts.py check CONTRACT FILE`. A violation stops the chain here; the consumer is not patched around it, since that hides the error from every later stage.
2. Convert with the adapters, not by hand: `scripts/adapters.py efficiency-at`, `yields-to-excitation` and `to-azure` make units, frames, the Sommerfeld factor and correlations explicit, and each writes a provenance sidecar. [contracts.md](references/contracts.md) states what each handoff must carry, especially which uncertainties are shared.
3. Record provenance for outputs whose tool does not, with `scripts/provenance.py record OUT --inputs ... --cmd ... --skill ...`.
4. Update the state file `docs/CHAIN.md`, from the template [assets/CHAIN.md](assets/CHAIN.md), with stage, status, inputs, outputs, gate result, open items and next step. A new session resumes from this file, not from memory, because context is compressed and sessions end.
5. Register the numbers that will leave the project as claims (`nuclear-research-project`), with `depends_on` following the chain, so that a rerun upstream flags everything downstream.

## Rules and their reasons

[orchestration.md](references/orchestration.md) is to be read before an unattended or multi-agent run.

1. Human checkpoints. The chain stops and a decision brief is written, giving question, options, evidence, recommendation, consequences and reversibility, before any of: excluding or re-extracting data; promoting a fit to master or changing a level scheme; choosing between analyses that give different results; overwriting results; runs longer than about an hour or above the agreed budget; anything that leaves the machine. These choices change what the result means, and only the researcher can accept that.
2. Bounded retries. Each stage gets at most three attempts, each a stated, different change, and the reason each failed is recorded. The chain then stops and escalates with a brief. A gate is never loosened, and data or tests are never edited, to make a stage pass; stopping with a clear brief is a successful outcome.
3. Parallel independent attempts. When the method choice is uncertain (background or peak model, target model, R-matrix hypothesis, channel radius), two to four subagents work with distinct approaches, one success criterion written before they start, and no access to each other's work. Agreement within uncertainty gives the result plus a method systematic. Disagreement goes to cross-examination and then to the researcher, and disagreeing answers are not averaged.
4. Generation and judgement are separate. The agent that produced a stage output does not approve its gate alone; the review subagents or the researcher do.
5. One stage per context, where practical. Heavy tool output goes to subagents, and the state file carries what the next stage needs.

## Scripts

`python3 scripts/selftest.py` runs the yield and efficiency demos, checks the contracts against their real outputs and corrupted copies, and verifies the adapters (frame, units, S factor → cross section) and the provenance check. It must print PASS. The scripts themselves need only the standard library.

## What to deliver

- Stage outputs that pass their contract check, each with a provenance sidecar.
- `docs/CHAIN.md` with the status, gate result and next step of every stage.
- Decision briefs at the checkpoints, with the answers in `docs/DECISIONS.md`.
- Claims registered with `depends_on` following the chain.
