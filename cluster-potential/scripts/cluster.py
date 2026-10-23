"""Two-body cluster model: deep local potentials with Pauli-forbidden states.

A light nucleus as two clusters in relative motion (alpha+3He, alpha+t,
alpha+d, alpha+alpha, ...).  Gaussian nuclear well (Buck-type, deep enough to
bind the Pauli-forbidden states) plus the Coulomb potential of a uniformly
charged sphere.  Bound states by finite differences (exact node counting),
scattering by Numerov matched to Coulomb functions, and the R-matrix quantities
the potential implies: penetrability, shift function, Wigner unit, single-
particle reduced width, ANC.  Also the RGM norm-kernel eigenvalues mu_N of two
0s clusters, which say which relative-motion shells are forbidden and how the
allowed ones are renormalized.

Generalized from the 7Be study (alpha+3He, a3he.py and at.py there).  Every
function takes a System, so mirrors and other partitions use the same code.

Units: MeV, fm.  Energies E are c.m. energies relative to the cluster threshold
(negative = bound).
"""
from dataclasses import dataclass
from functools import lru_cache
from math import comb

import mpmath as mp
import numpy as np
from scipy.linalg import eigh_tridiagonal

HBARC = 197.3269804
E2 = 1.4399764
U_MEV = 931.49410242
ME = 0.51099895

# nuclear masses in MeV
MASS = {"n": 939.56542052, "p": 938.27208816, "d": 1875.61294257, "t": 2808.92113298,
        "3He": 2808.39160743, "alpha": 3727.3794066}
CHARGE = {"n": 0, "p": 1, "d": 1, "t": 1, "3He": 2, "alpha": 2}
NUCLEONS = {"n": 1, "p": 1, "d": 2, "t": 3, "3He": 3, "alpha": 4}


@dataclass(frozen=True)
class System:
    """Two clusters.  thr_ex: E_x of the threshold in the compound nucleus;
    n_min: lowest allowed number of oscillator quanta N = 2n + l of the relative
    motion (Wildermuth condition); Rc: Coulomb radius of the uniform sphere."""
    c1: str
    c2: str
    thr_ex: float = 0.0
    n_min: int = 0
    Rc: float = 3.095

    @property
    def m1(self): return MASS[self.c1]
    @property
    def m2(self): return MASS[self.c2]
    @property
    def zz(self): return CHARGE[self.c1] * CHARGE[self.c2]
    @property
    def mu(self): return self.m1 * self.m2 / (self.m1 + self.m2)
    @property
    def h2m(self): return HBARC ** 2 / (2.0 * self.mu)


def s_shell_n_min(c1, c2):
    """N_min for two s-shell clusters with 4 < A <= 16: the A-4 nucleons above
    the 0s shell each carry one quantum (alpha+3He, alpha+t: 3; alpha+d: 2;
    alpha+alpha: 4).  For A <= 4 everything is allowed."""
    A = NUCLEONS[c1] + NUCLEONS[c2]
    if A > 16:
        raise ValueError("beyond the p shell: count the quanta of the shell-model ground configuration")
    return max(0, A - 4)


# ------------------------------------------------------------------ potential
class Pot:
    """V(r) = -V0 exp(-(r/a)^2) + V_C(r), uniformly charged sphere of radius Rc."""

    def __init__(self, system, V0, a, Rc=None):
        self.s, self.V0, self.a = system, V0, a
        self.Rc = system.Rc if Rc is None else Rc

    def __call__(self, r):
        r = np.asarray(r, float)
        Rc, zz = self.Rc, self.s.zz
        vc = np.where(r >= Rc, zz * E2 / np.maximum(r, 1e-30), zz * E2 / (2 * Rc) * (3.0 - (r / Rc) ** 2))
        return -self.V0 * np.exp(-(r / self.a) ** 2) + vc


# ------------------------------------------------------------ Coulomb functions
@lru_cache(maxsize=200000)
def coul(l, eta, rho):
    """F_l, G_l and their rho-derivatives (from the l+1 recurrence)."""
    F = float(mp.coulombf(l, eta, rho)); G = float(mp.coulombg(l, eta, rho))
    F1 = float(mp.coulombf(l + 1, eta, rho)); G1 = float(mp.coulombg(l + 1, eta, rho))
    L = l + 1.0
    S = L / rho + eta / L
    R = np.sqrt(1.0 + (eta / L) ** 2)
    return F, G, S * F - R * F1, S * G - R * G1


