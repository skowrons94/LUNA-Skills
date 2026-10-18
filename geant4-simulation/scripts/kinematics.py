#!/usr/bin/env python3
"""Relativistic two-body reaction kinematics for event generation and checks (standard library only).

Reaction 1 + 2 -> 3 + 4 with projectile 1 at lab kinetic energy T1 on target 2 at rest; particle 3 is
the detected ejectile (neutron, proton, gamma, ...), particle 4 the residual nucleus, optionally in an
excited state Ex. Energies in MeV, angles in degrees, masses in MeV/c^2 (nuclear masses).

    python3 kinematics.py "13C(a,n)16O" --T1 5.0 --theta 0 90 180
    python3 kinematics.py "7Li(p,n)7Be" --T1 2.5 --theta 0 --Ex 0.429
    python3 kinematics.py "12C(p,g)13N" --T1 0.5 --theta 0 90
    python3 kinematics.py "13C(a,n)16O" --T1 5.0 --spectrum out.csv          # isotropic-CM lab spectrum
    python3 kinematics.py "13C(a,n)16O" --T1 5.0 --events 1000 --seed 1 --out events.csv

The --spectrum output (E_low_MeV,E_high_MeV,weight) and --events output (E_MeV,ux,uy,uz) match the
hist and list sources of the neutron-counter template. Thick-target folding: thick_target_spectrum().
"""
from __future__ import annotations

import argparse
import math
import random
import re
import sys

U = 931.49410242          # MeV per atomic mass unit (CODATA 2018)
ME = 0.51099895           # electron mass, MeV
# Atomic mass excesses in keV (AME2020), a small set of light nuclides for textbook examples.
MASS_EXCESS_KEV = {
    "n": (0, 1, 8071.31806), "p": (1, 1, 7288.971064), "d": (1, 2, 13135.722895),
    "t": (1, 3, 14949.81090), "3He": (2, 3, 14931.21888), "a": (2, 4, 2424.91587),
    "6Li": (3, 6, 14086.8804), "7Li": (3, 7, 14907.105), "7Be": (4, 7, 15768.999),
    "9Be": (4, 9, 11348.453), "10B": (5, 10, 12050.611), "11B": (5, 11, 8667.708),
    "12C": (6, 12, 0.0), "13C": (6, 13, 3125.00888), "13N": (7, 13, 5345.48),
    "14N": (7, 14, 2863.41669), "15N": (7, 15, 101.43870), "16O": (8, 16, -4737.00137),
    "17O": (8, 17, -808.76360), "18O": (8, 18, -782.81560), "19F": (9, 19, -1487.44420),
}
ALIASES = {"1H": "p", "2H": "d", "3H": "t", "4He": "a", "alpha": "a", "α": "a", "γ": "g", "gamma": "g"}


def nuclear_mass(name: str) -> float:
    """Nuclear mass in MeV/c^2 (atomic mass minus Z electrons; electron binding neglected). 'g' -> 0."""
    name = ALIASES.get(name, name)
    if name == "g":
        return 0.0
    if name not in MASS_EXCESS_KEV:
        raise KeyError(f"no mass for {name!r}; pass masses explicitly (MASS_EXCESS_KEV holds a small table)")
    z, a, dkev = MASS_EXCESS_KEV[name]
    return a * U + dkev / 1000.0 - z * ME


def parse_reaction(text: str) -> tuple[str, str, str, str]:
    """'13C(a,n)16O' -> (projectile, target, ejectile, residual)."""
    m = re.fullmatch(r"\s*([^()\s]+)\s*\(\s*([^,\s]+)\s*,\s*([^)\s]+)\s*\)\s*([^()\s]+)\s*", text)
    if not m:
        raise ValueError(f"cannot parse reaction {text!r}; use e.g. 13C(a,n)16O")
    target, proj, ejec, resid = m.groups()
    return proj, target, ejec, resid


def masses(reaction: str, ex: float = 0.0) -> tuple[float, float, float, float]:
    p, t, e, r = parse_reaction(reaction)
    return nuclear_mass(p), nuclear_mass(t), nuclear_mass(e), nuclear_mass(r) + ex


def q_value(m1: float, m2: float, m3: float, m4: float) -> float:
    return m1 + m2 - m3 - m4


