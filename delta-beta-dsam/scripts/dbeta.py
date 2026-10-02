"""Doppler-velocity DSAM (Delta-beta) toolkit.

Method of Fougeres et al., Nature Commun. 14, 4536 (2023), as extended in the 15O AGATA lifetime
analysis (J. Skowronski et al., submitted 2026; code github.com/skowrons94/15O_Lifetime) and used in
the 28Si(3He,alpha)27Si AGATA feasibility study (~/Desktop/28Si/scripts/analyse_agata.py).

Conventions: energies in MeV for kinematics and keV for gamma rays, masses in MeV/c^2 (nuclear or
atomic consistently), angles in degrees unless stated, c = 1. beta = v/c.

Main entry points
  recoil_from_ejectile   beta_reac, recoil direction and E_x from the ejectile energy and angle
  energy_before          undo energy losses with a user-supplied dE/dx(E) (MeV/um)
  beta_ems               invert the relativistic Doppler formula (root closest to a reference beta)
  dbeta_windows          Delta-beta centroids in windows of the gamma angle (Gaussian core + bootstrap)
  fit_dbeta_theta        Delta-beta(theta) = Delta-beta_true + distortion(theta; dE, dtheta)
  dbeta_dt               analytic d(beta)/dt from the stopping power
  calibrate              linear Delta-beta vs tau calibration
  lifetime_sensitivity   statistical sigma_tau for N events
"""

from __future__ import annotations

import numpy as np

C_UM_PER_FS = 0.299792458


# ----------------------------------------------------------------------------- kinematics
def momentum(T, m):
    T = np.asarray(T, float)
    return np.sqrt(T**2 + 2 * T * m)


def recoil_from_ejectile(T_beam, m_beam, m_target, m_ej, m_rec0, T_ej, theta_ej_deg, phi_ej_rad, ex_assume_MeV):
    """Recoil at the reaction point from the measured ejectile (energy already corrected for losses).

    |p_R|^2 = p_b^2 + p_e^2 - 2 p_b p_e cos(theta_e); beta_reac = |p_R| / sqrt(|p_R|^2 + (m_R0 + E_x)^2).
    E_x is reconstructed independently from energy conservation (missing mass) as a check.
    Returns dict of arrays: beta, ux, uy, uz (recoil direction), theta_rec_deg, T_rec, ex_reco_MeV.
    The beam is along +z. ex_assume_MeV may be a scalar (common value when the state is not known).
    """
    pb = momentum(T_beam, m_beam)
    Te = np.asarray(T_ej, float)
    pe = momentum(Te, m_ej)
    th = np.radians(np.asarray(theta_ej_deg, float))
    ph = np.asarray(phi_ej_rad, float)
    px, py, pz = -pe * np.sin(th) * np.cos(ph), -pe * np.sin(th) * np.sin(ph), pb - pe * np.cos(th)
    pr = np.sqrt(px**2 + py**2 + pz**2)
    E_rec = (T_beam + m_beam + m_target) - (Te + m_ej)
    ex_reco = np.sqrt(np.maximum(E_rec**2 - pr**2, 0)) - m_rec0
    m_r = m_rec0 + ex_assume_MeV
    E_r = np.sqrt(pr**2 + m_r**2)
    return dict(beta=pr / E_r, ux=px / pr, uy=py / pr, uz=pz / pr, theta_rec_deg=np.degrees(np.arccos(pz / pr)),
                T_rec=E_r - m_r, ex_reco_MeV=ex_reco)


def energy_before(E_after, path_um, dedx, nstep: int = 40):
    """Energy before crossing path_um of material, given the energy after; dedx(E) in MeV/um."""
    E = np.asarray(E_after, float).copy()
    dx = np.asarray(path_um, float) / nstep
    for _ in range(nstep):
        E = E + dedx(E) * dx
    return E


def energy_after(E_before, path_um, dedx, nstep: int = 40):
    E = np.asarray(E_before, float).copy()
    dx = np.asarray(path_um, float) / nstep
    for _ in range(nstep):
        E = np.maximum(E - dedx(E) * dx, 0.0)
    return E


