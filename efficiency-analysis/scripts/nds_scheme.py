#!/usr/bin/env python3
"""Convert reachable NDS adopted gamma levels into an explicitly conditional EM scheme.

Requires the caller's assessed completeness assumption. Missing conversion data
are errors unless explicitly treated as zero; every such assumption is recorded.
Radioactive parent feeding is NOT inferred from adopted gamma transitions.
"""

import argparse, csv, json, hashlib
from pathlib import Path
from cascade import enumerate_paths


def build(path, start_idx, complete_em=False, missing_icc="error"):
    if not complete_em:
        raise ValueError(
            "Assess electromagnetic branch completeness before constructing probabilities"
        )
    with Path(path).open() as f:
        rows = list(csv.DictReader(f))
    group = {}
    for i, r in enumerate(rows):
        group.setdefault(r["start_level_idx"], []).append((i, r))
    done = set()
    todo = [str(start_idx)]
    edges = []
    assumptions = []
    while todo:
        level = todo.pop()
        if level in done or level == "0":
            continue
        done.add(level)
        if level not in group:
            raise ValueError(
                f"No outgoing transitions for non-ground level {level}; isomer/incomplete scheme"
            )
        outgoing = []
        for i, r in group[level]:
            try:
                energy = float(r["energy"])
                intensity = float(r["relative_intensity"])
            except ValueError as e:
                raise ValueError(
                    f"Missing/qualified transition value at CSV row {i+2}"
                ) from e
            value = r["tot_conv_coeff"].strip()
            if not value and missing_icc == "zero":
                alpha = 0.0
                assumptions.append(f"Row {i+2}: missing ICC treated as zero")
            else:
                try:
                    alpha = float(value)
                except ValueError as e:
                    raise ValueError(f"Missing/qualified ICC at row {i+2}") from e
            if intensity < 0 or alpha < 0:
                raise ValueError("Negative intensity or ICC")
            outgoing.append(
                {
                    "from": level,
                    "to": r["end_level_idx"],
                    "energy_keV": energy,
                    "weight": intensity * (1 + alpha),
                    "gamma_probability": 1 / (1 + alpha),
                    "nds_row": i + 2,
                }
            )
        norm = sum(t["weight"] for t in outgoing)
        if norm <= 0:
            raise ValueError("Zero outgoing branch normalization")
        for t in outgoing:
            t["probability"] = t.pop("weight") / norm
            edges.append(t)
            if t["probability"] > 0:
                todo.append(t["to"])
    scheme = {
        "populations": {str(start_idx): 1.0},
        "terminal_levels": ["0"],
        "transitions": edges,
        "provenance": {
            "input_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "input": str(Path(path).resolve()),
            "assumptions": [
                "All outgoing electromagnetic branches represented; no competing particle decay",
                "Conditioned on population of specified daughter level; parent feeding not included",
                "Conversion electrons and atomic X-rays treated as undetected",
            ]
            + assumptions,
        },
    }
    enumerate_paths(scheme)
    return scheme


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv", type=Path)
    p.add_argument("--start-level-idx", required=True)
    p.add_argument("--assume-complete-em", action="store_true")
    p.add_argument("--missing-icc", choices=["error", "zero"], default="error")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    s = build(a.csv, a.start_level_idx, a.assume_complete_em, a.missing_icc)
    with a.out.open("x") as f:
        json.dump(s, f, indent=2)
        f.write("\n")
    print(f'Wrote {len(s["transitions"])} transitions; review recorded assumptions')
