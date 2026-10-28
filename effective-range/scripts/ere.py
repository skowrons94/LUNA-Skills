"""Coulomb-modified effective-range analysis of a charged-particle s (or l) wave.

    K(E) = C0^2(eta) k cot(delta_0) + 2 k eta h(eta) = -1/a0 + r0 k^2/2 + P k^4 + ...

with C0^2 = 2 pi eta/(exp(2 pi eta) - 1) and h(eta) = Re psi(1 + i eta) - ln eta
(Bethe; Lane & Thomas XI).  K is insensitive to the n*pi ambiguity of delta, so
phases of models with Pauli-forbidden bound states compare directly with data.

Also the one-level, one-channel R-matrix s wave (boundary condition B = S(E_lambda)):
which theta^2 must a level at E_lambda carry to reproduce a given a0?

Units: MeV, fm; E is the c.m. energy above the threshold; phases in degrees.
Generalized from the 7Be study (alpha+3He; ere.py and onepole.py there).
"""
from functools import lru_cache

import mpmath as mp
import numpy as np
from scipy.optimize import brentq
from scipy.special import digamma

HBARC = 197.3269804
E2 = 1.4399764
MASS = {"n": 939.56542052, "p": 938.27208816, "d": 1875.61294257, "t": 2808.92113298,
        "3He": 2808.39160743, "alpha": 3727.3794066}
CHARGE = {"n": 0, "p": 1, "d": 1, "t": 1, "3He": 2, "alpha": 2}


class Pair:
    """Two particles: reduced mass (MeV) and Z1 Z2."""

    def __init__(self, c1="alpha", c2="3He", m1=None, m2=None, zz=None):
        m1 = MASS[c1] if m1 is None else m1
        m2 = MASS[c2] if m2 is None else m2
        self.mu = m1 * m2 / (m1 + m2)
        self.zz = CHARGE[c1] * CHARGE[c2] if zz is None else zz
        self.h2m = HBARC ** 2 / (2 * self.mu)

    def k(self, E): return np.sqrt(np.asarray(E, float) / self.h2m)
    def eta(self, E): return self.zz * E2 * self.mu / (HBARC ** 2 * self.k(E))


def C0sq(e): return 2 * np.pi * e / np.expm1(2 * np.pi * e)
def hfun(e): return np.real(digamma(1 + 1j * np.asarray(e, float))) - np.log(e)


def Kfun(pair, E, delta_deg):
    """Effective-range function K(E), fm^-1 (s wave)."""
    E = np.asarray(E, float); d = np.radians(np.asarray(delta_deg, float))
    k = pair.k(E); e = pair.eta(E)
    return C0sq(e) * k / np.tan(d) + 2 * k * e * hfun(e)


def fit_ere(pair, E, delta_deg, emin, emax, order=2):
    """Least squares of K on k^2 over [emin, emax]: a0, r0, P (fm^3), rms, range.
    order = 1 is (a0, r0) only; order = 2 adds the shape term P k^4."""
    E = np.asarray(E, float); d = np.asarray(delta_deg, float)
    m = (E >= emin) & (E <= emax) & np.isfinite(d) & (np.abs(np.sin(np.radians(d))) > 1e-9)
    k2 = pair.k(E[m]) ** 2; K = Kfun(pair, E[m], d[m])
    c = np.polyfit(k2, K, order)
    res = K - np.polyval(c, k2)
    return dict(a0=-1.0 / c[-1], r0=2.0 * c[-2], P=(c[-3] if order >= 2 else None),
                npts=int(m.sum()), rms=float(np.sqrt(np.mean(res ** 2))),
                Erange=(float(E[m].min()), float(E[m].max())))


def delta_from_ere(pair, E, a0, r0, P=0.0):
    """Phase shift (deg, in (0, 180)) that has exactly these ERE parameters."""
    E = np.asarray(E, float); k = pair.k(E); e = pair.eta(E)
    K = -1.0 / a0 + 0.5 * r0 * k ** 2 + P * k ** 4
    d = np.arctan2(C0sq(e) * k, K - 2 * k * e * hfun(e))
    return np.degrees(d)


def unwrap_from_threshold(E, delta_deg):
    """Unwrap a phase curve along E and reference it to its first point."""
    o = np.argsort(E)
    y = np.degrees(np.unwrap(2 * np.radians(np.asarray(delta_deg, float)[o])) / 2)
    return np.asarray(E, float)[o], y - y[0]


