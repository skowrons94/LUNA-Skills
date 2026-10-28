"""One checkpointed NUTS chain on any ``logp_grad`` target: warm-up, draws, resume.

    from chain import run_chain, load_draws
    S = run_chain(post.logp_grad, n, "runs/nominal/nuts/chain_0", warmup=500, draws=1000,
                  seed=1, chain=0, fingerprint=fid, to_x=post.x_of)

Files in ``cdir``: ``draws_NNNNN.npz`` (one chunk per checkpoint: z, x, logp and the
sampler statistics of every iteration, warm-up included and flagged) and
``state.pkl`` (position, step size, metric, dual-averaging and warm-up buffer, RNG).
Both are written atomically (temporary file + os.replace).  A chunk is written
before the state that points past it, so a kill between the two re-runs the same
iterations from the same RNG state and rewrites the same chunk: the chain stays
bit-identical.  Resume = call again with the same arguments.

``metric`` (auto, dense, diag, identity) is how each warm-up window updates the metric;
see nuts.regularized_covariance.  ``stop`` is a dict whose "flag" a signal handler may set; ``max_session`` stops after
that many iterations in this call (used by the self-test to emulate a kill).
"""
import os
import pickle

import numpy as np

from nuts import NUTS, DualAveraging, warmup_schedule, regularized_covariance


def _atomic_pickle(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump(obj, f)
    os.replace(tmp, path)


def _atomic_npz(path, **arrays):
    tmp = path + ".tmp.npz"
    np.savez(tmp, **arrays)
    os.replace(tmp, path)


def run_chain(logp_grad, dim, cdir, warmup, draws, seed, chain=0, init=None, init_scale=1.0,
              eps0=0.5, every=20, max_depth=10, target_accept=0.85, fingerprint="",
              to_x=None, stop=None, max_session=None, metric="auto", shrink_to=1.0, log=print):
    os.makedirs(cdir, exist_ok=True)
    state_path = os.path.join(cdir, "state.pkl")
    stop = stop if stop is not None else {"flag": False}
    sampler = NUTS(logp_grad, dim, max_depth=max_depth, target_accept=target_accept)
    N = warmup + draws
    wins = warmup_schedule(warmup)
    win_ends = {e: s for s, e in wins}

    if os.path.exists(state_path):
        with open(state_path, "rb") as f:
            S = pickle.load(f)
        if (S["fingerprint"] != fingerprint or S["N"] != N or S["warmup"] != warmup
                or S.get("metric") != metric):
            raise SystemExit(f"{state_path} belongs to another target or schedule; use another directory")
        rng = np.random.default_rng()
        rng.bit_generator.state = S["rng"]
        z = S["z"]
        da = DualAveraging(1.0, target_accept)
        da.load(S["da"])
        log(f"[chain {chain}] resuming at iteration {S['it']}")
    else:
        rng = np.random.default_rng([seed, chain])
        z = (np.asarray(init, float).copy() if init is not None
             else init_scale * rng.standard_normal(dim))
        S = dict(it=0, eps=eps0, Minv=np.eye(dim), buf=[], chunk=0, fingerprint=fingerprint,
                 N=N, warmup=warmup, metric=metric)
        da = DualAveraging(S["eps"], target_accept)
    sampler._set_metric(S["Minv"])
    lp, g = logp_grad(z)
    if not np.isfinite(lp):
        raise SystemExit(f"[chain {chain}] the target fails at the starting point; lower init_scale")

    rec = []

    def flush():
        if rec:
            cols = {k: np.array([r[k] for r in rec]) for k in rec[0]}
            _atomic_npz(os.path.join(cdir, f"draws_{S['chunk']:05d}.npz"), **cols)
            S["chunk"] += 1
            rec.clear()
        S.update(z=z, rng=rng.bit_generator.state, da=da.state())
        _atomic_pickle(S, state_path)

    done_here = 0
    while S["it"] < N and not stop["flag"]:
        if max_session is not None and done_here >= max_session:
            break
        it = S["it"]
        warm = it < warmup
        z, lp, g, st = sampler.transition(z, lp, g, S["eps"], rng)
        if warm:
            S["eps"] = da.update(st["accept"])
            if wins and wins[0][0] <= it < wins[-1][1]:
                S["buf"].append(z.copy())
            if it + 1 in win_ends:                          # end of a slow window: new metric
                S["Minv"] = regularized_covariance(np.array(S["buf"]), metric, shrink_to)   # 1: whitened coordinates
                sampler._set_metric(S["Minv"])
                S["buf"] = []
                da.restart(S["eps"])
            if it + 1 == warmup:
                S["eps"] = da.final()
        row = dict(z=z, logp=lp, warmup=warm, eps=S["eps"], **st)
        if to_x is not None:
            row["x"] = to_x(z)
        rec.append(row)
        S["it"] = it + 1
        done_here += 1
        if S["it"] % every == 0 or S["it"] == N:
            flush()
            log(f"[chain {chain}] it {S['it']}/{N} {'warmup' if warm else 'sample'} "
                f"log p {lp:.2f} eps {S['eps']:.3f} depth {st['depth']} accept {st['accept']:.2f}")
    flush()
    return S


def load_draws(cdir):
    """Concatenate the chunks of one chain into a dict of arrays (empty dict if none)."""
    files = sorted(f for f in os.listdir(cdir) if f.startswith("draws_") and f.endswith(".npz")
                   and ".tmp" not in f) if os.path.isdir(cdir) else []
    if not files:
        return {}
    D = [np.load(os.path.join(cdir, f)) for f in files]
    return {k: np.concatenate([d[k] for d in D]) for k in D[0].files}
