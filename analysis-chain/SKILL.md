---
name: analysis-chain
description: Run a nuclear-astrophysics analysis that spans several skills — data audit, spectra to yields, efficiency, target and effective energy, cross section or S factor, R-matrix fit and extrapolation, review, write-up — as fixed stages with gates, validated handoff files (contracts, unit and frame adapters, provenance sidecars), a resumable state file, human checkpoints with decision briefs, bounded retries and parallel independent attempts. Use when a task crosses stage boundaries (e.g. yields into target-analysis or AZURE2, an efficiency curve into yields), when planning, running or resuming an end-to-end analysis campaign, or when deciding how to split analysis work between agents.
---
# Analysis chain

An analysis is a chain of stages, each owned by one skill. Errors that cost weeks usually happen between stages: a unit that changes meaning, a shared uncertainty that becomes independent, a lab energy read as centre of mass, a stage rerun while the next one keeps the old numbers. Run the chain as fixed stages with checked handoffs, not as one long improvised session.

## Route the task

- One stage only: use that stage's skill directly.
- Several stages, a handoff between them, or a campaign to plan or resume: this skill.
- Project layout, claims register and handoff notes: `nuclear-research-project`. Proposal feasibility chains: `proposal-analysis`.

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
| 6 Review | `physics-referee` subagent | findings | — | blocking findings resolved; responses in `docs/VALIDATION.md` |
| 7 Write-up | writing skills, `prc-figures`, `research-slides` | text, figures | claims register | `check_claims.py` passes on the documents |

Skip stages that do not apply; do not reorder dependencies.

## At every stage boundary

1. **Check the input contract** before reading: `python3 scripts/contracts.py check CONTRACT FILE`. A violation stops the chain here. Do not patch the consumer around it.
2. **Convert with the adapters**, not by hand: `scripts/adapters.py efficiency-at`, `yields-to-excitation`, `to-azure` (units, frames, Sommerfeld factor and correlations are explicit; each writes a provenance sidecar). See [contracts.md](references/contracts.md) for what each handoff must carry, especially which uncertainties are shared.
3. **Record provenance** for outputs whose tool does not: `scripts/provenance.py record OUT --inputs ... --cmd ... --skill ...`.
4. **Update the state file** `docs/CHAIN.md` (template in [assets/CHAIN.md](assets/CHAIN.md)): stage, status, inputs, outputs, gate result, open items, next step. A new session resumes from this file, not from memory.
5. **Register the numbers** that will leave the project as claims (`nuclear-research-project`), with `depends_on` following the chain, so a rerun upstream flags everything downstream.

## Control rules

Read [orchestration.md](references/orchestration.md) before an unattended or multi-agent run.

- **Human checkpoints.** Stop and write a decision brief (question, options, evidence, recommendation, consequences, reversibility) before: excluding or re-extracting data; promoting a fit to master or changing a level scheme; choosing between analyses that give different results; overwriting results; runs longer than about an hour or above the agreed budget; anything that leaves the machine.
- **Bounded retries.** At most three attempts per stage, each a stated, different change. Record why each failed. Then stop and escalate with a brief. Never loosen a gate, edit data or edit tests to make a stage pass.
- **Parallel independent attempts** when the method choice is uncertain (background or peak model, target model, R-matrix hypothesis, channel radius): two to four subagents with distinct approaches, one success criterion written before they start, no access to each other's work. Agreement within uncertainty gives the result plus a method systematic; disagreement goes to cross-examination and then to the researcher.
- **Generation and judgement are separate.** The agent that produced a stage output does not approve its gate alone; use the review subagents or the researcher.
- **One stage per context** where practical. Heavy tool output goes to subagents; the state file carries what the next stage needs.

## Helpers

`python3 scripts/selftest.py` runs the yield and efficiency demos, checks the contracts against their real outputs and corrupted copies, verifies the adapters (frame, units, S factor → cross section) and the provenance check. It must print PASS. Standard library only for the scripts themselves.
