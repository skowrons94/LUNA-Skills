"""Compact Big Bang nucleosynthesis code on top of pynucastro/REACLIB rates.

Physics:
  * standard cosmology: photons + e+- (full Fermi-Dirac thermodynamics) +
    decoupled neutrinos (T_nu tracks 1/a, N_eff scaling) + baryons;
    entropy conservation gives T_gamma(a) through e+- annihilation.
  * n <-> p weak rates: Born approximation, six processes with Fermi-Dirac
    blocking at T_gamma / T_nu, normalised to the measured neutron lifetime.
  * nuclear network: every REACLIB rate (forward + detailed-balance reverse)
    linking n, p, d, t, 3He, 4He, 6Li, 7Li, 7Be, 8Li, 8B, 9Be, plus
    7Be(d,p)2a (CF88), which is not in REACLIB.
  * every rate can be scaled (`mult`) or replaced/augmented (`extra`),
    which is what the lithium-problem study uses.

Independent variable: x = ln a, a = 1/T_nu [MeV^-1].
"""
import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.interpolate import interp1d
import pynucastro as pyna

# ---------------------------------------------------------------- constants
HBARC = 197.3269804e-13          # MeV cm
MEV_TO_ERG = 1.602176634e-6
G_NEWTON = 6.67430e-8            # cgs
C_LIGHT = 2.99792458e10
M_U = 1.66053906660e-24          # g
ME = 0.51099895                  # MeV
Q_NP = 1.29333236                # MeV
TAU_N = 878.4                    # s
ZETA3 = 1.2020569031595942
K_MEV = 8.617333262e-11          # MeV / K

SPECIES = ["n", "p", "d", "t", "he3", "he4", "li6", "li7", "be7",
           "li8", "b8", "be9"]
IDX = {s: i for i, s in enumerate(SPECIES)}
NSP = len(SPECIES)
A_NUM = np.array([1, 1, 2, 3, 3, 4, 6, 7, 7, 8, 8, 9], float)

# --------------------------------------------------------- thermodynamics
def _e_pm(T):
    """Energy density and pressure of e+ + e- (g=4) at temperature T [MeV]."""
    if T < ME / 60.0:
        return 0.0, 0.0
    f = lambda p, k: p**2 * (np.sqrt(p * p + ME * ME) if k == 0 else
                             p**2 / (3 * np.sqrt(p * p + ME * ME))) \
        / (np.exp(np.sqrt(p * p + ME * ME) / T) + 1.0)
    pmax = 60.0 * T + 10 * ME
    rho = 4 / (2 * np.pi**2) * quad(f, 0, pmax, args=(0,), limit=200)[0]
    P = 4 / (2 * np.pi**2) * quad(f, 0, pmax, args=(1,), limit=200)[0]
    return rho, P


def _build_background(neff=3.044):
    Tg = np.logspace(np.log10(30.0), np.log10(3e-4), 1500)       # MeV
    rho_e, P_e = np.array([_e_pm(T) for T in Tg]).T
    s = (4 * np.pi**2 / 45) * Tg**3 + (rho_e + P_e) / Tg         # gamma + e
    # normalise: at T=30 MeV, a = 1/T_nu = 1/T_gamma
    C = s[0] * (1 / Tg[0])**3
    a = (C / s)**(1 / 3)
    Tnu = 1 / a
    rho_tot = (np.pi**2 / 15) * Tg**4 + rho_e \
        + neff * (7 / 8) * (np.pi**2 / 15) * Tnu**4             # MeV^4
    return Tg, a, Tnu, rho_tot


class Background:
    def __init__(self, eta10, neff=3.044):
        Tg, a, Tnu, rho_rad = _build_background(neff)
        self.eta = eta10 * 1e-10
        lna = np.log(a)
        self._lnT = interp1d(lna, np.log(Tg), kind="cubic")
        self._lnrho = interp1d(lna, np.log(rho_rad), kind="cubic")
        self.x0, self.x1 = lna[0], lna[-1]

    def state(self, x):
        Tg = np.exp(self._lnT(x))
        Tnu = np.exp(-x)
        n_gamma = 2 * ZETA3 / np.pi**2 * (Tg / HBARC)**3          # cm^-3
        rho_b = self.eta * n_gamma * M_U                           # g cm^-3
        rho_rad = np.exp(self._lnrho(x)) / HBARC**3 * MEV_TO_ERG / C_LIGHT**2
        H = np.sqrt(8 * np.pi * G_NEWTON / 3 * (rho_rad + rho_b))
        return Tg, Tnu, rho_b, H


