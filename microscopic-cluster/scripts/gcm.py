"""Microscopic two-cluster model: GCM kernels of 0s clusters and the microscopic R-matrix.

All nucleons are antisymmetrized.  Both clusters are 0s configurations in a
common oscillator of width b (Brink wave functions); the nucleon-nucleon force
is the Minnesota force (Thompson, LeMere and Tang, Nucl. Phys. A286 (1977) 53)
plus Coulomb between protons.  Its exchange-mixture parameter u is the only
adjustable quantity.  The Hamiltonian kernel is linear in u, so kernels are
built once at u = 0 and u = 1 (build_kernels) and interpolated (H_of).

Generator coordinate R: cluster 1 at +A2/A R, cluster 2 at -A1/A R, so the
centre of mass sits at the origin in every basis state.  Overlap, kinetic,
nuclear and Coulomb kernels between Slater determinants follow from the
Loewdin formulas; the c.m. kinetic energy 3 hbar^2/(4 m b^2) is removed.
Kernels are projected on the orbital angular momentum l (no spin-orbit force,
so J = l +- s are degenerate) by Gauss-Legendre integration over the angle
between R and R'.

Scattering: the microscopic R-matrix of Baye, Heenen and Libert-Heinemann,
Nucl. Phys. A291 (1977) 230.  Inside the channel radius a the full kernels,
outside the relative motion under point Coulomb; Pauli-forbidden directions
are removed by diagonalizing the internal norm kernel (threshold eps).

Generalized from the 7Be study (alpha+3He).  Call configure(c1, c2) first;
clusters: n, p, d, t, 3He, alpha (all 0s).  Units MeV, fm.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.special import erf, eval_legendre, ive
from scipy.linalg import eigh

HB2M  = 41.4711          # hbar^2/m, MeV fm^2 (the Minnesota convention)
E2    = 1.439965
# 0s clusters as (spin, isospin) labels of their nucleons
CLUSTERS = {
    "n": [(+1, 'n')], "p": [(+1, 'p')],
    "d": [(+1, 'p'), (+1, 'n')],                       # S = 1, M = 1 Brink deuteron
    "t": [(+1, 'n'), (-1, 'n'), (+1, 'p')],
    "3He": [(+1, 'p'), (-1, 'p'), (+1, 'n')],
    "alpha": [(+1, 'p'), (-1, 'p'), (+1, 'n'), (-1, 'n')],
}
ALPHA, HE3 = CLUSTERS["alpha"], CLUSTERS["3He"]
A1, A2 = 4, 3
MU_A  = A1 * A2 / (A1 + A2)          # reduced mass number
Z1Z2  = 4
C1, C2 = "alpha", "3He"


def configure(c1, c2):
    """Select the two clusters (default alpha + 3He).  Sets the module globals."""
    global A1, A2, MU_A, Z1Z2, LABELS, C1, C2
    l1, l2 = CLUSTERS[c1], CLUSTERS[c2]
    C1, C2 = c1, c2
    A1, A2 = len(l1), len(l2)
    MU_A = A1 * A2 / (A1 + A2)
    Z1Z2 = sum(t == 'p' for _, t in l1) * sum(t == 'p' for _, t in l2)
    LABELS = l1 + l2

MINNESOTA = dict(VR=200.0, kR=1.487, Vt=-178.0, kt=0.639, Vs=-91.85, ks=0.465)


# --------------------------------------------------------------- determinants
def det_kernel(ca, cb, labels, b, u):
    """Overlap N and <H> N between two Slater determinants of 0s Gaussians.

    ca, cb: (n,3) arrays of centres for bra and ket; labels: list of (spin, iso).
    Returns (N, H) with H the full Hamiltonian kernel (no c.m. correction)."""
    n = len(labels)
    s = np.array([l[0] for l in labels]); t = np.array([l[1] == 'p' for l in labels])
    Ds = (s[:, None] == s[None, :]); Dt = (t[:, None] == t[None, :])
    dac = ca[:, None, :] - cb[None, :, :]
    r2 = np.einsum('ikx,ikx->ik', dac, dac)
    O = np.exp(-r2 / (4 * b * b))
    lab = Ds & Dt
    B = O * lab
    det = np.linalg.det(B)
    if abs(det) < 1e-300:
        return 0.0, 0.0
    Bi = np.linalg.inv(B)
    # one-body kinetic
    tik = 0.5 * HB2M * (1 / (2 * b * b)) * (3 - r2 / (2 * b * b)) * B
    E1 = np.einsum('ik,ki->', tik, Bi)
    # two-body: centres of the product densities
    M = 0.5 * (ca[:, None, :] + cb[None, :, :])                    # (i,k,3)
    dM = M[:, :, None, None, :] - M[None, None, :, :, :]            # (i,k,j,l,3)
    D2 = np.einsum('ikjlx,ikjlx->ikjl', dM, dM)
    OO = O[:, :, None, None] * O[None, None, :, :]                  # O_ik O_jl
    def gauss(k):
        f = 1 + 2 * k * b * b
        return OO * f ** -1.5 * np.exp(-k * D2 / f)
    p = MINNESOTA
    gR, gt, gs = gauss(p['kR']), gauss(p['kt']), gauss(p['ks'])
    A_ = p['VR'] * gR + 0.5 * p['Vt'] * gt + 0.5 * p['Vs'] * gs    # spin independent
    S_ = 0.5 * p['Vt'] * gt - 0.5 * p['Vs'] * gs                   # times P_sigma
    # label deltas, indexed [i,k,j,l]
    d_dir = (lab[:, :, None, None] & lab[None, None, :, :])
    # P_sigma on the ket |k l>: spins of k and l swapped
    d_sig = ((s[:, None, None, None] == s[None, None, None, :]) &      # s_i = s_l
             (s[None, None, :, None] == s[None, :, None, None]) &      # s_j = s_k
             Dt[:, :, None, None] & Dt[None, None, :, :])
    # space exchange P_r: swap the spatial labels k <-> l  -> I[i,l,j,k]
    swap = lambda X: np.transpose(X, (0, 3, 2, 1))
    V = 0.5 * u * (A_ * d_dir + S_ * d_sig) \
        + 0.5 * (2 - u) * (swap(A_) * d_dir + swap(S_) * d_sig)
    # Coulomb between protons
    Dd = np.sqrt(D2)
    with np.errstate(invalid='ignore', divide='ignore'):
        cf = np.where(Dd > 1e-9, erf(Dd / (np.sqrt(2) * b)) / Dd, np.sqrt(2 / np.pi) / b)
    pp = t[:, None, None, None] & t[None, None, :, None]
    V = V + E2 * OO * cf * d_dir * pp
    # antisymmetrize over the ket pair (k,l): <ij|v|kl> - <ij|v|lk>
    VA = V - swap(V)
    E2b = 0.5 * np.einsum('ikjl,ki,lj->', VA, Bi, Bi)
    return det, det * (E1 + E2b)


def t_cm(b):
    """c.m. kinetic energy of an A-nucleon 0s Brink state: 3 hbar^2/(4 m b^2)."""
    return 0.75 * HB2M / (b * b)


def cluster_energy(labels, b, u):
    c = np.zeros((len(labels), 3))
    N, H = det_kernel(c, c, labels, b, u)
    return H / N - t_cm(b)


def centres(R, direction):
    d = np.asarray(direction, float); d = d / np.linalg.norm(d)
    ca = np.array([(A2 / (A1 + A2)) * R * d] * A1 + [-(A1 / (A1 + A2)) * R * d] * A2)
    return ca


LABELS = ALPHA + HE3


def projected_kernels(Rs, ls, b, u, nang=96):
    """{l: (N_l, H_l)} on the generator grid Rs, c.m. kinetic energy removed."""
    x, w = leggauss(nang)
    Pl = {l: eval_legendre(l, x) for l in ls}
    n = len(Rs)
    out = {l: (np.zeros((n, n)), np.zeros((n, n))) for l in ls}
    tc = t_cm(b)
    for i, R in enumerate(Rs):
        ca = centres(R, (0, 0, 1))
        for j in range(i, n):
            Nth = np.empty(nang); Hth = np.empty(nang)
            for q, c in enumerate(x):
                cb = centres(Rs[j], (np.sqrt(max(0.0, 1 - c * c)), 0, c))
                Nq, Hq = det_kernel(ca, cb, LABELS, b, u)
                Nth[q] = Nq; Hth[q] = Hq - tc * Nq
            for l in ls:
                Nl = 0.5 * np.sum(w * Pl[l] * Nth)
                Hl = 0.5 * np.sum(w * Pl[l] * Hth)
                out[l][0][i, j] = out[l][0][j, i] = Nl
                out[l][1][i, j] = out[l][1][j, i] = Hl
    return out


# ---------------------------------------------------------- relative motion
def u_rel(l, R, rho, b):
    """Projected relative Gaussian rho * Gamma_l(rho; R), normalized so that
    int u_R u_R' drho equals the l-projected direct overlap kernel."""
    beta = MU_A / (2 * b * b)
    C = (MU_A / (np.pi * b * b)) ** 0.75
    z = 2 * beta * rho * R
    # i_l(z) = sqrt(pi/2z) I_{l+1/2}(z);  ive = I * exp(-z)
    il_scaled = np.sqrt(np.pi / (2 * z)) * ive(l + 0.5, z)          # i_l(z) e^{-z}
    return np.sqrt(4 * np.pi) * C * rho * np.exp(-beta * (rho - R) ** 2) * il_scaled


