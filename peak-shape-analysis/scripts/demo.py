from pathlib import Path
import sys, json, numpy as np
import argparse

p = argparse.ArgumentParser(description="Generate and fit a synthetic asymmetric peak")
p.add_argument("--out", required=True, type=Path)
args = p.parse_args()
from fit_peak import intrinsic, response_matrix, deviance_residual, run

assert np.isclose(deviance_residual(np.array([0.0]), np.array([2.0]))[0], 2)
p = args.out
p.mkdir(parents=True, exist_ok=False)
low = np.arange(85, 115, 0.5)
high = low + 0.5
x = np.linspace(75, 125, 1001)
w = np.full(len(x), x[1] - x[0])
w[[0, -1]] *= 0.5
truth = {
    "area_counts": 8000.0,
    "edge_keV": 105.0,
    "loss_width_keV": 12.0,
    "low_edge_scale_keV": 1.2,
    "high_edge_scale_keV": 0.6,
    "background_left": 3.0,
    "background_right": 5.0,
}
density = intrinsic(x, truth, "target_edge")
signal = truth["area_counts"] * (
    response_matrix(low, high, x, 0.5) @ (density * w / np.sum(density * w))
)
mu = signal + np.interp((low + high) / 2, [low[0], high[-1]], [3, 5]) * (high - low)
np.savetxt(
    p / "spectrum.csv",
    np.c_[low, high, mu, mu],
    delimiter=",",
    header="low,high,counts,variance",
    comments="",
)
parameters = {k: {"value": v, "vary": False} for k, v in truth.items()}
parameters.update(
    area_counts={"value": 7000, "min": 3000, "max": 12000},
    edge_keV={"value": 104, "min": 102, "max": 108},
    loss_width_keV={"value": 10, "min": 6, "max": 18},
)
cfg = {
    "spectrum": {"spectrum_csv": "spectrum.csv"},
    "fit_window": [85, 115],
    "shape": "target_edge",
    "source_domain": [75, 125],
    "source_points": 1001,
    "response_sigma_keV": 0.5,
    "likelihood": "gaussian",
    "starts": 2,
    "parameters": parameters,
}
(p / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
r = run(p / "config.json", p / "result")
for k in ["area_counts", "edge_keV", "loss_width_keV"]:
    np.testing.assert_allclose(r["parameters"][k], truth[k], rtol=1e-5)
# Source quadrature normalization: near-full observed range captures almost all signal.
assert 0.99 < signal.sum() / 8000 <= 1
print(
    "PASS: target-edge recovery, bin-integrated response normalization and zero-count deviance"
)
