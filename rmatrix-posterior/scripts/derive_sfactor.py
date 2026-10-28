#!/usr/bin/env python3
"""A derived quantity on thinned posterior draws: S(0) from one AZURE2 test segment.

For each draw, S(E) on the <segmentsTest> grid with key --key (R-matrix block of the draw
only), then S(0) from a polynomial of order --order fitted below --emax (c.m. MeV).  The
recipe must be the one the paper uses for the adopted fit: compare variants with one
method.  Results are cached per sampler in <out>/sfactor_<sampler>.npz, so the script can
be stopped and rerun.

    python3 derive_sfactor.py --azr fit.azr --cwd . --out runs/nominal --key 113 \
        [--emax 0.30 --order 2 --scale 1e3 --every-nuts 5 --emcee-draws 2000]
"""
import argparse
import glob
import json
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "4")
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from target import whitening                                           # noqa: E402
from chain import load_draws                                           # noqa: E402

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--azr", required=True)
ap.add_argument("--cwd", default=None)
ap.add_argument("--out", required=True)
ap.add_argument("--key", type=int, required=True, help="<segmentsTest> key of the S-factor grid")
ap.add_argument("--emax", type=float, default=0.30)
ap.add_argument("--order", type=int, default=2)
ap.add_argument("--scale", type=float, default=1.0, help="multiply S (MeV b) by this, e.g. 1e3 for keV b")
ap.add_argument("--every-nuts", type=int, default=5)
ap.add_argument("--emcee-draws", type=int, default=2000)
ap.add_argument("--burn", type=int, default=None, help="emcee burn-in (default: compare.json)")
a = ap.parse_args()
from pyazr import azure2, trimmed_model                                # noqa: E402

cwd = a.cwd or os.path.dirname(os.path.abspath(a.azr))
ref = np.load(os.path.join(a.out, "map.npz"))
names = [str(s) for s in ref["names"]]
nR = sum(1 for n in names if n.startswith(("energy", "width")))
assert all(n.startswith(("energy", "width")) for n in names[:nR]), "R-matrix block must come first"


def draw_sets():
    sets = {}
    X = [c["x"][~c["warmup"]] for c in (load_draws(d) for d in
                                         sorted(glob.glob(os.path.join(a.out, "nuts", "chain_*")))) if c]
    if X:
        sets["nuts"] = np.concatenate(X)[::a.every_nuts]
    h5 = os.path.join(a.out, "emcee", "chain.h5")
    if os.path.exists(h5):
        import emcee
        be = emcee.backends.HDFBackend(h5, read_only=True)
        burn = a.burn
        if burn is None:
            cj = os.path.join(a.out, "compare.json")
            burn = json.load(open(cj))["emcee"]["burn"] if os.path.exists(cj) else be.iteration // 2
        st = json.load(open(os.path.join(a.out, "emcee", "settings.json")))
        Z = be.get_chain(discard=burn, flat=True)
        idx = np.random.default_rng(0).choice(len(Z), min(a.emcee_draws, len(Z)), replace=False)
        sets["emcee"] = ref["x"] + Z[idx] @ whitening(ref["H"], st.get("temperature", 1.0))[0].T
    sets["map"] = ref["x"][None, :]
    sets["best"] = ref["x_best"][None, :]
    return sets


wd = os.path.join(a.out, "sfactor_grid")
os.makedirs(wd, exist_ok=True)
tmp, _ = trimmed_model(a.azr, keys=[a.key], cwd=cwd, workdir=wd)
try:
    with azure2(tmp, cwd=cwd) as m:
        m.extrap_mode()
        E = lo = None
        for name, X in draw_sets().items():
            cache = os.path.join(a.out, f"sfactor_{name}.npz")
            s0 = list(np.load(cache)["s0"][:len(X)]) if os.path.exists(cache) else []
            for i in range(len(s0), len(X)):
                v = np.asarray(X[i][:nR], float)
                if E is None:
                    E = np.asarray(m.calculate_energies(v)[0], float)
                    lo = E <= a.emax
                S = np.asarray(m.calculate_sfactor_rwa(v)[0], float) * a.scale
                s0.append(float(np.polyval(np.polyfit(E[lo], S[lo], a.order), 0.0)))
                if (i + 1) % 200 == 0:
                    np.savez(cache, s0=np.array(s0))
            s0 = np.array(s0)
            np.savez(cache, s0=s0)
            q = np.percentile(s0, [16, 50, 84])
            print(f"{name:6s} n={len(s0):5d}  S(0) mean {s0.mean():.5g} sd {s0.std():.3g}; "
                  f"median {q[1]:.5g} (+{q[2] - q[1]:.3g} -{q[1] - q[0]:.3g})", flush=True)
finally:
    os.remove(tmp)
