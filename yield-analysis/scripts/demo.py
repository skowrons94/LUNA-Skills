import sys, json
from pathlib import Path
import numpy as np
import argparse

p = argparse.ArgumentParser(description="Generate and analyze a synthetic ROI example")
p.add_argument("--out", required=True, type=Path)
args = p.parse_args()
from analyze_yield import integrate_roi, run

low = np.arange(100.0)
high = low + 1
n = np.full(100, 4.0)
n[50] += 100
r = integrate_roi(low, high, n, n, [40, 60], [20, 30], [70, 80])
assert r["net_counts"] == 100 and r["net_variance"] == 260, r
s = integrate_roi(
    low, high, n, n, [40, 60], [20, 30], [70, 80], background="step", step_energy=50
)
assert s["net_counts"] == 100 and s["net_variance"] == 260
try:
    integrate_roi(low, high, n, n, [40.5, 60], [20, 30], [70, 80])
except ValueError:
    pass
else:
    raise AssertionError("Must reject partial bins")
p = args.out
p.mkdir(parents=True, exist_ok=False)
np.savetxt(
    p / "spectrum.csv",
    np.c_[low, high, n],
    delimiter=",",
    header="low,high,counts",
    comments="",
)
cfg = {
    "shared_systematics": {"charge_calibration": 0.02},
    "runs": [
        {
            "run_id": "demo-1",
            "energy_lab_keV": 250,
            "spectrum_csv": "spectrum.csv",
            "roi": [40, 60],
            "left_sideband": [20, 30],
            "right_sideband": [70, 80],
            "charge_C": 1e-6,
            "live_fraction": 0.9,
            "efficiency": 0.1,
        }
    ],
}
(p / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
res = run(p / "config.json", p / "result")
expected = 100 / (1e-6 / 1.602176634e-19 * 0.9 * 0.1)
assert np.isclose(res[0]["yield_per_ion"], expected)
print(
    "PASS: exact background, finite-sideband variance, partial-bin rejection, normalization and report"
)
