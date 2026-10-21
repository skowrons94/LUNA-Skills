"""Graded agent tasks: synthetic fixtures with known answers, traps, and checkers.

Each task has
  generate(d)        -> truth dict; writes the fixture into the empty directory d
  prompt             -> what the agent is asked (it must write answer.json in d)
  check(d, truth)    -> list of (name, passed, info)
  reference(d, truth) / baseline(d, truth)
                     -> write a correct answer and a plausible naive one into d.
The selftest requires every reference to pass and every baseline to fail, so a checker that
cannot tell a right answer from a common wrong one is caught before it grades an agent.
Fixtures are deterministic (fixed seeds) and need only NumPy and SciPy.
"""

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

E_CHARGE = 1.602176634e-19
YEAR_D = 365.2422


# ---------------------------------------------------------------- helpers

def _spectrum(d, name, lo, hi, peaks, bg, seed):
    """Poisson spectrum with 1-keV bins; peaks = [(centroid, sigma, area)], bg = (a, b) counts/keV."""
    rng = np.random.default_rng(seed)
    low = np.arange(lo, hi, 1.0)
    mid = low + 0.5
    mu = bg[0] + bg[1] * (mid - lo)
    for c, s, a in peaks:
        mu = mu + a / (s * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((mid - c) / s) ** 2)
    n = rng.poisson(mu)
    with open(d / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["low", "high", "counts"])
        for a, b, c in zip(low, low + 1, n):
            w.writerow([f"{a:g}", f"{b:g}", int(c)])
    return low, n


def _read_spectrum(path):
    a = np.genfromtxt(path, delimiter=",", names=True)
    return a["low"], a["counts"].astype(float)


def _sideband_net(low, n, roi, left, right):
    """Net area with a linear background through the two sideband densities (exact for linear bg)."""
    sel = lambda w: (low >= w[0]) & (low + 1 <= w[1])
    mid = low + 0.5
    xl, xr = mid[sel(left)].mean(), mid[sel(right)].mean()
    dl = n[sel(left)].sum() / (left[1] - left[0])
    dr = n[sel(right)].sum() / (right[1] - right[0])
    slope = (dr - dl) / (xr - xl)
    xroi = 0.5 * (roi[0] + roi[1])
    width = roi[1] - roi[0]
    bkg = (dl + slope * (xroi - xl)) * width
    gross = n[sel(roi)].sum()
    # variance: gross + propagated sideband variance
    wl = (xr - xroi) / (xr - xl) * width / (left[1] - left[0])
    wr = (xroi - xl) / (xr - xl) * width / (right[1] - right[0])
    var = gross + wl ** 2 * n[sel(left)].sum() + wr ** 2 * n[sel(right)].sum()
    return gross - bkg, float(np.sqrt(var))


def _answer(d):
    p = d / "answer.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def _num(ans, key):
    try:
        return float(ans[key])
    except (KeyError, TypeError, ValueError):
        return None


def _write(d, obj):
    (d / "answer.json").write_text(json.dumps(obj, indent=2) + "\n")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- tasks

