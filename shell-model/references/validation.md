# Validation ladder

| Rung | Check | How | Proves | Does not prove |
|---|---|---|---|---|
| 0 | Tools | `scripts/selftest.py` PASS | parsing, spurious flag, calibration arithmetic | KSHELL itself |
| 1 | Convergence | Lanczos converged for every state used (log); `n_eigen` large enough to pass the spurious states | the eigenvalues are converged | — |
| 2 | Spurious states | runs with β_cm = 0 and 10: the states with ⟨H_cm⟩ of several MeV disappear and the physical ones keep ⟨H_cm⟩ ≲ 0.1 | no c.m. excitation is being interpreted | — |
| 3 | Normal parity | the known normal-parity spectrum of the nucleus and its mirror (and a p-shell benchmark such as Cohen–Kurath) | interaction and setup | the intruder band |
| 4 | Calibration | intruder states in ≥ 3 neighbouring nuclei, residuals referred to thresholds; offset and scatter | the systematic of the band | the nucleus of interest |
| 5 | Truncation | 0ħω/1ħω against 0–2ħω/1–3ħω | model-space sensitivity (7Be: 0.3–0.6 MeV) | — |
| 6 | Identification | distance to the R-matrix level in combined σ, occupancy, and whether the continuum calculation agrees about what the state is | the assignment | the width |

## Lessons that changed results (7Be study)

- **The three lowest positive-parity states of the full 1ħω space were spurious** (⟨H_cm⟩ = 5.2–5.8 MeV with the Lawson term off). With β_cm = 10 the retained states carry 0.02–0.09, and the physical ones sit ~6 MeV higher.
- **The reference sets the error.** The intruder band scattered by 1.04 MeV about experiment when referred to ground states and by 0.38 MeV when referred to the core+nucleon threshold. The predictions moved accordingly.
- **The prediction matched an R-matrix level that the compilation lacks.** The calibrated 1/2⁺ at E_x = 7.95(38) MeV is 1.1σ from the fitted 8.40(12) MeV. sd occupancy 1.00 identified it as a nucleon on a ⁶Li core, consistent with the fit's p+⁶Li coupling. The continuum calculations explained its large α width separately.
- **A third 1/2⁺ near 13.45(38) MeV** coincided with a pole that the R-matrix fit favoured above the data. The shell model can motivate a level above the data, but it does not decide whether to adopt it: that is a model-selection question for the fit.
