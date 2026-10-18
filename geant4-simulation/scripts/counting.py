#!/usr/bin/env python3
"""Standard counting analyses for simulated detectors (standard library only).

Efficiency with binomial (Wilson) or weighted uncertainties, flatness of efficiency against energy,
die-away time by truncated maximum likelihood, time-gate fractions, dead time and pile-up from rates.

    python3 counting.py efficiency out/scan_r*.json              # efficiency vs source energy, flatness
    python3 counting.py dieaway out/smoke_r0_captures.csv --tmin 20 --tmax 1000
    python3 counting.py deadtime --rate 2e4 --tau 2e-6          # true rate in 1/s, tau in s
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys


def efficiency(k: float, n: float, z: float = 1.0) -> dict:
    """Binomial efficiency k/n with the Wilson score interval (z = 1 for 68 %)."""
    if n <= 0:
        raise ValueError("n must be positive")
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return {"eff": p, "sigma": math.sqrt(p * (1 - p) / n), "lo": centre - half, "hi": centre + half}


def weighted_efficiency(sum_w_pass: float, sum_w2_pass: float, sum_w_all: float) -> dict:
    """Efficiency from weighted events; sigma from sum of w^2 of passing events (valid when the pass
    fraction is small or the weights of all events are known only through their sum)."""
    return {"eff": sum_w_pass / sum_w_all, "sigma": math.sqrt(sum_w2_pass) / sum_w_all}


def flatness(values: list[float], sigmas: list[float] | None = None) -> dict:
    """Max/min ratio and relative spread of an efficiency curve (or any response) over its points."""
    mean = sum(values) / len(values)
    rms = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    out = {"mean": mean, "max_over_min": max(values) / min(values), "rel_spread": rms / mean}
    if sigmas:  # chi2 of the constant hypothesis: is the curve flat within statistics?
        w = [1 / s ** 2 for s in sigmas]
        wm = sum(wi * v for wi, v in zip(w, values)) / sum(w)
        out["chi2_flat"] = sum((v - wm) ** 2 / s ** 2 for v, s in zip(values, sigmas))
        out["ndf"] = len(values) - 1
    return out


def die_away(times: list[float], t_min: float, t_max: float) -> dict:
    """Single-exponential decay constant from capture times inside [t_min, t_max] (truncated MLE).

    Exclude the early thermalisation region with t_min; check stability by varying it."""
    t = [x - t_min for x in times if t_min <= x <= t_max]
    n = len(t)
    if n < 2:
        raise ValueError("fewer than 2 times inside the window")
    w, mean = t_max - t_min, sum(t) / n

    def score(tau):  # d logL / d tau = 0  <=>  mean = tau - w / (exp(w/tau) - 1)
        x = w / tau
        return tau - (w / math.expm1(x) if x < 700 else 0.0) - mean

    lo, hi = 1e-9 * w, 1e6 * w
    if score(hi) < 0:  # flat distribution: no decay within the window
        return {"tau": math.inf, "sigma": math.inf, "n": n}
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if score(mid) < 0 else (lo, mid)
    tau = math.sqrt(lo * hi)
    x = w / tau  # Fisher information of the truncated exponential
    var_t = tau ** 2 - (w ** 2 * math.exp(x) / math.expm1(x) ** 2 if x < 700 else 0.0)
    sigma = tau ** 2 / math.sqrt(n * var_t) if var_t > 0 else math.inf
    return {"tau": tau, "sigma": sigma, "n": n}


def gate_fraction(tau: float, t_open: float, t_close: float) -> float:
    """Fraction of single-exponential captures inside a gate [t_open, t_close] after the source event."""
    return math.exp(-t_open / tau) - math.exp(-t_close / tau)


def measured_rate(true_rate: float, tau: float, model: str = "nonparalyzable") -> float:
    if model == "nonparalyzable":
        return true_rate / (1 + true_rate * tau)
    if model == "paralyzable":
        return true_rate * math.exp(-true_rate * tau)
    raise ValueError(model)


def true_rate(meas_rate: float, tau: float, model: str = "nonparalyzable") -> float:
    """Invert the dead-time model; for the paralyzable model the low-rate branch (n tau < 1) is returned."""
    if model == "nonparalyzable":
        if meas_rate * tau >= 1:
            raise ValueError("measured rate exceeds 1/tau")
        return meas_rate / (1 - meas_rate * tau)
    if meas_rate * tau > 1 / math.e:
        raise ValueError("measured rate above the paralyzable maximum 1/(e tau)")
    n = meas_rate
    for _ in range(100):  # Newton on n exp(-n tau) = m
        f = n * math.exp(-n * tau) - meas_rate
        n -= f / (math.exp(-n * tau) * (1 - n * tau))
    return n


def pileup_probability(rate: float, window: float) -> float:
    """Probability that at least one other Poisson event falls within the resolving window."""
    return 1 - math.exp(-rate * window)


def accidentals_per_trigger(rate: float, gate: float) -> float:
    """Mean number of uncorrelated counts in a gate of length `gate` opened by each trigger."""
    return rate * gate


def _cli_efficiency(paths):
    rows = []
    for p in paths:
        d = json.load(open(p))
        e = efficiency(d["gas_captures"], d["n_generated"]) if d.get("sum_weights") == d["n_generated"] else \
            weighted_efficiency(d["gas_captures"], d["gas_captures_w2"], d["sum_weights"])
        rows.append((d["source"]["spectrum"], d["source"]["mean_E0_MeV"], e["eff"], e["sigma"], p))
    for spec, e0, eff, sig, p in rows:
        print(f"{spec:8s} E0_mean={e0:10.5g} MeV  eff={eff:.5f} +- {sig:.5f}  {p}")
    if len(rows) > 1:
        print(json.dumps(flatness([r[2] for r in rows], [r[3] for r in rows])))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("efficiency")
    s.add_argument("json", nargs="+")
    s = sub.add_parser("dieaway")
    s.add_argument("csv")
    s.add_argument("--column", default="t_us")
    s.add_argument("--tmin", type=float, required=True)
    s.add_argument("--tmax", type=float, required=True)
    s = sub.add_parser("deadtime")
    s.add_argument("--rate", type=float, required=True, help="true rate, 1/s")
    s.add_argument("--tau", type=float, required=True, help="dead time or resolving time, s")
    a = ap.parse_args(argv)
    if a.cmd == "efficiency":
        _cli_efficiency(a.json)
    elif a.cmd == "dieaway":
        with open(a.csv) as f:
            times = [float(r[a.column]) for r in csv.DictReader(line for line in f if not line.startswith("#"))]
        print(json.dumps(die_away(times, a.tmin, a.tmax)))
    else:
        out = {m: measured_rate(a.rate, a.tau, m) for m in ("nonparalyzable", "paralyzable")}
        out["pileup_probability"] = pileup_probability(a.rate, a.tau)
        print(json.dumps(out))
    return 0


def selftest(check, seed: int = 11):
    import random
    rng = random.Random(seed)
    e = efficiency(30, 100)
    check("efficiency: Wilson interval brackets k/n", e["lo"] < 0.3 < e["hi"])
    check("efficiency: k = 0 gives a positive upper bound", efficiency(0, 50)["hi"] > 0)
    w = weighted_efficiency(10.0, 10.0, 100.0)
    check("weighted efficiency with unit weights", abs(w["eff"] - 0.1) < 1e-12 and abs(w["sigma"] - 10 ** 0.5 / 100) < 1e-12)
    f = flatness([0.20, 0.21, 0.19], [0.005] * 3)
    check("flatness: ratio and chi2", abs(f["max_over_min"] - 0.21 / 0.19) < 1e-12 and abs(f["chi2_flat"] - 8.0) < 1e-9)
    tau = 80.0
    times = [5.0 + rng.expovariate(1 / tau) for _ in range(20000)]
    d = die_away(times, 10.0, 600.0)
    check("die-away: truncated MLE recovers tau within 3 sigma", abs(d["tau"] - tau) < 3 * d["sigma"])
    d2 = die_away(times, 40.0, 300.0)
    check("die-away: independent of the window start (memoryless)", abs(d2["tau"] - tau) < 3 * d2["sigma"])
    check("gate fraction: full gate is 1", abs(gate_fraction(tau, 0, 1e9) - 1) < 1e-12)
    m = measured_rate(1e5, 1e-6)
    check("dead time: non-paralyzable round trip", abs(true_rate(m, 1e-6) - 1e5) < 1e-6)
    m = measured_rate(1e5, 1e-6, "paralyzable")
    check("dead time: paralyzable round trip", abs(true_rate(m, 1e-6, "paralyzable") - 1e5) < 1e-3)
    check("pile-up: small-rate limit rate*window", abs(pileup_probability(10.0, 1e-4) - 1e-3) < 1e-6)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(main())
    failed = []

    def _check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            failed.append(name)

    selftest(_check)
    print("FAIL" if failed else "PASS")
    sys.exit(1 if failed else 0)
