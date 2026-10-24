---
name: clear-experimental-writing
description: Write or revise experimental nuclear-astrophysics manuscripts with clear motivation, reproducible methods, transparent uncertainty and bounded physics interpretation. Use for abstracts, paper sections, captions, proceedings, thesis chapters, referee replies or full-paper restructuring of a measurement paper; use `methods-paper-style` for formalism and methods papers, `proposal-style` for proposals, `research-slides` for talks, and `unslop` only when asked to de-AI a text.
---
# Clear experimental writing

This skill makes the logic of a measurement paper easy to follow: astrophysical question → nuclear uncertainty → experimental gap → measurement strategy → observable extraction → uncertainty → comparison → consequence. A referee and a later reader judge the measurement through this chain, so a missing link reads as a missing piece of work. You need the draft or the results it reports, with their numbers and references. You get the revised passage or document, and a short note of the scientific ambiguities that remain.

## Where this fits

- Comes from: the results of an analysis, at the Write-up stage (7) of `analysis-chain`, with the numbers in the claims register of `nuclear-research-project`; figures from `prc-figures`.
- Goes to: the manuscript, proceedings or thesis chapter. Formalism and method sections follow `methods-paper-style`, proposals follow `proposal-style`, and a final `unslop` pass is made only when the user asks for one.
- Checked by: the `citation-checker` and `physics-referee` subagents, and the claims checker run on the manuscript.

## Guidance

Read the relevant sections of [manuscript-guide.md](references/manuscript-guide.md) for introduction structure, apparatus descriptions, analysis, uncertainty, captions or full-paper revision. Treat the proposed paragraph and section sequences as adaptable patterns, not a requirement to expand a short document.

Each paragraph should answer the reader's next question. Introduce the physical purpose before technical detail and the observable before its equation. Preserve quantitative details needed for reproducibility and distinguish measured, assumed and model-derived quantities.

For technically mature drafts, prefer the minimum restructuring and sentence-level edits needed. Preserve precise domain wording, energy-frame conventions, citations, numbers and necessary caveats. Never invent a reference, result, experimental justification or missing numerical value. Flag unresolved inconsistencies separately. If the project keeps a claims register (`docs/CLAIMS.toml`, see `nuclear-research-project`), quote numbers exactly as registered, add new ones there with their evidence, and run its checker on the manuscript.

Use restrained scientific English and explicit comparisons. Explain what simulation or fitting determines, how it was validated, and how uncertainty enters. Keep conclusions proportional to sensitivity. Apply this manuscript style rather than proposal rhetoric unless the user requests a proposal.

Before submission, or after drafting text with citations, delegate a check of every reference and attributed number to the `citation-checker` subagent if it is installed, and a check of the quantitative claims against the result files to `physics-referee`.

## What to deliver

Deliver the revised passage or document in the requested format. Briefly identify substantive scientific ambiguities that remain; do not add a long editorial checklist unless asked.
