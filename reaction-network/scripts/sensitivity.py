#!/usr/bin/env python3
"""Rate sensitivity of one-zone observables: Monte Carlo or one-at-a-time (OAT).

  python3 sensitivity.py CONFIG --out DIR --mode mc  --n 500 --seed 1 --jobs 4
  python3 sensitivity.py CONFIG --out DIR --mode oat --factor 2 [--only "mg25(p,g)al26" ...]

Monte Carlo: every rate with an uncertainty factor fu(T) is multiplied by fu(T)**p with one
p ~ N(0, 1) per sample and per rate group (a forward rate, its reverse and its branches share
p; Longland et al. 2010 convention, lognormal rates). Rates without fu are held fixed and listed
in the output. For each observable: median and 68 % interval, and per rate group the Spearman
rank correlation with a bootstrap interval, plus the variance share from a linear regression
of ln(observable) on all p (when there are enough samples).

OAT: each rate group multiplied and divided by FACTOR; reports d ln O / d ln lambda.

Outputs DIR/samples.csv (MC) or DIR/oat.csv, DIR/summary.json and DIR/ranking.md.
"""

import argparse
import csv
import json
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
import build  # noqa: E402
import netlib as nl  # noqa: E402
import prov  # noqa: E402

_W = {}


def _init(cfg_path):
    warnings.simplefilter("ignore", UserWarning)
    cfg = build.load(cfg_path)
    net, info = build.build(cfg)
    cond = build.conditions(cfg)
    _W.update(cfg=cfg, net=net, info=info, cond=cond, Y0=build.initial_Y(cfg, net),
              tout=np.array([cond.t[0], cond.t[-1]]), obs=cfg["output"]["observables"])


def _evaluate(task):
    """task = (kind, payload): ('p', vector over groups) or ('mult', {group: factor})."""
    kind, payload = task
    net = _W["net"]
    net.p[:] = 0.0
    net.const[:] = _W.setdefault("const0", net.const.copy())
    if kind == "p":
        pg = payload
        for i in range(len(net.rates)):
            if net.fu[i] is not None:
                net.p[i] = pg[net.group[i]]
    else:
        for g, f in payload.items():
            net.const[net.group == g] *= f
    s = _W["cfg"].get("solver", {})
    try:
        res = nl.burn(net, _W["Y0"], _W["cond"], _W["tout"], rtol=s.get("rtol", 1e-6),
                      atol=s.get("atol", 1e-20), method=s.get("method", "BDF"))
    except Exception as e:  # noqa: BLE001  a failed sample is recorded, not dropped silently
        return None, str(e)
    return [nl.observable(net, res["X"][-1], res["Y"][-1], res["E"][-1], o) for o in _W["obs"]], ""


def group_table(net, uncertain_only=True):
    """Rate groups: id -> member rate names, the exothermic (forward) member first."""
    g = {}
    for i, r in enumerate(net.rates):
        if net.fu[i] is not None or not uncertain_only:
            g.setdefault(int(net.group[i]), []).append(
                (r.fname.endswith('__modified'), -(r.Q if r.Q is not None else 0), r.fname))
    return {k: [n for *_, n in sorted(v)] for k, v in g.items()}


def group_label(members):
    return members[0]


def noise_threshold(n, ngroups, alpha=0.05):
    """|Spearman| a pure-noise rate exceeds with probability alpha after a Bonferroni
    correction over all groups (normal approximation, sd = 1/sqrt(n-1))."""
    return float(stats.norm.ppf(1 - alpha / (2 * max(ngroups, 1))) / np.sqrt(max(n - 1, 1)))


