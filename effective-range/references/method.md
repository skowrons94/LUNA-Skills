# Method

## The Coulomb-modified expansion

K(E) = C0²(η) k cot δ0 + 2kη h(η) = −1/a0 + r0 k²/2 + P k⁴ + …

- C0² = 2πη/(e^{2πη} − 1) is the Gamow factor, and h(η) = Re ψ(1 + iη) − ln η.
- η = Z1Z2 e² μ/(ħ²k). Bethe (1949); Lane & Thomas, Rev. Mod. Phys. 30, 257, Sec. XI.
- Sign convention: a0 > 0 corresponds to a pole near threshold (a large positive a0 here). Some halo-EFT papers define the s-wave a0 with the opposite sign: check before comparing.
- K is unchanged by δ → δ + nπ. That is why potentials with Pauli-forbidden bound states can be compared with data through K even though their phases differ by multiples of π.

## Getting the phase

- **R-matrix fit (AZURE2).** Add a phase-shift test segment (observable `phase-shift`, J and L of the wave) on a fine c.m. grid starting at ~0.05 MeV. The result is the eigenphase of that partial wave. Below the next threshold it is the elastic phase shift. Lab energies: E_lab = E_cm / (m_target/(m_beam + m_target)). The 7Be scripts take 3He as the beam.
- **Data.** Published phase-shift analyses usually give nuclear phases relative to Coulomb. Check whether hard-sphere phases have been subtracted.
- **Models.** Phases from `cluster-potential` (`delta_curve`, radians) or `microscopic-cluster`.

## Fit choices

- Three terms (a0, r0, P) over 0.20–2.00 MeV was the 7Be recipe, used for every comparison in that study.
- The window matters because the shape term is not small at the upper edge. Report two windows, or fix the recipe once for all compared curves.
- The rms of the K fit (fm⁻¹) measures whether the expansion holds over the window.

## One-level, one-channel R-matrix

δ = −φ_0 + arctan[P R/(1 − (S − B)R)], with R = γ²/(E_λ − E), φ_0 = arctan(F/G), and boundary condition B = S(E_λ), so that E_λ is the observed energy of a narrow level. For fixed E_λ the scattering length grows with γ². `theta2_for_a0` inverts that on the branch below the threshold crossing of K.

7Be (alpha+3He, a = 4.7 fm, E_x = 8.39 MeV):

| a0 (fm) | 22 | 40 | 60 |
|---|---|---|---|
| θ² needed (ħ²/μa² units) | 2.23 | 1.55 | 0.93 |

So θ² of order one is what the measured a0 demands of a level placed where the structure calculations put it.

In a multichannel, multilevel fit the relation is approximate: use it to explain the width, not to replace the fit.
