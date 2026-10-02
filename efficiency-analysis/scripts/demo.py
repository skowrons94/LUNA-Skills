from pathlib import Path
import sys, json, numpy as np
import argparse

p = argparse.ArgumentParser(
    description="Synthetic efficiency calibration and summing checks; no network required"
)
p.add_argument("--out", required=True, type=Path)
args = p.parse_args()
from cascade import enumerate_paths, peak_probability
from fit_efficiency import fit
from build_points import integrated_decays, build
from nds import decay_lines

s = {
    "populations": {"2": 1.0},
    "transitions": [
        {"from": "2", "to": "1", "energy_keV": 1000.0, "probability": 1.0},
        {"from": "1", "to": "0", "energy_keV": 500.0, "probability": 1.0},
    ],
}
paths = enumerate_paths(s)
ep = lambda e: 0.1
et = lambda e: 0.2
assert np.isclose(peak_probability(paths, 1000, 1, ep, et), 0.08)
assert np.isclose(peak_probability(paths, 1500, 1, ep, et), 0.01)
assert np.isclose(sum(p for p, e in paths), 1)
s["transitions"][0]["gamma_probability"] = 0.5
assert np.isclose(sum(p for p, e in enumerate_paths(s)), 1)
try:
    enumerate_paths(
        {
            "populations": {"1": 1},
            "transitions": [
                {"from": "1", "to": "1", "energy_keV": 1, "probability": 1}
            ],
        }
    )
except ValueError:
    pass
else:
    raise AssertionError("Cycle must be rejected")
assert np.isclose(integrated_decays(1000, 0, 10, 1e20), 10000)
p = args.out
p.mkdir(parents=True, exist_ok=False)
E = np.geomspace(100, 3000, 15)
truth = np.array([-4.0, -0.6, -0.08])
y = np.exp(np.vander(np.log(E / 1000), 3, increasing=True) @ truth)
np.savetxt(
    p / "points.csv",
    np.c_[E, y, 0.02 * y],
    delimiter=",",
    header="energy_keV,efficiency,error",
    comments="",
)
cfg = {"points_csv": "points.csv", "geometry": "Synthetic fixed geometry", "degree": 2}
(p / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
r = fit(p / "config.json", p / "result")
np.testing.assert_allclose(r["coefficients"], truth, atol=1e-10)
D = 1e6
I = 0.8
live = 0.9
n = D * I * live * y
np.savetxt(
    p / "areas.csv",
    np.c_[
        E, n, np.sqrt(n), np.full(len(E), D), np.full(len(E), I), np.full(len(E), live)
    ],
    delimiter=",",
    header="energy_keV,net_counts,net_error,decays,emission_probability,live_fraction",
    comments="",
)
a, err = build(p / "areas.csv", p / "points-built")
np.testing.assert_allclose(a, y)
print(
    "PASS: analytic sum-in/out, conversion path normalization, cycle rejection, decay exposure, efficiency coefficient recovery and area normalization"
)
