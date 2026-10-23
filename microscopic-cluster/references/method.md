# Method

## Model

- **Clusters.** Brink 0s Slater determinants of a common oscillator width b. Cluster 1 sits at +A2/A·R and cluster 2 at −A1/A·R, so the centre of mass is at the origin for every generator coordinate R. The c.m. kinetic energy 3ħ²/(4mb²) is subtracted.
- **Force.** Minnesota: V_R = 200 MeV, κ_R = 1.487 fm⁻²; V_t = −178 MeV, κ_t = 0.639 fm⁻²; V_s = −91.85 MeV, κ_s = 0.465 fm⁻². Exchange mixture [u/2 + (2 − u)/2 P_r]. Coulomb between protons with the error-function form for Gaussian charge distributions. ħ²/m = 41.4711 MeV fm² (Minnesota convention).
- **Projection.** The kernels between determinants come from the Löwdin formulas and are projected on l by Gauss–Legendre integration over the angle between R and R′ (96 points). There is no spin–orbit term, so J = l ± s are degenerate: compare with both members, or with their centroid.
- **Linearity.** H(u) = H(0) + u[H(1) − H(0)]: build twice, interpolate.

## Microscopic R-matrix (Baye, Heenen & Libert-Heinemann 1977)

- Inside the channel radius a, the full antisymmetrized kernels. Outside, the relative motion under point Coulomb; the external parts of the kernels are subtracted by quadrature of the projected relative Gaussians.
- The Bloch operator (B = 0) restores hermiticity, and the residual asymmetry is reported (`asym`).
- Pauli-forbidden combinations are removed by diagonalizing the internal norm kernel and keeping eigenvalues above eps·max (1e-7).
- The R-matrix is matched to F, G at a: tan δ = −(F − R x F′)/(G − R x G′).
- Use a beyond the range of exchange: 8 fm for α+³He, checked between 7 and 9 fm.

## Fixing u

Take one negative-parity datum, either:
- the l = 1 bound-state centroid, (2J+1)-weighted: (4·E(3/2⁻) + 2·E(1/2⁻))/6 relative to threshold; or
- the 90° crossing of the l = 3 phase at the (7/2⁻, 5/2⁻) resonance centroid.

The two choices bracket the systematic. The 7Be values:

| b (fm) | fixed on | u | a0 (fm) | r0 (fm) |
|---|---|---|---|---|
| 1.30 | p | 0.960 | 36.5 | 1.01 |
| 1.30 | f | 1.003 | 35.0 | 1.00 |
| 1.36 | p | 0.981 | 40.6 | 1.03 |
| 1.36 | f | 1.006 | 39.7 | 1.02 |
| 1.42 | p | 1.000 | 45.0 | 1.04 |
| 1.42 | f | 1.008 | 44.7 | 1.04 |

b = 1.42 fm reproduces both negative-parity data at once (u = 1.000 against 1.008).

## Norm kernel

At small R the projected norm kernel of the l = N wave tends to μ_N times the direct overlap. For α+x it equals Σ_k (−1)^k C(A_x, k)(1 − kA/(4A_x))^N. This is the cleanest correctness test of a new system: μ_N = 0 for every N below N_min.
