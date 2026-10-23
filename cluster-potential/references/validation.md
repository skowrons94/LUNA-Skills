# Validation ladder

Record each rung in the study's report. A depth that reproduces one level proves only that the bisection converged.

| Rung | Check | How | Proves | Does not prove |
|---|---|---|---|---|
| 0 | Library | `scripts/selftest.py` prints PASS | node counting, mu_N, Coulomb limit, 7Be/7Li known answers | that your system is set up right |
| 1 | Admissibility | `pauli_ok` for every fitted wave; node number of the physical state as in the table of physics.md | the potential is a cluster potential, not a shallow fit | that the depth is right |
| 2 | Numerics | phase stable when r_max moves 14 → 25 fm; bound energy stable when the box doubles; ANC stable against r_match | the numbers are converged | — |
| 3 | Fitted levels | every level used to fix a depth is reproduced (by construction) and listed | bookkeeping | predictive power |
| 4 | Unfitted predictions | widths of resonances, ANCs, other band members against data. 7Be: f-wave widths within 30 %, ground-state C² = 23.0 fm⁻¹ against 20–27 in the literature, none fitted | the model has content | parity transfer |
| 5 | Mirror | the same depths in the mirror (`mirror-nucleus`). 7Be → 7Li: four levels to 40–130 keV, no parameter refitted | the potential is charge symmetric where it should be | exchange effects |
| 6 | Other parity | positive-parity phases, or the scattering length, against data or a microscopic calculation | whether a local potential is adequate | — |

Rungs 0–3 always. Rung 4 before quoting a model width or ANC. Rung 6 before using the model for the other parity.

## Lessons that changed results (7Be study)

- **A local potential fitted to negative parity gives the wrong sign of a0 for the s wave** (−31 fm against +22 to +60 fm measured). The fix is shell dependent (−17.5 MeV for the whole N = 4 shell), not l dependent. Do not use the negative-parity depth for positive-parity extrapolations.
- **A repulsive core is an alternative to a shallower well, within limits.** A +49 MeV, 1.0 fm Gaussian core reproduced the s wave equally well. Longer-range cores unbound a forbidden state and were excluded by rung 1.
- **No positive-parity alpha+3He resonance at any reasonable depth.** The s wave peaked at 23° and the d waves at 56° and 46° without crossing 90°. A large R-matrix α width on a positive-parity level is then a background statement, not a cluster state.
- **The ANC ratio of mirrors is robust; individual ANCs are not.** C² varied by 68 % over range 2.50–2.90 fm and R_c 2.8–3.4 fm. The 7Be/7Li ratio held to 1 % (`mirror-nucleus`).