# ------------------------------------------------------------- weak rates
def _fd(E, T):
    return 1.0 / (np.exp(np.clip(E / T, -700, 700)) + 1.0)


def _weak_raw(T, Tnu):
    """Unnormalised n->p and p->n rates (Born approximation)."""
    pe = lambda E: np.sqrt(max(E * E - ME * ME, 0.0))
    Emax = ME + 50 * max(T, Tnu) + 5 * Q_NP
    # n -> p
    r1 = quad(lambda Ev: (Ev + Q_NP) * pe(Ev + Q_NP) * Ev**2 * _fd(Ev, Tnu)
              * (1 - _fd(Ev + Q_NP, T)), 0, Emax, limit=200)[0]   # n nu -> p e
    r2 = quad(lambda Ee: Ee * pe(Ee) * (Ee + Q_NP)**2 * _fd(Ee, T)
              * (1 - _fd(Ee + Q_NP, Tnu)), ME, Emax, limit=200)[0]  # n e+ -> p nub
    r3 = quad(lambda Ee: Ee * pe(Ee) * (Q_NP - Ee)**2 * (1 - _fd(Ee, T))
              * (1 - _fd(Q_NP - Ee, Tnu)), ME, Q_NP, limit=200)[0]  # decay
    # p -> n
    r4 = quad(lambda Ee: Ee * pe(Ee) * (Ee - Q_NP)**2 * _fd(Ee, T)
              * (1 - _fd(Ee - Q_NP, Tnu)), Q_NP, Emax, limit=200)[0]  # p e -> n nu
    r5 = quad(lambda Ev: (Ev - Q_NP) * pe(Ev - Q_NP) * Ev**2 * _fd(Ev, Tnu)
              * (1 - _fd(Ev - Q_NP, T)), Q_NP + ME, Emax, limit=200)[0]  # p nub -> n e+
    return r1 + r2 + r3, r4 + r5


def build_weak_table(bg):
    xs = np.linspace(bg.x0, bg.x1, 600)
    r0 = quad(lambda Ee: Ee * np.sqrt(Ee**2 - ME**2) * (Q_NP - Ee)**2,
              ME, Q_NP)[0]
    K = 1.0 / (TAU_N * r0)
    lnp, lpn = [], []
    for x in xs:
        Tg, Tnu, _, _ = bg.state(x)
        a, b = _weak_raw(Tg, Tnu)
        lnp.append(np.log(K * a))
        lpn.append(np.log(K * b + 1e-300))
    return interp1d(xs, lnp, kind="cubic"), interp1d(xs, lpn, kind="cubic")


# ----------------------------------------------------------- nuclear rates
NAMES_TO_PYNA = {"n": "n", "p": "p", "d": "d", "t": "t", "he3": "he3",
                 "he4": "he4", "li6": "li6", "li7": "li7", "be7": "be7",
                 "li8": "li8", "b8": "b8", "be9": "be9"}


class NetRate:
    """A rate with stoichiometry and a log-T table of N_A<sigma v> (or lambda)."""

    def __init__(self, name, reac, prod, func, prefactor=1.0):
        self.name, self.reac, self.prod = name, reac, prod
        self.func, self.prefactor = func, prefactor
        self.order = len(reac)

    def tabulate(self, T9grid):
        v = np.array([max(self.func(T9 * 1e9), 1e-300) for T9 in T9grid])
        self._interp = interp1d(np.log(T9grid), np.log(v), kind="linear",
                                bounds_error=False,
                                fill_value=(np.log(v[0]), np.log(v[-1])))

    def __call__(self, T9):
        return np.exp(self._interp(np.log(T9)))


def _short(nuc):
    s = str(nuc.raw if hasattr(nuc, "raw") else nuc).lower()
    return {"h2": "d", "h3": "t"}.get(s, s)


