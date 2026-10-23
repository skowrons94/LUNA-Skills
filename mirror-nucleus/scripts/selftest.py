#!/usr/bin/env python3
"""Self-test of mirror.py with known answers (7Be <-> 7Li, alpha+3He <-> alpha+t).

Needs the cluster-potential skill next to this one.
  1. mirror_system(alpha+3He) = alpha+t, Z1Z2 4 -> 2, geometry kept
  2. 7Be depths (fitted on the four negative-parity 7Be levels) predict 7Li with nothing
     refitted: 3/2- at -2.430, 1/2- at -1.983, 7/2- at +2.10 MeV (study values)
  3. ground-state ANC ratio C^2(7Be)/C^2(7Li) = 1.333 with spread < 0.01 over
     ranges 2.50-2.90 fm, while each C^2 varies by tens of percent
  4. theta2_at_radii and threshold_shift arithmetic
Run: python3 selftest.py   -> PASS/FAIL lines; exit code 1 on any failure.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mirror as mr  # noqa: E402

cl = mr.cl
ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


be7 = cl.System("alpha", "3He", thr_ex=1.5866, n_min=3)
li7 = mr.mirror_system(be7, thr_ex=2.4675)
check("mirror of alpha+3He is alpha+t", (li7.c1, li7.c2) == ("alpha", "t") and li7.zz == 2 and li7.n_min == 3)

A0 = 2.6883
DEPTHS = {"3/2-": (75.24282, 1, 1, True), "1/2-": (73.50376, 1, 1, True), "7/2-": (74.48709, 3, 0, False)}
pred = mr.predict_levels(li7, DEPTHS, A0)
for lab, want, tol in (("3/2-", -2.430, 0.01), ("1/2-", -1.983, 0.01), ("7/2-", 2.103, 0.03)):
    E = pred[lab][0]
    check(f"7Li {lab} predicted at {want:+.3f} MeV", E is not None and abs(E - want) < tol, f"{E:+.3f}")

rows, mean, spread = mr.anc_ratio(be7, -1.5866, li7, -2.4675, l=1, nodes=1)
c2 = [r[2] for r in rows]
check("ANC ratio 7Be/7Li = 1.333", abs(mean - 1.333) < 0.01, f"{mean:.3f}")
check("ratio stable over the geometry (spread < 0.01)", spread < 0.01, f"{spread:.4f}")
check("individual C^2 varies strongly", (max(c2) - min(c2)) / min(c2) > 0.1, f"{min(c2):.1f}-{max(c2):.1f} fm^-1")

P, _ = cl.PS(be7, 0, 6.8, 4.7)
G = 2 * P * 1.3 * cl.gamma2_W(be7, 4.7)
t = mr.theta2_at_radii(be7, G, 6.8, 0, [4.7, 5.5])
check("theta2 at the fit radius round-trips", abs(t[4.7] - 1.3) < 1e-12, f"{t[4.7]:.4f} (5.5 fm: {t[5.5]:.3f})")
dEx, drel = mr.threshold_shift(8.40, 5.606, 9.56, 7.250)
check("threshold_shift arithmetic", abs(dEx - 1.16) < 1e-12 and abs(drel - (-0.484)) < 1e-12, f"{dEx:.3f}, {drel:.3f}")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
