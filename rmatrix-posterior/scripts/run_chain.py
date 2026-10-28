#!/usr/bin/env python3
"""One checkpointed NUTS chain on the AZURE2 posterior (whitened with map.npz).

    OMP_NUM_THREADS=1 python3 run_chain.py --azr fit.azr --sav param.sav --cwd . \
        --out runs/nominal --chain 0 [--warmup 500 --draws 1000 --max-depth 8]

Output in <out>/nuts/chain_<k>/ (chain.py): draws_NNNNN.npz and state.pkl, written
atomically every --every iterations and on SIGINT/SIGTERM.  Stop at any time (Ctrl-C,
kill); run the same command again to continue.  Run several chains as separate
single-thread processes (run_all.sh): log p does not speed up with threads.
"""
import argparse
import os
import signal
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from target import add_args, posterior_from_args, fingerprint          # noqa: E402
from chain import run_chain                                             # noqa: E402

ap = add_args(argparse.ArgumentParser(description=__doc__.split("\n")[0]))
ap.add_argument("--chain", type=int, required=True)
ap.add_argument("--warmup", type=int, default=500)
ap.add_argument("--draws", type=int, default=1000)
ap.add_argument("--init-scale", type=float, default=1.0,
                help="start at z ~ N(0, s^2 I): s = 1 is a draw from the Laplace approximation")
ap.add_argument("--max-depth", type=int, default=8)
ap.add_argument("--target-accept", type=float, default=0.85)
ap.add_argument("--metric", default="auto", choices=["auto", "dense", "diag", "identity"],
                help="warm-up metric update; dense needs >= 10 draws per dimension per window")
ap.add_argument("--every", type=int, default=20, help="checkpoint interval (iterations)")
ap.add_argument("--seed", type=int, default=20261026)
a = ap.parse_args()

stop = {"flag": False}


def _handler(signum, frame):
    stop["flag"] = True
    print(f"[chain {a.chain}] signal {signum}: checkpointing after this iteration", flush=True)


signal.signal(signal.SIGINT, _handler)
signal.signal(signal.SIGTERM, _handler)

t0 = time.time()
post = posterior_from_args(a)
print(f"[chain {a.chain}] model loaded in {time.time() - t0:.0f} s: {post.n} free parameters, "
      f"{post.prior_idx.size} Gaussian prior terms, transformability prior "
      f"{'on' if post.phys else 'off'}, objective at the MAP {post.objective(post.x_ref):.2f}", flush=True)
fid = fingerprint(post) + f"|T={a.temperature}"
S = run_chain(post.logp_grad, post.n, os.path.join(a.out, "nuts", f"chain_{a.chain}"),
              warmup=a.warmup, draws=a.draws, seed=a.seed, chain=a.chain, init_scale=a.init_scale,
              every=a.every, max_depth=a.max_depth, target_accept=a.target_accept,
              fingerprint=fid, to_x=post.x_of, stop=stop, metric=a.metric,
              log=lambda s: print(s, f"[{time.time() - t0:.0f} s]", flush=True))
print(f"[chain {a.chain}] {'stopped' if stop['flag'] else 'finished'} at iteration {S['it']}", flush=True)
