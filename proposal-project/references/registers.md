# Registers

Four short files keep a proposal honest across many revisions. Keep each entry dated and specific.

## docs/DECISIONS.md

One entry per decision that changes framing, scope or a quoted number.

```
## D-NNN (YYYY-MM-DD): pilot number replaced after convergence check
- What: <quantity> <old value> → <new value> in <section>, <section>, <figure>.
- Why: longer chains with corrected priors; quantile-stability test in analysis/results/<file>.json.
- Consequence: dependent numbers updated; objection #<n> closed.
```

## docs/OBJECTIONS.md

A table of every reviewer objection, real or simulated.

| # | Objection (who, round) | Answer in the text | Status | Evidence |
|---|---|---|---|---|
| 1 | Selection of comparison cases looks hand-picked (specialist, rN) | explicit rule, exclusion table, sensitivity variants | answered | analysis/results/<file>.json |

Status values: answered (with evidence) · partly answered · open (needs new work or PI input). An objection is closed only when the text and the evidence both exist.

## docs/INPUTS_PI.md

Facts and decisions given by the applicant, copied as received with the date: budget route, collaborators who agreed to be named, roles, equipment loans, facility statements, personal constraints relevant to the call. These override assumptions elsewhere.

## docs/FINAL_CHECKLIST.md

- Every remaining placeholder, grouped (letters, quotes, CV/personal, facility confirmations, references to verify), with file and line.
- Analysis items that should be redone before submission (longer chains, refits under final priors, figures).
- Call checks: template edition, page limits per part, font and margins, budget caps and categories, ethics and data-management sections, mandatory annexes.
- Consistency checks: numbers identical across parts and figures; questions and objectives worded identically where repeated; references resolve.
- File locations of the final PDFs and sources.
