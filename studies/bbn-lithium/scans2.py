"""(1) most favourable resonance: theta^2 = 1, wide exit channel, large radius;
(2) late neutron injection (decaying particle) grid: Li/H and D/H;
(3) eta scan (Schramm plot)."""
import json
import warnings
from multiprocessing import Pool
import numpy as np

warnings.filterwarnings("ignore")
import bbn
import lithium_fix as L


def res_job(arg):
    x, Er, gout, a = arg
    rate, gin, _ = L.resonance_rate(x, Er, 1.0, gamma_out=gout, a=a)
    T9 = np.exp(bbn.BBN.LNT9)
    vals = np.array([rate(t * 1e9) for t in T9])
    func = lambda TK, v=vals: float(np.exp(np.interp(np.log(TK / 1e9), bbn.BBN.LNT9,
                                                      np.log(np.maximum(v, 1e-300)))))
    r = bbn.BBN(extra=[bbn.NetRate(f"res_{x}", ["be7", x], L.PARTNERS[x][4], func)]).run()
    return {"x": x, "Er": Er, "Gout": gout, "a": a, "Li7/H": float(r["Li7/H"]),
            "D/H": float(r["D/H"])}


def inj_job(arg):
    Yx, tau = arg
    r = bbn.BBN(inject=(Yx, tau)).run()
    return {"Yx": Yx, "tau": tau, **{k: float(v) for k, v in r.items()}}


def eta_job(e):
    return {"eta10": e, **{k: float(v) for k, v in bbn.BBN(eta10=e).run().items()}}


if __name__ == "__main__":
    ER = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.6]
    res_jobs = [(x, e, g, a) for x in ["d", "he3", "t"] for e in ER
                for g in [0.05, 0.3, 1.0] for a in [None, 10.0]]
    inj_jobs = [(y, t) for y in np.logspace(-6.5, -4, 11) for t in
                [100, 300, 600, 1000, 2000, 4000, 1e4]]
    eta_jobs = list(np.linspace(2.0, 10.0, 17))
    with Pool(4) as p:
        R = p.map(res_job, res_jobs)
        I = p.map(inj_job, inj_jobs)
        E = p.map(eta_job, eta_jobs)
    json.dump({"resonance_max": R, "injection": I, "eta": E},
              open("results/scans2.json", "w"), indent=1, default=float)
    for x in ["d", "he3", "t"]:
        sub = [r for r in R if r["x"] == x]
        best = min(sub, key=lambda r: r["Li7/H"])
        print(x, "best", best)
    ok = [i for i in I if i["Li7/H"] < 2.2e-10]
    print("injection reaching Li/H<2.2e-10: min D/H =",
          min(i["D/H"] for i in ok) if ok else None)
