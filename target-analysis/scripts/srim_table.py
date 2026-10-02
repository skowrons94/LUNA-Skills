#!/usr/bin/env python3
"""Parse SRIM stopping tables with explicit units; export lab-keV, keV cm2/atom CSV."""

import argparse
from pathlib import Path
import re
import numpy as np


def read_srim(path, component="total"):
    if component not in ("electronic", "nuclear", "total"):
        raise ValueError("component must be electronic, nuclear or total")
    text = Path(path).read_text()
    if not re.search(r"Stopping Units\s*=\s*eV\s*/\s*\(1E15 atoms/cm2\)", text, re.I):
        raise ValueError("Unsupported stopping units; expected eV / (1E15 atoms/cm2)")
    try:
        body = text.split("Straggling   Straggling", 1)[1].split(
            "Multiply Stopping by", 1
        )[0]
    except IndexError as exc:
        raise ValueError("SRIM table header missing") from exc
    rows = []
    factors = {"eV": 0.001, "keV": 1.0, "MeV": 1000.0, "GeV": 1e6}
    for line in body.splitlines():
        fields = line.replace(",", ".").split()
        if len(fields) < 4 or not re.match(r"^\d", fields[0]):
            continue
        if fields[1] not in factors:
            raise ValueError("Unsupported energy unit: " + fields[1])
        e = float(fields[0]) * factors[fields[1]]
        electronic, nuclear = map(float, fields[2:4])
        rows.append((e, electronic, nuclear))
    a = np.array(rows, dtype=float)
    if (
        a.ndim != 2
        or len(a) < 2
        or not np.isfinite(a).all()
        or (a < 0).any()
        or (np.diff(a[:, 0]) <= 0).any()
    ):
        raise ValueError("Invalid or non-increasing SRIM table")
    stop = {"electronic": a[:, 1], "nuclear": a[:, 2], "total": a[:, 1] + a[:, 2]}[
        component
    ] * 1e-18
    return np.column_stack((a[:, 0], stop))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument(
        "--component", required=True, choices=["electronic", "nuclear", "total"]
    )
    a = p.parse_args()
    data = read_srim(a.input, a.component)
    with a.output.open("x") as f:
        np.savetxt(
            f,
            data,
            delimiter=",",
            header="energy_lab_keV,stopping_keV_cm2_per_atom",
            comments="",
        )
    print(
        f"Wrote {len(data)} rows; {data[0,0]:g}–{data[-1,0]:g} keV; {a.component} stopping"
    )


if __name__ == "__main__":
    main()
