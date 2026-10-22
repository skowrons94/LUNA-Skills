#!/usr/bin/env python3
"""B23 / SF-III standard solar models (Herrera & Serenelli, Zenodo 10822316): fluxes, linear
variations, uncertainty budgets, and comparison with a MESA model.

  python3 ssm.py fluxes  --model GS98
  python3 ssm.py vary    --model GS98 S114=1.084 C=1.10            (factors on the inputs)
  python3 ssm.py budget  --model GS98 S114=0.084 S34=0.05 C=0.10    (1-sigma fractional inputs)
  python3 ssm.py budget  --model GS98 S114=0.084 --what-if S114=0.03 (what a measurement buys)
  python3 ssm.py compare --model GS98 --profile RUN/final.profile [--neutrinos RUN/neutrinos.json]

Models: GS98, AGSS09, C11, AAG21, MB22m, MB22p. Data directory: --data, else
$NUCLEAR_DATA_DIR/SolarModels_B23/extracted. Variations use the logarithmic partial derivatives
(PLD/pwrlaws_SF3_*.dat): new = model * prod_j factor_j ** alpha_ij, valid for small changes
(the package's own SSM-variations.R does the same in dex). Inputs: S11 S33 S34 Se7 S17 Shep
S114 S116 age diff lumi opacA opacB C N O Ne Mg Si S Ar Fe. Outputs: pp pep hep be7 b8 n13 o15
f17 fluxes, ys (surface He), rcz (convective-zone base, R_sun).
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

SOURCES = ["pp", "pep", "hep", "7Be", "8B", "13N", "15O", "17F"]
PLD_ROWS = ["pp", "pep", "hep", "be7", "b8", "n13", "o15", "f17", "ys", "rcz"]
ROW_TO_SOURCE = dict(zip(PLD_ROWS[:8], SOURCES))
# surface He and R_cz of each model, from SSM-variations.R v1.2 (the flux files hold fluxes only)
YS_RCZ = {"AAG21": (0.23467429, 0.7188408371), "AGSS09": (0.23200218, 0.7221316935),
          "C11": (0.23683168, 0.7154190607), "GS98": (0.24293369, 0.7111655734),
          "MB22m": (0.24431846, 0.7113853858), "MB22p": (0.24369318, 0.7116922929)}


def data_dir(arg):
    d = Path(arg) if arg else Path(os.environ.get("NUCLEAR_DATA_DIR", "")) / "SolarModels_B23" / "extracted"
    if not (d / "SolarModels").is_dir():
        raise SystemExit(f"B23 data not found in {d}; download Zenodo 10822316 (see references/solar.md)")
    return d


def fluxes(d, model):
    """Fluxes (cm^-2 s^-1), fractional errors and correlation matrix of one model."""
    lines = (d / "SolarModels" / f"fluxes_SF3_{model}.dat").read_text().splitlines()
    flux = err = None
    corr = []
    for ln in lines:
        p = ln.split()
        if p and p[-1] == "Flux":
            flux = np.array([float(x) for x in p[:-1]])
        elif p and p[-1] == "Fract.Err":
            err = np.array([float(x) for x in p[:-1]])
        elif len(p) == 9 and p[-1] in SOURCES:
            corr.append([float(x) for x in p[:-1]])
    if flux is None or err is None or len(corr) != 8:
        raise ValueError(f"unexpected format of fluxes_SF3_{model}.dat")
    return dict(zip(SOURCES, flux)), dict(zip(SOURCES, err)), np.array(corr)


def pld(d, model):
    key = "mb22" if model.startswith("MB22") else model.lower()
    lines = (d / "PLD" / f"pwrlaws_SF3_{key}.dat").read_text().splitlines()
    cols = [ln for ln in lines if ln.startswith("#") and "S11" in ln][0].lstrip("#").split()
    M = {}
    for ln in lines:
        p = ln.split()
        if p and not ln.startswith("#") and p[-1] in PLD_ROWS:
            M[p[-1]] = dict(zip(cols, [float(x) for x in p[:-1]]))
    return cols, M


def structure(d, model):
    path = d / "SolarModels" / f"struct+nu_SF3_{model}.dat"
    names = path.read_text().splitlines()[0].strip().lstrip("#").split()  # header is ' #  R_sun ...'
    return names, np.loadtxt(path, comments="#")


def reference(d, model):
    """Reference values of the 10 PLD outputs. Taken from the package's SSM-variations.R, which
    holds more digits than the flux files (e.g. 8B 5024799 vs 5.025e6), so that variations
    reproduce the package's own routine; falls back to the flux files plus YS_RCZ."""
    import re
    r_file = d / "SSM-variations.R"
    if r_file.exists():
        arrays = {}
        for ln in r_file.read_text().splitlines():
            m = re.match(r"\s*SF3_(\w+)\s*<-\s*c\((.*)\)", ln)
            if m:
                arrays[m.group(1)] = [float(x) for x in m.group(2).split(",")]
        # the script names the meteoritic-scale AAG21 and AGSS09 arrays AAG21m, AGSS09m
        key = model if model in arrays else model + "m"
        if key in arrays:
            return dict(zip(PLD_ROWS, arrays[key]))
    f, _, _ = fluxes(d, model)
    ys, rcz = YS_RCZ[model]
    out = {r: f[ROW_TO_SOURCE[r]] for r in PLD_ROWS[:8]}
    out.update(ys=ys, rcz=rcz)
    return out