def threshold(m1: float, m2: float, m3: float, m4: float) -> float:
    """Lab kinetic energy of the projectile at threshold (0 for exothermic reactions)."""
    q = q_value(m1, m2, m3, m4)
    if q >= 0:
        return 0.0
    return ((m3 + m4) ** 2 - (m1 + m2) ** 2) / (2.0 * m2)


def _initial(m1: float, m2: float, t1: float) -> tuple[float, float, float]:
    e_tot = t1 + m1 + m2
    p_tot = math.sqrt(t1 * (t1 + 2.0 * m1))
    s = e_tot ** 2 - p_tot ** 2
    return e_tot, p_tot, s


def lab_at_angle(m1, m2, m3, m4, t1, theta_deg):
    """All solutions for ejectile 3 at lab angle theta: list of dicts (T3, theta_cm, T4, theta4).

    Two solutions occur below the maximum angle when the CM velocity exceeds the ejectile CM speed."""
    e_tot, p_tot, s = _initial(m1, m2, t1)
    if math.sqrt(s) < m3 + m4:
        return []
    c = math.cos(math.radians(theta_deg))
    k = 0.5 * (s + m3 ** 2 - m4 ** 2)        # E_tot E3 - P p3 cos(theta) = k
    a = e_tot ** 2 - (p_tot * c) ** 2
    disc = k ** 2 - m3 ** 2 * a
    if disc < 0:
        return []
    roots = {(k * p_tot * c + sg * e_tot * math.sqrt(disc)) / a for sg in (1.0, -1.0)}
    out = []
    for p3 in sorted(roots, reverse=True):
        if p3 < 0:
            continue
        e3 = math.sqrt(p3 ** 2 + m3 ** 2)
        if abs(e_tot * e3 - p_tot * p3 * c - k) > 1e-9 * max(1.0, k):
            continue  # spurious root introduced by squaring
        out.append(_complete(m3, m4, e_tot, p_tot, s, p3, theta_deg))
    return out


def _complete(m3, m4, e_tot, p_tot, s, p3, theta_deg):
    th = math.radians(theta_deg)
    e3 = math.sqrt(p3 ** 2 + m3 ** 2)
    p3z, p3t = p3 * math.cos(th), p3 * math.sin(th)
    beta = p_tot / e_tot
    gamma = e_tot / math.sqrt(s)
    pz_cm = gamma * (p3z - beta * e3)
    theta_cm = math.degrees(math.atan2(p3t, pz_cm))
    p4z, p4t = p_tot - p3z, -p3t
    e4 = e_tot - e3
    return {"T3": e3 - m3, "theta3": theta_deg, "theta_cm": theta_cm, "T4": e4 - m4,
            "theta4": math.degrees(math.atan2(abs(p4t), p4z)), "p3": p3}


def lab_from_cm(m1, m2, m3, m4, t1, cos_cm, phi=0.0):
    """Ejectile lab kinetic energy and unit direction (ux, uy, uz) for a CM emission cosine about the beam."""
    e_tot, p_tot, s = _initial(m1, m2, t1)
    rs = math.sqrt(s)
    if rs < m3 + m4:
        raise ValueError("below threshold")
    e3c = (s + m3 ** 2 - m4 ** 2) / (2.0 * rs)
    p3c = math.sqrt(max(0.0, e3c ** 2 - m3 ** 2))
    beta, gamma = p_tot / e_tot, e_tot / rs
    sin_cm = math.sqrt(max(0.0, 1.0 - cos_cm ** 2))
    pz = gamma * (p3c * cos_cm + beta * e3c)
    pt = p3c * sin_cm
    e3 = gamma * (e3c + beta * p3c * cos_cm)
    p = math.hypot(pz, pt)
    return e3 - m3, (pt * math.cos(phi) / p, pt * math.sin(phi) / p, pz / p)


def isotropic_spectrum(m1, m2, m3, m4, t1, n_cos=2000):
    """(T3, weight) pairs for isotropic CM emission, integrated over all lab angles (equal CM solid angle)."""
    return [(lab_from_cm(m1, m2, m3, m4, t1, -1.0 + (i + 0.5) * 2.0 / n_cos)[0], 1.0 / n_cos)
            for i in range(n_cos)]


