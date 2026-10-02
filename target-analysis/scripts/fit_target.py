#!/usr/bin/env python3
"""Fit an excitation curve with named parameters; save plots, covariance and provenance.

CSV requires energy_lab_keV,yield,error. JSON provides parameter bounds and fixed
model settings; see references/usability.md. Reported errors are local Gaussian
errors with absolute input uncertainties, not a full systematic uncertainty budget.
"""

import argparse
import json
from pathlib import Path
import numpy as np
from analysis_utils import read_csv, fit_model, save_report, plotting
from target_model import table, response, profile, counts_per_microcoulomb


def run(config_path, out):
    config_path = Path(config_path)
    cfg = json.loads(config_path.read_text())
    root = config_path.parent
    inputs = [config_path]

    def path(key):
        p = (root / cfg[key]).resolve()
        inputs.append(p)
        return p

    data = read_csv(path("data_csv"), ["energy_lab_keV", "yield", "error"])
    if (data["error"] <= 0).any():
        raise ValueError("All errors must be positive absolute standard deviations")
    xs = table(path("cross_section_csv"))
    mixture = "active_stopping_csv" in cfg
    if mixture:
        if "effective_stopping_csv" in cfg:
            raise ValueError("Choose effective table OR active/inactive mixture tables")
        active = table(path("active_stopping_csv"))
        inactive = table(path("inactive_stopping_csv"))
        lo = max(active[0, 0], inactive[0, 0])
        hi = min(active[-1, 0], inactive[-1, 0])
        grid = np.union1d(active[:, 0], inactive[:, 0])
        grid = grid[(grid >= lo) & (grid <= hi)]
        if len(grid) < 2:
            raise ValueError("Stopping tables have no useful common range")
        active_values = np.interp(grid, active[:, 0], active[:, 1])
        inactive_values = np.interp(grid, inactive[:, 0], inactive[:, 1])
    else:
        stop = table(path("effective_stopping_csv"))
    yunit = cfg.get("yield_unit", "per_ion")
    if yunit not in ("per_ion", "counts_per_microcoulomb"):
        raise ValueError("Unknown yield_unit")

    def model(p, x):
        settings = {**cfg.get("model", {}), **p}
        background = settings.pop("background", 0.0)
        if mixture:
            ratio = settings.pop("inactive_to_active")
            if ratio < 0:
                raise ValueError("Composition ratio must be nonnegative")
            current_stop = np.column_stack(
                (grid, active_values + ratio * inactive_values)
            )
        else:
            current_stop = stop
        y = response(x, xs, current_stop, **settings)
        if yunit == "counts_per_microcoulomb":
            y = counts_per_microcoulomb(
                y, cfg["efficiency"], cfg.get("charge_state", 1)
            )
        return y + background

    priors = cfg.get("priors", {})

    def residual(p):
        r = (model(p, data["energy_lab_keV"]) - data["yield"]) / data["error"]
        for name, v in priors.items():
            if v["sigma"] <= 0:
                raise ValueError("Prior sigma must be positive")
            r = np.append(r, (p[name] - v["mean"]) / v["sigma"])
        return r

    summary = fit_model(
        residual,
        cfg["parameters"],
        seed=cfg.get("seed", 12345),
        starts=cfg.get("starts", 3),
        max_nfev=cfg.get("max_nfev", 1000),
    )
    params = summary["parameters"]
    pred = model(params, data["energy_lab_keV"])
    r = (pred - data["yield"]) / data["error"]
    summary.update(
        data_chi2=float(r @ r),
        data_points=len(data),
        free_parameter_count=len(summary["free_parameters"]),
        uncertainty_note="Local absolute-error covariance; priors included once. Profile is in lab energy loss, not physical depth.",
        yield_unit=yunit,
    )
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    np.savetxt(
        out / "fit.csv",
        np.column_stack(
            (data["energy_lab_keV"], data["yield"], data["error"], pred, r)
        ),
        delimiter=",",
        header="energy_lab_keV,observed,error,predicted,standardized_residual",
        comments="",
    )
    plt = plotting()
    fig, axes = plt.subplots(
        2, 1, figsize=(8, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    ix = np.argsort(data["energy_lab_keV"])
    axes[0].errorbar(
        data["energy_lab_keV"],
        data["yield"],
        yerr=data["error"],
        fmt="o",
        ms=4,
        color="#17324d",
        label="Measurements",
    )
    axes[0].plot(
        data["energy_lab_keV"][ix], pred[ix], color="#df7834", label="Fitted response"
    )
    axes[0].set_ylabel(yunit.replace("_", " "))
    axes[0].legend()
    axes[1].axhline(0, color="gray")
    axes[1].plot(data["energy_lab_keV"], r, "o", ms=4)
    axes[1].set(xlabel="Incident laboratory energy (keV)", ylabel="Residual / σ")
    fig.tight_layout()
    fig.savefig(out / "fit.png")
    fig.savefig(out / "fit.pdf")
    plt.close(fig)
    settings = {**cfg.get("model", {}), **params}
    u = np.linspace(0, settings.get("max_loss_keV", 30), 600)
    rho = settings.get("amplitude", 1) * profile(
        u,
        settings.get("profile_kind", "gaussian"),
        settings.get("mean_keV", 7),
        settings.get("sigma_keV", 4),
        settings.get("width_keV", 10),
    )
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(u, rho, color="#217b7e")
    ax.set(
        xlabel="Laboratory energy loss (keV)",
        ylabel="Profile modifier",
        title="Phenomenological target profile",
    )
    fig.tight_layout()
    fig.savefig(out / "profile.png")
    plt.close(fig)
    save_report(
        out,
        "Target excitation-curve analysis",
        summary,
        inputs,
        cfg,
        ["fit.png", "profile.png"],
    )
    print(f'Results: {out / "report.html"}')
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("config", type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    result = run(a.config, a.out)
    raise SystemExit(0 if result["success"] else 1)
