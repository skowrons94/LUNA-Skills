#!/usr/bin/env python3
"""Validate the files passed between analysis stages against their contracts.

  python3 contracts.py list
  python3 contracts.py check yield-table results/yields/yields.csv
  python3 contracts.py check efficiency-curve results/efficiency/result.json
  python3 contracts.py check azure-dat r-matrix/data/sfactor_lab.dat

A contract fixes the columns or keys, units, frame and value ranges of one handoff. The consumer
runs the check before reading the file; a failure stops the chain at the boundary instead of
three stages later. Standard library only. Exit code 1 on any violation.
"""

import csv
import json
import math
import sys
from pathlib import Path

CONTRACTS = {
    "spectrum-csv": {
        "doc": "Raw gamma spectrum: contiguous increasing bins in keV, raw (not live-time corrected) counts",
        "type": "csv",
        "columns": {"low": "keV", "high": "keV", "counts": "counts"},
        "optional": {"variance": "counts^2"},
        "rules": ["contiguous_bins", "nonneg:counts"],
    },
    "yield-table": {
        "doc": "yield-analysis output: one row per analysis_id, photon yield per incident ion",
        "type": "csv",
        "columns": {"analysis_id": "", "run_id": "", "energy_lab_keV": "keV", "net_counts": "counts",
                    "stat_error_counts": "counts", "yield_per_ion": "1/ion", "stat_error": "1/ion",
                    "independent_normalization_error": "1/ion"},
        "rules": ["unique:analysis_id", "positive:energy_lab_keV", "positive:stat_error",
                  "nonneg:independent_normalization_error"],
        "companions": ["covariance.csv", "result.json"],
    },
    "excitation-curve": {
        "doc": "target-analysis input: yield vs lab energy, one error column (state what it contains)",
        "type": "csv",
        "columns": {"energy_lab_keV": "keV", "yield": "1/ion", "error": "1/ion"},
        "rules": ["positive:energy_lab_keV", "positive:error", "increasing:energy_lab_keV"],
    },
    "efficiency-curve": {
        "doc": "efficiency-analysis fit: ln(eff) = sum c_i [ln(E/E_ref)]^i with covariance and validity range",
        "type": "json",
        "keys": ["coefficients", "coefficient_definition", "reference_energy_keV", "covariance",
                 "valid_energy_keV", "quantity", "geometry"],
        "rules": ["covariance_shape", "quantity_full_energy_peak"],
    },
    "rate-table": {
        "doc": "reaction-network input: N_A<sigma v> (cm^3/mol/s, or 1/s for decays) on a T9 grid, "
               "bare (unscreened), no 1/(1+delta) factor; optional lognormal factor uncertainty fu",
        "type": "csv",
        "columns": {"T9": "GK", "rate": "cm^3/mol/s"},
        "optional": {"fu": "factor"},
        "rules": ["positive:T9", "increasing:T9", "nonneg:rate", "min:fu:1"],
    },
    "thermo-trajectory": {
        "doc": "reaction-network conditions: time (s), temperature (K), density (g/cm^3)",
        "type": "csv",
        "columns": {"time_s": "s", "T_K": "K", "rho_cgs": "g/cm^3"},
        "rules": ["increasing:time_s", "positive:T_K", "positive:rho_cgs", "peak:T_K:1e5"],
    },
    "azure-dat": {
        "doc": "AZURE2 data segment: E_lab (MeV), angle (deg), cross section (b or b/sr), uncertainty; "
               "lab frame, forward kinematics; whitespace separated, no header",
        "type": "dat",
        "ncols": 4,
        "rules": ["positive_col:0", "range_col:1:0:180", "positive_col:3", "mev_scale:0"],
    },
}


