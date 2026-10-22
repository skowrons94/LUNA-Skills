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

Check these against the paper before quoting them (`citation-checker`), and use the newer SSMs where they apply (e.g. Magg et al. 2022 abundances). The GS98/AGSS09 difference in the CNO fluxes, ~30–40 %, is the solar-abundance problem that CNO-neutrino measurements (Borexino, and later SNO+ and JUNO) are meant to resolve. It is also why the ¹⁴N(p,γ) and ¹²C(p,γ) rates matter: the CNO flux is proportional to the rate times the core C+N content, so a rate uncertainty limits how well a measured flux constrains the core composition.

## Rate sensitivity of the fluxes

Two runs that differ only in one rate factor give the logarithmic derivative:

α = ln(Φ₁/Φ₀) / ln(f).

Run them with identical inputs (same template, same calibration parameters, same MESA version) and compare at the same age. Without recalibration, L and R drift slightly with the changed rate. That is acceptable for small factors (≤ 10–20 %), but report L, R, surface Z/X and R_cz of both runs. In published SSM work the derivatives come from recalibrated models. Expect agreement at the ~10 % level on α, not better.

What to expect qualitatively: changing S₁₁₄ (¹⁴N(p,γ)) moves the ¹⁵O and ¹³N fluxes almost proportionally (α near 1 for ¹⁵O, smaller for ¹³N, because part of the ¹³N flux comes from ¹²C burning outside the CN-equilibrium core) and leaves pp, ⁷Be and ⁸B nearly unchanged. Changing S₃₄ (³He(α,γ)) moves ⁷Be and ⁸B by α ≈ 0.8–0.9. The model must reproduce these patterns before any new sensitivity it gives is believed.