# ---------------------------------------------------- one-level R-matrix s wave
@lru_cache(maxsize=200000)
def _coul(l, eta, rho):
    F = float(mp.coulombf(l, eta, rho)); G = float(mp.coulombg(l, eta, rho))
    F1 = float(mp.coulombf(l + 1, eta, rho)); G1 = float(mp.coulombg(l + 1, eta, rho))
    L = l + 1.0; S = L / rho + eta / L; R = np.sqrt(1 + (eta / L) ** 2)
    return F, G, S * F - R * F1, S * G - R * G1


def PS(pair, l, E, a):
    """Penetrability and shift function at radius a."""
    k, eta = float(pair.k(E)), float(pair.eta(E))
    F, G, dF, dG = _coul(l, round(eta, 12), round(k * a, 12))
    den = F * F + G * G
    return k * a / den, k * a * (F * dF + G * dG) / den


def gamma2_W(pair, a):
    """Wigner unit hbar^2/(mu a^2), MeV."""
    return HBARC ** 2 / (pair.mu * a * a)


def delta_onepole(pair, E, E_lam, theta2, a):
    """s-wave phase (deg) of one level at E_lam (c.m.) with theta^2 (units of hbar^2/mu a^2),
    B = S(E_lam) so that E_lam is the observed resonance energy of a narrow level."""
    E = np.atleast_1d(np.asarray(E, float))
    gam2 = theta2 * gamma2_W(pair, a)
    B = PS(pair, 0, E_lam, a)[1]
    out = []
    for e in E:
        P, S = PS(pair, 0, e, a)
        k, eta = float(pair.k(e)), float(pair.eta(e))
        F, G, _, _ = _coul(0, round(eta, 12), round(k * a, 12))
        R = gam2 / (E_lam - e)
        out.append(-np.arctan2(F, G) + np.arctan2(P * R, 1.0 - (S - B) * R))
    return np.degrees(np.unwrap(2 * np.array(out)) / 2)


def a0_onepole(pair, E_lam, theta2, a, emin=0.20, emax=2.00):
    Es = np.linspace(emin, emax, 60)
    return fit_ere(pair, Es, delta_onepole(pair, Es, E_lam, theta2, a), emin, emax, order=2)


def theta2_for_a0(pair, E_lam, a0_target, a, emin=0.20, emax=2.00, tmax=3.5):
    """theta^2 a single level at E_lam needs to give a0_target (branch below the
    crossing of the effective-range function); nan if none below tmax."""
    f = lambda t: 1.0 / a0_onepole(pair, E_lam, t, a, emin, emax)["a0"] - 1.0 / a0_target
    lo, hi = 1e-4, 0.05
    while hi < tmax and f(hi) < 0:
        hi *= 1.35
    try:
        return brentq(f, lo, min(hi, tmax), xtol=1e-5)
    except ValueError:
        return float("nan")


# ---- charged hard sphere: the reference a large Coulomb-modified a0 must be compared with
def delta_hard_sphere(pair, E, R, l=0):
    """Phase (deg) of a charged hard sphere of radius R: delta = -atan(F_l(kR)/G_l(kR))."""
    out = []
    for e in np.atleast_1d(np.asarray(E, float)):
        k, eta = float(pair.k(e)), float(pair.eta(e))
        F, G, _, _ = _coul(l, round(eta, 12), round(k * R, 12))
        out.append(-np.arctan2(F, G))
    return np.degrees(np.unwrap(2 * np.array(out)) / 2)


def ere_hard_sphere(pair, R, emin=0.20, emax=2.00):
    """a0, r0 of a charged hard sphere of radius R with the same recipe as fit_ere."""
    Es = np.linspace(emin, emax, 60)
    return fit_ere(pair, Es, delta_hard_sphere(pair, Es, R), emin, emax, order=2)


def core_radius(pair, E, delta_deg):
    """Equivalent hard-sphere radius (fm) of a phase delta (deg, any branch) at one energy.
    Tracking it against E shows whether a phase is one hard sphere (constant) or not."""
    d = (float(delta_deg) + 90.0) % 180.0 - 90.0
    f = lambda R: float(delta_hard_sphere(pair, E, R)[0]) - d
    return brentq(f, 0.2, 8.0)
