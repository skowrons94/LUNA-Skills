#!/usr/bin/env python3
"""Self-test of uq_checks.py on synthetic cases with known answers. Prints PASS/FAIL; exit 1 on failure."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import uq_checks as U  # noqa: E402

rng = np.random.default_rng(7)
ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


x = np.linspace(100, 1000, 200)
truth = 5 + 0.002 * x
s = np.full_like(x, 0.2)

y = truth + rng.normal(0, 0.2, x.size)
r = U.residual_summary(y, truth, s, x)
check("correct model and errors: no flags", not r["flags"], f"chi2/nu={r['chi2_per_dof']:.2f} p_runs={r['p_runs']:.2f}")

r = U.residual_summary(truth + rng.normal(0, 0.4, x.size), truth, s, x)
check("errors underestimated x2: chi2 flagged", any("too large" in f for f in r["flags"]), f"chi2/nu={r['chi2_per_dof']:.2f}")

bump = 0.3 * np.exp(-0.5 * ((x - 550) / 60) ** 2)
r = U.residual_summary(truth + bump + rng.normal(0, 0.2, x.size), truth, s, x)
check("missed resonance: localised structure flagged at the right place",
      any("localised" in f for f in r["flags"]) and 400 < np.mean(r["local_window"]) < 700,
      f"window {r['local_window']} p={r['p_local']:.3g}")

r = U.residual_summary(1.03 * truth + rng.normal(0, 0.2, x.size), truth, s, x)
check("3 % normalisation offset: pull mean flagged", any("offset" in f for f in r["flags"]), f"pull mean {r['pull_mean']:.2f}")

dm = np.full_like(x, 0.15)
pred = truth + rng.normal(0, 0.15, x.size)  # honest prediction band
c = U.coverage_summary(truth + rng.normal(0, 0.2, x.size), s, pred, dm)
check("honest band: coverage near 68 %", not c["flags"], f"{c['frac_within_1sigma']:.2f}")
c = U.coverage_summary(truth + rng.normal(0, 0.2, x.size), s, truth + rng.normal(0, 0.6, x.size), dm)
check("overconfident band: under-coverage flagged", any("under-coverage" in f for f in c["flags"]),
      f"{c['frac_within_1sigma']:.2f}")

cov = np.array([[1.0, 0.99, 0.0], [0.99, 1.0, 0.1], [0.0, 0.1, 1.0]])
k = U.correlation_summary(cov, ["E_r", "Gamma_p", "a_c"])
check("degenerate pair flagged", any("E_r" in f and "Gamma_p" in f for f in k["flags"]))
k = U.correlation_summary(np.array([[1.0, 1.2], [1.2, 1.0]]))
check("non-positive-definite covariance flagged", any("positive definite" in f for f in k["flags"]))

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
