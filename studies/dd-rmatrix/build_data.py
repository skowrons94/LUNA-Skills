"""Curated d+d data set with an explicit systematic-uncertainty budget.

Reads data/exfor/dd_sets.json (exfor_parse.py output) and writes
data/catalog.json:

  experiments: {key: {norm_prior (fractional, None = free), dE_lab (keV or
                frac), notes, reactions, entries, tier}}
  points:      [{exp, reac ('dp'|'dn'), E (keV c.m.), sigma (b), err (b,
                uncorrelated point-to-point), err_alt (b, alternative
                assignment, if any)}]

Conventions
  * E is the centre-of-mass energy; EXFOR 'EN' is the deuteron lab energy
    (E_cm = E_lab / 2, checked against Brown & Jarmie's own S-factor column).
  * Point errors are the uncorrelated part only.  Overall scale errors go into
    one normalisation per experiment, shared by d(d,p) and d(d,n) when they come
    from the same measurement (same target thickness and charge).
  * Data are stored as measured (screened).  Electron screening is applied in
    the fitter, so U_e can be varied as a systematic.
"""
import json
import numpy as np

S = {s["entry"]: s for s in json.load(open("data/exfor/dd_sets.json"))}
TWO_PI_ETA = lambda E: 31.29 * np.sqrt(1.00728 / E)        # E keV c.m., Z1Z2 = 1

EXPS = {
    # key: norm prior (fraction; None -> free), energy uncertainty, tier, notes
    "BJ90": dict(norm=0.013, dE=("abs_lab_keV", 0.015), tier="core",
                 ref="Brown & Jarmie, PRC 41, 1391 (1990)",
                 notes="cryogenic windowless gas target; 1.3 % scale shared by dp/dn; "
                       "point errors relative (EXFOR C0109004/5)"),
    "KR87a": dict(norm=0.064, dE=("frac", 0.005), tier="core",
                  ref="Krauss et al., NPA 465, 150 (1987), jet target setup 1",
                  notes="6.4 % absolute normalisation. EXFOR says the dn point errors include it, "
                        "but they are 1-2 %, so they are taken as statistical"),
    "KR87b": dict(norm=0.081, dE=("frac", 0.005), tier="core",
                  ref="Krauss et al., NPA 465, 150 (1987), setup 2",
                  notes="6.4 % (shared with KR87a) + 5 % beam/jet alignment"),
    "GR95": dict(norm=None, dE=("abs_cm_keV", 0.02), tier="core",
                 ref="Greife et al., ZPA 351, 107 (1995), LUNA gas target",
                 notes="scale normalised by the authors to Bosch & Hale: no independent "
                       "normalisation -> free; dominated by electron screening"),
    "LE06": dict(norm=0.02, dE=("frac", 0.005), tier="core",
                 ref="Leonard et al., PRC 73, 045801 (2006)",
                 notes="CD4 targets; point errors from the authors' error matrix; "
                       "2 % scale ASSUMED (not in EXFOR) and varied"),
    "AR54": dict(norm=0.03, dE=("frac", 0.005), tier="legacy",
                 ref="Arnold et al., PR 93, 483 (1954)",
                 notes="errors are total 'standard' errors; authors' 'assigned' = 2x "
                       "(alternative)"),
    "DA53": dict(norm=0.05, dE=("frac", 0.01), tier="legacy",
                 ref="Davenport et al., PRSA 216, 66 (1953)", notes="relative errors; "
                 "scale ASSUMED 5 %"),
    "PR54": dict(norm=0.05, dE=("frac", 0.01), tier="legacy",
                 ref="Preston et al., PRSA 226, 206 (1954)", notes="relative errors; scale ASSUMED 5 %"),
    "BO56": dict(norm=0.03, dE=("frac", 0.006), tier="legacy",
                 ref="Booth et al., PPSA 69, 265 (1956)", notes="2 energies; errors include systematics"),
    "YI73": dict(norm=0.05, dE=("abs_lab_keV", 1.5), tier="legacy",
                 ref="Ying et al., NPA 206, 481 (1973)",
                 notes="NO errors in EXFOR: 3 % point + 5 % scale ASSUMED"),
    "CH56": dict(norm=0.05, dE=("frac", 0.01), tier="legacy",
                 ref="Chagnon & Owen, PR 101, 1798 (1956)",
                 notes="no point errors: 5 % ASSUMED; lowest point (250 keV lab) is a 35 % outlier"),
    "HO01": dict(norm=0.02, dE=("frac", 0.01), tier="legacy",
                 ref="Hofstee et al., NPA 688, 527c (2001)", notes="2 points; 5 % stat, 2 % sys"),
    "TU14": dict(norm=None, dE=("frac", 0.0), tier="thm",
                 ref="Tumino et al. (THM), EXFOR D0651",
                 notes="indirect; scale fixed to direct data by construction -> free"),
}


def add(points, exp, reac, E_cm, sig, err, err_alt=None):
    for k in range(len(E_cm)):
        if not (np.isfinite(E_cm[k]) and np.isfinite(sig[k]) and sig[k] > 0 and np.isfinite(err[k])):
            continue
        p = dict(exp=exp, reac=reac, E=float(E_cm[k]), sigma=float(sig[k]), err=float(err[k]))
        if err_alt is not None:
            p["err_alt"] = float(err_alt[k])
        points.append(p)


