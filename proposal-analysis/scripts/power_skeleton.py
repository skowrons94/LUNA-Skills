#!/usr/bin/env python3
"""Power-simulation skeleton with clustered errors and run-level gross errors.

Structure: campaigns > runs > items. Each item residual (measured - reference,
in units of the item uncertainty) is

    bias + campaign effect + run error + item noise   (+ gross shift on a bad run)

Endpoints (fixed before simulation; edit for the real protocol):
  A  equivalence: |bias| < margin by TOST at alpha, on campaign means
     (the independent units), after removing runs flagged as gross;
  B  gross-error rate: Clopper-Pearson upper bound on the per-run gross rate
     below p_max, counting flagged runs (not items).

The flag is a rule applied to the data (robust outlier test on run means),
not knowledge of the truth. Reported: power, false-pass rate at the margin,
the same for a naive item-level test, and the joint pass probability.

    python power_skeleton.py
    python power_skeleton.py --selftest
"""
import sys
from dataclasses import dataclass, replace

import numpy as np
from scipy import stats


@dataclass
class Design:
    n_campaigns: int = 8
    runs_per_campaign: int = 4
    items_per_run: int = 10
    sd_campaign: float = 0.3
    sd_run: float = 0.4
    p_gross: float = 0.05     # probability that a whole run is bad
    gross_shift: float = 5.0
    margin: float = 0.6       # equivalence margin on the bias
    margin_sd: float = 0.0    # spread of a margin estimated from a small development set
    alpha: float = 0.05
    p_max: float = 0.25       # endpoint B threshold on the per-run gross rate
    flag_k: float = 3.0       # robust-z threshold for flagging a run


def simulate(d, bias, rng):
    """Return item residuals with shape (campaign, run, item)."""
    c = rng.normal(0, d.sd_campaign, (d.n_campaigns, 1, 1))
    r = rng.normal(0, d.sd_run, (d.n_campaigns, d.runs_per_campaign, 1))
    bad = rng.random((d.n_campaigns, d.runs_per_campaign, 1)) < d.p_gross
    sign = rng.choice([-1.0, 1.0], bad.shape)
    e = rng.normal(0, 1, (d.n_campaigns, d.runs_per_campaign, d.items_per_run))
    return bias + c + r + e + bad * sign * d.gross_shift


def flag_runs(x, k):
    m = x.mean(axis=2)
    med = np.median(m)
    mad = 1.4826 * np.median(np.abs(m - med))
    return np.abs(m - med) > k * max(mad, 1e-12)


def tost(values, margin, alpha):
    values = np.asarray(values)
    n = len(values)
    if n < 2:
        return False
    se = values.std(ddof=1) / np.sqrt(n)
    t = stats.t.ppf(1 - alpha, n - 1)
    return abs(values.mean()) + t * se < margin


def cp_upper(k, n, cl=0.95):
    return 1.0 if k == n else float(stats.beta.ppf(cl, k + 1, n - k))


def one_trial(d, bias, rng):
    x = simulate(d, bias, rng)
    margin = d.margin * (1 + d.margin_sd * rng.normal()) if d.margin_sd else d.margin
    flags = flag_runs(x, d.flag_k)
    keep = ~flags
    camp = [x[i][keep[i]].mean() for i in range(d.n_campaigns) if keep[i].any()]
    a_cluster = tost(camp, margin, d.alpha)
    a_naive = tost(x[keep].ravel(), margin, d.alpha)
    n_runs = flags.size
    b = cp_upper(int(flags.sum()), n_runs) < d.p_max
    return a_cluster, a_naive, b


def rates(d, bias, n_trials, rng):
    res = np.array([one_trial(d, bias, rng) for _ in range(n_trials)])
    return {"A": res[:, 0].mean(), "A_naive": res[:, 1].mean(), "B": res[:, 2].mean(),
            "joint": (res[:, 0] & res[:, 2]).mean()}


def summary(d, n_trials=2000, seed=1):
    rng = np.random.default_rng(seed)
    return {"power (bias 0)": rates(d, 0.0, n_trials, rng),
            "false pass (bias = margin)": rates(d, d.margin, n_trials, rng)}


def selftest(check):
    d = Design()
    n = 2000
    s = summary(d, n)
    pw, fp = s["power (bias 0)"], s["false pass (bias = margin)"]
    mc = np.sqrt(d.alpha * (1 - d.alpha) / n)
    check(f"cluster TOST false pass {fp['A']:.3f} <= alpha + 3 MC s.e.", fp["A"] <= d.alpha + 3 * mc)
    check(f"naive item-level TOST false pass {fp['A_naive']:.3f} inflated (> 2 alpha)", fp["A_naive"] > 2 * d.alpha)
    check(f"power {pw['A']:.3f} well above false pass", pw["A"] > 0.5 > fp["A"])
    check(f"joint pass {pw['joint']:.3f} <= each endpoint", pw["joint"] <= min(pw["A"], pw["B"]) + 1e-12)
    worse = rates(replace(d, p_gross=0.30), 0.0, 500, np.random.default_rng(2))
    check(f"gross endpoint fails when the per-run rate is high ({worse['B']:.3f} < 0.2)", worse["B"] < 0.2)
    noisy = rates(replace(d, margin_sd=0.2), d.margin, n, np.random.default_rng(3))
    check(f"uncertain margin raises false pass ({noisy['A']:.3f} > {fp['A']:.3f} + 2 MC s.e.)",
          noisy["A"] > fp["A"] + 2 * mc)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        failed = []

        def check(name, cond):
            print(("PASS  " if cond else "FAIL  ") + name)
            if not cond:
                failed.append(name)

        selftest(check)
        print("FAIL" if failed else "PASS")
        sys.exit(1 if failed else 0)
    for case, r in summary(Design()).items():
        print(case + ": " + ", ".join(f"{k} {v:.3f}" for k, v in r.items()))
