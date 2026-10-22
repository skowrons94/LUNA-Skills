#!/usr/bin/env python3
"""Read STARLIB rate files (Sallaska et al. 2013 format) and match entries to pynucastro rates.

Each entry: a header line (chapter in columns 1-2, up to six nuclide labels right-aligned in
5-character fields from column 6, label in columns 44-47, flag in column 48: 'v' reverse,
'w' laboratory weak, Q value), then 60 lines 'T9  rate  fu' from 0.001 to 10 GK. For Monte Carlo
rates the rate is the median and fu = exp(sigma) of a lognormal distribution.

Isomers: 'al-6' is 26Al ground state, 'al*6' the 228-keV isomer; plain 'al26' is the total.

  python3 starlib.py show FILE "p n14 o15"        # reactants and products, space separated
  python3 starlib.py show FILE "p mg25 al26" --T9 0.03 0.05 0.1
"""

import argparse
import re
import sys
from collections import Counter

import numpy as np

_ELEMENTS = None
# isomer labels used in STARLIB v6.x (checked on starlib_v610): only 26Al
ISOMERS = {"al-6": (13, 26, "g"), "al*6": (13, 26, "m")}


def _symbols():
    global _ELEMENTS
    if _ELEMENTS is None:
        import pynucastro as pyna
        _ELEMENTS = {}
        for z in range(0, 119):
            try:
                sym = pyna.nucdata.elements.PeriodicTable.lookup_Z(z).abbreviation.lower()
            except Exception:  # noqa: BLE001  gaps in the table
                continue
            _ELEMENTS[sym] = z
    return _ELEMENTS


def parse_label(s):
    """STARLIB nuclide label -> (Z, A, state) with state None (total), 'g' or 'm'."""
    s = s.strip().lower()
    special = {"n": (0, 1), "p": (1, 1), "d": (1, 2), "t": (1, 3), "g": None}
    if s in special:
        return None if special[s] is None else (*special[s], None)
    if s in ISOMERS:
        return ISOMERS[s]
    if re.fullmatch(r"[a-z]+[-*]\d+", s):
        raise ValueError(f"unknown STARLIB isomer label {s!r}; add it to ISOMERS")
    m = re.fullmatch(r"([a-z]+)(\d+)", s)
    if not m:
        raise ValueError(f"cannot parse STARLIB label {s!r}")
    el, a = m.groups()
    return (_symbols()[el], int(a), None)


def read(path, cache=True):
    """Return a list of entries: dict(chapter, reactants, products, label, flag, Q, T9, rate, fu).

    The parsed library is cached in ~/.cache/reaction-network keyed by the file's SHA-256, so
    the source file itself is never modified."""
    import hashlib
    import pickle
    from pathlib import Path
    cpath = None
    if cache:
        h = hashlib.sha256(Path(path).read_bytes()).hexdigest()[:20]
        cdir = Path.home() / ".cache" / "reaction-network"
        cpath = cdir / f"starlib-{h}.pkl"
        if cpath.exists():
            with open(cpath, "rb") as f:
                return pickle.load(f)
    entries = _parse(path)
    if cpath is not None:
        cdir.mkdir(parents=True, exist_ok=True)
        with open(cpath, "wb") as f:
            pickle.dump(entries, f)
    return entries


def _parse(path):
    entries = []
    with open(path) as f:
        lines = f.read().splitlines()
    i = 0
    while i < len(lines):
        h = lines[i]
        if not h.strip():
            i += 1
            continue
        chapter = int(h[0:2])
        labels = [h[5 + 5 * k: 10 + 5 * k] for k in range(6)]
        labels = [x for x in labels if x.strip()]
        nucs = [parse_label(x) for x in labels]
        nucs = [x for x in nucs if x is not None]
        nr = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 2, 8: 3, 9: 3, 10: 4, 11: 1}[chapter]
        label = h[43:47].strip()
        flag = h[47:48].strip()
        try:
            Q = float(h[52:64])
        except ValueError:
            Q = float("nan")
        data = np.array([[float(v) for v in lines[i + 1 + k].split()[:3]] for k in range(60)])
        entries.append({"chapter": chapter, "reactants": nucs[:nr], "products": nucs[nr:],
                        "label": label, "flag": flag, "Q": Q, "T9": data[:, 0],
                        "rate": data[:, 1], "fu": data[:, 2], "line": i + 1})
        i += 61
    return entries


def key(reactants, products):
    return (tuple(sorted(Counter(reactants).items())), tuple(sorted(Counter(products).items())))


def index(entries):
    idx = {}
    for e in entries:
        idx.setdefault(key(e["reactants"], e["products"]), []).append(e)
    return idx


def rate_key(rate):
    """Key of a pynucastro rate; nuclei carry state None (pynucastro has no isomer split here)."""
    r = [(n.Z, n.A, None) for n in rate.reactants]
    p = [(n.Z, n.A, None) for n in rate.products]
    return key(r, p)


def match(idx, rate):
    """STARLIB entries for a pynucastro rate (may be empty or several)."""
    return idx.get(rate_key(rate), [])


def choose(hits, rate, label=None):
    """Narrow several STARLIB entries for one pynucastro rate: an explicit label first, then
    the weak-interaction type (STARLIB labels electron captures 'ec'), then the REACLIB label."""
    if len(hits) <= 1:
        return hits
    if label:
        sel = [h for h in hits if h["label"] == label]
        if sel:
            return sel
    if getattr(rate, "weak", False):
        ec = getattr(rate, "weak_type", "") == "electron_capture"
        sel = [h for h in hits if (h["label"] == "ec") == ec]
        if sel:
            hits = sel
    sel = [h for h in hits if h["label"] == getattr(rate, "label", None)]
    return sel or hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("file")
    s.add_argument("reaction", help='reactants then products, e.g. "p n14 o15"')
    s.add_argument("--T9", type=float, nargs="*")
    a = ap.parse_args(argv)
    ents = read(a.file)
    toks = [parse_label(t) for t in a.reaction.split()]
    toks = [t for t in toks if t is not None]
    hits = []
    for nr in (1, 2, 3, 4):
        hits += [e for e in ents if key(e["reactants"], e["products"]) == key(toks[:nr], toks[nr:])]
    if not hits:
        print("no entry")
        return 1
    for e in hits:
        print(f"chapter {e['chapter']}  label {e['label']}  flag '{e['flag']}'  Q {e['Q']}  "
              f"(file line {e['line']})")
        T9s = a.T9 or [0.01, 0.03, 0.1, 0.3, 1.0, 3.0]
        for t in T9s:
            r = np.exp(np.interp(np.log(t), np.log(e["T9"]), np.log(np.maximum(e["rate"], 1e-300))))
            fu = np.exp(np.interp(np.log(t), np.log(e["T9"]), np.log(e["fu"])))
            print(f"   T9 {t:7.4f}  rate {r:11.4e}  fu {fu:7.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
