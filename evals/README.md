# Agent evaluations

The demos and selftests in each skill check the scripts. These evaluations check the agent that uses them: does a request load the right skill, and does the agent avoid the traps the skills warn about? A skill edit is a change to the analysis method; run the relevant evaluations before relying on it.

```bash
python3 evals/run_evals.py selftest                      # offline, free: checkers and routing file
python3 evals/run_evals.py routing --model sonnet         # ~1 cent per prompt
python3 evals/run_evals.py tasks --only peak-doublet --keep
python3 evals/run_evals.py report
```

`routing` and `tasks` run `claude -p` in a fresh temporary directory whose `.claude/skills` links to this working tree, with user and global settings not loaded. Tasks accept edits and allow Bash inside that directory, with a cost cap per run (`--budget`). Run them where that is acceptable, preferably in a container.

## Contents

| File | Purpose |
|---|---|
| `routing.jsonl` | Requests labelled with the skill that should load first (`none` for requests no skill covers). Near-misses matter most: yield vs peak shape, r-matrix vs resonance-search, the three Geant4 skills, the writing skills. |
| `tasks.py` | Graded tasks with deterministic synthetic fixtures and a known answer. Most carry a trap a careless analysis falls into. |
| `run_evals.py` | Runner, offline selftest and report. |
| `ledger.jsonl` | One line per run: model, git commit, dirty flag, SKILL.md hashes, skills invoked, checks, cost, time. Commit it. |

## Tasks

| Task | Known answer | Trap |
|---|---|---|
| `yield-basic` | Generated peak area and normalisation | Forgetting the live fraction |
| `yield-units-trap` | Normalisation | Charge in µC; a field named `deadTime` that holds the live fraction |
| `peak-doublet` | Generated area of the weaker line | Sideband subtraction under a 6 keV doublet |
| `negative-net-area` | Exact sideband result | Clipping a negative net area to zero |
| `efficiency-decay` | Generated efficiencies | Not decay-correcting certified activities (5 y, ⁶⁰Co) |
| `raw-data-immutable` | — | Editing `data/raw/` in place instead of writing a corrected copy and recording why |

## Rules

- **Validate the validators.** Every task has a `reference` answer that must pass and a `baseline` answer (a common mistake) that must fail; `selftest` enforces both. A checker that a trivial answer also passes does not measure anything.
- **Agents are not deterministic.** Use `--repeat 3` or more before concluding that a change helped. Compare pass rates at the same model.
- **Grade outcomes, not wording.** Checkers read `answer.json` and files on disk. Do not reward a method the user did not ask for.
- **Grow the set from failures.** When an agent makes a mistake in real work, reduce it to a fixture with a known answer and add it here, with its reference and baseline.

## Adding a task

Add a class to `tasks.py` with `id`, `skills`, `prompt`, `generate(d)`, `check(d, truth)`, `reference(d, truth)` and `baseline(d, truth)`, register it in `TASKS`, and run `selftest`. Fixtures must be synthetic or published values, deterministic, and small.
