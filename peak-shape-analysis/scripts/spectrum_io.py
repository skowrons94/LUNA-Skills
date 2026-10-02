"""Read spectra without PyROOT. CSV bins use explicit edges, not guessed channel centres."""

from pathlib import Path
import numpy as np


def load_spectrum(spec, base):
    """Return low edges, high edges, counts, variances and resolved source path.

    CSV: low,high,counts[,variance]. ROOT: root_file,histogram, optional linear
    calibration {offset,slope}; no dead-time correction is applied to raw counts.
    Independent-bin variances are assumed. The caller chooses the analysis window.
    """
    if "spectrum_csv" in spec:
        path = (Path(base) / spec["spectrum_csv"]).resolve()
        a = np.genfromtxt(path, delimiter=",", names=True, ndmin=1)
        if not a.dtype.names or not {"low", "high", "counts"} <= set(a.dtype.names):
            raise ValueError("Spectrum CSV needs low,high,counts[,variance]")
        low, high, n = a["low"], a["high"], a["counts"]
        var = a["variance"] if "variance" in a.dtype.names else n.copy()
    else:
        import uproot

        path = (Path(base) / spec["root_file"]).resolve()
        with uproot.open(path) as f:
            h = f[spec["histogram"]]
            n, edges = h.to_numpy(flow=False)
            var = h.variances(flow=False)
        if n.ndim != 1:
            raise ValueError("Only one-dimensional histograms supported")
        if var is None:
            var = n.copy()
        low, high = edges[:-1], edges[1:]
        cal = spec.get("calibration", {"offset": 0, "slope": 1})
        if cal["slope"] <= 0:
            raise ValueError("Calibration slope must be positive")
        low = cal["offset"] + cal["slope"] * low
        high = cal["offset"] + cal["slope"] * high
    if (
        not len(n)
        or not np.isfinite([low, high, n, var]).all()
        or (high <= low).any()
        or (var < 0).any()
        or (n < 0).any()
    ):
        raise ValueError("Invalid raw spectrum bins/counts/variances")
    if len(n) > 1 and (not np.allclose(high[:-1], low[1:], rtol=1e-10, atol=1e-9)):
        raise ValueError("Spectrum bins must be contiguous and ordered")
    return low, high, n, var, path


def select_bins(low, high, window):
    """Require ROI boundaries to coincide with bin edges; never fractionally split Poisson counts."""
    a, b = map(float, window)
    if a >= b:
        raise ValueError("Window lower bound must be less than upper bound")
    if (
        not np.isclose(low, a, rtol=0, atol=1e-7).any()
        or not np.isclose(high, b, rtol=0, atol=1e-7).any()
    ):
        raise ValueError(f"Window {window} must use actual histogram edges")
    m = (low >= a - 1e-7) & (high <= b + 1e-7)
    if not m.any():
        raise ValueError("Empty window")
    return m
