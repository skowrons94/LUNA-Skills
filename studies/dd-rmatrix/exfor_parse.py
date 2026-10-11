"""Minimal EXFOR (.x4) parser: pulls 1-H-2(D,N) and 1-H-2(D,P) angle-integrated
cross sections (SIG) and S-factors (SFC) with their BIB metadata."""
import glob
import json
import re
import sys

REACS = {"1-H-2(D,N)2-HE-3": "dn", "1-H-2(D,P)1-H-3": "dp"}


def fields(line, n=6):
    return [line[i * 11:(i + 1) * 11].strip() for i in range(n)]


def num(s):
    s = s.strip()
    if not s:
        return None
    s = re.sub(r"(?<=\d)([+-])(?=\d)", r"e\1", s)       # 1.2-3 -> 1.2e-3
    try:
        return float(s)
    except ValueError:
        return None


def parse_table(lines, i):
    """lines[i] starts with DATA/COMMON; returns (heads, units, rows, next_i)."""
    ncol = int(lines[i][11:22]); nrow = int(lines[i][22:33])
    if lines[i].startswith("COMMON"):
        nrow = 1
    nl = (ncol + 5) // 6
    i += 1
    heads = sum((fields(lines[i + k]) for k in range(nl)), [])[:ncol]; i += nl
    units = sum((fields(lines[i + k]) for k in range(nl)), [])[:ncol]; i += nl
    rows = []
    for _ in range(nrow):
        vals = sum((fields(lines[i + k]) for k in range(nl)), [])[:ncol]; i += nl
        rows.append([num(v) for v in vals])
    return heads, units, rows, i


def parse_entry(path):
    lines = open(path, errors="replace").read().splitlines()
    out, entry_bib, entry_common = [], {}, {}
    sub, bib, common, key, in_bib = None, {}, {}, None, False
    i = 0
    while i < len(lines):
        L = lines[i].ljust(80)
        tag = L[:10].strip()
        if tag == "SUBENT":
            sub, bib, common, key = L[14:22].strip(), {}, {}, None
        elif tag == "BIB":
            in_bib, key = True, None
        elif tag == "ENDBIB":
            in_bib = False
            if sub.endswith("001"):
                entry_bib = bib
        elif in_bib:
            if tag:
                key = tag
            if key:
                bib.setdefault(key, []).append(L[11:66].strip())
        elif tag in ("COMMON", "DATA") and L[11:22].strip().isdigit():
            h, u, r, i = parse_table(lines, i)
            if tag == "COMMON":
                common = {hh: (uu, vv) for hh, uu, vv in zip(h, u, r[0])} if r else {}
                if sub.endswith("001"):
                    entry_common = common
                continue
            reac = " ".join(bib.get("REACTION", []))
            hit = [v for k, v in REACS.items() if k in reac]
            m = re.search(r"\(1-H-2\(D,[NP]\)[^,]*,([^,]*),([^,)]*),?([^,)]*),?([^,)]*)", reac)
            if len(hit) == 1 and m and m.group(1) == "" and m.group(2) == "SIG" \
                    and m.group(3) == "" and m.group(4) in ("", "SFC"):
                get = lambda k: " ".join(bib.get(k, entry_bib.get(k, [])))
                out.append({
                    "entry": sub, "reaction": hit[0],
                    "quantity": "SFC" if m.group(4) == "SFC" else "SIG",
                    "reaction_string": reac, "author": get("AUTHOR"),
                    "reference": get("REFERENCE")[:160], "errors": get("ERR-ANALYS")[:2000],
                    "method": get("METHOD")[:500], "sample": get("SAMPLE")[:500],
                    "comment": get("COMMENT")[:1500], "status": get("STATUS")[:300],
                    "common": {**entry_common, **common},
                    "heads": h, "units": u, "rows": r})
            continue
        i += 1
    return out


if __name__ == "__main__":
    root = sys.argv[1]
    sets = []
    for f in sorted(glob.glob(f"{root}/**/*.x4", recursive=True)):
        txt = open(f, errors="replace").read()
        if "1-H-2(D,N)" in txt or "1-H-2(D,P)" in txt:
            try:
                sets += parse_entry(f)
            except Exception as e:
                print("fail", f, e)
    json.dump(sets, open("data/exfor/dd_sets.json", "w"), indent=0)
    for s in sets:
        ek = next((h for h in s["heads"] if h.startswith("EN")), None)
        e = [r[s["heads"].index(ek)] for r in s["rows"]] if ek else []
        e = [x for x in e if x is not None]
        print(f"{s['entry']:9s} {s['reaction']} {s['quantity']} n={len(s['rows']):3d} "
              f"E=[{min(e) if e else '?'}..{max(e) if e else '?'}] {s['units'][:4]} {s['author'][:45]} | {s['reference'][:40]}")
