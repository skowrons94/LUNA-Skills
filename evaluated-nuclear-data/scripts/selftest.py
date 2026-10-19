#!/usr/bin/env python3
"""Offline checks of the window integrals in xs.py (no nuclear data needed). Prints PASS.

1/v cross section sigma = c/sqrt(E):  MACS(kT) = sigma(kT)  and  RI(0.5 eV, inf) = 2 c / sqrt(0.5).
Constant cross section: averages equal the constant, except MACS = (2/sqrt(pi)) sigma by definition.
If ~/nuclear-data holds an OpenMC library, also checks that 10B(n,alpha) at 0.0253 eV is ~3840 b.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import xs  # noqa: E402

E = np.geomspace(1e-5, 2e7, 200000)
c = 3840.0 * np.sqrt(0.0253)
s = c / np.sqrt(E)
ok = True

def check(name, got, want, tol):
    global ok
    good = abs(got / want - 1) < tol
    ok &= good
    print(f"{'ok ' if good else 'BAD'} {name}: {got:.6g} (expected {want:.6g})")

check("thermal 1/v", xs.thermal(E, s), 3840.0, 1e-4)
check("MACS 1/v at 30 keV", xs.macs(E, s, 30e3), c / np.sqrt(30e3), 2e-3)
check("RI 1/v 0.5 eV-100 keV", xs.resonance_integral(E, s), 2 * c * (1 / np.sqrt(0.5) - 1 / np.sqrt(1e5)), 1e-3)
one = np.ones_like(E)
check("MACS constant (= 2/sqrt(pi) by definition)", xs.macs(E, one), 2 / np.sqrt(np.pi), 2e-3)
check("Watt average constant", xs.watt_average(E, one), 1.0, 1e-6)
check("1/E mean constant", xs.mean_1overE(E, one), 1.0, 1e-6)

lib = next((k for k in xs.LIBRARIES if xs.find_h5(k, "B10")), None)
if lib:
    try:
        Eb, sb = xs.from_hdf5(xs.find_h5(lib, "B10"), 107)
        check(f"10B(n,alpha) thermal, {lib}", xs.thermal(Eb, sb), 3840.0, 0.02)
    except Exception as e:  # library present but unusable: report, do not fail
        print(f"skip library check: {e}")
else:
    print("skip library check: no OpenMC library with B10 found")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
