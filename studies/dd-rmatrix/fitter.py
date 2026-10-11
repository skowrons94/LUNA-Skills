"""Likelihood and fitter for the d+d R-matrix evaluation.

Residual for point i of experiment k:

    r_i = (n_k * f_scr(E_i) * sigma_R(E_i; x) - sigma_i) / s_i
    s_i^2 = err_i^2 + (sigma_i * dln(sigma)/dE * dE_i)^2

  sigma_R   bare R-matrix cross section (AZURE2, pyazr model_gradients)
  f_scr     electron screening exp(pi*eta*U_e/E) for direct (non-THM) data
  n_k       experiment normalisation (shared by d(d,p) and d(d,n) of one
            measurement; Krauss setup 2 = setup 1 x extra 5 %)
  dE_i      energy-calibration uncertainty folded in as an effective error

plus prior rows (p_j - 1)/delta_j for every constrained normalisation
parameter.  Point errors are the measured ones (statistical/uncorrelated),
so the normalisation enters only the model term (no Peelle bias).
"""
import json
import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy.optimize import least_squares

from pyazr import azure2

HERE = os.path.dirname(os.path.abspath(__file__))
CAT = json.load(open(os.path.join(HERE, "data", "catalog.json")))
EXPS = CAT["experiments"]
MU = 1.00728   # reduced mass d+d (u)

DEFAULT_OPTS = dict(
    exps=["BJ90", "KR87a", "KR87b", "GR95", "LE06", "AR54", "DA53", "PR54", "BO56",
          "YI73", "CH56", "HO01"],
    emin=0.0, emax=600.0,           # keV c.m. fit window
    Ue_eV=20.0,                     # electron screening potential for direct data
    dE_scale=1.0,                   # scale of energy-calibration uncertainties
    norm_scale=1.0,                 # scale of all normalisation priors
    norm_override={},               # {exp: fraction or None (free)}
    alt_errors=[],                  # experiments using their alternative errors
    err_inflate={},                 # {exp: factor} on point errors
    drop_points=[["CH56", "dn", 125.0]],   # [(exp, reac, E)] documented outliers
    birge_exp=False,                # per-experiment error inflation is passed via err_inflate
)
E_BOUNDS = (20.0, 60.0)            # pole Ex window: p+t threshold .. 60 MeV


def pi_eta(E):
    return 15.645 * np.sqrt(MU / E)


