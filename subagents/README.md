# Subagents

Claude Code subagents that check work rather than produce it. Each runs in its own context with read-only file tools, so it judges the files instead of inheriting the reasoning of the agent that made them. A model that produces a plausible fit or paragraph is not automatically good at judging it; a second agent with a fresh context and a checklist catches different errors.

| Agent | Use it for |
|---|---|
| `data-auditor` | Input data before a fit: units, frames, uncertainty types, transcription copies, overlaps, provenance |
| `physics-referee` | A finished result: recomputes key numbers, checks corrections, covariances, physics limits and claims |
| `citation-checker` | References and attributed numbers in a manuscript, proposal or talk |

Install (Claude Code reads personal subagents from `~/.claude/agents/`):

```bash
mkdir -p ~/.claude/agents
for a in subagents/*.md; do [ "$(basename "$a")" = README.md ] || ln -sfn "$PWD/$a" ~/.claude/agents/; done
```

Ask for them by name ("have the physics-referee check results/yields.csv against the run sheets") or let the skills delegate to them. Give them the files and the claim to check, not an explanation of why it is right. They report; the researcher decides what to change, and the decision goes into the project's `docs/VALIDATION.md`.

The agents inherit the session's model. To trade depth for cost, add `model: sonnet` (or another alias) to an agent's frontmatter.
