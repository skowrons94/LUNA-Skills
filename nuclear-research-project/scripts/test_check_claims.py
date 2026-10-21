#!/usr/bin/env python3
"""Self-test of check_claims.py on a temporary project. Prints PASS/FAIL lines; exit 1 on failure."""

import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).with_name("check_claims.py")
ok = True


def run(*args):
    p = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True)
    return p.returncode, p.stdout


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


with tempfile.TemporaryDirectory() as t:
    root = Path(t)
    (root / "docs").mkdir()
    (root / "results").mkdir()
    (root / "results/sfactor.csv").write_text("E,S\n65,4.3\n")
    (root / "results/norm.csv").write_text("n\n1.02\n")
    (root / "docs/CLAIMS.toml").write_text('''
[[claim]]
id = "C1"
statement = "Normalisation of data set B"
value = "1.02 \\\\pm 0.03"
kind = "derived"
evidence = ["results/norm.csv"]
produced_by = "python3 scripts/fit.py"
confidence = "high"
status = "accepted"

[[claim]]
id = "C2"
statement = "S(65 keV)"
value = "4.3 \\\\pm 0.4"
kind = "extrapolated"
evidence = ["results/sfactor.csv"]
produced_by = "python3 scripts/extrapolate.py"
limits = "radius scan quoted separately"
depends_on = ["C1"]
confidence = "medium"
status = "accepted"
''')
    rc, out = run(root, "--accept", "C1", "C2")
    check("accept freezes evidence", rc == 0 and (root / "docs/claims.lock.json").exists(), out.strip())
    rc, out = run(root)
    check("clean register passes", rc == 0, out.strip().splitlines()[-1])

    (root / "report.tex").write_text(r"We find $S(65)=4.3 \pm 0.4$ keV b and a width of $12.1 \pm 0.9$ eV.")
    rc, out = run(root, "--text", root / "report.tex")
    check("untracked quoted value is reported", rc == 0 and "12.1\\pm0.9" in out and "matches no claim" in out)

    (root / "results/norm.csv").write_text("n\n1.05\n")
    rc, out = run(root)
    check("changed evidence makes claim stale", rc == 1 and "C1: STALE" in out)
    check("staleness propagates to dependants", "C2: depends on C1" in out)

    (root / "results/sfactor.csv").unlink()
    rc, out = run(root)
    check("missing evidence is an error", rc == 1 and "evidence file missing" in out)

    (root / "docs/CLAIMS.toml").write_text('''
[[claim]]
id = "C3"
statement = "Rate at 0.1 GK"
kind = "extrapolated"
confidence = "high"
status = "open"
''')
    rc, out = run(root)
    check("unsupported high-confidence and limitless extrapolation rejected",
          rc == 1 and "no evidence" in out and "must state its limits" in out)

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
