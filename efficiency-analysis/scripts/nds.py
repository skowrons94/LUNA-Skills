#!/usr/bin/env python3
"""Direct IAEA LiveChart CSV client; no nudel dependency, no implicit nuclear-data updates.

fetch preserves the raw CSV, URL, UTC retrieval time and SHA-256. lines selects
parent excitation/decay mode explicitly. Neither operation invents missing values.
"""

import argparse, csv, hashlib, io, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://www-nds.iaea.org/relnsd/v1/data"


def fetch(nuclide, fields, out, timeout=30):
    if not re.fullmatch(r"[1-9][0-9]*[a-z]{1,3}", nuclide):
        raise ValueError("Use mass+lowercase element, e.g. 60co")
    if fields not in ("gammas", "levels", "ground_states", "decay_rads"):
        raise ValueError("Unsupported field group")
    query = {"fields": fields, "nuclides": nuclide}
    if fields == "decay_rads":
        query["rad_types"] = "g"
    url = BASE + "?" + urlencode(query)
    with urlopen(
        Request(url, headers={"User-Agent": "Livechart/1.0"}), timeout=timeout
    ) as response:
        raw = response.read()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    required = (
        {"energy", "intensity", "p_energy", "decay"}
        if fields == "decay_rads"
        else {"energy"} if fields == "gammas" else {"z", "n"}
    )
    if not rows or not reader.fieldnames or not required <= set(reader.fieldnames):
        raise ValueError("NDS returned no usable CSV or an API error: " + text[:180])
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "data.csv").write_bytes(raw)
    meta = {
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "nuclide": nuclide,
        "fields": fields,
        "rows": len(rows),
        "fieldnames": reader.fieldnames,
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))
    return meta


def decay_lines(path, parent_energy, decay):
    """Return full raw rows for a parent state and decay mode, retaining qualifiers/uncertainties."""
    selected = []
    with Path(path).open() as f:
        for row in csv.DictReader(f):
            if row.get("p_energy_shift", "").strip():
                continue
            try:
                energy = float(row["p_energy"])
            except (ValueError, KeyError):
                continue
            if (
                abs(energy - parent_energy) <= 1e-6
                and row.get("decay", "").strip() == decay
            ):
                selected.append(row)
    if not selected:
        raise ValueError("No matching parent excitation and decay mode")
    return selected


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("nuclide")
    f.add_argument(
        "--fields",
        choices=["gammas", "levels", "ground_states", "decay_rads"],
        required=True,
    )
    f.add_argument("--out", type=Path, required=True)
    l = sub.add_parser("lines")
    l.add_argument("csv", type=Path)
    l.add_argument("--parent-energy-keV", type=float, required=True)
    l.add_argument("--decay", required=True)
    l.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.command == "fetch":
        fetch(a.nuclide, a.fields, a.out)
    else:
        rows = decay_lines(a.csv, a.parent_energy_keV, a.decay)
        with a.out.open("x") as f:
            json.dump(rows, f, indent=2)
            f.write("\n")
        print(f"Wrote {len(rows)} selected rows with original NDS fields")


if __name__ == "__main__":
    main()
