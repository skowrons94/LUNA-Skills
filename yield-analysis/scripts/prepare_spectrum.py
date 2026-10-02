#!/usr/bin/env python3
"""List ROOT objects, export a TH1 to portable CSV, or suggest reviewable peak windows."""

import argparse, json
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
from spectrum_io import load_spectrum


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("list-root")
    a.add_argument("file", type=Path)
    a = sub.add_parser("export")
    a.add_argument("file", type=Path)
    a.add_argument("histogram")
    a.add_argument("--offset", type=float, default=0)
    a.add_argument("--slope", type=float, default=1)
    a.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("suggest")
    a.add_argument("csv", type=Path)
    a.add_argument("--prominence", type=float, required=True)
    a.add_argument("--distance-bins", type=int, default=10)
    a.add_argument("--half-width-bins", type=int, default=10)
    a.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.command == "list-root":
        import uproot

        with uproot.open(a.file) as f:
            print("\n".join(f.keys(recursive=True)))
    elif a.command == "export":
        lo, hi, n, var, _ = load_spectrum(
            {
                "root_file": str(a.file.resolve()),
                "histogram": a.histogram,
                "calibration": {"offset": a.offset, "slope": a.slope},
            },
            Path.cwd(),
        )
        with a.out.open("x") as f:
            np.savetxt(
                f,
                np.c_[lo, hi, n, var],
                delimiter=",",
                header="low,high,counts,variance",
                comments="",
            )
        print(f"Exported {len(n)} bins; verify energy calibration before analysis")
    else:
        if min(a.prominence, a.distance_bins, a.half_width_bins) <= 0:
            raise ValueError("Positive prominence and bin widths required")
        lo, hi, n, var, _ = load_spectrum(
            {"spectrum_csv": str(a.csv.resolve())}, Path.cwd()
        )
        peaks, props = find_peaks(n, prominence=a.prominence, distance=a.distance_bins)
        suggestions = []
        for idx, k in enumerate(peaks):
            left = max(0, k - a.half_width_bins)
            right = min(len(n) - 1, k + a.half_width_bins)
            suggestions.append(
                {
                    "peak_energy": float((lo[k] + hi[k]) / 2),
                    "prominence": float(props["prominences"][idx]),
                    "roi": [float(lo[left]), float(hi[right])],
                }
            )
        with a.out.open("x") as f:
            json.dump(
                {
                    "status": "Suggestions only: review overlaps, continuum and sidebands",
                    "peaks": suggestions,
                },
                f,
                indent=2,
            )
            f.write("\n")
        print(f"Wrote {len(suggestions)} candidate windows")


if __name__ == "__main__":
    main()