def kinematics(system, E):
    k = np.sqrt(2 * system.mu * E) / HBARC
    return k, system.zz * E2 * system.mu / (HBARC ** 2 * k)


def coul_at(system, l, E, r):
    """(k, eta, F, G, dF/dr, dG/dr) at radius r."""
    k, eta = kinematics(system, E)
    F, G, dF, dG = coul(l, round(eta, 12), round(k * r, 12))
    return k, eta, F, G, dF * k, dG * k


# ------------------------------------------------------- bound states (exact)
@lru_cache(maxsize=64)
def _fdgrid(rbox, N):
    r = np.linspace(rbox / (N + 1), rbox * N / (N + 1), N)
    return r, r[1] - r[0]


def bound_states(pot, l, rbox=40.0, N=4000, nmax=6):
    """Lowest eigenstates in a box: (energies, vectors, r, interior nodes)."""
    r, h = _fdgrid(rbox, N)
    h2m = pot.s.h2m
    diag = 2 * h2m / h ** 2 + pot(r) + h2m * l * (l + 1) / r ** 2
    off = -h2m / h ** 2 * np.ones(N - 1)
    w, v = eigh_tridiagonal(diag, off, select="i", select_range=(0, nmax - 1))
    nodes = []
    for j in range(v.shape[1]):
        u = v[:, j]; s = np.sign(u[np.abs(u) > 1e-8 * np.abs(u).max()])
        nodes.append(int(np.sum(s[1:] * s[:-1] < 0)))
    return w, v, r, nodes


def level(pot, l, nodes, **kw):
    """Energy of the bound state with this many nodes (None if unbound)."""
    w, _v, _r, nn = bound_states(pot, l, **kw)
    for E, k in zip(w, nn):
        if k == nodes:
            return E if E < 0 else None
    return None


def fit_V0_bound(system, l, nodes, Etarget, a, Rc=None, lo=1.0, hi=400.0):
    """Depth that puts the state with `nodes` nodes at Etarget (bisection)."""
    for _ in range(90):
        m = 0.5 * (lo + hi)
        E = level(Pot(system, m, a, Rc), l, nodes)
        if E is None or E > Etarget:
            lo = m
        else:
            hi = m
        if hi - lo < 1e-9:
            break
    return 0.5 * (lo + hi)


# ------------------------------------------------------------------ scattering
def numerov(pot, l, E, rmax=14.0, n=3000):
    r = np.linspace(rmax / n, rmax, n); h = r[1] - r[0]
    f = (pot(r) - E) / pot.s.h2m + l * (l + 1) / r ** 2
    u = np.zeros(n); u[0] = r[0] ** (l + 1); u[1] = r[1] ** (l + 1)
    c = h * h / 12.0
    for i in range(1, n - 1):
        u[i + 1] = ((2 + 10 * c * f[i]) * u[i] - (1 - c * f[i - 1]) * u[i - 1]) / (1 - c * f[i + 1])
        if abs(u[i + 1]) > 1e200:
            u[:i + 2] *= 1e-200
    return r, u, h


def phase_shift(pot, l, E, rmax=14.0, n=3000):
    """Nuclear phase shift (rad, relative to Coulomb), matched at rmax."""
    r, u, h = numerov(pot, l, E, rmax, n)
    L = ((-u[-5] + 8 * u[-4] - 8 * u[-2] + u[-1]) / (-12 * h)) / u[-3]
    k, eta, F, G, dF, dG = coul_at(pot.s, l, E, r[-3])
    return np.arctan2(L * F - dF, dG - L * G)


def delta_curve(pot, l, Es, **kw):
    """Phase shift on a grid, unwrapped (mod pi ambiguity removed along E)."""
    d = np.array([phase_shift(pot, l, E, **kw) for E in Es])
    return np.unwrap(2 * d) / 2


def first_resonance(pot, l, elo=0.02, ehi=14.0, npts=350):
    """Lowest E where delta(E)-delta(elo) rises through pi/2, and Gamma = 2/(d delta/dE).
    None if it never does (no resonance in this wave)."""
    Es = np.linspace(elo, ehi, npts)
    d = delta_curve(pot, l, Es); d = d - d[0]
    idx = np.where((d[:-1] < np.pi / 2) & (d[1:] >= np.pi / 2))[0]
    if len(idx) == 0:
        return None
    lo, hi = Es[idx[0]], Es[idx[0] + 1]
    f = lambda E: np.diff(delta_curve(pot, l, np.array([elo, E])))[0] - np.pi / 2
    for _ in range(40):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if f(m) < 0 else (lo, m)
        if hi - lo < 1e-7:
            break
    Er = 0.5 * (lo + hi); h = max(1e-3, 0.002 * Er)
    dd = np.diff(delta_curve(pot, l, np.array([Er - h, Er + h])))[0] / (2 * h)
    return Er, 2.0 / dd


