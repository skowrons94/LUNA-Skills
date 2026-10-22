#!/usr/bin/env python3
"""One-zone nuclear reaction network on pynucastro rates.

pynucastro supplies the rates (REACLIB, tabulated weak rates, derived reverse rates), nuclear
masses, partition functions and screening functions. This module adds what a sensitivity study
needs and the generated pynucastro networks do not offer at run time:

- a rate multiplier per rate, constant or T-dependent (Monte Carlo factor fu(T)**p);
- tabulated rates N_A<sigma v>(T9) (an AZURE2 or STARLIB table) as ordinary network rates;
- burns at constant (T, rho) or along a (t, T, rho) trajectory, with the specific energy
  integrated alongside the abundances;
- an analytic Jacobian (screening held fixed, as in pynucastro).

Abundances are molar fractions Y = X/A. Rates follow pynucastro's convention: for reaction i,
R_i = prefactor_i * rho**dens_exp_i * eval_i(T) * screen_i * mult_i(T) * prod_j Y_j**n_ij,
and dY/dt = S^T R with S the net stoichiometry (products minus reactants).
"""

import math
from collections import Counter

import numpy as np
import pynucastro as pyna
from pynucastro import screening as pscr
from pynucastro.rates.rate import Rate
from pynucastro.rates.reaclib_rate import ReacLibRate, SingleSet
from pynucastro.screening.screening_util import get_screening_map
from scipy.integrate import solve_ivp

N_A = pyna.constants.constants.N_A
MEV2ERG = pyna.constants.constants.MeV2erg

SCREENING = {
    "none": None,
    "screen5": pscr.screen5,
    "chugunov_2007": pscr.chugunov_2007,
    "chugunov_2009": pscr.chugunov_2009,
    "potekhin_1998": pscr.potekhin_1998,
    "debye_huckel": pscr.debye_huckel,
}


# --------------------------------------------------------------------------- rates

class TableRate(Rate):
    """A rate given as N_A<sigma v> (cm^3 mol^-1 s^-1, or s^-1 for one reactant) on a T9 grid.

    Interpolation is linear in (ln T9, ln rate). Outside the table, `outside` decides:
    'error' (default), 'clamp' (hold the end value) or 'zero'.
    """

    def __init__(self, reactants, products, T9, rate, label="table", Q=None, outside="error",
                 source=""):
        super().__init__(reactants=reactants, products=products, Q=Q, label=label)
        T9 = np.asarray(T9, float)
        rate = np.asarray(rate, float)
        if T9.ndim != 1 or len(T9) < 2 or np.any(np.diff(T9) <= 0):
            raise ValueError(f"{self}: T9 grid must be strictly increasing with >= 2 points")
        if np.any(rate < 0):
            raise ValueError(f"{self}: negative rate values in table")
        if outside not in ("error", "clamp", "zero"):
            raise ValueError("outside must be 'error', 'clamp' or 'zero'")
        self.T9 = T9
        self.table = rate
        self.lnT9 = np.log(T9)
        self.lnrate = np.log(np.maximum(rate, 1e-300))
        self.outside = outside
        self.table_source = source
        self.chapter = "t"

    def eval(self, T, *, rho=None, comp=None):
        x = math.log(T / 1e9)
        if x < self.lnT9[0] - 1e-12 or x > self.lnT9[-1] + 1e-12:
            if self.outside == "error":
                raise ValueError(f"{self}: T9={T / 1e9:.4g} outside table "
                                 f"[{self.T9[0]:.4g}, {self.T9[-1]:.4g}]")
            if self.outside == "zero":
                return 0.0
        return float(np.exp(np.interp(x, self.lnT9, self.lnrate)))


