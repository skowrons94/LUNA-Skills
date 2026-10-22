#!/usr/bin/env python3
"""One-zone burn from a JSON configuration (references/config.md).

  python3 burn.py CONFIG --out DIR [--check-tolerance] [--top 15]

Writes DIR/abundances.csv (t, T, rho, E and every mass fraction at the output times),
DIR/results.json (final abundances, observables, rate provenance, conservation and solver
checks, provenance block) and prints a short summary. --check-tolerance repeats the run with
rtol/100 and atol/1e4 and reports the largest relative change of the observables; a result is
not converged if that change is comparable to the effect being studied.
"""

import argparse
import csv
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import build  # noqa: E402
import netlib as nl  # noqa: E402
import prov  # noqa: E402


def run(cfg, net, Y0, cond, tout, rtol=None, atol=None):
    s = cfg.get("solver", {})
    return nl.burn(net, Y0, cond, tout, rtol=rtol or s.get("rtol", 1e-6),
                   atol=atol or s.get("atol", 1e-20), method=s.get("method", "BDF"))


def observables(cfg, net, res):
    obs = {}
    for expr in cfg.get("output", {}).get("observables", []):
        obs[expr] = nl.observable(net, res["X"][-1], res["Y"][-1], res["E"][-1], expr)
    return obs


def below_floor(cfg, net, res, factor=1e3):
    """Observables containing an abundance within `factor` x atol of zero (Y units): numbers
    there are solver noise, not results."""
    import re
    atol = res["atol"]
    out = []
    for expr in cfg.get("output", {}).get("observables", []):
        for name in re.findall(r"[XY]\(([^)]+)\)", expr):
            n = nl.pyna.Nucleus.cast(name)
            if n in net.index and abs(res["Y"][-1][net.index[n]]) < factor * atol:
                out.append(expr)
                break
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--out", required=True)
    ap.add_argument("--check-tolerance", action="store_true")
    ap.add_argument("--top", type=int, default=15, help="nuclei printed in the summary")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = build.load(a.config)
    t0 = time.time()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        net, info = build.build(cfg)
        cond = build.conditions(cfg)
        Y0 = build.initial_Y(cfg, net)
        tout = build.output_times(cfg, cond)
        res = run(cfg, net, Y0, cond, tout)
    wall = time.time() - t0

    Xf = res["X"][-1]
    sumX = res["X"].sum(axis=1)
    obs = observables(cfg, net, res)
    checks = {
        "max_abs_sumX_minus_1": float(np.max(np.abs(sumX - 1))),
        "min_Y": float(res["Y"].min()),
        "negative_abundances": bool(res["Y"].min() < -1e-12),
    }
    if a.check_tolerance:
        s = cfg.get("solver", {})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            tight = run(cfg, net, Y0, cond, tout, rtol=s.get("rtol", 1e-6) / 100,
                        atol=s.get("atol", 1e-20) / 1e4)
        o2 = observables(cfg, net, tight)
        floor = below_floor(cfg, net, res)
        rel = {k: abs(o2[k] / obs[k] - 1) if obs[k] else abs(o2[k]) for k in obs if k not in floor}
        checks["tolerance_rel_change"] = rel
        checks["tolerance_max_rel_change"] = max(rel.values()) if rel else None
        checks["below_solver_floor"] = floor
        Xt = tight["X"][-1]
        big = Xf > 1e-12
        checks["tolerance_max_rel_change_X_gt_1e-12"] = float(np.max(np.abs(Xt[big] / Xf[big] - 1)))

    with open(out / "abundances.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_s", "T_K", "rho_cgs", "E_erg_per_g"] + [f"X_{n}" for n in net.names])
        for k in range(len(res["t"])):
            w.writerow([f"{res['t'][k]:.8e}", f"{res['T'][k]:.6e}", f"{res['rho'][k]:.6e}",
                        f"{res['E'][k]:.8e}"] + [f"{x:.8e}" for x in res["X"][k]])
    order = np.argsort(-Xf)
    result = {
        "config": {k: v for k, v in cfg.items() if not k.startswith("_")},
        "final_time_s": float(res["t"][-1]),
        "final_X": {net.names[i]: float(Xf[i]) for i in order},
        "observables": obs,
        "E_erg_per_g": float(res["E"][-1]),
        "checks": checks,
        "solver": {**res["stats"], "rtol": res["rtol"], "atol": res["atol"], "method": res["method"],
                   "wall_s": wall},
        "network": info,
        "provenance": prov.block(inputs=[Path(a.config), *prov.config_inputs(cfg)],
                                 tools={"pynucastro": info["pynucastro"]}),
    }
    prov.write_json(out / "results.json", result)

    print(f"network: {info['n_nuclei']} nuclei, {info['n_rates']} rates, screening {info['screening']}")
    for s in info["substitutions"]:
        print(f"  {s}")
    for wmsg in info["warnings"]:
        print(f"  WARNING {wmsg}")
    print(f"t_end {res['t'][-1]:.4e} s  E {res['E'][-1]:.4e} erg/g  |sum X - 1| {checks['max_abs_sumX_minus_1']:.1e}"
          f"  wall {wall:.1f} s")
    for i in order[: a.top]:
        print(f"  X({net.names[i]:>5s}) = {Xf[i]:.5e}")
    for k, v in obs.items():
        print(f"  {k} = {v:.6e}")
    if a.check_tolerance:
        print(f"tolerance check: max relative change of observables {checks['tolerance_max_rel_change']}")
        for k in checks["below_solver_floor"]:
            print(f"  UNRESOLVED {k}: abundance at the solver floor (< 1e3 x atol); "
                  "lower atol or shorten the burn before quoting it")
    if checks["negative_abundances"]:
        print("WARNING negative abundances: tighten atol or inspect the network")
    return 0


if __name__ == "__main__":
    sys.exit(main())
