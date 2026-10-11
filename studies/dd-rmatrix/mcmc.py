"""Bayesian posterior of the nominal evaluation (emcee) -> rate samples.

log p(z) = -chi2(z)/2  (data with the nominal inflated errors + Gaussian
normalisation priors), flat in the reduced-width amplitudes, norms in [0.3, 3].
Started in a small ball around the nominal minimum (Laplace covariance).
Writes runs/mcmc/chain.npy, runs/mcmc/rates.npz.

usage: python3 mcmc.py [nsteps] [run_dir]
"""
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import emcee
import numpy as np

import fitter
import rates

nsteps = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
src = sys.argv[2] if len(sys.argv) > 2 else "runs/var_nominal"
res = json.load(open(f"{src}/result.json"))
f = fitter.DDFit(src, res["opts"])
z0 = np.load(f"{src}/best.npy")
nx = len(f.x0)
ndim = len(z0)


# weak physical prior on the reduced-width amplitudes: |gamma| ~ 20 x Wigner limit
WL = np.ones(nx)
for p in f.m.parameters:
    if p.kind == "width" and not p.fixed and p.free_index is not None and p.wigner_limit:
        WL[p.free_index] = 20.0 * np.sqrt(p.wigner_limit)


def logp(z):
    if np.any(z[nx:] < 0.3) or np.any(z[nx:] > 3.0):
        return -np.inf
    try:
        R = f.residuals(z)
    except Exception:
        return -np.inf
    v = -0.5 * float(R @ R) - 0.5 * float(np.sum((z[:nx] / WL)**2))
    return v if np.isfinite(v) else -np.inf


cov = np.load(f"{src}/cov.npy")
rng = np.random.default_rng(7)
nw = 2 * ndim + 2
w, U = np.linalg.eigh(0.5 * (cov + cov.T))
w = np.clip(w, 0, None)
p0 = z0 * (1 + 1e-3 * rng.normal(size=(nw, ndim)))      # tight ball; DE moves spread it
moves = [(emcee.moves.DEMove(), 0.8), (emcee.moves.DESnookerMove(), 0.2)]
os.makedirs("runs/mcmc", exist_ok=True)
t = time.time()
sampler = emcee.EnsembleSampler(nw, ndim, logp, moves=moves)
sampler.run_mcmc(p0, nsteps, progress=False)
chain = sampler.get_chain()
lp = sampler.get_log_prob()
np.save("runs/mcmc/chain.npy", chain)
np.save("runs/mcmc/logp.npy", lp)
try:
    tau = sampler.get_autocorr_time(tol=0)
except Exception:
    tau = np.full(ndim, np.nan)
burn = nsteps // 2
flat = chain[burn:].reshape(-1, ndim)
flat_lp = lp[burn:].reshape(-1)
print(f"{nsteps} steps x {nw} walkers in {time.time() - t:.0f} s; acceptance "
      f"{np.mean(sampler.acceptance_fraction):.2f}; max tau {np.nanmax(tau):.0f}; "
      f"best chi2 {-2 * lp.max():.1f} (fit {-2 * logp(z0):.1f})", flush=True)

# rates for a thinned posterior sample
idx = rng.choice(len(flat), size=min(600, len(flat)), replace=False)
grid = np.array(res["grid"])
f.m.extrap_mode()
R_dp, R_dn, norms = [], [], []
for i in idx:
    x = flat[i, :nx]
    c = f.m.calculate_rwa(x)
    en = f.m.calculate_energies(x)
    out = []
    for ks in ((0, 1), (2, 3)):
        Ek = np.concatenate([np.asarray(en[k], float) for k in ks]) * 1e3
        ck = np.concatenate([np.asarray(c[k], float) for k in ks])
        o = np.argsort(Ek)
        out.append(np.exp(np.interp(grid, Ek[o], np.log(np.maximum(ck[o], 1e-300)))))
    R_dp.append(rates.rate(grid, out[0], rates.T9_GRID))
    R_dn.append(rates.rate(grid, out[1], rates.T9_GRID))
    norms.append(list(f.norms(flat[i, nx:]).values()))
np.savez("runs/mcmc/rates.npz", T9=rates.T9_GRID, dp=np.array(R_dp), dn=np.array(R_dn),
         norms=np.array(norms), norm_names=np.array(list(f.norms(flat[0, nx:]).keys())),
         tau=tau, chi2=-2 * flat_lp[idx])
for k, A in (("dp", np.array(R_dp)), ("dn", np.array(R_dn))):
    q = np.percentile(A, [16, 50, 84], axis=0)
    print(k, " ".join(f"T9={t}: {q[1][i]:.4g} (+{100 * (q[2][i] / q[1][i] - 1):.2f}/"
                      f"-{100 * (1 - q[0][i] / q[1][i]):.2f} %)"
                      for i, t in enumerate(rates.T9_GRID) if t in (0.1, 0.5, 1.0)))
f.close()
