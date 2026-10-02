#!/usr/bin/env python3
"""Energy-loss-coordinate target response; all energy variables are LAB keV.
Input cross section is cm2; effective stopping is keV cm2 per active atom.
Profile is a dimensionless modifier, not a normalized depth probability density.
"""

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.integrate import simpson

E_CHARGE = 1.602176634e-19


def table(path):
    a = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    return validate_table(a, str(path))


def validate_table(a, label="table"):
    a = np.asarray(a, dtype=float)
    if (
        a.ndim != 2
        or a.shape[1] != 2
        or len(a) < 2
        or not np.isfinite(a).all()
        or (np.diff(a[:, 0]) <= 0).any()
        or (a < 0).any()
    ):
        raise ValueError(
            f"{label}: need two finite nonnegative columns, strictly increasing energy"
        )
    return a


def interpolate(a, x):
    x = np.asarray(x, dtype=float)
    if not np.isfinite(x).all() or x.min() < a[0, 0] or x.max() > a[-1, 0]:
        raise ValueError(
            f"Query outside table coverage [{a[0,0]}, {a[-1,0]}] keV; no endpoint clamping"
        )
    return np.interp(x, a[:, 0], a[:, 1])


def profile(u, kind, mean_keV=0.0, sigma_keV=1.0, width_keV=1.0):
    if kind == "gaussian":
        if sigma_keV <= 0 or mean_keV < 0:
            raise ValueError("Invalid Gaussian profile")
        return np.exp(-0.5 * ((u - mean_keV) / sigma_keV) ** 2)
    if kind == "uniform":
        if width_keV <= 0:
            raise ValueError("Invalid width")
        return (u <= width_keV).astype(float)
    raise ValueError("Profile must be gaussian or uniform")


def response(
    energy_lab_keV,
    cross_section,
    stopping,
    *,
    profile_kind="gaussian",
    mean_keV=7.0,
    sigma_keV=4.0,
    width_keV=10.0,
    max_loss_keV=30.0,
    beam_sigma_keV=0.0,
    doppler_sigma_keV=0.0,
    straggling_keV_per_sqrt_keV=0.0,
    amplitude=1.0,
    depth_points=401,
    kernel_points=101,
    kernel_sigmas=5.0,
):
    cross_section = validate_table(cross_section, "cross section")
    stopping = validate_table(stopping, "stopping")
    vals = [
        mean_keV,
        sigma_keV,
        width_keV,
        max_loss_keV,
        beam_sigma_keV,
        doppler_sigma_keV,
        straggling_keV_per_sqrt_keV,
        amplitude,
        kernel_sigmas,
    ]
    if (
        not np.isfinite(vals).all()
        or min(vals) < 0
        or max_loss_keV <= 0
        or kernel_sigmas <= 0
    ):
        raise ValueError(
            "Finite nonnegative parameters and positive integration extent required"
        )
    if (
        depth_points < 3
        or kernel_points < 3
        or depth_points % 2 != 1
        or kernel_points % 2 != 1
    ):
        raise ValueError("Use odd integration point counts >=3")
    if profile_kind == "uniform" and max_loss_keV < width_keV:
        raise ValueError("Integration extent truncates the uniform profile")
    # Integrate exactly to the uniform edge rather than discretizing a jump.
    extent = width_keV if profile_kind == "uniform" else max_loss_keV
    u = np.linspace(0, extent, depth_points)
    rho = profile(u, profile_kind, mean_keV, sigma_keV, width_keV)
    s = np.sqrt(
        beam_sigma_keV**2 + doppler_sigma_keV**2 + straggling_keV_per_sqrt_keV**2 * u
    )
    z = np.linspace(-kernel_sigmas, kernel_sigmas, kernel_points)
    w = np.exp(-0.5 * z * z)
    norm = simpson(w, x=z)
    result = []
    for energy in np.atleast_1d(energy_lab_keV):
        x = energy - u[:, None] + s[:, None] * z[None, :]
        stop = interpolate(stopping, x)
        if (stop <= 0).any():
            raise ValueError("Stopping must be positive over the integration domain")
        f = interpolate(cross_section, x) / stop
        folded = simpson(f * w, x=z, axis=1) / norm
        result.append(amplitude * simpson(rho * folded, x=u))
    return np.array(result)


def counts_per_microcoulomb(yield_per_ion, efficiency, charge_state=1):
    if not 0 < efficiency <= 1 or charge_state <= 0:
        raise ValueError("Invalid efficiency or positive charge state")
    return np.asarray(yield_per_ion) * efficiency * 1e-6 / (charge_state * E_CHARGE)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("config", type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    cfg = json.loads(a.config.read_text())
    xs = (a.config.parent / cfg["cross_section_csv"]).resolve()
    sp = (a.config.parent / cfg["effective_stopping_csv"]).resolve()
    energies = np.asarray(cfg["energy_lab_keV"], dtype=float)
    if energies.ndim != 1 or not len(energies) or not np.isfinite(energies).all():
        raise ValueError("Invalid beam energies")
    y = response(energies, table(xs), table(sp), **cfg["model"])
    a.out.mkdir(parents=True, exist_ok=False)
    np.savetxt(
        a.out / "prediction.csv",
        np.column_stack((energies, y)),
        delimiter=",",
        header="energy_lab_keV,yield_per_incident_ion",
        comments="",
    )
    manifest = {
        "config": cfg,
        "assumptions": "Lab energy; cm2 cross section; effective stopping per active atom; energy-loss-profile approximation",
        "sha256": {
            str(f): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in [a.config, xs, sp]
        },
        "numpy_version": np.__version__,
    }
    (a.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(y)} predictions to {a.out}")


if __name__ == "__main__":
    main()
