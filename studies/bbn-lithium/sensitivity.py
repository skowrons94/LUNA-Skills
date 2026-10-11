"""Logarithmic sensitivities d ln(X) / d ln(rate) for the BBN abundances."""
import json
import warnings
from multiprocessing import Pool
import numpy as np

warnings.filterwarnings("ignore")
import bbn

RATES = [
    "p_n_to_d", "d_p_to_He3", "d_d_to_n_He3", "d_d_to_p_t", "He3_n_to_p_t",
    "t_d_to_n_He4", "He3_d_to_p_He4", "He3_He4_to_Be7", "t_He4_to_Li7",
    "Be7_n_to_p_Li7", "Be7_n_to_He4_He4", "Be7_d_to_p_He4_He4",
    "Li7_p_to_He4_He4", "Be7_p_to_B8", "d_He4_to_Li6", "Li6_p_to_He4_He3",
    "t_p_to_He4", "He3_t_to_d_He4",
]
EPS = 0.10


def run(job):
    kind, name, f = job
    if kind == "rate":
        return job, bbn.BBN(mult={name: f}).run()
    if kind == "eta":
        return job, bbn.BBN(eta10=6.104 * f).run()
    if kind == "tau":
        old = bbn.TAU_N
        bbn.TAU_N = old * f
        bbn._CACHE.pop(("weak", 3.044), None)
        out = bbn.BBN().run()
        bbn.TAU_N = old
        return job, out
    return job, bbn.BBN().run()


if __name__ == "__main__":
    jobs = [("base", None, 1.0)]
    for r in RATES:
        jobs += [("rate", r, 1 + EPS), ("rate", r, 1 - EPS)]
    jobs += [("eta", None, 1 + EPS), ("eta", None, 1 - EPS),
             ("tau", None, 1 + EPS), ("tau", None, 1 - EPS)]
    with Pool(4) as pool:
        out = dict((tuple(j), r) for j, r in pool.map(run, jobs))
    base = out[("base", None, 1.0)]
    keys = ["Yp", "D/H", "He3/H", "Li7/H"]
    table = {}
    for kind, name in [("rate", r) for r in RATES] + [("eta", None), ("tau", None)]:
        up, dn = out[(kind, name, 1 + EPS)], out[(kind, name, 1 - EPS)]
        lab = name if kind == "rate" else {"eta": "eta (baryon/photon)", "tau": "neutron lifetime"}[kind]
        table[lab] = {k: float(np.log(up[k] / dn[k]) / np.log((1 + EPS) / (1 - EPS)))
                      for k in keys}
    json.dump({"base": {k: float(v) for k, v in base.items()}, "sens": table},
              open("results/sensitivity.json", "w"), indent=1)
    print("base", {k: f"{v:.4g}" for k, v in base.items()})
    print(f"{'rate':28s}" + "".join(f"{k:>9s}" for k in keys))
    for lab, d in sorted(table.items(), key=lambda kv: -abs(kv[1]["Li7/H"])):
        print(f"{lab:28s}" + "".join(f"{d[k]:9.3f}" for k in keys))