def reaclib_rates():
    rl = pyna.ReacLibLibrary()
    lib = rl.linking_nuclei(SPECIES, with_reverse=True)
    rates = []
    for r in lib.get_rates():
        if r.weak:            # beta decays / captures handled separately
            continue
        reac = [_short(n) for n in r.reactants]
        prod = [_short(n) for n in r.products]
        if any(s not in IDX for s in reac + prod):
            continue
        if len(reac) > 2:     # 3/4-body inverses: negligible, ill-conditioned
            continue
        rates.append(NetRate(r.fname.replace("_reaclib", ""), reac, prod,
                             r.eval, r.prefactor))
    # 7Be(d,p)2a, Caughlan & Fowler 1988 (absent from REACLIB)
    cf88 = lambda T: 1.07e12 * (T / 1e9)**(-2 / 3) * np.exp(-12.428 * (T / 1e9)**(-1 / 3))
    rates.append(NetRate("Be7_d_to_p_He4_He4", ["be7", "d"], ["p", "he4", "he4"], cf88))
    # slow decays that matter on BBN timescales
    rates.append(NetRate("Li8_beta", ["li8"], ["he4", "he4"], lambda T: np.log(2) / 0.839))
    rates.append(NetRate("B8_beta", ["b8"], ["he4", "he4"], lambda T: np.log(2) / 0.770))
    return rates


# ------------------------------------------------------------------ solver
_CACHE = {}


def _cached(key, builder):
    if key not in _CACHE:
        _CACHE[key] = builder()
    return _CACHE[key]