def thick_target_spectrum(m1, m2, m3, m4, t0, sigma, stopping, theta_deg=None, n_e=200, n_cos=200):
    """Ejectile spectrum from a thick target: projectile slows from t0 to threshold (or 0).

    Each energy step dE is weighted by sigma(E)/stopping(E) (any consistent units; the product is a yield
    per incident projectile up to a constant). With theta_deg the ejectile is taken at that lab angle (all
    kinematic solutions), otherwise isotropic CM emission integrated over angle. Returns (T3, weight) pairs.
    """
    e_lo = max(threshold(m1, m2, m3, m4), 0.0)
    if t0 <= e_lo:
        return []
    de = (t0 - e_lo) / n_e
    out = []
    for i in range(n_e):
        e = e_lo + (i + 0.5) * de
        w = sigma(e) / stopping(e) * de
        if w <= 0:
            continue
        if theta_deg is None:
            out += [(t3, w * wc) for t3, wc in isotropic_spectrum(m1, m2, m3, m4, e, n_cos)]
        else:
            out += [(sol["T3"], w) for sol in lab_at_angle(m1, m2, m3, m4, e, theta_deg)]
    return out


def histogram(pairs, n_bins=100, lo=None, hi=None):
    """Bin (value, weight) pairs; returns list of (low, high, weight)."""
    if not pairs:
        return []
    lo = min(v for v, _ in pairs) if lo is None else lo
    hi = max(v for v, _ in pairs) if hi is None else hi
    if hi <= lo:
        hi = lo + 1e-6
    width = (hi - lo) / n_bins
    w = [0.0] * n_bins
    for v, wt in pairs:
        w[min(n_bins - 1, max(0, int((v - lo) / width)))] += wt
    return [(lo + i * width, lo + (i + 1) * width, w[i]) for i in range(n_bins)]


def sample_events(m1, m2, m3, m4, t1, n, rng):
    """n ejectiles with isotropic CM emission: list of (T3, ux, uy, uz)."""
    out = []
    for _ in range(n):
        t3, u = lab_from_cm(m1, m2, m3, m4, t1, rng.uniform(-1.0, 1.0), rng.uniform(0.0, 2 * math.pi))
        out.append((t3, *u))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reaction", help="e.g. 13C(a,n)16O, 7Li(p,n)7Be, 12C(p,g)13N")
    ap.add_argument("--T1", type=float, required=True, help="projectile lab kinetic energy, MeV")
    ap.add_argument("--Ex", type=float, default=0.0, help="excitation energy of the residual, MeV")
    ap.add_argument("--theta", type=float, nargs="*", default=[], help="ejectile lab angles, deg")
    ap.add_argument("--spectrum", help="write the isotropic-CM lab spectrum as E_low_MeV,E_high_MeV,weight")
    ap.add_argument("--bins", type=int, default=50)
    ap.add_argument("--events", type=int, default=0, help="sample N isotropic-CM events")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", help="output CSV for --events (E_MeV,ux,uy,uz)")
    a = ap.parse_args(argv)
    m = masses(a.reaction, a.Ex)
    print(f"# {a.reaction}  Ex={a.Ex} MeV  Q={q_value(*m):.5f} MeV  threshold={threshold(*m):.5f} MeV (lab)")
    for th in a.theta:
        sols = lab_at_angle(*m, a.T1, th)
        if not sols:
            print(f"theta={th:g} deg: no solution (closed channel or beyond maximum angle)")
        for s in sols:
            print(f"theta={th:g} deg: T3={s['T3']:.6f} MeV  theta_cm={s['theta_cm']:.3f} deg  "
                  f"T4={s['T4']:.6f} MeV  theta4={s['theta4']:.3f} deg")
    if a.spectrum:
        rows = histogram(isotropic_spectrum(*m, a.T1), a.bins)
        with open(a.spectrum, "w") as f:
            f.write(f"# {a.reaction} T1={a.T1} MeV Ex={a.Ex} MeV, isotropic CM, angle-integrated\n")
            f.write("# E_low_MeV,E_high_MeV,weight\n")
            f.writelines(f"{lo:.6f},{hi:.6f},{w:.6e}\n" for lo, hi, w in rows)
        print(f"wrote {a.spectrum}")
    if a.events:
        ev = sample_events(*m, a.T1, a.events, random.Random(a.seed))
        out = open(a.out, "w") if a.out else sys.stdout
        out.write("# E_MeV,ux,uy,uz\n")
        out.writelines(f"{e:.6f},{x:.6f},{y:.6f},{z:.6f}\n" for e, x, y, z in ev)
        if a.out:
            out.close()
            print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
