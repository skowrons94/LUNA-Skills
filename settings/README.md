# Project guard

The skills tell the agent never to edit raw data and to ask before anything leaves the machine. Instructions can be ignored or forgotten after context compression. This hook makes the important ones mechanical.

| Tier | What | Decision |
|---|---|---|
| 2 | Edit/Write, or shell writes (`>`, `sed -i`, `cp` onto, `mv`, `rm`, …), under `data/raw/` or `data/external/` | denied, with the instruction to write a corrected copy to `data/processed/` |
| 1 | Changes under `r-matrix/master/`; `git push`, `gh pr/release create`, `scp`, `rsync` to a host, `curl` uploads, mail | asks you first |
| 0 | Everything else | normal permission rules |

Install into a project (merges into `.claude/settings.json`, keeps what is there):

```bash
python3 settings/install_guard.py /path/to/project
```

Edit `.claude/guard.json` in the project to change the protected paths, e.g. `{"deny": ["data/raw/", "data/external/", "tests/"], "ask": ["r-matrix/master/", "results/release/"]}`. Adding `tests/` to `deny` gives the "tests are the contract" rule: if a test looks wrong, the agent must say so instead of editing it.

`python3 settings/test_guard.py` checks the decisions on 21 cases. The shell check is a heuristic. It catches the usual write commands, not a deliberately obscured one, so keep backups and version control as the real protection. The installed hook points to this repository's `project_guard.py` by absolute path; reinstall if you move the repository.

Run unattended agents (for example `evals/run_evals.py tasks`) in a container or a disposable directory, and never with all permission checks disabled on a machine that holds data you cannot recreate.