def hb2mu():
    return 0.5 * HB2M / MU_A


# ---------------------------------------------------------- Coulomb functions
def coulomb_FG(l, eta, x):
    import mpmath as mp
    F = float(mp.coulombf(l, eta, x)); G = float(mp.coulombg(l, eta, x))
    h = 1e-6 * max(1.0, x)
    dF = float((mp.coulombf(l, eta, x + h) - mp.coulombf(l, eta, x - h)) / (2 * h))
    dG = float((mp.coulombg(l, eta, x + h) - mp.coulombg(l, eta, x - h)) / (2 * h))
    return F, G, dF, dG


# ---------------------------------------------------------------- R-matrix
class RMatrix:
    """Microscopic R-matrix for one partial wave."""

    def __init__(self, l, Rs, N, H, b, Ethr, a, eps=1e-7):
        self.l, self.b, self.a, self.Ethr = l, b, a, Ethr
        rho = np.linspace(a, a + 25.0, 5001); h = rho[1] - rho[0]
        U = np.array([u_rel(l, R, rho, b) for R in Rs])             # (n, nrho)
        d2 = np.gradient(np.gradient(U, h, axis=1), h, axis=1)
        k2 = hb2mu()
        TU = k2 * (-d2 + l * (l + 1) / rho ** 2 * U)
        VU = (Z1Z2 * E2 / rho + Ethr) * U
        wq = np.full(rho.size, h); wq[0] = wq[-1] = 0.5 * h
        self.Next = (U * wq) @ U.T
        self.Hext = (U * wq) @ (TU + VU).T
        self.Nint = N - self.Next
        self.Hint = H - self.Hext
        ua = U[:, 0]
        dua = (np.array([u_rel(l, R, np.array([a + 1e-4]), b)[0] for R in Rs]) -
               np.array([u_rel(l, R, np.array([a - 1e-4]), b)[0] for R in Rs])) / 2e-4
        self.L = k2 * np.outer(ua, dua)                              # Bloch, B = 0
        lam, V = eigh(self.Nint)
        keep = lam > eps * lam.max()
        self.nkept = int(keep.sum()); self.lam = lam
        T = V[:, keep] / np.sqrt(lam[keep])
        self.T = T
        # H_int + L is exactly symmetric (the Bloch term cancels the surface term of
        # the truncated kinetic energy); symmetrize only the quadrature residual
        HL = self.Hint + self.L
        self.asym = float(np.abs(HL - HL.T).max() / np.abs(HL).max())
        HL = 0.5 * (HL + HL.T)
        self.Hk = T.T @ HL @ T
        self.wa = T.T @ ua

    def phase(self, Ecm):
        k2 = hb2mu()
        C = self.Hk - (self.Ethr + Ecm) * np.eye(self.nkept)
        R = k2 / self.a * self.wa @ np.linalg.solve(C, self.wa)
        k = np.sqrt(Ecm / k2)
        eta = Z1Z2 * E2 / (2 * k2 * k)
        x = k * self.a
        F, G, dF, dG = coulomb_FG(self.l, eta, x)
        # u(a) = R a u'(a)  ->  tan(delta) = -(F - R x F')/(G - R x G')
        return np.arctan2(-(F - R * x * dF), (G - R * x * dG))


