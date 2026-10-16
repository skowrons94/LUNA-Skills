#!/usr/bin/env python3
"""Peelle's pertinent puzzle on synthetic data, with an energy-dependent model.

Two datasets of unequal size and precision measure y_i = mu g(E_i) (true
mu = 1; g varies by a factor 2-3 across the points). Each point has an
independent absolute error sigma_j; each dataset has its own multiplicative
normalization error f, drawn as k = 1 + f z (mean 1) and applied to the model.
Four treatments of the normalization:

  data          covariance f^2 y_i y_j built from the measured values (biased low)
  model         covariance f^2 mu^2 g_i g_j from the current estimate, iterated;
                the GLS weights between datasets depend on mu, so the iteration matters
  factor_ln     joint MAP with an explicit factor k per dataset on the model,
                lognormal prior ln k / f
  factor_gauss  the same with a Gaussian prior (k - 1) / f

Both joint-MAP factor fits are biased at O(f^2): the Gaussian prior high (about
f^2 (1 - 1/N_sets) for comparably precise sets), the lognormal prior less and,
for mean-1 factors, low. BIASES below lists the values for this design from
many trials; the sign and size of the O(f^2) terms change if the factor is
defined with median 1 instead of mean 1, so state the convention.

    python peelle_demo.py [--trials N] [--seed S]   # prints the biases
    python peelle_demo.py --selftest [--seed S]
"""
import argparse
import sys

import numpy as np

F = 0.20                                                  # normalization uncertainty of each dataset
G = (np.linspace(0.6, 1.8, 8), np.linspace(1.0, 2.4, 4))  # model shape g(E_i) per dataset
SIGMA = (0.03, 0.15)                                      # independent absolute error per dataset
SETS = np.concatenate([np.full(len(g), j) for j, g in enumerate(G)])
GVEC = np.concatenate(G)
SVEC = np.array(SIGMA)[SETS]
IN_SET = SETS[:, None] == SETS[None, :]
NSETS = len(G)

# Mean bias of each treatment for this design: 2 x 10^5 trials (seeds 0-9), MC s.e. about 0.03%.
BIASES = {"data": -0.195, "model": 0.000, "factor_ln": -0.009, "factor_gauss": +0.021}


def simulate(rng, n_trials, mu=1.0):
    """Measured values, shape (trials, points)."""
    k = 1.0 + F * rng.normal(size=(n_trials, NSETS))
    return k[:, SETS] * mu * GVEC + SVEC * rng.normal(size=(n_trials, len(GVEC)))


def gls(y, cov):
    """GLS estimate of mu for the model mu g, vectorised over trials."""
    rhs = np.stack([y, np.broadcast_to(GVEC, y.shape)], axis=-1)
    sol = np.linalg.solve(cov, rhs)
    return np.einsum("i,ti->t", GVEC, sol[..., 0]) / np.einsum("i,ti->t", GVEC, sol[..., 1])


def norm_cov(scale):
    """sigma^2 on the diagonal plus f^2 scale_i scale_j within each dataset; scale has shape (trials, points)."""
    return np.diag(SVEC ** 2) + F ** 2 * scale[:, :, None] * scale[:, None, :] * IN_SET


def fit_data(y):
    return gls(y, norm_cov(y))


def fit_model(y, n_iter=30):
    mu = np.mean(y / GVEC, axis=1)
    for _ in range(n_iter):
        mu = gls(y, norm_cov(mu[:, None] * GVEC))
    return mu


