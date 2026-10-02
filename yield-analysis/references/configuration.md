# Data contract and execution

Run the bundled demo first and adapt its generated `config.json`. Every run accepts:

| Field | Meaning |
|---|---|
| `run_id`, `analysis_id` | Acquisition ID and unique analysis-row ID (include detector/transition in the latter) |
| `detector`, `transition`, `target` | Optional preserved labels |
| `energy_lab_keV` | Incident projectile laboratory energy |
| `spectrum_csv` | Numeric CSV with `low,high,counts` and optional `variance` |
| `roi`, `left_sideband`, `right_sideband` | Two-element energy edge arrays, ordered, disjoint and aligned to actual bins |
| `background` | `constant`, `linear` (default), or `step` |
| `step_energy` | Required step position for the step background |
| `charge_C`, `charge_state` | Integrated electrical charge in coulombs; positive projectile charge state (default 1) |
| `live_fraction` | Live/real time, in (0,1] |
| `efficiency`, `branching`, `summing_survival` | Probabilities, default branch/survival 1; survival divides observed area |
| `independent_normalization_relative_error` | Optional independent relative standard deviation |

Instead of `spectrum_csv`, use `root_file`, `histogram`, and `calibration: {"offset": ..., "slope": ...}`. The linear calibration acts on histogram axis coordinates, in keV; it does not reinterpret ROOT bin indices. Confirm that the ROOT histogram has not already been calibrated. CSV bins must be contiguous and increasing. For raw Poisson counts the default variance is counts; weighted spectra need their actual variance.

For example, the demo's run has ROI [40,60], sidebands [20,30] and [70,80], charge 1e-6 C, live fraction 0.9 and efficiency 0.1. These are synthetic values, never measurement defaults.

The model computes `net = gross - aL*left_counts - aR*right_counts`, with variance `Var(gross) + aL²*Var(left) + aR²*Var(right)`. The coefficients integrate a constant, linear density or two-level step over the exact ROI. Finite sidebands contribute uncertainty even when their background estimate is small.

`yield_per_ion = net / ((charge_C/(charge_state*e))*live_fraction*efficiency*branching*summing_survival)`.

Raw counts must not already be live-time corrected. Total efficiency is not a photopeak-efficiency substitute. A summing correction multiplier C corresponds to survival 1/C only if that multiplicative treatment is valid; appreciable additive sum-in needs a joint cascade model.

Top-level `shared_systematics: {"charge_calibration": 0.02}` adds an outer product `(0.02*y)(0.02*y)^T`. Each named source is independent of other sources and fully correlated over all configured rows. For subset-specific or energy-dependent correlations, extend the covariance builder with explicit sensitivity vectors rather than applying a global scalar.

Outputs: `yields.csv`, `covariance.csv`, an excitation-curve PNG/PDF, individual ROI PNGs, `result.json` and `report.html`. Covariance rows follow the analysis ID order recorded in the result. Independent and statistical errors remain available separately. Calibration/ROI-selection uncertainty is not automatically estimated: repeat with justified alternatives and record those sensitivity results.

# Spectrum preparation

```
python scripts/prepare_spectrum.py list-root spectra.root
python scripts/prepare_spectrum.py export spectra.root 'folder/histogram' --offset -2 --slope 0.54 --out bins.csv
python scripts/prepare_spectrum.py suggest bins.csv --prominence 20 --out candidates.json
```

The example calibration is illustrative. Inspect the candidate list and overlay before choosing the final windows. Generated files and result directories refuse accidental overwrite.

# Comparing yields to weighted simulation

Keep experimental raw counts and simulation weights distinct. For a weighted histogram the relevant bin variance involves squared weights, with additional covariance if several entries descend from the same primary history. The supplied ROI tool assumes independent bin errors and does not reconstruct that covariance. A histogram of several photons/hits per event is not automatically an independent-event count spectrum; use per-history scores or an explicit covariance treatment for correlated simulation tallies.

Match the simulated selection to the measurement: per-crystal versus addback, energy smearing, thresholds, live/gating conventions and reaction channel. Preserve the generated-primary or reaction denominator and define every correction exactly once. A simulation normalized per reaction needs a physical reaction yield before comparison to measured yield per beam ion.
