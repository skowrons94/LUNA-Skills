#!/usr/bin/env python3
"""Back-test skeleton: did an evaluation's quoted uncertainties cover later measurements?

Input: a CSV with columns id, lineage, earlier, sigma_earlier, later, sigma_later
(one row per pair that passed the pre-stated selection rule).

    python backtest_skeleton.py pairs.csv
    python backtest_skeleton.py --selftest
"""
import argparse
import csv
import sys

import numpy as np
from scipy import stats

P1 = stats.norm.cdf(1) - stats.norm.cdf(-1)  # 0.6827
P2 = stats.norm.cdf(2) - stats.norm.cdf(-2)  # 0.9545


def pulls(earlier, s_earlier, later, s_later):
    """Primary pull with the combined uncertainty, and z_e = shift / sigma_earlier."""
    earlier, s_earlier, later, s_later = map(np.asarray, (earlier, s_earlier, later, s_later))
    shift = later - earlier
    return shift / np.hypot(s_earlier, s_later), shift / s_earlier


def coverage(z):
    """Counts inside 1 and 2 sigma, with two-sided exact binomial p-values under calibration."""
    z = np.abs(np.asarray(z))
    n = len(z)
    out = {"n": n}
    for k, p in ((1, P1), (2, P2)):
        inside = int(np.sum(z < k))
        out[f"in{k}"] = inside
        out[f"p{k}"] = stats.binomtest(inside, n, p).pvalue
    out["rms"] = float(np.sqrt(np.mean(z ** 2)))
    out["mean_abs"] = float(np.mean(z))
    out["median_abs"] = float(np.median(z))
    return out


def lineage_bootstrap(z, lineage, n_boot=2000, rng=None):
    """68% interval of the rms pull, resampling whole lineages (needs many lineages)."""
    rng = rng or np.random.default_rng()
    z = np.asarray(z)
    lineage = np.asarray(lineage)
    groups = [z[lineage == g] for g in np.unique(lineage)]
    rms = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        zz = np.concatenate([groups[i] for i in pick])
        rms.append(np.sqrt(np.mean(zz ** 2)))
    return tuple(np.percentile(rms, [16, 84])), len(groups)


def report(rows):
    e, se, l, sl = (np.array([float(r[k]) for r in rows])
                    for k in ("earlier", "sigma_earlier", "later", "sigma_later"))
    z, ze = pulls(e, se, l, sl)
    c = coverage(z)
    print(f"pairs: {c['n']}")
    print(f"inside 1 sigma: {c['in1']}/{c['n']} (expected {P1 * c['n']:.1f}), exact binomial p = {c['p1']:.3g}")
    print(f"inside 2 sigma: {c['in2']}/{c['n']} (expected {P2 * c['n']:.1f}), exact binomial p = {c['p2']:.3g}")
    print(f"pull rms {c['rms']:.2f}, mean |pull| {c['mean_abs']:.2f}, median |pull| {c['median_abs']:.2f}")
    if "lineage" in rows[0]:
        (lo, hi), ng = lineage_bootstrap(z, [r["lineage"] for r in rows])
        print(f"rms pull 68% lineage bootstrap [{lo:.2f}, {hi:.2f}] over {ng} lineages"
              + ("  (too few lineages: indicative only)" if ng < 10 else ""))
    for r, zi, zei in sorted(zip(rows, z, ze), key=lambda t: -abs(t[1])):
        print(f"  {r['id']:<20s} pull {zi:+.2f}   z_e {zei:+.2f}")


def selftest(check):
    rng = np.random.default_rng(3)
    n = 4000
    truth = rng.normal(10, 1, n)
    se = np.full(n, 0.5)
    sl = np.full(n, 0.3)
    e = truth + rng.normal(0, se)
    l = truth + rng.normal(0, sl)
    z, ze = pulls(e, se, l, sl)
    c = coverage(z)
    check(f"calibrated: 1-sigma coverage {c['in1'] / n:.3f} near {P1:.3f}", abs(c["in1"] / n - P1) < 0.03)
    check("calibrated: binomial p not small", c["p1"] > 0.001 and c["p2"] > 0.001)
    check("calibrated: rms pull near 1", abs(c["rms"] - 1) < 0.05)
    check("z_e exceeds pull in magnitude", np.all(np.abs(ze) >= np.abs(z)))

    e_bad = truth + rng.normal(0, 2 * se)  # quoted sigma is half the true error
    c_bad = coverage(pulls(e_bad, se, l, sl)[0])
    check(f"under-reported: coverage {c_bad['in1'] / n:.3f} well below {P1:.3f}", c_bad["in1"] / n < 0.55)
    check("under-reported: binomial p tiny", c_bad["p1"] < 1e-6)

    small = coverage(pulls(e[:8], se[:8], l[:8], sl[:8])[0])
    check("eight pairs: exact p defined and in (0, 1]", 0 < small["p1"] <= 1)

    lineage = np.repeat(np.arange(40), n // 40)
    (lo, hi), ng = lineage_bootstrap(z, lineage, n_boot=300, rng=rng)
    check(f"lineage bootstrap interval [{lo:.2f}, {hi:.2f}] contains 1", lo < 1 < hi and ng == 40)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or not a.csv:
        failed = []

        def check(name, cond):
            print(("PASS  " if cond else "FAIL  ") + name)
            if not cond:
                failed.append(name)

        selftest(check)
        print("FAIL" if failed else "PASS")
        sys.exit(1 if failed else 0)
    with open(a.csv, newline="") as f:
        report(list(csv.DictReader(f)))