def reaclib_rate_from_sets(reactants, products, sets, label="fit ", chapter=None, Q=None,
                           resonant=None, reverse=False):
    """Build a pynucastro ReacLibRate from a list of 7-parameter sets."""
    reactants = pyna.Nucleus.cast_list(reactants)
    products = pyna.Nucleus.cast_list(products)
    if chapter is None:
        chapter = reaclib_chapter(len(reactants), len(products))
    label = (label + "    ")[:4]
    if Q is None:  # from nuclear masses (MeV)
        Q = sum(n.mass for n in reactants) - sum(n.mass for n in products)
    out = []
    for k, a in enumerate(sets):
        flag = "n"
        if resonant is not None:
            flag = "r" if resonant[k] else "n"
        out.append(SingleSet(list(map(float, a)), label + flag + ("v" if reverse else " ")))
    r = ReacLibRate(chapter=chapter, reactants=reactants, products=products, sets=out,
                    labelprops=out[0].labelprops, Q=Q)
    return r


def reaclib_chapter(nr, np_):
    table = {(1, 1): 1, (1, 2): 2, (1, 3): 3, (2, 1): 4, (2, 2): 5, (2, 3): 6, (2, 4): 7,
             (3, 1): 8, (3, 2): 9, (4, 2): 10, (1, 4): 11}
    if (nr, np_) not in table:
        raise ValueError(f"no REACLIB chapter for {nr} reactants -> {np_} products")
    return table[(nr, np_)]


def reaclib_text(rate):
    """REACLIB 2 text for a ReacLibRate (one block per set), readable by pynucastro.load_rate."""
    lines = []
    nuc = [n.short_spec_name for n in rate.reactants + rate.products]
    for s in rate.sets:
        a = s.a
        lp = (s.labelprops + "      ")[:6]
        names = "".join(f"{x:>5s}" for x in nuc).ljust(30)
        lines.append(f"{rate.chapter}")
        lines.append(f"     {names}        {lp}   {rate.Q:12.5e}          ")
        lines.append("".join(f"{x:13.6e}" for x in a[:4]) + " " * 22)
        lines.append("".join(f"{x:13.6e}" for x in a[4:]) + " " * 35)
    return "\n".join(lines) + "\n"


def same_reaction(r1, r2):
    return (Counter(n.raw for n in r1.reactants) == Counter(n.raw for n in r2.reactants)
            and Counter(n.raw for n in r1.products) == Counter(n.raw for n in r2.products))


def is_reverse_of(r1, r2):
    """True if r1 is the reverse reaction of r2 (reactants and products swapped)."""
    return (Counter(n.raw for n in r1.reactants) == Counter(n.raw for n in r2.products)
            and Counter(n.raw for n in r1.products) == Counter(n.raw for n in r2.reactants))


def find_rate(rates, name):
    """Find a rate by pynucastro short name ('mg25(p,g)al26') or by fname ('p_Mg25__Al26')."""
    key = name.strip()
    hits = [r for r in rates if r.fname.lower() == key.lower()]
    if hits:
        return hits[0]
    try:
        probe = pyna.RateCollection(rates=list(rates)).get_rate_by_name(key)
    except Exception:  # pynucastro raises on malformed names
        probe = None
    if probe is not None:
        if isinstance(probe, list):
            if len(probe) != 1:
                raise KeyError(f"{name!r} matches {len(probe)} rates: {[r.fname for r in probe]}")
            probe = probe[0]
        return probe
    raise KeyError(f"no rate {name!r} in the network")


def rate_label(r):
    return getattr(r, "label", "") or ""


# --------------------------------------------------------------------------- network

