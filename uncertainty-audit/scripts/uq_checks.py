#!/usr/bin/env python3
"""Quantitative checks of whether quoted uncertainties are right.

  residuals    TABLE.csv --data y --model m --sigma dy [--x E] [--group dataset]
      chi2/nu with p-value, pull mean and width, Wald-Wolfowitz runs test on the sign of the
      residuals ordered in x, and a sliding-window scan for localised structure (missed level,
      contaminant) with a look-elsewhere-calibrated p-value; per group and overall.
  coverage     TABLE.csv --obs y --obs-err dy --pred m --pred-err dm
      Held-out or later data against a prediction band: fraction inside 1 and 2 combined sigma,
      compared with 68.3 % and 95.4 %, and the z-score distribution.
  correlations COV.csv [--names a b c]
      Parameter correlation matrix from a covariance; flags |rho| > 0.95 (parameters the data
      do not separate) and non-positive-definite covariances.

Writes a JSON summary with --out. NumPy and SciPy.
"""

import argparse
import json
import sys

import numpy as np
from scipy import stats


def runs_test(signs):
    """Wald-Wolfowitz runs test on a +/- sequence; returns (runs, expected, z, two-sided p)."""
    s = np.asarray(signs) > 0
    n1, n2 = int(s.sum()), int((~s).sum())
    if n1 == 0 or n2 == 0:
        return int(1), float("nan"), float("inf"), 0.0
    runs = 1 + int(np.count_nonzero(s[1:] != s[:-1]))
    mu = 2 * n1 * n2 / (n1 + n2) + 1
    var = 2 * n1 * n2 * (2 * n1 * n2 - n1 - n2) / ((n1 + n2) ** 2 * (n1 + n2 - 1))
    z = (runs - mu) / np.sqrt(var) if var > 0 else 0.0
    return runs, mu, float(z), float(2 * stats.norm.sf(abs(z)))


def window_stat(pull, widths):
    """Largest |sum of consecutive pulls| / sqrt(width) over all windows of the given widths."""
    c = np.concatenate([[0.0], np.cumsum(pull)])
    best, where = 0.0, (0, 0)
    for w in widths:
        if w > len(pull):
            continue
        z = np.abs(c[w:] - c[:-w]) / np.sqrt(w)
        i = int(np.argmax(z))
        if z[i] > best:
            best, where = float(z[i]), (i, i + w)
    return best, where


def local_structure(pull, widths=(3, 5, 10, 20, 40), n_sim=2000, seed=0):
    """Scan for a localised excess or deficit (missed resonance, contaminant, bad segment).
    The p-value is calibrated on standard-normal pulls of the same length, so it includes the
    look-elsewhere effect of scanning many windows."""
    obs, where = window_stat(pull, widths)
    rng = np.random.default_rng(seed)
    null = np.array([window_stat(rng.standard_normal(len(pull)), widths)[0] for _ in range(n_sim)])
    return obs, where, float((np.sum(null >= obs) + 1) / (n_sim + 1))


def residual_summary(y, m, s, x=None, n_par=0):
    y, m, s = map(np.asarray, (y, m, s))
    pull = (y - m) / s
    n = len(pull)
    chi2 = float(np.sum(pull ** 2))
    dof = max(n - n_par, 1)
    order = np.argsort(x) if x is not None else np.arange(n)
    runs, mu, z, p_runs = runs_test(pull[order])
    zloc, (i0, i1), p_loc = local_structure(pull[order])
    xs = np.asarray(x)[order] if x is not None else order
    flags = []
    p_chi2 = float(stats.chi2.sf(chi2, dof))
    if p_chi2 < 0.01:
        flags.append("chi2 too large: model misses data or uncertainties too small")
    if p_chi2 > 0.999 and n > 10:
        flags.append("chi2 too small: uncertainties overestimated or correlated")
    if p_runs < 0.01 and z < 0:
        flags.append("too few sign runs: structured residuals the model does not reproduce")
    if p_loc < 0.01:
        flags.append(f"localised structure over x = {xs[i0]:g}..{xs[i1 - 1]:g} "
                     f"(window z = {zloc:.1f}, global p = {p_loc:.3g}): missed level, contaminant or bad segment")
    if abs(np.mean(pull)) > 3 / np.sqrt(n):
        flags.append("pull mean offset: normalisation or energy-scale bias")
    return {"n": n, "chi2": chi2, "dof": dof, "chi2_per_dof": chi2 / dof, "p_chi2": p_chi2,
            "pull_mean": float(np.mean(pull)), "pull_std": float(np.std(pull, ddof=1)) if n > 1 else float("nan"),
            "runs": runs, "runs_expected": mu, "runs_z": z, "p_runs": p_runs,
            "local_z": zloc, "local_window": [float(xs[i0]), float(xs[i1 - 1])], "p_local": p_loc,
            "max_abs_pull": float(np.max(np.abs(pull))), "flags": flags}


