#!/usr/bin/env python3
"""Posterior sampling checks: Kish ESS, Pareto k-hat of importance weights,
integrated autocorrelation time, autocorrelation growth, split R-hat and
quantile stability with its sampling-noise baseline.

    from sampling_checks import (kish_ess, pareto_khat, integrated_tau, tau_growth,
                                 split_rhat, split_rhat_classic, quantile_shift)

    python sampling_checks.py [--seed S]    # self-test
"""
import numpy as np
from scipy import stats


def kish_ess(weights):
    """Kish effective sample size (sum w)^2 / sum w^2 of importance weights."""
    w = np.asarray(weights, dtype=float)
    if np.any(w < 0) or w.sum() <= 0:
        raise ValueError("weights must be non-negative with positive sum")
    return w.sum() ** 2 / np.sum(w ** 2)


def _gpd_khat(x):
    """Shape k of a generalized Pareto fit to sorted positive exceedances (Zhang & Stephens 2009,
    with the weak prior used in PSIS, Vehtari et al. 2024)."""
    n = len(x)
    m = 30 + int(np.sqrt(n))
    b = 1 - np.sqrt(m / (np.arange(1, m + 1) - 0.5))
    b = b / (3 * x[int(n / 4 + 0.5) - 1]) + 1 / x[-1]
    k = np.mean(np.log1p(-b[:, None] * x), axis=1)
    ll = n * (np.log(-b / k) - k - 1)
    wts = 1 / np.sum(np.exp(ll - ll[:, None]), axis=1)
    b_post = np.sum(b * wts) / np.sum(wts)
    k_post = np.mean(np.log1p(-b_post * x))
    return float((n * k_post + 10 * 0.5) / (n + 10))


def pareto_khat(weights):
    """Pareto k-hat diagnostic of importance weights (PSIS tail fit).

    k-hat < 0.5: reliable; 0.5-0.7: usable with care; > 0.7: the weighted estimate is unreliable
    even when the Kish ESS looks acceptable.
    """
    w = np.asarray(weights, dtype=float)
    if np.any(w < 0) or w.sum() <= 0:
        raise ValueError("weights must be non-negative with positive sum")
    w = np.sort(w / w.max())
    s = len(w)
    m = int(np.ceil(min(0.2 * s, 3 * np.sqrt(s))))
    if m < 5:
        raise ValueError("too few weights for a tail fit")
    x = w[-m:] - w[-m - 1]
    x = x[x > 0]
    return _gpd_khat(x) if len(x) >= 5 else float("inf")


def _autocorr(x):
    x = np.asarray(x, dtype=float) - np.mean(x)
    n = len(x)
    size = 1 << (2 * n - 1).bit_length()
    f = np.fft.rfft(x, size)
    acf = np.fft.irfft(f * np.conj(f), size)[:n]
    return acf / acf[0]


def integrated_tau(x, c=5.0):
    """Integrated autocorrelation time with Sokal's automatic window (M >= c tau).

    x: 1-d chain, or 2-d array (walkers, steps); for 2-d the autocorrelation
    functions are averaged over walkers before windowing.
    """
    x = np.atleast_2d(np.asarray(x, dtype=float))
    rho = np.mean([_autocorr(row) for row in x], axis=0)
    taus = 2.0 * np.cumsum(rho) - 1.0
    m = np.arange(len(taus))
    ok = m >= c * taus
    window = np.argmax(ok) if np.any(ok) else len(taus) - 1
    return float(taus[window])


def tau_growth(x, fractions=(0.25, 0.5, 1.0), c=5.0):
    """tau estimated on growing prefixes of the chain(s).

    Returns (lengths, taus, slope) where slope is d log tau / d log N.
    A slope near 1 means tau grows in proportion to N: not converged. The test is
    meaningful only once the shortest prefix is already >~ 50 tau; below that the
    estimate grows even for a converged chain.
    """
    x = np.atleast_2d(np.asarray(x, dtype=float))
    n = x.shape[1]
    lengths = np.array([int(f * n) for f in fractions])
    taus = np.array([integrated_tau(x[:, :k], c) for k in lengths])
    slope = np.polyfit(np.log(lengths), np.log(taus), 1)[0]
    return lengths, taus, float(slope)


def _rhat(chains):
    n = chains.shape[1]
    w = chains.var(axis=1, ddof=1).mean()
    b = n * chains.mean(axis=1).var(ddof=1)
    return float(np.sqrt(((n - 1) / n * w + b / n) / w))


def _split(chains):
    chains = np.atleast_2d(np.asarray(chains, dtype=float))
    half = chains.shape[1] // 2
    return np.vstack([chains[:, :half], chains[:, half:2 * half]])


def _rank_normalize(s):
    r = stats.rankdata(s, method="average").reshape(s.shape)
    return stats.norm.ppf((r - 0.375) / (s.size + 0.25))


def split_rhat_classic(chains):
    """Classic split R-hat (Gelman et al.) for an array (chains, steps)."""
    return _rhat(_split(chains))