def bound_energy(N, H, eps=1e-7):
    lam, V = eigh(N)
    keep = lam > eps * lam.max()
    T = V[:, keep] / np.sqrt(lam[keep])
    return eigh(T.T @ H @ T, eigvals_only=True)


# ---------------------------------------------------------------- checks
def check_structure(b=1.40, u=1.0, nmin=3):
    """(1) small-R limit of the projected norm kernel -> mu_N for N = nmin, nmin+1
       (l = N, a single oscillator shell); (2) large-R limit -> direct overlap."""
    from math import comb
    if C1 != "alpha":
        raise NotImplementedError("the mu_N check is coded for alpha + an s-shell cluster")
    A = A1 + A2
    mu = lambda N: sum((-1) ** k * comb(A2, k) * (1 - A * k / (A1 * A2)) ** N for k in range(A2 + 1))
    out = {}
    Rs = np.array([0.35, 0.40])
    K = projected_kernels(Rs, [nmin, nmin + 1], b, u, nang=48)
    rho = np.linspace(1e-4, 40, 40001); h = rho[1] - rho[0]
    for l, Nmin in ((nmin, nmin), (nmin + 1, nmin + 1)):
        Nd = np.array([[np.sum(u_rel(l, Ri, rho, b) * u_rel(l, Rj, rho, b)) * h
                        for Rj in Rs] for Ri in Rs])
        ratio = K[l][0][1, 1] / Nd[1, 1]
        out[f'mu_{Nmin} (l={l})'] = (ratio, mu(Nmin))
    Rs2 = np.array([9.0, 10.0])
    K2 = projected_kernels(Rs2, [0, 2], b, u, nang=96)
    for l in (0, 2):
        Nd = np.sum(u_rel(l, 9.0, rho, b) * u_rel(l, 10.0, rho, b)) * h
        cl = cluster_overlap_norm(b)
        out[f'large-R N_{l}/direct'] = (K2[l][0][0, 1] / (Nd * cl), 1.0)
    return out


