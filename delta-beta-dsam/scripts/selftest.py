#!/usr/bin/env python3
"""Self-test of dbeta.py on a synthetic DSAM sample (no Geant4 needed).

A recoil with beta0 is decelerated at a constant rate d(beta)/dt inside the backing; the state
decays after an exponential time; gamma rays are detected at backward angles with energy and angle
resolution. Checks: Doppler inversion, no-stopping reference unbiased, Delta-beta_true grows
linearly with tau, dE recovered when an energy offset is injected.
Run: python3 selftest.py   -> prints PASS/FAIL lines, exit code 1 on failure.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import dbeta as D  # noqa: E402

rng = np.random.default_rng(1)
ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


# 1. Doppler inversion round trip
c = np.linspace(-0.99, 0.99, 50)
b = D.beta_ems(D.doppler_energy(3204.3, 0.095, c), 3204.3, c, 0.095)
check("Doppler inversion", np.allclose(b, 0.095, atol=1e-9))


def sample(tau_fs, n=40000, beta0=0.095, rate=1.2e-4, e0=3204.3, dE=0.0, cos_range=(-1, -0.3)):
    t = rng.exponential(tau_fs, n) if tau_fs > 0 else np.zeros(n)
    beta_e = np.maximum(beta0 - rate * t, 0)
    cos = rng.uniform(*cos_range, n)
    e = D.doppler_energy(e0, beta_e, cos) + rng.normal(0, 1.5, n)
    cos_m = np.cos(np.arccos(cos) + np.radians(rng.normal(0, 1.0, n)))
    breac = beta0 + rng.normal(0, 0.0005, n)
    db = breac - D.beta_ems(e, e0 + dE, cos_m, breac)
    return np.degrees(np.arccos(cos_m)), db, beta0


res = {}
for tau in (0, 2, 5, 10, 20):
    th, db, b0 = sample(tau)
    w = D.dbeta_windows(th, db, n_boot=20)
    res[tau] = D.fit_dbeta_theta(w, 3204.3, b0)
check("no stopping unbiased", abs(res[0]["dbeta"]) < 3 * res[0]["dbeta_err"] + 2e-5,
      f"dbeta={res[0]['dbeta']:.2e}+-{res[0]['dbeta_err']:.1e}")
taus = np.array([2, 5, 10, 20.0])
a, ae, b0_, be = D.calibrate(taus, [res[t]["dbeta"] for t in taus], [res[t]["dbeta_err"] for t in taus])
resid = np.array([res[t]["dbeta"] - (a * t + b0_) for t in taus]) / np.array([res[t]["dbeta_err"] for t in taus])
vals = [res[t]["dbeta"] for t in (0, 2, 5, 10, 20)]
check("monotonic in tau and linear for tau >= 2 fs (free intercept, as in the calibration fit)",
      np.all(np.diff(vals) > 0) and np.all(np.abs(resid) < 3.5),
      f"centroids(1e-4) {np.round(np.array(vals) * 1e4, 2)}; slope={a:.2e}, intercept={b0_:.1e}+-{be:.1e}")
check("centroid slope below d(beta)/dt (Gaussian-core centroid of an exponential tail)", 0.4 < a / 1.2e-4 < 1.0,
      f"ratio={a / 1.2e-4:.2f}: calibrate the slope with simulation or known lifetimes")
th, db, b0 = sample(5, dE=1.0)
f = D.fit_dbeta_theta(D.dbeta_windows(th, db, n_boot=20), 3204.3, b0)
check("energy offset recovered", abs(f["dE"] - 1.0) < 3 * f["dE_err"] + 0.2, f"dE={f['dE']:.2f}+-{f['dE_err']:.2f} keV (injected: inversion with E0+1)")
sys.exit(0 if ok else 1)
