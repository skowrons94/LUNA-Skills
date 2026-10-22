# Solar models and neutrino fluxes

## A solar model

Template: `simplex_solar_calibration` (copy it with `run.py`). With `just_do_first_values = .true.` in `inlist_simplex_search_controls_solar` it runs one model with the given initial [Fe/H], Y, mixing length α and overshoot f_ov to the solar age and prints a χ² against L, R (via Teff), surface Z/X, surface Y, the convective-zone base R_cz and the rms sound-speed difference to helioseismology. A real calibration lets the simplex vary them (`just_do_first_values = .false.`, many runs, hours). Keep the shipped first values for rate-sensitivity work unless the study is about the calibration itself, and say so.

To compute neutrino fluxes:

- the net must contain the decays explicitly (`new_net_name = 'pp_and_cno_extras.net'`, as the template does);
- add `add_screened_rates` to `profile_columns.list`;
- set `write_profile_when_terminate = .true.` and `filename_for_profile_when_terminate = 'final.profile'` in `&controls`.

Then:

```bash
python3 SKILL_DIR/scripts/mesa.py neutrinos RUN/final.profile --json RUN/neutrinos.json
```

Each `screened_rate` column holds reactions per second in a cell. The flux of a source is the sum over cells divided by 4π(1 AU)². The sources are pp (`r_h1_h1_wk_h2`), pep (`r_h1_h1_ec_h2`), hep (`r_h1_he3_wk_he4`), ⁷Be (`r_be7_wk_li7`, both lines), ⁸B (`r_b8_wk_he4_he4`), ¹³N, ¹⁵O and ¹⁷F (their β⁺ decays).

## Reference values

Standard solar models B16 (Vinyoles et al. 2017, ApJ 835, 202), fluxes in cm⁻² s⁻¹:

| Source | B16-GS98 | B16-AGSS09met |
|---|---|---|
| pp | 5.98 × 10¹⁰ | 6.03 × 10¹⁰ |
| pep | 1.44 × 10⁸ | 1.46 × 10⁸ |
| hep | 7.98 × 10³ | 8.25 × 10³ |
| ⁷Be | 4.93 × 10⁹ | 4.50 × 10⁹ |
| ⁸B | 5.46 × 10⁶ | 4.50 × 10⁶ |
| ¹³N | 2.78 × 10⁸ | 2.04 × 10⁸ |
| ¹⁵O | 2.05 × 10⁸ | 1.44 × 10⁸ |
| ¹⁷F | 5.29 × 10⁶ | 3.26 × 10⁶ |

Values checked against Vinyoles et al. 2017, Table 6 (fractional uncertainties there: e.g. ⁸B ±12 %, ¹³N ±15 %, ¹⁵O ±17 % for GS98). Use newer SSMs where they apply (e.g. Magg et al. 2022, A&A 661, A140). The CNO fluxes are ~25–40 % lower with AGSS09met than with GS98. That difference is the solar-abundance problem that CNO-neutrino measurements (Borexino, and later SNO+ and JUNO) are meant to resolve. It is also why the ¹⁴N(p,γ) and ¹²C(p,γ) rates matter: the CNO flux is proportional to the rate times the core C+N content, so a rate uncertainty limits how well a measured flux constrains the core composition.

## Rate sensitivity of the fluxes

Two runs that differ only in one rate factor give the logarithmic derivative:

α = ln(Φ₁/Φ₀) / ln(f).

Run them with identical inputs (same template, same calibration parameters, same MESA version) and compare at the same age. Without recalibration, L and R drift slightly with the changed rate. That is acceptable for small factors (≤ 10–20 %), but report L, R, surface Z/X and R_cz of both runs. In published SSM work the derivatives come from recalibrated models. Expect agreement at the ~10 % level on α, not better.

Published exponents (Serenelli, Peña-Garay & Haxton 2013, PRD 87, 043001, Table I, SFII-GS98 SSM): for S₁₁₄ (¹⁴N(p,γ)), α = 1.000 for ¹⁵O and 0.747 for ¹³N (part of the ¹³N flux comes from primordial ¹²C burning in the outer core), and |α| < 0.01 for pp, pep, ⁷Be and ⁸B. For S₃₄ (³He(α,γ)), α = 0.853 for ⁷Be and 0.806 for ⁸B. The model must reproduce these patterns before any new sensitivity it gives is believed.

## Tested result (MESA r26.04.1, this template, 2026-10-22)

The template at its shipped first values, run unchanged and with `special_rate_factor` 1.10 on `r_n14_pg_o15`. Each run took 89 min on 3 threads, with energy error 10⁻⁹. The template prints no termination code; use `check-run --done "save best model results"`.

| | pp | pep | ⁷Be | ⁸B | ¹³N | ¹⁵O | ¹⁷F |
|---|---|---|---|---|---|---|---|
| MESA / B16-GS98 | 0.99 | 0.96 | 0.99 | 0.92 | **1.98** | **2.32** | 1.13 |
| α(S₁₁₄), MESA | −0.02 | −0.03 | −0.02 | −0.03 | 0.84 | 0.97 | −0.02 |
| α(S₁₁₄), Serenelli et al. 2013 | −0.007 | −0.010 | −0.001 | 0.007 | 0.747 | 1.000 | — |

- **Rate response: reproduced.** α(¹⁵O) agrees to 3 % and α(¹³N) to 12 %. The pp-chain fluxes are insensitive, as expected. The small negative α values come from the missing recalibration (log L moved from −0.00146 to −0.00171).
- **Absolute CNO fluxes: not reproduced.** ¹³N and ¹⁵O are ≈2× the SSM, consistently with the model's own CNO luminosity (`cno` = 1.5 % of L). Internal bookkeeping is consistent: ¹⁴N(p,γ), ¹⁵O decay and ¹⁵N(p,α) rates agree. The cause is not established. The template is a test case, not an SSM: surface Z/X is 0.0257 against the 0.0229 target, f_ov = 0.031, TDC convection, and no calibration loop. Do not quote absolute CNO fluxes from it. For absolute fluxes, run the simplex calibration, compare its central T and C+N profile with an SSM, and find the cause first. Ratios and logarithmic derivatives from paired runs are usable with the caveat above.