def cluster_overlap_norm(b):
    """Intrinsic norm of the two normalized 0s clusters = 1."""
    return 1.0


# ------------------------------------------------------------ drivers
def build_kernels(Rs, ls, b, nang=96):
    """Projected kernels at u = 0 and u = 1, and the model threshold energy.
    Returns (K, Ethr) with K[(l, u)] = (N_l, H_l)."""
    K = {}
    for u in (0.0, 1.0):
        P = projected_kernels(Rs, ls, b, u, nang=nang)
        for l in P:
            K[(l, u)] = P[l]
    Ethr = cluster_energy(CLUSTERS[C1], b, 1.0) + cluster_energy(CLUSTERS[C2], b, 1.0)
    return K, Ethr


def H_of(K, l, u):
    """Hamiltonian kernel at exchange parameter u (linear in u)."""
    return K[(l, 0.0)][1] + u * (K[(l, 1.0)][1] - K[(l, 0.0)][1])


def rmatrix(K, Ethr, Rs, b, l, u, a=8.0, eps=1e-7):
    return RMatrix(l, Rs, K[(l, 0.0)][0], H_of(K, l, u), b, Ethr, a, eps=eps)


def phase_curve(rm, Es):
    """Phase (deg) on Es, unwrapped, with the n*180 offset of forbidden states removed."""
    d = np.array([rm.phase(E) for E in Es])
    d = np.degrees(np.unwrap(2 * d) / 2)
    return d - 180.0 * np.round(d[0] / 180.0)


def fit_u_bound(K, Ethr, l, Etarget, lo=0.7, hi=1.3):
    """u that puts the lowest physical bound state of wave l at Etarget (relative to threshold)."""
    from scipy.optimize import brentq
    f = lambda u: bound_energy(K[(l, 0.0)][0], H_of(K, l, u))[0] - Ethr - Etarget
    return brentq(f, lo, hi, xtol=1e-6)


if __name__ == '__main__':
    for k, (got, want) in check_structure().items():
        print(f"{k:>22}: {got:.5f}   expected {want:.5f}")
