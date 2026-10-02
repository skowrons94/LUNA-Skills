#!/usr/bin/env python3
"""Offline demo of the PRC figure style: builds a spectrum, a stacked multi-panel zoom, an S-factor
plot with data, a method-comparison plot and a heatmap from synthetic data, renders them to PNG and
prints PASS."""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prcstyle as ps  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/prc-demo")
out = Path(ap.parse_args().out)
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(1)
ps.apply()

# 1. spectrum
bins = np.arange(300, 7800, 10.0)
c = 0.5 * (bins[1:] + bins[:-1])
tot = 30 * np.exp(-c / 3000) + 1
for e, a in ((6791, 800), (6175, 200), (5181, 60), (5240, 60), (6280, 150), (640, 2000)):
    tot += a * np.exp(-0.5 * ((c - e) / 4) ** 2)
tot = rng.poisson(tot).astype(float)
fig, ax = plt.subplots(figsize=(ps.COL_2, 2.6))
ax.stairs(tot, bins, color="k", lw=0.6, label="all transitions")
ax.axhline(1, color=ps.C["bkg"], ls=":", label="background")
ax.set_yscale("log"); ax.set_ylim(0.3, tot.max() * 8)
ps.annotate_peaks(ax, bins, tot, [(6791, "6.79", 0), (6175, "6.17", -9), (6280, "SE", 7), (5210, "5.18, 5.24", 0)])
ps.legend_above(ax, ncol=2)
ax.set_xlabel(r"$E_\gamma$ (keV)"); ax.set_ylabel("counts / 10 keV"); ps.minor(ax)
fig.savefig(out / "spectrum.pdf"); plt.close(fig)

# 2. stacked zoom, two selections
zb = np.arange(7300, 7480, 4.0)
zc = 0.5 * (zb[1:] + zb[:-1])
sig = 40 * np.exp((zc - 7450) / 15) * (zc < 7452)
summ = 50 * np.exp((zc - 7450) / 15) * (zc < 7452)
fig, axes = plt.subplots(2, 1, figsize=(ps.COL_1, 3.6), sharex=True)
for ax, f, title in zip(axes, (1.0, 0.07), ("(a) all events", "(b) not tagged")):
    ps.stacked_stairs(ax, zb, [(summ * f, "sum-in", ps.C["sum"]), (sig * (1 if f == 1 else 0.8), "signal", ps.C["gs"])],
                      background=np.full(len(zc), 0.5))
    ps.label(ax, title); ax.set_ylabel("counts / 4 keV"); ps.minor(ax)
    ax.set_ylim(0, 1.9 * ax.get_ylim()[1])
h, l = axes[0].get_legend_handles_labels()
fig.legend(h[::-1], l[::-1], loc="upper center", ncol=3, fontsize=7, bbox_to_anchor=(0.55, 1.0))
axes[-1].set_xlabel(r"$E_\gamma$ (keV)")
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(out / "zoom.pdf"); plt.close(fig)

# 3. S factor with data and model band (full resonance kept)
E = np.linspace(60, 420, 600)
S = 0.06 + 0.15 * np.exp(-E / 60) + 30 * (0.5) ** 2 / ((E - 259) ** 2 + 0.5**2 + 400)
fig, ax = plt.subplots(figsize=(ps.COL_1, 2.8))
ax.fill_between(E, S * 0.94, S * 1.06, color=ps.C["gs"], alpha=0.22, lw=0)
ax.plot(E, S, color=ps.C["gs"], label="R-matrix")
xd = np.array([110, 130, 150, 180, 210, 320, 350]); yd = np.interp(xd, E, S) * rng.normal(1, 0.08, len(xd))
ax.errorbar(xd, yd, 0.1 * yd, fmt="o", ms=3, mfc="white", color="k", lw=0.7, label="data A")
ax.errorbar(xd + 4, yd * 1.1, 0.08 * yd, fmt="D", ms=3, color="#444444", lw=0.7, label="data B")
ax.set_yscale("log"); ax.set_ylim(0.03, 1.5); ax.set_xlabel(r"$E$ (keV, c.m.)"); ax.set_ylabel(r"$S(E)$ (keV b)")
ps.legend_above(ax, ncol=3); ps.minor(ax)
fig.savefig(out / "sfactor.pdf"); plt.close(fig)

# 4. method comparison with readable log ticks
ep = np.array([120, 140, 160, 190, 220, 250, 360, 400])
fig, ax = plt.subplots(figsize=(ps.COL_1, 2.6))
for k, (name, col, mk, ls) in enumerate((("classical", ps.C["bkg"], "s", "--"), ("new method", ps.C["gs"], "o", "-"))):
    ax.plot(ep, (30 - 18 * k) * (ep / 120) ** -0.8, marker=mk, ms=3.5, color=col, ls=ls, label=name)
ax.set_yscale("log"); ax.set_ylim(1, 60); ps.log_ticks(ax, [1, 2, 5, 10, 20, 50])
ax.set_xlabel(r"$E_p$ (keV, lab)"); ax.set_ylabel("relative uncertainty (%)"); ps.legend_above(ax)
fig.savefig(out / "methods.pdf"); plt.close(fig)

# 5. heatmap with expected lines
xb = np.arange(4000, 7400.1, 10); yb = np.arange(0, 121, 4.0)
x = np.concatenate([rng.uniform(4000, 7400, 20000), rng.normal(6793, 4, 3000), rng.normal(6176, 4, 1000)])
y = np.concatenate([rng.exponential(12, 20000), rng.uniform(5, 110, 4000)])
H = np.histogram2d(x, y, [xb, yb])[0]
fig, ax = plt.subplots(figsize=(ps.COL_1 + 0.6, 2.6))
ps.heatmap(ax, xb, yb, H, label="entries / bin", fig=fig)
for e, t in ((6176, "6.17"), (6793, "6.79")):
    ax.annotate(t, (e, yb[-1]), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=6.5,
                annotation_clip=False)
ax.set_xlabel(r"$E_{\rm tot}-E(S)$ (keV)"); ax.set_ylabel("separation (mm)")
fig.savefig(out / "heatmap.pdf", dpi=300); plt.close(fig)

ok = True
for f in ("spectrum", "zoom", "sfactor", "methods", "heatmap"):
    try:
        png = ps.check_render(out / f"{f}.pdf")
        ok &= png.exists()
    except FileNotFoundError:      # pdftoppm not installed: PDFs still produced
        ok &= (out / f"{f}.pdf").exists()
print("PASS" if ok else "FAIL")
