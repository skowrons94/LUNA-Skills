#!/usr/bin/env python3
"""Self-test of the MESA helpers on synthetic files (no MESA needed).

Checks: history/profile parsing (header, columns, D exponents, truncated last line, restart
duplicates), inlist editing (existing key with inline comment, new key, other namelists
untouched), rate-table resampling (log interpolation exact for a power law, zero below range,
error above), neutrino flux integration, centre trajectory, composition name mapping, run-log
checks (physical vs solver-limit termination).
Run: python3 selftest.py   -> PASS/FAIL lines; exit code 1 on any failure.
"""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import mesa  # noqa: E402

ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


tmp = Path(tempfile.mkdtemp(prefix="se-selftest-"))


def write_mesa(path, header, names, rows, truncate=False):
    w = 30
    lines = ["".join(f"{i + 1:>{w}d}" for i in range(len(header))),
             "".join(f"{k:>{w}s}" for k in header),
             "".join(f"{v:>{w}s}" for v in header.values()), "",
             "".join(f"{i + 1:>{w}d}" for i in range(len(names))),
             "".join(f"{n:>{w}s}" for n in names)]
    for r in rows:
        lines.append("".join(f"{x:>{w}.16E}".replace("E", "D") if isinstance(x, float) else f"{x:>{w}d}"
                             for x in r))
    if truncate:
        lines.append(lines[-1][: w * 2])
    Path(path).write_text("\n".join(lines) + "\n")


# 1. history with a restart (model 3 repeated) and a truncated line
hist = tmp / "history.data"
rows = [[1, 1.0e6, 7.0, 2.0], [2, 2.0e6, 7.1, 2.1], [3, 3.0e6, 7.2, 2.2],
        [3, 3.1e6, 7.25, 2.25], [4, 4.0e6, 7.3, 2.3]]
write_mesa(hist, {"version_number": '"r26.4.1"', "initial_mass": "1.0D+00"},
           ["model_number", "star_age", "log_center_T", "log_center_Rho"], rows, truncate=True)
h, names, data = mesa.read(hist)
check("history header parsed", h["version_number"] == "r26.4.1" and h["initial_mass"] == 1.0)
check("history rows parsed, truncated line skipped", data.shape == (5, 4))
d2 = mesa.history_rows(names, data)
check("restart duplicate removed (last kept)", list(d2[:, 0]) == [1, 2, 3, 4] and d2[2, 1] == 3.1e6)

# 2. trajectory
out = tmp / "traj.csv"


class A:
    pass


a = A()
a.file, a.center, a.from_age, a.to_age, a.out = str(hist), True, None, None, str(out)
mesa.cmd_trajectory(a)
tr = np.loadtxt(out, delimiter=",", skiprows=1)
check("centre trajectory: time from first point, T and rho from logs",
      tr[0, 0] == 0 and abs(tr[-1, 0] - 3.0e6 * mesa.YEAR_S) < 1 and abs(tr[-1, 1] - 10 ** 7.3) < 1e-3)

# 3. inlist editing
inl = tmp / "inlist"
inl.write_text("&star_job\n    pgstar_flag = .true.\n/\n\n&controls\n"
               "    mesh_delta_coeff = 0.4 ! coarse\n    max_age = 1d9\n/\n")
mesa.set_inlist(inl, "controls", [("mesh_delta_coeff", "0.8"), ("varcontrol_target", "1d-4")])
txt = inl.read_text()
check("inlist: existing key replaced, comment kept", "mesh_delta_coeff = 0.8 ! coarse" in txt)
check("inlist: new key inserted in the right namelist",
      txt.index("varcontrol_target") > txt.index("&controls") and "max_age = 1d9" in txt)
check("inlist: other namelist untouched", "pgstar_flag = .true." in txt)
mesa.set_inlist(inl, "star_job", [("reaction_for_special_factor(1)", "'r_n14_pg_o15'")])
check("inlist: indexed key with string value", "reaction_for_special_factor(1) = 'r_n14_pg_o15'"
      in inl.read_text())

# 4. rate table resampling
T9 = np.geomspace(0.01, 2, 25)
rate = 3e-5 * T9 ** 12.5
T8, r = mesa.rate_table(T9, rate, n=500, T8min=0.05, T8max=20)
inside = (T8 / 10 >= T9[0]) & (T8 / 10 <= T9[-1])
dev = np.max(np.abs(r[inside] / (3e-5 * (T8[inside] / 10) ** 12.5) - 1))
check("rate table: log interpolation exact for a power law", dev < 1e-10, f"{dev:.1e}")
check("rate table: zero below the source table", np.all(r[T8 / 10 < T9[0] * (1 - 1e-9)] == 0))
try:
    mesa.rate_table(T9, rate, T8max=50)
    raised = False
except ValueError:
    raised = True
check("rate table: error above the source table by default", raised)

# 5. neutrino fluxes
prof = tmp / "final.profile"
n = 10
cells = np.full(n, 1e37)
names = ["zone", "mass"] + [f"screened_rate_{rx}" for rx in mesa.NEUTRINO_SOURCES.values()]
rows = [[k + 1, float(1 - k / n)] + [float(cells[k] * (j + 1)) for j in range(8)] for k in range(n)]
write_mesa(prof, {"model_number": "1", "star_age": "4.6D+09"}, names, rows)
flux, missing, _ = mesa.neutrino_fluxes(prof)
expect = 1e38 / (4 * np.pi * mesa.AU_CM ** 2)
check("neutrino fluxes: sum over cells / 4 pi AU^2", abs(flux["pp"] / expect - 1) < 1e-12
      and abs(flux["17F"] / (8 * expect) - 1) < 1e-12 and not missing)

# 6. composition mapping
prof2 = tmp / "comp.profile"
write_mesa(prof2, {"model_number": "1"}, ["zone", "mass", "h1", "he4", "c12", "neut", "logT"],
           [[1, 1.0, 0.7, 0.28, 0.02, 0.0, 6.0], [2, 0.0, 0.3, 0.68, 0.02, 0.0, 7.2]])
X, mk = mesa.composition(prof2, 0.0)
check("composition: centre zone, pynucastro names, non-isotope columns dropped",
      mk == 0.0 and X == {"p": 0.3, "he4": 0.68, "c12": 0.02, "n": 0.0})

# 7. run-log checks
run = tmp / "run"
run.mkdir()
(run / "rn.log").write_text("...\ntermination code: max_age\n log_rel_run_E_err  -9.1D+00\n"
                            "  runtime (minutes), retries, steps       12.0         3       812\n")
r = mesa.check_run(run)
check("check-run: physical termination ok", r["ok"] and r["retries"] == 3 and r["steps"] == 812)
(run / "rn.log").write_text("termination code: max_model_number\n")
check("check-run: solver-limit termination fails", not mesa.check_run(run)["ok"])
(run / "rn.log").write_text("model 10\n")
check("check-run: missing termination fails", not mesa.check_run(run)["ok"])

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
