#!/usr/bin/env python3
"""Tests of kinematics.py against conservation laws, known Q values and thresholds, and the
non-relativistic limit. Run: python3 test_kinematics.py  -> PASS/FAIL lines, exit code 1 on failure."""
import io
import math
import random
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kinematics as K  # noqa: E402


def run(check):
    an = K.masses("13C(a,n)16O")
    pn = K.masses("7Li(p,n)7Be")
    pg = K.masses("12C(p,g)13N")
    check("Q 13C(a,n)16O = 2.2156 MeV", abs(K.q_value(*an) - 2.2156) < 1e-3)
    check("Q 7Li(p,n)7Be = -1.6442 MeV", abs(K.q_value(*pn) + 1.6442) < 1e-3)
    check("threshold 7Li(p,n)7Be = 1.8804 MeV", abs(K.threshold(*pn) - 1.8804) < 5e-4)
    check("exothermic threshold is 0", K.threshold(*an) == 0.0)
    check("parse reaction", K.parse_reaction("13C(a,n)16O") == ("a", "13C", "n", "16O"))

    # energy and momentum conservation at several angles
    worst = 0.0
    for th in (0, 30, 60, 90, 120, 150, 180):
        for s in K.lab_at_angle(*an, 5.0, th):
            worst = max(worst, abs(5.0 + K.q_value(*an) - s["T3"] - s["T4"]))
            p4 = math.sqrt(s["T4"] * (s["T4"] + 2 * an[3]))
            p1 = math.sqrt(5.0 * (5.0 + 2 * an[0]))
            pz = s["p3"] * math.cos(math.radians(th)) + p4 * math.cos(math.radians(s["theta4"]))
            pt = s["p3"] * math.sin(math.radians(th)) - p4 * math.sin(math.radians(s["theta4"]))
            worst = max(worst, abs(pz - p1), abs(pt))
    check("energy and momentum conserved (1e-6 MeV)", worst < 1e-6)

    # near threshold: forward cone with two solutions, nothing at 90 deg, nothing below threshold
    e = K.threshold(*pn)
    check("below threshold: no solution", K.lab_at_angle(*pn, e - 1e-3, 0) == [])
    near = K.lab_at_angle(*pn, e + 0.01, 0)
    check("just above threshold: two solutions at 0 deg", len(near) == 2 and near[0]["T3"] > near[1]["T3"])
    check("just above threshold: no solution at 90 deg", K.lab_at_angle(*pn, e + 0.01, 90) == [])

    # non-relativistic limit for 13C(a,n)16O at 5 MeV, 0 deg
    ma, mc, mn, mo = an
    q, t1 = K.q_value(*an), 5.0
    b = math.sqrt(ma * mn * t1) / (mn + mo)
    c = (mo * q + t1 * (mo - ma)) / (mn + mo)
    t3_nr = (b + math.sqrt(b * b + c)) ** 2
    t3 = K.lab_at_angle(*an, t1, 0)[0]["T3"]
    check("non-relativistic limit within 0.3 %", abs(t3 / t3_nr - 1) < 3e-3)

    # excited final state lowers the ejectile energy, CM<->lab round trip
    ex = K.masses("13C(a,n)16O", ex=6.049)
    check("excited residual (6.049 MeV): channel closed at 5 MeV", K.lab_at_angle(*ex, 5.0, 0) == [])
    t3g, t3x = K.lab_at_angle(*an, 8.0, 0)[0]["T3"], K.lab_at_angle(*ex, 8.0, 0)[0]["T3"]
    check("excited residual: T3 lower by at least ~Ex at 8 MeV", t3g - t3x > 0.8 * 6.049)
    t3c, u = K.lab_from_cm(*an, 5.0, 0.3)
    th = math.degrees(math.acos(u[2]))
    sols = K.lab_at_angle(*an, 5.0, th)
    check("CM -> lab round trip", any(abs(s["T3"] - t3c) < 1e-9 and abs(math.cos(math.radians(s["theta_cm"])) - 0.3)
                                      < 1e-9 for s in sols))

    # capture gamma: Doppler ordering and E_gamma ~ Q + E_cm
    g0, g90, g180 = (K.lab_at_angle(*pg, 0.5, a)[0]["T3"] for a in (0, 90, 180))
    check("(p,g) Doppler: E(0) > E(90) > E(180)", g0 > g90 > g180)
    check("(p,g) E_gamma(90) ~ Q + E_cm within 2 keV", abs(g90 - (K.q_value(*pg) + 0.5 * pg[1] / (pg[0] + pg[1])))
          < 2e-3)

    # thick target: constant sigma/stopping -> total weight = energy range; spectrum inside kinematic limits
    tt = K.thick_target_spectrum(*an, 5.0, lambda e: 1.0, lambda e: 1.0, n_e=50, n_cos=50)
    check("thick target: total weight = T0 - threshold", abs(sum(w for _, w in tt) - 5.0) < 1e-9)
    tmax = K.lab_at_angle(*an, 5.0, 0)[0]["T3"]
    check("thick target: T3 never above the 0-deg maximum", max(t for t, _ in tt) <= tmax + 1e-9)
    # CM -> lab Jacobian: against finite differences of d(cos theta_cm)/d(cos theta_lab), each branch
    worst = 0.0
    for m, t1, th in ((an, 5.0, 40.0), (pn, 1.885, 10.0), (pn, 2.3, 10.0)):
        h = 1e-4
        lo, mid, hi = (K.lab_at_angle(*m, t1, th + d) for d in (-h, 0.0, h))
        for b in range(len(mid)):
            dc_cm = math.cos(math.radians(hi[b]["theta_cm"])) - math.cos(math.radians(lo[b]["theta_cm"]))
            dc_lab = math.cos(math.radians(th + h)) - math.cos(math.radians(th - h))
            worst = max(worst, abs(K.cm_to_lab_jacobian(*m, t1, mid[b]) / abs(dc_cm / dc_lab) - 1))
    check("Jacobian dOmega_cm/dOmega_lab matches finite differences (1e-4)", worst < 1e-4)

    def solid_angle_integral(m, t1, n=4000):  # integral of the Jacobian over the lab sphere, all branches
        tot = 0.0
        for i in range(n):  # midpoint rule in theta; the integrable edge singularity converges slowly
            th = (i + 0.5) * 180.0 / n
            tot += sum(K.cm_to_lab_jacobian(*m, t1, sl) for sl in K.lab_at_angle(*m, t1, th)) * \
                2 * math.pi * math.sin(math.radians(th)) * math.radians(180.0 / n)
        return tot
    check("Jacobian integrates to 4 pi (one branch, 13C(a,n) 5 MeV)", abs(solid_angle_integral(an, 5.0) / (4 * math.pi) - 1) < 1e-4)
    check("Jacobian integrates to 4 pi (two branches, 7Li(p,n) 1.885 MeV)",
          abs(solid_angle_integral(pn, 1.885, 20000) / (4 * math.pi) - 1) < 0.02)

    # thick target at fixed lab angles: integrating the per-steradian weights over the sphere gives back
    # the angle-integrated total (would fail without the Jacobian)
    sig, eps = (lambda e: 1.0 + 0.3 * e), (lambda e: 2.0 / (0.5 + e))
    total = sum(w for _, w in K.thick_target_spectrum(*an, 5.0, sig, eps, n_e=20, n_cos=20))
    n_th, integ = 360, 0.0
    for i in range(n_th):
        th = (i + 0.5) * 180.0 / n_th
        w_th = sum(w for _, w in K.thick_target_spectrum(*an, 5.0, sig, eps, theta_deg=th, n_e=20))
        integ += w_th * 2 * math.pi * math.sin(math.radians(th)) * math.radians(180.0 / n_th)
    check("thick target: lab-angle weights integrate over 4 pi to the angle-integrated yield",
          abs(integ / total - 1) < 1e-3)
    fwd = sum(w for _, w in K.thick_target_spectrum(*an, 5.0, sig, eps, theta_deg=0.0, n_e=20))
    bwd = sum(w for _, w in K.thick_target_spectrum(*an, 5.0, sig, eps, theta_deg=180.0, n_e=20))
    check("thick target: forward focusing (yield per lab sr larger at 0 than at 180 deg)", fwd > bwd)
    h = K.histogram(K.isotropic_spectrum(*an, 5.0, 500), 20)
    check("histogram preserves total weight", abs(sum(w for _, _, w in h) - 1.0) < 1e-9)

    ev1 = K.sample_events(*an, 5.0, 200, random.Random(7))
    ev2 = K.sample_events(*an, 5.0, 200, random.Random(7))
    check("events: same seed reproduces", ev1 == ev2)
    check("events: unit directions", all(abs(x * x + y * y + z * z - 1) < 1e-9 for _, x, y, z in ev1))

    with tempfile.TemporaryDirectory() as tmp:
        spec, evf = Path(tmp) / "s.csv", Path(tmp) / "e.csv"
        with redirect_stdout(io.StringIO()):
            rc = K.main(["13C(a,n)16O", "--T1", "5", "--theta", "0", "--spectrum", str(spec),
                         "--events", "10", "--out", str(evf)])
        rows = [r for r in spec.read_text().splitlines() if not r.startswith("#")]
        check("CLI writes spectrum and events", rc == 0 and len(rows) == 50 and
              len(evf.read_text().splitlines()) == 11)


if __name__ == "__main__":
    failed = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            failed.append(name)

    run(check)
    print("FAIL" if failed else "PASS")
    sys.exit(1 if failed else 0)
