"""Fit one configuration: python3 run_fit.py <name> '<json cfg>' '<json opts>' [n_starts]"""
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
import numpy as np

import make_azr
import fitter

name = sys.argv[1]
cfg = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
opts = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
nst = int(sys.argv[4]) if len(sys.argv) > 4 else 12
d = f"runs/{name}"
make_azr.write_project(cfg, d)
t = time.time()
if cfg.get("model") == "poly":
    f = fitter.PolyFit(d, opts, degree=cfg.get("degree", 5))
else:
    f = fitter.DDFit(d, opts)
start = None
for cand in (f"{d}/best.npy", os.environ.get("DD_START", "")):
    if cand and os.path.exists(cand):
        z = np.load(cand)
        if len(z) >= len(f.x0) and len(z) - len(f.x0) >= 0:
            try:
                start = z[:len(f.x0)]
                f.residuals(np.concatenate([start, np.ones(f.nn)]))
                break
            except Exception:
                start = None
b = f.fit(n_starts=nst, x_start=start, verbose=True, max_nfev=int(os.environ.get("DD_NFEV", 3000)))
s = f.summary(b["z"])
grid = np.concatenate([np.arange(0.5, 60, 0.25), np.arange(60, 2000, 5.0)])
cur = f.curves(b["z"][:len(f.x0)], grid)
np.save(f"{d}/best.npy", b["z"])
# covariance of all fitted parameters from the Jacobian at the minimum
J = b["jac"]
cov = np.linalg.pinv(J.T @ J)
np.save(f"{d}/cov.npy", cov)
json.dump({"cfg": cfg, "opts": opts, "summary": s, "time": time.time() - t,
           "grid": grid.tolist(), "dp": cur["dp"].tolist(), "dn": cur["dn"].tolist()},
          open(f"{d}/result.json", "w"))
print(f"{name}: chi2 data {s['chi2_data']:.1f} prior {s['chi2_prior']:.1f} / {s['npts']} pts, "
      f"{s['npar']} par, {time.time() - t:.0f} s")
print(" norms", {k: round(v, 4) for k, v in s["norms"].items()})
print(" per-exp chi2/N", {k: f"{a:.1f}/{n}" for k, (a, n) in s["per_exp"].items()})
f.close()
