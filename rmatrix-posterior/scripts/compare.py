#!/usr/bin/env python3
"""NUTS against emcee on the same posterior: effective samples per core-hour.

    python3 compare.py --out runs/nominal --t-grad 0.091 --t-logp 0.030 [--key '@7.65' --key 'E$']

Reads <out>/nuts/chain_*/draws_*.npz and <out>/emcee/chain.h5 (either may still be
running: whatever is on disk is used); writes <out>/compare.json and compare.txt.

NUTS: post-warm-up draws of every chain, rank-normalized split R-hat and bulk/tail ESS
(Vehtari et al. 2021, arviz-stats).  emcee: integrated autocorrelation time tau per
quantity (emcee's walker-averaged estimator) after discarding --burn-tau x max(tau);
ESS = walkers x kept / tau, flagged NOT reliable when kept < 50 tau (then the ESS is an
upper bound and the true NUTS/emcee ratio is larger).  Walkers of one ensemble are not
independent chains, so emcee gets no R-hat here.
Cost: core-seconds = gradient calls x t_grad (NUTS), log p calls x t_logp (emcee), with
per-call costs measured on ONE thread at fresh points (laplace_check.py prints them).
"""
import argparse
import glob
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from target import whitening                                           # noqa: E402
from chain import load_draws                                           # noqa: E402

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--out", required=True)
ap.add_argument("--t-grad", type=float, required=True, help="s per log p + gradient, one thread")
ap.add_argument("--t-logp", type=float, required=True, help="s per log p, one thread")
ap.add_argument("--burn-tau", type=float, default=5.0)
ap.add_argument("--key", action="append", default=[], help="regex on parameter labels to tabulate")
a = ap.parse_args()
import arviz_stats as azs                                              # noqa: E402

ref = np.load(os.path.join(a.out, "map.npz"))
names = [str(s) for s in ref["names"]]
x_ref, H = ref["x"], ref["H"]
out, lines = {}, []


def say(s=""):
    print(s)
    lines.append(s)


# ---------------------------------------------------------------- NUTS
chains = []
for cdir in sorted(glob.glob(os.path.join(a.out, "nuts", "chain_*"))):
    cat = load_draws(cdir)
    if cat:
        chains.append(cat)
if chains:
    nkeep = min(int(np.sum(~c["warmup"])) for c in chains)
    say(f"NUTS: {len(chains)} chains, {nkeep} post-warm-up draws each (shortest chain)")
    if nkeep >= 20:
        X = np.array([c["x"][~c["warmup"]][:nkeep] for c in chains])          # (chain, draw, n)
        LP = np.array([c["logp"][~c["warmup"]][:nkeep] for c in chains])
        g_samp = sum(int(np.sum(c["ngrad"][~c["warmup"]][:nkeep])) for c in chains)
        g_warm = sum(int(np.sum(c["ngrad"][c["warmup"]])) for c in chains)
        divs = sum(int(np.sum(c["divergent"][~c["warmup"]][:nkeep])) for c in chains)
        depth = np.concatenate([c["depth"][~c["warmup"]][:nkeep] for c in chains])
        eps = [float(c["eps"][~c["warmup"]][0]) for c in chains]
        ess_b = np.asarray(azs.ess(X, method="bulk"), float)
        ess_t = np.asarray(azs.ess(X, method="tail"), float)
        rh = np.asarray(azs.rhat(X), float)
        ess_lp = float(np.asarray(azs.ess(LP[..., None], method="bulk"), float)[0])
        core_h = g_samp * a.t_grad / 3600
        say(f"  step sizes {np.round(eps, 3)}; tree depth counts {np.bincount(depth).tolist()}; "
            f"{g_samp / X.shape[0] / nkeep:.0f} gradients per draw; divergences {divs}")
        say(f"  R-hat max {np.nanmax(rh):.3f}; bulk ESS min {np.nanmin(ess_b):.0f} median {np.nanmedian(ess_b):.0f}; "
            f"tail ESS min {np.nanmin(ess_t):.0f}; ESS(log p) {ess_lp:.0f}")
        say(f"  cost {core_h:.2f} core-h (+ warm-up {g_warm * a.t_grad / 3600:.2f}); "
            f"min bulk ESS per core-h {np.nanmin(ess_b) / core_h:.1f}; ESS(log p) per core-h {ess_lp / core_h:.1f}")
        flat = X.reshape(-1, X.shape[-1])
        out["nuts"] = dict(chains=len(chains), draws=nkeep, rhat_max=float(np.nanmax(rh)),
                           ess_bulk_min=float(np.nanmin(ess_b)), ess_bulk_median=float(np.nanmedian(ess_b)),
                           ess_tail_min=float(np.nanmin(ess_t)), ess_logp=ess_lp, divergences=divs,
                           grads_per_draw=g_samp / X.shape[0] / nkeep, core_hours=core_h,
                           warmup_core_hours=g_warm * a.t_grad / 3600, ess_bulk=ess_b.tolist(),
                           rhat=rh.tolist(), mean=flat.mean(0).tolist(), sd=flat.std(0).tolist())
        worst = np.argsort(ess_b)[:6]
        say("  slowest parameters (bulk ESS): " + "; ".join(f"{names[i]} {ess_b[i]:.0f}" for i in worst))