def split_rhat(chains):
    """Rank-normalized split R-hat (Vehtari et al. 2021): max of the bulk and folded values.

    chains: (chains, steps) from independent runs with dispersed starts. The walkers of one
    ensemble sampler are coupled and are not independent chains. Threshold: 1.01.
    """
    s = _split(chains)
    bulk = _rhat(_rank_normalize(s))
    folded = _rhat(_rank_normalize(np.abs(s - np.median(s))))
    return max(bulk, folded)


def _density(x, p):
    """Density at the p-quantile from the spacing of neighbouring quantiles."""
    h = min(0.02, p / 2, (1 - p) / 2)
    lo, hi = np.quantile(x, [p - h, p + h])
    return 2 * h / max(hi - lo, 1e-300)


def quantile_shift(a, b, qs=(2.5, 16, 50, 84, 97.5), tau_a=1.0, tau_b=1.0):
    """Quantile differences between two sample sets with their sampling-noise baseline.

    Returns {q: (shift, se)}, both in units of the 68% width of a and b pooled. se is the expected
    standard error of the difference for independent sets with integrated autocorrelation times
    tau_a and tau_b: sqrt(p (1 - p) (tau_a / N_a + tau_b / N_b)) / pdf(x_p). A shift is
    significant only relative to se; halves of one chain are treated as independent.
    """
    a = np.ravel(a)
    b = np.ravel(b)
    both = np.concatenate([a, b])
    width = np.percentile(both, 84) - np.percentile(both, 16)
    out = {}
    for q in qs:
        p = q / 100
        se = np.sqrt(p * (1 - p) * (tau_a / len(a) + tau_b / len(b))) / _density(both, p)
        out[q] = (float((np.percentile(a, q) - np.percentile(b, q)) / width), float(se / width))
    return out


def ar1(n, phi, rng):
    """AR(1) chain with unit stationary variance; tau = (1 + phi) / (1 - phi)."""
    e = rng.normal(0.0, np.sqrt(1 - phi ** 2), n)
    x = np.empty(n)
    x[0] = rng.normal()
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def selftest(check, seed=11):
    rng = np.random.default_rng(seed)
    check("ESS of equal weights is N", abs(kish_ess(np.ones(1000)) - 1000) < 1e-9)
    w = np.ones(1000)
    w[0] = 1e6
    check("ESS of one dominant weight is ~1", kish_ess(w) < 1.01)
    k_heavy = pareto_khat(rng.pareto(1.0, 40000) + 1)   # weights with tail index 1: true k = 1
    k_light = pareto_khat(rng.pareto(5.0, 40000) + 1)   # true k = 0.2
    check(f"Pareto k-hat: heavy-tailed weights {k_heavy:.2f} > 0.7, light-tailed {k_light:.2f} < 0.5",
          k_heavy > 0.7 and k_light < 0.5)

    phi = 0.9
    tau_true = (1 + phi) / (1 - phi)
    x = ar1(200_000, phi, rng)
    tau = integrated_tau(x)
    check(f"AR(1) tau {tau:.1f} within 10% of {tau_true:.0f}", abs(tau / tau_true - 1) < 0.10)
    _, _, slope = tau_growth(x)
    check(f"stationary chain: tau growth slope {slope:.2f} < 0.3", slope < 0.3)
    walk = np.cumsum(rng.normal(size=(32, 20_000)), axis=1)   # 32 independent random walks
    _, _, slope_w = tau_growth(walk)
    check(f"random walks: tau growth slope {slope_w:.2f} > 0.7", slope_w > 0.7)

    iid = rng.normal(size=(4, 5000))
    check(f"rank-normalized split R-hat of iid chains {split_rhat(iid):.4f} < 1.01", split_rhat(iid) < 1.01)
    shifted = iid + np.array([[0.0], [0.0], [0.0], [1.0]])
    check(f"split R-hat flags a chain displaced by 1 sd ({split_rhat(shifted):.3f} > 1.05)", split_rhat(shifted) > 1.05)
    wide = iid * np.array([[1.0], [1.0], [1.0], [3.0]])
    check(f"folded R-hat flags a chain with a different scale ({split_rhat(wide):.3f} > 1.05; "
          f"classic {split_rhat_classic(wide):.3f})", split_rhat(wide) > 1.05)

    qs = quantile_shift(x[:100_000], x[100_000:], tau_a=tau, tau_b=tau)
    check("halves of a long chain agree to 0.1 of the 68% width and within 4 baseline s.e.",
          max(abs(s) for s, _ in qs.values()) < 0.1 and max(abs(s / e) for s, e in qs.values()) < 4)
    z = np.array([[s / e for s, e in quantile_shift(rng.normal(size=2000), rng.normal(size=2000)).values()]
                  for _ in range(400)])
    spread = z.std(axis=0)
    check(f"quantile-shift baseline calibrated on iid pairs (sd of shift/se {spread.min():.2f}-{spread.max():.2f})",
          np.all((spread > 0.8) & (spread < 1.2)))


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    failed = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            failed.append(name)

    selftest(check, a.seed)
    print("FAIL" if failed else "PASS")
    sys.exit(1 if failed else 0)