def col(entry, i):
    return np.array([r[i] if r[i] is not None else np.nan for r in S[entry]["rows"]], float)


def sfactor_to_sigma(E, Sk):        # S in keV b -> sigma in b
    return Sk / E * np.exp(-TWO_PI_ETA(E))


pts = []
# Brown & Jarmie: lab keV, mb, relative % error
for e, r in (("C0109004", "dp"), ("C0109005", "dn")):
    E = col(e, 0) / 2; s = col(e, 1) * 1e-3; add(pts, "BJ90", r, E, s, s * col(e, 3) / 100)
# Krauss: E_cm keV, S keV b
for e, r, exp_, deconv in (("A0409002", "dp", "KR87a", False), ("A0409003", "dn", "KR87a", False),
                           ("A0409004", "dp", "KR87b", False), ("A0409005", "dn", "KR87b", False)):
    E = col(e, 0); Sk = col(e, 1); dS = col(e, 2)
    dS = np.where(np.isfinite(dS), dS, 0.01 * Sk)    # "statistical error < 1 % except where quoted"
    if deconv:   # point errors include the 6.4 % normalisation
        dS = np.sqrt(np.maximum(dS**2 - (0.064 * Sk)**2, (0.005 * Sk)**2))
    add(pts, exp_, r, E, sfactor_to_sigma(E, Sk), sfactor_to_sigma(E, dS))
# Greife (gas, far geometry, table 4): E_cm keV, S keV b, total error
E = col("O1171007", 0); Sk = col("O1171007", 1); dS = col("O1171007", 2)
add(pts, "GR95", "dp", E, sfactor_to_sigma(E, Sk), sfactor_to_sigma(E, dS))
# Leonard: lab keV, mb
for e, r in (("C1499002", "dp"), ("C1499003", "dn")):
    E = col(e, 0) / 2; add(pts, "LE06", r, E, col(e, 1) * 1e-3, col(e, 2) * 1e-3)
# Arnold: lab keV, mb, % (standard, assigned)
for e, r in (("C0018005", "dp"), ("C0018006", "dn")):
    E = col(e, 0) / 2; s = col(e, 1) * 1e-3
    add(pts, "AR54", r, E, s, s * col(e, 2) / 100, s * col(e, 3) / 100)
# Davenport: lab MeV, mb
E = col("A1152002", 0) * 1e3 / 2; add(pts, "DA53", "dp", E, col("A1152002", 1) * 1e-3, col("A1152002", 2) * 1e-3)
# Preston: lab MeV, mb
for e, r in (("A1142002", "dn"), ("A1142003", "dp")):
    E = col(e, 0) * 1e3 / 2; add(pts, "PR54", r, E, col(e, 1) * 1e-3, col(e, 2) * 1e-3)
# Booth: lab keV, mb
for e, r in (("C0033004", "dn"), ("C0033005", "dp")):
    E = col(e, 0) / 2; add(pts, "BO56", r, E, col(e, 1) * 1e-3, col(e, 2) * 1e-3)
# Ying: lab MeV, mb, no errors
for e, r in (("A1076006", "dn"), ("A1076008", "dp")):
    E = col(e, 0) * 1e3 / 2; s = col(e, 1) * 1e-3; add(pts, "YI73", r, E, s, 0.03 * s)
# Chagnon: lab MeV, mb, no errors
E = col("A1192002", 0) * 1e3 / 2; s = col("A1192002", 1) * 1e-3; add(pts, "CH56", "dn", E, s, 0.05 * s)
# Hofstee: E_cm keV, mb, % stat
E = col("C1511002", 0); s = col("C1511002", 1) * 1e-3; add(pts, "HO01", "dn", E, s, s * col("C1511002", 2) / 100)
# Tumino THM: E_cm MeV, two S-factor columns (dp), one (dn)
E = col("D0651002", 0) * 1e3
for i in (1, 3):
    Sk = col("D0651002", i); dS = col("D0651002", i + 1)
    add(pts, "TU14", "dp", E, sfactor_to_sigma(E, Sk), sfactor_to_sigma(E, dS))
E = col("D0651003", 0) * 1e3
add(pts, "TU14", "dn", E, sfactor_to_sigma(E, col("D0651003", 1)), sfactor_to_sigma(E, col("D0651003", 2)))

json.dump({"experiments": EXPS, "points": pts}, open("data/catalog.json", "w"), indent=0)
print(f"{'exp':6s} {'tier':7s} {'reac':5s} {'n':>3s} {'E_cm range (keV)':>18s}  norm prior")
for k, v in EXPS.items():
    for r in ("dp", "dn"):
        P = [p for p in pts if p["exp"] == k and p["reac"] == r]
        if P:
            E = [p["E"] for p in P]
            print(f"{k:6s} {v['tier']:7s} {r:5s} {len(P):3d} {min(E):8.2f}-{max(E):8.2f}   "
                  f"{'free' if v['norm'] is None else f'{100*v['norm']:.1f} %'}")
print("total points:", len(pts))
