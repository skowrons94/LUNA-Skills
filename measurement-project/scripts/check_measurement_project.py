#!/usr/bin/env python3
"""Check a measurement project against the layout of the measurement-project skill.

Errors: missing registers or main folders, a logbook.csv without the required columns or with an unknown purpose,
file_map.csv without its header, checksum mismatches (with --verify); members of packed archives (`x.tar:member`) only
need the archive. Warnings: stray file names (*.bak, *copy*, tmp*, _out_*, .DS_Store), uppercase names of authored files
or folders, stages without README, logbook rows whose ROOT file is missing, CHAIN.md or CLAIMS.toml missing.
Exit code 1 on errors (also on warnings with --strict).

Usage: python3 check_measurement_project.py PATH [--verify] [--strict]
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import re
import sys
from pathlib import Path

REGISTERS = ["README.md", "CLAUDE.md", "HANDOFF.md", "PROBLEMS.md", "LITERATURE.md", "DECISIONS.md",
             "ASSUMPTIONS.md", "CHANGELOG.md"]
FOLDERS = ["data/raw", "data/root", "docs", "analysis", "tools", "report", "slides"]
LOGBOOK_COLS = ["run", "file", "start", "stop", "real_s", "live_s", "charge_C", "charge_source", "current_uA",
                "Ep_keV", "Ep_source", "target", "purpose", "geometry", "source_id", "flags", "notes"]
PURPOSES = {"scan", "long_run", "background", "source", "calibration", "test", "excluded"}
STRAY = ["*.bak", "*.orig", "*copy*", "tmp*", "_out_*", "*~", ".ds_store"]
AUTHORED = {".py", ".md", ".tex", ".sh", ".toml", ".yaml", ".yml"}   # files people write: lowercase names
UPPER_OK = set(REGISTERS) | {"CHAIN.md", "CLAIMS.toml", "MANIFEST.sha256", "Makefile"}
SKIP_DIRS = {".git", "_claude", "build", "__pycache__"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(root: Path, sub: str):
    base = root / sub
    if not base.exists():
        return
    for p in base.rglob("*"):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        yield p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", type=Path)
    ap.add_argument("--verify", action="store_true", help="recompute checksums of file_map.csv and MANIFEST.sha256")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    root = a.path.resolve()
    err, warn = [], []
    for f in REGISTERS:
        if not (root / f).is_file():
            err.append(f"missing register {f}")
    for f in ("CHAIN.md", "CLAIMS.toml"):
        if not (root / f).is_file():
            warn.append(f"missing {f} (analysis-chain state / claims register)")
    for d in FOLDERS:
        if not (root / d).is_dir():
            err.append(f"missing folder {d}/")
    if (root / "report").is_dir() and not (root / "report" / "Makefile").is_file():
        warn.append("report/Makefile missing (build into report/build/)")
    # stages
    for st in sorted((root / "analysis").glob("*")) if (root / "analysis").is_dir() else []:
        if st.is_dir():
            if not re.fullmatch(r"\d\d_[a-z0-9_]+", st.name):
                warn.append(f"analysis/{st.name}: stage folders are NN_<stage>")
            if not (st / "README.md").is_file():
                warn.append(f"analysis/{st.name}: no README.md (stage report with gate)")
    # file map
    fm = root / "data" / "file_map.csv"
    if fm.is_file():
        rows = list(csv.DictReader(open(fm)))
        hdr = open(fm).readline().strip().split(",")
        if hdr[:3] != ["source_path", "local_path", "sha256"]:
            err.append("data/file_map.csv: header must start with source_path,local_path,sha256")
        for r in rows:
            lp = r.get("local_path", "")
            if not lp:
                continue                                   # recorded but not copied (unreadable at the source)
            if re.search(r"\.(tar|tgz|tar\.gz|zip):", lp):  # member of a packed archive: the archive must exist
                if not (root / re.split(r"(?<=\.tar|\.tgz|\.zip):|(?<=\.tar\.gz):", lp)[0]).is_file():
                    err.append(f"file_map: archive of {lp} missing")
                continue
            p = root / lp
            if not p.is_file():
                err.append(f"file_map: {r.get('local_path')} listed but missing")
            elif a.verify and sha256(p) != r.get("sha256"):
                err.append(f"file_map: checksum mismatch {r.get('local_path')}")
    else:
        err.append("missing data/file_map.csv")
    man = root / "data" / "MANIFEST.sha256"
    if man.is_file() and a.verify:
        for line in open(man):
            if line.strip():
                h, f = line.split(None, 1)
                p = root / "data" / f.strip().lstrip("*")
                if not p.is_file() or sha256(p) != h:
                    err.append(f"MANIFEST: {f.strip()} missing or changed")
    elif not man.is_file() and any((root / "data" / "raw").glob("*")):
        warn.append("data/MANIFEST.sha256 missing while data/raw/ has content")
    # logbook
    lb = root / "data" / "logbook.csv"
    if lb.is_file():
        rd = csv.DictReader(open(lb))
        miss = [c for c in LOGBOOK_COLS if c not in (rd.fieldnames or [])]
        if miss:
            err.append(f"logbook.csv: missing columns {', '.join(miss)}")
        n_missing_file = 0
        for i, r in enumerate(rd, start=2):
            if "purpose" in r and r["purpose"] not in PURPOSES:
                err.append(f"logbook.csv line {i}: purpose {r['purpose']!r} not in {sorted(PURPOSES)}")
            if r.get("file") and not (root / r["file"]).is_file():
                n_missing_file += 1
        if n_missing_file:
            warn.append(f"logbook.csv: {n_missing_file} rows point to a missing ROOT file")
    elif any((root / "data" / "raw").glob("*")):
        warn.append("data/raw/ has content but data/logbook.csv is missing (tools/build_logbook.py)")
    # names
    for sub in ("analysis", "tools", "report", "slides", "data/root", "simulation"):
        for p in walk(root, sub):
            n = p.name
            if any(fnmatch.fnmatch(n.lower(), s) for s in STRAY):
                warn.append(f"stray file name: {p.relative_to(root)}")
            elif n != n.lower() and n not in UPPER_OK and sub != "data/root" and (
                    p.is_dir() or p.suffix.lower() in AUTHORED):
                # generated files may carry original run or target names (e.g. MrX), which keep their capitals
                warn.append(f"uppercase name: {p.relative_to(root)}")
            elif " " in n:
                warn.append(f"space in name: {p.relative_to(root)}")
    for e in err:
        print("ERROR  ", e)
    for w in warn:
        print("WARNING", w)
    print(f"{len(err)} errors, {len(warn)} warnings")
    return 1 if err or (a.strict and warn) else 0


if __name__ == "__main__":
    sys.exit(main())
