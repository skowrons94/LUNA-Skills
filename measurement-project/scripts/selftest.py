#!/usr/bin/env python3
"""Selftest of the measurement-project scripts; prints PASS.

1. A new project passes the check with no errors and its root CLAIMS.toml is accepted by
   nuclear-research-project/scripts/check_claims.py; a second create changes nothing (non-destructive).
2. A logbook.csv with the required columns and a raw file listed in file_map.csv with its checksum pass --verify.
3. Corruptions are caught: an edited raw file (checksum), an unknown purpose, a missing logbook column, a missing
   register, and a stray *.bak in a stage (warning, error with --strict).
"""
import csv
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CREATE, CHECK = HERE / "create_measurement_project.py", HERE / "check_measurement_project.py"
COLS = ["run", "file", "start", "stop", "real_s", "live_s", "charge_C", "charge_source", "current_uA", "Ep_keV",
        "Ep_source", "target", "purpose", "geometry", "source_id", "flags", "notes"]


def run(*args):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "14npg_bgo_solid_2023-2025"
        rc, out = run(CREATE, p, "--reaction", "14npg", "--setup", "bgo", "--target", "solid", "--years", "2023-2025")
        if rc:
            fails.append("create failed: " + out)
        rc, out = run(CHECK, p)
        if rc or "0 errors" not in out:
            fails.append("fresh project does not pass: " + out)
        claims = HERE.parents[1] / "nuclear-research-project" / "scripts" / "check_claims.py"
        if claims.exists():
            rc, out = run(claims, p)
            if rc:
                fails.append("check_claims does not accept the root CLAIMS.toml: " + out)
        (p / "HANDOFF.md").write_text("edited by the user\n")
        run(CREATE, p)
        if (p / "HANDOFF.md").read_text() != "edited by the user\n":
            fails.append("create overwrote an existing file")
        raw = p / "data" / "raw" / "2025-02" / "run_1.txt"
        raw.parent.mkdir(parents=True)
        raw.write_text("counts\n")
        h = hashlib.sha256(raw.read_bytes()).hexdigest()
        with open(p / "data" / "file_map.csv", "a", newline="") as f:
            csv.writer(f).writerow(["/server/run_1.txt", "data/raw/2025-02/run_1.txt", h, "test"])
        (p / "data" / "MANIFEST.sha256").write_text(f"{h}  raw/2025-02/run_1.txt\n")
        row = dict.fromkeys(COLS, "")
        row.update(run="run_1", purpose="long_run", file="data/root/2025-02/run_1.root")
        (p / "data" / "root" / "2025-02").mkdir(parents=True)
        (p / "data" / "root" / "2025-02" / "run_1.root").write_bytes(b"root")
        with open(p / "data" / "logbook.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerow(row)
        with open(p / "data" / "file_map.csv", "a", newline="") as f:      # a member of a packed archive
            csv.writer(f).writerow(["/server/b.tar", "data/raw/2025-02/backups.tar:old/run_1.txt~", "0" * 64, "packed"])
        (p / "data" / "raw" / "2025-02" / "backups.tar").write_bytes(b"tar")
        (p / "analysis" / "06_yield" / "results" / "fit_ep140_MrX.csv").write_text("x\n")   # original target name
        rc, out = run(CHECK, p, "--verify")
        if rc or "uppercase" in out:
            fails.append("valid data (archive member, original target name) do not pass --verify cleanly: " + out)
        raw.write_text("counts edited\n")
        rc, out = run(CHECK, p, "--verify")
        if not rc or "checksum mismatch" not in out:
            fails.append("edited raw file not caught")
        raw.write_text("counts\n")
        row["purpose"] = "longrun"
        with open(p / "data" / "logbook.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerow(row)
        rc, out = run(CHECK, p)
        if not rc or "purpose" not in out:
            fails.append("unknown purpose not caught")
        with open(p / "data" / "logbook.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS[:-3])
            w.writeheader()
        rc, out = run(CHECK, p)
        if not rc or "missing columns" not in out:
            fails.append("missing logbook columns not caught")
        with open(p / "data" / "logbook.csv", "w", newline="") as f:
            csv.DictWriter(f, fieldnames=COLS).writeheader()
        (p / "PROBLEMS.md").unlink()
        rc, out = run(CHECK, p)
        if not rc or "PROBLEMS.md" not in out:
            fails.append("missing register not caught")
        run(CREATE, p)
        (p / "analysis" / "06_yield" / "fit.py.bak").write_text("")
        rc, out = run(CHECK, p)
        rc2, _ = run(CHECK, p, "--strict")
        if rc or not rc2 or "stray" not in out:
            fails.append("stray file: warning without --strict, error with it, expected")
    for f in fails:
        print("FAIL:", f)
    print("PASS" if not fails else "FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
