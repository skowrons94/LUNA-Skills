"""Thermonuclear rates from bare cross sections, comparison with REACLIB and
propagation to BBN through ../bbn-lithium/bbn.py."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bbn-lithium"))

NA = 6.02214076e23
KB = 8.617333262e-2          # MeV / GK
AMU_G = 1.66053906660e-24
MEV_ERG = 1.602176634e-6
MU = 1.00728                 # d+d reduced mass, u
T9_GRID = np.array([0.01, 0.02, 0.03, 0.05, 0.07, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5,
                    0.6, 0.7, 0.8, 0.9, 1.0, 1.25, 1.5, 2.0])


def rate(E_keV, sigma_b, T9):
    """N_A <sigma v> [cm^3 mol^-1 s^-1] on the T9 array (trapezoid on the grid)."""
    E = np.asarray(E_keV) * 1e-3                       # MeV
    s = np.asarray(sigma_b) * 1e-24                    # cm^2
    out = []
    for t in np.atleast_1d(T9):
        kT = KB * t
        integ = np.trapezoid(s * E * np.exp(-E / kT), E)   # cm^2 MeV^2
        sv = np.sqrt(8 / (np.pi * MU * AMU_G)) * (kT * MEV_ERG) ** -1.5 * integ * MEV_ERG**2
        out.append(NA * sv)
    return np.array(out)


def reaclib(name):
    import pynucastro as pyna
    return pyna.ReacLibLibrary().get_rate_by_name(name)


REACLIB_NAMES = {"dn": "d(d,n)he3", "dp": "d(d,p)t"}
BBN_NAMES = {"dn": ("d_d_to_n_He3", "He3_n_to_d_d"), "dp": ("d_d_to_p_t", "t_p_to_d_d")}


def bbn_replace(rates_T9, values):
    """Build a bbn.BBN `replace` dict from {'dp': N_A<sv>(T9_GRID), 'dn': ...}.
    The inverse rates keep REACLIB's detailed-balance ratio."""
    import bbn
    base = {r.name: r for r in bbn.reaclib_rates()}
    lt = np.log(rates_T9)
    rep = {}
    for key, (fwd, rev) in BBN_NAMES.items():
        lv = np.log(values[key])

        def new(TK, lv=lv):
            return float(np.exp(np.interp(np.log(TK / 1e9), lt, lv)))
        f_old, r_old = base[fwd].func, base[rev].func
        rep[fwd] = new
        rep[rev] = (lambda TK, new=new, f_old=f_old, r_old=r_old:
                    r_old(TK) * new(TK) / max(f_old(TK), 1e-300))
    return rep


def run_bbn(values, eta10=6.104):
    import bbn
    return bbn.BBN(eta10=eta10, replace=bbn_replace(T9_GRID, values)).run()
