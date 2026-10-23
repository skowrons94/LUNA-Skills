#!/usr/bin/env python3
"""Self-test of ere.py with known answers.

  1. C0^2 -> 1 as eta -> 0; h(eta) -> 1/(12 eta^2) for large eta
  2. K is unchanged by delta -> delta + 180 deg (n*pi insensitivity)
  3. a synthetic phase with (a0, r0, P) = (40, 1.0, -0.3) is recovered by the order-2 fit
  4. the order-1 fit of the same phase over a long range is biased (the trap)
  5. one-level s wave, alpha+3He, a = 4.7 fm, E_x = 8.3887 MeV (E_lam = 6.8021 MeV c.m.):
     theta^2 needed for a0 = 22 / 40 / 60 fm is 2.234 / 1.548 / 0.934 (7Be study)
Run: python3 selftest.py   -> PASS/FAIL lines; exit code 1 on any failure.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import ere  # noqa: E402

ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


check("C0^2 -> 1 as eta -> 0", abs(ere.C0sq(1e-6) - 1) < 1e-5, f"{ere.C0sq(1e-6):.6f}")
e = 50.0
check("h(eta) -> 1/(12 eta^2) for large eta", abs(ere.hfun(e) - 1 / (12 * e * e)) < 1e-7, f"{ere.hfun(e):.3e}")

pair = ere.Pair("alpha", "3He")
E = np.linspace(0.20, 2.00, 60)
d = ere.delta_from_ere(pair, E, 40.0, 1.0, -0.3)
K1, K2 = ere.Kfun(pair, E, d), ere.Kfun(pair, E, d + 180.0)
check("K insensitive to delta + 180 deg", np.max(np.abs(K1 - K2)) < 1e-10)

f = ere.fit_ere(pair, E, d, 0.20, 2.00, order=2)
check("recover a0 = 40 fm", abs(f["a0"] - 40.0) < 1e-6, f"{f['a0']:.6f}")
check("recover r0 = 1.0 fm", abs(f["r0"] - 1.0) < 1e-8, f"{f['r0']:.8f}")
check("recover P = -0.3 fm^3", abs(f["P"] + 0.3) < 1e-8, f"{f['P']:.8f}")

E2_ = np.linspace(0.30, 4.0, 60)
d2 = ere.delta_from_ere(pair, E2_, 40.0, 1.0, -0.3)
g = ere.fit_ere(pair, E2_, d2, 0.30, 4.0, order=1)
check("order-1 fit over 0.3-4 MeV is biased (trap)", abs(g["a0"] - 40.0) > 1.0, f"a0 = {g['a0']:.2f} fm")

E_lam = 8.3887 - 1.5866
for a0, want in ((22.0, 2.234), (40.0, 1.548), (60.0, 0.934)):
    t = ere.theta2_for_a0(pair, E_lam, a0, 4.7)
    check(f"one-level theta^2 for a0 = {a0:.0f} fm", abs(t - want) < 0.01, f"{t:.3f} (study {want})")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
