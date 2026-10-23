#!/usr/bin/env python3
"""Self-test of gcm.py with known answers (the 7Be alpha+3He microscopic study).

  1. small-R limit of the projected norm kernel: mu_3 = 1.19097, mu_4 = 0.59549
  2. large-R limit of the norm kernel = direct relative-motion overlap (ratio 1)
  3. Minnesota alpha energy at b = 1.36 fm: -24.283 MeV, independent of u
  4. configure('alpha', 't'): Z1Z2 = 2, reduced mass number 12/7, 7 nucleons
  5. (--full, ~minutes) end to end: b = 1.36 fm kernels, u fixed on the l=1 bound-state
     centroid (-1.444 MeV) -> u = 0.9809, s-wave a0 = 40.6 fm, r0 = 1.03 fm (7Be study);
     needs the effective-range skill next to this one
Run: python3 selftest.py [--full]   -> PASS/FAIL lines; exit code 1 on any failure.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gcm  # noqa: E402

ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


gcm.configure("alpha", "3He")
res = gcm.check_structure(b=1.40, u=1.0, nmin=3)
for key, (got, want) in res.items():
    tol = 2e-4 if key.startswith("mu") else 2e-3
    check(key, abs(got - want) < tol, f"{got:.5f} (expected {want:.5f})")

Ea1 = gcm.cluster_energy(gcm.ALPHA, 1.36, 1.0)
Ea0 = gcm.cluster_energy(gcm.ALPHA, 1.36, 0.0)
check("E_alpha(b=1.36) = -24.283 MeV", abs(Ea1 + 24.283) < 0.01, f"{Ea1:.3f}")
check("E_alpha independent of u (space symmetric)", abs(Ea1 - Ea0) < 1e-9, f"{Ea0:.3f}")

gcm.configure("alpha", "t")
check("alpha+t: Z1Z2 = 2, A = 7, mu_A = 12/7",
      gcm.Z1Z2 == 2 and len(gcm.LABELS) == 7 and abs(gcm.MU_A - 12 / 7) < 1e-12,
      f"Z1Z2={gcm.Z1Z2}, A={len(gcm.LABELS)}")

if "--full" in sys.argv:
    import numpy as np
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "effective-range" / "scripts"))
    import ere
    gcm.configure("alpha", "3He")
    Rs = np.round(np.arange(0.8, 12.01, 0.8), 3)
    K, Et = gcm.build_kernels(Rs, [0, 1], 1.36)
    u = gcm.fit_u_bound(K, Et, 1, -(4 * 1.5866 + 2 * 1.1575) / 6)
    check("u fixed on the p-wave centroid = 0.9809", abs(u - 0.9809) < 2e-3, f"{u:.4f}")
    Es = np.linspace(0.05, 6.0, 120)
    d0 = gcm.phase_curve(gcm.rmatrix(K, Et, Rs, 1.36, 0, u), Es)
    f = ere.fit_ere(ere.Pair("alpha", "3He"), Es, d0, 0.20, 2.00, order=2)
    check("microscopic a0 = 40.6 fm", abs(f["a0"] - 40.6) < 0.5, f"{f['a0']:.2f}")
    check("microscopic r0 = 1.03 fm", abs(f["r0"] - 1.027) < 0.01, f"{f['r0']:.3f}")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
