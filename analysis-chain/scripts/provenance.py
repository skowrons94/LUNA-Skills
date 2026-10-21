#!/usr/bin/env python3
"""Provenance sidecars: OUT.prov.json next to any output, recording how it was made.

  python3 provenance.py record OUT --inputs A B --cmd "AZURE2 --no-gui ... " --skill azure2 \
          [--tool AZURE2=4.1.0 --tool geant4=11.3] [--note TEXT]
  python3 provenance.py verify OUT.prov.json      inputs and output unchanged since recording?

The sidecar holds SHA-256 of the output and every input (paths relative to the sidecar), the
command, the project's git commit and dirty flag, the skills repository commit and the hash of
the SKILL.md that guided the step, tool versions, Python and platform, and the time. Use it for
steps whose tool does not record provenance itself (AZURE2 and Geant4 runs, adapters, ad-hoc
scripts). Standard library only.
"""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

SKILLS_REPO = Path(__file__).resolve().parents[2]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(cwd, *args):
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def record(out, inputs, cmd="", skill=None, tools=None, note=""):
    out = Path(out).resolve()
    side = out.with_name(out.name + ".prov.json")
    base = side.parent
    rel = lambda p: os.path.relpath(Path(p).resolve(), base)
    proj = out.parent
    skill_md = SKILLS_REPO / skill / "SKILL.md" if skill else None
    rec = {
        "output": {"path": rel(out), "sha256": sha(out)},
        "inputs": [{"path": rel(p), "sha256": sha(p)} for p in inputs],
        "command": cmd,
        "cwd": os.getcwd(),
        "project_git": {"commit": git(proj, "rev-parse", "HEAD"),
                        "dirty": bool(git(proj, "status", "--porcelain"))},
        "skill": {"name": skill, "skills_commit": git(SKILLS_REPO, "rev-parse", "--short", "HEAD"),
                  "skill_md_sha256": sha(skill_md) if skill_md and skill_md.exists() else None} if skill else None,
        "tools": tools or {},
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "note": note,
    }
    side.write_text(json.dumps(rec, indent=2) + "\n")
    return side


def verify(side):
    side = Path(side).resolve()
    rec = json.loads(side.read_text())
    problems = []
    for item in [rec["output"], *rec["inputs"]]:
        p = side.parent / item["path"]
        if not p.exists():
            problems.append(f"missing: {item['path']}")
        elif sha(p) != item["sha256"]:
            problems.append(f"changed since recorded: {item['path']}")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("out")
    r.add_argument("--inputs", nargs="*", default=[])
    r.add_argument("--cmd", default="")
    r.add_argument("--skill")
    r.add_argument("--tool", action="append", default=[], help="NAME=VERSION")
    r.add_argument("--note", default="")
    v = sub.add_parser("verify")
    v.add_argument("sidecar")
    a = ap.parse_args()
    if a.cmd == "record":
        tools = dict(t.split("=", 1) for t in a.tool)
        print(record(a.out, a.inputs, a.cmd, a.skill, tools, a.note))
        return 0
    probs = verify(a.sidecar)
    for p in probs:
        print(f"PROBLEM  {p}")
    print("OK" if not probs else f"{len(probs)} problem(s)")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
