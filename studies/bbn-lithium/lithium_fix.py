"""Can a nuclear-physics change bring BBN 7Li/H down to the Spite plateau?

Part A: global multipliers on 7Be/7Li producing and destroying channels.
Part B: a hypothetical new s-wave resonance in 7Be + x (x = n, d, t, 3He),
        single-level Breit-Wigner with an energy-dependent entrance width
        Gamma_in(E) = 2 P_l(E) theta^2 gamma_W^2 (Coulomb penetrability,
        Wigner limit gamma_W^2 = 3 hbar^2 / (2 mu a^2)); thermally averaged
        numerically.  For each resonance energy we find the dimensionless
        reduced width theta^2 that gives 7Li/H = 1.6e-10 and check D/H.
"""
import json
import warnings
from multiprocessing import Pool
import numpy as np
import mpmath as mp
from scipy.integrate import quad
from scipy.optimize import brentq

warnings.filterwarnings("ignore")
import bbn

LI_OBS, LI_OBS_ERR = 1.6e-10, 0.3e-10          # Sbordone et al. 2010
DH_OBS, DH_OBS_ERR = 2.527e-5, 0.030e-5        # Cooke et al. 2018
AMU_MEV = 931.494
HBARC_FM = 197.327
NA = 6.02214076e23

# ---------------------------------------------------------------- Part A
CHANNELS_A = {
    "Be7_n_to_p_Li7": "7Be(n,p)7Li",
    "Be7_n_to_He4_He4": "7Be(n,a)4He",
    "Be7_d_to_p_He4_He4": "7Be(d,p)2a",
    "He3_He4_to_Be7": "3He(a,g)7Be",
    "Li7_p_to_He4_He4": "7Li(p,a)4He",
}
FACTORS = [0.1, 0.2, 0.33, 0.5, 2, 5, 10, 30, 100, 300, 1000]


def job_a(arg):
    name, f = arg
    return name, f, bbn.BBN(mult={name: f}).run()


# ---------------------------------------------------------------- Part B
PARTNERS = {   # x : (Z, A, mass excess-free mass [u], spin, products)
    "n":   (0, 1, 1.008665, 0.5, ["p", "li7"]),          # 8Be* -> p + 7Li
    "d":   (1, 2, 2.014102, 1.0, ["p", "he4", "he4"]),   # 9B*  -> p + 2a
    "t":   (1, 3, 3.016049, 0.5, ["he4", "li6"]),        # 10B* -> a + 6Li
    "he3": (2, 3, 3.016029, 0.5, ["p", "p", "he4", "he4"]),  # 10C* -> 2p + 2a
}
M_BE7, Z_BE7, J_BE7 = 7.016929, 4, 1.5
J_RES = {"n": 1.0, "d": 1.5, "t": 1.0, "he3": 1.0}   # s-wave: |J_be7 - j_x| ..


def penetrability(E, Z1, Z2, mu, a, l=0):
    """Coulomb penetrability P_l = rho / (F^2 + G^2); E in MeV, a in fm."""
    k = np.sqrt(2 * mu * AMU_MEV * E) / HBARC_FM
    rho = k * a
    if Z1 * Z2 == 0:
        return rho if l == 0 else rho**3 / (1 + rho**2)
    eta = Z1 * Z2 * 1.43996 * mu * AMU_MEV / (HBARC_FM**2 * k)
    F = mp.coulombf(l, eta, rho)
    G = mp.coulombg(l, eta, rho)
    return float(rho / (F**2 + G**2))


