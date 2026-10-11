"""Combine nominal fit, MCMC posterior and systematic variations into the
d(d,n)3He and d(d,p)t rates with an itemised uncertainty budget, and propagate
to BBN (D/H, 3He/H, eta from D/H).

Budget convention (per T9):
  stat        68 % posterior half-width (MCMC; Laplace propagation as check).
              Includes Birge-inflated point errors and PDG-scaled norm priors.
  influence   leave-one-experiment-out shifts beyond what the error model
              predicts: sum_i max(0, d_i^2 - (s_-i^2 - s^2)), s from Laplace.
  group g     max |R_var / R_nom - 1| over the variations of g.
  excluded    'norm:all' (absolute scale undefined: a diagnostic, not an
              uncertainty) and '+ THM' (indirect data, reported separately).
  Polynomial (model-independent) fits are compared only where the data
  constrain them: sigma_poly for E <= 350 keV, nominal R-matrix above.
  total       stat (+) influence (+) all included groups, in quadrature.
"""
import json
import os
import warnings

warnings.filterwarnings("ignore")
import numpy as np

import rates

VARS = json.load(open("runs/variations.json"))
T9 = rates.T9_GRID
OUT = "results"
os.makedirs(OUT, exist_ok=True)


def safe(name):
    return "var_" + "".join(c if c.isalnum() else "_" for c in name)


NOMR = json.load(open("runs/var_nominal/result.json"))
SPLICE_KEV = 350.0
EXCLUDE = {"norm:all", "data:thm", "norm:BJ90"}   # BJ90 scale: covered by the influence term


def load_rates(name):
    p = f"runs/{safe(name)}/result.json"
    if not os.path.exists(p):
        return None
    r = json.load(open(p))
    E = np.array(r["grid"])
    sdp, sdn = np.array(r["dp"]), np.array(r["dn"])
    if r["cfg"].get("model") == "poly":          # splice above the data
        hi = E > SPLICE_KEV
        sdp[hi] = np.array(NOMR["dp"])[hi]
        sdn[hi] = np.array(NOMR["dn"])[hi]
    return dict(dp=rates.rate(E, sdp, T9), dn=rates.rate(E, sdn, T9),
                summary=r["summary"], E=E, sdp=sdp, sdn=sdn)