# ----------------------------------------------------------------------------- Doppler
def doppler_energy(e0, beta, cos_theta):
    """E_obs = E0 sqrt(1 - beta^2) / (1 - beta cos theta)."""
    beta = np.asarray(beta, float)
    return e0 * np.sqrt(1 - beta**2) / (1 - beta * np.asarray(cos_theta, float))


def beta_ems(e_obs, e0, cos_theta, beta_ref=None):
    """Invert the Doppler formula: beta = (R^2 c +- sqrt(1 + R^2 c^2 - R^2)) / (1 + R^2 c^2), R = E_obs/E0.

    The physical root is the one closest to beta_ref (e.g. beta_reac or a nominal value); without
    beta_ref the root with the smaller |beta| is taken. Near theta = 90 deg the inversion is ill-
    conditioned (d beta / d E ~ 1/cos theta): cut |cos theta| or let the windowed fit down-weight it.
    """
    R2 = (np.asarray(e_obs, float) / e0) ** 2
    c = np.asarray(cos_theta, float)
    disc = np.sqrt(np.maximum(1 + R2 * c**2 - R2, 0))
    den = 1 + R2 * c**2
    b1, b2 = (R2 * c + disc) / den, (R2 * c - disc) / den
    if beta_ref is None:
        return np.where(np.abs(b1) < np.abs(b2), b1, b2)
    ref = np.broadcast_to(np.asarray(beta_ref, float), b1.shape)
    return np.where(np.abs(b1 - ref) < np.abs(b2 - ref), b1, b2)


def doppler_window(e_obs, e0, beta_reac, cos_theta, margin_keV):
    """Selection between the fully shifted (beta_reac) and the unshifted energy, +- margin."""
    efull = doppler_energy(e0, beta_reac, cos_theta)
    lo, hi = np.minimum(efull, e0), np.maximum(efull, e0)
    return (e_obs > lo - margin_keV) & (e_obs < hi + margin_keV)


# ----------------------------------------------------------------------------- Delta-beta(theta)
def _gauss(x, A, mu, s):
    return A * np.exp(-0.5 * ((x - mu) / s) ** 2)


def gaussian_centroid(x, nsig_range: float = 3.0, nbins: int = 41):
    """Centroid of the Gaussian core (fit within +-nsig_range robust sigma of the median)."""
    from scipy.optimize import curve_fit
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    med = np.median(x)
    sd = 1.4826 * np.median(np.abs(x - med))
    if not sd > 0:
        return float(med)
    h, e = np.histogram(x, np.linspace(med - nsig_range * sd, med + nsig_range * sd, nbins))
    xc = 0.5 * (e[1:] + e[:-1])
    try:
        p, _ = curve_fit(_gauss, xc, h, p0=[h.max(), med, sd], sigma=np.sqrt(h + 1), absolute_sigma=True, maxfev=5000)
        return float(p[1])
    except Exception:
        return float(med)


def dbeta_windows(theta_deg, dbeta, width: float = 7.0, step: float | None = None, n_boot: int = 50,
                  n_min: int = 100, seed: int = 11, drop_edges: bool = True):
    """Centroids of Delta-beta in windows of the gamma angle w.r.t. the recoil.

    drop_edges: discard the first and last populated window. With finite angular resolution, events
    migrate across the edges of the angular acceptance asymmetrically and bias the edge centroids
    (synthetic test: -1e-3 to -3e-3 for 1 deg smearing), which an energy-offset fit then absorbs into
    a biased Delta-beta. Also inspect per-window residuals for gaps between detector rings.
    Returns a dict of arrays: theta, n, centroid, err (bootstrap), rms.
    """
    th, db = np.asarray(theta_deg, float), np.asarray(dbeta, float)
    step = width if step is None else step
    rng = np.random.default_rng(seed)
    out = {k: [] for k in ("theta", "n", "centroid", "err", "rms")}
    for lo in np.arange(0, 180 - width + 1e-9, step):
        m = (th >= lo) & (th < lo + width)
        if m.sum() < n_min:
            continue
        x = db[m]
        c = gaussian_centroid(x)
        boot = [gaussian_centroid(rng.choice(x, len(x))) for _ in range(n_boot)]
        for k, v in zip(out, (lo + width / 2, int(m.sum()), c, float(np.std(boot)), float(np.std(x)))):
            out[k].append(v)
    res = {k: np.asarray(v) for k, v in out.items()}
    if drop_edges and len(res["theta"]) > 4:
        res = {k: v[1:-1] for k, v in res.items()}
    return res


