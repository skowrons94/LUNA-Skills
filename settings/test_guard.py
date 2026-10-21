#!/usr/bin/env python3
"""Self-test of project_guard.py decisions. Prints PASS/FAIL lines; exit 1 on failure."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from project_guard import decide  # noqa: E402

ok = True

with tempfile.TemporaryDirectory() as t:
    root = Path(t)
    for d in ("data/raw", "data/processed", "data/external", "r-matrix/master", "results"):
        (root / d).mkdir(parents=True)
    cases = [
        ({"tool_name": "Edit", "tool_input": {"file_path": str(root / "data/raw/a.csv")}}, "deny"),
        ({"tool_name": "Write", "tool_input": {"file_path": "data/external/exfor.txt"}}, "deny"),
        ({"tool_name": "Write", "tool_input": {"file_path": "data/processed/a.csv"}}, None),
        ({"tool_name": "Edit", "tool_input": {"file_path": "r-matrix/master/model.azr"}}, "ask"),
        ({"tool_name": "Read", "tool_input": {"file_path": "data/raw/a.csv"}}, None),
        ({"tool_name": "Bash", "tool_input": {"command": "sed -i 's/1250/125/' data/raw/a.csv"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "sed 's/1250/125/' data/raw/a.csv > data/processed/a.csv"}}, None),
        ({"tool_name": "Bash", "tool_input": {"command": "python3 fix.py > data/raw/a.csv"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "cat data/raw/a.csv | head"}}, None),
        ({"tool_name": "Bash", "tool_input": {"command": "cp data/raw/a.csv data/processed/a.csv"}}, None),
        ({"tool_name": "Bash", "tool_input": {"command": "cp new.csv data/raw/a.csv"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "rm -rf data/external"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "mv data/raw/a.csv old/"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "cd x && git push origin main"}}, "ask"),
        ({"tool_name": "Bash", "tool_input": {"command": "git status && git diff"}}, None),
        ({"tool_name": "Bash", "tool_input": {"command": "curl -s https://www-nds.iaea.org/x.json -o d.json"}}, None),
        ({"tool_name": "Bash", "tool_input": {"command": "curl -X POST -d @r.json https://api.example.org"}}, "ask"),
        ({"tool_name": "Bash", "tool_input": {"command": "rsync -av results/ user@cluster:/scratch/"}}, "ask"),
        ({"tool_name": "Bash", "tool_input": {"command": "gh pr create --fill"}}, "ask"),
        ({"tool_name": "Bash", "tool_input": {"command": "AZURE2 --no-gui r-matrix/master/model.azr"}}, None),
        ({"tool_name": "Bash", "tool_input": {"command": "cp runs/best.azr r-matrix/master/model.azr"}}, "ask"),
    ]
    for ev, want in cases:
        got, why = decide(ev, root)
        good = got == want
        ok &= good
        what = ev["tool_input"].get("command") or ev["tool_input"].get("file_path")
        print(f"{'PASS' if good else 'FAIL'}  {ev['tool_name']:5s} {what!r:70.70s} -> {got} (want {want})")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
