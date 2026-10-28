#!/usr/bin/env python3
"""Validate the whitened target, then test the Laplace approximation.

1. objective parts at the best fit: data + AZURE2 priors must equal pyazr ``objective``;
   z-space gradient against central finite differences on random directions;
   cost of one log p + gradient at fresh points (a repeated point is served from cache).
2. 1-D scans along every whitened axis: exact log p minus the Gaussian -t^2/2 at
   t = -2, -1, +1, +2.  Large values name the directions the metric gets wrong.
3. Importance sampling from a Student-t (nu = 7) on the same metric, Pareto-smoothed:
   khat < 0.7 means the reweighted Laplace approximation is the posterior; otherwise
   (or khat = nan) a sampler is needed.

    python3 laplace_check.py --azr fit.azr --sav param.sav --cwd . --out runs/nominal [--gauss-newton]
Writes <out>/laplace_<map|gn>.txt, axis_scan_<tag>.npy and laplace_<tag>.npz.
"""
import argparse
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "8")
import numpy as np
from scipy.special import gammaln

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from target import add_args, posterior_from_args          # noqa: E402

ap = add_args(argparse.ArgumentParser(description=__doc__.split("\n")[0]))
ap.add_argument("--n", type=int, default=2000)
ap.add_argument("--nu", type=float, default=7.0)
ap.add_argument("--gauss-newton", action="store_true",
                help="whiten with J^T J at the best fit instead of the exact Hessian at the MAP")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
tag = "gn" if a.gauss_newton else "map"
log = open(os.path.join(a.out, f"laplace_{tag}.txt"), "w")


def say(*s):
    print(*s, flush=True)
    print(*s, file=log, flush=True)


post = posterior_from_args(a, reference=not a.gauss_newton)
lam = post.hessian_eigenvalues
say(f"{post.n} free parameters; whitening matrix cond = {lam.max() / max(lam.min(), 1e-300):.2e} "
    f"({'J^T J at the best fit' if a.gauss_newton else 'exact Hessian at the MAP'})")
p = post.parts(post.x_hat)
ours, theirs = p["data"] + p.get("azure2", 0.0), post.m.objective(post.x_hat)
say(f"best fit: data + AZURE2 priors {ours:.4f}, pyazr objective {theirs:.4f} "
    f"({'agree' if abs(ours - theirs) < 1e-6 * max(1, abs(theirs)) else 'DISAGREE: fix the prior rows'})")
say(f"objective at the reference point: {post.objective(post.x_ref):.4f}")

rng = np.random.default_rng(1)
lp0, g0 = post.logp_grad(np.zeros(post.n))
say(f"|grad log p| at the reference point (z units): {np.linalg.norm(g0):.3e}")
for k in range(4):
    z = 0.5 * rng.standard_normal(post.n)
    u = rng.standard_normal(post.n); u /= np.linalg.norm(u)
    _, g = post.logp_grad(z)
    h = 1e-3
    fd = (post.logp(z + h * u) - post.logp(z - h * u)) / (2 * h)
    say(f"gradient check {k}: analytic {g @ u:+.6e}  finite-difference {fd:+.6e}  "
        f"rel {abs(g @ u - fd) / max(abs(fd), 1e-12):.1e}")
Zt = 0.3 * rng.standard_normal((5, post.n))
t = time.time()
for z in Zt:
    post.logp_grad(z)
tg = (time.time() - t) / len(Zt)
t = time.time()
for z in Zt + 0.01:
    post.logp(z)
tl = (time.time() - t) / len(Zt)
say(f"cost at fresh points, {os.environ.get('OMP_NUM_THREADS')} threads: log p {tl * 1e3:.0f} ms, "
    f"log p + gradient {tg * 1e3:.0f} ms (use one-thread numbers in compare.py)")

names = post.labels()
ts = np.array([-2.0, -1.0, 1.0, 2.0])
dev = np.zeros((post.n, 4))
for k in range(post.n):
    e = np.zeros(post.n); e[k] = 1.0
    dev[k] = [post.logp(t_ * e) - (lp0 - 0.5 * t_ * t_) for t_ in ts]
absdev = np.nan_to_num(np.abs(dev), nan=1e9, posinf=1e9)
say(f"axis scan: max |log p - Gaussian| at t = +-1: worst {absdev[:, 1:3].max():.2f}, "
    f"{np.sum(absdev[:, 1:3].max(1) < 0.25)} of {post.n} axes below 0.25")
worst = np.argsort(-absdev.max(1))[:12]
say("axes least like the Laplace approximation (log p - Gaussian at t = -2,-1,+1,+2; dominant parameters):")
for k in worst:
    col = post.L[:, k] / np.sqrt(np.diag(post.L @ post.L.T))
    top = np.argsort(-np.abs(col))[:3]
    say(f"  axis {k:3d} (eigenvalue {lam[k]:.2e}): " + " ".join(f"{v:+9.2f}" for v in dev[k])
        + "   " + ", ".join(f"{names[j]} ({col[j]:+.2f})" for j in top))
np.save(os.path.join(a.out, f"axis_scan_{tag}.npy"), dev)

n, nu = post.n, a.nu


def logq(z):
    return (gammaln((nu + n) / 2) - gammaln(nu / 2) - 0.5 * n * np.log(nu * np.pi)
            - 0.5 * (nu + n) * np.log1p(z @ z / nu))


Z = rng.standard_normal((a.n, n)) / np.sqrt(rng.chisquare(nu, a.n) / nu)[:, None]
lw = np.empty(a.n)
lpv = np.empty(a.n)
t = time.time()
for i, z in enumerate(Z):
    lpv[i] = post.logp(z)
    lw[i] = lpv[i] - logq(z)
    if (i + 1) % 500 == 0:
        say(f"  {i + 1}/{a.n} draws, {(time.time() - t) / (i + 1) * 1e3:.0f} ms each")
ok = np.isfinite(lw)
w = np.exp(lw[ok] - lw[ok].max())
w /= w.sum()
khat = np.nan
try:
    from arviz_stats.base.array import array_stats
    _, khat = array_stats.psislw(lw[ok] - lw[ok].max())
    khat = float(khat)
except Exception as e:                                  # noqa: BLE001
    say(f"(PSIS unavailable: {e})")
say(f"model failures: {np.sum(~ok)} of {a.n}")
say(f"importance-sampling ESS (Kish) = {1 / np.sum(w ** 2):.1f} of {ok.sum()}")
verdict = ("the reweighted Laplace approximation is usable" if np.isfinite(khat) and khat < 0.7
           else "the Laplace approximation FAILS as an importance proposal: sample")
say(f"Pareto khat = {khat:.2f} ({verdict}; nan counts as failure)")
dlog = lpv[ok] - (lp0 - 0.5 * np.sum(Z[ok] ** 2, 1))
say(f"log p - Laplace log p over the draws: median {np.median(dlog):+.1f}, "
    f"16-84% {np.percentile(dlog, 16):+.1f} .. {np.percentile(dlog, 84):+.1f}")
np.savez(os.path.join(a.out, f"laplace_{tag}.npz"), x=np.array([post.x_of(z) for z in Z[ok]]),
         lw=lw[ok], khat=khat, dlog=dlog)