def fit_factor(y, prior="lognormal", n_iter=50):
    """Joint MAP of (mu, ln k_j) by vectorised Gauss-Newton."""
    t, n = y.shape
    p = np.zeros((t, 1 + NSETS))
    p[:, 0] = np.mean(y / GVEC, axis=1)
    for _ in range(n_iter):
        mu, lk = p[:, :1], p[:, 1:]
        k = np.exp(lk)
        kp = k[:, SETS]
        pen = lk / F if prior == "lognormal" else (k - 1.0) / F
        r = np.concatenate([(y - kp * mu * GVEC) / SVEC, pen], axis=1)
        jac = np.zeros((t, n + NSETS, 1 + NSETS))
        jac[:, :n, 0] = -kp * GVEC / SVEC
        for j in range(NSETS):
            jac[:, :n, 1 + j] = -(kp * mu * GVEC / SVEC) * (SETS == j)
            jac[:, n + j, 1 + j] = 1.0 / F if prior == "lognormal" else k[:, j] / F
        jt = np.transpose(jac, (0, 2, 1))
        step = np.linalg.solve(jt @ jac, -(jt @ r[..., None]))[..., 0]
        p += step
        if np.max(np.abs(step)) < 1e-13:
            break
    return p[:, 0]


def fit_factor_reference(y, prior="lognormal"):
    """Unvectorised scipy fit of one trial, used to check fit_factor."""
    from scipy.optimize import least_squares

    def resid(p):
        mu, lk = p[0], p[1:]
        k = np.exp(lk)
        pen = lk / F if prior == "lognormal" else (k - 1.0) / F
        return np.concatenate([(y - k[SETS] * mu * GVEC) / SVEC, pen])

    start = np.r_[np.mean(y / GVEC), np.zeros(NSETS)]
    return float(least_squares(resid, start, xtol=1e-14, ftol=1e-14, gtol=1e-14).x[0])


def run(n_trials=20000, seed=5):
    y = simulate(np.random.default_rng(seed), n_trials)
    return {"data": fit_data(y), "model": fit_model(y),
            "factor_ln": fit_factor(y, "lognormal"), "factor_gauss": fit_factor(y, "gaussian")}


def bias_table(est):
    return {k: (float(v.mean() - 1.0), float(v.std(ddof=1) / np.sqrt(len(v)))) for k, v in est.items()}


def selftest(check, seed=5):
    y = simulate(np.random.default_rng(seed + 1000), 20)
    agree = max(np.abs(fit_factor(y, pr) - [fit_factor_reference(row, pr) for row in y]).max()
                for pr in ("lognormal", "gaussian"))
    check(f"vectorised factor fit matches scipy least_squares (max diff {agree:.1e})", agree < 1e-6)
    moved = np.abs(fit_model(y) - fit_model(y, n_iter=1)).max()
    check(f"model-based iteration matters (estimate moves by up to {moved:.1e} after the first step)",
          moved > 1e-4)

    b = bias_table(run(n_trials=20000, seed=seed))
    (bd, sd), (bm, sm), (bl, sl), (bg, sg) = (b[k] for k in ("data", "model", "factor_ln", "factor_gauss"))
    check(f"data-based covariance biased low: {bd:+.4f} ({bd / sd:+.0f} MC s.e.)", bd / sd < -10)
    check(f"model-based covariance bias {bm:+.4f} ({bm / sm:+.1f} MC s.e.) small: |bias| < 4 s.e. + f^2/20",
          abs(bm) < 4 * sm + F ** 2 / 20)
    check(f"Gaussian-prior factor MAP biased high at O(f^2): {bg:+.4f} ({bg / sg:+.0f} MC s.e.)",
          bg / sg > 5 and 0.2 * F ** 2 < bg < 1.5 * F ** 2)
    check(f"lognormal-prior factor MAP bias {bl:+.4f} ({bl / sl:+.1f} MC s.e.) below Gaussian and < f^2/2",
          abs(bl) < abs(bg) and abs(bl) < F ** 2 / 2)
    # Classic two-point Peelle case: 1.5 and 1.0, 10% independent, 20% common.
    y2 = np.array([1.5, 1.0])
    ci = np.linalg.inv(np.diag((0.1 * y2) ** 2) + 0.2 ** 2 * np.outer(y2, y2))
    m2 = float(ci.sum(axis=0) @ y2 / ci.sum())
    check(f"classic Peelle: data-based GLS {m2:.3f} lies below both points", m2 < 1.0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--trials", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=5)
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
    for k, (bias, se) in bias_table(run(a.trials, a.seed)).items():
        print(f"{k:>12s}: bias {100 * bias:+.2f}% +- {100 * se:.2f}% (MC s.e.)")