class DDFit:
    def __init__(self, project, opts=None, nprocs=1):
        self.dir = os.path.abspath(project)
        self.opts = {**DEFAULT_OPTS, **(opts or {})}
        meta = json.load(open(f"{self.dir}/segments.json"))
        self.segments = meta["segments"]
        self.cfg = meta["cfg"]
        self.m = azure2(f"{self.dir}/dd.azr", cwd=self.dir)
        self.x0 = np.asarray(self.m.params_rwa, float)
        self.width_idx = np.array([p.free_index for p in self.m.parameters
                                   if p.kind == "width" and not p.fixed
                                   and p.free_index is not None], int)
        self.energy_idx = np.array([p.free_index for p in self.m.parameters
                                    if p.kind == "energy" and not p.fixed
                                    and p.free_index is not None], int)
        self._build()

    # ----------------------------------------------------------- bookkeeping
    def _build(self):
        o = self.opts
        E, y, err, exp, reac, seg, use, dE = [], [], [], [], [], [], [], []
        for s, S in enumerate(self.segments):
            ex = S["exp"]
            for p in S["points"]:
                e = p["err_alt"] if (ex in o["alt_errors"] and "err_alt" in p) else p["err"]
                e *= o["err_inflate"].get(ex, 1.0)
                kind, val = EXPS[ex]["dE"]
                d = {"abs_lab_keV": val / 2, "abs_cm_keV": val, "frac": val * p["E"]}[kind]
                E.append(p["E"]); y.append(p["sigma"]); err.append(e); exp.append(ex)
                reac.append(S["reac"]); seg.append(s); dE.append(d * o["dE_scale"])
                drop = any(ex == a and S["reac"] == b and abs(p["E"] - c) < 1e-6
                           for a, b, c in o["drop_points"])
                use.append(ex in o["exps"] and o["emin"] <= p["E"] <= o["emax"] and not drop)
        self.E, self.y, self.err = map(np.array, (E, y, err))
        self.exp, self.reac, self.seg = np.array(exp), np.array(reac), np.array(seg)
        self.use = np.array(use)
        thm = np.array([EXPS[e]["tier"] == "thm" for e in exp])
        self.fscr = np.where(thm, 1.0, np.exp(pi_eta(self.E) * o["Ue_eV"] * 1e-3 / self.E))
        dlns = (pi_eta(self.E) - 1.0) / self.E
        self.s = np.sqrt(self.err**2 + (self.y * dlns * np.array(dE))**2)
        # normalisation parameters
        active = sorted(set(self.exp[self.use]))
        self.norm_names, self.norm_prior = [], []
        for ex in active:
            if ex == "KR87b":
                continue
            self._add_norm(ex, o)
        if "KR87b" in active:
            if "KR87a" not in self.norm_names:
                self._add_norm("KR87a", o)
            self.norm_names.append("KR87b_extra")
            self.norm_prior.append(0.05 * o["norm_scale"])
        self.nn = len(self.norm_names)
        # map experiment -> list of norm params whose product is n_k
        self.norm_map = {ex: ([self.norm_names.index("KR87a"), self.norm_names.index("KR87b_extra")]
                              if ex == "KR87b" else [self.norm_names.index(ex)])
                         for ex in active}
        self.idx = np.where(self.use)[0]

    def _add_norm(self, ex, o):
        pr = o["norm_override"].get(ex, EXPS[ex]["norm"])
        if ex == "KR87a" and "KR87a" not in o["norm_override"]:
            pr = 0.064
        self.norm_names.append(ex)
        self.norm_prior.append(None if pr is None else pr * o["norm_scale"])

    def norms(self, p):
        return {ex: float(np.prod(p[ii])) for ex, ii in self.norm_map.items()}

    # ------------------------------------------------------------ model
    def model(self, x):
        c = self.m.calculate_rwa(x)
        return np.concatenate([np.asarray(ci, float) for ci in c])

    def _model_and_grad(self, x):
        c = np.concatenate([np.asarray(ci, float) for ci in self.m.calculate_rwa(x)])
        g = np.vstack([np.asarray(gi, float) for gi in self.m.model_gradients(x)])
        return c, g

    def residuals(self, z, want_jac=False):
        nx = len(self.x0)
        x, p = z[:nx], z[nx:]
        if want_jac:
            c, g = self._model_and_grad(x)
        else:
            c = self.model(x)
        nrm = self.norms(p)
        n_i = np.array([nrm[e] for e in self.exp[self.idx]])
        i = self.idx
        r = (n_i * self.fscr[i] * c[i] - self.y[i]) / self.s[i]
        prior_rows = [(k, d) for k, d in enumerate(self.norm_prior) if d is not None]
        rp = np.array([(p[k] - 1.0) / d for k, d in prior_rows])
        R = np.concatenate([r, rp])
        if not want_jac:
            return R
        J = np.zeros((len(R), len(z)))
        J[:len(i), :nx] = (n_i * self.fscr[i] / self.s[i])[:, None] * g[i]
        for row, ii in enumerate(i):
            ex = self.exp[ii]
            for k in self.norm_map[ex]:
                J[row, nx + k] = self.fscr[ii] * c[ii] * nrm[ex] / p[k] / self.s[ii]
        for row, (k, d) in enumerate(prior_rows):
            J[len(i) + row, nx + k] = 1.0 / d
        return R, J

    # ------------------------------------------------------------- fitting
    def fit(self, n_starts=12, seed=1, x_start=None, verbose=False, max_nfev=3000):
        rng = np.random.default_rng(seed)
        nx = len(self.x0)
        best = None
        starts = []
        if x_start is not None:
            starts.append(np.asarray(x_start, float))
        starts.append(self.x0.copy())
        while len(starts) < n_starts:
            xs = self.x0.copy()
            w = self.width_idx
            xs[w] *= np.exp(rng.normal(0, 1.0, len(w))) * rng.choice([-1, 1], len(w))
            starts.append(xs)
        lb = np.full(nx + self.nn, -np.inf); ub = np.full(nx + self.nn, np.inf)
        ei = getattr(self, "energy_idx", np.array([], int))
        lb[ei], ub[ei] = E_BOUNDS
        lb[nx:], ub[nx:] = 0.3, 3.0
        for k, xs in enumerate(starts):
            z0 = np.concatenate([xs[:nx], np.ones(self.nn)])
            z0 = np.clip(z0, lb + 1e-9, ub - 1e-9)
            try:
                sol = least_squares(lambda z: self.residuals(z), z0, bounds=(lb, ub),
                                    jac=lambda z: self.residuals(z, True)[1],
                                    method="trf", x_scale="jac", max_nfev=max_nfev,
                                    xtol=1e-10, ftol=1e-10)
            except Exception as e:           # a start that wanders off
                if verbose:
                    print("start", k, "failed", e)
                continue
            chi2 = 2 * sol.cost
            if verbose:
                print(f"start {k:2d}: chi2 = {chi2:.2f}  nfev = {sol.nfev}")
            if best is None or chi2 < best["chi2"]:
                best = dict(z=sol.x, chi2=chi2, jac=sol.jac)
        self.best = best
        return best

    def summary(self, z):
        nx = len(self.x0)
        R = self.residuals(z)
        i = self.idx
        r = R[:len(i)]
        out = {"chi2_data": float(np.sum(r**2)), "chi2_prior": float(np.sum(R[len(i):]**2)),
               "npts": int(len(i)), "npar": int(len(z)), "per_exp": {}}
        for ex in sorted(set(self.exp[i])):
            for rc in ("dp", "dn"):
                mask = (self.exp[i] == ex) & (self.reac[i] == rc)
                if mask.any():
                    out["per_exp"][f"{ex}_{rc}"] = (float(np.sum(r[mask]**2)), int(mask.sum()))
        out["norms"] = self.norms(z[nx:])
        return out

    # ------------------------------------------------------- extrapolation
    def curves(self, x, grid_cm_keV):
        """bare sigma_dp, sigma_dn (b) on a c.m. grid, via the extrapolation segments."""
        self.m.extrap_mode()
        c = self.m.calculate_rwa(x)
        en = self.m.calculate_energies(x)
        self.m.data_mode()
        out = {}
        for key, ks in (("dp", (0, 1)), ("dn", (2, 3))):
            Ek = np.concatenate([np.asarray(en[k], float) for k in ks]) * 1e3
            ck = np.concatenate([np.asarray(c[k], float) for k in ks])
            o = np.argsort(Ek)
            out[key] = np.exp(np.interp(grid_cm_keV, Ek[o], np.log(np.maximum(ck[o], 1e-300))))
        out["E_grid_range"] = (float(Ek.min()), float(Ek.max()))
        return out

    def close(self):
        self.m.close()


