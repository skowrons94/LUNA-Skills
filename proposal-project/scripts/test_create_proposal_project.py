#!/usr/bin/env python3
"""Offline test of create_proposal_project.py: dry run writes nothing, creation works, nothing is overwritten,
--merge restores missing template files, and a file or non-empty directory as target is refused.
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
    check("empty directories keep a .gitkeep", (target / "analysis/results/.gitkeep").exists()
          and (target / "proposal/source/.gitkeep").exists())
    check("no .gitkeep in private/", not (target / "private/.gitkeep").exists())
    (target / "docs/DECISIONS.md").write_text("user content")
    check("refuses non-empty without --merge", C.create(target, "ACME", "x", out=sink) == 2)
    check("merge returns 0", C.create(target, "ACME", "x", merge=True, out=sink) == 0)
    check("merge never overwrites", (target / "docs/DECISIONS.md").read_text() == "user content")
    check("dry run on a non-empty directory without --merge returns 2",
          C.create(target, "ACME", "x", dry_run=True, out=sink) == 2)
    (target / "docs/CALL.md").unlink()
    check("merge returns 0 after a template file was deleted", C.create(target, "ACME", "x", merge=True, out=sink) == 0)
    check("merge restores the deleted template file", (target / "docs/CALL.md").exists())
    a_file = Path(tmp) / "not_a_dir"
    a_file.write_text("x")
    check("target that is a file is refused (returns 2)", C.create(a_file, "ACME", "x", merge=True, out=sink) == 2)
    check("file target left unchanged", a_file.read_text() == "x")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
