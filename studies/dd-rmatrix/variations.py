"""Systematic variations around the nominal evaluation.

Each variation changes ONE analysis choice relative to the nominal
(cfg = R-matrix model, opts = likelihood/data choices from runs/nominal_opts.json)
and is refitted from scratch (warm-started from the nominal minimum where the
parameter vector is compatible).  Results: runs/var_<name>/result.json.

usage: python3 variations.py [group ...]   (default: all groups)
"""
import copy
import json
import os
import subprocess
import sys
from multiprocessing import Pool

NOM = json.load(open("runs/nominal_opts.json"))
CFG0, OPTS0 = NOM["cfg"], NOM["opts"]
ALL = ["BJ90", "KR87a", "KR87b", "GR95", "LE06", "AR54", "DA53", "PR54", "BO56",
       "YI73", "CH56", "HO01"]


def v(group, name, cfg=None, opts=None):
    c = copy.deepcopy(CFG0); c.update(cfg or {})
    o = copy.deepcopy(OPTS0); o.update(opts or {})
    return dict(group=group, name=name, cfg=c, opts=o)


VARS = [v("nominal", "nominal")]
# ---- R-matrix model ---------------------------------------------------
for a in (4.5, 5.0, 7.0, 8.0):
    VARS.append(v("model:radius_dd", f"a_dd={a}", {"a_dd": a}))
for a in (4.0, 6.0):
    VARS.append(v("model:radius_exit", f"a_pt=a_nh={a}", {"a_pt": a, "a_nh": a}))
VARS += [
    v("model:poles", "pole at 26 MeV", {"poles": [26.0]}),
    v("model:poles", "pole at 40 MeV", {"poles": [40.0]}),
    v("model:poles", "two poles per J (28, 40 MeV)", {"poles": [28.0, 40.0]}),
    v("model:poles", "free pole energies (20-60 MeV)", {"free_E": True, "poles": [30.0]}),
    v("model:partial_waves", "+ d-wave entrance", {"jpi": "dwave"}),
    v("model:independent", "polynomial S, deg 4", {"model": "poly", "degree": 4}),
    v("model:independent", "polynomial S, deg 6", {"model": "poly", "degree": 6}),
]
# ---- data selection ----------------------------------------------------
VARS.append(v("data:selection", "core only (BJ90,KR87,GR95,LE06)",
              opts={"exps": ["BJ90", "KR87a", "KR87b", "GR95", "LE06"]}))
VARS.append(v("data:selection", "+ THM (Tumino)", opts={"exps": ALL + ["TU14"]}))
for ex in ALL:
    VARS.append(v("data:jackknife", f"without {ex}", opts={"exps": [e for e in ALL if e != ex]}))
VARS.append(v("data:outliers", "keep CH56 outlier", opts={"drop_points": []}))
# ---- error model --------------------------------------------------------
VARS += [
    v("errors:inflation", "no Birge inflation", opts={"err_inflate": {}}),
    v("errors:inflation", "no norm-prior scaling", opts={"norm_scale": 1.0}),
    v("errors:inflation", "quoted errors only (no inflation at all)",
      opts={"err_inflate": {}, "norm_scale": 1.0}),
    v("errors:inflation", "Birge factors from R-matrix iteration",
      opts=NOM["opts_rmatrix_selfconsistent"]),
    v("errors:arnold", "AR54 'assigned' (2x) errors", opts={"alt_errors": ["AR54"]}),
    v("errors:energy", "no energy-calibration errors", opts={"dE_scale": 0.0}),
    v("errors:energy", "energy-calibration errors x2", opts={"dE_scale": 2.0}),
]
# ---- normalisation priors ---------------------------------------------
no = OPTS0.get("norm_override", {})
VARS += [
    v("norm:BJ90", "BJ90 scale 3 %", opts={"norm_override": {**no, "BJ90": 0.03}}),
    v("norm:BJ90", "BJ90 scale free", opts={"norm_override": {**no, "BJ90": None}}),
    v("norm:LE06", "LE06 scale 1 %", opts={"norm_override": {**no, "LE06": 0.01}}),
    v("norm:LE06", "LE06 scale 4 %", opts={"norm_override": {**no, "LE06": 0.04}}),
    v("norm:legacy", "legacy scales 10 %", opts={"norm_override": {**no, **{e: 0.10 for e in
                                                ["AR54", "DA53", "PR54", "BO56", "YI73", "CH56"]}}}),
    v("norm:all", "all scales free (shape only)", opts={"norm_override": {e: None for e in ALL}}),
]
# ---- screening and fit window --------------------------------------------
VARS += [
    v("screening", "U_e = 0", opts={"Ue_eV": 0.0}),
    v("screening", "U_e = 30 eV", opts={"Ue_eV": 30.0}),
    v("window", "E_cm <= 300 keV", opts={"emax": 300.0}),
    v("window", "E_cm >= 10 keV", opts={"emin": 10.0}),
]


def safe(name):
    return "var_" + "".join(c if c.isalnum() else "_" for c in name)


def run(var):
    d = safe(var["name"])
    if os.path.exists(f"runs/{d}/result.json"):
        return var["name"], "cached"
    env = {**os.environ, "OMP_NUM_THREADS": "1", "DD_START": "runs/var_nominal/best.npy",
           "DD_NFEV": "1500"}
    nst = "2"
    if var["name"] == "nominal":
        nst = "8"
    p = subprocess.run([sys.executable, "-W", "ignore", "run_fit.py", d, json.dumps(var["cfg"]),
                        json.dumps(var["opts"]), nst], env=env, capture_output=True, text=True)
    open(f"runs/{d}.log", "w").write(p.stdout + p.stderr)
    return var["name"], p.stdout.strip().splitlines()[-3] if p.stdout.strip() else p.stderr[-300:]


if __name__ == "__main__":
    groups = sys.argv[1:]
    todo = [x for x in VARS if not groups or x["group"].split(":")[0] in groups or x["name"] in groups]
    json.dump(VARS, open("runs/variations.json", "w"), indent=1)
    # nominal first (its minimum warm-starts the others)
    nom = [x for x in todo if x["name"] == "nominal"]
    for x in nom:
        print(run(x), flush=True)
    with Pool(4) as pool:
        for out in pool.imap_unordered(run, [x for x in todo if x["name"] != "nominal"]):
            print(out, flush=True)