class PolyFit(DDFit):
    """Model-independent cross-check: S(E) = sum_k a_k (E/100 keV)^k per channel."""

    def __init__(self, project, opts=None, degree=4):
        self.dir = os.path.abspath(project)
        self.opts = {**DEFAULT_OPTS, **(opts or {})}
        meta = json.load(open(f"{self.dir}/segments.json"))
        self.segments, self.cfg = meta["segments"], meta["cfg"]
        self.deg = degree
        self.x0 = np.concatenate([[60.0] + [1.0] * degree] * 2)   # keV b
        self.width_idx = np.arange(len(self.x0))
        self._build()
        self.m = None

    def _basis(self, E):
        return np.vstack([(E / 100.0)**k for k in range(self.deg + 1)]).T

    def _conv(self, E):
        return np.exp(-2 * pi_eta(E)) / E          # S [keV b] -> sigma [b]

    def _model_and_grad(self, x):
        B = self._basis(self.E) * self._conv(self.E)[:, None]
        g = np.zeros((len(self.E), len(x)))
        n = self.deg + 1
        dp = self.reac == "dp"
        g[dp, :n] = B[dp]
        g[~dp, n:] = B[~dp]
        return g @ x, g

    def model(self, x):
        return self._model_and_grad(x)[0]

    def curves(self, x, grid):
        n = self.deg + 1
        B = self._basis(grid) * self._conv(grid)[:, None]
        return {"dp": B @ x[:n], "dn": B @ x[n:], "E_grid_range": (grid.min(), grid.max())}

    def close(self):
        pass
