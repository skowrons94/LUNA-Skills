"""Figures for the d+d evaluation (PRC style)."""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "prc-figures", "scripts"))
import prcstyle as ps
import fitter

ps.apply()
os.makedirs("figures", exist_ok=True)
EV = json.load(open("results/dd_evaluation.json"))
T9 = np.array(EV["T9"])
LAB = {"dp": r"$^2$H(d,p)$^3$H", "dn": r"$^2$H(d,n)$^3$He"}

# ------------------------------------------------ 1. S-factors with data
res = json.load(open("runs/var_nominal/result.json"))
grid = np.array(res["grid"])
f = fitter.PolyFit("runs/var_nominal", res["opts"], degree=5)   # bookkeeping only
z = np.load("runs/var_nominal/best.npy")
nrm = {}
names = [n for n in res["summary"]["norms"]]
nrm = res["summary"]["norms"]
mc = np.load("runs/mcmc/rates.npz") if os.path.exists("runs/mcmc/rates.npz") else None
conv = grid * np.exp(2 * fitter.pi_eta(grid)) * 1e3          # sigma[b] -> S[eV b]... keV b below
fig, axs = plt.subplots(2, 1, figsize=(ps.COL_2 * 0.62, 5.6), sharex=True)
exps = sorted(set(f.exp[f.use]))
marks = dict(zip(exps, "osD^v<>phH*Xd"))
cols = plt.cm.tab20(np.linspace(0, 1, len(exps) + 1))
for ax, key in zip(axs, ("dp", "dn")):
    S = np.array(res[key]) * grid * np.exp(2 * fitter.pi_eta(grid))
    ax.plot(grid, S, color="k", lw=1.2, label="R-matrix (this work)", zorder=5)
    for ex, c in zip(exps, cols):
        m = (f.exp == ex) & (f.reac == key) & f.use
        if not m.any():
            continue
        Sd = f.y[m] / (nrm[ex] * f.fscr[m]) * f.E[m] * np.exp(2 * fitter.pi_eta(f.E[m]))
        Se = f.s[m] / (nrm[ex] * f.fscr[m]) * f.E[m] * np.exp(2 * fitter.pi_eta(f.E[m]))
        ax.errorbar(f.E[m], Sd, Se, fmt=marks[ex], ms=3, mfc="none", color=c, lw=0.7,
                    label=f"{ex} ($n$={nrm[ex]:.3f})")
    ax.set_xscale("log"); ax.set_xlim(1.5, 700); ax.set_ylim(40, 180)
    ax.set_ylabel(f"{LAB[key]}  $S$ (keV b)")
    ax.axvspan(30, 300, color=ps.C["bkgfill"], lw=0, zorder=0)
    ps.minor(ax)
axs[0].text(35, 165, "BBN Gamow window", fontsize=7)
axs[1].set_xlabel(r"$E$ (keV, c.m.)")
h, l = axs[1].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=4, fontsize=6, frameon=False, bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(rect=(0, 0, 1, 0.9))
fig.savefig("figures/sfactors.pdf"); fig.savefig("figures/sfactors.png", dpi=200)

# ------------------------------------------- 2. rate ratio to REACLIB
fig, axs = plt.subplots(1, 2, figsize=(ps.COL_2, 2.8), sharey=True)
for ax, key in zip(axs, ("dp", "dn")):
    nom = np.array(EV["nominal"][key]); rl = np.array(EV["reaclib"][key])
    B = EV["budget"][key]
    tot = np.array(B["total"]); st = np.array(B.get("stat", np.zeros_like(tot)))
    ax.fill_between(T9, nom / rl * (1 - tot), nom / rl * (1 + tot), color=ps.C["sum2"], alpha=0.6,
                    lw=0, label="total (stat + syst)")
    ax.fill_between(T9, nom / rl * (1 - st), nom / rl * (1 + st), color=ps.C["sum"], alpha=0.8,
                    lw=0, label="statistical (MCMC)")
    ax.plot(T9, nom / rl, color="k", lw=1.0, label="this work")
    ax.axhline(1, color=ps.C["alt"], ls="--", lw=1.0, label="REACLIB (Gómez Iñesta 2017)")
    ax.set_xscale("log"); ax.set_xlabel(r"$T_9$"); ax.set_title(LAB[key], fontsize=9)
    ax.axvspan(0.3, 1.0, color=ps.C["bkgfill"], lw=0, zorder=0)
    ps.minor(ax)
axs[0].set_ylabel(r"$N_A\langle\sigma v\rangle$ / REACLIB")
axs[0].set_ylim(0.88, 1.12)
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=4, fontsize=6.5, frameon=False)
fig.tight_layout(rect=(0, 0, 1, 0.9))
fig.savefig("figures/rate_ratio.pdf"); fig.savefig("figures/rate_ratio.png", dpi=200)

