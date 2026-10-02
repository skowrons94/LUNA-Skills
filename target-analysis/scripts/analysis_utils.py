"""Small shared conventions, bundled with each skill for independent use.

No implicit global state: callers provide paths, model and residual functions.
Covariance assumes supplied residuals are standardized with absolute errors.
"""

from pathlib import Path
import hashlib
import html
import json
import numpy as np
from scipy.optimize import least_squares


def read_csv(path, required):
    """Read named numeric columns; preserve row order and reject missing/nonfinite data."""
    a = np.genfromtxt(path, delimiter=",", names=True, encoding="utf-8", ndmin=1)
    if not len(a) or not a.dtype.names or not set(required) <= set(a.dtype.names):
        raise ValueError(f"{path}: required columns {required}")
    for name in required:
        if not np.isfinite(a[name]).all():
            raise ValueError(f"{path}: nonfinite {name}")
    return a


def fit_model(residual, specifications, *, seed=12345, starts=3, max_nfev=1000):
    """Bounded, repeatable multi-start fit. Returns parameters, diagnostics, covariance.

    Specifications map names to {value,min,max,vary}; fixed values still reach model.
    Full-rank local covariance is inv(J.T J), never silently rescaled by chi-square.
    """
    names = [k for k, v in specifications.items() if v.get("vary", True)]
    if not names:
        raise ValueError("Choose at least one varying parameter")
    fixed = {k: float(v["value"]) for k, v in specifications.items()}
    if not np.isfinite(list(fixed.values())).all():
        raise ValueError("Fixed and initial parameter values must be finite")
    lower = np.array([specifications[k]["min"] for k in names], float)
    upper = np.array([specifications[k]["max"] for k in names], float)
    x0 = np.array([fixed[k] for k in names])
    if (
        not np.isfinite([lower, upper, x0]).all()
        or np.any(lower >= upper)
        or np.any(x0 < lower)
        or np.any(x0 > upper)
    ):
        raise ValueError(
            "Finite ordered bounds containing the initial values are required"
        )
    if starts < 1:
        raise ValueError("starts must be >=1")

    def unpack(x):
        return {**fixed, **dict(zip(names, x))}

    def fun(x):
        r = np.asarray(residual(unpack(x)), float)
        if r.ndim != 1 or not np.isfinite(r).all():
            raise ValueError("Residuals must be finite 1-D values")
        return r

    rng = np.random.default_rng(seed)
    attempts = []
    for i in range(starts):
        initial = x0 if i == 0 else rng.uniform(lower, upper)
        result = least_squares(
            fun, initial, bounds=(lower, upper), x_scale="jac", max_nfev=max_nfev
        )
        attempts.append(result)
    best = min(attempts, key=lambda r: float(r.fun @ r.fun))
    rank = int(np.linalg.matrix_rank(best.jac))
    cov = None
    warnings = []
    if not best.success:
        warnings.append("Optimizer did not converge")
    if rank < len(names):
        warnings.append(
            "Rank-deficient Jacobian: parameters not independently constrained"
        )
    else:
        # SVD avoids squaring the Jacobian condition number in normal equations.
        _, singular_values, vt = np.linalg.svd(best.jac, full_matrices=False)
        cov = (vt.T / singular_values**2) @ vt
    bound = [
        name
        for i, name in enumerate(names)
        if min(best.x[i] - lower[i], upper[i] - best.x[i])
        < 1e-5 * (upper[i] - lower[i])
    ]
    if bound:
        warnings.append("Parameters near bounds: " + ", ".join(bound))
    summary = {
        "parameters": unpack(best.x),
        "free_parameters": names,
        "success": bool(best.success),
        "message": str(best.message),
        "objective": float(best.fun @ best.fun),
        "residual_count": len(best.fun),
        "jacobian_rank": rank,
        "covariance_order": names,
        "covariance": cov.tolist() if cov is not None else None,
        "standard_errors": (
            dict(zip(names, np.sqrt(np.maximum(0, np.diag(cov))).tolist()))
            if cov is not None
            else None
        ),
        "warnings": warnings,
        "seed": seed,
        "starts_objective": [float(r.fun @ r.fun) for r in attempts],
    }
    return summary


def save_report(out, title, summary, inputs=(), config=None, figures=()):
    """Write human-readable HTML and machine-readable JSON, including SHA-256 inputs."""
    out = Path(out)
    record = {
        **summary,
        "inputs_sha256": {
            str(Path(p).resolve()): hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in inputs
        },
    }
    if config is not None:
        record["config"] = config
    text = json.dumps(record, indent=2, allow_nan=False)
    (out / "result.json").write_text(text + "\n")
    imgs = "".join(
        f'<figure><img src="{html.escape(str(x),quote=True)}" alt="Analysis diagnostic"></figure>'
        for x in figures
    )
    (out / "report.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>'
        + html.escape(title)
        + "</title><style>body{font:16px system-ui;max-width:1050px;margin:40px auto;padding:0 24px;color:#17324d;background:#f5f8fb}h1{font-size:30px}figure{margin:24px 0}img{max-width:100%;background:white;border-radius:12px}pre{background:white;padding:24px;overflow:auto;border-radius:12px;font-size:13px}</style><h1>"
        + html.escape(title)
        + "</h1>"
        + imgs
        + "<h2>Results and provenance</h2><pre>"
        + html.escape(text)
        + "</pre>"
    )


def plotting():
    """Headless plotting with consistent legible output; never depends on a GUI."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 140,
            "savefig.bbox": "tight",
            "axes.grid": True,
            "grid.alpha": 0.2,
        }
    )
    return plt
