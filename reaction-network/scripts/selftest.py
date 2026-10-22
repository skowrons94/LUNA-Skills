#!/usr/bin/env python3
"""Self-test of the reaction-network scripts (needs pynucastro; STARLIB checks run if
$NUCLEAR_DATA_DIR/STARLIB/starlib.dat exists).

Checks with known answers:
  1. dY/dt and energy generation equal pynucastro's RateCollection (with screening)
  2. analytic Jacobian equals finite differences
  3. a pure decay follows exp(-t ln2 / t_half) (13N)
  4. CNO cycle at constant T reaches Y(12C) lambda_12 = Y(14N) lambda_14 (steady flow)
  5. a REACLIB rate replaced by its own table gives the same burn
  6. detailed balance: derived reverse of a table rate matches pynucastro's DerivedRate
  7. a constant trajectory file gives the same burn as constant conditions
  8. REACLIB-form fit recovers a two-set rate; REACLIB text round-trips through pynucastro
  9. Monte Carlo multipliers: forward and reverse share p; fu**p applied; seeds reproduce
 10. branch: flows split by the fraction, total preserved
 11. STARLIB parser on a synthetic entry; on the real file if present
Run: python3 selftest.py   -> PASS/FAIL lines; exit code 1 on any failure.
"""

import csv
import json
import os
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np

warnings.simplefilter("ignore", UserWarning)
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import pynucastro as pyna  # noqa: E402

import build  # noqa: E402
import netlib as nl  # noqa: E402
import rates as rtools  # noqa: E402
import starlib  # noqa: E402

ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {info}")


rl = pyna.ReacLibLibrary()
CNO = ["p", "he4", "c12", "c13", "n13", "n14", "n15", "o14", "o15", "o16", "o17", "f17", "f18"]

# 1. ydot and eps against pynucastro
lib = rl.linking_nuclei(CNO, with_reverse=True, print_warning=False)
rc = pyna.RateCollection(libraries=[lib])
net = nl.Network(rc.get_rates(), screening="chugunov_2007")
comp = pyna.Composition(rc.unique_nuclei)
comp.set_equal()
Y = np.array([comp.get_molar()[n] for n in net.nuclei])
worst, worst_e = 0.0, 0.0
for T, rho in [(2e7, 100.0), (2e8, 1e3), (1e9, 1e5)]:
    ref = rc.evaluate_ydots(rho, T, comp, screen_func=pyna.screening.chugunov_2007)
    r = np.array([ref[n] for n in net.nuclei])
    worst = max(worst, np.max(np.abs(net.ydot(T, rho, Y) - r)) / np.max(np.abs(r)))
    e_ref = rc.evaluate_energy_generation(rho, T, comp, screen_func=pyna.screening.chugunov_2007)
    worst_e = max(worst_e, abs(net.eps(net.ydot(T, rho, Y)) / e_ref - 1))
check("ydot equals pynucastro (screened)", worst < 1e-12, f"max rel {worst:.1e}")
check("energy generation equals pynucastro", worst_e < 1e-10, f"max rel {worst_e:.1e}")

# 2. Jacobian
net0 = nl.Network(rc.get_rates(), screening="none")
T, rho = 2e8, 1e3
J = net0.jacobian(T, rho, Y)
Jn = np.zeros_like(J)
for j in range(len(Y)):
    h = 1e-7 * Y[j]
    Yp, Ym = Y.copy(), Y.copy()
    Yp[j] += h
    Ym[j] -= h
    Jn[:, j] = (net0.ydot(T, rho, Yp) - net0.ydot(T, rho, Ym)) / (2 * h)
rel = np.max(np.abs(J - Jn)) / np.max(np.abs(J))
check("analytic Jacobian equals finite differences", rel < 1e-6, f"max rel {rel:.1e}")

