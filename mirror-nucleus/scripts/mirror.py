"""Mirror-nucleus tools: charge-symmetry predictions and tests between mirror systems.

Built on the cluster-potential skill (cluster.py, imported from the sibling folder).

    mirror_system(s)              the mirror partition: 3He <-> t, p <-> n (same geometry)
    predict_levels(...)           a spectrum with depths fixed in one nucleus, nothing refitted
    anc_ratio(...)                C^2 ratio of mirror bound states, depths refitted separately per
                                  geometry; the spread over geometries is the model uncertainty
    theta2_at_radii(...)          dimensionless reduced width of an isolated level at several radii
    threshold_shift(...)          Thomas-Ehrman-type shift: E_x difference and the difference
                                  relative to a chosen threshold in each nucleus

Units: MeV, fm.  E relative to the cluster threshold (negative = bound).
"""
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

_CP = Path(__file__).resolve().parents[2] / "cluster-potential" / "scripts"
if str(_CP) not in sys.path:
    sys.path.insert(0, str(_CP))
import cluster as cl  # noqa: E402

MIRROR = {"3He": "t", "t": "3He", "p": "n", "n": "p", "d": "d", "alpha": "alpha"}


def mirror_system(s, thr_ex=None):
    """Same clusters with Z and N exchanged; geometry (n_min, Rc) kept."""
    return replace(s, c1=MIRROR[s.c1], c2=MIRROR[s.c2], thr_ex=s.thr_ex if thr_ex is None else thr_ex)


def predict_levels(system, waves, a, Rc=None):
    """waves: {label: (V0, l, nodes, bound)}.  Returns {label: (E, Gamma or None)};
    bound states by node count, unbound ones by the first pi/2 crossing."""
    out = {}
    for lab, (V0, l, nodes, bound) in waves.items():
        pot = cl.Pot(system, V0, a, Rc)
        if bound:
            out[lab] = (cl.level(pot, l, nodes), None)
        else:
            r = cl.first_resonance(pot, l)
            out[lab] = r if r else (None, None)
    return out


def anc_ratio(sys_a, E_a, sys_b, E_b, l, nodes, ranges=(2.50, 2.60, 2.6883, 2.80, 2.90), Rc=None):
    """C^2(a)/C^2(b) with the depth refitted in EACH nucleus to its own binding, per range.
    Returns (rows, mean, spread) with rows = [(range, V_a, C2_a, V_b, C2_b, ratio)]."""
    rows = []
    for rng in ranges:
        Va = cl.fit_V0_bound(sys_a, l, nodes, E_a, rng, Rc)
        Vb = cl.fit_V0_bound(sys_b, l, nodes, E_b, rng, Rc)
        Ca = cl.anc(cl.Pot(sys_a, Va, rng, Rc), l, E_a)
        Cb = cl.anc(cl.Pot(sys_b, Vb, rng, Rc), l, E_b)
        rows.append((rng, Va, Ca * Ca, Vb, Cb * Cb, (Ca * Ca) / (Cb * Cb)))
    r = np.array([x[-1] for x in rows])
    return rows, float(r.mean()), float(r.std())


def theta2_at_radii(system, Gamma, E, l, radii):
    """theta^2 = Gamma / (2 P_l(a) hbar^2/(mu a^2)) of an isolated level at each radius a.
    Mirror levels are compared at the SAME radius; their fits may use different ones."""
    return {a: cl.theta2_from_width(system, Gamma, E, l, a) for a in radii}


def threshold_shift(Ex_a, thr_a, Ex_b, thr_b):
    """(dEx, d_rel): difference of excitation energies and of energies above the given
    thresholds (e.g. the core+nucleon thresholds for a nucleon-on-core state)."""
    return Ex_b - Ex_a, (Ex_b - thr_b) - (Ex_a - thr_a)
