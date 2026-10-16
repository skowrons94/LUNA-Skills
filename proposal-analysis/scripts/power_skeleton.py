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
not knowledge of the truth. Removing flagged runs before the test inflates the
size of TOST above alpha: the robust flag also removes ordinary tail runs,
which shrinks the spread of the campaign means (5.6% instead of 5% in the
default design, 5.9% without gross errors; 2 x 10^5 trials). Calibrate the critical
value (or alpha, or the margin) by simulation of the complete protocol, as
calibrated_t() does, or pre-register the flag rule and report the simulated
size. Reported: power, false-pass rate at the margin, the same without
flagging and for a naive item-level test, and the joint pass probability.

    python power_skeleton.py [--trials N] [--seed S]
    python power_skeleton.py --selftest [--seed S]
"""
import argparse
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
    flag_k: float = 3.0       # robust-z threshold for flagging a run (np.inf: no flagging)


def simulate(d, bias, rng, n_trials):
    """Item residuals with shape (trial, campaign, run, item)."""
    shape_run = (n_trials, d.n_campaigns, d.runs_per_campaign, 1)
    c = rng.normal(0, d.sd_campaign, (n_trials, d.n_campaigns, 1, 1))
    r = rng.normal(0, d.sd_run, shape_run)
    bad = rng.random(shape_run) < d.p_gross
    sign = rng.choice([-1.0, 1.0], shape_run)
    e = rng.normal(0, 1, shape_run[:3] + (d.items_per_run,))
    return bias + c + r + e + bad * sign * d.gross_shift


def flag_runs(x, k):
    """Robust-z flag on run means, per trial; returns (trial, campaign, run) booleans."""
    m = x.mean(axis=3)
    med = np.median(m, axis=(1, 2), keepdims=True)
    mad = 1.4826 * np.median(np.abs(m - med), axis=(1, 2), keepdims=True)
    return np.abs(m - med) > k * np.maximum(mad, 1e-12)


def tost_stat(values, valid, margin):
    """(margin - |mean|) / se over the valid entries of the last axis, and the degrees of freedom.

    TOST passes when the statistic exceeds t_{1-alpha, dof}.
    """
    n = valid.sum(axis=-1)
    v = np.where(valid, values, 0.0)
    mean = v.sum(axis=-1) / np.maximum(n, 1)
    var = (np.where(valid, values - mean[..., None], 0.0) ** 2).sum(axis=-1) / np.maximum(n - 1, 1)
    se = np.sqrt(var / np.maximum(n, 1))
    stat = np.where(n >= 2, (margin - np.abs(mean)) / np.maximum(se, 1e-300), -np.inf)
    return stat, n - 1


def cp_upper(k, n, cl=0.95):
    """One-sided Clopper-Pearson upper bound (vectorised over k)."""
    k = np.asarray(k)
    return np.where(k >= n, 1.0, stats.beta.ppf(cl, k + 1, np.maximum(n - k, 1)))


def statistics(d, bias, n_trials, rng):
    """Per-trial TOST statistics (flagged, unflagged, naive), their dof and the endpoint-B result."""
    x = simulate(d, bias, rng, n_trials)
    margin = d.margin * (1 + d.margin_sd * rng.normal(size=n_trials)) if d.margin_sd else d.margin
    flags = flag_runs(x, d.flag_k)
    keep = ~flags
    run_sum = x.sum(axis=3)
    n_items = keep.sum(axis=2) * d.items_per_run
    camp = (run_sum * keep).sum(axis=2) / np.maximum(n_items, 1)
    a, dof = tost_stat(camp, n_items > 0, margin)
    a0, dof0 = tost_stat(x.mean(axis=(2, 3)), np.ones(camp.shape, bool), margin)
    items = x.reshape(n_trials, -1)
    item_keep = np.repeat(keep.reshape(n_trials, -1), d.items_per_run, axis=1)
    an, dofn = tost_stat(items, item_keep, margin)
    b = cp_upper(flags.reshape(n_trials, -1).sum(axis=1), flags[0].size) < d.p_max
    return {"A": (a, dof), "A_noflag": (a0, dof0), "A_naive": (an, dofn), "B": b}


def rates(d, bias, n_trials, rng, t_crit=None):
    """Pass rates; t_crit replaces t_{1-alpha} for endpoint A (a simulation-calibrated value)."""
    s = statistics(d, bias, n_trials, rng)
    out = {}
    for key in ("A", "A_noflag", "A_naive"):
        stat, dof = s[key]
        crit = stats.t.ppf(1 - d.alpha, np.maximum(dof, 1)) if (t_crit is None or key != "A") else t_crit
        out[key] = stat > crit
    res = {k: float(v.mean()) for k, v in out.items()}
    res["B"] = float(s["B"].mean())
    res["joint"] = float((out["A"] & s["B"]).mean())
    return res


def calibrated_t(d, n_trials=20000, rng=None):
    """Critical value for endpoint A whose simulated false-pass rate at bias = margin equals alpha."""
    rng = rng or np.random.default_rng()
    stat, _ = statistics(d, d.margin, n_trials, rng)["A"]
    return float(np.quantile(stat, 1 - d.alpha))


def summary(d, n_trials=20000, seed=1):
    rng = np.random.default_rng(seed)
    return {"power (bias 0)": rates(d, 0.0, n_trials, rng),
            "false pass (bias = margin)": rates(d, d.margin, n_trials, rng)}


def selftest(check, seed=1):
    d = Design()
    n = 20000
    mc = np.sqrt(d.alpha * (1 - d.alpha) / n)
    s = summary(d, n, seed)
    pw, fp = s["power (bias 0)"], s["false pass (bias = margin)"]
    # Without gross errors the unflagged t-test on campaign means is exact; flagging alone inflates
    # its size (paired comparison on the same pseudo-data).
    clean = rates(replace(d, p_gross=0.0), d.margin, n, np.random.default_rng(seed + 10))
    check(f"no gross errors: unflagged cluster TOST false pass {clean['A_noflag']:.4f} = alpha within 3 MC s.e.",
          abs(clean["A_noflag"] - d.alpha) < 3 * mc)
    check(f"no gross errors: flagging inflates the size ({clean['A']:.4f} vs {clean['A_noflag']:.4f} unflagged)",
          clean["A"] > clean["A_noflag"] + 1.5 * mc)
    check(f"default design: flagged cluster TOST false pass {fp['A']:.4f} reported; within [alpha, 1.5 alpha]"
          " up to MC noise", d.alpha - 3 * mc < fp["A"] < 1.5 * d.alpha)
    t_cal = calibrated_t(d, n, np.random.default_rng(seed + 20))
    cal = rates(d, d.margin, n, np.random.default_rng(seed + 30), t_crit=t_cal)
    # Calibration and check each carry MC noise, so the tolerance is 4 single-run s.e. (2.8 combined).
    check(f"simulation-calibrated t = {t_cal:.3f}: false pass {cal['A']:.4f} = alpha within 4 MC s.e.",
          abs(cal["A"] - d.alpha) < 4 * mc)
    check(f"naive item-level TOST false pass {fp['A_naive']:.3f} inflated (> 2 alpha)", fp["A_naive"] > 2 * d.alpha)
    check(f"power {pw['A']:.3f} well above false pass", pw["A"] > 0.5 > fp["A"])
    check(f"sanity: joint pass {pw['joint']:.3f} <= each endpoint", pw["joint"] <= min(pw["A"], pw["B"]) + 1e-12)
    worse = rates(replace(d, p_gross=0.30), 0.0, 2000, np.random.default_rng(seed + 2))
    check(f"gross endpoint fails when the per-run rate is high ({worse['B']:.3f} < 0.2)", worse["B"] < 0.2)
    noisy = rates(replace(d, margin_sd=0.2), d.margin, n, np.random.default_rng(seed + 3))
    check(f"uncertain margin raises false pass ({noisy['A']:.4f} > {fp['A']:.4f} + 3 MC s.e.)",
          noisy["A"] > fp["A"] + 3 * mc)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--trials", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    if a.selftest:
        failed = []

        def check(name, cond):
            print(("PASS  " if cond else "FAIL  ") + name)
            if not cond:
                failed.append(name)

        selftest(check, a.seed)
        print("FAIL" if failed else "PASS")
        sys.exit(1 if failed else 0)
    d = Design()
    for case, r in summary(d, a.trials, a.seed).items():
        print(case + ": " + ", ".join(f"{k} {v:.3f}" for k, v in r.items()))
    print(f"simulation-calibrated critical value for endpoint A: t = "
          f"{calibrated_t(d, a.trials, np.random.default_rng(a.seed + 1)):.3f} "
          f"(nominal t_(1-alpha) = {stats.t.ppf(1 - d.alpha, d.n_campaigns - 1):.3f})")
