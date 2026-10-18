#!/usr/bin/env python3
"""Offline test of create_proposal_project.py: dry run writes nothing, creation works, nothing is overwritten,
--merge restores missing template files, a file or non-empty directory as target is refused, and
--tools / --study add the tool directories and per-study REPORT.md and results.json.
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

with tempfile.TemporaryDirectory() as tmp:
    target = Path(tmp) / "TOOLS"
    sink = io.StringIO()
    check("tools: bad study name refused", C.create(target, "T", "x", studies=("geant4/a",), out=sink) == 2)
    check("tools: bad study name writes nothing", not target.exists())
    check("tools: create returns 0", C.create(target, "T", "x", tools=True, out=sink) == 0)
    for rel in ("r-matrix/master/.gitkeep", "r-matrix/studies/.gitkeep", "simulation/.gitkeep",
                "transport/.gitkeep", "docs/ENVIRONMENT.md"):
        check(f"tools: exists {rel}", (target / rel).exists())
    check("tools: no .gitkeep in ignored r-matrix/runs and analysis/chains",
          (target / "r-matrix/runs").is_dir() and not (target / "r-matrix/runs/.gitkeep").exists()
          and (target / "analysis/chains").is_dir() and not (target / "analysis/chains/.gitkeep").exists())
    gi = (target / ".gitignore").read_text()
    check("tools: .gitignore covers builds, ROOT files, statepoint runs, chains",
          all(r in gi for r in ("simulation/*/build/", "*.root", "transport/*/runs/", "analysis/chains/")))
    check("tools: .gitignore does not ignore JSON", "*.json" not in gi)
    check("tools: merge adds a simulation study",
          C.create(target, "T", "x", merge=True, studies=("simulation/counter-eff",), out=sink) == 0)
    study = target / "simulation/counter-eff"
    for sub in ("src", "macros", "scripts", "runs"):
        check(f"tools: study has {sub}/", (study / sub).is_dir())
    rep = (study / "REPORT.md").read_text()
    check("tools: study REPORT.md rendered", "counter-eff" in rep and "@@" not in rep)
    import json
    check("tools: study results.json is valid JSON", json.loads((study / "results.json").read_text())["study"]
          == "counter-eff")
    check("tools: study dir itself has no stray .gitkeep", not (study / ".gitkeep").exists())
    (study / "REPORT.md").write_text("edited")
    check("tools: transport study added by merge",
          C.create(target, "T", "x", merge=True, studies=("transport/shield", "simulation/counter-eff"),
                   out=sink) == 0)
    check("tools: transport study has model/ and runs/", (target / "transport/shield/model").is_dir()
          and (target / "transport/shield/runs").is_dir())
    check("tools: merge never overwrites a study report", (study / "REPORT.md").read_text() == "edited")
    check("tools: simulation study has inputs/ (tracked inputs)", (study / "inputs/.gitkeep").exists())
    check("tools: no .gitkeep in ignored transport runs/", not (target / "transport/shield/runs/.gitkeep").exists())

with tempfile.TemporaryDirectory() as tmp:  # existing project with an old .gitignore
    target = Path(tmp) / "OLD"
    target.mkdir()
    (target / ".gitignore").write_text("private/\n")
    sink = io.StringIO()
    check("old project: merge with --tools returns 0", C.create(target, "O", "x", merge=True, tools=True, out=sink) == 0)
    msg = sink.getvalue()
    check("old project: .gitignore left unchanged", (target / ".gitignore").read_text() == "private/\n")
    check("old project: missing tool ignore rules are listed", "add these lines by hand" in msg
          and "analysis/chains/" in msg and "*.root" in msg)
    (target / ".gitignore").write_text((C.Path(C.__file__).resolve().parent.parent / "assets/proposal-template/_gitignore").read_text())
    sink = io.StringIO()
    C.create(target, "O", "x", merge=True, tools=True, out=sink)
    check("old project: no message once the rules are present", "add these lines by hand" not in sink.getvalue())

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
