#!/usr/bin/env python3
"""Fit a positive log-polynomial efficiency curve at one specified detector geometry.

Uses generalized least squares on log efficiency. The delta-method covariance
requires reasonably small relative uncertainties. Does not infer total efficiency
from peak efficiency or claim reliable extrapolation outside calibrated energies.
"""

import argparse, json
from pathlib import Path
import numpy as np
from analysis_utils import read_csv, save_report, plotting


def fit(config, out):
    config = Path(config)
    cfg = json.loads(config.read_text())
    path = (config.parent / cfg["points_csv"]).resolve()
    a = read_csv(path, ["energy_keV", "efficiency", "error"])
    inputs = [config, path]
    E, y, err = a["energy_keV"], a["efficiency"], a["error"]
    degree = int(cfg.get("degree", 2))
    eref = float(cfg.get("reference_energy_keV", 1000))
    if (
        np.any(E <= 0)
        or np.any((y <= 0) | (y > 1))
        or np.any(err <= 0)
        or eref <= 0
        or not 0 <= degree <= 5
        or len(E) <= degree + 1
    ):
        raise ValueError(
            "Need positive physical efficiencies/errors, degree 0..5, and more points than coefficients"
        )
    if "geometry" not in cfg:
        raise ValueError("Provide geometry description; do not silently pool positions")
    C = np.diag(err**2)
    if "covariance_csv" in cfg:
        p = (config.parent / cfg["covariance_csv"]).resolve()
        inputs.append(p)
        C = np.loadtxt(p, delimiter=",", ndmin=2)
        if (
            C.shape != (len(E), len(E))
            or not np.isfinite(C).all()
            or not np.allclose(C, C.T, rtol=1e-10, atol=0)
        ):
            raise ValueError(
                "Covariance must be finite symmetric and aligned with points"
            )
    err = np.sqrt(np.diag(C))
    L = np.linalg.cholesky(C / np.outer(y, y))
    x = np.log(E / eref)
    X = np.vander(x, degree + 1, increasing=True)
    WX = np.linalg.solve(L, X)
    Wy = np.linalg.solve(L, np.log(y))
    coef, _, rank, _ = np.linalg.lstsq(WX, Wy, rcond=None)
    if rank < degree + 1:
        raise ValueError("Rank-deficient efficiency fit")
    cov = np.linalg.inv(WX.T @ WX)
    res = np.linalg.solve(L, X @ coef - np.log(y))
    grid = np.geomspace(E.min(), E.max(), 400)
    G = np.vander(np.log(grid / eref), degree + 1, increasing=True)
    curve = np.exp(G @ coef)
    sigma_log = np.sqrt(np.maximum(0, np.einsum("ij,jk,ik->i", G, cov, G)))
    if np.any(curve > 1):
        raise ValueError(
            "Fitted curve exceeds efficiency 1 inside calibration range; revise model"
        )
    warnings = []
    if np.any(err / y > 0.2):
        warnings.append(
            "Large relative errors: log-space delta approximation may be inadequate; fit count likelihood instead"
        )
    summary = {
        "coefficients": coef.tolist(),
        "coefficient_definition": "ln(efficiency)=sum c_i [ln(E_keV/reference_energy_keV)]^i",
        "reference_energy_keV": eref,
        "covariance": cov.tolist(),
        "chi2_log_space": float(res @ res),
        "dof": len(E) - degree - 1,
        "valid_energy_keV": [float(E.min()), float(E.max())],
        "geometry": cfg["geometry"],
        "quantity": cfg.get("quantity", "full_energy_peak"),
        "warnings": warnings,
    }
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    np.savetxt(
        out / "curve.csv",
        np.c_[grid, curve, curve * np.exp(-sigma_log), curve * np.exp(sigma_log)],
        delimiter=",",
        header="energy_keV,efficiency,local_1sigma_low,local_1sigma_high",
        comments="",
    )
    plt = plotting()
    fig, axes = plt.subplots(
        2, 1, figsize=(8, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    axes[0].errorbar(E, y, yerr=err, fmt="o", color="#17324d", label="Calibration")
    axes[0].plot(grid, curve, color="#df7834", label="Fit")
    axes[0].fill_between(
        grid,
        curve * np.exp(-sigma_log),
        curve * np.exp(sigma_log),
        color="#df7834",
        alpha=0.2,
        label="Local 1σ",
    )
    axes[0].set(xscale="log", yscale="log", ylabel="Absolute efficiency")
    axes[0].legend()
    axes[1].axhline(0, color="gray")
    axes[1].plot(E, (y - np.exp(X @ coef)) / err, "o")
    axes[1].set(xlabel="Gamma energy (keV)", ylabel="Marginal residual / σ")
    fig.tight_layout()
    fig.savefig(out / "efficiency.png")
    fig.savefig(out / "efficiency.pdf")
    plt.close(fig)
    save_report(
        out, "Detector-efficiency calibration", summary, inputs, cfg, ["efficiency.png"]
    )
    print(f'Results: {out / "report.html"}')
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("config", type=Path)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    fit(a.config, a.out)
