"""The posterior of an AZURE2 evaluation, in whitened coordinates.

log p(x) = -objective(x) / (2 T), where

  objective = data chi-squared (pyazr ``calculate_chi2_rwa`` / ``chi2_and_grad``)
            + AZURE2's own prior terms (normalizations, energy shifts, screening),
              exactly as pyazr ``azure2.objective`` adds them
            + width priors: theta = gamma / gamma_W ~ N(0, theta_scale^2) for every particle
              channel of a physical level and N(0, bg_scale^2) for background poles (level
              energy >= bg_energy); gamma_W^2 = ``Parameter.wigner_limit`` (MeV, already squared)
            + optionally the ENDF-transformability constraint as a smooth prior
              (SoftTransformability): lambda_max(K_g) <= tau per J^pi group and
              |D_l| <= E_target per level, each hinge max(0, u) replaced by a softplus of
              width `soft`; shift functions frozen at the reference parameters.

T = 1 is the posterior of the quoted uncertainties; T = chi2/ndf corresponds to the
covariance scaled by sqrt(chi2/ndf).

Whitening: the sampler works in z with x = x_ref + L z, L = V diag(lam^-1/2) sqrt(T), from
H = V diag(lam) V^T, the Hessian of objective/2 at x_ref.  Use the exact Hessian at the MAP
(find_map.py writes it to map.npz); Gauss-Newton J^T J at the best fit is only the bootstrap.
The map is linear, so it adds no Jacobian term to log p.

The transformability prior needs a ``poles.py`` module (the user's, built on Ferdinand's
Coulomb functions) with ``structure(azr, parameters)`` and ``shifts(grp, x, epar)``; see
references/method.md.  Without --poles the prior is off and the run says so.

Nothing here is specific to one nucleus.  pyazr is imported only when a Posterior is built,
so whitening() and SoftTransformability work without AZURE2 (selftest.py).
"""
import importlib.util
import os

import numpy as np


# ---------------------------------------------------------------- whitening
def whitening(H, temperature=1.0, floor=1e-8):
    """(L, Linv, lam) with x = x_ref + L z; eigenvalues floored at floor * max |lam|."""
    H = 0.5 * (np.asarray(H, float) + np.asarray(H, float).T)
    lam, V = np.linalg.eigh(H)
    lam_f = np.maximum(np.abs(lam), floor * np.abs(lam).max())
    L = V * (np.sqrt(temperature) / np.sqrt(lam_f))
    Linv = (V * (np.sqrt(lam_f) / np.sqrt(temperature))).T
    return L, Linv, lam


# ---------------------------------------------------------------- physicality
def softplus(u, s):
    """s * log(1 + exp(u / s)) and its derivative; -> max(0, u) as s -> 0."""
    t = u / s
    return s * np.logaddexp(0.0, t), 0.5 * (1.0 + np.tanh(0.5 * t))


