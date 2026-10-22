#!/usr/bin/env python3
"""Rate tools: compare sources, convert AZURE2 output, fit the REACLIB 7-parameter form.

  python3 rates.py compare "mg25(p,g)al26" [--table T.csv] [--starlib FILE] [--T9 0.03 0.05 0.1]
  python3 rates.py from-azure reactionrates.out --out T.csv [--fu-from STARLIB_FILE --rate NAME]
  python3 rates.py from-sfactor --rate "n14(p,g)o15" --S0 1.68e-3 --S1 -1.7e-3 --T9 0.003 0.06 \
                       --source "SF III Table I" --out T.csv     bare non-resonant rate from S(E)
  python3 rates.py fit T.csv --rate "c12(p,g)n13" --forms nonresonant resonance --out fit.json
                       [--reaclib-out fit.reaclib] [--tol 0.03]

Tables follow the rate-table contract: CSV with T9 (GK), rate (N_A<sigma v>, cm^3 mol^-1 s^-1;
s^-1 for decays) and optionally fu (lognormal factor uncertainty). REACLIB form:
ln(rate) = a0 + a1/T9 + a2 T9^(-1/3) + a3 T9^(1/3) + a4 T9 + a5 T9^(5/3) + a6 ln T9, summed over sets.
Set forms: 'full' (7 free), 'nonresonant' (a1 = 0), 'resonance' (a0, a1 free, a6 = -3/2, others 0).
"""

import argparse
import csv
import json
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).parent))
import build  # noqa: E402
import netlib as nl  # noqa: E402

FORMS = {
    "full": ([0, 1, 2, 3, 4, 5, 6], {}),
    "nonresonant": ([0, 2, 3, 4, 5, 6], {1: 0.0}),
    "resonance": ([0, 1], {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: -1.5}),
}


def basis(T9):
    T9 = np.asarray(T9, float)
    return np.column_stack([np.ones_like(T9), 1 / T9, T9 ** (-1 / 3), T9 ** (1 / 3), T9,
                            T9 ** (5 / 3), np.log(T9)])


def eval_sets(sets, T9):
    B = basis(T9)
    with np.errstate(over="ignore"):
        return np.sum([np.exp(np.minimum(B @ np.asarray(a), 700)) for a in sets], axis=0)


def _unpack(x, forms):
    sets, k = [], 0
    for f in forms:
        free, fixed = FORMS[f]
        a = np.zeros(7)
        for j, v in fixed.items():
            a[j] = v
        a[free] = x[k:k + len(free)]
        k += len(free)
        sets.append(a)
    return sets


def fit(T9, rate, forms, seed=0, restarts=30):
    """Least squares in ln(rate). Returns (sets, max relative deviation on a dense grid)."""
    T9, rate = np.asarray(T9, float), np.asarray(rate, float)
    good = rate > 0
    T9, rate = T9[good], rate[good]
    y = np.log(rate)
    B = basis(T9)
    rng = np.random.default_rng(seed)
    # dense check grid: ln-interpolation of the table between its points
    Td = np.exp(np.linspace(np.log(T9[0]), np.log(T9[-1]), 400))
    yd = np.interp(np.log(Td), np.log(T9), y)

    def resid(x):
        return np.log(np.maximum(eval_sets(_unpack(x, forms), T9), 1e-300)) - y

    best = None
    for trial in range(restarts if len(forms) > 1 else 1):
        x0 = []
        for k, f in enumerate(forms):
            free, fixed = FORMS[f]
            if k == 0:
                yt = y - (np.log(len(forms)) if len(forms) > 1 else 0) - sum(B[:, j] * v for j, v in fixed.items())
                coef, *_ = np.linalg.lstsq(B[:, free], yt, rcond=None)
                x0 += list(coef)
            else:
                # resonance-like start: E_r ~ uniform in ln over the table range
                a1 = -11.605 * np.exp(rng.uniform(np.log(0.01), np.log(5.0))) * (1 if f == "resonance" else 0.3)
                a0 = np.max(y + -a1 / T9 + 1.5 * np.log(T9)) - rng.uniform(0, 8)
                start = np.zeros(len(free))
                start[0] = a0
                if 1 in free:
                    start[free.index(1)] = a1
                x0 += list(start)
        try:
            sol = least_squares(resid, np.array(x0), method="lm" if len(x0) <= len(y) else "trf",
                                max_nfev=20000)
        except Exception:  # noqa: BLE001  a failed restart is skipped
            continue
        sets = _unpack(sol.x, forms)
        dev = np.max(np.abs(eval_sets(sets, Td) / np.exp(yd) - 1))
        if best is None or dev < best[1]:
            best = (sets, dev, float(np.max(np.abs(np.exp(resid(sol.x)) - 1))))
    if best is None:
        raise RuntimeError("all fits failed")
    return best


ALPHA = 1 / 137.035999084
AMU_MEV = 931.49410242
KB_MEV = 8.617333262e-11
C_CMS = 2.99792458e10
NA = 6.02214076e23


