# Agent-facing command guide

Use Python with numpy, scipy and matplotlib; scripts do not install packages or modify input data. Each output directory must be new. `--help` documents the entrypoint. CSV/JSON inputs make runs reproducible without notebook state.

## Fit an excitation curve

`python SKILL_DIR/scripts/fit_target.py config.json --out temp/target-fit-001`

The data CSV has `energy_lab_keV,yield,error`, with absolute standard deviations in the same units as yield. Cross section and effective-stopping CSVs follow model-and-fitting.md. Minimum JSON:

```json
{
  "data_csv": "excitation.csv",
  "cross_section_csv": "cross_section.csv",
  "effective_stopping_csv": "effective_stopping.csv",
  "yield_unit": "per_ion",
  "starts": 3,
  "seed": 12345,
  "model": {"max_loss_keV": 30, "beam_sigma_keV": 0.1},
  "parameters": {
    "mean_keV": {"value": 7, "min": 0, "max": 15},
    "sigma_keV": {"value": 4, "min": 0.2, "max": 8},
    "amplitude": {"value": 1, "min": 0.1, "max": 3}
  }
}
```

Every parameter in this example is illustrative. `vary:false` fixes a parameter; varying parameters require finite bounds. Values in `parameters` override `model`. `background` is an optional constant in measurement yield units. `yield_unit:counts_per_microcoulomb` additionally requires `efficiency` and optionally `charge_state`. A scalar efficiency must already represent the applicable response; do not use it for a changing gamma spectrum without justification.

Optional `priors` maps a parameter name to `{mean:...,sigma:...}`. Each Gaussian constraint is included once. The fit's covariance treats supplied errors as absolute and includes priors; it is not automatically scaled to force reduced chi-square to one. Check parameter rank, bound warnings and alternative minima in result.json. This CLI uses independent point errors; correlated measurement errors require adapting residual whitening as described in the modeling guide. For composition fitting, replace `effective_stopping_csv` with `active_stopping_csv` and `inactive_stopping_csv` (elemental exports in keV cm²/atom), then include `inactive_to_active` in `parameters` or `model`. The model builds epsilon_active + ratio*epsilon_inactive over their common energy range on every evaluation. Constrain amplitude/efficiency independently: fitting both scale and ratio freely can be poorly identifiable. The CLI supports this two-component Bragg-additive case; more complex composition profiles require a model extension.

Outputs: `report.html`, fit PNG/PDF, profile PNG, `fit.csv`, `result.json` (parameters, local covariance, diagnostics, input hashes and full configuration). Only the stated forward model and local statistical covariance are calculated; this does not automate a full systematic uncertainty analysis or physical depth reconstruction.

## Passing yields between skills

The yield-analysis output uses `yield_per_ion` and `stat_error`; the target fitter expects `yield` and `error`. Select one compatible target/detector/transition/scan, preserve its row order, and make an explicit numeric CSV mapping `energy_lab_keV,yield_per_ion,stat_error` to `energy_lab_keV,yield,error`. Do not pool different scans or substitute a sum of statistical and shared errors without a covariance model. The supplied target CLI fits independent errors only; adapt residual whitening before using yield-analysis's full `covariance.csv`, retaining the same selected row/column order.
