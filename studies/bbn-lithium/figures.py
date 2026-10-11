"""Figures for the lithium study (PRC style from prc-figures/scripts/prcstyle.py)."""
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "prc-figures", "scripts"))
import prcstyle as ps

ps.apply()
R = os.path.join(HERE, "results")
F = os.path.join(HERE, "figures")
os.makedirs(F, exist_ok=True)
LI_OBS, LI_ERR = 1.6e-10, 0.3e-10
DH_OBS, DH_ERR = 2.527e-5, 0.030e-5
ETA_PLANCK, ETA_ERR = 6.104, 0.055

fix = json.load(open(f"{R}/lithium_fix.json"))
sens = json.load(open(f"{R}/sensitivity.json"))
s2 = json.load(open(f"{R}/scans2.json")) if os.path.exists(f"{R}/scans2.json") else None

# ---------------------------------------------------------------- 1 Schramm
if s2:
    E = sorted(s2["eta"], key=lambda d: d["eta10"])
    eta = np.array([d["eta10"] for d in E])
    fig, axs = plt.subplots(2, 1, figsize=(ps.COL_1, 4.6), sharex=True)
    ax = axs[0]
    ax.plot(eta, [d["D/H"] for d in E], color=ps.C["sum"], ls="-", label="D/H")
    ax.plot(eta, [d["He3/H"] for d in E], color=ps.C["casc"], ls="-.", label="$^3$He/H")
    ax.axhspan(DH_OBS - DH_ERR, DH_OBS + DH_ERR, color=ps.C["sum"], alpha=0.25, lw=0)
    ax.set_yscale("log")
    ax.set_ylabel("abundance / H")
    ax.legend(loc="upper right", frameon=False)
    ax = axs[1]
    ax.plot(eta, [d["Li7/H"] for d in E], color=ps.C["gs"], label="$^7$Li/H, this code")
    ax.axhspan(LI_OBS - LI_ERR, LI_OBS + LI_ERR, color=ps.C["bkg"], alpha=0.35, lw=0,
               label="Spite plateau")
    ax.set_yscale("log")
    ax.set_ylabel("$^7$Li/H")
    ax.set_xlabel(r"$\eta_{10}$")
    ax.legend(loc="upper left", frameon=False)
    for a in axs:
        a.axvspan(ETA_PLANCK - ETA_ERR, ETA_PLANCK + ETA_ERR, color=ps.C["alt"], alpha=0.35, lw=0)
        ps.minor(a)
    axs[0].text(ETA_PLANCK + 0.15, 1.2e-5, "Planck", color=ps.C["alt"])
    fig.tight_layout()
    fig.savefig(f"{F}/schramm.pdf"); fig.savefig(f"{F}/schramm.png", dpi=200)

# --------------------------------------------------------- 2 sensitivities
S = sens["sens"]
labels = {"p_n_to_d": r"p(n,$\gamma$)d", "He3_He4_to_Be7": r"$^3$He($\alpha$,$\gamma$)$^7$Be",
          "He3_d_to_p_He4": r"$^3$He(d,p)$^4$He", "Be7_n_to_p_Li7": r"$^7$Be(n,p)$^7$Li",
          "d_d_to_n_He3": r"d(d,n)$^3$He", "d_p_to_He3": r"d(p,$\gamma$)$^3$He",
          "neutron lifetime": r"$\tau_n$", "He3_n_to_p_t": r"$^3$He(n,p)t",
          "d_d_to_p_t": "d(d,p)t", "Li7_p_to_He4_He4": r"$^7$Li(p,$\alpha$)$\alpha$",
          "Be7_d_to_p_He4_He4": r"$^7$Be(d,p)2$\alpha$", "Be7_n_to_He4_He4": r"$^7$Be(n,$\alpha$)$\alpha$",
          "eta (baryon/photon)": r"$\eta$"}
keys = [k for k in sorted(S, key=lambda k: -abs(S[k]["Li7/H"])) if k in labels][:12]
fig, ax = plt.subplots(figsize=(ps.COL_1, 3.4))
y = np.arange(len(keys))[::-1]
ax.barh(y + 0.18, [S[k]["Li7/H"] for k in keys], 0.36, color=ps.C["gs"], label="$^7$Li/H")
ax.barh(y - 0.18, [S[k]["D/H"] for k in keys], 0.36, color=ps.C["sum"], label="D/H")
ax.set_yticks(y, [labels[k] for k in keys])
ax.axvline(0, color="k", lw=0.6)
ax.set_xlabel(r"$\partial \ln X / \partial \ln \lambda$")
ps.legend_above(ax, ncol=2)
fig.tight_layout()
fig.savefig(f"{F}/sensitivity.pdf"); fig.savefig(f"{F}/sensitivity.png", dpi=200)

