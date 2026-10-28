# Cluster-model physics and conventions

## Pauli bookkeeping (Wildermuth condition)

Two clusters in their 0s configurations, relative motion in oscillator states of N = 2n + l quanta. The compound nucleus has a minimum number of quanta N_min in its lowest shell-model configuration. For 4 < A ≤ 16 with s-shell clusters, each of the A − 4 nucleons above the 0s shell carries one quantum (`s_shell_n_min`: alpha+3He and alpha+t 3, alpha+d 2, alpha+alpha 4). Relative states with N < N_min are Pauli forbidden. A deep local potential represents them as bound states that must be present (and are not physical). The physical state of a wave with forbidden states below it has n = number of forbidden states nodes.

alpha+3He (N_min = 3):

| l | forbidden N | lowest allowed | nodes of physical state | band |
|---|---|---|---|---|
| 0 | 0, 2 | N = 4 | 2 | positive parity (1/2+) |
| 1 | 1 | N = 3 | 1 | ground-state band (3/2−, 1/2−) |
| 2 | 2 | N = 4 | 1 | positive parity (3/2+, 5/2+) |
| 3 | — | N = 3 | 0 | ground-state band (7/2−, 5/2−) |
| 4 | — | N = 4 | 0 | positive parity (7/2+, 9/2+) |

## Norm kernel and parity dependence

Antisymmetrizing an N-quantum relative state of two 0s clusters returns it times
mu_N = Σ_k (−1)^k w_k (1 − kA/(A1A2))^N (Horiuchi, PTP Suppl. 62, 90 (1977)), where k nucleons are exchanged and w_k counts label-matching exchanges. For alpha + an s-shell cluster x, w_k = C(A_x, k).
- mu_N = 0 for every N < N_min. This is a check on the formula, not an input.
- For alpha+3He: mu_3 = 343/288 = 1.19097, mu_4 = 343/576 = 0.59549, mu_5 = 1.19924, mu_6 = 0.80639 (Horiuchi Eq. 4·1·12; a CI calculation with projected cluster channels gives the same, Volya 2026). mu_N alternates between odd and even N; the k = A_x term, −(1 − A/A1)^N, carries the sign (−1)^N. mu_N is a normalization: it multiplies the energy and kinetic terms of the Hamiltonian kernel, and the force enters through a separate exchange term (Horiuchi Eq. 4·2·8). Neither Horiuchi nor Saito reads mu_N > 1 or < 1 as a stronger or weaker interaction; do not either.
- Spectroscopic factors of cluster channels: a channel normalized to unity has SF = SF(as built) / mu_Q, with Q the oscillator quanta. A shell-model 'normalized' SF that does not follow this (7Be FSU files: old/new = 6.95 at Q = 4 instead of 1/0.5955) included spurious centre-of-mass states; use the as-built SF (see `shell-model`, amplitudes-to-widths).
- Consequence: one local potential cannot describe both parities. Fitted to negative parity, it is too attractive in positive parity. The 7Be study needed the positive-parity (N = 4) depth 17.5 ± 1.9 MeV shallower, nearly the same for l = 0 and l = 2, which is the signature of a shell-dependent (nonlocal exchange) correction rather than an l-dependent one.

### Pauli-forbidden states as a repulsive core

In the orthogonality-condition model (Saito, PTP 41, 705 (1969)) the relative wave function is kept orthogonal to the forbidden states. This fixes energy-independent inner nodes and pushes the wave out "as if a hard core existed"; the core shrinks with energy. For the alpha+3He s wave (forbidden 0s, 1s relative states; relative oscillator length b_nuc/sqrt(12/7)), Coulomb plus orthogonality and no attraction (`ocm_phase`) gives a0 = 21–26 fm and an equivalent hard sphere of 2.65–2.90 fm at 1 MeV for b_nuc = 1.30–1.42 fm, and δ0 = −43 to −49° at 3.56 MeV. That matches the hard sphere of 2.8 fm of the phase-shift analysis (Tombrello and Parker, Phys. Rev. 130, 1112 (1963): δ0 = −45° at 3.56 MeV) and the outermost node at 2.5 fm of Kajino's RGM (NPA 460, 559 (1986)). The data are more repulsive at threshold (3.2–3.3 fm, a0 ≈ 36 fm), as the antisymmetrized calculations are (`microscopic-cluster`), and less repulsive above 5 MeV: the force acts at both ends. Use this test before attributing a repulsive s wave to the Pauli principle.

A parity-dependent (Majorana) potential, V_l = −[V_W + (−1)^l V_M] exp(−(r/a)^2), fixes the odd-l depth on negative-parity levels and the even-l depth on one positive-parity datum (e.g. the scattering length). Everything else is a prediction. It reproduces a0 but not necessarily r0 (7Be: r0 = 1.34 fm against 1.03 from the R-matrix). The effective range needs the nonlocal kernel (`microscopic-cluster`).

## Potential and numerics

- Gaussian well −V0 exp(−(r/a)^2) plus the Coulomb potential of a uniform sphere of radius R_c. 7Be values: a = 2.6883 fm (fixed on the N = 3 band), R_c = 3.095 fm.
- Bound states: finite differences in a 40 fm box, N = 4000 (energies to ~1 keV for light systems); nodes counted on the eigenvector.
- Scattering: Numerov to r_max = 14 fm, matched to F_l, G_l (mpmath, cached). Check that the phase does not change when r_max moves (14 to 25 fm).
- ANC: u(r_match)/W_{−η,l+1/2}(2kr_match) with r_match beyond the nuclear range (8 fm for alpha+3He). Check stability against r_match.

## R-matrix quantities

- P_l = ka/(F² + G²), S_l = a(FF' + GG')/(F² + G²) at the channel radius a.
- Wigner unit γ_W² = ħ²/(μa²). Some papers use the Teichmann–Wigner limit (3/2)ħ²/(μa²): say which.
- For an isolated level, θ² = Γ/(2 P γ_W²) (`theta2_from_width`). For a multilevel fit in the Brune parameterization the observed widths are not simple: take θ² from the fit code (AZURE2 `dimensionless_widths`).
- Single-particle reduced width of a bound potential state: γ² = (ħ²/2μa) u(a)² with u normalized (`sp_reduced_width`).

## Two-channel coupled partitions (not shipped; method)

To ask whether coupling to another partition (e.g. 6Li + p) creates a resonance in the cluster channel:
- Use a matrix Numerov with channel-dependent reduced masses and thresholds.
- Use the fitted cluster potential in channel 1 with no freedom, and a Woods–Saxon in channel 2 placed where the shell model puts the doorway.
- Scan the coupling strength, so that no conclusion rests on an unmeasured form factor.
- Validate that zero coupling reproduces the single-channel phase exactly.

7Be result: no well depth and no coupling made a 1/2+ resonance in either channel. The s wave went from 23° to 40° between zero and 30 MeV coupling. Reference implementation: the 7Be study's `coupled-channels/cc/cc2.py`.
