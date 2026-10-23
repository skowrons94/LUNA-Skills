# Validation ladder

| Rung | Check | How | Proves | Does not prove |
|---|---|---|---|---|
| 0 | Library | `scripts/selftest.py` prints PASS | K, the fit, the n·π invariance, the one-level relation (7Be values) | that your phase is right |
| 1 | Phase | unwrapped, referenced to threshold, below the next threshold; for an R-matrix fit, the phase-shift grid uses the adopted parameters (not the .azr defaults) | the input is the quantity you think | — |
| 2 | Window | a0, r0 from two windows (e.g. 0.20–2.00 and 0.30–upper threshold) and orders 1–2; rms of the K fit | how much the number depends on the recipe | the physics |
| 3 | Same recipe | every compared curve (fit, model, published band) through the same window and order | that differences are not recipe artefacts | — |
| 4 | Round trip | `delta_from_ere` of the fitted (a0, r0, P) overlays the input phase within its uncertainty | the expansion represents the phase over the window | — |

## Lessons that changed results (7Be study)

- **The window moved a0 by 4 fm.** The same R-matrix eigenphase gave 39.7 fm (0.20–2.00 MeV) and 35.5 fm (0.30–4.02 MeV). The paper quotes the first with its window; the second is a stated systematic.
- **A local cluster potential fitted to negative parity gives a0 = −31 fm**, the wrong sign. The measured band (22–60 fm) needs the positive-parity depth 15–21 MeV shallower, the same shift the R-matrix eigenphases ask for.
- **A one-level θ² above the Teichmann–Wigner limit can be what the data demand.** θ² = 1.95 at E_x = 8.39 MeV implies a0 ≈ 29 fm. With the residual nuclear potential carried outside the channel radius, θ² = 1.11 implies 54 fm. Both are inside the measured range: the width is a parameterization of a0.
- **The antisymmetrized calculation reproduces r0 where a local Majorana potential does not** (1.00–1.04 fm against 1.34 fm), so quote r0 alongside a0: it discriminates between models.