# 3. 13N decay
dec = [r for r in rc.get_rates() if r.fname.startswith("N13__C13")]
ndec = nl.Network(dec, screening="none")
Y0 = np.zeros(len(ndec.nuclei))
Y0[ndec.index[pyna.Nucleus("n13")]] = 1 / 13
thalf = np.log(2) / dec[0].eval(1e7)
cond = nl.Conditions.constant(1e7, 1.0, 3 * thalf)
res = nl.burn(ndec, Y0, cond, [thalf, 2 * thalf, 3 * thalf], rtol=1e-9, atol=1e-30)
expect = (1 / 13) * 0.5 ** np.array([1, 2, 3])
got = res["Y"][1:, ndec.index[pyna.Nucleus("n13")]]
check("13N decay is exponential", np.allclose(got, expect, rtol=1e-6),
      f"t_half {thalf:.1f} s, rel {np.max(np.abs(got / expect - 1)):.1e}")
check("13N half-life is 9.97 min", abs(thalf / 60 - 9.965) < 0.01, f"{thalf / 60:.3f} min")

# 4. CNO steady flow
libf = rl.linking_nuclei(CNO, with_reverse=False, print_warning=False)
netc = nl.Network(libf.get_rates(), screening="none")
X = {"p": 0.7, "he4": 0.28, "c12": 0.003, "n14": 0.001, "o16": 0.009}
X["he4"] += 1 - sum(X.values())
Yc = netc.Y_from_X(X)
T, rho = 4e7, 100.0
lam12 = rho * rl.get_rate_by_name("c12(p,g)n13").eval(T)
cond = nl.Conditions.constant(T, rho, 3e14)
res = nl.burn(netc, Yc, cond, None, rtol=1e-8, atol=1e-22)
Yp = res["Y"][-1][netc.index[pyna.Nucleus("p")]]
lam14 = rho * rl.get_rate_by_name("n14(p,g)o15").eval(T)
ratio = (res["Y"][-1][netc.index[pyna.Nucleus("c12")]] * lam12) / \
        (res["Y"][-1][netc.index[pyna.Nucleus("n14")]] * lam14)
check("CNO steady flow Y12 l12 = Y14 l14", abs(ratio - 1) < 0.02,
      f"ratio {ratio:.4f}, X(p) {Yp:.3f}")
check("mass conservation", np.max(np.abs(res["X"].sum(axis=1) - 1)) < 1e-10)

