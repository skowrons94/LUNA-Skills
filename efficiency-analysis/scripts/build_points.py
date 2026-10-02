#!/usr/bin/env python3
"""Build full-energy efficiency points from measured net areas and known emitted decays.

CSV: energy_keV,net_counts,net_error,decays,emission_probability,live_fraction.
Optional summing_factor multiplies observed efficiency; default 1. All net_error
values are absolute count uncertainties, including background subtraction.
"""

import argparse, json
from pathlib import Path
import numpy as np
from analysis_utils import read_csv, save_report


def integrated_decays(activity_Bq, elapsed_s, real_time_s, half_life_s):
    """Activity at reference time, then delay and real counting duration in seconds."""
    if (
        not np.isfinite([activity_Bq, elapsed_s, real_time_s, half_life_s]).all()
        or min(activity_Bq, elapsed_s, real_time_s) < 0
        or half_life_s <= 0
    ):
        raise ValueError("Invalid decay exposure")
    lam = np.log(2) / half_life_s
    return float(
        activity_Bq * np.exp(-lam * elapsed_s) * (-np.expm1(-lam * real_time_s)) / lam
    )


def build(csv_path, out):
    d = read_csv(
        csv_path,
        [
            "energy_keV",
            "net_counts",
            "net_error",
            "decays",
            "emission_probability",
            "live_fraction",
        ],
    )
    if (
        (d["energy_keV"] <= 0).any()
        or (d["decays"] <= 0).any()
        or (d["net_error"] <= 0).any()
        or any(
            ((d[k] <= 0) | (d[k] > 1)).any()
            for k in ["emission_probability", "live_fraction"]
        )
    ):
        raise ValueError("Invalid exposure/probability/error")
    factor = (
        d["summing_factor"] if "summing_factor" in d.dtype.names else np.ones(len(d))
    )
    if not np.isfinite(factor).all() or (factor <= 0).any():
        raise ValueError("Invalid summing correction factor")
    norm = d["decays"] * d["emission_probability"] * d["live_fraction"]
    eff = d["net_counts"] / norm * factor
    err = d["net_error"] / norm * factor
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    np.savetxt(
        out / "points.csv",
        np.c_[d["energy_keV"], eff, err],
        delimiter=",",
        header="energy_keV,efficiency,error",
        comments="",
    )
    save_report(
        out,
        "Efficiency calibration points",
        {
            "points": len(d),
            "uncertainty_scope": "Net-area statistical errors only. Supply correlated activity, emission-probability, timing and summing covariance to the curve fit separately.",
            "nonpositive_points": int(np.sum(eff <= 0)),
        },
        [csv_path],
    )
    print(f'Wrote {out / "points.csv"}')
    return eff, err


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv", type=Path)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    build(a.csv, a.out)