def distortion(theta_deg, e0, beta_ref, dE_keV=0.0, dtheta_deg=0.0):
    """beta_ref - beta_ems reconstructed with an energy offset dE and an angle offset dtheta
    (the distortion of Delta-beta(theta) produced by calibration offsets)."""
    th = np.radians(np.asarray(theta_deg, float))
    eg = doppler_energy(e0, beta_ref, np.cos(th))
    return beta_ref - beta_ems(eg, e0 + dE_keV, np.cos(th + np.radians(dtheta_deg)), beta_ref)


def fit_dbeta_theta(win: dict, e0: float, beta_ref: float, fit_dE: bool = True, dtheta_deg: float = 0.0):
    """Fit Delta-beta(theta) = Delta-beta_true + distortion(theta; dE, dtheta).

    dtheta is kept fixed (it is degenerate with dE and common to all transitions of a setup).
    Returns dict: dbeta, dbeta_err, dE, dE_err, chi2, ndf; plus dbeta_fixedE(_err) with dE = 0.
    """
    from scipy.optimize import curve_fit
    th, y, e = win["theta"], win["centroid"], win["err"]
    w = 1 / e**2
    res = dict(dbeta_fixedE=float(np.sum(w * y) / np.sum(w)), dbeta_fixedE_err=float(np.sqrt(1 / np.sum(w))))
    if fit_dE:
        f = lambda t, db, dE: db + distortion(t, e0, beta_ref, dE, dtheta_deg)
        p, cov = curve_fit(f, th, y, p0=[res["dbeta_fixedE"], 0.0], sigma=e, absolute_sigma=True)
        chi2 = float(np.sum(((y - f(th, *p)) / e) ** 2))
        res.update(dbeta=float(p[0]), dbeta_err=float(np.sqrt(cov[0, 0])), dE=float(p[1]),
                   dE_err=float(np.sqrt(cov[1, 1])), chi2=chi2, ndf=len(th) - 2)
    else:
        chi2 = float(np.sum(((y - res["dbeta_fixedE"]) / e) ** 2))
        res.update(dbeta=res["dbeta_fixedE"], dbeta_err=res["dbeta_fixedE_err"], dE=0.0, dE_err=0.0,
                   chi2=chi2, ndf=len(th) - 1)
    return res


# ----------------------------------------------------------------------------- calibration
def dbeta_dt(T_rec_MeV, m_rec_MeV, dedx_MeV_per_um):
    """d(beta)/dt in fs^-1: c m^2 / E_tot^3 dE/dx (electronic + nuclear stopping in the backing)."""
    E = T_rec_MeV + m_rec_MeV
    return C_UM_PER_FS * m_rec_MeV**2 / E**3 * dedx_MeV_per_um


def calibrate(tau_fs, dbeta, dbeta_err, tau_max: float = 30.0):
    """Weighted linear fit Delta-beta = a tau + b for tau <= tau_max. Returns (a, a_err, b, b_err)."""
    t, y, e = (np.asarray(v, float) for v in (tau_fs, dbeta, dbeta_err))
    m = t <= tau_max
    k, cov = np.polyfit(t[m], y[m], 1, w=1 / e[m], cov="unscaled")
    return float(k[0]), float(np.sqrt(cov[0, 0])), float(k[1]), float(np.sqrt(cov[1, 1]))


def lifetime_sensitivity(dbeta_err_fit, n_events_fit, n_events_expected, slope_per_fs):
    """sigma_tau (fs) for n_events_expected, scaling the fitted Delta-beta uncertainty as 1/sqrt(N)."""
    return dbeta_err_fit * np.sqrt(n_events_fit / n_events_expected) / abs(slope_per_fs)