class BBN:
    """mult:    {rate name: factor} (inverse rate scaled consistently)
    extra:   list of NetRate added to the network
    replace: {rate name: callable(T[K]) -> N_A<sigma v>}"""

    LNT9 = np.linspace(np.log(1e-3), np.log(15.0), 1200)

    def __init__(self, eta10=6.104, neff=3.044, mult=None, extra=None,
                 replace=None, inject=None):
        self.bg = Background(eta10, neff)
        # inject = (Y_n injected per baryon, lifetime [s]): late decaying
        # particle releasing neutrons (thermalised; no 4He spallation)
        self.inject = inject
        xs = np.linspace(self.bg.x0, self.bg.x1, 4000)
        invH = np.array([1 / self.bg.state(x)[3] for x in xs])
        tt = np.concatenate([[0.0], np.cumsum(0.5 * (invH[1:] + invH[:-1]) * np.diff(xs))])
        tt += 1 / (2 * self.bg.state(xs[0])[3])          # radiation era t = 1/2H
        self._t = interp1d(xs, tt)
        self.lnp, self.lpn = _cached(("weak", neff),
                                     lambda: build_weak_table(Background(eta10, neff)))
        base = _cached("rates", reaclib_rates)
        self.rates = [NetRate(r.name, r.reac, r.prod, r.func, r.prefactor)
                      for r in base] + list(extra or [])
        replace = replace or {}
        tabs = []
        for r in self.rates:
            if r.name in replace:
                r.func = replace[r.name]
                tabs.append(self._tab(r))
            else:
                tabs.append(_cached(("tab", r.name, id(r.func)),
                                    lambda r=r: self._tab(r)))
        self.logv = np.array(tabs)                      # (nrates, nT)
        nr = len(self.rates)
        self.S = np.zeros((NSP, nr))
        self.r1 = np.zeros(nr, int)
        self.r2 = np.full(nr, NSP)                      # NSP -> "1.0" slot
        self.pref = np.array([r.prefactor for r in self.rates])
        self.order = np.array([r.order for r in self.rates])
        for k, r in enumerate(self.rates):
            ii = [IDX[s] for s in r.reac]
            self.r1[k] = ii[0]
            if len(ii) == 2:
                self.r2[k] = ii[1]
            for i in ii:
                self.S[i, k] -= 1
            for s_ in r.prod:
                self.S[IDX[s_], k] += 1
        self.set_mult(mult or {})

    def _tab(self, r):
        return np.log(np.maximum([r.func(np.exp(l) * 1e9) for l in self.LNT9], 1e-300))

    def set_mult(self, mult):
        self.mult = np.array([mult.get(r.name, 1.0) for r in self.rates])
        # detailed balance: scaling a forward rate scales its inverse too
        for k, r in enumerate(self.rates):
            for name, f in mult.items():
                if self._is_inverse(r, name):
                    self.mult[k] = f

    def _is_inverse(self, r, name):
        fwd = next((q for q in self.rates if q.name == name), None)
        return (fwd is not None and r is not fwd and
                sorted(r.reac) == sorted(fwd.prod) and
                sorted(r.prod) == sorted(fwd.reac))

    def _lam(self, x):
        Tg, Tnu, rho, H = self.bg.state(x)
        l = np.log(Tg / K_MEV / 1e9)
        g = self.LNT9
        j = int(np.clip((l - g[0]) / (g[1] - g[0]), 0, len(g) - 2))
        w = np.clip((l - g[j]) / (g[1] - g[0]), 0.0, 1.0)
        v = np.exp(self.logv[:, j] * (1 - w) + self.logv[:, j + 1] * w)
        return self.mult * v * self.pref * rho ** (self.order - 1), H

    def _rhs_jac(self, x, Y, want_jac, nuclear=True):
        lnp, lpn = np.exp(self.lnp(x)), np.exp(self.lpn(x))
        n, p = IDX["n"], IDX["p"]
        if nuclear:
            lam, H = self._lam(x)
        else:
            H = self.bg.state(x)[3]
        if not want_jac:
            dY = np.zeros(NSP)
            f = lnp * Y[n] - lpn * Y[p]
            dY[n] -= f
            dY[p] += f
            if nuclear:
                Ye = np.append(Y, 1.0)
                dY += self.S @ (lam * Ye[self.r1] * Ye[self.r2])
            if self.inject:
                Yx, tau = self.inject
                dY[n] += Yx / tau * np.exp(-self._t(x) / tau)
            return dY / H
        J = np.zeros((NSP, NSP))
        J[n, n] -= lnp; J[n, p] += lpn; J[p, n] += lnp; J[p, p] -= lpn
        if nuclear:
            Ye = np.append(Y, 1.0)
            D = np.zeros((len(lam), NSP + 1))
            k = np.arange(len(lam))
            np.add.at(D, (k, self.r1), lam * Ye[self.r2])
            np.add.at(D, (k, self.r2), lam * Ye[self.r1])
            J += self.S @ D[:, :NSP]
        return J / H

    def time(self, T9):
        """Cosmic time [s] at photon temperature T9."""
        xs = np.linspace(self.bg.x0, self.bg.x1, 4000)
        lt = self.bg._lnT(xs)
        x = np.interp(-np.log(T9 * 1e9 * K_MEV), -lt, xs)
        return float(self._t(x))

    def run(self, x_switch_T9=3.0):
        bg = self.bg
        # phase 1: n/p only, from T=30 MeV until T9 = 3 (nuclei negligible above)
        x_sw = float(np.interp(-np.log(x_switch_T9 * 1e9 * K_MEV),
                               -np.log([np.exp(bg._lnT(z)) for z in
                                        np.linspace(bg.x0, bg.x1, 2000)]),
                               np.linspace(bg.x0, bg.x1, 2000)))
        T0 = np.exp(bg._lnT(bg.x0))
        Y = np.full(NSP, 1e-30)
        Y[IDX["n"]] = 1 / (1 + np.exp(Q_NP / T0))
        Y[IDX["p"]] = 1 - Y[IDX["n"]]
        s1 = solve_ivp(lambda x, y: self._rhs_jac(x, y, False, False), (bg.x0, x_sw), Y,
                       method="LSODA", jac=lambda x, y: self._rhs_jac(x, y, True, False),
                       rtol=1e-8, atol=1e-30)
        if not s1.success:
            raise RuntimeError("phase 1: " + s1.message)
        Y = s1.y[:, -1].copy()
        # phase 2: full network until T ~ 1e-3 MeV (T9 ~ 0.01)
        x_end = -np.log(1.2e-3) + 0.0
        x_end = min(x_end, bg.x1 - 0.01)
        sol = solve_ivp(lambda x, y: self._rhs_jac(x, y, False), (x_sw, x_end), Y,
                        method="LSODA", jac=lambda x, y: self._rhs_jac(x, y, True),
                        rtol=1e-7, atol=1e-30, dense_output=False,
                        t_eval=np.linspace(x_sw, x_end, 400))
        self.sol = sol
        if not sol.success:
            raise RuntimeError("phase 2: " + sol.message)
        return self.final(sol.y[:, -1])

    @staticmethod
    def final(Y):
        Y = np.clip(Y, 0, None)
        H = Y[IDX["p"]]
        return {
            "Yp": 4 * Y[IDX["he4"]],
            "D/H": Y[IDX["d"]] / H,
            "He3/H": (Y[IDX["he3"]] + Y[IDX["t"]]) / H,
            "Li7/H": (Y[IDX["li7"]] + Y[IDX["be7"]]) / H,
            "Be7/H": Y[IDX["be7"]] / H,
            "Li6/H": Y[IDX["li6"]] / H,
        }


if __name__ == "__main__":
    import time
    t = time.time()
    b = BBN()
    res = b.run()
    for k, v in res.items():
        print(f"{k:7s} {v:.4e}")
    print(f"({time.time() - t:.1f} s)")