# ------------------------------------------- 3. uncertainty budget at BBN T9
order = ["stat", "influence (jackknife excess)", "data:selection", "data:outliers", "errors:inflation",
         "errors:arnold", "errors:energy", "norm:LE06", "norm:legacy",
         "model:radius_dd", "model:radius_exit", "model:poles", "model:partial_waves",
         "model:independent", "screening", "window", "total",
         "norm:BJ90", "data:thm"]
i5 = int(np.argmin(abs(T9 - 0.5)))
fig, ax = plt.subplots(figsize=(ps.COL_1 * 1.15, 3.8))
keys = [k for k in order if k in EV["budget"]["dp"]]
y = np.arange(len(keys))[::-1]
ax.barh(y + 0.18, [100 * EV["budget"]["dp"][k][i5] for k in keys], 0.36, color=ps.C["gs"], label="d(d,p)")
ax.barh(y - 0.18, [100 * EV["budget"]["dn"][k][i5] for k in keys], 0.36, color=ps.C["sum"], label="d(d,n)")
lab = [k + ("  [check]" if k in ("norm:BJ90", "data:thm") else "") for k in keys]
ax.set_yticks(y, lab, fontsize=6.5)
ax.axhline(y[keys.index("total")] - 0.5, color="k", lw=0.5, ls=":")
ax.set_xlabel(r"rate uncertainty at $T_9$ = 0.5 (%)")
ps.legend_above(ax, ncol=2)
ps.minor(ax)
fig.tight_layout()
fig.savefig("figures/budget.pdf"); fig.savefig("figures/budget.png", dpi=200)

# ------------------------------------------- 4. variations at T9 = 0.5
V = EV["variations"]
fig, ax = plt.subplots(figsize=(ps.COL_2 * 0.62, 6.4))
y = np.arange(len(V))[::-1]
ax.scatter([100 * v["d_dp"][i5] for v in V], y + 0.15, s=10, color=ps.C["gs"], label="d(d,p)")
ax.scatter([100 * v["d_dn"][i5] for v in V], y - 0.15, s=10, marker="s", color=ps.C["sum"], label="d(d,n)")
ax.set_yticks(y, [f"{v['group']}: {v['name']}" for v in V], fontsize=5.5)
ax.axvline(0, color="k", lw=0.6)
for k, c in (("dp", ps.C["gs"]), ("dn", ps.C["sum"])):
    st = 100 * EV["budget"][k].get("stat", [0] * len(T9))[i5]
    ax.axvspan(-st, st, color=c, alpha=0.12, lw=0)
ax.set_xlabel(r"rate change vs nominal at $T_9$ = 0.5 (%)")
ps.legend_above(ax, ncol=2)
fig.tight_layout()
fig.savefig("figures/variations.pdf"); fig.savefig("figures/variations.png", dpi=200)
print("figures written")

# ------------------------------------------- 5. the scale tension
import rates as _r
fig, axs = plt.subplots(1, 2, figsize=(ps.COL_2, 3.0), sharey=True)
scen = [("nominal", "k", "-", "nominal"), ("without KR87b", ps.C["gs"], "--", "without Krauss 87 setup 2"),
        ("without BJ90", ps.C["sum"], "-.", "without Brown & Jarmie 90"),
        ("+ THM (Tumino)", ps.C["alt"], ":", "+ THM")]
def curve(name):
    r = json.load(open(f"runs/var_{''.join(c if c.isalnum() else '_' for c in name)}/result.json"))
    return {k: np.array(r[k]) for k in ("dp", "dn")}
base = curve("nominal")
for ax, key in zip(axs, ("dp", "dn")):
    for name, c, ls, lab in scen:
        cv = curve(name)
        ax.plot(grid, cv[key] / base[key], color=c, ls=ls, lw=1.1, label=lab)
    for ex, mk, col in (("BJ90", "o", ps.C["sum"]), ("LE06", "s", ps.C["casc"]), ("KR87b", "^", ps.C["gs"])):
        m = (f.exp == ex) & (f.reac == key) & f.use
        mod = np.interp(f.E[m], grid, base[key]) * f.fscr[m]
        ax.errorbar(f.E[m], f.y[m] / mod, f.err[m] / mod, fmt=mk, ms=3, mfc="none", color=col, lw=0.6,
                    label=f"{ex} data (as published)")
    ax.axvspan(30, 300, color=ps.C["bkgfill"], lw=0, zorder=0)
    ax.set_xscale("log"); ax.set_xlim(8, 450); ax.set_ylim(0.85, 1.15)
    ax.set_xlabel(r"$E$ (keV, c.m.)"); ax.set_title(LAB[key], fontsize=9)
    ps.minor(ax)
axs[0].set_ylabel(r"$\sigma$ / nominal fit")
h, l = axs[1].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=4, fontsize=6, frameon=False)
fig.tight_layout(rect=(0, 0, 1, 0.84))
fig.savefig("figures/scale_tension.pdf"); fig.savefig("figures/scale_tension.png", dpi=200)
print("scale tension figure written")
