#!/usr/bin/env python3
"""Fit raw gamma-spectrum bins with an asymmetric target edge or Gaussian signal.

The detector response is integrated over actual bin edges. Counts stay raw for
the Poisson likelihood. A supplied physics template may weight the intrinsic
shape; this tool does not infer nuclear cross sections from a generic peak shape.
"""

import argparse, json
from pathlib import Path
import numpy as np
from scipy.special import expit, ndtr, xlogy
from analysis_utils import read_csv, fit_model, save_report, plotting
from spectrum_io import load_spectrum, select_bins


def response_matrix(low, high, x, sigma):
    """Probability of a Gaussian response landing in each observed bin per true energy."""
    if sigma <= 0:
        raise ValueError(
            "Response sigma must be positive; refine below bin width if negligible"
        )
    return ndtr((high[:, None] - x) / sigma) - ndtr((low[:, None] - x) / sigma)


def intrinsic(x, p, kind):
    """Nonnegative source shapes; target-edge widths are logistic scales, not Gaussian sigma."""
    if kind == "gaussian":
        if p["intrinsic_sigma_keV"] <= 0:
            raise ValueError("Gaussian sigma must be positive")
        return np.exp(-0.5 * ((x - p["centroid_keV"]) / p["intrinsic_sigma_keV"]) ** 2)
    if kind != "target_edge":
        raise ValueError("Choose gaussian or target_edge")
    b = p["edge_keV"]
    d = p["loss_width_keV"]
    lo = p["low_edge_scale_keV"]
    hi = p["high_edge_scale_keV"]
    if min(d, lo, hi) <= 0:
        raise ValueError("Positive loss width and edge scales required")
    shape = expit((b - x) / hi) * expit((x - b + d) / lo)
    if p.get("tail_amplitude", 0) < 0:
        raise ValueError("Tail amplitude must be nonnegative")
    if p.get("tail_amplitude", 0) > 0:
        if min(p["tail_low_scale_keV"], p["tail_high_scale_keV"]) <= 0:
            raise ValueError("Tail scales must be positive")
        shape += (
            p["tail_amplitude"]
            * expit((x - p["tail_start_keV"]) / p["tail_low_scale_keV"])
            * expit((b - d - x) / p["tail_high_scale_keV"])
        )
    return shape


def deviance_residual(observed, expected):
    """Signed square-root Poisson deviance, including zero-count bins exactly."""
    if (expected <= 0).any():
        raise ValueError("Expected bin counts must be positive")
    return np.sign(expected - observed) * np.sqrt(
        np.maximum(
            0,
            2
            * (
                expected
                - observed
                + xlogy(observed, observed)
                - xlogy(observed, expected)
            ),
        )
    )