# ---------------------------------------------------------------- emcee
h5 = os.path.join(a.out, "emcee", "chain.h5")
if os.path.exists(h5):
    import emcee
    be = emcee.backends.HDFBackend(h5, read_only=True)
    nsteps = be.iteration
    if nsteps > 50:
        st = json.load(open(os.path.join(a.out, "emcee", "settings.json")))
        thin, T = st["thin"], st.get("temperature", 1.0)
        L = whitening(H, T)[0]                                   # the L the run used
        Zc, lpc = be.get_chain(), be.get_log_prob()
        nw = Zc.shape[1]
        Xc = x_ref + np.einsum("ij,swj->swi", L, Zc)
        tau_all = emcee.autocorr.integrated_time(Xc, tol=0)
        tau_lp_all = float(emcee.autocorr.integrated_time(lpc[:, :, None], tol=0)[0])
        burn = int(min(nsteps // 2, a.burn_tau * max(np.nanmax(tau_all), tau_lp_all)))
        K = Xc[burn:]
        tau = emcee.autocorr.integrated_time(K, tol=0)
        tau_lp = float(emcee.autocorr.integrated_time(lpc[burn:, :, None], tol=0)[0])
        kept = K.shape[0]
        ess, ess_lp = nw * kept / tau, nw * kept / tau_lp
        core_h = nw * kept * thin * a.t_logp / 3600
        reliable = bool(kept > 50 * np.nanmax(tau))
        say(f"emcee: {nw} walkers, {nsteps} stored steps (every {thin}th), burn-in {burn}, kept {kept}")
        say(f"  tau (stored steps): max {np.nanmax(tau):.0f}, median {np.nanmedian(tau):.0f}, log p {tau_lp:.0f}; "
            f"{'reliable' if reliable else 'NOT reliable (kept < 50 tau): ESS is an upper bound'}")
        say(f"  ESS min {np.nanmin(ess):.0f} median {np.nanmedian(ess):.0f}; ESS(log p) {ess_lp:.0f}; "
            f"cost {core_h:.2f} core-h (+ burn-in {nw * burn * thin * a.t_logp / 3600:.2f}); "
            f"min ESS per core-h {np.nanmin(ess) / core_h:.1f}; ESS(log p) per core-h {ess_lp / core_h:.1f}")
        flat = K.reshape(-1, K.shape[-1])
        out["emcee"] = dict(walkers=nw, steps=nsteps, thin=thin, burn=burn, kept=kept,
                            tau_max=float(np.nanmax(tau)), tau_median=float(np.nanmedian(tau)),
                            tau_logp=tau_lp, reliable=reliable, ess_min=float(np.nanmin(ess)),
                            ess_logp=ess_lp, core_hours=core_h, tau=tau.tolist(),
                            mean=flat.mean(0).tolist(), sd=flat.std(0).tolist())
        worst = np.argsort(-tau)[:6]
        say("  slowest parameters (tau): " + "; ".join(f"{names[i]} {tau[i]:.0f}" for i in worst))

# ---------------------------------------------------------------- side by side
if "nuts" in out and "emcee" in out:
    nu, em = out["nuts"], out["emcee"]
    r_min = (nu["ess_bulk_min"] / nu["core_hours"]) / (em["ess_min"] / em["core_hours"])
    r_lp = (nu["ess_logp"] / nu["core_hours"]) / (em["ess_logp"] / em["core_hours"])
    say(f"NUTS / emcee, ESS per core-hour: slowest parameter x{r_min:.1f}, log p x{r_lp:.1f}"
        + ("" if em["reliable"] else "  (emcee tau not converged: the true ratio is larger)"))
    m1, m2, s1, s2 = (np.array(nu["mean"]), np.array(em["mean"]), np.array(nu["sd"]), np.array(em["sd"]))
    dz = (m1 - m2) / np.sqrt(s1 ** 2 + s2 ** 2)
    say(f"  |mean difference|/sd: median {np.median(np.abs(dz)):.2f}, max {np.max(np.abs(dz)):.2f}; "
        f"sd ratio emcee/NUTS median {np.median(s2 / s1):.2f}")
    out["ratio_min_ess_per_core_hour"], out["ratio_logp_ess_per_core_hour"] = r_min, r_lp
    for i, nm in enumerate(names):
        if any(re.search(k, nm) for k in a.key):
            say(f"  {nm:32s} NUTS {m1[i]:+.4g} +- {s1[i]:.3g} (ESS {nu['ess_bulk'][i]:.0f})   "
                f"emcee {m2[i]:+.4g} +- {s2[i]:.3g} (tau {em['tau'][i]:.0f})")

json.dump(out, open(os.path.join(a.out, "compare.json"), "w"))
open(os.path.join(a.out, "compare.txt"), "w").write("\n".join(lines) + "\n")
