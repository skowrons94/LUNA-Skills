#!/usr/bin/env python3
"""Joint peak/total efficiency fitting with reviewed prompt-cascade schemes.

This is an independent-photon approximation, not a substitute for validated
angular correlations, electron/X-ray response or timing-dependent summing.
CSV rows: source,energy_keV,distance_cm,exposure,observed,error.
"""

import argparse, csv, json
from pathlib import Path
import numpy as np
from scipy.special import expit
from analysis_utils import fit_model, save_report, plotting
from cascade import enumerate_paths, peak_probability


def efficiencies(energy, distance, p, reference_distance):
    """Bounded alternative to the legacy distance curve: 0<=peak<=total<=1.

    Logit(total)=quadratic ln(E/1000) minus 2ln((d+d0)/(dref+d0));
    peak/total=logistic(quadratic ln(E/1000)). d0 and distances are in cm.
    """
    if energy <= 0 or min(distance + p["d0_cm"], reference_distance + p["d0_cm"]) <= 0:
        raise ValueError("Invalid energy/distance offset")
    x = np.log(energy / 1000)
    total = expit(
        p["t0"]
        + p.get("t1", 0) * x
        + p.get("t2", 0) * x * x
        - 2 * np.log((distance + p["d0_cm"]) / (reference_distance + p["d0_cm"]))
    )
    fraction = expit(p["f0"] + p.get("f1", 0) * x + p.get("f2", 0) * x * x)
    return float(total * fraction), float(total)


def run(config, out):
    config = Path(config)
    cfg = json.loads(config.read_text())
    root = config.parent
    data_path = (root / cfg["data_csv"]).resolve()
    inputs = [config, data_path]
    with data_path.open() as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("Empty observations")
    sources = {}
    for name, spec in cfg["sources"].items():
        path = (root / spec["scheme_json"]).resolve()
        inputs.append(path)
        sources[name] = (enumerate_paths(json.loads(path.read_text())), spec)
    obs = []
    errors = []
    for r in rows:
        if r["source"] not in sources:
            raise ValueError("Unknown source " + r["source"])
        for k in ["energy_keV", "distance_cm", "exposure", "observed", "error"]:
            r[k] = float(r[k])
        if (
            not np.isfinite(
                [
                    r[k]
                    for k in [
                        "energy_keV",
                        "distance_cm",
                        "exposure",
                        "observed",
                        "error",
                    ]
                ]
            ).all()
            or min(r["energy_keV"], r["exposure"], r["error"]) <= 0
            or r["distance_cm"] < 0
        ):
            raise ValueError("Invalid observation")
        obs.append(r["observed"])
        errors.append(r["error"])
    obs = np.array(obs)
    errors = np.array(errors)
    ref = float(cfg["reference_distance_cm"])
    tol = float(cfg["energy_tolerance_keV"])

    def prediction(p):
        out = []
        for r in rows:
            paths, spec = sources[r["source"]]
            dist = r["distance_cm"]
            ep = lambda E: efficiencies(E, dist, p, ref)[0]
            et = lambda E: efficiencies(E, dist, p, ref)[1]
            scale = (
                p[spec["scale_parameter"]]
                if "scale_parameter" in spec
                else float(spec.get("scale", 1))
            )
            if scale <= 0:
                raise ValueError("Source scale must be positive")
            out.append(
                r["exposure"]
                * scale
                * peak_probability(paths, r["energy_keV"], tol, ep, et)
            )
        return np.array(out)

    def residual(p):
        r = (prediction(p) - obs) / errors
        for name, prior in cfg.get("priors", {}).items():
            if prior["sigma"] <= 0:
                raise ValueError("Prior sigma must be positive")
            r = np.append(r, (p[name] - prior["mean"]) / prior["sigma"])
        return r

    summary = fit_model(
        residual,
        cfg["parameters"],
        starts=cfg.get("starts", 3),
        seed=cfg.get("seed", 12345),
        max_nfev=cfg.get("max_nfev", 1000),
    )
    pred = prediction(summary["parameters"])
    r = (pred - obs) / errors
    summary.update(
        data_chi2=float(r @ r),
        observations=len(rows),
        model="Bounded distance-logit total efficiency and logit peak/total ratio",
        assumptions="Independent prompt photons; ideal sum peaks; assessed complete schemes; no angular correlations, Compton sum-in, atomic X-rays or electron detection",
    )
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    with (out / "predictions.csv").open("w") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "source",
                "energy_keV",
                "distance_cm",
                "observed",
                "error",
                "predicted",
                "standardized_residual",
            ]
        )
        for row, m, v in zip(rows, pred, r):
            w.writerow(
                [
                    row["source"],
                    row["energy_keV"],
                    row["distance_cm"],
                    row["observed"],
                    row["error"],
                    m,
                    v,
                ]
            )
    plt = plotting()
    fig, ax = plt.subplots(2, 1, figsize=(8, 6), gridspec_kw={"height_ratios": [3, 1]})
    i = np.arange(len(rows))
    ax[0].errorbar(i, obs, yerr=errors, fmt="o", label="Observed")
    ax[0].plot(i, pred, "x", label="Cascade fit", color="#df7834")
    ax[0].legend()
    ax[0].set_ylabel("Observable counts / yield units")
    ax[1].axhline(0, color="gray")
    ax[1].plot(i, r, "o")
    ax[1].set(xlabel="Observation index (see predictions.csv)", ylabel="Residual / σ")
    fig.tight_layout()
    fig.savefig(out / "cascade_fit.png")
    fig.savefig(out / "cascade_fit.pdf")
    plt.close(fig)
    save_report(
        out,
        "Joint cascade-efficiency analysis",
        summary,
        inputs,
        cfg,
        ["cascade_fit.png"],
    )
    print(f'Results: {out / "report.html"}')
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("config", type=Path)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    r = run(a.config, a.out)
    raise SystemExit(0 if r["success"] else 1)
