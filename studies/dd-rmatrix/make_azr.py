"""Write a 4He R-matrix project (d+d, p+t, n+3He) for AZURE2 from a config.

config keys (defaults in DEFAULT):
  a_dd, a_pt, a_nh      channel radii (fm)
  jpi                   list of (J, parity, [(pair, L, 2S), ...]) groups
  poles                 Ex (MeV) of the background/broad poles placed in every group
  gamma0                starting partial widths (eV)
  emax_cm_keV           data above this are not written

Every (experiment, reaction) becomes one angle-integrated segment with its
normalisation fixed at 1: normalisations, screening and energy uncertainties
are handled in the likelihood (fitter.py), not by AZURE2.
"""
import json
import os
import numpy as np

# nuclear masses (u), separation energies of 4He (MeV)
M = dict(d=2.013553212, p=1.007276467, t=3.015500716, n=1.008664916, h=3.014932247)
SEP = {1: 23.8473, 2: 19.8139, 3: 20.5776}
PAIR = {1: ("d", "d", 1.0, 1.0, 1, 1), 2: ("p", "t", 0.5, 0.5, 1, 1), 3: ("n", "h", 0.5, 0.5, 0, 2)}
EXIT = {"dp": 2, "dn": 3}

# identical spin-1 bosons: l + S even.  Exit pairs: S = 0, 1.
JPI_NOMINAL = [
    (0, +1, [(1, 0, 0), (2, 0, 0), (3, 0, 0)]),                 # 1S0 -> 1S0
    (2, +1, [(1, 0, 4), (2, 2, 0), (2, 2, 2), (3, 2, 0), (3, 2, 2)]),   # 5S2 -> D
    (0, -1, [(1, 1, 2), (2, 1, 2), (3, 1, 2)]),                 # 3P0
    (1, -1, [(1, 1, 2), (2, 1, 0), (2, 1, 2), (3, 1, 0), (3, 1, 2)]),   # 3P1
    (2, -1, [(1, 1, 2), (2, 1, 2), (3, 1, 2)]),                 # 3P2
]
# d-wave entrance additions (variant)
JPI_DWAVE = [
    (2, +1, [(1, 2, 0)]), (1, +1, [(1, 2, 4), (2, 2, 2), (3, 2, 2)]),
    (3, +1, [(1, 2, 4), (2, 2, 2), (3, 2, 2)]),
]

# extrapolation grids (lab MeV; E_cm = E_lab/2): 0.5-60 keV c.m. fine, then to 2 MeV
EXTRAP = []
for ex in (2, 3):
    EXTRAP.append(f"1 1 {ex} 0.001 0.12 0.0005 0 0 0 0")
    EXTRAP.append(f"1 1 {ex} 0.12 4.0 0.005 0 0 0 0")

DEFAULT = dict(a_dd=6.0, a_pt=5.0, a_nh=5.0, jpi="nominal", poles=[30.0],
               gamma0=1.0e6, emax_cm_keV=1500.0, exps=None)


def jpi_groups(name):
    groups = {(J, p): list(ch) for J, p, ch in JPI_NOMINAL}
    if name == "dwave":
        for J, p, ch in JPI_DWAVE:
            groups.setdefault((J, p), [])
            groups[(J, p)] += [c for c in ch if c not in groups[(J, p)]]
    elif name == "s_only":
        groups = {k: v for k, v in groups.items() if k[1] == +1}
    return groups


def level_lines(cfg):
    radii = {1: cfg["a_dd"], 2: cfg["a_pt"], 3: cfg["a_nh"]}
    lines, lid = [], 0
    for (J, par), chans in sorted(jpi_groups(cfg["jpi"]).items()):
        for Ex in cfg["poles"]:
            lid += 1
            for (pair, L, S2) in chans:
                a, b, j1, j2, z1, z2 = PAIR[pair]
                sign = 1 if (lid + pair + L) % 2 == 0 else -1
                g = sign * cfg["gamma0"] * (1.0 if pair == 1 else 0.7)
                lines.append(" ".join(str(x) for x in [
                    J, par, Ex, 0 if cfg.get("free_E") else 1, 1, pair, S2, 2 * L, lid, 1, 0, f"{g:.6g}",
                    j1, 1, j2, 1, 0, M[a], M[b], z1, z2, SEP[1], SEP[pair],
                    0, 0, 0.0, 0, radii[pair], 0, 0, 0]))
            lines.append("")
    return lines


def write_project(cfg, outdir, catalog="data/catalog.json"):
    cfg = {**DEFAULT, **cfg}
    os.makedirs(f"{outdir}/output", exist_ok=True)
    os.makedirs(f"{outdir}/checks", exist_ok=True)
    os.makedirs(f"{outdir}/data", exist_ok=True)
    cat = json.load(open(catalog))
    segs, meta = [], []
    keys = sorted({(p["exp"], p["reac"]) for p in cat["points"]})
    for exp, reac in keys:
        if cfg["exps"] is not None and exp not in cfg["exps"]:
            continue
        P = sorted([p for p in cat["points"] if p["exp"] == exp and p["reac"] == reac
                    and p["E"] <= cfg["emax_cm_keV"]], key=lambda p: p["E"])
        if not P:
            continue
        fn = f"data/{exp}_{reac}.dat"
        with open(f"{outdir}/{fn}", "w") as f:
            for p in P:   # lab MeV, dummy angle, b, b
                f.write(f"{2 * p['E'] / 1e3:.7g} 0 {p['sigma']:.7g} {p['err']:.7g}\n")
        segs.append(f"1 1 {EXIT[reac]} 0 100 0 180 0 1 0 0 0 0 0 {fn} 0 0")
        meta.append(dict(exp=exp, reac=reac, points=P))
    txt = ["<config>", "true #Perform A-Matrix Calculation", "output/ #Output", "checks/ #Checks"]
    txt += ["none #check"] * 8 + ["</config>", "<levels>"] + level_lines(cfg) + ["</levels>"]
    txt += ["<segmentsData>"] + segs + ["</segmentsData>", "<segmentsTest>"] + EXTRAP + ["</segmentsTest>",
            "<targetInt>", "</targetInt>", "<lastRun>", "9997", '"output/param.sav"', '""',
            "0 0", '0 ""', "-1. -1. -1.", "</lastRun>"]
    path = f"{outdir}/dd.azr"
    open(path, "w").write("\n".join(txt) + "\n")
    json.dump({"cfg": cfg, "segments": meta}, open(f"{outdir}/segments.json", "w"))
    return path


if __name__ == "__main__":
    print(write_project({}, "runs/nominal"))
