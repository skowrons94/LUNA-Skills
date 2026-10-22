#!/usr/bin/env python3
"""MESA helpers: read output, check runs, edit inlists, rate tables, trajectories, neutrinos.

  python3 mesa.py columns LOGS/history.data                     list header values and columns
  python3 mesa.py final LOGS/history.data star_age log_L log_R  last-row values
  python3 mesa.py check-run RUN_DIR [--log rn.log]               termination, errors, energy error
  python3 mesa.py set inlist_project controls max_age=4.6d9 'reaction_for_special_factor(1)'="'r_n14_pg_o15'"
  python3 mesa.py rate-table rate.csv --out r_mg25_pg_al26.dat --reaction r_mg25_pg_al26
  python3 mesa.py trajectory LOGS/history.data --center --out traj.csv [--from-age 1e6 --to-age 1e10]
  python3 mesa.py composition final.profile --mass 0.0 --out X.json       mass fractions at m (Msun)
  python3 mesa.py neutrinos final.profile [--json out.json]     solar neutrino fluxes at 1 AU
  python3 mesa.py compare A/LOGS/history.data B/LOGS/history.data star_age log_L ...

Standard library and numpy only. MESA output: line 1 column numbers, 2 header names, 3 header
values, 5 column numbers, 6 column names, data from line 7.
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

YEAR_S = 3.15576e7          # Julian year, MESA's secyer
AU_CM = 1.495978707e13
MSUN_G = 1.98840987e33      # MESA const msun (IAU 2015 nominal GM / G)

# neutrino-producing reactions in MESA nets (pp_and_cno_extras and larger)
NEUTRINO_SOURCES = {
    "pp": "r_h1_h1_wk_h2",
    "pep": "r_h1_h1_ec_h2",
    "hep": "r_h1_he3_wk_he4",
    "7Be": "r_be7_wk_li7",
    "8B": "r_b8_wk_he4_he4",
    "13N": "r_n13_wk_c13",
    "15O": "r_o15_wk_n15",
    "17F": "r_f17_wk_o17",
}

# MESA isotope names that differ from pynucastro's
MESA_TO_PYNA = {"h1": "p", "neut": "n", "prot": "p", "h2": "d", "h3": "t"}


def read(path):
    """Return (header dict, column names, 2-D float array) of a MESA history/profile file."""
    lines = Path(path).read_text().splitlines()
    hnames, hvals = lines[1].split(), lines[2].split()
    header = {}
    for k, v in zip(hnames, hvals):
        v = v.strip('"')
        try:
            header[k] = float(v.replace("D", "E"))
        except ValueError:
            header[k] = v
    names = lines[5].split()
    rows = []
    for ln in lines[6:]:
        p = ln.split()
        if len(p) != len(names):
            continue  # truncated last line of a running model
        rows.append([float(x.replace("D", "E")) for x in p])
    return header, names, np.array(rows)


def col(names, data, name):
    if name not in names:
        raise KeyError(f"column {name!r} not in file; add it to history_columns.list or "
                       f"profile_columns.list (have e.g. {names[:8]} ...)")
    return data[:, names.index(name)]


def history_rows(names, data):
    """Drop rows superseded by a backup or restart (model_number not increasing)."""
    if "model_number" not in names:
        return data
    mn = col(names, data, "model_number")
    keep = np.ones(len(mn), bool)
    last = np.inf
    for i in range(len(mn) - 1, -1, -1):  # keep the last occurrence of each model number
        if mn[i] >= last:
            keep[i] = False
        else:
            last = mn[i]
    return data[keep]


# --------------------------------------------------------------------------- commands

def cmd_columns(a):
    h, names, data = read(a.file)
    for k, v in h.items():
        print(f"  {k} = {v}")
    print(f"{len(names)} columns, {len(data)} rows:")
    print("  " + " ".join(names))
    return 0


def cmd_final(a):
    h, names, data = read(a.file)
    data = history_rows(names, data)
    for c in a.columns:
        print(f"{c} = {col(names, data, c)[-1]:.10g}")
    return 0


def cmd_compare(a):
    _, na, da = read(a.a)
    _, nb, db = read(a.b)
    da, db = history_rows(na, da), history_rows(nb, db)
    print(f"{'column':24s} {'A':>16s} {'B':>16s} {'B/A - 1':>12s}")
    for c in a.columns:
        x, y = col(na, da, c)[-1], col(nb, db, c)[-1]
        rel = y / x - 1 if x else float("nan")
        print(f"{c:24s} {x:16.8g} {y:16.8g} {rel:+12.4e}")
    return 0


def check_run(run_dir, log="rn.log", done_pattern=None, allow=()):
    """Read a run's terminal log: termination code, retries, errors, final energy error.
    Cases that stop from run_star_extras (e.g. simplex_solar_calibration at its target age)
    print no termination code; pass done_pattern, a regex their log prints on success."""
    p = Path(run_dir) / log
    if not p.exists():
        return {"ok": False, "problems": [f"no {log} in {run_dir}"]}
    txt = p.read_text(errors="replace")
    out = {"ok": True, "problems": []}
    tc = re.findall(r"termination code:\s*(\S+)", txt)
    out["termination_codes"] = tc
    if done_pattern:
        out["done_pattern_found"] = bool(re.search(done_pattern, txt))
    if not tc and not out.get("done_pattern_found"):
        out["ok"] = False
        out["problems"].append("no termination code (and no done pattern): the run did not finish")
    bad = ("max_model_number", "min_timestep_limit", "max_number_retries", "dt_is_zero",
           "nonzero_ierr", "failed_in_")
    for t in tc:
        if t in allow:  # an intentional stop for this study (e.g. a fixed number of models)
            continue
        if any(b in t for b in bad):
            out["ok"] = False
            out["problems"].append(f"termination '{t}' is a solver limit, not the physical stop")
    for pat in ("ERROR", "STOP", "failed", "Backtrace", "NaN"):
        n = len(re.findall(rf"\b{pat}\b", txt))
        if n:
            out.setdefault("log_hits", {})[pat] = n
    if out.get("log_hits", {}).get("Backtrace") or "STOP 1" in txt:
        out["ok"] = False
        out["problems"].append("crash in log (Backtrace / STOP 1)")
    e = re.findall(r"log_rel_run_E_err\s+(\S+)", txt)
    if e:
        out["log_rel_run_E_err"] = float(e[-1].replace("D", "E"))
        if out["log_rel_run_E_err"] > -3:
            out["problems"].append(f"cumulative energy error 10^{out['log_rel_run_E_err']:.1f}")
    rt = re.findall(r"runtime \(minutes\), retries, steps\s+(\S+)\s+(\S+)\s+(\S+)", txt)
    if rt:
        out["runtime_min"], out["retries"], out["steps"] = float(rt[-1][0]), int(rt[-1][1]), int(rt[-1][2])
    return out


def cmd_check_run(a):
    r = check_run(a.dir, a.log, a.done, tuple(a.allow or ()))
    print(json.dumps(r, indent=1))
    return 0 if r["ok"] else 1


DEFAULTS_FILES = {"star_job": "star/defaults/star_job.defaults",
                  "controls": "star/defaults/controls.defaults",
                  "pgstar": "star/defaults/pgstar.defaults",
                  "eos": "eos/defaults/eos.defaults", "kap": "kap/defaults/kap.defaults"}


def known_keys(namelist, mesa_dir=None):
    """Keys MESA accepts in a namelist, from its *.defaults file (None if unavailable)."""
    mesa_dir = mesa_dir or os.environ.get("MESA_DIR")
    rel = DEFAULTS_FILES.get(namelist.lower())
    if not mesa_dir or not rel or not (Path(mesa_dir) / rel).exists():
        return None
    keys = set()
    for ln in (Path(mesa_dir) / rel).read_text().splitlines():
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(\([^)]*\))?\s*=", ln)
        if m:
            keys.add(m.group(1).lower())
    return keys


def set_inlist(path, namelist, assignments, mesa_dir=None):
    """Set key = value inside &namelist ... / of an inlist file; insert the key if absent.
    Values are written verbatim (Fortran syntax: 1d-3, .true., 'string'). Keys are checked
    against $MESA_DIR's defaults for that namelist: a key in the wrong namelist makes MESA stop
    with 'Failed while trying to read ... namelist'."""
    keys = known_keys(namelist, mesa_dir)
    if keys is not None:
        bad = [k for k, _ in assignments if re.sub(r"\(.*\)", "", k).strip().lower() not in keys]
        if bad:
            others = [nl for nl in DEFAULTS_FILES if nl != namelist and (known_keys(nl, mesa_dir) or set())
                      & {re.sub(r"\(.*\)", "", b).lower() for b in bad}]
            raise KeyError(f"not &{namelist} options in this MESA: {bad}"
                           + (f" (found in &{', &'.join(others)})" if others else ""))
    txt = Path(path).read_text()
    m = re.search(rf"(&{namelist}\b)(.*?)(\n\s*/)", txt, flags=re.S | re.I)
    if not m:
        raise KeyError(f"namelist &{namelist} not found in {path}")
    body = m.group(2)
    for k, v in assignments:
        key = re.escape(k)
        pat = rf"(?im)^([ \t]*)({key})[ \t]*=[ \t]*[^!\n]*?([ \t]*)(?=!|$)"
        if re.search(pat, body):
            body = re.sub(pat, lambda mm: f"{mm.group(1)}{k} = {v}{mm.group(3) or ''}", body, count=1)
        else:
            body = body.rstrip() + f"\n    {k} = {v}  ! set by mesa.py"
    new = txt[:m.start(2)] + body + txt[m.end(2):]
    Path(path).write_text(new)


def cmd_set(a):
    pairs = []
    for s in a.assign:
        k, _, v = s.partition("=")
        if not v:
            raise SystemExit(f"bad assignment {s!r}; use key=value")
        pairs.append((k.strip(), v.strip()))
    set_inlist(a.file, a.namelist, pairs)
    for k, v in pairs:
        print(f"&{a.namelist}: {k} = {v}")
    return 0


def rate_table(T9, rate, n=2000, T8min=0.01, T8max=100.0, below="zero", above="error"):
    """Resample a rate table onto a dense T8 grid for MESA, interpolating in (ln T, ln rate).
    MESA interpolates its tables piecewise-monotonically in *linear* rate vs T8, so a coarse
    table of a steep rate would be mis-interpolated; a dense log-resampled grid avoids that."""
    T9, rate = np.asarray(T9, float), np.asarray(rate, float)
    T8 = np.geomspace(T8min, T8max, n)
    x = np.log(T8 / 10)
    lo, hi = np.log(T9[0]), np.log(T9[-1])
    out = np.exp(np.interp(x, np.log(T9), np.log(np.maximum(rate, 1e-300))))
    if np.any(x < lo - 1e-12):
        if below == "zero":
            out[x < lo - 1e-12] = 0.0
        elif below == "error":
            raise ValueError(f"table starts at T9 = {T9[0]:g} > T8min/10 = {T8min / 10:g}")
    if np.any(x > hi + 1e-12):
        if above == "error":
            raise ValueError(f"table ends at T9 = {T9[-1]:g} < T8max/10 = {T8max / 10:g}; "
                             "extend it or lower --T8max (and say what MESA does above it)")
        if above == "clamp":
            pass  # np.interp already holds the end value
    return T8, out


def cmd_rate_table(a):
    with open(a.table, newline="") as f:
        rows = list(csv.DictReader(f))
    T9 = np.array([float(r["T9"]) for r in rows])
    val = np.array([float(r["rate"]) for r in rows])
    T8max = a.T8max if a.T8max else min(100.0, 10 * T9[-1])
    T8, out = rate_table(T9, val, a.n, a.T8min, T8max, a.below, a.above)
    with open(a.out, "w") as f:
        f.write(f"# {a.reaction}  N_A<sigma v> (cm^3 mol^-1 s^-1), bare (MESA screens)\n")
        f.write(f"# from {a.table}; resampled in (ln T, ln rate) to {a.n} points by mesa.py\n")
        f.write(f"# T9 range of the source table: {T9[0]:g} - {T9[-1]:g}; below: {a.below}\n")
        f.write("# T8            RATE\n")
        f.write(f"{len(T8)}\n")
        for t, v in zip(T8, out):
            f.write(f"{t:.8e} {v:.8e}\n")
    print(f"wrote {a.out}: {len(T8)} points, T8 {T8[0]:g}-{T8[-1]:g}")
    print("use in &star_job:\n"
          f"    num_special_rate_factors = 1\n"
          f"    reaction_for_special_factor(1) = '{a.reaction}'\n"
          f"    special_rate_factor(1) = 1\n"
          f"    filename_of_special_rate(1) = '{Path(a.out).name}'\n"
          "    rates_cache_dir = './rates_cache'   ! never reuse a cache built with another rate")
    return 0


def cmd_trajectory(a):
    h, names, data = read(a.file)
    data = history_rows(names, data)
    age = col(names, data, "star_age")
    if a.center:
        T = 10 ** col(names, data, "log_center_T")
        rho = 10 ** col(names, data, "log_center_Rho")
    else:
        raise SystemExit("only --center from history is implemented; for a mass shell extract "
                         "profiles (see references/trajectories.md)")
    sel = np.ones(len(age), bool)
    if a.from_age is not None:
        sel &= age >= a.from_age
    if a.to_age is not None:
        sel &= age <= a.to_age
    t = (age[sel] - age[sel][0]) * YEAR_S
    keep = np.concatenate([[True], np.diff(t) > 0])
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_s", "T_K", "rho_cgs"])
        for x in zip(t[keep], T[sel][keep], rho[sel][keep]):
            w.writerow([f"{v:.10e}" for v in x])
    print(f"wrote {a.out}: {keep.sum()} points from star_age {age[sel][0]:.6g} to {age[sel][-1]:.6g} yr "
          f"(time_s counted from the first point)")
    return 0


def composition(path, mass):
    """Mass fractions at mass coordinate m (Msun) from a profile with isotope columns."""
    h, names, data = read(path)
    m = col(names, data, "mass")
    k = int(np.argmin(np.abs(m - mass)))
    X = {}
    for i, n in enumerate(names):
        if re.fullmatch(r"(neut|prot|[a-z]{1,2}\d{1,3})", n):
            X[MESA_TO_PYNA.get(n, n)] = float(data[k, i])
    return X, float(m[k])


def cmd_composition(a):
    X, mk = composition(a.file, a.mass)
    s = sum(X.values())
    print(f"zone at m = {mk:.6g} Msun: {len(X)} isotopes, sum X = {s:.8f}")
    if abs(s - 1) > 1e-3:
        print("WARNING profile does not list all isotopes (add them to profile_columns.list)")
    if a.out:
        Path(a.out).write_text(json.dumps({"X": X, "mass_Msun": mk, "source": str(a.file)}, indent=1))
    else:
        for k, v in sorted(X.items(), key=lambda kv: -kv[1])[:15]:
            print(f"  {k:6s} {v:.6e}")
    return 0


def neutrino_fluxes(path):
    """Fluxes at 1 AU (cm^-2 s^-1) from per-cell screened reaction rates (reactions/s)."""
    h, names, data = read(path)
    out, missing = {}, []
    for src, rx in NEUTRINO_SOURCES.items():
        cand = [n for n in names if n.endswith(rx) and ("screened" in n or n == rx)]
        if not cand:
            missing.append(src)
            continue
        total = float(np.sum(col(names, data, cand[0])))
        out[src] = total / (4 * np.pi * AU_CM ** 2)
    return out, missing, h


def cmd_neutrinos(a):
    flux, missing, h = neutrino_fluxes(a.file)
    print(f"model {h.get('model_number')}, age {h.get('star_age', float('nan')):.5g} yr")
    for k, v in flux.items():
        print(f"  {k:4s} {v:.4e} cm^-2 s^-1")
    if missing:
        print(f"missing (not in profile or not in the net): {missing}. Use a net with explicit "
              "pp and CNO decays (pp_and_cno_extras.net) and add_screened_rates to profile_columns.list")
    if a.json:
        Path(a.json).write_text(json.dumps({"fluxes_cm2_s": flux, "missing": missing,
                                            "profile": str(a.file)}, indent=1))
    return 0 if flux else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("columns")
    s.add_argument("file")
    s = sub.add_parser("final")
    s.add_argument("file")
    s.add_argument("columns", nargs="+")
    s = sub.add_parser("compare")
    s.add_argument("a")
    s.add_argument("b")
    s.add_argument("columns", nargs="+")
    s = sub.add_parser("check-run")
    s.add_argument("dir")
    s.add_argument("--log", default="rn.log")
    s.add_argument("--done", help="regex printed by cases that stop from run_star_extras")
    s.add_argument("--allow", nargs="*", help="termination codes that are intentional stops here")
    s = sub.add_parser("set")
    s.add_argument("file")
    s.add_argument("namelist")
    s.add_argument("assign", nargs="+")
    s = sub.add_parser("rate-table")
    s.add_argument("table")
    s.add_argument("--out", required=True)
    s.add_argument("--reaction", required=True, help="MESA reaction name, e.g. r_mg25_pg_al26")
    s.add_argument("--n", type=int, default=2000)
    s.add_argument("--T8min", type=float, default=0.01)
    s.add_argument("--T8max", type=float)
    s.add_argument("--below", choices=["zero", "clamp", "error"], default="zero")
    s.add_argument("--above", choices=["clamp", "error"], default="error")
    s = sub.add_parser("trajectory")
    s.add_argument("file")
    s.add_argument("--center", action="store_true")
    s.add_argument("--from-age", type=float)
    s.add_argument("--to-age", type=float)
    s.add_argument("--out", required=True)
    s = sub.add_parser("composition")
    s.add_argument("file")
    s.add_argument("--mass", type=float, required=True)
    s.add_argument("--out")
    s = sub.add_parser("neutrinos")
    s.add_argument("file")
    s.add_argument("--json")
    a = ap.parse_args(argv)
    return {"columns": cmd_columns, "final": cmd_final, "compare": cmd_compare,
            "check-run": cmd_check_run, "set": cmd_set, "rate-table": cmd_rate_table,
            "trajectory": cmd_trajectory, "composition": cmd_composition,
            "neutrinos": cmd_neutrinos}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
