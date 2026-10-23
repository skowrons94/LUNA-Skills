# Validation ladder

| Rung | Check | How | Proves | Does not prove |
|---|---|---|---|---|
| 0 | Kernels | `selftest.py` PASS: μ_3, μ_4 at small R; large-R norm → direct overlap; E_α = −24.283 MeV at b = 1.36 | Löwdin algebra, projection, c.m. removal | the scattering |
| 1 | End to end | `selftest.py --full`: u = 0.9809, a0 = 40.6 fm | the R-matrix and the u fit reproduce the 7Be study | your system |
| 2 | Numerics | phases stable to ~0.1° for a = 7–10 fm and eps = 1e-6/1e-7; generator step and R_max (a0 to 0.5 %) | no numerical artefact | — |
| 3 | Fixed datum | the negative-parity datum used for u is reproduced; the other one predicted (7Be: the f-wave resonance came at 4.07–4.91 MeV when u was fixed on the p wave, against 3.91 measured) | the force is sensible | the other parity |
| 4 | Robustness | three b values × two u data | the spread is the model uncertainty | — |
| 5 | Comparison | positive-parity phases against the R-matrix eigenphases or data below the next threshold, via the same ERE recipe | the prediction | anything about states outside the cluster partition |

## Lessons that changed results (7Be study)

- **The antisymmetrized continuum alone reproduces the measured s wave.** With nothing adjusted in positive parity it gave a0 = 35–45 fm, r0 = 1.00–1.04 fm and s-wave phases within 1–3.5° of the R-matrix fit. A large α width on the R-matrix 1/2⁺ level is therefore continuum physics, not a spectroscopic factor.
- **The local Majorana potential gets a0 but not r0** (1.34 fm). The nonlocal exchange kernel fixes r0: quote both.
- **No positive-parity α+³He resonance appears**, consistent with the NCSMC (Vorabbi 2019) and with the ⁷Li finding (Herko 2026) that the 1/2⁺ is absent when only the binary-cluster basis is kept. A state that is present in the R-matrix fit must then be built on another partition (⁶Li ⊗ sd), which this model does not contain.
- **The threshold is underbound.** ³He in 0s binds −3.3 MeV against −7.7 MeV. Work relative to the model threshold, and do not quote absolute energies.