class YieldBasic:
    id = "yield-basic"
    skills = ["yield-analysis"]
    prompt = (
        "spectrum.csv is a 1-keV-binned gamma spectrum (columns low,high,counts) from run 812. "
        "runsheet.json gives the beam and detector information. Extract the net area of the line "
        "near 120 keV and the photon yield per incident projectile for that line, with statistical "
        "uncertainties. Write answer.json with keys net_counts, net_counts_err, yield_per_ion, "
        "yield_per_ion_err."
    )
    AREA, CHARGE, LIVE, EFF = 5000.0, 2.0e-5, 0.95, 0.02

    def generate(self, d):
        _spectrum(d, "spectrum.csv", 60, 200, [(120.0, 1.6, self.AREA)], (180.0, -0.4), seed=11)
        (d / "runsheet.json").write_text(json.dumps({
            "run": 812, "beam": "p", "charge_state": 1, "E_lab_keV": 300,
            "integrated_charge_C": self.CHARGE, "live_fraction": self.LIVE,
            "photopeak_efficiency_120keV": self.EFF, "branching": 1.0,
            "note": "counts are raw (not live-time corrected)"}, indent=2))
        low, n = _read_spectrum(d / "spectrum.csv")
        net, err = _sideband_net(low, n, [112, 128], [90, 105], [135, 150])
        norm = self.CHARGE / E_CHARGE * self.LIVE * self.EFF
        return {"net_ref": net, "net_err_ref": err, "norm": norm}

    def check(self, d, t):
        a = _answer(d)
        if a is None:
            return [("answer.json readable", False, "missing or invalid")]
        net, y, ye = _num(a, "net_counts"), _num(a, "yield_per_ion"), _num(a, "yield_per_ion_err")
        out = [("keys present", None not in (net, y, ye), "")]
        if None in (net, y, ye):
            return out
        tol = 4 * t["net_err_ref"]
        out.append(("net area consistent with truth", abs(net - self.AREA) < tol,
                    f"{net:.0f} vs {self.AREA:.0f} +- {tol:.0f}"))
        out.append(("normalisation = charge/e * live * eff", abs(y * t["norm"] / net - 1) < 0.01,
                    f"implied norm ratio {y * t['norm'] / net:.4f}"))
        out.append(("uncertainty quoted and plausible", 0.5 < (ye / y) / (t["net_err_ref"] / net) < 2.5,
                    f"rel err {ye / y:.4f}"))
        return out

    def reference(self, d, t):
        _write(d, {"net_counts": t["net_ref"], "net_counts_err": t["net_err_ref"],
                   "yield_per_ion": t["net_ref"] / t["norm"],
                   "yield_per_ion_err": t["net_err_ref"] / t["norm"]})

    def baseline(self, d, t):
        # forgets the live fraction
        norm = t["norm"] / self.LIVE
        _write(d, {"net_counts": t["net_ref"], "net_counts_err": t["net_err_ref"],
                   "yield_per_ion": t["net_ref"] / norm, "yield_per_ion_err": t["net_err_ref"] / norm})


class YieldUnitsTrap:
    id = "yield-units-trap"
    skills = ["yield-analysis"]
    prompt = (
        "spectrum.csv is the gamma spectrum of run 57 (columns low,high,counts, 1-keV bins) and "
        "run57.json is the acquisition log written by our DAQ; daq_notes.txt documents its fields. "
        "Give the photon yield per incident proton of the line near 300 keV. The photopeak "
        "efficiency there is 0.035. Write answer.json with keys net_counts, net_counts_err, "
        "yield_per_ion, yield_per_ion_err."
    )
    LIVE, CHARGE_UC, EFF = 0.88, 20.0, 0.035

    def generate(self, d):
        _spectrum(d, "spectrum.csv", 240, 360, [(300.0, 1.8, 8000.0)], (90.0, -0.2), seed=23)
        (d / "run57.json").write_text(json.dumps({
            "run": 57, "beam": "1H+", "E_lab_keV": 400, "charge_uC": self.CHARGE_UC,
            "deadTime": self.LIVE, "realTime_s": 3600.0}, indent=2))
        (d / "daq_notes.txt").write_text(
            "DAQ log fields\n"
            "charge_uC   integrated charge from the current integrator, microcoulombs\n"
            "deadTime    historical name: the ratio live_time / real_time (NOT the dead fraction)\n"
            "realTime_s  wall-clock acquisition time\n"
            "Counts in the spectra are raw and not live-time corrected.\n")
        low, n = _read_spectrum(d / "spectrum.csv")
        net, err = _sideband_net(low, n, [291, 309], [265, 282], [318, 335])
        norm = self.CHARGE_UC * 1e-6 / E_CHARGE * self.LIVE * self.EFF
        return {"net_ref": net, "net_err_ref": err, "norm": norm}

    def check(self, d, t):
        a = _answer(d)
        if a is None:
            return [("answer.json readable", False, "missing or invalid")]
        net, y = _num(a, "net_counts"), _num(a, "yield_per_ion")
        if None in (net, y) or net == 0:
            return [("keys present", False, "")]
        r = y * t["norm"] / net
        return [("keys present", True, ""),
                ("charge in uC and deadTime read as live fraction", abs(r - 1) < 0.01,
                 f"implied norm ratio {r:.4f} (1/0.12*0.88={0.88 / 0.12:.2f} if read as dead fraction)")]

    def reference(self, d, t):
        _write(d, {"net_counts": t["net_ref"], "net_counts_err": t["net_err_ref"],
                   "yield_per_ion": t["net_ref"] / t["norm"],
                   "yield_per_ion_err": t["net_err_ref"] / t["norm"]})

    def baseline(self, d, t):
        norm = t["norm"] / self.LIVE * (1 - self.LIVE)  # deadTime taken as dead fraction
        _write(d, {"net_counts": t["net_ref"], "net_counts_err": t["net_err_ref"],
                   "yield_per_ion": t["net_ref"] / norm, "yield_per_ion_err": t["net_err_ref"] / norm})


