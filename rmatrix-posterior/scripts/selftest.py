#!/usr/bin/env python3
"""Self-test of the sampler stack without AZURE2 (pure numpy targets, fixed seeds).

  1. whitened by its Hessian, NUTS (chain.py, full warm-up) recovers the mean and covariance
     of a correlated Gaussian with cond(C) = 1e6 in d = 20, with no divergences
  2. the same target with the identity metric: ESS per gradient is far lower (the
     conditioning lesson: a coordinate problem, fixed by whitening, not by a sampler)
  3. checkpoint/resume is bit-identical: a chain stopped twice (once inside a warm-up
     window) and a kill between chunk and state write give the same draws as one run
  4. the soft transformability prior: analytic gradient = finite differences, and the
     softplus tends to the hinge max(0, u) as its width -> 0
  5. a model failure (log p = -inf) is a divergence, not a crash; no draw crosses it
  6. importance sampling from a near-Gaussian proposal collapses in high dimension although
     every axis deviates by < 0.1 in log p at 1 sigma (the 202-parameter lesson)
  7. a dense metric estimated from warm-up windows shorter than the dimension is a trap
     (rank-deficient, collapsed eigenvalues, deep trees); metric="auto" falls back to diag
Run: python3 selftest.py   -> PASS/FAIL lines; exit code 1 on any failure (~1 min).
"""
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from nuts import NUTS, DualAveraging                     # noqa: E402
from chain import run_chain, load_draws                  # noqa: E402
from target import whitening, softplus, SoftTransformability   # noqa: E402

ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}", flush=True)


def ess(x):
    """Effective sample size of x (chains, draws): Geyer's initial monotone sequence."""
    x = np.atleast_2d(np.asarray(x, float))
    m, n = x.shape
    xc = x - x.mean()
    f = np.fft.rfft(xc, 2 * n, axis=1)
    ac = np.fft.irfft(f * np.conj(f), axis=1)[:, :n].mean(0) / n
    rho = ac / ac[0]
    s, prev = 0.0, np.inf
    for k in range(0, n - 1, 2):
        pair = rho[k] + rho[k + 1]
        if pair < 0:
            break
        pair = min(pair, prev)
        s += pair
        prev = pair
    tau = max(2 * s - 1, 1e-3)
    return m * n / tau


def gaussian(P):
    def f(x):
        g = -P @ x
        return 0.5 * float(x @ g), g
    return f