def main():
    nom = load_rates("nominal")
    table, groups = [], {}
    for v in VARS:
        if v["name"] == "nominal":
            continue
        r = load_rates(v["name"])
        if r is None:
            continue
        s = r["summary"]
        grp = "data:thm" if "THM" in v["name"] else v["group"]
        row = dict(group=grp, name=v["name"],
                   chi2=s["chi2_data"], chi2_prior=s["chi2_prior"], npts=s["npts"], npar=s["npar"],
                   d_dp=(r["dp"] / nom["dp"] - 1).tolist(), d_dn=(r["dn"] / nom["dn"] - 1).tolist())
        table.append(row)
        groups.setdefault(grp, []).append(row)
    mc = np.load("runs/mcmc/rates.npz") if os.path.exists("runs/mcmc/rates.npz") else None
    budget = {}
    for key in ("dp", "dn"):
        b = {}
        if mc is not None:
            q = np.percentile(mc[key], [16, 50, 84], axis=0)
            b["stat"] = ((q[2] - q[0]) / 2 / nom[key]).tolist()
            b["mcmc_median_shift"] = (q[1] / nom[key] - 1).tolist()
        lap = json.load(open("results/laplace_stat.json"))
        s0 = np.array(lap["runs/var_nominal"][key])
        b["stat_laplace"] = s0.tolist()
        infl = {}
        for g, rows in groups.items():
            D = np.array([r[f"d_{key}"] for r in rows])
            if g == "data:jackknife":
                exc = np.zeros(len(T9))
                for r in rows:
                    sl = np.array(lap.get("runs/" + safe(r["name"]), {}).get(key, s0))
                    d = np.array(r[f"d_{key}"])
                    expv = np.clip(sl**2 - s0**2, 0, None)
                    infl[r["name"]] = (d / np.sqrt(np.maximum(expv, 1e-8))).tolist()
                    exc += np.clip(d**2 - expv, 0, None)
                b["influence (jackknife excess)"] = np.sqrt(exc).tolist()
            else:
                b[g] = np.max(np.abs(D), axis=0).tolist()
        b["_influence_z"] = infl
        skip = {"mcmc_median_shift", "stat_laplace", "_influence_z"} | EXCLUDE
        if "stat" not in b:
            b["stat"] = b["stat_laplace"]
        tot = np.sqrt(sum(np.array(v)**2 for k, v in b.items() if k not in skip))
        b["total"] = tot.tolist()
        budget[key] = b
    # REACLIB comparison
    rl = {k: np.array([rates.reaclib(rates.REACLIB_NAMES[k]).eval(t * 1e9) for t in T9])
          for k in ("dp", "dn")}
    out = dict(T9=T9.tolist(), nominal={k: nom[k].tolist() for k in ("dp", "dn")},
               reaclib={k: rl[k].tolist() for k in rl}, budget=budget, variations=table,
               nominal_summary=nom["summary"])
    # ---------- BBN propagation
    import bbn
    base = bbn.BBN().run()
    ours = rates.run_bbn({"dp": nom["dp"], "dn": nom["dn"]})
    def band(sign, which=("dp", "dn"), comp="total"):
        v = {}
        for k in ("dp", "dn"):
            u = np.minimum(np.array(budget[k][comp]), 0.5)
            v[k] = nom[k] * (1 + sign * u) if k in which else nom[k]
        return rates.run_bbn(v)
    up, dn_ = band(+1), band(-1)
    out["bbn"] = dict(reaclib=base, this_work=ours, plus1sigma=up, minus1sigma=dn_,
                      stat_plus=band(+1, comp="stat"), stat_minus=band(-1, comp="stat"))
    # scenarios: which dataset sets the scale
    scen = {}
    for name in ("without KR87b", "without BJ90", "BJ90 scale free", "without LE06", "+ THM (Tumino)",
                 "core only (BJ90,KR87,GR95,LE06)", "free pole energies (20-60 MeV)"):
        r = load_rates(name)
        if r is not None:
            scen[name] = rates.run_bbn({"dp": r["dp"], "dn": r["dn"]})["D/H"]
    out["bbn"]["scenarios_DH"] = scen
    # eta from observed D/H with our rates (log-linear solve, 2 iterations)
    DH_OBS = 2.527e-5
    eta, dh = 6.104, ours["D/H"]
    for _ in range(3):
        eta *= (dh / DH_OBS) ** (1 / 1.6)
        dh = rates.run_bbn({"dp": nom["dp"], "dn": nom["dn"]}, eta10=eta)["D/H"]
    out["eta10_from_DH"] = eta
    json.dump(out, open(f"{OUT}/dd_evaluation.json", "w"), indent=1, default=float)

    # ---------- printout
    sel = [i for i, t in enumerate(T9) if t in (0.1, 0.3, 0.5, 0.8, 1.0)]
    print("rate (cm^3/mol/s) and ratio to REACLIB (gi17/go17):")
    for k in ("dp", "dn"):
        print(f" {k}: " + "  ".join(f"T9={T9[i]}: {nom[k][i]:.4g} ({nom[k][i] / rl[k][i]:.3f})" for i in sel))
    print("\nbudget (%), T9 =", [T9[i] for i in sel])
    for k in ("dp", "dn"):
        print(f" {k}")
        for g, v in budget[k].items():
            if g.startswith("_"):
                continue
            tag = " (not in total)" if g in EXCLUDE or g in ("stat_laplace", "mcmc_median_shift") else ""
            print(f"   {g:30s} " + " ".join(f"{100 * v[i]:7.2f}" for i in sel) + tag)
        print("   influence z (T9=0.5):", {n: round(z[sel[2]], 1) for n, z in budget[k]["_influence_z"].items()})
    print("\nBBN:", {k: f"{v:.4e}" for k, v in ours.items() if k in ("D/H", "He3/H", "Yp")},
          " REACLIB rates:", {k: f"{v:.4e}" for k, v in base.items() if k in ("D/H", "He3/H")})
    print("D/H band (total):", f"{up['D/H']:.4e} .. {dn_['D/H']:.4e}",
          " (stat only):", f"{out['bbn']['stat_plus']['D/H']:.4e} .. {out['bbn']['stat_minus']['D/H']:.4e}",
          " eta10 from D/H:", f"{eta:.4f}")
    print("D/H scenarios:", {k: f"{v:.4e}" for k, v in out["bbn"]["scenarios_DH"].items()})


if __name__ == "__main__":
    main()


def write_table():
    ev = json.load(open(f"{OUT}/dd_evaluation.json"))
    lines = ["# d+d thermonuclear rates, this evaluation (R-matrix, AZURE2/pyazr)",
             "# N_A<sigma v> in cm^3 mol^-1 s^-1; uncertainties are 1 sigma, relative (%)",
             "# columns: T9  rate_dp  stat_dp%  total_dp%  ratio_dp/REACLIB  rate_dn  stat_dn%  total_dn%  ratio_dn/REACLIB"]
    for i, t in enumerate(ev["T9"]):
        row = [f"{t:6.3f}"]
        for k in ("dp", "dn"):
            r = ev["nominal"][k][i]
            row += [f"{r:11.4e}", f"{100 * ev['budget'][k]['stat'][i]:6.2f}",
                    f"{100 * ev['budget'][k]['total'][i]:6.2f}", f"{r / ev['reaclib'][k][i]:7.4f}"]
        lines.append("  ".join(row))
    open(f"{OUT}/dd_rates_table.txt", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    write_table()