class PeakDoublet:
    id = "peak-doublet"
    skills = ["peak-shape-analysis", "yield-analysis"]
    prompt = (
        "spectrum.csv (columns low,high,counts, 1-keV bins) contains the reaction line at about "
        "1006 keV that we need, close to a stronger contaminant line. The detector resolution is "
        "about 2.8 keV FWHM at 1 MeV. Give the net area of the 1006 keV line and its uncertainty. "
        "Write answer.json with keys net_counts, net_counts_err."
    )
    TARGET = 3000.0

    def generate(self, d):
        _spectrum(d, "spectrum.csv", 960, 1050,
                  [(1000.0, 1.2, 8000.0), (1006.0, 1.2, self.TARGET)], (60.0, -0.15), seed=5)
        return {}

    def check(self, d, t):
        a = _answer(d)
        net = _num(a, "net_counts") if a else None
        if net is None:
            return [("answer.json readable", False, "")]
        return [("contaminant separated from 1006 keV line", abs(net - self.TARGET) < 0.10 * self.TARGET,
                 f"{net:.0f} vs {self.TARGET:.0f} +- 10%")]

    def reference(self, d, t):
        low, n = _read_spectrum(d / "spectrum.csv")
        x = low + 0.5

        def f(x, a1, a2, c, s, b0, b1):
            g = lambda m, a: a / (s * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((x - m) / s) ** 2)
            return g(c, a1) + g(c + 6.0, a2) + b0 + b1 * (x - 960)

        p, cov = curve_fit(f, x, n, p0=[7000, 2500, 1000, 1.3, 60, 0], sigma=np.sqrt(np.maximum(n, 1)))
        _write(d, {"net_counts": p[1], "net_counts_err": float(np.sqrt(cov[1, 1]))})

    def baseline(self, d, t):
        low, n = _read_spectrum(d / "spectrum.csv")
        net, err = _sideband_net(low, n, [1002, 1011], [985, 994], [1015, 1024])
        _write(d, {"net_counts": net, "net_counts_err": err})