def parse_pairs(items, cols):
    out = {}
    for s in items:
        k, _, v = s.partition("=")
        match = [c for c in cols if c.lower() == k.lower()]
        if not match or not v:
            raise SystemExit(f"bad input {s!r}; inputs: {' '.join(cols)}")
        out[match[0]] = float(v)
    return out


def cmd_fluxes(a):
    d = data_dir(a.data)
    f, e, c = fluxes(d, a.model)
    print(f"B23/SF-III {a.model}: flux (cm^-2 s^-1) and fractional 1-sigma error")
    for s in SOURCES:
        print(f"  {s:4s} {f[s]:.4e}  ±{e[s] * 100:.1f} %")
    print("correlation 13N-15O {:+.3f}, 7Be-8B {:+.3f}".format(c[5, 6], c[3, 4]))
    return 0


def cmd_vary(a):
    d = data_dir(a.data)
    cols, M = pld(d, a.model)
    fac = parse_pairs(a.factors, cols)
    ref = reference(d, a.model)
    print(f"{a.model}, inputs x {fac}")
    print(f"{'output':6s} {'reference':>12s} {'varied':>12s} {'ratio':>8s}")
    res = {}
    for r in PLD_ROWS:
        ratio = float(np.prod([fac[j] ** M[r][j] for j in fac]))
        res[r] = ref[r] * ratio
        print(f"{r:6s} {ref[r]:12.4e} {res[r]:12.4e} {ratio:8.4f}")
    if a.json:
        Path(a.json).write_text(json.dumps({"model": a.model, "factors": fac, "reference": ref,
                                            "varied": res}, indent=1))
    return 0


def budget(M, sig, rows=PLD_ROWS[:8]):
    """Fractional 1-sigma contribution of each input (independent inputs, linear)."""
    return {r: {j: abs(M[r][j]) * s for j, s in sig.items()} for r in rows}


def cmd_budget(a):
    d = data_dir(a.data)
    cols, M = pld(d, a.model)
    sig = parse_pairs(a.sigmas, cols)
    B = budget(M, sig)
    alt = None
    if a.what_if:
        sig2 = dict(sig, **parse_pairs(a.what_if, cols))
        alt = budget(M, sig2)
    print(f"{a.model}: fractional 1-sigma flux uncertainty from the given inputs only "
          "(independent, linear); the package's total errors include all inputs")
    hdr = " ".join(f"{j:>7s}" for j in sig)
    print(f"{'flux':5s} {hdr} {'total':>7s}" + ("  what-if" if alt else ""))
    for r in PLD_ROWS[:8]:
        tot = np.sqrt(sum(v ** 2 for v in B[r].values()))
        line = f"{ROW_TO_SOURCE[r]:5s} " + " ".join(f"{B[r][j] * 100:6.2f}%" for j in sig) + f" {tot * 100:6.2f}%"
        if alt:
            line += f"  {np.sqrt(sum(v ** 2 for v in alt[r].values())) * 100:6.2f}%"
        print(line)
    return 0


def cmd_compare(a):
    sys.path.insert(0, str(Path(__file__).parent))
    import mesa
    d = data_dir(a.data)
    names, S = structure(d, a.model)
    sc = dict(zip(names, S[0]))
    h, n, P = mesa.read(a.profile)
    k = int(np.argmin(P[:, n.index("mass")]))  # centre
    pairs = [("logT", "logT"), ("logRho", "logRho"), ("H1", "h1"), ("He4", "he4"), ("He3", "he3"),
             ("C12", "c12"), ("C13", "c13"), ("N14", "n14"), ("O16", "o16")]
    print(f"centre: B23 {a.model} vs MESA ({a.profile})")
    for s_name, m_name in pairs:
        if s_name in sc and m_name in n:
            x, y = sc[s_name], P[k, n.index(m_name)]
            diff = f"{y - x:+.4f}" if s_name.startswith("log") else f"{y / x:.3f}x" if x else ""
            print(f"  {s_name:6s} {x:12.5e} {y:12.5e}  {diff}")
    if a.neutrinos:
        f, e, _ = fluxes(d, a.model)
        mf = json.loads(Path(a.neutrinos).read_text())["fluxes_cm2_s"]
        print("fluxes: MESA / B23 (B23 1-sigma)")
        for s in SOURCES:
            if s in mf:
                r = mf[s] / f[s]
                print(f"  {s:4s} {r:6.3f}  ({(r - 1) / e[s]:+.1f} sigma)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("fluxes", "vary", "budget", "compare"):
        s = sub.add_parser(name)
        s.add_argument("--model", default="GS98", choices=list(YS_RCZ))
        if name == "vary":
            s.add_argument("factors", nargs="+")
            s.add_argument("--json")
        if name == "budget":
            s.add_argument("sigmas", nargs="+")
            s.add_argument("--what-if", nargs="+")
        if name == "compare":
            s.add_argument("--profile", required=True)
            s.add_argument("--neutrinos")
    a = ap.parse_args(argv)
    return {"fluxes": cmd_fluxes, "vary": cmd_vary, "budget": cmd_budget, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
