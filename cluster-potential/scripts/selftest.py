#!/usr/bin/env python3
"""Self-test of cluster.py with known answers (the 7Be/7Li alpha-cluster study).

  1. Pauli bookkeeping: alpha+3He N_min = 3; forbidden counts per l
  2. norm kernel: mu_0..2 = 0 (forbidden), mu_3 = 1.19097, mu_4 = 0.59549 (alpha+3He)
  3. point Coulomb with V0 = 0 gives zero nuclear phase shift (a finite Rc does not:
     the uniform sphere differs from a point charge inside Rc, 0.008 rad at 1 MeV)
  4. the 7Be g.s. (l=1, 1 node, -1.5866 MeV) at range 2.6883 fm needs V0 = 75.24 MeV
  5. the fitted potential is admissible (binds exactly the forbidden l=1 state + the g.s.)
  6. its ANC: C^2 = 23.0 fm^-1 (study value)
  7. mirror: the same depth with alpha+t (Z1Z2=2, triton mass) puts the 7Li g.s. at -2.430 MeV
  8. theta2_from_width inverts Gamma = 2 P theta^2 gamma_W^2
Run: python3 selftest.py   -> PASS/FAIL lines; exit code 1 on any failure.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import cluster as cl  # noqa: E402

ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


A0 = 2.6883
be7 = cl.System("alpha", "3He", thr_ex=1.5866, n_min=cl.s_shell_n_min("alpha", "3He"))
li7 = cl.System("alpha", "t", thr_ex=2.4675, n_min=cl.s_shell_n_min("alpha", "t"))

check("N_min(alpha+3He) = 3", be7.n_min == 3, f"got {be7.n_min}")
nf = [cl.n_forbidden(be7, l) for l in range(5)]
check("forbidden states per l = [2,1,1,0,0]", nf == [2, 1, 1, 0, 0], str(nf))

w = cl.alpha_x_weights("3He")
mu = [cl.norm_kernel_mu(N, 4, 3, w) for N in range(5)]
check("mu_0..2 = 0", max(abs(m) for m in mu[:3]) < 1e-12, str(np.round(mu[:3], 14)))
check("mu_3 = 1.19097", abs(mu[3] - 1.19097) < 1e-5, f"{mu[3]:.5f}")
check("mu_4 = 0.59549", abs(mu[4] - 0.59549) < 1e-5, f"{mu[4]:.5f}")

d0 = cl.phase_shift(cl.Pot(be7, 0.0, A0, Rc=1e-3), 0, 1.0)   # point Coulomb, no nuclear well
check("point Coulomb, V0 = 0: delta = 0 (mod pi)", abs(np.sin(d0)) < 2e-4, f"sin(delta) = {np.sin(d0):.1e}")

V = cl.fit_V0_bound(be7, 1, 1, -1.5866, A0)
check("7Be g.s. depth 75.24 MeV", abs(V - 75.24) < 0.05, f"{V:.3f}")
pot = cl.Pot(be7, V, A0)
check("fitted potential admissible (l=1)", cl.pauli_ok(pot, 1))
C = cl.anc(pot, 1, -1.5866)
check("7Be g.s. C^2 = 23.0 fm^-1", abs(C * C - 23.0) < 0.5, f"{C * C:.2f}")

Eli = cl.level(cl.Pot(li7, V, A0), 1, 1)
check("mirror 7Li g.s. predicted at -2.430 MeV", Eli is not None and abs(Eli + 2.430) < 0.01, f"{Eli:.3f}")

P, _ = cl.PS(be7, 0, 2.0, 4.7)
G = 2 * P * 1.3 * cl.gamma2_W(be7, 4.7)
t = cl.theta2_from_width(be7, G, 2.0, 0, 4.7)
check("theta2_from_width round trip", abs(t - 1.3) < 1e-12, f"{t:.6f}")

# orthogonality-condition model, Pauli only (no nuclear well): alpha+3He s wave, b = 1.36 fm (7Be study)
d1 = np.degrees(cl.ocm_phase(be7, 0, 1.0, 1.36)); d1 = (d1 + 90) % 180 - 90
d2 = np.degrees(cl.ocm_phase(be7, 0, 1.0, 1.36, lam=1e4)); d2 = (d2 + 90) % 180 - 90
check("OCM Pauli-only delta0(1 MeV) = -6.83 deg", abs(d1 + 6.83) < 0.05, f"{d1:.3f}")
check("OCM converged in lambda (1e4 vs 1e5)", abs(d1 - d2) < 0.02, f"{d2 - d1:+.3f} deg")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
