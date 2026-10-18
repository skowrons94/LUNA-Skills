#!/usr/bin/env python3
"""Run any simulation executable in a fresh directory and judge it on more than its return code.

Generic counterpart of underground-gamma-simulation/scripts/run_checked.py: no macro rewriting and no
ROOT assumption. It copies the input files named on the command line into the run directory (so the
inputs that ran are kept), captures the log, scans it for Geant4 failure markers, checks that the
expected outputs exist and parse, applies numeric thresholds to JSON outputs, and writes manifest.json
(command, hashes, environment, datasets, host load, timing, verdict). Standard library only.

    python3 run_checked.py --out /data/runs/smoke-1 --expect out/smoke_r0.json \\
        --json-min out/smoke_r0.json:gas_captures=1 --timeout 600 --nice 10 \\
        -- /path/build/ncounter macros/smoke.mac --seeds 12345 67890
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

FAIL_MARKERS = re.compile(
    r"-+ EEEE -+ G4Exception-START|\*\*\* Fatal Exception|G4Exception: Aborting|Segmentation fault|"
    r"segmentation violation|COMMAND NOT FOUND|Illegal application state|parameter out of range|"
    r"command refused|Batch is interrupted|Overlap is detected|\*\*\* Break \*\*\*|std::bad_alloc|"
    r"core dumped")
WARN_MARKER = re.compile(r"-+ WWWW -+ G4Exception-START")
ENV_KEYS = re.compile(r"^(G4\w*DATA|G4\w*|OPENMC_\w+|CONDA_PREFIX|OMP_NUM_THREADS|LD_LIBRARY_PATH)$")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_state(src: Path) -> dict:
    def g(*args):
        r = subprocess.run(["git", "-C", str(src), *args], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    return {"path": str(src), "revision": g("rev-parse", "HEAD"), "dirty": bool(g("status", "--porcelain"))}


def json_threshold(run_dir: Path, spec: str) -> str | None:
    """'file.json:key=min' (key may be dotted). Returns a problem string or None."""
    try:
        target, rest = spec.rsplit(":", 1)
        key, minimum = rest.split("=", 1)
        value = json.loads((run_dir / target).read_text())
        for part in key.split("."):
            value = value[part]
        if float(value) < float(minimum):
            return f"{target}:{key} = {value} < {minimum}"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return f"cannot evaluate {spec}: {exc}"
    return None


def run(out: Path, command: list[str], expect=(), json_min=(), timeout=None, nice=0, source=None,
        copy_inputs=True) -> dict:
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"run directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    exe = shutil.which(command[0]) or command[0]
    args, inputs = [exe], {}
    for a in command[1:]:
        p = Path(a)
        if copy_inputs and p.is_file():
            dest = out / "inputs" / p.name
            dest.parent.mkdir(exist_ok=True)
            shutil.copy2(p, dest)
            inputs[a] = {"copied_to": str(dest.relative_to(out)), "sha256": sha256(p)}
            args.append(str(dest.resolve()))
        else:
            args.append(a)
    if nice:
        args = ["nice", "-n", str(nice)] + args
    manifest = {
        "command": command, "executed": args, "cwd": str(out.resolve()),
        "executable": {"path": exe, "sha256": sha256(Path(exe)) if Path(exe).is_file() else None},
        "inputs": inputs, "source": git_state(source) if source else None,
        "environment": {k: v for k, v in sorted(os.environ.items()) if ENV_KEYS.match(k)},
        "host": {"name": platform.node(), "cpus": os.cpu_count(),
                 "load_avg": os.getloadavg() if hasattr(os, "getloadavg") else None,
                 "python": sys.version.split()[0]},
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    t0 = time.time()
    log_path = out / "run.log"
    with open(log_path, "w") as log:
        try:
            rc = subprocess.run(args, cwd=out, stdout=log, stderr=subprocess.STDOUT, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
    manifest["wall_s"] = round(time.time() - t0, 3)
    manifest["return_code"] = rc
    text = log_path.read_text(errors="replace")
    problems = []
    if rc != 0:
        problems.append(f"return code {rc}")
    hits = [m.group(0) for m in FAIL_MARKERS.finditer(text)]
    problems += [f"log: {h} (x{hits.count(h)})" for h in dict.fromkeys(hits)]
    manifest["warnings_in_log"] = len(WARN_MARKER.findall(text))
    outputs = {}
    for rel in expect:
        p = out / rel
        if not p.is_file() or p.stat().st_size == 0:
            problems.append(f"missing or empty output: {rel}")
            continue
        outputs[rel] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
        if p.suffix == ".json":
            try:
                json.loads(p.read_text())
            except ValueError as exc:
                problems.append(f"invalid JSON {rel}: {exc}")
    for spec in json_min:
        msg = json_threshold(out, spec)
        if msg:
            problems.append(msg)
    manifest.update(outputs=outputs, problems=problems, status="ok" if not problems else "failed")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True, help="new, empty run directory")
    ap.add_argument("--expect", action="append", default=[], help="output file relative to the run directory")
    ap.add_argument("--json-min", action="append", default=[], metavar="FILE:KEY=MIN")
    ap.add_argument("--timeout", type=float, default=None, help="seconds")
    ap.add_argument("--nice", type=int, default=0, help="run at lower priority on shared machines")
    ap.add_argument("--source", type=Path, help="source checkout to record (git revision, dirty flag)")
    ap.add_argument("--no-copy", action="store_true", help="do not copy input files into the run directory")
    ap.add_argument("command", nargs=argparse.REMAINDER, help="-- EXECUTABLE ARGS...")
    a = ap.parse_args(argv)
    cmd = a.command[1:] if a.command[:1] == ["--"] else a.command
    if not cmd:
        ap.error("give the command after --")
    m = run(a.out, cmd, a.expect, a.json_min, a.timeout, a.nice, a.source, not a.no_copy)
    print(json.dumps({"status": m["status"], "problems": m["problems"], "wall_s": m["wall_s"],
                      "warnings_in_log": m["warnings_in_log"], "manifest": str(a.out / "manifest.json")}, indent=2))
    return 0 if m["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