log = lambda s: None
tmp = Path(tempfile.mkdtemp(prefix="rmatrix-posterior-selftest-"))
t_start = time.time()
try:
    # ---------------------------------------------------------------- 1 whitened
    d = 20
    rng = np.random.default_rng(1)
    Q, _ = np.linalg.qr(rng.standard_normal((d, d)))
    lam = np.logspace(0, -6, d)                           # covariance eigenvalues 1 .. 1e-6
    C = (Q * lam) @ Q.T
    P = np.linalg.inv(C)
    mu = rng.standard_normal(d) * np.sqrt(lam) @ Q.T      # a non-zero mean
    fx = gaussian(P)
    f_shift = lambda x: fx(x - mu)
    H = P                                                  # Hessian of objective/2 = -log p
    L, Linv, _ = whitening(H)
    x_ref = mu                                             # reference = the mode
    fz = lambda z: (lambda v: (v[0], L.T @ v[1]))(f_shift(x_ref + L @ z))
    X, grads, divs = [], 0, 0
    for c in range(4):
        run_chain(fz, d, str(tmp / f"w{c}"), warmup=150, draws=500, seed=11, chain=c, log=log,
                  to_x=lambda z: x_ref + L @ z)
        D = load_draws(str(tmp / f"w{c}"))
        X.append(D["x"][~D["warmup"]])
        grads += int(D["ngrad"][~D["warmup"]].sum())
        divs += int(D["divergent"][~D["warmup"]].sum())
    X = np.array(X)                                        # (4, 500, d)
    Y = np.einsum("ij,cnj->cni", Q.T / np.sqrt(lam)[:, None], X - mu)   # exact whitening: N(0, I)
    pm = max(abs(Y[..., i].mean()) / (Y[..., i].std() / np.sqrt(ess(Y[..., i]))) for i in range(d))
    pv = max(abs((Y[..., i] ** 2).mean() - 1) / ((Y[..., i] ** 2).std() / np.sqrt(ess(Y[..., i] ** 2)))
             for i in range(d))
    epg_w = min(ess(Y[..., i]) for i in range(d)) / grads
    check("1 whitened NUTS recovers mean and covariance, d=20, cond 1e6",
          pm < 4.5 and pv < 4.5 and divs == 0,
          f"max|pull| mean {pm:.2f}, variance {pv:.2f} (limit 4.5); divergences {divs}; "
          f"ESS/gradient {epg_w:.3f}")

    # ---------------------------------------------------------------- 2 identity metric
    s = NUTS(f_shift, d, max_depth=10)
    s._set_metric(np.eye(d))
    r2 = np.random.default_rng(2)
    z = mu + Q @ (np.sqrt(lam) * r2.standard_normal(d))
    lp, g = f_shift(z)
    eps, da = 1e-3, DualAveraging(1e-3, 0.85)
    for _ in range(100):
        z, lp, g, st = s.transition(z, lp, g, eps, r2)
        eps = da.update(st["accept"])
    eps = da.final()
    Xi, gi, maxd = [], 0, 0
    for _ in range(200):
        z, lp, g, st = s.transition(z, lp, g, eps, r2)
        Xi.append(z.copy()); gi += st["ngrad"]; maxd += st["depth"] == 10
    Yi = (np.array(Xi) - mu) @ (Q / np.sqrt(lam))
    epg_i = min(ess(Yi[:, i]) for i in range(d)) / gi
    check("2 identity metric is far slower (ESS per gradient)", epg_w > 20 * epg_i,
          f"identity: eps {eps:.1e}, ESS/gradient {epg_i:.1e}, tree depth 10 in {maxd / 2:.0f}% | "
          f"whitened/identity = {epg_w / max(epg_i, 1e-300):.0f}x")

    # ---------------------------------------------------------------- 3 resume
    d3 = 6
    Q3, _ = np.linalg.qr(np.random.default_rng(7).standard_normal((d3, d3)))
    C3 = (Q3 * np.logspace(0, -2, d3)) @ Q3.T
    f3 = gaussian(np.linalg.inv(C3))
    kw = dict(warmup=150, draws=70, seed=5, chain=0, every=20, log=log, max_depth=8)
    run_chain(f3, d3, str(tmp / "A"), **kw)
    run_chain(f3, d3, str(tmp / "B"), max_session=87, **kw)        # stops inside the window 75-100
    run_chain(f3, d3, str(tmp / "B"), max_session=33, **kw)        # stops at 120, on a chunk boundary
    shutil.copy(tmp / "B" / "state.pkl", tmp / "state_120.pkl")
    run_chain(f3, d3, str(tmp / "B"), max_session=20, **kw)        # writes chunk 120-140 and state
    shutil.copy(tmp / "state_120.pkl", tmp / "B" / "state.pkl")    # = killed after the chunk, before the state
    run_chain(f3, d3, str(tmp / "B"), **kw)
    A, B = load_draws(str(tmp / "A")), load_draws(str(tmp / "B"))
    same = A.keys() == B.keys() and all(np.array_equal(A[k], B[k]) for k in A)
    check("3 checkpoint/resume bit-identical (3 stops, one inside a warm-up window, one kill)",
          same and len(A["logp"]) == 220, f"{len(A['logp'])} vs {len(B['logp'])} iterations")

    # ---------------------------------------------------------------- 4 soft prior
    r4 = np.random.default_rng(4)
    n4 = 3
    pairs = []
    for a in range(n4):
        for b in range(n4):
            if a != b:
                for ch in range(2):
                    W = 0.3 + 0.1 * (a + b) + 0.05 * ch          # symmetric in (a, b)
                    pairs.append((a, b, 2 * a + ch, 2 * b + ch, W))
    levels = [(5.0 + 10 * l, [(2 * l + ch, 40.0 + 30 * ch) for ch in range(2)]) for l in range(n4)]
    prior = SoftTransformability([(n4, pairs, levels)], tau=0.7, etarget=300.0, soft=0.05)
    x4 = 1.5 * r4.standard_normal(2 * n4)
    v, G = prior(x4)
    worst = 0.0
    for _ in range(5):
        u = r4.standard_normal(x4.size)
        h = 1e-6
        fd = (prior(x4 + h * u, False)[0] - prior(x4 - h * u, False)[0]) / (2 * h)
        worst = max(worst, abs(G @ u - fd) / max(abs(fd), 1e-9))
    uu = np.linspace(-1, 1, 41)
    hinge = np.max(np.abs(softplus(uu, 1e-4)[0] - np.maximum(0, uu)))
    check("4 soft transformability prior: gradient = finite differences; softplus -> hinge",
          v > 0 and worst < 1e-5 and hinge < 1e-4,
          f"penalty {v:.3g}, worst relative gradient error {worst:.1e}, |softplus - hinge| {hinge:.1e}")

    # ---------------------------------------------------------------- 5 failure = divergence
    def f5(x):
        if x[0] > 0.5:
            return -np.inf, np.full(5, np.nan)
        return -0.5 * float(x @ x), -x
    run_chain(f5, 5, str(tmp / "wall"), warmup=100, draws=400, seed=3, init=np.full(5, -0.5), log=log)
    D5 = load_draws(str(tmp / "wall"))
    nd = int(D5["divergent"].sum())
    check("5 model failure -> divergence, no crash, no draw beyond it",
          nd > 0 and D5["z"][:, 0].max() <= 0.5 and np.isfinite(D5["logp"]).all(),
          f"divergences {nd}/500, max x0 {D5['z'][:, 0].max():.3f}")

    # ---------------------------------------------------------------- 6 Laplace IS
    s6, N6 = 1.1, 4000
    r6 = np.random.default_rng(6)
    dev1 = 0.5 * (1 - 1 / s6 ** 2)                          # |log p - Gaussian| at 1 sigma, per axis
    frac = {}
    for d6 in (5, 202):
        Z = r6.standard_normal((N6, d6))
        lw = -0.5 * np.sum(Z ** 2, 1) / s6 ** 2 + 0.5 * np.sum(Z ** 2, 1)
        w = np.exp(lw - lw.max())
        frac[d6] = (w.sum() ** 2 / np.sum(w ** 2)) / N6
    check("6 importance sampling collapses in high dimension", frac[5] > 0.5 and frac[202] < 0.05,
          f"per-axis deviation at 1 sigma {dev1:.3f}; Kish ESS/N: d=5 {frac[5]:.2f}, d=202 {frac[202]:.4f}")

    # ---------------------------------------------------------------- 7 dense-window trap
    d7 = 60
    s7 = np.exp(0.3 * np.random.default_rng(8).standard_normal(d7))      # whitened, imperfectly
    f7 = lambda z: (-0.5 * float((z / s7) @ (z / s7)), -z / s7 ** 2)
    gpd = {}
    for m, sh in (("dense", 1e-3), ("dense", 1.0), ("auto", 1.0)):
        run_chain(f7, d7, str(tmp / f"m_{m}_{sh}"), warmup=200, draws=100, seed=1, metric=m,
                  shrink_to=sh, log=log)
        D7 = load_draws(str(tmp / f"m_{m}_{sh}"))
        gpd[(m, sh)] = D7["ngrad"][~D7["warmup"]].mean()
    trap, mild, auto = gpd[("dense", 1e-3)], gpd[("dense", 1.0)], gpd[("auto", 1.0)]
    check("7 dense metric from windows of 25-50 draws in d=60: a trap with Stan's 1e-3 shrinkage, "
          "milder shrunk to 1, auto (diag) best",
          trap > 10 * auto and mild < trap and auto <= mild,
          f"gradients per draw: dense/1e-3 {trap:.0f}, dense/1 {mild:.0f}, auto {auto:.0f}")
    # ---------------------------------------------------------------- 8 sign fold
    from fold import fold_level_signs
    r8 = np.random.default_rng(8)
    groups8 = [[0, 1, 2], [3, 4]]
    xref8 = np.array([-4.0, 1.0, 2.5, 0.3, -0.9])
    A = xref8 + 0.1 * r8.standard_normal((2, 300, 5))     # two chains in the reference copy
    B = A.copy(); B[1][:, [0, 1, 2]] *= -1                # chain 1 in the mirror copy of level 0
    F, nf = fold_level_signs(B, groups8, xref8)
    check("8 exact level-sign symmetry: folding maps the mirror chain back",
          np.allclose(F, A) and nf == 300,
          f"flips {nf} (expected 300), max |folded - reference| {np.abs(F - A).max():.1e}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"({time.time() - t_start:.0f} s)")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