class SoftTransformability:
    """Soft ENDF-transformability penalty on the reduced-width amplitudes x.

    groups: list of (n_levels, pairs, levels) with
      pairs  = [(a, b, fi_a, fi_b, W_ab)]  ordered level pairs sharing a channel, where
               W_ab = (S_c(E_a) - S_c(E_b)) / (E_a - E_b) and fi = free index of gamma (or None)
      levels = [(E_l, [(fi, S_c(E_l) - B_c)])]
    penalty = sum_g w_lam softplus(lambda_max(K_g) - tau)^2 + sum_l w_pole softplus(ln|D_l| - ln E_t)^2
    with K_ab = sum_c gamma_ac gamma_bc W_ab,c and D_l = E_l + sum_c gamma_lc^2 (S - B).
    """

    def __init__(self, groups, tau=0.70, etarget=300.0, w_lam=2000.0, w_pole=200.0, soft=0.01):
        self.groups, self.tau, self.lnT, self.s = groups, tau, np.log(etarget), soft
        self.w1, self.w2 = np.sqrt(w_lam), np.sqrt(w_pole)

    def __call__(self, x, grad=True):
        g = lambda fi: x[fi] if fi is not None else 0.0
        val, G = 0.0, (np.zeros(x.size) if grad else None)
        for n, pairs, levels in self.groups:
            if n > 1 and pairs:
                K = np.zeros((n, n))
                for a, b, fa, fb, W in pairs:
                    K[a, b] += g(fa) * g(fb) * W
                ev, V = np.linalg.eigh(K)
                sp, sig = softplus(ev[-1] - self.tau, self.s)
                r = self.w1 * sp
                val += r * r
                if grad and sig > 1e-300:
                    v = V[:, -1]
                    for a, b, fa, fb, W in pairs:     # d lam / d gamma_a = 2 v_a v_b gamma_b W
                        if fa is not None:
                            G[fa] += 2 * r * self.w1 * sig * 2.0 * v[a] * v[b] * g(fb) * W
            for E, chans in levels:
                D = E + sum(g(fi) ** 2 * sb for fi, sb in chans)
                sp, sig = softplus(np.log(abs(D)) - self.lnT, self.s)
                r = self.w2 * sp
                val += r * r
                if grad and sig > 1e-300:
                    for fi, sb in chans:
                        if fi is not None:
                            G[fi] += 2 * r * self.w2 * sig * 2.0 * x[fi] * sb / D
        return val, G

    @classmethod
    def from_poles(cls, poles_path, azr, m, x_ref, single_level_groups=False, **kw):
        """Build the groups with the user's poles.py (structure, shifts) at x_ref."""
        spec = importlib.util.spec_from_file_location("poles", poles_path)
        poles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(poles)
        epar = {(p.jpi, p.level): p.free_index for p in m.parameters
                if p.kind == "energy" and not p.fixed and p.free_index is not None}
        grp = poles.structure(azr, m.parameters)
        if not single_level_groups:            # the 7Be evaluation's choice (refit_physical.py)
            grp = {j: v for j, v in grp.items() if len(v) > 1}
        S, B, E = poles.shifts(grp, x_ref, epar)
        groups = []
        for j in sorted(grp):
            ids = sorted(grp[j])
            pairs = []
            for a, la in enumerate(ids):
                for b, lb in enumerate(ids):
                    if a == b:
                        continue
                    for c in grp[j][la]["ch"]:
                        if c in grp[j][lb]["ch"]:
                            W = (S[(j, la, c)] - S[(j, lb, c)]) / (E[(j, la)] - E[(j, lb)])
                            pairs.append((a, b, grp[j][la]["ch"][c]["fi"], grp[j][lb]["ch"][c]["fi"], W))
            levels = [(E[(j, li)], [(grp[j][li]["ch"][c]["fi"], S[(j, li, c)] - B[(j, c)])
                                    for c in grp[j][li]["ch"]]) for li in ids]
            groups.append((len(ids), pairs, levels))
        return cls(groups, **kw)


