#!/usr/bin/env python3
"""Thermodynamic trajectories (thermo-trajectory contract: CSV time_s, T_K, rho_cgs).

  python3 trajectory.py check FILE
  python3 trajectory.py make exp --T0 3e8 --rho0 1e3 --tau 300 --t-end 3000 --out traj.csv
  python3 trajectory.py make adiabatic-exp --T0 2.5e9 --rho0 1e7 --tau 0.4 --t-end 5 --out traj.csv

'exp': T = T0 exp(-t/tau), rho = rho0 exp(-t/tau) (the parametrised explosive-burning profile,
e.g. nova or X-ray-burst one-zone studies). 'adiabatic-exp': rho = rho0 exp(-t/tau),
T = T0 (rho/rho0)^(1/3) (radiation-dominated adiabatic expansion). The parameters are the
user's: a parametrised trajectory is a model of a site, and its values need a source.
Trajectories from stellar models (MESA profiles or tracer particles) are converted to the same
CSV by the stellar-evolution skill.
"""

import argparse
import csv
import sys

import numpy as np


def check(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    errs = []
    if not rows:
        return ["no rows"]
    for c in ("time_s", "T_K", "rho_cgs"):
        if c not in rows[0]:
            errs.append(f"missing column {c}")
    if errs:
        return errs
    t = np.array([float(r["time_s"]) for r in rows])
    T = np.array([float(r["T_K"]) for r in rows])
    rho = np.array([float(r["rho_cgs"]) for r in rows])
    if np.any(np.diff(t) <= 0):
        errs.append("time_s not strictly increasing")
    if np.any(T <= 0) or np.any(rho <= 0):
        errs.append("T_K and rho_cgs must be > 0")
    if T.max() < 1e5:
        errs.append(f"max T = {T.max():g} K: temperatures look like T9 or log T, column is kelvin")
    if T.max() > 2e10:
        errs.append(f"max T = {T.max():g} K: above the range of REACLIB fits (T9 <= 10)")
    # resolution: T changes by more than 10 % between successive points
    jump = np.max(np.abs(np.diff(np.log(T)))) if len(T) > 1 else 0
    if jump > 0.1:
        errs.append(f"T changes by up to {np.expm1(jump) * 100:.0f} % between points: the network "
                    "interpolates log-linearly between them, resample if the peak is under-resolved")
    print(f"{len(t)} points, t {t[0]:.4g}-{t[-1]:.4g} s, T {T.min():.4g}-{T.max():.4g} K, "
          f"rho {rho.min():.4g}-{rho.max():.4g} g/cm3")
    return errs


def make(a):
    # log-spaced start, then linear steps of 0.02 tau: ln T changes by <= 2 % per step
    t = np.unique(np.concatenate([[0.0], np.geomspace(a.tau * 1e-4, 0.02 * a.tau, 20),
                                  np.arange(0.02 * a.tau, a.t_end, 0.02 * a.tau), [a.t_end]]))
    if a.kind == "exp":
        T = a.T0 * np.exp(-t / a.tau)
        rho = a.rho0 * np.exp(-t / a.tau)
    else:
        rho = a.rho0 * np.exp(-t / a.tau)
        T = a.T0 * (rho / a.rho0) ** (1 / 3)
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_s", "T_K", "rho_cgs"])
        for x in zip(t, T, rho):
            w.writerow([f"{v:.8e}" for v in x])
    print(f"wrote {a.out}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("file")
    m = sub.add_parser("make")
    m.add_argument("kind", choices=["exp", "adiabatic-exp"])
    m.add_argument("--T0", type=float, required=True)
    m.add_argument("--rho0", type=float, required=True)
    m.add_argument("--tau", type=float, required=True)
    m.add_argument("--t-end", type=float, required=True)
    m.add_argument("--n", type=int, default=400)
    m.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "check":
        errs = check(a.file)
        for e in errs:
            print(f"PROBLEM {e}")
        print("OK" if not errs else "NOT OK")
        return 1 if errs else 0
    return make(a)


if __name__ == "__main__":
    sys.exit(main())
