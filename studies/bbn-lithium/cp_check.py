"""Cross-check of the 7Be+d -> 9B* resonance proposal (Cyburt & Pospelov 2012)
and of the measured 9B level (E_r = 310 keV, Gamma = 81 keV; Kirsebom & Davids
2011), with several width/spin assumptions."""
import json
import warnings
from multiprocessing import Pool
import numpy as np

warnings.filterwarnings("ignore")
import bbn
import lithium_fix as L

MU = 7.016929 * 2.014102 / (7.016929 + 2.014102)


def li(args):
    Er, Gd, Gout, J, a, const = args
    om = (2 * J + 1) / (4 * 3)
    P0 = L.penetrability(Er, 4, 1, MU, a)

    def sig(E):
        k2 = 2 * MU * 931.494 * E / 197.327**2
        Gin = Gd if const else Gd * L.penetrability(E, 4, 1, MU, a) / P0
        return np.pi / k2 * om * Gin * Gout / ((E - Er)**2 + (Gin + Gout)**2 / 4) * 1e-26

    Eg = np.linspace(1e-4, 3, 6000)
    sg = np.array([sig(e) for e in Eg])
    mug = MU * 1.66054e-24
    v = []
    for t in np.exp(bbn.BBN.LNT9):
        kT = t * 1e9 * bbn.K_MEV
        v.append(6.02214e23 * np.sqrt(8 / (np.pi * mug)) * (kT * 1.602177e-6) ** -1.5
                 * np.trapezoid(sg * Eg * np.exp(-Eg / kT), Eg) * 1.602177e-6**2)
    v = np.maximum(v, 1e-300)
    f = lambda TK: float(np.exp(np.interp(np.log(TK / 1e9), bbn.BBN.LNT9, np.log(v))))
    r = bbn.BBN(extra=[bbn.NetRate("res_d", ["be7", "d"], ["p", "he4", "he4"], f)]).run()
    return {"Er": Er, "Gd": Gd, "Gout": Gout, "J": J, "a": a, "const_width": const,
            "Li7/H": float(r["Li7/H"]), "D/H": float(r["D/H"])}


if __name__ == "__main__":
    cases = [
        (0.17, 0.04, 0.04, 1.5, 10.0, False),   # CP-like, s-wave 3/2
        (0.17, 0.04, 0.04, 2.5, 10.0, False),   # CP spin 5/2
        (0.17, 0.04, 0.20, 2.5, 10.0, False),   # + wide exit channel
        (0.17, 0.04, 0.20, 2.5, 10.0, True),    # + energy-independent Gamma_d
        (0.20, 0.04, 0.20, 2.5, 10.0, True),
        (0.22, 0.04, 0.20, 2.5, 10.0, True),
        # measured level, Gamma_tot = 81 keV; Gamma_d as large as allowed
        (0.31, 0.04, 0.041, 2.5, 10.0, False),
        (0.31, 0.06, 0.021, 2.5, 10.0, False),
    ]
    with Pool(4) as p:
        out = p.map(li, cases)
    json.dump(out, open("results/cp_check.json", "w"), indent=1)
    for o in out:
        print(o)
