"""Spectroscopic amplitudes from a CI calculation -> R-matrix channel amplitudes (7Be study, Oct 2026).

recouple(l, j, I, J, s): j-j coupling (orbital l, nucleon j, daughter spin I, total J) to channel spin s,
    U = (-1)^(l + 1/2 + I + J) sqrt((2j+1)(2s+1)) {l 1/2 j; I J s}.  A channel amplitude is sum_j U A_j.
renormalized_sf(sf_as_built, Q, mu): cluster SF of a channel normalized to unity = as-built SF / mu_Q.
sum_rule(sfs, L): renormalized strength summed over all states of one (L, Q) channel; a complete channel gives
    the number of J values (1 for L = 0 with channel spin 1/2, else 2). The check that exposed a bad
    normalization: as-built/mu_Q gave 2.000, 0.970, 2.078 for 7Be; the code's own 'normalized' SF gave 0.083.
"""
from sympy import Rational
from sympy.physics.wigner import wigner_6j


def _half(x):
    return Rational(int(round(2 * x)), 2)


def recouple(l, j, I, J, s):
    w = wigner_6j(_half(l), _half(0.5), _half(j), _half(I), _half(J), _half(s))
    ph = (-1) ** int(round(l + 0.5 + I + J))
    return float(ph * ((2 * j + 1) * (2 * s + 1)) ** 0.5 * w)


def renormalized_sf(sf_as_built, Q, mu):
    """mu: {Q: projected norm-kernel eigenvalue}; for 0s alpha + 0s 3He: {3: 1.191, 4: 0.5955, 5: 1.1992}."""
    return sf_as_built / mu[Q]


def sum_rule(sfs, L, s=0.5):
    """Sum of renormalized SF over states and the value a complete channel should reach."""
    n_J = int(round(2 * min(L, s) + 1))
    return sum(sfs), n_J


if __name__ == "__main__":
    # unitarity of the recoupling: sum_j U^2 = 1 for each s (p + 6Li(1+), l = 1, J = 3/2)
    for s in (0.5, 1.5):
        tot = sum(recouple(1, j, 1, 1.5, s) ** 2 for j in (0.5, 1.5))
        print(f"sum_j U^2 (s = {s}) = {tot:.6f}")
    print(renormalized_sf(0.0762, 4, {4: 0.5955}))      # 7Be 1/2+_1: 0.128