def run(config, out):
    config = Path(config)
    cfg = json.loads(config.read_text())
    low, high, n, var, path = load_spectrum(cfg["spectrum"], config.parent)
    m = select_bins(low, high, cfg["fit_window"])
    low, high, n, var = [a[m] for a in [low, high, n, var]]
    kind = cfg.get("shape", "target_edge")
    likelihood = cfg.get("likelihood", "poisson")
    if likelihood == "poisson" and (
        not np.allclose(n, np.round(n), rtol=0, atol=1e-8) or not np.allclose(var, n)
    ):
        raise ValueError(
            "Poisson fitting requires raw, unweighted integer counts and Poisson variances"
        )
    if likelihood not in ("poisson", "gaussian"):
        raise ValueError("Unknown likelihood")
    if likelihood == "gaussian" and (var <= 0).any():
        raise ValueError("Gaussian likelihood needs positive supplied bin variances")
    domain = cfg["source_domain"]
    points = int(cfg.get("source_points", 1201))
    if len(domain) != 2 or not domain[0] < domain[1] or points < 101:
        raise ValueError("Ordered source_domain and >=101 points required")
    x = np.linspace(*domain, points)
    dx = x[1] - x[0]
    quad = np.full(points, dx)
    quad[[0, -1]] *= 0.5
    K = response_matrix(low, high, x, float(cfg["response_sigma_keV"]))
    template = np.ones_like(x)
    inputs = [config, path]
    if "template_csv" in cfg:
        p = (config.parent / cfg["template_csv"]).resolve()
        inputs.append(p)
        t = read_csv(p, ["energy_keV", "weight"])
        if (np.diff(t["energy_keV"]) <= 0).any() or (t["weight"] < 0).any():
            raise ValueError("Template needs ordered energies and nonnegative weights")
        if x.min() < t["energy_keV"].min() or x.max() > t["energy_keV"].max():
            raise ValueError("Template must cover source_domain; no extrapolation")
        template = np.interp(x, t["energy_keV"], t["weight"])
    centres = (low + high) / 2
    width = high - low

    def prediction(p, components=False):
        dens = intrinsic(x, p, kind) * template
        norm = np.sum(dens * quad)
        if norm <= 0 or p["area_counts"] < 0:
            raise ValueError("Invalid signal normalization")
        signal = p["area_counts"] * (K @ (dens * quad / norm))
        back = (
            np.interp(
                centres,
                [low[0], high[-1]],
                [p["background_left"], p["background_right"]],
            )
            * width
        )
        if (back < 0).any():
            raise ValueError("Background density must be nonnegative")
        mu = np.maximum(signal + back, 1e-300)
        return (mu, signal, back) if components else mu

    def residual(p):
        mu = prediction(p)
        return (
            deviance_residual(n, mu)
            if likelihood == "poisson"
            else (mu - n) / np.sqrt(var)
        )

    summary = fit_model(
        residual,
        cfg["parameters"],
        seed=cfg.get("seed", 12345),
        starts=cfg.get("starts", 3),
        max_nfev=cfg.get("max_nfev", 1000),
    )
    p = summary["parameters"]
    mu, sig, back = prediction(p, True)
    res = residual(p)
    summary.update(
        likelihood=likelihood,
        fit_bins=len(n),
        observed_signal_counts_in_window=float(sig.sum()),
        area_definition="Expected observed signal counts over the configured true-energy source_domain, before loss outside fit_window; no charge/live/efficiency correction",
        response_sigma_keV=cfg["response_sigma_keV"],
        source_grid_step_keV=dx,
        physical_scope="Phenomenological gamma-energy shape; physical beam/target loss requires a validated kinematic/stopping model",
    )
    if dx > cfg["response_sigma_keV"] / 3:
        summary["warnings"].append(
            "Source grid coarse relative to detector response; refine and verify convergence"
        )
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    np.savetxt(
        out / "fit.csv",
        np.c_[low, high, n, mu, sig, back, res],
        delimiter=",",
        header="low,high,observed,predicted,signal,background,residual",
        comments="",
    )
    plt = plotting()
    fig, ax = plt.subplots(
        2, 1, figsize=(9, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    ax[0].stairs(n, np.r_[low, high[-1]], color="#17324d", label="Raw spectrum")
    ax[0].plot(centres, mu, color="#df7834", label="Fit")
    ax[0].plot(centres, back, "--", color="#217b7e", label="Background")
    ax[0].set_ylabel("Counts / bin")
    ax[0].legend()
    ax[1].axhline(0, color="gray")
    ax[1].plot(centres, res, ".")
    ax[1].set(
        xlabel="Gamma energy (keV)",
        ylabel="Deviance" if likelihood == "poisson" else "Residual / σ",
    )
    fig.tight_layout()
    fig.savefig(out / "fit.png")
    fig.savefig(out / "fit.pdf")
    plt.close(fig)
    save_report(out, "Gamma peak-shape analysis", summary, inputs, cfg, ["fit.png"])
    print(f'Results: {out / "report.html"}')
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("config", type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    r = run(a.config, a.out)
    raise SystemExit(0 if r["success"] else 1)