def coverage_summary(y, dy, m, dm):
    y, dy, m, dm = map(np.asarray, (y, dy, m, dm))
    z = (y - m) / np.sqrt(dy ** 2 + dm ** 2)
    n = len(z)
    f1, f2 = float(np.mean(np.abs(z) < 1)), float(np.mean(np.abs(z) < 2))
    # binomial check of the 1-sigma fraction
    p1 = float(stats.binomtest(int(round(f1 * n)), n, 0.6827).pvalue) if n else float("nan")
    flags = []
    if p1 < 0.05 and f1 < 0.6827:
        flags.append("under-coverage: prediction band (or data errors) too narrow")
    if p1 < 0.05 and f1 > 0.6827:
        flags.append("over-coverage: prediction band too wide or errors double counted")
    if n and abs(np.mean(z)) > 3 / np.sqrt(n):
        flags.append("systematic offset between prediction and held-out data")
    return {"n": n, "frac_within_1sigma": f1, "frac_within_2sigma": f2, "expected": [0.6827, 0.9545],
            "p_binomial_1sigma": p1, "z_mean": float(np.mean(z)), "z_std": float(np.std(z, ddof=1)) if n > 1 else float("nan"),
            "max_abs_z": float(np.max(np.abs(z))) if n else float("nan"), "flags": flags}


def correlation_summary(cov, names=None):
    cov = np.asarray(cov, float)
    n = cov.shape[0]
    names = names or [f"p{i}" for i in range(n)]
    d = np.sqrt(np.clip(np.diag(cov), 0, None))
    with np.errstate(invalid="ignore", divide="ignore"):
        rho = cov / np.outer(d, d)
    eig = np.linalg.eigvalsh(0.5 * (cov + cov.T))
    flags = []
    if eig.min() <= 0:
        flags.append("covariance not positive definite: fit did not converge or parameters are degenerate")
    pairs = [(names[i], names[j], float(rho[i, j])) for i in range(n) for j in range(i + 1, n)
             if abs(rho[i, j]) > 0.95]
    for a, b, r in pairs:
        flags.append(f"|rho({a},{b})| = {abs(r):.3f}: the data do not separate these parameters")
    return {"correlation": rho.tolist(), "names": names, "min_eigenvalue": float(eig.min()),
            "condition_number": float(eig.max() / eig.min()) if eig.min() > 0 else float("inf"),
            "strong_pairs": pairs, "flags": flags}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("residuals")
    r.add_argument("table")
    r.add_argument("--data", required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--sigma", required=True)
    r.add_argument("--x")
    r.add_argument("--group")
    r.add_argument("--n-par", type=int, default=0, help="number of fitted parameters (for dof)")
    c = sub.add_parser("coverage")
    c.add_argument("table")
    for k in ("obs", "obs-err", "pred", "pred-err"):
        c.add_argument(f"--{k}", required=True)
    k = sub.add_parser("correlations")
    k.add_argument("cov")
    k.add_argument("--names", nargs="*")
    for p in (r, c, k):
        p.add_argument("--out")
    a = ap.parse_args()

    if a.cmd == "correlations":
        cov = np.loadtxt(a.cov, delimiter=",")
        res = correlation_summary(cov, a.names)
    else:
        t = np.genfromtxt(a.table, delimiter=",", names=True, dtype=None, encoding=None)
        col = lambda name: np.asarray(t[name], float)
        if a.cmd == "residuals":
            groups = {"all": np.ones(len(t), bool)}
            if a.group:
                g = np.asarray(t[a.group]).astype(str)
                groups.update({u: g == u for u in np.unique(g)})
            res = {}
            for name, sel in groups.items():
                x = col(a.x)[sel] if a.x else None
                res[name] = residual_summary(col(a.data)[sel], col(a.model)[sel], col(a.sigma)[sel], x,
                                             a.n_par if name == "all" else 0)
        else:
            res = coverage_summary(col(a.obs), col(a.obs_err), col(a.pred), col(a.pred_err))

    def show(name, d):
        keys = [k for k in d if k not in ("flags", "correlation", "names", "strong_pairs")]
        print(f"[{name}] " + "  ".join(f"{k}={d[k]:.4g}" if isinstance(d[k], float) else f"{k}={d[k]}" for k in keys))
        for f in d["flags"]:
            print(f"  FLAG  {f}")

    if a.cmd == "residuals":
        for name, d in res.items():
            show(name, d)
    else:
        show(a.cmd, res)
    if a.out:
        with open(a.out, "w") as f:
            json.dump(res, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