def resonance_rate(x, Er, theta2, gamma_out=0.05, a=None):
    """N_A<sigma v>(T) [cm^3/mol/s] for a 7Be + x s-wave resonance."""
    Z, A, m, jx, _ = PARTNERS[x]
    mu = M_BE7 * m / (M_BE7 + m)
    if a is None:
        a = 1.4 * (7 ** (1 / 3) + A ** (1 / 3))
    gW2 = 3 * HBARC_FM**2 / (2 * mu * AMU_MEV * a**2)          # MeV
    omega = (2 * J_RES[x] + 1) / ((2 * J_BE7 + 1) * (2 * jx + 1))

    def sigma(E):    # cm^2
        G_in = 2 * penetrability(E, Z_BE7, Z, mu, a) * theta2 * gW2
        G = G_in + gamma_out
        k2 = 2 * mu * AMU_MEV * E / HBARC_FM**2                   # fm^-2
        return np.pi / k2 * omega * G_in * gamma_out / ((E - Er)**2 + G**2 / 4) * 1e-26

    Eg = np.concatenate([np.linspace(1e-4, max(Er - 0.2, 1e-3), 150),
                         np.linspace(max(Er - 0.2, 1e-3), Er + 0.2, 600),
                         np.linspace(Er + 0.2, 4.0, 150)])
    Eg = np.unique(Eg)
    sg = np.array([sigma(E) for E in Eg])

    def rate(TK):
        kT = TK * bbn.K_MEV
        w = sg * Eg * np.exp(-Eg / kT)
        integral = np.trapezoid(w, Eg)                        # cm^2 MeV^2
        # <sv> = sqrt(8/(pi mu)) (kT)^-3/2 \int sigma E exp(-E/kT) dE
        mu_g = mu * 1.66053906660e-24
        sv = np.sqrt(8 / (np.pi * mu_g)) * (kT * 1.602176634e-6) ** -1.5 \
            * integral * (1.602176634e-6) ** 2
        return NA * sv

    return rate, theta2 * gW2, omega


def li_with_resonance(x, Er, theta2):
    rate, _, _ = resonance_rate(x, Er, theta2)
    T9 = np.exp(bbn.BBN.LNT9)
    vals = np.array([rate(t * 1e9) for t in T9])
    func = lambda TK, v=vals: float(np.exp(np.interp(np.log(TK / 1e9), bbn.BBN.LNT9,
                                                      np.log(np.maximum(v, 1e-300)))))
    extra = [bbn.NetRate(f"res_{x}", ["be7", x], PARTNERS[x][4], func)]
    return bbn.BBN(extra=extra).run()


def job_b(arg):
    x, Er = arg
    f = lambda lt: np.log(li_with_resonance(x, Er, 10**lt)["Li7/H"] / LI_OBS)
    out = {"x": x, "Er": Er}
    try:
        hi = f(0.0)                      # theta^2 = 1 (Wigner limit)
        out["Li_at_wigner"] = float(np.exp(hi) * LI_OBS)
        if hi > 0:
            out["theta2_needed"] = None
        else:
            lt = brentq(f, -8, 0.0, xtol=0.02)
            out["theta2_needed"] = 10**lt
            r = li_with_resonance(x, Er, 10**lt)
            out["D/H"] = r["D/H"]
            out["Yp"] = r["Yp"]
            _, gin, om = resonance_rate(x, Er, 10**lt)
            Z, A, m, jx, _ = PARTNERS[x]
            mu = M_BE7 * m / (M_BE7 + m)
            a = 1.4 * (7 ** (1 / 3) + A ** (1 / 3))
            out["Gamma_in_keV_at_Er"] = 2 * penetrability(Er, Z_BE7, Z, mu, a) * gin * 1e3
    except Exception as e:
        out["error"] = str(e)
    return out


if __name__ == "__main__":
    base = bbn.BBN().run()
    jobs_a = [(n, f) for n in CHANNELS_A for f in FACTORS]
    ER = [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.8]
    jobs_b = [(x, e) for x in PARTNERS for e in ER]
    with Pool(4) as pool:
        ra = pool.map(job_a, jobs_a)
        rb = pool.map(job_b, jobs_b)
    resA = {}
    for n, f, r in ra:
        resA.setdefault(n, []).append({"f": f, **{k: float(v) for k, v in r.items()}})
    json.dump({"base": {k: float(v) for k, v in base.items()}, "A": resA, "B": rb},
              open("results/lithium_fix.json", "w"), indent=1, default=float)
    print("Part A: 7Li/H and D/H vs rate multiplier")
    for n in CHANNELS_A:
        print(f"  {CHANNELS_A[n]:14s}", " ".join(f"{d['f']:g}:{d['Li7/H']*1e10:.2f}/{d['D/H']*1e5:.2f}"
                                               for d in resA[n]))
    print("Part B: s-wave resonance in 7Be + x needed for Li/H = 1.6e-10")
    for o in rb:
        print(" ", o)