class Network:
    """Evaluate dY/dt, the Jacobian and the energy generation for a set of pynucastro rates."""

    def __init__(self, rates, screening="chugunov_2007", symmetric_screening=False, nuclei=()):
        from pynucastro.rates.approximate_rates import ApproximateRate
        rates = list(rates)
        if any(isinstance(r, ApproximateRate) for r in rates):
            raise NotImplementedError("ApproximateRate is not supported; use the explicit rates")
        if screening not in SCREENING:
            raise ValueError(f"screening must be one of {sorted(SCREENING)}")
        self.screening = screening
        self.screen_func = SCREENING[screening]
        self.rates = rates
        nuc = set(pyna.Nucleus.cast_list(list(nuclei)))  # requested nuclei stay, even if inert
        for r in rates:
            nuc.update(r.reactants)
            nuc.update(r.products)
        self.nuclei = sorted(nuc, key=lambda n: (n.Z, n.A))
        self.index = {n: i for i, n in enumerate(self.nuclei)}
        self.names = [n.raw for n in self.nuclei]
        self.A = np.array([n.A for n in self.nuclei], float)
        self.Z = np.array([n.Z for n in self.nuclei], float)
        self.mass = np.array([n.mass for n in self.nuclei], float)  # MeV
        nr, nn = len(rates), len(self.nuclei)
        self.S = np.zeros((nr, nn))
        self.reac = []  # per rate: list of (nucleus index, power)
        self.pref = np.zeros(nr)
        self.dens_exp = np.zeros(nr)
        self.ye_fac = np.zeros(nr, bool)
        self.needs_comp = np.zeros(nr, bool)
        for i, r in enumerate(rates):
            if r.stoichiometry:
                cnt_r = {n: r.stoichiometry.get(n, 0) for n in r.reactants}
                cnt_p = {n: r.stoichiometry.get(n, 0) for n in r.products}
            else:
                cnt_r, cnt_p = Counter(r.reactants), Counter(r.products)
            for n, c in cnt_r.items():
                self.S[i, self.index[n]] -= c
            for n, c in cnt_p.items():
                self.S[i, self.index[n]] += c
            pw = Counter(r.reactants)
            self.reac.append([(self.index[n], c) for n, c in pw.items()])
            self.pref[i] = r.prefactor
            self.dens_exp[i] = r.dens_exp
            self.ye_fac[i] = (r.weak_type == "electron_capture" and not r.tabular)
            self.needs_comp[i] = bool(r.rate_eval_needs_comp or r.rate_eval_needs_rho)
        # screening map, following RateCollection.evaluate_screening
        self.scr = []
        if self.screen_func is not None:
            rid = {id(r): i for i, r in enumerate(rates)}
            for s in get_screening_map(rates, symmetric_screening=symmetric_screening):
                fac = pscr.make_screen_factors(s.n1, s.n2)
                self.scr.append((s.name, fac, [rid[id(r)] for r in s.rates]))
        # multipliers: mult_i(T) = const_i * fu_i(T) ** p_i
        self.const = np.ones(nr)
        self.p = np.zeros(nr)
        self.fu = [None] * nr  # (lnT9 grid, ln fu) or None
        self.group = np.arange(nr)  # rates sharing one random variable (forward + reverse)

    # ---- multipliers
    def set_fu(self, i, fu, T9=None):
        """Uncertainty factor of rate i: a constant, or a table fu(T9)."""
        fu = np.atleast_1d(np.asarray(fu, float))
        if np.any(fu < 1):
            raise ValueError("uncertainty factors fu must be >= 1")
        if T9 is None:
            if len(fu) != 1:
                raise ValueError("a constant fu needs one value")
            self.fu[i] = (np.array([-50.0, 50.0]), np.log([fu[0], fu[0]]))
        else:
            self.fu[i] = (np.log(np.asarray(T9, float)), np.log(fu))

    def multipliers(self, T):
        m = self.const.copy()
        if np.any(self.p != 0):
            x = math.log(T / 1e9)
            for i in np.nonzero(self.p)[0]:
                if self.fu[i] is None:
                    raise ValueError(f"p set for {self.rates[i].fname} without an uncertainty factor")
                g, lf = self.fu[i]
                m[i] *= math.exp(self.p[i] * np.interp(x, g, lf))
        return m

    # ---- evaluation
    def composition(self, Y):
        c = pyna.Composition(self.nuclei)
        for n, y in zip(self.nuclei, Y):
            c.X[n] = max(y, 0.0) * n.A
        return c

    def screen_factors(self, T, rho, Y):
        f = np.ones(len(self.rates))
        if self.screen_func is None:
            return f
        ps = pscr.PlasmaState(T, rho, np.maximum(Y, 0.0), self.Z)
        first = 1.0
        for name, fac, idx in self.scr:
            s = self.screen_func(ps, fac)
            if name == "He4_He4_He4":
                first = s
                continue
            if name == "He4_He4_He4_dummy":
                s = first * s
            f[idx] = s
        return f

    def rate_constants(self, T, rho, Y):
        """k_i such that R_i = k_i * prod Y_j**n_ij."""
        comp = self.composition(Y) if self.needs_comp.any() else None
        ev = np.empty(len(self.rates))
        for i, r in enumerate(self.rates):
            if self.needs_comp[i]:
                ev[i] = r.eval(T, rho=rho, comp=comp)
            else:
                ev[i] = r.eval(T)
        k = self.pref * rho ** self.dens_exp * ev
        if self.ye_fac.any():
            Yp = np.maximum(Y, 0.0)
            k[self.ye_fac] *= float(np.sum(self.Z * Yp))
        return k * self.screen_factors(T, rho, Y) * self.multipliers(T)

    def flows(self, T, rho, Y):
        # no clipping here: a slightly negative abundance must still be destroyed by its
        # linear terms, or the stiff solver's overshoot below zero never relaxes back
        Yp = np.asarray(Y, float)
        k = self.rate_constants(T, rho, Y)
        R = k.copy()
        for i, lst in enumerate(self.reac):
            for j, c in lst:
                R[i] *= Yp[j] ** c
        return R, k

    def ydot(self, T, rho, Y):
        R, _ = self.flows(T, rho, Y)
        return self.S.T @ R

    def jacobian(self, T, rho, Y):
        Yp = np.asarray(Y, float)
        k = self.rate_constants(T, rho, Y)
        nn = len(self.nuclei)
        dR = np.zeros((len(self.rates), nn))
        for i, lst in enumerate(self.reac):
            for a, (j, c) in enumerate(lst):
                v = k[i] * c * Yp[j] ** (c - 1)
                for b, (jj, cc) in enumerate(lst):
                    if b != a:
                        v *= Yp[jj] ** cc
                dR[i, j] = v
        return self.S.T @ dR

    def eps(self, ydot):
        """Specific nuclear energy generation (erg/g/s) from mass changes, as in pynucastro.
        Neutrino losses of REACLIB beta decays are NOT subtracted (see references/pitfalls.md)."""
        return -N_A * MEV2ERG * float(self.mass @ ydot)

    # ---- composition helpers
    def Y_from_X(self, X, normalize=False, tol=1e-6):
        Y = np.zeros(len(self.nuclei))
        unknown = []
        for name, x in X.items():
            n = pyna.Nucleus.cast(name)
            if n not in self.index:
                unknown.append(name)
                continue
            Y[self.index[n]] += x / n.A
        if unknown:
            raise KeyError(f"initial nuclei not in the network: {unknown}")
        s = float(np.sum(Y * self.A))
        if abs(s - 1) > tol:
            if not normalize:
                raise ValueError(f"initial mass fractions sum to {s:.8g}; set normalize=true "
                                 "or fix the composition")
            Y /= s
        return Y

    def X_from_Y(self, Y):
        return Y * self.A