def sfactor_rate(T9, S, Z1, Z2, mu_mev):
    """Bare non-resonant N_A<sigma v> (cm^3 mol^-1 s^-1) from S(E) in MeV b (E in MeV, c.m.),
    by numerical integration of the Maxwell-Boltzmann average. No identical-particle factor."""
    kT = KB_MEV * T9 * 1e9
    E0 = (np.pi * Z1 * Z2 * ALPHA * kT) ** (2 / 3) * (mu_mev / 2) ** (1 / 3)
    from scipy.integrate import quad

    def f(E):
        return S(E) * np.exp(-2 * np.pi * Z1 * Z2 * ALPHA * np.sqrt(mu_mev / (2 * E)) - E / kT)

    tau = 3 * E0 / kT
    width = 4 / np.sqrt(3) * np.sqrt(E0 * kT)
    lo, hi = max(E0 - 8 * width, E0 / 50), E0 + 12 * width
    val, _ = quad(f, lo, hi, points=[E0], limit=400, epsrel=1e-10)
    return NA * np.sqrt(8 / (np.pi * mu_mev)) * kT ** -1.5 * C_CMS * val * 1e-24, E0, tau


def from_sfactor(a):
    import pynucastro as pyna
    r = pyna.ReacLibLibrary().get_rate_by_name(a.rate)
    if len(r.reactants) != 2:
        raise SystemExit("from-sfactor needs a two-body entrance channel")
    n1, n2 = r.reactants
    # bare-nucleus masses (MeV): the Gamow exponent tau ~ mu^(1/3) is 60-150 at T9 = 0.016-0.001,
    # so 0.1 % in mu moves the rate by 2-5 %; mass numbers or atomic masses are not good enough
    me = 0.51099895  # pynucastro's Nucleus.mass is the atomic mass: remove the electrons
    m1, m2 = n1.mass - n1.Z * me, n2.mass - n2.Z * me
    mu = m1 * m2 / (m1 + m2)
    S = lambda E: a.S0 + a.S1 * E + 0.5 * a.S2 * E * E  # noqa: E731  Eq. (4) of SF III
    T9 = np.geomspace(a.T9[0], a.T9[1], a.n)
    rows = []
    for t in T9:
        v, E0, _ = sfactor_rate(t, S, n1.Z, n2.Z, mu)
        rows.append((t, v, E0))
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["T9", "rate"])
        for t, v, _ in rows:
            w.writerow([f"{t:.8g}", f"{v:.8e}"])
    Path(a.out + ".meta.json").write_text(json.dumps({
        "rate": a.rate, "S0_MeVb": a.S0, "S1_b": a.S1, "S2_b_per_MeV": a.S2, "source": a.source,
        "kind": "bare, non-resonant, S(E) = S0 + S1 E + S2 E^2 / 2 (E c.m. in MeV)",
        "valid_T9": [float(T9[0]), float(T9[-1])], "E0_keV_range": [rows[0][2] * 1e3, rows[-1][2] * 1e3],
        "note": "valid only where the expansion describes S(E) over the Gamow window; resonances are not included"},
        indent=1))
    print(f"wrote {a.out}: {a.n} points, T9 {T9[0]:g}-{T9[-1]:g}, Gamow peak {rows[0][2] * 1e3:.1f}-{rows[-1][2] * 1e3:.1f} keV")
    for t in (T9[0], T9[len(T9) // 2], T9[-1]):
        v = [x for x in rows if x[0] == t][0][1]
        print(f"  T9 {t:.4g}: rate {v:.4e}, REACLIB {r.label} {r.eval(t * 1e9):.4e}, ratio {v / r.eval(t * 1e9):.4f}")
    return 0


def compare(a):
    import pynucastro as pyna
    T9s = a.T9 or [0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0]
    rl = pyna.ReacLibLibrary()
    r = rl.get_rate_by_name(a.rate)
    cols = {"REACLIB " + r.label: [r.eval(t * 1e9) for t in T9s]}
    if a.starlib:
        import starlib
        ents = starlib.read(a.starlib)
        hits = starlib.match(starlib.index(ents), r)
        for h in hits:
            cols[f"STARLIB {h['label']}{h['flag']}"] = list(np.exp(np.interp(
                np.log(T9s), np.log(h["T9"]), np.log(np.maximum(h["rate"], 1e-300)))))
            cols[f"fu {h['label']}"] = list(np.exp(np.interp(np.log(T9s), np.log(h["T9"]),
                                                            np.log(h["fu"]))))
    if a.table:
        T9, val, fu = build.read_rate_table(a.table)
        cols["table"] = [float(np.exp(np.interp(np.log(t), np.log(T9), np.log(np.maximum(val, 1e-300)))))
                         if T9[0] <= t <= T9[-1] else np.nan for t in T9s]
    names = list(cols)
    ref = names[0]
    print(f"{a.rate}: ratios are to {ref}")
    print(f"{'T9':>7s} " + " ".join(f"{n[:16]:>16s}" for n in names))
    for k, t in enumerate(T9s):
        row = []
        for n in names:
            v = cols[n][k]
            row.append(f"{v:16.4e}" if n == ref or n.startswith("fu") else
                       f"{v:10.4e} ({v / cols[ref][k]:.3f})"[:16].rjust(16))
        print(f"{t:7.3f} " + " ".join(row))
    return 0


def from_azure(a):
    T9, val = [], []
    for line in Path(a.file).read_text().splitlines():
        p = line.split()
        if len(p) < 2:
            continue
        try:
            t, v = float(p[0]), float(p[1])
        except ValueError:
            continue  # header
        T9.append(t)
        val.append(v)
    T9, val = np.array(T9), np.array(val)
    if np.any(np.diff(T9) <= 0):
        raise SystemExit("T9 not strictly increasing in AZURE2 output")
    fu = None
    if a.fu_from:
        import starlib
        import pynucastro as pyna
        r = pyna.ReacLibLibrary().get_rate_by_name(a.rate)
        hits = starlib.match(starlib.index(starlib.read(a.fu_from)), r)
        if not hits:
            raise SystemExit(f"no STARLIB entry for {a.rate}")
        h = hits[0]
        fu = np.exp(np.interp(np.log(T9), np.log(h["T9"]), np.log(h["fu"])))
        print(f"fu borrowed from STARLIB {h['label']}: this is NOT the uncertainty of the AZURE2 rate")
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["T9", "rate"] + (["fu"] if fu is not None else []))
        for k in range(len(T9)):
            w.writerow([f"{T9[k]:.6g}", f"{val[k]:.6e}"] + ([f"{fu[k]:.4f}"] if fu is not None else []))
    print(f"wrote {a.out}: {len(T9)} points, T9 {T9[0]:g}-{T9[-1]:g}")
    return 0


def do_fit(a):
    import pynucastro as pyna
    T9, val, _ = build.read_rate_table(a.table)
    sets, dev_dense, dev_pts = fit(T9, val, a.forms, seed=a.seed)
    print(f"forms {a.forms}: max |fit/table - 1| = {dev_pts:.4f} at table points, "
          f"{dev_dense:.4f} on a dense grid (ln-interpolated table)")
    ok = dev_dense <= a.tol
    print("PASS" if ok else f"FAIL: above tolerance {a.tol}; try other forms or more sets")
    r = pyna.ReacLibLibrary().get_rate_by_name(a.rate)
    res = [f == "resonance" for f in a.forms]
    fr = nl.reaclib_rate_from_sets(r.reactants, r.products, sets, label=a.label, resonant=res)
    out = {"rate": a.rate, "forms": a.forms, "sets": [list(map(float, s)) for s in sets],
           "valid_T9": [float(T9[0]), float(T9[-1])], "max_rel_dev_dense": float(dev_dense),
           "max_rel_dev_points": float(dev_pts), "table": str(a.table),
           "note": "valid only inside valid_T9; REACLIB-form fits are unconstrained outside"}
    Path(a.out).write_text(json.dumps(out, indent=1))
    if a.reaclib_out:
        Path(a.reaclib_out).write_text(nl.reaclib_text(fr))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            back = pyna.load_rate(str(Path(a.reaclib_out).resolve()))
        chk = max(abs(back.eval(t * 1e9) / fr.eval(t * 1e9) - 1) for t in T9)
        print(f"wrote {a.reaclib_out} (re-read by pynucastro, max difference {chk:.1e})")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("rate")
    c.add_argument("--table")
    c.add_argument("--starlib")
    c.add_argument("--T9", type=float, nargs="*")
    z = sub.add_parser("from-azure")
    z.add_argument("file")
    z.add_argument("--out", required=True)
    z.add_argument("--fu-from")
    z.add_argument("--rate")
    f = sub.add_parser("fit")
    f.add_argument("table")
    f.add_argument("--rate", required=True)
    f.add_argument("--forms", nargs="+", default=["nonresonant", "full"], choices=sorted(FORMS))
    f.add_argument("--out", required=True)
    f.add_argument("--reaclib-out")
    f.add_argument("--label", default="fit")
    f.add_argument("--tol", type=float, default=0.03)
    f.add_argument("--seed", type=int, default=0)
    s = sub.add_parser("from-sfactor")
    s.add_argument("--rate", required=True)
    s.add_argument("--S0", type=float, required=True, help="S(0) in MeV b")
    s.add_argument("--S1", type=float, default=0.0, help="S'(0) in b")
    s.add_argument("--S2", type=float, default=0.0, help="S''(0) in b/MeV")
    s.add_argument("--T9", type=float, nargs=2, required=True, metavar=("MIN", "MAX"))
    s.add_argument("--n", type=int, default=80)
    s.add_argument("--source", required=True, help="where S0, S1, S2 come from")
    s.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"compare": compare, "from-azure": from_azure, "fit": do_fit,
            "from-sfactor": from_sfactor}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