# ---------------------------------------------------------------- the posterior
class Posterior:
    def __init__(self, azr, sav=None, cwd=None, temperature=1.0, theta_scale=1.0, bg_scale=10.0,
                 bg_energy=None, poles=None, phys_kw=None, reference=None, floor=1e-8):
        from pyazr import azure2, best_fit_params
        self.azr = azr
        self.m = azure2(azr, cwd=cwd or os.path.dirname(os.path.abspath(azr)))
        self.x_hat = np.asarray(best_fit_params(self.m, path=sav) if sav else self.m.params_rwa, float)
        self.n = self.x_hat.size
        self.T = float(temperature)
        self.theta_scale, self.bg_scale, self.bg_energy = theta_scale, bg_scale, bg_energy
        self._build_prior_rows()
        self.phys = (SoftTransformability.from_poles(poles, azr, self.m, self.x_hat, **(phys_kw or {}))
                     if poles else None)
        self.floor = floor
        if reference is None:
            r, J = self.residuals(self.x_hat)
            self.set_reference(self.x_hat, J.T @ J)
        else:
            d = np.load(reference)
            self.set_reference(d["x"], d["H"])

    # -- Gaussian prior rows ---------------------------------------------------
    def _build_prior_rows(self):
        """(free_index, nominal, sigma) per Gaussian prior term: AZURE2's own terms, mirroring
        pyazr ``penalties`` (a term on a fixed parameter is a constant and is left out), then
        the width priors."""
        m, rows, kinds = self.m, [], []
        P = m.parameters
        free = lambda p: (p is not None and not p.fixed and p.free_index is not None
                          and p.free_index < self.n)
        norms = {p.segment_key: p for p in P.norms}
        shifts = {p.segment_key: p for p in P.shifts}
        sqrts = {p.segment_key: p for p in P.sqrt_shifts}
        fns = {(p.segment_key, p.fn_term): p for p in P.fn_shifts}
        seen = set()
        for d in m.active_datasets:
            p = norms.get(d.key)
            sigma = d.norm / 100.0 * d.norm_error
            follower = bool(d.norm_group) and d.norm_group in seen
            if d.norm_group:
                seen.add(d.norm_group)
            if sigma and not follower and free(p):
                rows.append((p.free_index, d.norm, sigma)); kinds.append("azure2")
            q = shifts.get(d.key)
            if d.vary_shift and d.energy_shift_error and free(q):
                rows.append((q.free_index, 0.0, d.energy_shift_error)); kinds.append("azure2")
            q = sqrts.get(d.key)
            if d.vary_shift_sqrt and d.energy_shift_sqrt_error and free(q):
                rows.append((q.free_index, 0.0, d.energy_shift_sqrt_error)); kinds.append("azure2")
            for j, (nominal, sigma_j, vary) in enumerate(d.shift_fn_params):
                q = fns.get((d.key, j))
                if vary and sigma_j and free(q):
                    rows.append((q.free_index, 0.0, sigma_j)); kinds.append("azure2")
        for p in P.screenings:
            if free(p) and p.prior_sigma:
                rows.append((p.free_index, p.prior_nominal, p.prior_sigma)); kinds.append("azure2")
        self.theta_hat = {}
        if self.theta_scale:
            for p in P.widths:
                if not free(p) or p.radiation_type in ("E", "M") or not p.wigner_limit:
                    continue
                bg = (self.bg_energy is not None and p.level_energy is not None
                      and p.level_energy >= self.bg_energy)
                scale = self.bg_scale if bg else self.theta_scale
                rows.append((p.free_index, 0.0, scale * np.sqrt(p.wigner_limit)))
                kinds.append("theta_bg" if bg else "theta")
                self.theta_hat[p.free_index] = self.x_hat[p.free_index] / np.sqrt(p.wigner_limit)
        self.prior_idx = np.array([r[0] for r in rows], int)
        self.prior_nom = np.array([r[1] for r in rows], float)
        self.prior_sig = np.array([r[2] for r in rows], float)
        self.prior_kind = np.array(kinds)

    def large_theta(self, limit=3.0):
        """Free indices whose |theta| at the best fit exceeds `limit` under a physical-level prior:
        background poles that were not declared with --bg-energy."""
        return [i for i, k in zip(self.prior_idx, self.prior_kind)
                if k == "theta" and abs(self.theta_hat.get(i, 0.0)) > limit]

    def prior_residuals(self, x):
        return (x[self.prior_idx] - self.prior_nom) / self.prior_sig

    # -- x space -----------------------------------------------------------------
    def residuals(self, x):
        """Standardized residuals (data, then Gaussian prior rows) and their Jacobian."""
        r, J = self.m.residual_jacobian(x)
        rp = self.prior_residuals(x)
        Jp = np.zeros((rp.size, self.n))
        Jp[np.arange(rp.size), self.prior_idx] = 1.0 / self.prior_sig
        return np.concatenate([r, rp]), np.vstack([J, Jp])

    def parts(self, x):
        """The objective split into its terms (for reports)."""
        rp = self.prior_residuals(x)
        out = dict(data=float(np.sum(self.m.calculate_chi2_rwa(x))))
        for k in np.unique(self.prior_kind):
            q = rp[self.prior_kind == k]
            out[str(k)] = float(q @ q)
        out["physicality"] = self.phys(x, grad=False)[0] if self.phys else 0.0
        return out

    def objective(self, x):
        v = float(np.sum(self.m.calculate_chi2_rwa(x)))
        rp = self.prior_residuals(x)
        v += float(rp @ rp)
        if self.phys:
            v += self.phys(x, grad=False)[0]
        return v

    def objective_and_grad(self, x):
        chi2, g = self.m.chi2_and_grad(x)
        rp = self.prior_residuals(x)
        g = np.array(g, float)
        np.add.at(g, self.prior_idx, 2.0 * rp / self.prior_sig)
        v = chi2 + float(rp @ rp)
        if self.phys:
            pv, pg = self.phys(x)
            v += pv
            g += pg
        return v, g

    def labels(self):
        """A short name per free parameter, in free-vector order."""
        out = [""] * self.n
        for p in self.m.parameters:
            if not p.fixed and p.free_index is not None and p.free_index < self.n:
                e = f"@{p.level_energy:.2f}" if p.level_energy is not None else ""
                ch = f" pair{p.pair}" if p.pair is not None else ""
                rt = f" {p.radiation_type}" if p.radiation_type not in (None, "P") else ""
                seg = f" seg{p.segment_key}" if p.segment_key is not None else ""
                out[p.free_index] = f"{p.kind}{e}{ch}{rt}{seg}"
        return out

    # -- z space (what the sampler sees) -------------------------------------------
    def set_reference(self, x_ref, H):
        self.L, self.Linv, self.hessian_eigenvalues = whitening(H, self.T, self.floor)
        self.x_ref = np.asarray(x_ref, float).copy()

    def x_of(self, z):
        return self.x_ref + self.L @ z

    def z_of(self, x):
        return self.Linv @ (np.asarray(x, float) - self.x_ref)

    def logp(self, z):
        try:
            v = self.objective(self.x_of(z))
        except (RuntimeError, ValueError, FloatingPointError, OverflowError):
            return -np.inf
        return -0.5 * v / self.T if np.isfinite(v) else -np.inf

    def logp_grad(self, z):
        """(log p, d log p / dz); (-inf, nan) where the model fails: a divergence, not a crash."""
        try:
            v, g = self.objective_and_grad(self.x_of(z))
        except (RuntimeError, ValueError, FloatingPointError, OverflowError):
            return -np.inf, np.full(self.n, np.nan)
        if not (np.isfinite(v) and np.all(np.isfinite(g))):
            return -np.inf, np.full(self.n, np.nan)
        return -0.5 * v / self.T, -0.5 * (self.L.T @ g) / self.T

    def hessian_z(self, z, h=1e-4):
        """Hessian of -log p in z by central differences of the analytic gradient (2n gradients)."""
        H = np.zeros((self.n, self.n))
        for k in range(self.n):
            e = np.zeros(self.n); e[k] = h
            H[:, k] = -(self.logp_grad(z + e)[1] - self.logp_grad(z - e)[1]) / (2 * h)
        return 0.5 * (H + H.T)


