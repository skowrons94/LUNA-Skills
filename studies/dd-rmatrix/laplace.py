"""Linearised (Laplace) statistical uncertainty of the rates, as a cross-check
of the MCMC: Var(R) = g^T C g with C the R-matrix block of the fit covariance
(pseudo-inverse of J^T J at the minimum, nominal inflated errors and priors)
and g = dR/dx from AZURE2's analytic model gradients on the extrapolation grid.
"""
import json
import os
import warnings

warnings.filterwarnings("ignore")
import numpy as np

import fitter
import rates

import sys


def stat(src):
    res = json.load(open(f"{src}/result.json"))
    f = fitter.DDFit(src, res["opts"])
    z = np.load(f"{src}/best.npy")
    C = np.load(f"{src}/cov.npy")
    nx = len(f.x0)
    Cx = C[:nx, :nx]
    x = z[:nx]
    grid = np.array(res["grid"])
    f.m.extrap_mode()
    c = f.m.calculate_rwa(x)
    g = f.m.model_gradients(x)
    en = f.m.calculate_energies(x)
    out = {}
    for key, ks in (("dp", (0, 1)), ("dn", (2, 3))):
        E = np.concatenate([np.asarray(en[k], float) for k in ks]) * 1e3
        s = np.concatenate([np.asarray(c[k], float) for k in ks])
        G = np.vstack([np.asarray(g[k], float) for k in ks])
        o = np.argsort(E)
        E, s, G = E[o], s[o], G[o]
        R0 = rates.rate(E, s, rates.T9_GRID)
        # rate is linear in sigma: gradient column by column
        dR = np.array([rates.rate(E, G[:, j], rates.T9_GRID) for j in range(nx)]).T   # (nT, nx)
        var = np.einsum("ti,ij,tj->t", dR, Cx, dR)
        out[key] = (np.sqrt(np.clip(var, 0, None)) / R0).tolist()
        print(src, key, " ".join(f"T9={t}: {100 * out[key][i]:.2f}%" for i, t in enumerate(rates.T9_GRID)
                            if t in (0.1, 0.3, 0.5, 1.0)))
    f.close()
    return out


if __name__ == "__main__":
    dirs = sys.argv[1:] or ["runs/var_nominal"]
    out = {}
    for d in dirs:
        try:
            out[d] = stat(d)
        except Exception as e:
            print(d, "failed", e)
    old = json.load(open("results/laplace_stat.json")) if os.path.exists("results/laplace_stat.json") else {}
    old.update(out)
    old["T9"] = rates.T9_GRID.tolist()
    json.dump(old, open("results/laplace_stat.json", "w"))