def run_mc(a, cfg, net, info, out):
    groups = group_table(net)
    gid = sorted(groups)
    rng = np.random.default_rng(a.seed)
    P = rng.standard_normal((a.n, len(gid)))
    ngroup_all = int(net.group.max()) + 1
    tasks = []
    for k in range(a.n):
        pg = np.zeros(ngroup_all)
        pg[gid] = P[k]
        tasks.append(("p", pg))
    tasks.insert(0, ("p", np.zeros(ngroup_all)))  # nominal
    with ProcessPoolExecutor(max_workers=a.jobs, initializer=_init, initargs=(a.config,)) as ex:
        res = list(ex.map(_evaluate, tasks, chunksize=max(1, a.n // (4 * a.jobs))))
    nominal, _ = res[0]
    vals, errs = [r[0] for r in res[1:]], [r[1] for r in res[1:]]
    ok = np.array([v is not None for v in vals])
    obs_names = cfg["output"]["observables"]
    V = np.array([v if v is not None else [np.nan] * len(obs_names) for v in vals])
    with open(out / "samples.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sample", "ok"] + [f"p:{group_label(groups[g])}" for g in gid] + obs_names)
        for k in range(a.n):
            w.writerow([k, int(ok[k])] + [f"{x:.6f}" for x in P[k]] + [f"{x:.8e}" for x in V[k]])
    summary = {"mode": "mc", "n": a.n, "n_failed": int((~ok).sum()), "seed": a.seed,
               "failures": sorted(set(e for e in errs if e))[:10], "nominal": dict(zip(obs_names, nominal)),
               "observables": {}}
    Pk, Vk = P[ok], V[ok]
    rng_b = np.random.default_rng(a.seed + 1)
    for j, name in enumerate(obs_names):
        v = Vk[:, j]
        pos = np.all(v > 0)
        y = np.log(v) if pos else v
        q = np.percentile(v, [2.5, 16, 50, 84, 97.5])
        rows = []
        for c, g in enumerate(gid):
            rho = stats.spearmanr(Pk[:, c], y).statistic
            bs = []
            for _ in range(a.bootstrap):
                idx = rng_b.integers(0, len(y), len(y))
                bs.append(stats.spearmanr(Pk[idx, c], y[idx]).statistic)
            lo, hi = np.nanpercentile(bs, [16, 84]) if bs else (np.nan, np.nan)
            rows.append({"rate": group_label(groups[g]), "members": groups[g],
                         "spearman": float(rho), "spearman_68": [float(lo), float(hi)]})
        share = None
        if len(y) > len(gid) + 20 and np.std(y) > 0:
            Xd = np.column_stack([np.ones(len(y)), Pk])
            beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
            share = beta[1:] ** 2 / np.var(y)
            for r_, s_ in zip(rows, share):
                r_["variance_share"] = float(s_)
        rows.sort(key=lambda r: -abs(r["spearman"]) if np.isfinite(r["spearman"]) else 0)
        thr = noise_threshold(len(y), len(gid))
        for r_ in rows:
            r_["significant"] = bool(abs(r_["spearman"]) > thr)
        summary["observables"][name] = {
            "noise_threshold": thr,
            "log": bool(pos), "median": float(q[2]), "p16": float(q[1]), "p84": float(q[3]),
            "p2.5": float(q[0]), "p97.5": float(q[4]),
            "factor_68": float(np.sqrt(q[3] / q[1])) if pos else None,
            "linear_R2": float(share.sum()) if share is not None else None,
            "ranking": rows}
    return summary


def run_oat(a, cfg, net, info, out):
    groups = group_table(net, uncertain_only=False)
    if a.only:
        keep = set()
        for name in a.only:
            r = nl.find_rate(net.rates, name)
            keep.add(int(net.group[net.rates.index(r)]))
        groups = {g: m for g, m in groups.items() if g in keep}
    tasks = [("mult", {})]
    gid = sorted(groups)
    for g in gid:
        tasks += [("mult", {g: a.factor}), ("mult", {g: 1 / a.factor})]
    with ProcessPoolExecutor(max_workers=a.jobs, initializer=_init, initargs=(a.config,)) as ex:
        res = list(ex.map(_evaluate, tasks, chunksize=1))
    obs_names = cfg["output"]["observables"]
    nominal = res[0][0]
    summary = {"mode": "oat", "factor": a.factor, "nominal": dict(zip(obs_names, nominal)),
               "observables": {o: {"ranking": []} for o in obs_names}, "failures": []}
    with open(out / "oat.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rate", "members"] + [f"dlnO/dlnL:{o}" for o in obs_names])
        for k, g in enumerate(gid):
            up, dn = res[1 + 2 * k][0], res[2 + 2 * k][0]
            if up is None or dn is None:
                summary["failures"].append(group_label(groups[g]))
                continue
            sens = []
            for j, o in enumerate(obs_names):
                s = (np.log(up[j] / dn[j]) / (2 * np.log(a.factor))
                     if up[j] > 0 and dn[j] > 0 else np.nan)
                sens.append(s)
                summary["observables"][o]["ranking"].append(
                    {"rate": group_label(groups[g]), "members": groups[g], "dlnO_dlnL": float(s),
                     "ratio_up": up[j] / nominal[j] if nominal[j] else None,
                     "ratio_down": dn[j] / nominal[j] if nominal[j] else None})
            w.writerow([group_label(groups[g]), " ".join(groups[g])] + [f"{s:.5g}" for s in sens])
    for o in obs_names:
        summary["observables"][o]["ranking"].sort(
            key=lambda r: -abs(r["dlnO_dlnL"]) if np.isfinite(r["dlnO_dlnL"]) else 0)
    return summary


def ranking_md(summary, info, top):
    lines = [f"# Rate sensitivity ({summary['mode']})", ""]
    if summary["mode"] == "mc":
        lines.append(f"{summary['n']} samples, {summary['n_failed']} failed, seed {summary['seed']}. "
                     f"Uncertain rates: {len(info['uncertain'])}; fixed (no fu): {len(info['fixed'])}.")
    else:
        lines.append(f"Each rate group x/÷ {summary['factor']}.")
    lines.append("")
    for o, d in summary["observables"].items():
        lines.append(f"## {o}")
        if summary["mode"] == "mc":
            fac = f", factor {d['factor_68']:.3g} (68 %)" if d["factor_68"] else ""
            r2 = "" if d["linear_R2"] is None else f"; linear R² ≈ {d['linear_R2']:.2f}"
            lines.append(f"median {d['median']:.4e}, 68 % [{d['p16']:.4e}, {d['p84']:.4e}]{fac}{r2}. "
                         f"Noise threshold |ρ| > {d['noise_threshold']:.2f} (Bonferroni, 5 %).")
            lines += ["", "| rate | Spearman ρ | 68 % (bootstrap) | variance share | above noise |",
                      "|---|---|---|---|---|"]
            for r in d["ranking"][:top]:
                vs = r.get("variance_share")
                lines.append(f"| {r['rate']} | {r['spearman']:+.3f} | [{r['spearman_68'][0]:+.2f}, "
                             f"{r['spearman_68'][1]:+.2f}] | {'' if vs is None else f'{vs:.3f}'} | "
                             f"{'yes' if r['significant'] else 'no'} |")
        else:
            lines += ["", "| rate | d ln O / d ln λ | O(×f)/O | O(÷f)/O |", "|---|---|---|---|"]
            for r in d["ranking"][:top]:
                lines.append(f"| {r['rate']} | {r['dlnO_dlnL']:+.4f} | {r['ratio_up']:.4g} | "
                             f"{r['ratio_down']:.4g} |")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["mc", "oat"], required=True)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--bootstrap", type=int, default=100)
    ap.add_argument("--factor", type=float, default=2.0)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    cfg = build.load(a.config)
    if not cfg.get("output", {}).get("observables"):
        raise SystemExit("config.output.observables is empty: name what the sensitivity is of")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        net, info = build.build(cfg)
    if a.mode == "mc" and not info["uncertain"]:
        raise SystemExit("no rate has an uncertainty factor: set starlib or uncertainty.fu")
    summary = run_mc(a, cfg, net, info, out) if a.mode == "mc" else run_oat(a, cfg, net, info, out)
    summary["wall_s"] = time.time() - t0
    summary["network"] = info
    summary["provenance"] = prov.block(inputs=[Path(a.config), *prov.config_inputs(cfg)],
                                       tools={"pynucastro": info["pynucastro"]})
    prov.write_json(out / "summary.json", summary)
    md = ranking_md(summary, info, a.top)
    (out / "ranking.md").write_text(md)
    print(md)
    print(f"wall {summary['wall_s']:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
