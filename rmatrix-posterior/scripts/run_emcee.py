#!/usr/bin/env python3
"""emcee (affine-invariant stretch move) on the same posterior, checkpointed: the baseline.

    python3 run_emcee.py --azr fit.azr --sav param.sav --cwd . --out runs/nominal \
        [--walkers 416 --steps 4000 --thin 5 --procs 4]

Walkers start from the Laplace approximation at the MAP (z ~ N(0, I) in whitened
coordinates), the best start emcee can be given.  The stretch move is affine invariant,
so whitening neither helps nor hurts it.  Progress is in <out>/emcee/chain.h5 (HDF5
backend; every --thin-th step stored, so --steps stored steps cost steps x thin
proposals).  Storage: walkers x n doubles per stored step (416 x 202 = 672 kB).
The same command resumes from the last stored state.  Rows are stored in z; settings.json
records walkers, thin and T so that compare.py maps them back with the right L.
"""
import argparse
import json
import os
import signal
import sys
import time

os.environ["OMP_NUM_THREADS"] = os.environ.get("OMP_NUM_THREADS", "1")
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from target import add_args, posterior_from_args                      # noqa: E402

ap = add_args(argparse.ArgumentParser(description=__doc__.split("\n")[0]))
ap.add_argument("--walkers", type=int, default=416)
ap.add_argument("--steps", type=int, default=4000, help="stored steps")
ap.add_argument("--procs", type=int, default=4)
ap.add_argument("--thin", type=int, default=5, help="store every k-th step")
ap.add_argument("--seed", type=int, default=20261026)
a = ap.parse_args()

_post = None


def _init():
    global _post
    signal.signal(signal.SIGINT, signal.SIG_IGN)        # the parent handles Ctrl-C
    _post = posterior_from_args(a)


def _logp(z):
    return _post.logp(z)


if __name__ == "__main__":
    import emcee
    from multiprocessing import get_context
    odir = os.path.join(a.out, "emcee")
    os.makedirs(odir, exist_ok=True)
    backend = emcee.backends.HDFBackend(os.path.join(odir, "chain.h5"))
    n = int(np.load(os.path.join(a.out, "map.npz"))["x"].size)
    settings = dict(thin=a.thin, walkers=a.walkers, temperature=a.temperature)
    sfile = os.path.join(odir, "settings.json")
    done = backend.iteration if os.path.exists(backend.filename) else 0
    if done:
        old = json.load(open(sfile))
        if old != settings:
            raise SystemExit(f"{sfile} has {old}; this run asks {settings}; use another --out")
        start = backend.get_last_sample()                 # sample(None) does not resume
        print(f"resuming at stored step {done}", flush=True)
    else:
        backend.reset(a.walkers, n)
        json.dump(settings, open(sfile, "w"))
        start = np.random.default_rng(a.seed).standard_normal((a.walkers, n))
    stop = {"flag": False}

    def _handler(signum, frame):
        stop["flag"] = True
        print(f"signal {signum}: stopping after this step (the HDF5 file is up to date)", flush=True)

    t0 = time.time()
    with get_context("spawn").Pool(a.procs, initializer=_init) as pool:
        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)
        sampler = emcee.EnsembleSampler(a.walkers, n, _logp, pool=pool, backend=backend)
        tl = time.time()
        for _ in sampler.sample(start, iterations=max(a.steps - done, 0), thin_by=a.thin,
                                progress=False, store=True):
            it = backend.iteration
            if it % 4 == 0:
                lp = backend.get_last_sample().log_prob
                print(f"stored step {it}/{a.steps} (x{a.thin})  median log p {np.median(lp):.1f}  "
                      f"{(time.time() - tl) / (4 * a.thin):.2f} s/step", flush=True)
                tl = time.time()
            if stop["flag"]:
                break
    print(f"{'stopped' if stop['flag'] else 'finished'} at stored step {backend.iteration} "
          f"[{time.time() - t0:.0f} s]", flush=True)
