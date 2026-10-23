# Methods

## Potential transfer

Same range, same depths per partial wave and same Coulomb radius: change Z1Z2 and the reduced mass. The 7Be depths (fitted on 3/2⁻, 1/2⁻, 7/2⁻, 5/2⁻) put the four 7Li levels within 40–130 keV, and the 0.88 MeV shift of the α threshold comes out of the Coulomb term alone. A miss beyond ~0.1 MeV for a bound state means the potential is not charge symmetric as set up (check masses and R_c).

## ANC ratio

For each geometry (range 2.5–2.9 fm, R_c 2.8–3.4 fm), fit the depth separately in each nucleus to its own binding energy, then form C²(A)/C²(B). The ratio is set by the asymptotic Coulomb and binding difference, which the geometry hardly touches.
- 7Be/7Li: ground state 1.333 ± 0.008, first excited 1.409 ± 0.009.
- Two R-matrix fits whose ANCs give a ratio far from this, as the 7Be and 7Li evaluations did (2.28), are inconsistent with charge symmetry in their bound-state normalizations.

## Reduced widths at a common radius

For an isolated level θ²(a) = Γ/(2 P_l(a) ħ²/μa²). Evaluate both mirror levels at the same set of radii and form the ratio. If the ratio does not depend on a, the radius mismatch of the fits is not the cause of a discrepancy. 7Be/7Li 1/2⁺: the ratio was 2.1 from 4.2 to 6.5 fm.

## Mirror R-matrix refit (free vs constrained)

The question: do the mirror data accept the widths of the reference nucleus? The design used for 7Li against the 7Be PRL fit:

1. **One level structure for both variants.** The mirror's own analog level, plus new levels at the reference energies shifted by the mirror displacement (start values; energies free). Every channel to be transferred is made free in the .azr (a seed width replaces an exact zero).
2. **Free variant:** everything refitted.
3. **Constrained variant:** the transferred channels are fixed at amplitudes that give the reference nucleus's formal θ² (θ²_formal per amplitude² is a fixed factor at the model's radius); level energies and everything else are refitted.
4. **Δχ² = χ²(constrained) − χ²(free)**, with the per-dataset breakdown and the energies the constrained levels move to (moving out of the data range is a way of refusing the widths).

Engineering:
- Carry the starting parameters by (kind, J^π, raw .azr energy, pair, l, s), written once by a separate process. Names shift when levels are inserted, and observed energies change with the parameters.
- One AZURE2 session per process.
- Run the two variants in parallel; each takes minutes for a ~100-parameter model with the analytic Jacobian.

## Thomas–Ehrman shifts

The difference of a mirror pair's excitation energies is mostly the difference of their thresholds. Refer each to its own relevant threshold (`threshold_shift`). The remainder is the Thomas–Ehrman shift, which is large for loosely bound s-wave nucleon states. In the 7Be/7Li 1/2⁺ pair the displacement was about 1.4 MeV in E_x but about 0.24 MeV relative to the core+nucleon thresholds. Values depend on the fit used: quote the energies with their source.
