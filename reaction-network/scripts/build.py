#!/usr/bin/env python3
"""Build a Network, initial composition and conditions from a JSON configuration.

The configuration format is documented in references/config.md. Relative paths in the
configuration are resolved against the configuration file's directory. `build()` returns the
network and an `info` dict recording where every rate came from, which rates carry an
uncertainty factor, which are held fixed, and every substitution made. Write `info` into the
results: a sensitivity ranking is only as meaningful as this list.
"""

import csv
import json
import os
import warnings
from pathlib import Path

import numpy as np
import pynucastro as pyna

import netlib as nl


def load(path):
    path = Path(path)
    cfg = json.loads(path.read_text())
    cfg["_dir"] = str(path.resolve().parent)
    return cfg


def _p(cfg, rel):
    p = Path(os.path.expandvars(str(rel)))  # "$NUCLEAR_DATA_DIR/STARLIB/starlib.dat" works
    return p if p.is_absolute() else Path(cfg["_dir"]) / p


def read_rate_table(path):
    """rate-table contract: CSV with T9, rate[, fu]. Returns arrays (fu may be None)."""
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f)]
    if not rows or "T9" not in rows[0] or "rate" not in rows[0]:
        raise ValueError(f"{path}: rate table needs columns T9, rate[, fu]")
    T9 = np.array([float(r["T9"]) for r in rows])
    rate = np.array([float(r["rate"]) for r in rows])
    fu = np.array([float(r["fu"]) for r in rows]) if "fu" in rows[0] and rows[0]["fu"] else None
    return T9, rate, fu


def read_trajectory(path):
    """thermo-trajectory contract: CSV with time_s, T_K, rho_cgs."""
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f)]
    for c in ("time_s", "T_K", "rho_cgs"):
        if not rows or c not in rows[0]:
            raise ValueError(f"{path}: trajectory needs columns time_s, T_K, rho_cgs")
    t = np.array([float(r["time_s"]) for r in rows])
    T = np.array([float(r["T_K"]) for r in rows])
    rho = np.array([float(r["rho_cgs"]) for r in rows])
    return t, T, rho


def balance_ratio(reactants, products):
    """Callable T -> lambda_reverse / lambda_forward from detailed balance (pynucastro
    partition functions), independent of the forward rate itself."""
    unit = nl.reaclib_rate_from_sets(reactants, products, [[0.0] * 7], label="unit")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        d = pyna.DerivedRate(unit, compute_Q=False, use_pf=True)
    return d


def derived_table_reverse(fwd, outside):
    """TableRate for the reverse of a TableRate, on the same grid, by detailed balance."""
    ratio = balance_ratio(fwd.reactants, fwd.products)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        rev = np.array([fwd.table[k] * ratio.eval(t * 1e9) for k, t in enumerate(fwd.T9)])
    return nl.TableRate(fwd.products, fwd.reactants, fwd.T9, rev, label=fwd.label + "_db",
                        outside=outside, source=f"detailed balance of {fwd.fname}")


def extend_nuclei(names, shells, rl):
    """Add, `shells` times, every neighbour reachable by one n, p or alpha step (either way)
    that appears in REACLIB. Used for the network-completeness check."""
    known = {(n.Z, n.A) for r in rl.get_rates() for n in r.reactants + r.products}
    cur = {(pyna.Nucleus.cast(x).Z, pyna.Nucleus.cast(x).A) for x in names}
    steps = [(0, 1), (1, 1), (2, 4), (0, -1), (-1, -1), (-2, -4), (1, 0), (-1, 0)]
    for _ in range(shells):
        cur |= {(z + dz, a + da) for z, a in cur for dz, da in steps if (z + dz, a + da) in known}
    out = []
    for z, a in sorted(cur):
        out.append(pyna.Nucleus.from_Z_A(z, a).raw)
    return out


