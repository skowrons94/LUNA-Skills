"""PRC / ROOT-like matplotlib style and helpers for nuclear-physics figures."""

from __future__ import annotations

import subprocess
from pathlib import Path

import matplotlib as mpl
import numpy as np
from matplotlib.ticker import AutoMinorLocator, FixedLocator, NullFormatter

# colour roles (colour-blind safe, also separated by line style)
C = {
    "data": "#000000",
    "gs": "#c0392b",       # true signal (e.g. ground-state capture)
    "sum": "#1f5fbf",      # summing-in / main background
    "sum2": "#7fb2e5",     # secondary component
    "casc": "#2e8b57",     # another component
    "other": "#b9b9b9",    # remaining components
    "bkg": "#7f7f7f",      # flat / laboratory background
    "bkgfill": "#e3e3e3",
    "alt": "#e08a00",      # alternative scenario
}
LS = {"gs": "-", "sum": "--", "casc": "-.", "bkg": ":", "alt": (0, (5, 1, 1, 1))}
COL_1 = 3.4
COL_2 = 7.0


def apply() -> None:
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9, "axes.labelsize": 10, "axes.titlesize": 9, "legend.fontsize": 8,
        "xtick.labelsize": 9, "ytick.labelsize": 9,
        "axes.linewidth": 0.8, "axes.grid": False,
        "axes.spines.top": True, "axes.spines.right": True,
        "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True, "ytick.right": True,
        "xtick.minor.visible": True, "ytick.minor.visible": True,
        "xtick.major.size": 5, "ytick.major.size": 5, "xtick.minor.size": 2.5, "ytick.minor.size": 2.5,
        "xtick.major.width": 0.7, "ytick.major.width": 0.7,
        "lines.linewidth": 1.2, "legend.frameon": False, "legend.handlelength": 2.2,
        "errorbar.capsize": 0, "savefig.bbox": "tight", "savefig.dpi": 300, "pdf.fonttype": 42,
        "figure.figsize": (COL_1, 2.6),
    })


def minor(ax) -> None:
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    if ax.get_yscale() == "linear":
        ax.yaxis.set_minor_locator(AutoMinorLocator())


def label(ax, text: str, loc: str = "upper left", box: bool = True) -> None:
    x, ha = (0.04, "left") if "left" in loc else (0.96, "right")
    y, va = (0.94, "top") if "upper" in loc else (0.06, "bottom")
    kw = dict(bbox=dict(facecolor="white", edgecolor="none", pad=1)) if box else {}
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va, **kw)


def legend_above(ax, ncol: int = 2, **kw):
    """Legend outside the axes, above the frame (never on data)."""
    return ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=ncol, fontsize=kw.pop("fontsize", 7),
                     handlelength=kw.pop("handlelength", 1.6), columnspacing=kw.pop("columnspacing", 0.9), **kw)


def log_ticks(ax, values, axis: str = "y") -> None:
    """Readable labels on a log axis (e.g. [1, 2, 5, 10, 20, 50, 100])."""
    a = ax.yaxis if axis == "y" else ax.xaxis
    a.set_major_locator(FixedLocator(values))
    a.set_major_formatter(mpl.ticker.FixedFormatter([f"{v:g}" for v in values]))
    a.set_minor_formatter(NullFormatter())


def stacked_stairs(ax, bins, components, background=None, outline: bool = True, alpha: float = 0.85):
    """Stack histogram components (list of (counts, label, colour), drawn bottom->top) on an optional
    background array. Returns the total. Put the signal LAST so it sits on top."""
    base = np.zeros(len(bins) - 1) if background is None else np.asarray(background, float).copy()
    if background is not None:
        ax.stairs(base, bins, fill=True, color=C["bkgfill"], label="background")
    for h, lab, col in components:
        ax.stairs(base + h, bins, baseline=base, fill=True, color=col, alpha=alpha, lw=0, label=lab)
        base = base + h
    if outline:
        ax.stairs(base, bins, color="k", lw=0.6)
    return base


def annotate_peaks(ax, bins, counts, peaks, fontsize: float = 6.3, factor: float = 1.3):
    """Label peaks above the local maximum. peaks: [(energy, text, x_offset_points)]."""
    for e0, txt, dx in peaks:
        i = int(np.clip(np.searchsorted(bins, e0) - 1, 0, len(counts) - 1))
        y = counts[max(i - 3, 0): i + 4].max()
        ax.annotate(txt, (e0, y * factor), xytext=(dx, 10), textcoords="offset points", ha="center",
                    fontsize=fontsize, arrowprops=dict(arrowstyle="-", lw=0.5, color="#555555"))


def heatmap(ax, xb, yb, H, cmap="magma_r", vmin_frac: float = 3e-4, label: str | None = None, fig=None, cax=None):
    """2D histogram with log colour scale and masked empty bins (H shaped (nx, ny))."""
    vmax = np.nanmax(H)
    im = ax.pcolormesh(xb, yb, np.ma.masked_less_equal(H.T, 0), cmap=cmap,
                       norm=mpl.colors.LogNorm(vmin=vmax * vmin_frac, vmax=vmax), rasterized=True)
    if fig is not None:
        cb = fig.colorbar(im, ax=ax if cax is None else None, cax=cax, pad=0.01)
        if label:
            cb.set_label(label, fontsize=7)
    return im


def crop_image(path, threshold: int = 245, pad: int = 30):
    """Crop white margins of a rendered image (e.g. Geant4 TSG/RayTracer output)."""
    from PIL import Image
    im = np.asarray(Image.open(path).convert("RGB"))
    ys, xs = np.where((im < threshold).any(2))
    return im[max(ys.min() - pad, 0):ys.max() + pad, max(xs.min() - pad, 0):xs.max() + pad]


def dark_blob_center(im, x_max_frac: float = 0.35, level: int = 60):
    """Centre (y, x) of dark, unsaturated pixels in the left part of an image: use it to place
    an arrow on a feature (e.g. the beam opening of a target holder) instead of guessing."""
    rgb = im.astype(float)
    m = (rgb.max(2) < level) & ((rgb.max(2) - rgb.min(2)) < 20)
    m[:, int(x_max_frac * im.shape[1]):] = False
    ys, xs = np.where(m)
    return float(np.median(ys)), float(np.median(xs))


def check_render(pdf: str | Path, dpi: int = 110) -> Path:
    """Render a PDF figure to PNG next to it (pdftoppm) for visual inspection."""
    pdf = Path(pdf)
    out = pdf.with_suffix("")
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-singlefile", str(pdf), str(out)], check=True)
    return out.with_suffix(".png")
