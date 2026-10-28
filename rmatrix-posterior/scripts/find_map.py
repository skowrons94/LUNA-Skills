#!/usr/bin/env python3
"""Maximum a posteriori point and its exact Hessian: the reference every sampler whitens with.

Damped Newton on -log p, Hessian from central differences of the analytic gradient
(2n gradients; ~10 s for 202 parameters), eigenvalues reflected and floored so every
step is a descent step, backtracking through model failures.  Starts from the best fit
of the .azr/.sav.  Bootstrap metric: Gauss-Newton J^T J at the best fit.

    python3 find_map.py --azr fit.azr --sav output/param.sav --cwd . --out runs/nominal \
        [--bg-energy 25] [--poles path/to/poles.py]
Writes <out>/map.npz (x, H = Hessian of objective/2 in x, x_best, names, objective parts)
and <out>/map.txt.  A negative eigenvalue at the end means the MAP is not a maximum: a
ridge the data and priors do not close (see references/validation.md).
"""
import argparse
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "8")
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from target import add_args, posterior_from_args                      # noqa: E402

ap = add_args(argparse.ArgumentParser(description=__doc__.split("\n")[0]))
ap.add_argument("--iters", type=int, default=40)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
log = open(os.path.join(a.out, "map.txt"), "w")


def say(*s):
    print(*s, flush=True)
    print(*s, file=log, flush=True)


post = posterior_from_args(a, reference=False)
n = post.n
say(f"{n} free parameters; prior rows: " + ", ".join(
    f"{k} {np.sum(post.prior_kind == k)}" for k in np.unique(post.prior_kind)))
say(f"transformability prior: {'on (' + a.poles + ')' if post.phys else 'OFF (no --poles)'}")
big = post.large_theta()
if big:
    names = post.labels()
    say(f"WARNING: {len(big)} widths have |theta| > 3 under the unit prior; background poles? "
        "declare them with --bg-energy: " + "; ".join(names[i] for i in big[:8]))
say("objective parts at the best fit: " + ", ".join(f"{k} {v:.3f}" for k, v in post.parts(post.x_hat).items()))
if post.phys:
    rng = np.random.default_rng(0)
    x = post.x_hat * (1 + 0.05 * rng.standard_normal(n))
    u = rng.standard_normal(n)
    _, G = post.phys(x)
    h = 1e-6
    fd = (post.phys(x + h * u, False)[0] - post.phys(x - h * u, False)[0]) / (2 * h)
    say(f"transformability gradient check: analytic {G @ u:+.6e}  fd {fd:+.6e}")

z = np.zeros(n)
lp, g = post.logp_grad(z)
if not np.isfinite(lp):
    raise SystemExit("the model fails at the best fit")
t0 = time.time()
for it in range(a.iters):
    H = post.hessian_z(z)
    lam, V = np.linalg.eigh(H)
    lam_mod = np.maximum(np.abs(lam), 1e-6 * np.abs(lam).max())
    step = V @ ((V.T @ g) / lam_mod)                    # Newton on -log p
    for s in (1.0, 0.5, 0.25, 0.1, 0.03, 0.01):
        lpn, gn = post.logp_grad(z + s * step)
        if np.isfinite(lpn) and lpn > lp:
            break
    else:
        say(f"iteration {it}: no ascent along the Newton direction; stopping")
        break
    dlp = lpn - lp
    z, lp, g = z + s * step, lpn, gn
    say(f"iteration {it}: objective {-2 * lp * post.T:.4f} (step {s}, gain {2 * dlp * post.T:.4f}), "
        f"|grad| {np.linalg.norm(g):.2e}, Hessian eig min {lam.min():.3g} max {lam.max():.3g}  "
        f"[{time.time() - t0:.0f} s]")
    if dlp < 1e-5 and np.linalg.norm(g) < 1e-2:
        break

x = post.x_of(z)
Hz = post.hessian_z(z)
Hx = post.T * post.Linv.T @ Hz @ post.Linv             # Hessian of objective/2 in x (T-independent)
lam = np.linalg.eigvalsh(Hz)
parts = post.parts(x)
say("objective parts at the MAP: " + ", ".join(f"{k} {v:.3f}" for k, v in parts.items()))
say(f"Hessian at the MAP (bootstrap-whitened units): eig min {lam.min():.4g} max {lam.max():.4g}, "
    f"{np.sum(lam <= 0)} non-positive")
lx = np.linalg.eigvalsh(0.5 * (Hx + Hx.T))
say(f"cond(H) in x = {lx.max() / max(lx.min(), 1e-300):.3g}")
names = post.labels()
dx = x - post.x_hat
sig = np.sqrt(np.clip(np.diag(np.linalg.pinv(Hx)), 0, None))
order = np.argsort(-np.abs(dx / np.where(sig > 0, sig, np.inf)))[:10]
say("largest moves best fit -> MAP (in MAP sigma): " + "; ".join(
    f"{names[i]} {dx[i] / sig[i]:+.2f}" for i in order))
np.savez(os.path.join(a.out, "map.npz"), x=x, H=Hx, x_best=post.x_hat, names=np.array(names),
         **{f"part_{k}": v for k, v in parts.items()})
