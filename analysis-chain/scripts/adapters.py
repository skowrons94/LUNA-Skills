#!/usr/bin/env python3
"""Convert one stage's output into the next stage's input, with units, frame and correlations explicit.

  efficiency-at   RESULT.json E_keV [E_keV ...] [--out eff.csv]
      Evaluate an efficiency-analysis fit at the line energies, with the relative standard
      uncertainty and the correlation matrix between energies. The same curve enters every run,
      so its uncertainty is a shared systematic, not an independent per-run error.
  yields-to-excitation  yields.csv OUT.csv [--match COLUMN=VALUE ...] [--error stat|stat+independent]
      yield-analysis table -> target-analysis excitation curve (energy_lab_keV, yield, error).
  to-azure  IN.csv OUT.dat --energy-col C --energy-unit keV|MeV --frame lab|cm --value-col C
            --value-kind sigma|sfactor --value-unit U --error-col C [--angle DEG | --angle-col C]
            [--z1 Z --z2 Z --m1 AMU --m2 AMU]
      Table -> AZURE2 data segment (E_lab MeV, angle deg, cross section b, uncertainty b).
      Centre-of-mass energies and S factors need the masses (and charges) for the conversion;
      differential data in the centre of mass are refused (angle conversion is not done here).

Every output gets a provenance sidecar (OUT.prov.json). Standard library only.
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import provenance  # noqa: E402

ALPHA = 7.2973525693e-3
AMU_KEV = 931494.10242
XS_TO_B = {"b": 1.0, "mb": 1e-3, "ub": 1e-6, "nb": 1e-9, "pb": 1e-12, "cm2": 1e24}
S_TO_KEVB = {"keVb": 1.0, "MeVb": 1e3, "eVb": 1e-3}


def two_pi_eta(z1, z2, mu_amu, e_cm_kev):
    """Sommerfeld exponent 2*pi*eta for centre-of-mass energy in keV."""
    return 2 * math.pi * z1 * z2 * ALPHA * math.sqrt(mu_amu * AMU_KEV / (2 * e_cm_kev))


def efficiency_at(a):
    d = json.loads(Path(a.result).read_text())
    if d.get("quantity") != "full_energy_peak":
        sys.exit(f"quantity is {d.get('quantity')!r}; yields need the full-energy-peak efficiency")
    c, cov, e0 = d["coefficients"], d["covariance"], d["reference_energy_keV"]
    lo, hi = d["valid_energy_keV"]
    grads, rows = [], []
    for e in a.energies:
        x = math.log(e / e0)
        g = [x ** i for i in range(len(c))]
        ln_eff = sum(ci * gi for ci, gi in zip(c, g))
        var = sum(g[i] * cov[i][j] * g[j] for i in range(len(c)) for j in range(len(c)))
        grads.append(g)
        warn = "" if lo <= e <= hi else f"outside calibrated range [{lo:g}, {hi:g}] keV: extrapolation"
        rows.append({"energy_keV": e, "efficiency": math.exp(ln_eff), "rel_sigma": math.sqrt(var),
                     "warning": warn})
    n = len(rows)
    corr = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            cij = sum(grads[i][k] * cov[k][l] * grads[j][l] for k in range(len(c)) for l in range(len(c)))
            corr[i][j] = cij / (rows[i]["rel_sigma"] * rows[j]["rel_sigma"]) if rows[i]["rel_sigma"] * rows[j]["rel_sigma"] else 0.0
    for r in rows:
        print(f"E = {r['energy_keV']:9.2f} keV  eff = {r['efficiency']:.5g}  rel sigma = {r['rel_sigma']:.4f}  {r['warning']}")
    if n > 1:
        print("correlation between energies:")
        for line in corr:
            print("  " + " ".join(f"{v:6.3f}" for v in line))
    print("Use: efficiency -> each run's 'efficiency'; rel sigma -> shared_systematics "
          "(fully correlated over runs at the same energy; use the correlation above across energies).")
    if a.out:
        out = Path(a.out)
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        (out.with_suffix(".corr.json")).write_text(json.dumps({"energies_keV": a.energies, "correlation": corr}, indent=2))
        provenance.record(out, [a.result], cmd=" ".join(sys.argv), skill="efficiency-analysis",
                          note="curve evaluated at line energies")
    return rows, corr


def yields_to_excitation(a):
    with open(a.yields, newline="") as f:
        rows = list(csv.DictReader(f))
    for m in a.match or []:
        k, _, v = m.partition("=")
        rows = [r for r in rows if r.get(k) == v]
    if not rows:
        sys.exit("no rows left after --match")
    energies = [float(r["energy_lab_keV"]) for r in rows]
    if len(set(energies)) != len(energies):
        sys.exit("duplicate energies: select one detector/transition with --match COLUMN=VALUE")
    out_rows = []
    for r in sorted(rows, key=lambda r: float(r["energy_lab_keV"])):
        err = float(r["stat_error"])
        if a.error == "stat+independent":
            err = math.hypot(err, float(r["independent_normalization_error"] or 0))
        out_rows.append({"energy_lab_keV": r["energy_lab_keV"], "yield": r["yield_per_ion"], "error": err})
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["energy_lab_keV", "yield", "error"])
        w.writeheader()
        w.writerows(out_rows)
    provenance.record(Path(a.out), [a.yields], cmd=" ".join(sys.argv), skill="yield-analysis",
                      note=f"error column = {a.error}; shared systematics are NOT included and must be "
                           f"treated as a common normalisation downstream")
    print(f"wrote {len(out_rows)} points to {a.out} (error = {a.error}; shared systematics excluded)")
    return out_rows


def to_azure(a):
    with open(a.input, newline="") as f:
        rows = list(csv.DictReader(f))
    need_masses = a.frame == "cm" or a.value_kind == "sfactor"
    if need_masses and None in (a.m1, a.m2):
        sys.exit("centre-of-mass energies and S factors need --m1 and --m2 (amu)")
    if a.value_kind == "sfactor" and None in (a.z1, a.z2):
        sys.exit("S factor conversion needs --z1 and --z2")
    if a.frame == "cm" and a.angle_col:
        sys.exit("differential data in the centre of mass: convert angles and cross sections to the lab first")
    if a.angle is None and not a.angle_col:
        sys.exit("give --angle (dummy for angle-integrated data) or --angle-col")
    escale = {"keV": 1.0, "MeV": 1e3}[a.energy_unit]
    lines = []
    for r in rows:
        e = float(r[a.energy_col]) * escale  # keV, in the given frame
        if a.frame == "cm":
            e_cm, e_lab = e, e * (a.m1 + a.m2) / a.m2
        else:
            e_lab = e
            e_cm = e * a.m2 / (a.m1 + a.m2) if need_masses else None
        v, dv = float(r[a.value_col]), float(r[a.error_col])
        if a.value_kind == "sfactor":
            k = S_TO_KEVB[a.value_unit] / e_cm * math.exp(-two_pi_eta(a.z1, a.z2, a.m1 * a.m2 / (a.m1 + a.m2), e_cm))
        else:
            k = XS_TO_B[a.value_unit]
        ang = float(r[a.angle_col]) if a.angle_col else a.angle
        lines.append(f"{e_lab / 1e3:.8g} {ang:.6g} {v * k:.8g} {dv * k:.8g}")
    Path(a.out).write_text("\n".join(lines) + "\n")
    provenance.record(Path(a.out), [a.input], cmd=" ".join(sys.argv), skill="azure2",
                      note=f"from {a.frame}-frame {a.energy_unit}, {a.value_kind} in {a.value_unit}; "
                           f"written as lab MeV, deg, b")
    print(f"wrote {len(lines)} lines to {a.out} (lab MeV, deg, b)")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("efficiency-at")
    p.add_argument("result")
    p.add_argument("energies", type=float, nargs="+")
    p.add_argument("--out")
    p = sub.add_parser("yields-to-excitation")
    p.add_argument("yields")
    p.add_argument("out")
    p.add_argument("--match", nargs="*")
    p.add_argument("--error", choices=["stat", "stat+independent"], default="stat")
    p = sub.add_parser("to-azure")
    p.add_argument("input")
    p.add_argument("out")
    p.add_argument("--energy-col", required=True)
    p.add_argument("--energy-unit", choices=["keV", "MeV"], required=True)
    p.add_argument("--frame", choices=["lab", "cm"], required=True)
    p.add_argument("--value-col", required=True)
    p.add_argument("--value-kind", choices=["sigma", "sfactor"], required=True)
    p.add_argument("--value-unit", required=True, help=f"sigma: {list(XS_TO_B)}; sfactor: {list(S_TO_KEVB)}")
    p.add_argument("--error-col", required=True)
    p.add_argument("--angle", type=float)
    p.add_argument("--angle-col")
    for k in ("z1", "z2"):
        p.add_argument(f"--{k}", type=int)
    for k in ("m1", "m2"):
        p.add_argument(f"--{k}", type=float, help="projectile (m1) and target (m2) mass in amu")
    a = ap.parse_args(argv)
    if a.cmd == "to-azure":
        table = XS_TO_B if a.value_kind == "sigma" else S_TO_KEVB
        if a.value_unit not in table:
            sys.exit(f"--value-unit must be one of {list(table)} for {a.value_kind}")
    return {"efficiency-at": efficiency_at, "yields-to-excitation": yields_to_excitation,
            "to-azure": to_azure}[a.cmd](a)


if __name__ == "__main__":
    main()