# ---------------------------------------------------------------- command line
def add_args(ap):
    ap.add_argument("--azr", required=True, help="the .azr of the fit")
    ap.add_argument("--sav", default=None, help="its param.sav (default: the .azr's own parameters)")
    ap.add_argument("--cwd", default=None, help="directory the .azr's data paths are relative to")
    ap.add_argument("--out", required=True, help="run directory (map.npz, nuts/, emcee/)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--theta-scale", type=float, default=1.0, help="prior sd of theta, physical levels")
    ap.add_argument("--bg-scale", type=float, default=10.0, help="prior sd of theta, background poles")
    ap.add_argument("--bg-energy", type=float, default=None,
                    help="levels at or above this energy (as in the .azr) are background poles")
    ap.add_argument("--poles", default=None, help="poles.py for the transformability prior (optional)")
    ap.add_argument("--tau", type=float, default=0.70)
    ap.add_argument("--etarget", type=float, default=300.0)
    ap.add_argument("--soft", type=float, default=0.01)
    return ap


def posterior_from_args(a, reference=True):
    ref = os.path.join(a.out, "map.npz") if reference else None
    if ref and not os.path.exists(ref):
        raise SystemExit(f"{ref} missing: run find_map.py --out {a.out} first")
    return Posterior(a.azr, a.sav, a.cwd, temperature=a.temperature, theta_scale=a.theta_scale,
                     bg_scale=a.bg_scale, bg_energy=a.bg_energy, poles=a.poles,
                     phys_kw=dict(tau=a.tau, etarget=a.etarget, soft=a.soft), reference=ref)


def fingerprint(post):
    import hashlib
    return hashlib.sha1(post.x_ref.tobytes() + post.L.tobytes()).hexdigest()
