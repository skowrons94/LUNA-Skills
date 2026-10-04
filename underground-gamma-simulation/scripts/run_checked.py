#!/usr/bin/env python3
"""Run one flat, reviewed Geant4 application macro in a fresh directory; preserve provenance."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def prepare(text, events, seeds):
    lines = []
    initialized = False
    beams = outputs = 0
    # Deliberately only handle flat macros. Loops/includes can hide beamOn or output writes.
    forbidden = {
        "/control/execute",
        "/control/loop",
        "/control/foreach",
        "/control/shell",
        "/control/alias",
        "/control/unalias",
        "/control/if",
        "/control/doif",
    }
    for line in text.splitlines():
        active = line.split("#", 1)[0].strip()
        if not active:
            lines.append(line)
            continue
        cmd = active.split()[0]
        if cmd in forbidden or "{" in active or "}" in active:
            raise ValueError(
                "Expand includes, loops, aliases and shell commands into a reviewed flat macro first"
            )
        if cmd == "/run/initialize":
            initialized = True
        if cmd == "/analysis/filename":
            outputs += 1
            continue
        if cmd in {
            "/random/setSeeds",
            "/random/resetEngineFrom",
            "/random/setSequence",
            "/run/printProgress",
        }:
            continue
        if cmd == "/run/beamOn":
            if not initialized:
                raise ValueError("Expected /run/initialize before /run/beamOn")
            beams += 1
            lines += [
                "/analysis/filename result.root",
                f"/random/setSeeds {seeds[0]} {seeds[1]}",
                f"/run/printProgress {max(1, events // 10)}",
                f"/run/beamOn {events}",
            ]
        else:
            lines.append(line)
    if beams != 1 or outputs != 1:
        raise ValueError("Expected exactly one /run/beamOn and one /analysis/filename")
    return "\n".join(lines) + "\n"


def assess(log, returncode, events, output):
    errors = []
    if returncode != 0:
        errors.append(f"Process status: {returncode}")
    markers = r"COMMAND NOT FOUND|Illegal application state|parameter out of range|parameter value is not listed|COMMAND REFUSED|Batch is interrupted|FatalException|Fatal Error|Segmentation fault|segmentation violation|Error in <TFile|cannot open|Cannot open|Cannot create|GeomVol1002|Overlap is detected"
    errors += [s.strip() for s in log.splitlines() if re.search(markers, s, re.I)]
    counts = re.findall(r"Number of events:\s*(\d+)", log)
    if counts != [str(events)]:
        errors.append(f"Expected one completed run of {events} events, found {counts}")
    if not output.is_file() or output.stat().st_size < 100:
        errors.append("Missing or empty ROOT output")
    else:
        with output.open("rb") as f:
            if f.read(4) != b"root":
                errors.append("Output lacks ROOT file signature")
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", required=True, type=Path)
    p.add_argument("--macro", required=True, type=Path)
    p.add_argument(
        "--out", required=True, type=Path, help="New directory; must not exist"
    )
    p.add_argument("--events", type=int, default=1000)
    p.add_argument("--seeds", nargs=2, type=int, default=[12345, 67890])
    p.add_argument("--timeout", type=float, default=300)
    a = p.parse_args()
    if a.events < 1 or any(x < 1 or x > 2147483647 for x in a.seeds) or a.timeout <= 0:
        p.error("Use positive events/timeout and seeds in 1..2147483647")
    exe, macro, out = a.exe.resolve(), a.macro.resolve(), a.out.resolve()
    if not exe.is_file() or not os.access(exe, os.X_OK):
        p.error("Executable is missing or not executable")
    generated = prepare(macro.read_text(), a.events, a.seeds)
    out.mkdir(parents=True, exist_ok=False)
    (out / "input.mac").write_text(generated)
    env = {k: v for k, v in os.environ.items() if k.startswith("G4")}
    manifest = dict(
        executable=str(exe),
        executable_sha256=sha(exe),
        original_macro=str(macro),
        original_macro_sha256=sha(macro),
        macro_sha256=sha(out / "input.mac"),
        events=a.events,
        seeds=a.seeds,
        data_environment=env,
        command=[str(exe), "-m", "input.mac", "-s", str(a.seeds[0])],
    )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    start = time.monotonic()
    with (out / "run.log").open("w") as log:
        try:
            result = subprocess.run(
                manifest["command"],
                cwd=out,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=a.timeout,
            )
            rc = result.returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
        except OSError as e:
            rc = str(e)
    text = (out / "run.log").read_text(errors="replace")
    errors = assess(text, rc, a.events, out / "result.root")
    manifest.update(
        returncode=rc,
        elapsed_seconds=time.monotonic() - start,
        execution_checks_passed=not errors,
        errors=errors,
        warnings=[
            s.strip()
            for s in text.splitlines()
            if re.search(r"warning|non-critical error|exception", s, re.I)
        ],
    )
    if (out / "result.root").is_file():
        manifest["output_sha256"] = sha(out / "result.root")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "directory": str(out),
                "execution_checks_passed": not errors,
                "errors": errors,
                "next": "Inspect ROOT branches and validate physics separately",
            },
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
