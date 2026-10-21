#!/usr/bin/env python3
"""Self-test: contracts accept the real outputs of the upstream demos and reject corrupted copies;
adapters convert units, frames and S factors correctly; provenance detects changed inputs.
Runs the yield-analysis and efficiency-analysis demos (NumPy, SciPy, Matplotlib needed for those).
Prints PASS/FAIL lines; exit 1 on failure."""

import csv
import io
import json
import math
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import adapters  # noqa: E402
import contracts  # noqa: E402
import provenance  # noqa: E402

ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


def quiet(f, *a):
    with redirect_stdout(io.StringIO()):
        return f(*a)


with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    subprocess.run([sys.executable, REPO / "yield-analysis/scripts/demo.py", "--out", t / "y"], check=True,
                   capture_output=True)
    subprocess.run([sys.executable, REPO / "efficiency-analysis/scripts/demo.py", "--out", t / "e"], check=True,
                   capture_output=True)
    yields, eff = t / "y/result/yields.csv", t / "e/result/result.json"

    check("spectrum-csv accepts demo spectrum", contracts.check("spectrum-csv", t / "y/spectrum.csv") == [])
    check("yield-table accepts demo output", contracts.check("yield-table", yields) == [])
    check("efficiency-curve accepts demo fit", contracts.check("efficiency-curve", eff) == [])

    bad = t / "bad"
    bad.mkdir()
    rows = list(csv.DictReader(open(yields)))
    with open(bad / "yields.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in rows[0] if k != "stat_error"])
        w.writeheader()
        w.writerows([{k: v for k, v in r.items() if k != "stat_error"} for r in rows])
    errs = contracts.check("yield-table", bad / "yields.csv")
    check("yield-table rejects missing column and missing companions",
          any("missing columns" in e for e in errs), errs[0] if errs else "")
    d = json.loads(eff.read_text())
    d["quantity"] = "total"
    (bad / "eff.json").write_text(json.dumps(d))
    check("efficiency-curve rejects a total-efficiency curve",
          any("full-energy-peak" in e for e in contracts.check("efficiency-curve", bad / "eff.json")))

    # efficiency-at reproduces the curve and its uncertainty
    class A: pass
    a = A(); a.result, a.energies, a.out = str(eff), [661.657, 1332.492, 5000.0], str(t / "eff_at.csv")
    rows_e, corr = quiet(adapters.efficiency_at, a)
    c, e0 = d["coefficients"], d["reference_energy_keV"]
    direct = math.exp(sum(ci * math.log(661.657 / e0) ** i for i, ci in enumerate(c)))
    check("efficiency-at matches the curve", abs(rows_e[0]["efficiency"] / direct - 1) < 1e-12)
    check("efficiency-at flags extrapolation", rows_e[2]["warning"].startswith("outside"))
    check("efficiency correlation matrix is symmetric with unit diagonal",
          all(abs(corr[i][i] - 1) < 1e-9 for i in range(3)) and abs(corr[0][1] - corr[1][0]) < 1e-12)
    check("adapter writes provenance sidecar", (t / "eff_at.csv.prov.json").exists())

    # yields -> excitation curve satisfies the next contract
    a = A(); a.yields, a.out, a.match, a.error = str(yields), str(t / "exc.csv"), None, "stat"
    quiet(adapters.yields_to_excitation, a)
    check("yields-to-excitation output satisfies excitation-curve", contracts.check("excitation-curve", t / "exc.csv") == [])

    # to-azure: frame, units, Sommerfeld factor
    m1, m2 = 1.007825, 12.0
    with open(t / "s.csv", "w") as f:
        f.write("E_cm_keV,S,dS\n100,1.5,0.1\n200,1.6,0.1\n")
    args = ["to-azure", str(t / "s.csv"), str(t / "s.dat"), "--energy-col", "E_cm_keV", "--energy-unit", "keV",
            "--frame", "cm", "--value-col", "S", "--value-kind", "sfactor", "--value-unit", "keVb",
            "--error-col", "dS", "--angle", "0", "--z1", "1", "--z2", "6", "--m1", str(m1), "--m2", str(m2)]
    quiet(adapters.main, args)
    first = [float(x) for x in (t / "s.dat").read_text().split()[:4]]
    mu = m1 * m2 / (m1 + m2)
    tpe = 31.29 * 6 * math.sqrt(mu / 100)  # textbook 2*pi*eta with E in keV, mu in amu
    sigma = 1.5 / 100 * math.exp(-tpe)
    check("cm -> lab energy in MeV", abs(first[0] / (0.1 * (m1 + m2) / m2) - 1) < 1e-7, f"{first[0]}")
    check("S factor -> cross section (b) with Sommerfeld factor", abs(first[2] / sigma - 1) < 2e-3,
          f"{first[2]:.4e} vs {sigma:.4e}")
    check("to-azure output satisfies azure-dat", contracts.check("azure-dat", t / "s.dat") == [])
    (t / "kev.dat").write_text("150 0 1e-9 1e-10\n")
    check("azure-dat flags keV energies", any("keV" in e for e in contracts.check("azure-dat", t / "kev.dat")))

    # provenance detects a changed input
    side = provenance.record(t / "s.dat", [t / "s.csv"], cmd="test", skill="azure2")
    check("provenance verifies unchanged files", provenance.verify(side) == [])
    (t / "s.csv").write_text("E_cm_keV,S,dS\n100,1.7,0.1\n")
    check("provenance detects a changed input", any("changed" in p for p in provenance.verify(side)))
    rec = json.loads(side.read_text())
    check("provenance records the SKILL.md hash", rec["skill"]["skill_md_sha256"] is not None)

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
