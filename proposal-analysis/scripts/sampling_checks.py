#!/usr/bin/env python3
"""Posterior sampling checks: Kish ESS, integrated autocorrelation time,
autocorrelation growth, split R-hat and quantile stability.

    from sampling_checks import kish_ess, integrated_tau, tau_growth, split_rhat, quantile_shift
"""
import numpy as np


def kish_ess(weights):
    """Kish effective sample size (sum w)^2 / sum w^2 of importance weights."""
    w = np.asarray(weights, dtype=float)
    if np.any(w < 0) or w.sum() <= 0:
        raise ValueError("weights must be non-negative with positive sum")
    return w.sum() ** 2 / np.sum(w ** 2)


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
    A slope near 1 means tau grows in proportion to N: not converged.
    """
    x = np.atleast_2d(np.asarray(x, dtype=float))
    n = x.shape[1]
    lengths = np.array([int(f * n) for f in fractions])
    taus = np.array([integrated_tau(x[:, :k], c) for k in lengths])
    slope = np.polyfit(np.log(lengths), np.log(taus), 1)[0]
    return lengths, taus, float(slope)


def split_rhat(chains):
    """Split R-hat (Gelman et al.) for an array (chains, steps)."""
    chains = np.atleast_2d(np.asarray(chains, dtype=float))
    half = chains.shape[1] // 2
    s = np.vstack([chains[:, :half], chains[:, half:2 * half]])
    n = s.shape[1]
    w = s.var(axis=1, ddof=1).mean()
    b = n * s.mean(axis=1).var(ddof=1)
    var_plus = (n - 1) / n * w + b / n
    return float(np.sqrt(var_plus / w))


def quantile_shift(a, b, qs=(2.5, 16, 50, 84, 97.5)):
    """Quantile differences between two sample sets, in units of the 68% width of a ∪ b."""
    a = np.ravel(a)
    b = np.ravel(b)
    both = np.concatenate([a, b])
    width = np.percentile(both, 84) - np.percentile(both, 16)
    return {q: float((np.percentile(a, q) - np.percentile(b, q)) / width) for q in qs}


def ar1(n, phi, rng):
    """AR(1) chain with unit stationary variance; tau = (1 + phi) / (1 - phi)."""
    e = rng.normal(0.0, np.sqrt(1 - phi ** 2), n)
    x = np.empty(n)
    x[0] = rng.normal()
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def selftest(check):
    rng = np.random.default_rng(11)
    check("ESS of equal weights is N", abs(kish_ess(np.ones(1000)) - 1000) < 1e-9)
    w = np.ones(1000)
    w[0] = 1e6
    check("ESS of one dominant weight is ~1", kish_ess(w) < 1.01)

    phi = 0.9
    tau_true = (1 + phi) / (1 - phi)
    x = ar1(200_000, phi, rng)
    tau = integrated_tau(x)
    check(f"AR(1) tau {tau:.1f} within 10% of {tau_true:.0f}", abs(tau / tau_true - 1) < 0.10)
    _, _, slope = tau_growth(x)
    check(f"stationary chain: tau growth slope {slope:.2f} < 0.3", slope < 0.3)
    walk = np.cumsum(rng.normal(size=200_000))
    _, _, slope_w = tau_growth(walk)
    check(f"random walk: tau growth slope {slope_w:.2f} > 0.7", slope_w > 0.7)

    iid = rng.normal(size=(4, 5000))
    check("split R-hat of iid chains < 1.01", split_rhat(iid) < 1.01)
    shifted = iid + np.array([[0.0], [0.0], [0.0], [1.0]])
    check("split R-hat flags a displaced chain (> 1.1)", split_rhat(shifted) > 1.1)

    qs = quantile_shift(x[:100_000], x[100_000:])
    check("halves of a long chain agree to 0.1 of the 68% width",
          max(abs(v) for v in qs.values()) < 0.1)


if __name__ == "__main__":
    import sys
    failed = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            failed.append(name)

    selftest(check)
    print("FAIL" if failed else "PASS")
    sys.exit(1 if failed else 0)