class NegativeNetArea:
    id = "negative-net-area"
    skills = ["yield-analysis"]
    prompt = (
        "spectrum.csv (columns low,high,counts, 1-keV bins) is a long background-dominated run. "
        "Using the ROI 495-505 keV and linear-background sidebands 470-485 keV and 515-530 keV, "
        "give the background-subtracted net area in the ROI and its uncertainty, to be used later "
        "in a joint fit of several runs. Write answer.json with keys net_counts, net_counts_err."
    )

    def generate(self, d):
        for seed in range(100, 400):
            low, n = _spectrum(d, "spectrum.csv", 440, 560, [(500.0, 1.4, 40.0)], (200.0, -0.3), seed)
            net, err = _sideband_net(low, n, [495, 505], [470, 485], [515, 530])
            if net < -0.8 * err:
                return {"net_ref": net, "net_err_ref": err, "seed": seed}
        raise RuntimeError("no negative realisation found")

    def check(self, d, t):
        a = _answer(d)
        net = _num(a, "net_counts") if a else None
        if net is None:
            return [("answer.json readable", False, "")]
        return [("negative net area retained (not clipped to zero)",
                 abs(net - t["net_ref"]) < 0.15 * t["net_err_ref"],
                 f"{net:.1f} vs {t['net_ref']:.1f}")]

    def reference(self, d, t):
        _write(d, {"net_counts": t["net_ref"], "net_counts_err": t["net_err_ref"]})

    def baseline(self, d, t):
        _write(d, {"net_counts": 0.0, "net_counts_err": t["net_err_ref"]})


class EfficiencyDecay:
    id = "efficiency-decay"
    skills = ["efficiency-analysis"]
    prompt = (
        "calibration.json describes a calibration of our HPGe detector with certified 137Cs and "
        "60Co point sources (certificate activities, reference date, measurement date, live time and "
        "fitted net peak areas). Compute the full-energy-peak efficiency at 661.7, 1173.2 and "
        "1332.5 keV with uncertainties, using evaluated half-lives and emission probabilities. "
        "Write answer.json with keys eff_661, eff_1173, eff_1332 (and *_err)."
    )
    # evaluated values used to build the fixture (ENSDF/DDEP); the tolerance covers small differences
    LINES = {"eff_661": ("Cs137", 661.657, 0.8510), "eff_1173": ("Co60", 1173.228, 0.9985),
             "eff_1332": ("Co60", 1332.492, 0.999826)}
    HALF_LIFE_Y = {"Cs137": 30.08, "Co60": 5.2714}
    A0 = {"Cs137": 37.0e3, "Co60": 41.0e3}
    ELAPSED_D, LIVE_S = 1826.0, 7200.0

    @staticmethod
    def _eff(e):
        return 0.012 * (e / 1000.0) ** -0.85

    def _decayed(self, iso):
        return self.A0[iso] * np.exp(-np.log(2) * self.ELAPSED_D / (self.HALF_LIFE_Y[iso] * YEAR_D))

    def generate(self, d):
        peaks = []
        truth = {}
        for key, (iso, e, ig) in self.LINES.items():
            eff = self._eff(e)
            area = self._decayed(iso) * ig * self.LIVE_S * eff
            truth[key] = eff
            peaks.append({"source": iso, "energy_keV": e, "net_area": round(area),
                          "net_area_err": round(np.sqrt(area) * 1.05)})
        (d / "calibration.json").write_text(json.dumps({
            "detector": "HPGe-2", "geometry": "point source on axis, 25 cm from the endcap; "
                                              "true-coincidence summing is negligible here",
            "sources": {
                "Cs137": {"activity_Bq": self.A0["Cs137"], "activity_rel_unc": 0.015,
                          "reference_date": "2021-03-01"},
                "Co60": {"activity_Bq": self.A0["Co60"], "activity_rel_unc": 0.015,
                         "reference_date": "2021-03-01"}},
            "measurement_date": "2026-03-01", "live_time_s": self.LIVE_S,
            "peaks": peaks}, indent=2))
        return truth

    def check(self, d, t):
        a = _answer(d)
        if a is None:
            return [("answer.json readable", False, "")]
        out = []
        for k in self.LINES:
            v = _num(a, k)
            ok = v is not None and abs(v / t[k] - 1) < 0.015
            out.append((f"{k} decay-corrected", ok, f"{v} vs {t[k]:.5g}"))
        return out

    def reference(self, d, t):
        _write(d, {k: v for k, v in t.items()} | {k + "_err": 0.017 * v for k, v in t.items()})

    def baseline(self, d, t):
        # no decay correction
        ans = {}
        for k, (iso, e, ig) in self.LINES.items():
            ans[k] = t[k] * self._decayed(iso) / self.A0[iso]
        _write(d, ans)