# ------------------------------------------------------- 3 rate multipliers
names = {"Be7_n_to_p_Li7": (r"$^7$Be(n,p)", ps.C["sum"], "-"),
         "Be7_n_to_He4_He4": (r"$^7$Be(n,$\alpha$)", ps.C["sum2"], "--"),
         "Be7_d_to_p_He4_He4": (r"$^7$Be(d,p)2$\alpha$", ps.C["casc"], "-."),
         "He3_He4_to_Be7": (r"$^3$He($\alpha$,$\gamma$)", ps.C["gs"], "-")}
fig, ax = plt.subplots(figsize=(ps.COL_1, 2.9))
for n, (lab, c, ls) in names.items():
    pts = sorted(fix["A"][n], key=lambda d: d["f"]) + [{"f": 1.0, **fix["base"]}]
    pts = sorted(pts, key=lambda d: d["f"])
    ax.plot([d["f"] for d in pts], [d["Li7/H"] for d in pts], color=c, ls=ls, marker="o", ms=3, label=lab)
ax.axhspan(LI_OBS - LI_ERR, LI_OBS + LI_ERR, color=ps.C["bkg"], alpha=0.35, lw=0)
ax.text(1.15, 1.42e-10, "Spite plateau", color="k", fontsize=7)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("rate multiplier"); ax.set_ylabel("$^7$Li/H")
ax.set_ylim(1e-11, 3e-9)
ps.legend_above(ax, ncol=2)
fig.tight_layout()
fig.savefig(f"{F}/multipliers.pdf"); fig.savefig(f"{F}/multipliers.png", dpi=200)

if s2:
    # --------------------------------------------------- 4 best resonances
    fig, ax = plt.subplots(figsize=(ps.COL_1, 2.9))
    sty = {("d", None): (ps.C["casc"], "-", r"$^7$Be+d, $a$=1.4(A$_1^{1/3}$+A$_2^{1/3}$)"),
           ("d", 10.0): (ps.C["casc"], "--", r"$^7$Be+d, $a$=10 fm"),
           ("he3", None): (ps.C["gs"], "-", r"$^7$Be+$^3$He"),
           ("he3", 10.0): (ps.C["gs"], "--", r"$^7$Be+$^3$He, $a$=10 fm"),
           ("t", None): (ps.C["sum"], "-", r"$^7$Be+t")}
    for (x, a), (c, ls, lab) in sty.items():
        sub = [r for r in s2["resonance_max"] if r["x"] == x and r["a"] == a]
        ers = sorted({r["Er"] for r in sub})
        best = [min(r["Li7/H"] for r in sub if r["Er"] == e) for e in ers]
        ax.plot(np.array(ers) * 1e3, best, color=c, ls=ls, marker="o", ms=3, label=lab)
    ax.axhspan(LI_OBS - LI_ERR, LI_OBS + LI_ERR, color=ps.C["bkg"], alpha=0.35, lw=0)
    ax.axhline(fix["base"]["Li7/H"], color="k", lw=0.6, ls=":")
    ax.set_yscale("log")
    ax.set_xlabel(r"$E_r$ (keV, c.m.)"); ax.set_ylabel("$^7$Li/H (Wigner-limit resonance)")
    ps.legend_above(ax, ncol=2, fontsize=7)
    fig.tight_layout()
    fig.savefig(f"{F}/resonances.pdf"); fig.savefig(f"{F}/resonances.png", dpi=200)

    # ------------------------------------------------- 5 neutron injection
    I = s2["injection"]
    fig, ax = plt.subplots(figsize=(ps.COL_1, 2.9))
    taus = sorted({d["tau"] for d in I})
    cols = plt.cm.viridis(np.linspace(0.05, 0.9, len(taus)))
    for t, c in zip(taus, cols):
        sub = sorted([d for d in I if d["tau"] == t], key=lambda d: d["Yx"])
        ax.plot([d["D/H"] * 1e5 for d in sub], [d["Li7/H"] * 1e10 for d in sub], color=c,
                marker="o", ms=2.5, label=rf"$\tau_X$={t:g} s")
    ax.axhspan((LI_OBS - LI_ERR) * 1e10, (LI_OBS + LI_ERR) * 1e10, color=ps.C["bkg"], alpha=0.35, lw=0)
    ax.axvspan((DH_OBS - 2 * DH_ERR) * 1e5, (DH_OBS + 2 * DH_ERR) * 1e5, color=ps.C["sum"], alpha=0.25, lw=0)
    ax.set_xlim(2.3, 9.0)
    ax.set_xlabel(r"D/H ($10^{-5}$)"); ax.set_ylabel(r"$^7$Li/H ($10^{-10}$)")
    ps.legend_above(ax, ncol=3, fontsize=6.5)
    fig.tight_layout()
    fig.savefig(f"{F}/injection.pdf"); fig.savefig(f"{F}/injection.png", dpi=200)
print("figures written to", F)
