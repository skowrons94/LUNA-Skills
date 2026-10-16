#!/usr/bin/env python3
"""Offline test of create_proposal_project.py: dry run writes nothing, creation works, nothing is overwritten.
Run: python3 test_create_proposal_project.py   -> prints PASS/FAIL lines, exit code 1 on failure."""

import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import create_proposal_project as C  # noqa: E402

ok = True


def check(name, cond):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}")


with tempfile.TemporaryDirectory() as tmp:
    target = Path(tmp) / "ACME"
    sink = io.StringIO()
    check("dry run returns 0", C.create(target, "ACME", "Test call 2099", dry_run=True, out=sink) == 0)
    check("dry run writes nothing", not target.exists())
    check("create returns 0", C.create(target, "ACME", "Test call 2099", out=sink) == 0)
    for rel in ("proposal/source", "proposal/archive", "analysis/results", "docs/CALL.md",
                "docs/OBJECTIONS.md", "docs/FINAL_CHECKLIST.md", "proposal/numbers.tex", ".gitignore"):
        check(f"exists {rel}", (target / rel).exists())
    readme = (target / "README.md").read_text()
    check("tokens rendered", "ACME" in readme and "@@" not in readme)
    check("private is git-ignored", "private/" in (target / ".gitignore").read_text())
    (target / "docs/DECISIONS.md").write_text("user content")
    check("refuses non-empty without --merge", C.create(target, "ACME", "x", out=sink) == 2)
    check("merge returns 0", C.create(target, "ACME", "x", merge=True, out=sink) == 0)
    check("merge never overwrites", (target / "docs/DECISIONS.md").read_text() == "user content")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