def build(cfg, starlib_entries=None):
    info = {"rates": {}, "substitutions": [], "uncertain": {}, "fixed": [], "warnings": []}
    ncfg = cfg["network"]
    rl = pyna.ReacLibLibrary()
    if ncfg.get("extend"):
        ncfg = dict(ncfg, nuclei=extend_nuclei(ncfg["nuclei"], int(ncfg["extend"]), rl))
        info["extended_nuclei"] = ncfg["nuclei"]
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        lib = rl.linking_nuclei(ncfg["nuclei"], with_reverse=ncfg.get("with_reverse", True),
                                print_warning=False)
    rates = list(lib.get_rates())
    for name in ncfg.get("exclude", []):
        r = nl.find_rate(rates, name)
        rates.remove(r)
        info["substitutions"].append({"rate": r.fname, "action": "excluded"})
    for r in rates:
        info["rates"][r.fname] = f"REACLIB {r.label}"

    fu_tables = {}  # fname -> (T9, fu)
    const = {}      # fname -> multiplier

    # ---- STARLIB: rates and/or uncertainty factors
    sl = cfg.get("starlib")
    if sl:
        import starlib
        ents = starlib_entries if starlib_entries is not None else starlib.read(_p(cfg, sl["file"]))
        idx = starlib.index(ents)
        use = sl.get("use", "uncertainty")
        only = set(sl["only"]) if sl.get("only") else None
        new = []
        for r in rates:
            if only is not None and not any(r is nl.find_rate(rates, o) for o in only):
                new.append(r)
                continue
            hits = starlib.choose(starlib.match(idx, r), r, sl.get("label", {}).get(r.fname))
            if not hits:
                new.append(r)
                continue
            if len(hits) > 1:
                info["warnings"].append(f"{r.fname}: {len(hits)} STARLIB entries "
                                        f"{[h['label'] for h in hits]}; using the first")
            h = hits[0]
            if use == "rates":
                t = nl.TableRate(r.reactants, r.products, h["T9"], h["rate"],
                                 label="sl_" + h["label"], outside="clamp",
                                 source=f"STARLIB {h['label']}{h['flag']}")
                new.append(t)
                info["rates"].pop(r.fname, None)
                info["rates"][t.fname] = f"STARLIB {h['label']} (median)"
                fu_tables[t.fname] = (h["T9"], h["fu"])
            else:
                new.append(r)
                fu_tables[r.fname] = (h["T9"], h["fu"])
                if use != "uncertainty":
                    raise ValueError("starlib.use must be 'uncertainty' or 'rates'")
        rates = new

    # ---- explicit rate changes
    shared = []  # (fname_a, fname_b): one random variable in Monte Carlo
    for item in cfg.get("rates", []):
        outside = item.get("outside", "error")
        if "branch" in item:
            # split a rate's flow: fraction f to effective products, 1 - f stays
            b = item["branch"]
            r = nl.find_rate(rates, b["rate"])
            f = float(b["fraction"])
            if not 0 < f < 1:
                raise ValueError("branch fraction must be in (0, 1)")
            m = pyna.ModifiedRate(r, new_products=b["products"])
            rates.append(m)
            const[r.fname] = const.get(r.fname, 1.0) * (1 - f)
            const[m.fname] = const.get(m.fname, 1.0) * f
            if r.fname in fu_tables:
                fu_tables[m.fname] = fu_tables[r.fname]
            shared.append((r.fname, m.fname))
            info["rates"][m.fname] = f"branch of {r.fname} to {b['products']}"
            info["substitutions"].append({"rate": r.fname, "action": "branch", "fraction": f,
                                          "to": b["products"], "why": b.get("why", "")})
            continue
        if "add" in item:
            reac, prod = item["add"]["reactants"], item["add"]["products"]
            T9, val, fu = read_rate_table(_p(cfg, item["table"]))
            t = nl.TableRate(reac, prod, T9, val, label=item.get("label", "user"), outside=outside,
                             source=str(item["table"]))
            rates.append(t)
            info["rates"][t.fname] = f"table {item['table']}"
            info["substitutions"].append({"rate": t.fname, "action": "added", "table": item["table"]})
            if fu is not None:
                fu_tables[t.fname] = (T9, fu)
            if item.get("reverse", "none") == "derive":
                rv = derived_table_reverse(t, outside)
                rates.append(rv)
                info["rates"][rv.fname] = "detailed balance"
            continue
        r = nl.find_rate(rates, item["rate"])
        if "multiply" in item:
            const[r.fname] = const.get(r.fname, 1.0) * float(item["multiply"])
            info["substitutions"].append({"rate": r.fname, "action": "multiply",
                                          "factor": item["multiply"]})
        if "table" in item or "reaclib_sets" in item:
            rev = [x for x in rates if nl.is_reverse_of(x, r)]
            mode = item.get("reverse", "derive" if rev else "none")
            if "table" in item:
                T9, val, fu = read_rate_table(_p(cfg, item["table"]))
                new = nl.TableRate(r.reactants, r.products, T9, val, label=item.get("label", "user"),
                                   outside=outside, source=str(item["table"]))
                src = f"table {item['table']}"
            else:
                new = nl.reaclib_rate_from_sets(r.reactants, r.products, item["reaclib_sets"],
                                                label=item.get("label", "fit"))
                fu, src = None, "REACLIB-form sets from config"
            rates[rates.index(r)] = new
            info["rates"].pop(r.fname, None)
            fu_tables.pop(r.fname, None)
            info["rates"][new.fname] = src
            info["substitutions"].append({"rate": r.fname, "action": "replaced", "by": src,
                                          "reverse": mode})
            if fu is not None:
                fu_tables[new.fname] = (T9, fu)
            for rv in rev:
                if mode == "keep":
                    info["warnings"].append(f"{rv.fname}: library reverse kept although its forward "
                                            "rate was replaced (detailed balance violated)")
                    continue
                rates.remove(rv)
                info["rates"].pop(rv.fname, None)
                if mode == "drop":
                    info["substitutions"].append({"rate": rv.fname, "action": "dropped"})
                    continue
                if mode != "derive":
                    raise ValueError("reverse must be 'derive', 'keep' or 'drop'")
                if isinstance(new, nl.TableRate):
                    d = derived_table_reverse(new, outside)
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        d = pyna.DerivedRate(new, compute_Q=False, use_pf=True)
                rates.append(d)
                info["rates"][d.fname] = f"detailed balance of {new.fname}"
                if new.fname in fu_tables:
                    fu_tables[d.fname] = fu_tables[new.fname]

    # ---- user uncertainty factors
    unc = cfg.get("uncertainty", {})
    for name, v in unc.get("fu", {}).items():
        r = nl.find_rate(rates, name)
        if isinstance(v, (int, float)):
            fu_tables[r.fname] = (None, float(v))
        else:
            T9, _, fu = read_rate_table(_p(cfg, v))
            if fu is None:
                raise ValueError(f"{v}: no fu column")
            fu_tables[r.fname] = (T9, fu)
        # the reverse and any branch share it
        for rv in rates:
            if nl.is_reverse_of(rv, r):
                fu_tables[rv.fname] = fu_tables[r.fname]
        for a, b in shared:
            if a == r.fname:
                fu_tables[b] = fu_tables[r.fname]

    # correlated rate uncertainties: [{"rates": [A, B], "rho": r}], resolved to fnames here and
    # turned into a correlation matrix of the groups' normal variables by sensitivity.py
    info["correlations"] = []
    for c in unc.get("correlations", []):
        names = [nl.find_rate(rates, n).fname for n in c["rates"]]
        rho = float(c["rho"])
        if len(names) != 2 or not -1 < rho < 1:
            raise ValueError("a correlation entry needs two rates and -1 < rho < 1")
        info["correlations"].append({"rates": names, "rho": rho, "why": c.get("why", "")})
    net = nl.Network(rates, screening=ncfg.get("screening", "chugunov_2007"),
                     symmetric_screening=ncfg.get("symmetric_screening", False),
                     nuclei=ncfg["nuclei"])
    linked = {n for r in rates for n in r.reactants + r.products}
    info["inert"] = [n.raw for n in net.nuclei if n not in linked]
    for i, r in enumerate(net.rates):
        if r.fname in const:
            net.const[i] = const[r.fname]
        if r.fname in fu_tables:
            T9, fu = fu_tables[r.fname]
            net.set_fu(i, fu, T9)
        elif unc.get("default_fu") and not r.weak:
            net.set_fu(i, unc["default_fu"])
            info["warnings"].append(f"{r.fname}: default fu {unc['default_fu']} assumed")
    # groups: a forward rate and its reverse share one random variable
    group = list(range(len(net.rates)))
    pos = {r.fname: i for i, r in enumerate(net.rates)}
    for i, r in enumerate(net.rates):
        for j, s in enumerate(net.rates[:i]):
            if nl.is_reverse_of(r, s):
                group[i] = group[j]
    for a, b in shared:  # branches share their parent's variable
        group[pos[b]] = group[pos[a]]
    net.group = np.array(group)
    for i, r in enumerate(net.rates):
        if net.fu[i] is not None:
            info["uncertain"][r.fname] = "fu(T)" if len(net.fu[i][0]) > 2 else \
                f"fu={np.exp(net.fu[i][1][0]):.3g}"
        else:
            info["fixed"].append(r.fname)
    info["n_rates"] = len(net.rates)
    info["n_nuclei"] = len(net.nuclei)
    info["screening"] = net.screening
    info["pynucastro"] = pyna.__version__
    return net, info


def conditions(cfg):
    c = cfg["conditions"]
    if c["type"] == "constant":
        return nl.Conditions.constant(float(c["T_K"]), float(c["rho_cgs"]), float(c["t_end_s"]),
                                      float(c.get("t0_s", 0.0)))
    if c["type"] == "trajectory":
        t, T, rho = read_trajectory(_p(cfg, c["file"]))
        if "T_scale" in c:
            T = T * float(c["T_scale"])
        if "rho_scale" in c:
            rho = rho * float(c["rho_scale"])
        return nl.Conditions(t, T, rho)
    raise ValueError("conditions.type must be 'constant' or 'trajectory'")


def output_times(cfg, cond):
    o = cfg.get("output", {})
    if "times_s" in o:
        return np.array(o["times_s"], float)
    n = int(o.get("n_log", 40))
    t0, t1 = cond.t[0], cond.t[-1]
    first = max(t1 * 1e-12, (cond.t[1] - t0) * 1e-6) if t0 == 0 else t0
    return np.unique(np.concatenate([[t0], t0 + np.geomspace(first, t1 - t0, n)]))


def initial_Y(cfg, net):
    ini = cfg["initial"]
    return net.Y_from_X(ini["X"], normalize=ini.get("normalize", False))
