#!/usr/bin/env python3
"""Self-test of kshell_tools.py (no KSHELL needed).

  1. parse a real KSHELL log fragment (10Be, YSOX, 0-2hw): E, J, parity, T, <Hcm>, occupancies, hw
  2. a 1hw state with <Hcm> = 5.5 is flagged spurious; physical ones (0.03) kept
  3. sd occupancy of a one-nucleon intruder sums to 1.00
  4. calibration: the 7Be study's six ground-state-referenced residuals give
     offset -0.6341 MeV and scatter 1.1581 MeV
  5. write_input round trip: the namelist carries the Lawson term
Run: python3 selftest.py   -> PASS/FAIL lines; exit code 1 on any failure.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kshell_tools as kt  # noqa: E402

ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


LOG = """ n orbit 0p_1/2 0p_3/2 0d_3/2 0d_5/2 1s_1/2
-------------------------------------------------
   1  <H>:   -39.21236  <JJ>:    -0.00000  J:  0/2  prty  1
    <Hcm>:     0.03134  <TT>:     2.00000  T:  2/2
 <p Nj>  0.212  1.756  0.020  0.008  0.004
 <n Nj>  0.500  3.413  0.032  0.047  0.009
 hw:  0:0.940 2:0.060
-------------------------------------------------
   2  <H>:   -35.34796  <JJ>:     6.00000  J:  4/2  prty  1
    <Hcm>:     0.02913  <TT>:     2.00000  T:  2/2
 <p Nj>  0.212  1.747  0.022  0.014  0.005
 <n Nj>  0.548  3.359  0.037  0.048  0.009
   <Qp>    -3.101   <Qn>    -0.147   <eQ>    -3.938
 hw:  0:0.933 2:0.067
-------------------------------------------------
   3  <H>:   -30.10000  <JJ>:     0.75000  J:  1/2  prty -1
    <Hcm>:     5.50000  <TT>:     0.75000  T:  1/2
 <p Nj>  0.300  1.700  0.000  0.000  0.000
 <n Nj>  0.300  1.700  0.000  0.000  1.000
 hw:  1:1.000
-------------------------------------------------
"""
st = kt.parse_log(LOG)
check("three states parsed, sorted by E", len(st) == 3 and st[0]["E"] == -39.21236, str([s["E"] for s in st]))
s0 = st[0]
check("J, parity, T of the ground state", s0["J"] == 0 and s0["parity"] == 1 and s0["T"] == 1.0,
      f"{kt.jpi(s0)} T={s0['T']}")
check("<Hcm> and hw decomposition", abs(s0["Hcm"] - 0.03134) < 1e-9 and s0["hw"] == {0: 0.94, 2: 0.06})
check("2+ is J = 2", st[1]["J"] == 2.0 and kt.jpi(st[1]) == "2+", kt.jpi(st[1]))
phys, spur = kt.flag_spurious(st)
check("spurious 1hw state flagged", len(spur) == 1 and spur[0]["Hcm"] == 5.5 and len(phys) == 2)
check("sd occupancy of a one-nucleon intruder = 1.00", abs(kt.sd_occupancy(st[2]) - 1.0) < 1e-12,
      f"{kt.sd_occupancy(st[2]):.3f}")

bench = [1.20416, 0.77397, -1.27502, -1.58492, -1.42887, -1.49404]
off, unc = kt.calibrate(bench)
check("calibration offset -0.6341", abs(off + 0.63412) < 1e-4, f"{off:.4f}")
check("calibration scatter 1.1581", abs(unc - 1.15815) < 1e-4, f"{unc:.4f}")

with tempfile.TemporaryDirectory() as d:
    txt = kt.write_input(f"{d}/in_x.input", "ysox.snt", "Be7_p13.ptn", 25)
    check("namelist has the Lawson term and the files", "beta_cm = 10.0" in txt and 'fn_ptn = "Be7_p13.ptn"' in txt)

import amplitudes as amp  # noqa: E402
for s in (0.5, 1.5):
    tot = sum(amp.recouple(1, j, 1, 1.5, s) ** 2 for j in (0.5, 1.5))
    check(f"6j recoupling unitary (s = {s})", abs(tot - 1) < 1e-10, f"{tot:.10f}")
check("7Be 1/2+ alpha SF renormalized by mu_4", abs(amp.renormalized_sf(0.0762, 4, {4: 0.5955}) - 0.1280) < 1e-3)

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