def fit_V0_resonance(system, l, Etarget, a, Rc=None, lo=1.0, hi=400.0, **kw):
    """Depth that puts the first resonance of this wave at Etarget."""
    for _ in range(40):
        m = 0.5 * (lo + hi)
        r = first_resonance(Pot(system, m, a, Rc), l, **kw)
        lo, hi = (m, hi) if (r[0] if r else 1e9) > Etarget else (lo, m)
        if hi - lo < 1e-6:
            break
    return 0.5 * (lo + hi)


# ------------------------------------------------------ R-matrix observables
def PS(system, l, E, a):
    """Penetrability P_l and shift function S_l at channel radius a (E > 0)."""
    k, eta, F, G, dF, dG = coul_at(system, l, E, a)
    den = F * F + G * G
    return (k * a) / den, a * (F * dF + G * dG) / den


def gamma2_W(system, a):
    """Wigner unit hbar^2/(mu a^2) in MeV (theta^2 = gamma^2 / gamma2_W)."""
    return HBARC ** 2 / (system.mu * a * a)


def theta2_from_width(system, Gamma, E, l, a):
    """Dimensionless reduced width of a single isolated level: Gamma = 2 P gamma^2."""
    P, _ = PS(system, l, E, a)
    return Gamma / (2 * P * gamma2_W(system, a))


def sp_reduced_width(pot, l, E, a, rbox=40.0, N=4000):
    """gamma^2 = (hbar^2/2 mu a) u(a)^2 of the bound state nearest E (u normalized)."""
    w, v, r, _nn = bound_states(pot, l, rbox=rbox, N=N)
    j = int(np.argmin(np.abs(w - E)))
    u = v[:, j] / np.sqrt(r[1] - r[0])
    return (pot.s.h2m / a) * np.interp(a, r, u) ** 2


def anc(pot, l, E, rmatch=8.0, rbox=40.0, N=4000):
    """ANC C (fm^-1/2) of the bound state nearest E: u(r) -> C W_{-eta,l+1/2}(2kr)."""
    w, v, r, _nn = bound_states(pot, l, rbox=rbox, N=N)
    j = int(np.argmin(np.abs(w - E)))
    u = v[:, j] / np.sqrt(r[1] - r[0])
    kb = np.sqrt(2 * pot.s.mu * abs(E)) / HBARC
    etb = pot.s.zz * E2 * pot.s.mu / (HBARC ** 2 * kb)
    return np.interp(rmatch, r, u) / float(mp.whitw(-etb, l + 0.5, 2 * kb * rmatch))


# ------------------------------------------------------------ Pauli bookkeeping
def n_forbidden(system, l):
    """Number of Pauli-forbidden relative states of this l: N = 2n + l < n_min."""
    return sum(1 for n in range(0, 10) if 2 * n + l < system.n_min)


def pauli_ok(pot, l):
    """True if the potential binds the forbidden states (and possibly the
    physical bound state above them) -- the admissibility condition of a deep potential."""
    w, *_ = bound_states(pot, l, nmax=8)
    nb = int(np.sum(w < 0)); nf = n_forbidden(pot.s, l)
    return nb in (nf, nf + 1)


def norm_kernel_mu(N, A1, A2, weights):
    """RGM norm-kernel eigenvalue of two 0s clusters on an N-quantum relative state:
    mu_N = sum_k (-1)^k w_k (1 - k A/(A1 A2))^N  (Horiuchi 1977).  mu_N = 0: forbidden."""
    A = A1 + A2
    return sum((-1) ** k * w * (1 - k * A / (A1 * A2)) ** N for k, w in weights.items())


def alpha_x_weights(x):
    """Exchange weights for alpha + an s-shell cluster x (n, p, d, t, 3He): every
    nucleon of x has exactly one same-spin-isospin partner in alpha, w_k = C(A_x, k)."""
    ax = NUCLEONS[x]
    return {k: comb(ax, k) for k in range(ax + 1)}
