#!/usr/bin/env python3
"""Get evaluated cross sections from OpenMC HDF5 libraries or raw ENDF-6 files.

Subcommands
  get      pointwise sigma(E) of one reaction -> CSV (E_eV, sigma_b)
  windows  thermal value, resonance integral, 1/E mean, MACS(kT), fission-spectrum average
  compare  the same reaction in several libraries: window values and max/min spread
  info     header of a raw ENDF-6 file: material, sublibrary, MTs, resonance ranges (LRU/LRF)

Sources (choose with --lib or --endf):
  --lib NAME   OpenMC HDF5 library; NAME is a key of LIBRARIES below or a path to a
               cross_sections.xml / directory containing <Nuclide>.h5 files
  --endf FILE  raw ENDF-6 file; MF3 is read as tabulated (no resonance reconstruction:
               add --njoy to process with NJOY at --temp, needs NJOY2016 + OpenMC)

Energies are laboratory energies of the projectile in eV; cross sections in barns.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path

import numpy as np

_trapz = getattr(np, "trapezoid", None) or np.trapz
# Root folder of the local HDF5 libraries, taken from the environment so that no
# machine-specific path lives in the skill: export NUCLEAR_DATA_DIR=/path/to/nuclear-data
ND = Path(os.environ["NUCLEAR_DATA_DIR"]).expanduser() if os.environ.get("NUCLEAR_DATA_DIR") else None


def _under_root(*names: str) -> list[Path]:
    return [ND / n for n in names] if ND else []


# Folder names under NUCLEAR_DATA_DIR (first existing entry wins). Partial subsets are fine.
LIBRARIES = {
    "ENDF/B-VIII.1": _under_root("ENDF-B-VIII.1"),
    "ENDF/B-VIII.0": _under_root("ENDF-B-VIII.0"),
    "JEFF-3.3": _under_root("JEFF-3.3"),
    "JEFF-4.0": _under_root("JEFF-4.0", "JEFF-4.0-subset"),
    "JENDL-5": _under_root("JENDL-5", "JENDL-5-subset"),
    "FENDL-3.2": _under_root("FENDL-3.2"),
}
# nuclide-name aliases in specific OpenMC builds
ALIAS = {("JEFF-3.3", "C12"): "C0"}
# entries of the OpenMC JEFF-3.3 build that are TENDL-2019, not JEFF
TENDL_IN_JEFF33 = {"C13", "O17"}
# sums that NJOY/OpenMC do not store: build them from the partials
SUMS = {4: range(51, 92), 103: range(600, 650), 104: range(650, 700), 105: range(700, 750),
        106: range(750, 800), 107: range(800, 850)}
NONREDUNDANT = [2, 5, 11, 16, 17, 18, 22, 23, 24, 25, 28, 29, 30, 32, 33, 34, 35, 36, 37, 41, 42, 44, 45,
                *range(51, 92), 102, *range(108, 118), *range(600, 850)]


# ----------------------------------------------------------------------------- sources
def find_h5(lib: str, nuc: str) -> Path | None:
    dirs = LIBRARIES.get(lib, [Path(lib).expanduser()])
    name = ALIAS.get((lib, nuc), nuc)
    for d in dirs:
        d = Path(d)
        if d.is_file() and d.suffix == ".xml":
            d = d.parent
        if not d.exists():
            continue
        hits = glob.glob(str(d / "**" / "neutron" / f"{name}.h5"), recursive=True) or \
            glob.glob(str(d / "**" / f"{name}.h5"), recursive=True)
        if hits:
            return Path(sorted(hits, key=len)[0])
    return None


def from_hdf5(path: Path, mt: int, temp: str = "294K"):
    import openmc.data as od
    n = od.IncidentNeutron.from_hdf5(str(path))
    if temp not in n.energy:
        raise SystemExit(f"temperature {temp} not in {path.name}; available: {sorted(n.energy)}")
    E = np.asarray(n.energy[temp])

    def one(m):
        r = n.reactions.get(m)
        if r is None or temp not in r.xs:
            return None
        xs = r.xs[temp]
        return np.asarray(xs(E))

    def get(m):
        x = one(m)
        if x is None and m in SUMS:
            parts = [p for p in (one(k) for k in SUMS[m]) if p is not None]
            x = np.sum(parts, axis=0) if parts else None
        return x

    if mt == 1:
        parts = [p for p in (one(k) for k in NONREDUNDANT) if p is not None]
        return E, np.sum(parts, axis=0)
    x = get(mt)
    if x is None:
        avail = sorted(n.reactions)
        raise SystemExit(f"MT{mt} not in {path.name}; available MTs: {avail}")
    return E, x


def from_endf(path: Path, mt: int, mf: int = 3):
    import endf
    mat = endf.Material(str(path))
    if (mf, mt) not in mat.section_data:
        mts = sorted(k[1] for k in mat.section_data if k[0] == mf)
        raise SystemExit(f"MF{mf}/MT{mt} not in {path.name}; MF{mf} MTs: {mts}")
    tab = mat.section_data[mf, mt]["sigma"]
    res = mat.section_data.get((2, 151))
    if res and any(r["LRU"] > 0 for iso in res["isotopes"] for r in iso["ranges"]):
        print("WARNING: file has resolved/unresolved resonance parameters; MF3 holds only the background "
              "there. Use --njoy (or the OpenMC HDF5 library) for the full cross section.", file=sys.stderr)
    return np.asarray(tab.x, float), np.asarray(tab.y, float)


def from_njoy(path: Path, mt: int, temp: str = "294K"):
    import tempfile
    import openmc.data as od
    T = float(temp.rstrip("K"))
    with tempfile.TemporaryDirectory() as tmp:
        n = od.IncidentNeutron.from_njoy(str(path), temperatures=[T], stdout=False)
        h5 = Path(tmp) / "nuc.h5"
        n.export_to_hdf5(str(h5))
        key = f"{int(round(T))}K"
        return from_hdf5(h5, mt, key)


def load(args, nuc: str | None = None, lib: str | None = None):
    if args.endf:
        p = Path(args.endf).expanduser()
        return from_njoy(p, args.mt, args.temp) if args.njoy else from_endf(p, args.mt, args.mf)
    lib = lib or args.lib
    p = find_h5(lib, nuc or args.nuc)
    if p is None:
        hint = ("set NUCLEAR_DATA_DIR to the folder holding the libraries, or pass --lib PATH"
                if ND is None and lib in LIBRARIES else f"edit LIBRARIES in {__file__}")
        raise SystemExit(f"{nuc or args.nuc} not found for library '{lib}' ({hint})")
    return from_hdf5(p, args.mt, args.temp)


# ----------------------------------------------------------------------------- window quantities
def _grid(E, lo, hi, n=40000):
    lo, hi = max(lo, E[0]), min(hi, E[-1])
    if hi <= lo:
        return None
    return np.unique(np.concatenate([E[(E >= lo) & (E <= hi)], np.geomspace(lo, hi, n)]))


def thermal(E, s, e0=0.0253):
    return float(np.interp(e0, E, s, left=np.nan, right=np.nan))


def resonance_integral(E, s, lo=0.5, hi=1e5):
    """I = int sigma dE/E (lab). Standard lower limit 0.5 eV (Cd cut-off)."""
    g = _grid(E, lo, hi)
    return np.nan if g is None else float(_trapz(np.interp(g, E, s) / g, g))


def mean_1overE(E, s, lo=1.0, hi=1e5):
    g = _grid(E, lo, hi)
    return np.nan if g is None else resonance_integral(E, s, lo, hi) / np.log(g[-1] / g[0])


def macs(E, s, kT=30e3):
    """Maxwellian-averaged cross section 2/sqrt(pi) int sigma E exp(-E/kT) dE / kT^2.
    E is the lab neutron energy; for heavy targets the c.m./lab difference is A/(A+1) and is
    neglected here (state it, or convert E to c.m. before calling for light targets)."""
    g = _grid(E, 1e-5 * kT, 50 * kT)
    if g is None:
        return np.nan
    return float(2 / np.sqrt(np.pi) * _trapz(np.interp(g, E, s) * g * np.exp(-g / kT), g) / kT**2)


def watt_average(E, s, a=0.988e6, b=2.249e-6):
    """Average over a Watt fission spectrum chi ~ exp(-E/a) sinh(sqrt(bE)); default U-235 thermal."""
    g = _grid(E, 1e3, 2e7)
    if g is None:
        return np.nan
    chi = np.exp(-g / a) * np.sinh(np.sqrt(b * g))
    return float(_trapz(np.interp(g, E, s) * chi, g) / _trapz(chi, g))


def windows(E, s, kT=30e3):
    return {"thermal_b": thermal(E, s), "RI_0.5eV_b": resonance_integral(E, s),
            "mean_1eV-100keV_b": mean_1overE(E, s), f"MACS_{kT/1e3:g}keV_b": macs(E, s, kT),
            "watt_avg_b": watt_average(E, s)}


# ----------------------------------------------------------------------------- commands
def cmd_get(args):
    E, s = load(args)
    if args.emin or args.emax:
        m = (E >= (args.emin or 0)) & (E <= (args.emax or np.inf))
        E, s = E[m], s[m]
    out = args.out or f"{args.nuc or Path(args.endf).stem}_MT{args.mt}.csv"
    src = args.endf or f"{args.lib} {args.nuc} {args.temp}"
    np.savetxt(out, np.column_stack([E, s]), delimiter=",", fmt="%.8e",
               header=f"source: {src}; MT{args.mt}\nE_eV,sigma_b")
    print(f"wrote {out}: {len(E)} points, {E[0]:.4g}-{E[-1]:.4g} eV")


def cmd_windows(args):
    E, s = load(args)
    for k, v in windows(E, s, args.kT).items():
        print(f"{k:>20s}  {v:.6g}")


def cmd_compare(args):
    rows = {}
    for lib in args.libs:
        try:
            E, s = load(args, lib=lib)
        except SystemExit as e:
            print(f"{lib}: {e}", file=sys.stderr)
            continue
        tag = "TENDL-2019 (in JEFF-3.3 build)" if lib == "JEFF-3.3" and args.nuc in TENDL_IN_JEFF33 else lib
        rows[tag] = windows(E, s, args.kT)
    if not rows:
        raise SystemExit("no library had the reaction")
    keys = list(next(iter(rows.values())))
    print(f"{args.nuc} MT{args.mt} at {args.temp}")
    print("library".ljust(32) + "".join(k.rjust(18) for k in keys))
    for lib, w in rows.items():
        print(lib.ljust(32) + "".join(f"{w[k]:18.5g}" for k in keys))
    print("max/min".ljust(32) + "".join(
        f"{(lambda v: v.max() / v.min() if len(v) > 1 and v.min() > 0 else np.nan)(np.array([w[k] for w in rows.values() if np.isfinite(w[k])])):18.3f}"
        for k in keys))
    print("note: identical values usually mean a shared evaluation, not a small uncertainty.")


def cmd_info(args):
    import endf
    mat = endf.Material(str(Path(args.endf).expanduser()))
    h = mat.section_data[1, 451]
    nsub = {10: "neutron", 10010: "proton", 20040: "alpha", 10020: "deuteron", 0: "photo"}.get(h["NSUB"], h["NSUB"])
    print(f"{h['ZSYMAM'].strip()}  lib={h['ALAB'].strip()}  sublibrary={nsub}  AWR={h['AWR']:.4f}  "
          f"eval={h['EDATE'].strip()}  T={h['TEMP']}")
    for mf in (3, 6, 9, 10):
        mts = sorted(k[1] for k in mat.section_data if k[0] == mf)
        if mts:
            print(f"MF{mf}: {mts}")
    res = mat.section_data.get((2, 151))
    if res:
        names = {(0, 0): "scattering radius only", (1, 1): "SLBW", (1, 2): "MLBW", (1, 3): "Reich-Moore",
                 (1, 7): "R-matrix limited", (2, 1): "unresolved"}
        for iso in res["isotopes"]:
            for r in iso["ranges"]:
                print(f"MF2 range {r['EL']:.4g}-{r['EH']:.4g} eV: LRU={r['LRU']} LRF={r['LRF']} "
                      f"({names.get((r['LRU'], r['LRF']), '?')})")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("get", "windows", "compare", "info"):
        p = sub.add_parser(name)
        if name != "info":
            p.add_argument("--nuc", help="OpenMC nuclide name, e.g. O16, Pb208, Am242_m1")
            p.add_argument("--mt", type=int, default=102)
            p.add_argument("--mf", type=int, default=3)
            p.add_argument("--temp", default="294K")
            p.add_argument("--njoy", action="store_true")
            p.add_argument("--kT", type=float, default=30e3, help="MACS temperature in eV")
        p.add_argument("--endf", help="raw ENDF-6 file")
        if name in ("get", "windows"):
            p.add_argument("--lib", default="ENDF/B-VIII.1")
        if name == "get":
            p.add_argument("--out")
            p.add_argument("--emin", type=float)
            p.add_argument("--emax", type=float)
        if name == "compare":
            p.add_argument("--libs", nargs="+", default=["ENDF/B-VIII.1", "JEFF-3.3", "JEFF-4.0", "JENDL-5"])
    args = ap.parse_args(argv)
    {"get": cmd_get, "windows": cmd_windows, "compare": cmd_compare, "info": cmd_info}[args.cmd](args)


if __name__ == "__main__":
    main()
