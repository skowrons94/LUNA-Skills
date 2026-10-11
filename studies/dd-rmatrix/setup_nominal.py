"""Nominal analysis choices, determined self-consistently:

1. per-experiment Birge factors  b_k = sqrt(max(1, chi2_k / N_k))  on the
   uncorrelated point errors (data inconsistency beyond quoted errors);
2. a global scale factor on the normalisation priors,
   S_n = sqrt(max(1, chi2_prior / N_constrained))  (PDG-style), because the
   fitted normalisations are mutually inconsistent at their quoted values.

Both are iterated with the nominal R-matrix model until stable and stored in
runs/nominal_opts.json.  A model-independent (polynomial) iteration is run as a
check that the factors are not artefacts of the R-matrix model.
"""
import json
import warnings

warnings.filterwarnings("ignore")
import numpy as np

import fitter
import make_azr

NOMINAL_CFG = dict(free_E=False, poles=[28.0, 40.0])


def iterate(make_fit, n_iter=3, start=None):
    opts = {"err_inflate": {}, "norm_scale": 1.0}
    z = None
    hist = []
    for it in range(n_iter):
        f = make_fit(opts)
        b = f.fit(n_starts=6 if it == 0 else 2, x_start=None if z is None else z[:len(f.x0)])
        z = b["z"]
        s = f.summary(z)
        chi = {}
        for key, (c2, n) in s["per_exp"].items():
            ex = key.rsplit("_", 1)[0]
            a, m = chi.get(ex, (0.0, 0))
            chi[ex] = (a + c2, m + n)
        # undo the current inflation to get the raw per-experiment ratio
        new_inf = {}
        for ex, (c2, n) in chi.items():
            cur = opts["err_inflate"].get(ex, 1.0)
            new_inf[ex] = float(np.sqrt(max(1.0, c2 / n)) * cur)
        ncon = sum(1 for d in f.norm_prior if d is not None)
        sn = float(np.sqrt(max(1.0, s["chi2_prior"] / ncon)) * opts["norm_scale"])
        hist.append(dict(chi2=s["chi2_data"], chi2_prior=s["chi2_prior"], npts=s["npts"],
                         inflate=new_inf, norm_scale=sn, norms=s["norms"]))
        print(f"iter {it}: chi2 {s['chi2_data']:.1f}/{s['npts']}  prior {s['chi2_prior']:.1f}/{ncon}"
              f"  norm_scale -> {sn:.2f}")
        print("   inflate:", {k: round(v, 2) for k, v in new_inf.items()})
        opts = {"err_inflate": new_inf, "norm_scale": sn}
        f.close()
    return opts, hist


if __name__ == "__main__":
    make_azr.write_project(NOMINAL_CFG, "runs/nom_setup")
    print("== R-matrix (nominal model)")
    opts_r, hist_r = iterate(lambda o: fitter.DDFit("runs/nom_setup", o))
    print("== polynomial degree 5 (model-independent check)")
    opts_p, hist_p = iterate(lambda o: fitter.PolyFit("runs/nom_setup", o, degree=5))
    json.dump({"cfg": NOMINAL_CFG, "opts": opts_r, "history_rmatrix": hist_r,
               "opts_poly": opts_p, "history_poly": hist_p},
              open("runs/nominal_opts.json", "w"), indent=1)
