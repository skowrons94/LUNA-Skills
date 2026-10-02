#!/usr/bin/env python3
"""Offline identifiable joint-efficiency example: singles and a two-photon sum peak."""

import argparse
import csv
import json
from pathlib import Path
import numpy as np
from scipy.special import logit
from cascade import enumerate_paths, peak_probability
from fit_cascade_efficiency import efficiencies, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=False)
    scheme = {
        "populations": {"2": 1.0},
        "transitions": [
            {"from": "2", "to": "1", "energy_keV": 1000, "probability": 1.0},
            {"from": "1", "to": "0", "energy_keV": 500, "probability": 1.0},
        ],
    }
    (out / "scheme.json").write_text(json.dumps(scheme, indent=2))
    truth = {"t0": float(logit(0.2)), "f0": 0.0, "d0_cm": 1.0}
    paths = enumerate_paths(scheme)
    with (out / "observations.csv").open("w") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["source", "energy_keV", "distance_cm", "exposure", "observed", "error"]
        )
        for distance in [1.35, 3.0, 5.0]:
            ep = lambda e: efficiencies(e, distance, truth, 1.35)[0]
            et = lambda e: efficiencies(e, distance, truth, 1.35)[1]
            for energy in [500, 1000, 1500]:
                expected = 1e6 * peak_probability(paths, energy, 0.5, ep, et)
                writer.writerow(
                    ["demo", energy, distance, 1e6, expected, np.sqrt(expected)]
                )
    config = {
        "data_csv": "observations.csv",
        "reference_distance_cm": 1.35,
        "energy_tolerance_keV": 0.5,
        "sources": {"demo": {"scheme_json": "scheme.json"}},
        "parameters": {
            "t0": {"value": -1, "min": -4, "max": 0},
            "f0": {"value": 0.3, "min": -2, "max": 2},
            "d0_cm": {"value": 1.0, "vary": False},
        },
    }
    (out / "config.json").write_text(json.dumps(config, indent=2))
    result = run(out / "config.json", out / "result")
    for name in ["t0", "f0"]:
        np.testing.assert_allclose(result["parameters"][name], truth[name], atol=1e-7)
    print(
        "PASS: joint peak/total efficiency recovery from singles and sum peaks at three distances"
    )


if __name__ == "__main__":
    main()