def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def check_csv(spec, path):
    errs = []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return ["no data rows"]
    have = set(rows[0].keys())
    missing = [c for c in spec["columns"] if c not in have]
    if missing:
        errs.append(f"missing columns {missing} (have {sorted(have)})")
        return errs
    numeric = [c for c, u in {**spec["columns"], **spec.get("optional", {})}.items() if u and c in have]
    for i, r in enumerate(rows, start=2):
        for c in numeric:
            if fnum(r[c]) is None:
                errs.append(f"line {i}: {c}={r[c]!r} is not a finite number")
    if errs:
        return errs[:20]
    col = lambda c: [float(r[c]) for r in rows]
    for rule in spec.get("rules", []):
        name, _, arg = rule.partition(":")
        if name == "min":  # min:column:limit, skipped when an optional column is absent
            c, _, lim = arg.partition(":")
            if c in have and min(col(c)) < float(lim):
                errs.append(f"{c} has values below {lim}")
            continue
        if name == "peak":  # peak:column:limit, the maximum must reach it (catches T9 for K)
            c, _, lim = arg.partition(":")
            if max(col(c)) < float(lim):
                errs.append(f"max {c} = {max(col(c)):g} is below {lim}: wrong unit?")
            continue
        if name == "nonneg" and min(col(arg)) < 0:
            errs.append(f"{arg} has negative values")
        elif name == "positive" and min(col(arg)) <= 0:
            errs.append(f"{arg} must be > 0")
        elif name == "unique":
            vals = [r[arg] for r in rows]
            if len(set(vals)) != len(vals):
                errs.append(f"{arg} not unique")
        elif name == "increasing":
            v = col(arg)
            if any(b <= a for a, b in zip(v, v[1:])):
                errs.append(f"{arg} not strictly increasing")
        elif name == "contiguous_bins":
            lo, hi = col("low"), col("high")
            if any(h <= l for l, h in zip(lo, hi)) or any(abs(h - l2) > 1e-9 * max(1, abs(h))
                                                          for h, l2 in zip(hi, lo[1:])):
                errs.append("bins not contiguous and increasing")
    for comp in spec.get("companions", []):
        if not (Path(path).parent / comp).exists():
            errs.append(f"companion file {comp} missing next to {Path(path).name} "
                        "(shared systematics and covariance travel with the table)")
    return errs


def check_json(spec, path):
    try:
        d = json.loads(Path(path).read_text())
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]
    errs = [f"missing key {k}" for k in spec["keys"] if k not in d]
    if errs:
        return errs
    for rule in spec.get("rules", []):
        if rule == "covariance_shape":
            n = len(d["coefficients"])
            cov = d["covariance"]
            if len(cov) != n or any(len(r) != n for r in cov):
                errs.append(f"covariance is not {n}x{n}")
            elif any(cov[i][i] < 0 for i in range(n)):
                errs.append("negative variance on the covariance diagonal")
        elif rule == "quantity_full_energy_peak" and d["quantity"] != "full_energy_peak":
            errs.append(f"quantity is {d['quantity']!r}; yields need the full-energy-peak efficiency")
    lo, hi = d["valid_energy_keV"]
    if not 0 < lo < hi:
        errs.append("valid_energy_keV must be [low, high] with 0 < low < high")
    return errs


def check_dat(spec, path):
    errs, rows = [], []
    for i, line in enumerate(Path(path).read_text().splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        vals = [fnum(p) for p in parts]
        if len(parts) != spec["ncols"] or None in vals:
            errs.append(f"line {i}: expected {spec['ncols']} numeric columns, got {line.strip()!r}")
            continue
        rows.append(vals)
    if errs:
        return errs[:20]
    if not rows:
        return ["no data rows"]
    for rule in spec.get("rules", []):
        parts = rule.split(":")
        c = int(parts[1])
        v = [r[c] for r in rows]
        if parts[0] == "positive_col" and min(v) <= 0:
            errs.append(f"column {c + 1} must be > 0")
        elif parts[0] == "range_col" and not all(float(parts[2]) <= x <= float(parts[3]) for x in v):
            errs.append(f"column {c + 1} outside [{parts[2]}, {parts[3]}]")
        elif parts[0] == "mev_scale" and max(v) > 50:
            errs.append(f"column {c + 1} reaches {max(v):g}: energies look like keV, AZURE2 reads MeV")
    return errs


def check(name, path):
    spec = CONTRACTS[name]
    return {"csv": check_csv, "json": check_json, "dat": check_dat}[spec["type"]](spec, path)


def main(argv):
    if len(argv) >= 1 and argv[0] == "list":
        for k, s in CONTRACTS.items():
            cols = s.get("columns") or s.get("keys") or f"{s.get('ncols')} columns"
            print(f"{k:18s} {s['doc']}\n{'':18s} {cols}")
        return 0
    if len(argv) != 3 or argv[0] != "check" or argv[1] not in CONTRACTS:
        print(__doc__)
        return 2
    errs = check(argv[1], argv[2])
    for e in errs:
        print(f"VIOLATION  {argv[1]}  {argv[2]}: {e}")
    if not errs:
        print(f"OK  {argv[1]}  {argv[2]}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
