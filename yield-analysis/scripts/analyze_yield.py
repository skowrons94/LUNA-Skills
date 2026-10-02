#!/usr/bin/env python3
"""Batch ROI yields with finite-sideband uncertainty, explicit normalization and QA plots.

JSON config contains a runs list. Spectra are CSV or ROOT TH1 via uproot.
See references/configuration.md for bin-edge, normalization and covariance conventions.
"""

import argparse, csv, json
from pathlib import Path
import numpy as np
from analysis_utils import save_report, plotting
from spectrum_io import load_spectrum, select_bins

E_CHARGE = 1.602176634e-19


def integrate_roi(
    low, high, counts, variance, roi, left, right, background="linear", step_energy=None
):
    """Linear combination of independent bin counts; propagates sideband counting variance."""
    if not left[1] <= roi[0] < roi[1] <= right[0]:
        raise ValueError("Sidebands must flank and not overlap ROI")
    masks = [select_bins(low, high, w) for w in (roi, left, right)]
    widths = [float(np.sum((high - low)[m])) for m in masks]
    sums = [float(counts[m].sum()) for m in masks]
    vars_ = [float(variance[m].sum()) for m in masks]
    wr, wl, wh = widths
    if background == "constant":
        al = ah = wr / (wl + wh)
    elif background == "linear":
        xl = (left[0] + left[1]) / 2
        xh = (right[0] + right[1]) / 2
        xr = (roi[0] + roi[1]) / 2
        al = wr * (xh - xr) / (xh - xl) / wl
        ah = wr * (xr - xl) / (xh - xl) / wh
    elif background == "step":
        if step_energy is None or not roi[0] <= step_energy <= roi[1]:
            raise ValueError("Step needs an energy inside ROI")
        al = (step_energy - roi[0]) / wl
        ah = (roi[1] - step_energy) / wh
    else:
        raise ValueError("background must be constant, linear or step")
    b = al * sums[1] + ah * sums[2]
    v = vars_[0] + al * al * vars_[1] + ah * ah * vars_[2]
    return {
        "gross_counts": sums[0],
        "background_counts": b,
        "net_counts": sums[0] - b,
        "net_variance": v,
        "stat_error_counts": float(np.sqrt(v)),
        "left_coefficient": al,
        "right_coefficient": ah,
        "background_model": background,
    }


def normalization(run):
    """Total collected charge is paired with observed raw counts and live fraction."""
    q = float(run["charge_C"])
    z = float(run.get("charge_state", 1))
    live = float(run["live_fraction"])
    eff = float(run["efficiency"])
    br = float(run.get("branching", 1))
    survival = float(run.get("summing_survival", 1))
    if (
        not np.isfinite([q, z, live, eff, br, survival]).all()
        or min(q, z) <= 0
        or not all(0 < v <= 1 for v in [live, eff, br, survival])
    ):
        raise ValueError("Invalid charge or probability/live fraction")
    return q / (z * E_CHARGE) * live * eff * br * survival


def run(config, out):
    config = Path(config)
    cfg = json.loads(config.read_text())
    ids = [
        str(r.get("analysis_id", f"{r['run_id']}:{i}"))
        for i, r in enumerate(cfg["runs"])
    ]
    if len(ids) != len(set(ids)):
        raise ValueError("analysis_id must be unique for covariance alignment")
    if not all(
        np.isfinite(float(r["energy_lab_keV"])) and float(r["energy_lab_keV"]) > 0
        for r in cfg["runs"]
    ):
        raise ValueError("Incident energies must be finite and positive")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    plt = plotting()
    results = []
    inputs = [config]
    figures = []
    for i, r in enumerate(cfg["runs"]):
        low, high, n, v, path = load_spectrum(r, config.parent)
        inputs.append(path)
        res = integrate_roi(
            low,
            high,
            n,
            v,
            r["roi"],
            r["left_sideband"],
            r["right_sideband"],
            r.get("background", "linear"),
            r.get("step_energy"),
        )
        denom = normalization(r)
        y = res["net_counts"] / denom
        err = res["stat_error_counts"] / denom
        rel = float(r.get("independent_normalization_relative_error", 0))
        if not np.isfinite(rel) or rel < 0:
            raise ValueError("Normalization relative error must be nonnegative")
        res.update(
            analysis_id=r.get("analysis_id", f"{r['run_id']}:{i}"),
            detector=r.get("detector", ""),
            transition=r.get("transition", ""),
            target=r.get("target", ""),
            run_id=str(r["run_id"]),
            energy_lab_keV=float(r["energy_lab_keV"]),
            yield_per_ion=y,
            stat_error=err,
            independent_normalization_error=abs(y) * rel,
            normalization=denom,
            warning=(
                "Nonpositive net yield: preserve measurement; consider a count likelihood/upper limit"
                if y <= 0
                else ""
            ),
        )
        results.append(res)
        fig, ax = plt.subplots(figsize=(8, 4))
        centres = (low + high) / 2
        view = (centres >= r["left_sideband"][0]) & (centres <= r["right_sideband"][1])
        ax.stairs(
            n[view],
            np.r_[low[view], high[view][-1]],
            color="#17324d",
            label="Raw counts",
        )
        for window, color, label in [
            (r["roi"], "#df7834", "Signal ROI"),
            (r["left_sideband"], "#217b7e", "Sidebands"),
            (r["right_sideband"], "#217b7e", None),
        ]:
            ax.axvspan(*window, color=color, alpha=0.15, label=label)
        ax.set(
            xlabel=r.get("axis_label", "Energy (keV)"),
            ylabel="Counts / bin",
            title=f"Run {r['run_id']} • net {res['net_counts']:.1f} ± {res['stat_error_counts']:.1f}",
        )
        ax.legend()
        fig.tight_layout()
        name = f"roi_{i:04d}.png"
        fig.savefig(out / name)
        plt.close(fig)
        figures.append(name)
    if not results:
        raise ValueError("No runs configured")
    y = np.array([r["yield_per_ion"] for r in results])
    stat = np.array([r["stat_error"] for r in results])
    ind = np.array([r["independent_normalization_error"] for r in results])
    cov = np.diag(stat**2 + ind**2)
    for name, fraction in cfg.get("shared_systematics", {}).items():
        if not np.isfinite(fraction) or fraction < 0:
            raise ValueError(f"Invalid shared fractional error {name}")
        cov += np.outer(y * fraction, y * fraction)
    with (out / "yields.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)
    np.savetxt(out / "covariance.csv", cov, delimiter=",")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.errorbar(
        [r["energy_lab_keV"] for r in results], y, yerr=stat, fmt="o", color="#217b7e"
    )
    ax.set(
        xlabel="Incident lab energy (keV)",
        ylabel="Yield per ion",
        title="Statistical uncertainties; systematic covariance saved separately",
    )
    fig.tight_layout()
    fig.savefig(out / "excitation_curve.png")
    fig.savefig(out / "excitation_curve.pdf")
    plt.close(fig)
    save_report(
        out,
        "Reaction-yield analysis",
        {
            "runs": results,
            "covariance_row_order": [r["analysis_id"] for r in results],
            "shared_systematics": cfg.get("shared_systematics", {}),
            "variance_assumption": "Independent raw histogram bins; no uncertainty added twice",
        },
        inputs,
        cfg,
        ["excitation_curve.png"] + figures,
    )
    print(f'Results: {out / "report.html"}')
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("config", type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    run(a.config, a.out)