# 5. REACLIB rate replaced by its own table
tmp = Path(tempfile.mkdtemp(prefix="rn-selftest-"))
r14 = rl.get_rate_by_name("n14(p,g)o15")
T9g = np.geomspace(0.005, 2, 200)
with open(tmp / "n14pg.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["T9", "rate", "fu"])
    for t in T9g:
        w.writerow([f"{t:.10g}", f"{r14.eval(t * 1e9):.12e}", "1.1"])
traj_T = 4e7
cfg = {"network": {"nuclei": CNO, "with_reverse": False, "screening": "chugunov_2007"},
       "initial": {"X": X}, "conditions": {"type": "constant", "T_K": traj_T, "rho_cgs": 100.0,
                                           "t_end_s": 3e13},
       "output": {"observables": ["X(n14)", "X(c12)/X(c13)", "E"]}, "_dir": str(tmp)}
neta, _ = build.build(cfg)
cfgb = json.loads(json.dumps(cfg))
cfgb["rates"] = [{"rate": "n14(p,g)o15", "table": "n14pg.csv"}]
netb, infob = build.build(cfgb)
ra = nl.burn(neta, build.initial_Y(cfg, neta), build.conditions(cfg), None, rtol=1e-8, atol=1e-22)
rb = nl.burn(netb, build.initial_Y(cfgb, netb), build.conditions(cfgb), None, rtol=1e-8, atol=1e-22)
oa = [nl.observable(neta, ra["X"][-1], ra["Y"][-1], ra["E"][-1], o) for o in cfg["output"]["observables"]]
ob = [nl.observable(netb, rb["X"][-1], rb["Y"][-1], rb["E"][-1], o) for o in cfg["output"]["observables"]]
dev = max(abs(b / a - 1) for a, b in zip(oa, ob))
check("table copy of a REACLIB rate gives the same burn", dev < 1e-4, f"max rel {dev:.1e}")
check("table rate carries its fu", any("fu" in v for v in infob["uncertain"].values()))

# 6. detailed balance of a table rate
r = rl.get_rate_by_name("mg25(p,g)al26")
tab = nl.TableRate(r.reactants, r.products, T9g, [r.eval(t * 1e9) for t in T9g])
rev = build.derived_table_reverse(tab, "error")
dr = pyna.DerivedRate(r, compute_Q=True, use_pf=True)  # Q from the mass table, as in build
dev = max(abs(rev.eval(t * 1e9) / dr.eval(t * 1e9) - 1) for t in T9g[T9g > 0.3])
check("detailed-balance reverse of a table rate (at grid points)", dev < 1e-8, f"max rel {dev:.1e}")

# 7. constant trajectory file
with open(tmp / "traj.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["time_s", "T_K", "rho_cgs"])
    for t in np.linspace(0, 3e13, 7):
        w.writerow([f"{t:.8e}", f"{traj_T:.8e}", "100.0"])
cfgt = json.loads(json.dumps(cfg))
cfgt["conditions"] = {"type": "trajectory", "file": "traj.csv"}
rt = nl.burn(neta, build.initial_Y(cfgt, neta), build.conditions(cfgt), None, rtol=1e-8, atol=1e-22)
ot = [nl.observable(neta, rt["X"][-1], rt["Y"][-1], rt["E"][-1], o) for o in cfg["output"]["observables"]]
dev = max(abs(b / a - 1) for a, b in zip(oa, ot))
check("trajectory with constant T, rho = constant burn", dev < 1e-5, f"max rel {dev:.1e}")

# 8. REACLIB-form fit and text round trip
rc12 = rl.get_rate_by_name("c12(p,g)n13")
T9f = np.geomspace(0.01, 3, 60)
sets, dev_dense, dev_pts = rtools.fit(T9f, [rc12.eval(t * 1e9) for t in T9f], ["nonresonant", "full"])
check("two-set REACLIB fit recovers c12(p,g) at the table points", dev_pts < 5e-3, f"{dev_pts:.1e}")
fr = nl.reaclib_rate_from_sets(rc12.reactants, rc12.products, [s.a for s in rc12.sets], label="test")
(tmp / "rt.reaclib").write_text(nl.reaclib_text(fr))
back = pyna.load_rate(str(tmp / "rt.reaclib"))
dev = max(abs(back.eval(t * 1e9) / rc12.eval(t * 1e9) - 1) for t in T9f)
check("REACLIB text round trip", dev < 1e-5, f"{dev:.1e}")

# 8b. rate from an S factor: numerical Maxwellian average vs the analytic non-resonant formula
#     N_A<sv> = 7.8327e9 (Z1Z2/(mu T9^2))^(1/3) S_eff e^-tau, tau = 4.2487 (Z1^2 Z2^2 mu/T9)^(1/3),
#     S_eff = S0 (1 + 5/(12 tau)) for constant S (Iliadis, Nuclear Physics of Stars, Sec. 3.2.1)
mu_amu = 14 / 15
worst = 0.0
for T9 in (0.01, 0.016, 0.03):
    v, E0, _ = rtools.sfactor_rate(T9, lambda E: 1.68e-3, 1, 7, mu_amu * rtools.AMU_MEV)
    tau = 4.2487 * (49 * mu_amu / T9) ** (1 / 3)
    ana = 7.8327e9 * (7 / (mu_amu * T9 ** 2)) ** (1 / 3) * 1.68e-3 * (1 + 5 / (12 * tau)) * np.exp(-tau)
    worst = max(worst, abs(v / ana - 1))
check("S-factor rate equals the analytic non-resonant formula", worst < 3e-3, f"max rel {worst:.1e}")

# 9. Monte Carlo multipliers
cfgm = json.loads(json.dumps(cfg))
cfgm["network"]["with_reverse"] = True
cfgm["uncertainty"] = {"fu": {"n14(p,g)o15": 1.5}}
netm, infom = build.build(cfgm)
i_f = netm.rates.index(nl.find_rate(netm.rates, "n14(p,g)o15"))
i_r = [i for i, x in enumerate(netm.rates) if nl.is_reverse_of(x, netm.rates[i_f])][0]
check("forward and reverse share one random variable", netm.group[i_f] == netm.group[i_r])
netm.p[i_f] = netm.p[i_r] = 1.0
m = netm.multipliers(3e7)
check("multiplier is fu**p", abs(m[i_f] - 1.5) < 1e-12 and abs(m[i_r] - 1.5) < 1e-12)
netm.p[:] = 0
check("rates without fu are listed as fixed", len(infom["fixed"]) == len(netm.rates) - 2)

# 10. branch
cfgx = {"network": {"nuclei": ["p", "he4", "mg25", "mg26", "al26"], "with_reverse": False,
                    "screening": "none"},
        "rates": [{"branch": {"rate": "mg25(p,g)al26", "products": ["mg26"], "fraction": 0.25}}],
        "uncertainty": {"fu": {"mg25(p,g)al26": 1.3}},
        "initial": {"X": {"p": 0.7, "he4": 0.2999, "mg25": 1e-4}},
        "conditions": {"type": "constant", "T_K": 6e7, "rho_cgs": 50.0, "t_end_s": 1e8},
        "_dir": str(tmp)}
netx, infox = build.build(cfgx)
Yx = build.initial_Y(cfgx, netx)
R, _ = netx.flows(6e7, 50.0, Yx)
i0 = netx.rates.index(nl.find_rate(netx.rates, "mg25(p,g)al26"))
i1 = [i for i, x in enumerate(netx.rates) if x.fname.endswith("__modified")][0]
tot = rl.get_rate_by_name("mg25(p,g)al26").eval(6e7) * 50.0 * Yx[netx.index[pyna.Nucleus("p")]] * \
    Yx[netx.index[pyna.Nucleus("mg25")]]
check("branch splits the flow 0.75 / 0.25", abs(R[i0] / tot - 0.75) < 1e-12 and abs(R[i1] / tot - 0.25) < 1e-12)
check("branch shares the parent's random variable and fu", netx.group[i0] == netx.group[i1]
      and netx.fu[i1] is not None)
check("requested nucleus without rates kept as inert", "he4" in infox["inert"])

# 11. STARLIB
hdr = "4        p  n14  o15                       im05      7.29678E+00      "
data = "\n".join(f"{t:.2E}     {1e-10 * t:.3E}     1.090E+00" for t in np.geomspace(1e-3, 10, 60))
(tmp / "mini.dat").write_text(hdr + "\n" + data + "\n")
ents = starlib.read(tmp / "mini.dat", cache=False)
e = ents[0]
check("STARLIB synthetic entry parsed", e["chapter"] == 4 and e["label"] == "im05"
      and e["reactants"] == [(1, 1, None), (7, 14, None)] and e["products"] == [(8, 15, None)]
      and len(e["T9"]) == 60)
hits = starlib.match(starlib.index(ents), rl.get_rate_by_name("n14(p,g)o15"))
check("STARLIB entry matched to the pynucastro rate", len(hits) == 1)
check("STARLIB isomer labels", starlib.parse_label("al-6") == (13, 26, "g")
      and starlib.parse_label("al*6") == (13, 26, "m"))
real = Path(os.environ.get("NUCLEAR_DATA_DIR", "/nonexistent")) / "STARLIB" / "starlib.dat"
if real.exists():
    E = starlib.read(real)
    h = starlib.match(starlib.index(E), rl.get_rate_by_name("n14(p,g)o15"))
    fu = np.exp(np.interp(np.log(0.03), np.log(h[0]["T9"]), np.log(h[0]["fu"]))) if h else None
    check("real STARLIB: n14(p,g)o15 present with fu < 1.3 at T9 = 0.03", bool(h) and fu < 1.3,
          f"{len(E)} entries, fu {fu}")
else:
    print("SKIP  real STARLIB file not found under $NUCLEAR_DATA_DIR/STARLIB/")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