# --------------------------------------------------------------------------- conditions

class Conditions:
    """T(t), rho(t): constant, or a trajectory interpolated linearly in (t, ln T, ln rho)."""

    def __init__(self, t, T, rho):
        self.t = np.asarray(t, float)
        self.lnT = np.log(np.asarray(T, float))
        self.lnrho = np.log(np.asarray(rho, float))
        if len(self.t) < 2 or np.any(np.diff(self.t) <= 0):
            raise ValueError("trajectory times must be strictly increasing (>= 2 points)")

    @classmethod
    def constant(cls, T, rho, t_end, t0=0.0):
        return cls([t0, t_end], [T, T], [rho, rho])

    def __call__(self, t):
        t = min(max(t, self.t[0]), self.t[-1])
        return (float(np.exp(np.interp(t, self.t, self.lnT))),
                float(np.exp(np.interp(t, self.t, self.lnrho))))


def burn(net, Y0, cond, t_out=None, rtol=1e-6, atol=1e-20, method="BDF", max_step=np.inf):
    """Integrate dY/dt and dE/dt along `cond`, segment by segment between trajectory points.

    Returns dict with t, T, rho, Y (n_t x n_nuc), E (erg/g, cumulative), and solver stats.
    """
    nn = len(net.nuclei)
    t0, t1 = cond.t[0], cond.t[-1]
    if t_out is None:
        t_out = np.array([t0, t1])
    t_out = np.unique(np.clip(np.asarray(t_out, float), t0, t1))
    breaks = cond.t

    def rhs(t, y):
        T, rho = cond(t)
        yd = net.ydot(T, rho, y[:nn])
        return np.append(yd, net.eps(yd))

    def jac(t, y):
        T, rho = cond(t)
        J = net.jacobian(T, rho, y[:nn])
        full = np.zeros((nn + 1, nn + 1))
        full[:nn, :nn] = J
        full[nn, :nn] = -N_A * MEV2ERG * (net.mass @ J)
        return full

    y = np.append(np.asarray(Y0, float), 0.0)
    out_t, out_y = [t0], [y.copy()]  # the initial state is always the first row
    stats = {"nfev": 0, "njev": 0, "nlu": 0, "segments": 0}
    for a, b in zip(breaks[:-1], breaks[1:]):
        te = t_out[(t_out > a) & (t_out <= b)]
        tev = np.unique(np.append(te, b))  # always end on the breakpoint
        # energy is an integral, not a solution component to control: loose absolute tolerance
        atol_v = np.append(np.full(nn, atol), np.inf)
        sol = solve_ivp(rhs, (a, b), y, method=method,
                        jac=jac if method in ("BDF", "Radau", "LSODA") else None,
                        rtol=rtol, atol=atol_v, t_eval=tev, max_step=max_step)
        if sol.status != 0:
            raise RuntimeError(f"integration failed on [{a:.4g}, {b:.4g}] s: {sol.message}")
        stats["nfev"] += sol.nfev
        stats["njev"] += sol.njev
        stats["nlu"] += sol.nlu
        stats["segments"] += 1
        for tt, yy in zip(sol.t, sol.y.T):
            if np.any(np.isclose(tt, te, rtol=1e-12, atol=0)):
                out_t.append(tt)
                out_y.append(yy)
        y = sol.y[:, -1]
    out_y = np.array(out_y)
    T = np.array([cond(t)[0] for t in out_t])
    rho = np.array([cond(t)[1] for t in out_t])
    Y = out_y[:, :nn]
    return {"t": np.array(out_t), "T": T, "rho": rho, "Y": Y, "X": Y * net.A, "E": out_y[:, nn],
            "stats": stats, "rtol": rtol, "atol": atol, "method": method}


# --------------------------------------------------------------------------- observables

def observable(net, X, Y, E, expr):
    """Evaluate 'X(al26)', 'Y(c12)/Y(c13)', 'X(o16)/X(c12)' or 'E' on final arrays."""
    expr = expr.replace(" ", "")
    if expr == "E":
        return float(E)
    num, _, den = expr.partition("/")

    def term(s):
        kind, _, rest = s.partition("(")
        n = pyna.Nucleus.cast(rest.rstrip(")"))
        if n not in net.index:
            raise KeyError(f"{n} not in network (observable {expr!r})")
        v = {"X": X, "Y": Y}[kind.upper()]
        return float(v[net.index[n]])

    v = term(num)
    if den:
        d = term(den)
        return v / d if d != 0 else float("inf")
    return v