class RawDataImmutable:
    id = "raw-data-immutable"
    skills = ["nuclear-research-project"]
    prompt = (
        "This is my analysis project. In data/raw/S_factor_lit.csv the energy 1250 keV is a "
        "transcription typo for 125 keV (I checked it against Table 2 of the paper). Fix it so I can "
        "use the corrected table in the fit. When done, write answer.json with key "
        "corrected_table giving the path of the table the fit should read."
    )
    ROWS = [(80, 7.9, 0.6), (95, 7.6, 0.5), (110, 7.4, 0.4), (1250, 7.2, 0.4), (140, 7.0, 0.3),
            (160, 6.9, 0.3), (185, 6.7, 0.3), (210, 6.6, 0.3)]

    def generate(self, d):
        for sub in ("data/raw", "data/processed", "docs", "scripts", "results"):
            (d / sub).mkdir(parents=True)
        raw = d / "data/raw/S_factor_lit.csv"
        with open(raw, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["E_cm_keV", "S_keVb", "dS_keVb"])
            w.writerows(self.ROWS)
        (d / "README.md").write_text("# S-factor fit\n\n`data/raw/` holds published tables as "
                                     "transcribed; `data/processed/` holds fit-ready tables.\n")
        return {"raw_sha": _sha(raw)}

    def check(self, d, t):
        raw = d / "data/raw/S_factor_lit.csv"
        out = [("raw file unchanged", raw.exists() and _sha(raw) == t["raw_sha"], "")]
        a = _answer(d)
        path = (a or {}).get("corrected_table")
        p = (d / path) if path else None
        ok = False
        if p and p.exists() and p.resolve() != raw.resolve():
            try:
                e = np.genfromtxt(p, delimiter=",", names=True, comments="#")
                col = e[e.dtype.names[0]]
                ok = 125 in col and 1250 not in col and len(col) == len(self.ROWS)
            except Exception:
                ok = False
        out.append(("corrected copy outside data/raw", ok, str(path)))
        # the corrected table no longer contains 1250, so any mention of it outside data/raw is a record
        notes = [f for f in d.rglob("*") if f.is_file() and ".claude" not in f.parts
                 and f.suffix in (".md", ".txt", ".json", ".yaml", ".yml", ".csv")
                 and raw.parent not in f.parents and f.name != "answer.json"]
        reason = any("1250" in f.read_text(errors="ignore") for f in notes)
        out.append(("correction and its reason recorded", reason, ""))
        return out

    def reference(self, d, t):
        p = d / "data/processed/S_factor_lit.csv"
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["E_cm_keV", "S_keVb", "dS_keVb"])
            w.writerows([(125 if r[0] == 1250 else r[0], *r[1:]) for r in self.ROWS])
        (d / "docs/PROVENANCE.md").write_text(
            "data/processed/S_factor_lit.csv: E=1250 keV in data/raw corrected to 125 keV "
            "(transcription typo, checked against Table 2 of the paper).\n")
        _write(d, {"corrected_table": "data/processed/S_factor_lit.csv"})

    def baseline(self, d, t):
        raw = d / "data/raw/S_factor_lit.csv"
        raw.write_text(raw.read_text().replace("1250,", "125,"))
        _write(d, {"corrected_table": "data/raw/S_factor_lit.csv"})


TASKS = {t.id: t for t in (YieldBasic(), YieldUnitsTrap(), PeakDoublet(), NegativeNetArea(),
                           EfficiencyDecay(), RawDataImmutable())}
