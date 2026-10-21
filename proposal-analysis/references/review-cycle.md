# Simulated review cycle

Simulated reviewers find weaknesses before real ones do. They do not replace colleagues who read the proposal as hostile referees before submission.

## Reviewers

- **Panel generalist** (the call's panel, outside the subfield): is the question clear in the first half page; is the case ambitious, coherent and feasible; is the applicant's independence visible; score with the call's scale.
- **Specialist referee** (the subfield): physics and attribution errors, unfair characterisation of prior work, feasibility details, whether each number survives checking against its source and script. Give the specialist read access to the analysis outputs and scripts and ask for re-runs. The `physics-referee` subagent is a ready-made specialist for the numbers; `citation-checker` verifies references and attributed values.
- **Style editor** (the applicant's style guide, e.g. `proposal-style`): reading flow, sentence length in commitments, one claim per sentence, repetition between parts, consistency of numbers and wording.

## Rules

- Tell every reviewer to ignore applicant-only placeholders (`[[...]]`) and to judge the proposal as written.
- Each reviewer writes to a file per round (`proposal/review/rN_<role>.md`) with ranked weaknesses and exact replacement text.
- Numbers suggested by reviewers are hypotheses: recompute them before use (see SKILL.md boundary 5). A reviewer may also be wrong; check its re-derivations.
- Apply all points, or record in the objections register why not; log number changes in the decision register.
- Iterate until the reviewers' remaining points are wording or applicant-only inputs, then run one confirmation round. Scores are a heuristic, not a forecast.
