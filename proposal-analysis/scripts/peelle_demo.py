#!/usr/bin/env python3
"""Peelle's pertinent puzzle on synthetic data.

Two datasets measure one constant mu (true value 1). Each point has an
independent absolute error sigma; each dataset has its own multiplicative
normalization error f. Three treatments of the normalization:

  data   covariance f^2 y_i y_j built from the measured values (biased low)
  model  covariance f^2 mu^2 from the current estimate, iterated
  factor_ln    explicit factor k per dataset on the model, lognormal prior ln k / f
  factor_gauss same with a Gaussian prior (k - 1) / f: the MAP estimate is
               biased high at order f^2 (about +3% for f = 20% here)

    python peelle_demo.py            # prints the mean estimates
    python peelle_demo.py --selftest
"""
import sys

import numpy as np
from scipy.optimize import least_squares

SIGMA, F, NPTS, NSETS = 0.05, 0.20, 6, 2


def simulate(rng, mu=1.0):
    k = 1.0 + F * rng.normal(size=NSETS)
    y = (k[:, None] * mu + SIGMA * rng.normal(size=(NSETS, NPTS))).ravel()
    sets = np.repeat(np.arange(NSETS), NPTS)
    return y, sets


def gls_constant(y, cov):
    ci = np.linalg.inv(cov)
    one = np.ones_like(y)
    return float(one @ ci @ y / (one @ ci @ one))


def norm_cov(scale, sets):
    same = sets[:, None] == sets[None, :]
    return np.diag(np.full(len(sets), SIGMA ** 2)) + F ** 2 * np.outer(scale, scale) * same


def fit_data(y, sets):
    return gls_constant(y, norm_cov(y, sets))


def fit_model(y, sets, n_iter=20):
    mu = float(np.mean(y))
    for _ in range(n_iter):
        mu = gls_constant(y, norm_cov(np.full(len(y), mu), sets))
    return mu


def fit_factor(y, sets, prior="lognormal"):
    def resid(p):
        mu, lk = p[0], p[1:]
        k = np.exp(lk)
        pen = lk / F if prior == "lognormal" else (k - 1.0) / F
        return np.concatenate([(y - k[sets] * mu) / SIGMA, pen])

    return float(least_squares(resid, np.r_[np.mean(y), np.zeros(NSETS)]).x[0])


def run(n_trials=4000, seed=5):
    rng = np.random.default_rng(seed)
    est = {"data": [], "model": [], "factor_ln": [], "factor_gauss": []}
    for _ in range(n_trials):
        y, sets = simulate(rng)
        est["data"].append(fit_data(y, sets))
        est["model"].append(fit_model(y, sets))
        est["factor_ln"].append(fit_factor(y, sets, "lognormal"))
        est["factor_gauss"].append(fit_factor(y, sets, "gaussian"))
    return {k: np.array(v) for k, v in est.items()}


def selftest(check):
    est = run(n_trials=2000)
    for k, v in est.items():
        se = v.std(ddof=1) / np.sqrt(len(v))
        bias = v.mean() - 1.0
        if k == "data":
            check(f"data-based covariance biased low: {bias:+.4f} ({bias / se:+.1f} MC s.e.)", bias / se < -5)
        elif k == "factor_gauss":
            check(f"Gaussian-prior factor biased high at O(f^2): {bias:+.4f} ({bias / se:+.1f} MC s.e.)",
                  bias / se > 3 and bias < 0.05)
        else:
            check(f"{k}-based treatment unbiased: {bias:+.4f} ({bias / se:+.1f} MC s.e.)", abs(bias / se) < 3)
    # Classic two-point Peelle case: 1.5 and 1.0, 10% independent, 20% common.
    y = np.array([1.5, 1.0])
    cov = np.diag((0.1 * y) ** 2) + 0.2 ** 2 * np.outer(y, y)
    check(f"classic Peelle: data-based GLS {gls_constant(y, cov):.3f} lies below both points",
          gls_constant(y, cov) < 1.0)


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
    for k, v in run().items():
        print(f"{k:>12s}: mean {v.mean():.4f}  sd {v.std(ddof=1):.4f}")
