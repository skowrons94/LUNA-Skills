import sys, json
from pathlib import Path
import numpy as np
import argparse

p = argparse.ArgumentParser(
    description="Create and fit a synthetic target curve; no experimental inference"
)
p.add_argument("--out", required=True, type=Path)
args = p.parse_args()
from target_model import response

p = args.out
p.mkdir(parents=True, exist_ok=False)
e = np.linspace(150, 400, 10001)
xs = np.c_[e, 1e-27 * np.exp(-0.5 * ((e - 260) / 0.8) ** 2)]
stop = np.array([[1, 4e-18], [1000, 4e-18]])
x = np.linspace(258, 285, 35)
model = {
    "max_loss_keV": 28,
    "beam_sigma_keV": 0.4,
    "straggling_keV_per_sqrt_keV": 0.15,
    "depth_points": 201,
    "kernel_points": 51,
}
y = response(x, xs, stop, mean_keV=7, sigma_keV=3, amplitude=1.4, **model)
np.savetxt(
    p / "data.csv",
    np.c_[x, y, np.full(len(x), 1e-11)],
    delimiter=",",
    header="energy_lab_keV,yield,error",
    comments="",
)
np.savetxt(
    p / "cross.csv",
    xs,
    delimiter=",",
    header="energy_lab_keV,cross_section_cm2",
    comments="",
)
np.savetxt(
    p / "stop.csv",
    stop,
    delimiter=",",
    header="energy_lab_keV,stopping_keV_cm2_per_active_atom",
    comments="",
)
cfg = {
    "data_csv": "data.csv",
    "cross_section_csv": "cross.csv",
    "effective_stopping_csv": "stop.csv",
    "model": model,
    "starts": 2,
    "parameters": {
        "mean_keV": {"value": 6, "min": 1, "max": 15},
        "sigma_keV": {"value": 4, "min": 1, "max": 8},
        "amplitude": {"value": 1, "min": 0.1, "max": 3},
    },
}
(p / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")

from fit_target import run

result = run(p / "config.json", p / "result")
for name, truth in {"mean_keV": 7.0, "sigma_keV": 3.0, "amplitude": 1.4}.items():
    np.testing.assert_allclose(result["parameters"][name], truth, rtol=1e-5)
print("PASS: target mean, width and amplitude recovery")
