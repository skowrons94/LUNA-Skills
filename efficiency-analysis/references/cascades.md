# Cascade probabilities and joint fits

A scheme contains `populations` mapping level IDs to initial probabilities summing to one, `transitions` with `from,to,energy_keV,probability`, and optional `gamma_probability` (default 1). Outgoing total transition probabilities must sum to one. `terminal_levels` defaults to ["0"]. A non-gamma branch transfers to the next level without a detected photon. Atomic X-rays and conversion electrons are omitted, not assumed physically absent. Review isomers and coincidence timing separately.

`enumerate_paths` rejects cycles, missing levels and resource-limit overflow instead of silently discarding weak paths. `peak_probability` enumerates all photon subsets whose full energies match the chosen peak within a positive tolerance. Selected photons contribute peak efficiencies; unselected photons contribute `(1-total_efficiency)`. This includes sum-in and sum-out for independent prompt photons. It excludes angular correlations, Compton sum-in, pileup, atomic radiation, electrons and finite timing acceptance.

For a two-gamma cascade with peak efficiencies 0.1 and total efficiencies 0.2, an isolated single line has probability 0.08 and the sum peak 0.01. This is a useful analytic regression case, not a universal correction factor.

```
python scripts/cascade.py scheme.json --efficiencies efficiencies.csv --energy-keV 1500 --tolerance-keV 0.5 --out probability.json
```

The efficiency CSV is increasing `energy_keV,peak,total`; it must cover every photon energy in the scheme. Require `0 <= peak <= total <= 1`. Matching tolerance describes which ideal full-energy sums enter the observable; detector resolution and window acceptance are not integrated by this command.

## Joint calibration

Run `demo_cascade.py` for a complete editable example and `fit_cascade_efficiency.py CONFIG --out NEW_DIRECTORY` for observations. Input CSV columns are `source,energy_keV,distance_cm,exposure,observed,error`. Observed/errors share units; exposure is the known number of initial cascade events for counts, or the corresponding normalization in a yield calculation. Account for live fraction consistently in exposure. Errors are positive absolute Gaussian uncertainties on net observations.

Config fields: `data_csv`, `reference_distance_cm`, `energy_tolerance_keV`, `sources`, `parameters`. Each source maps to `scheme_json` and either fixed `scale` (default 1) or `scale_parameter` naming a nuisance parameter. Optional `priors:{name:{mean,sigma}}` append one residual each, not once per measurement. Parameter entries have `value,min,max`, or `value,vary:false`. Optional `starts,seed,max_nfev` control the fitter.

With `x=ln(E/1000)`, the empirical bounded model is:

```
total = logistic(t0 + t1*x + t2*x*x - 2*ln((distance+d0_cm)/(reference_distance+d0_cm)))
peak = total * logistic(f0 + f1*x + f2*x*x)
```

`t0`, `f0`, `d0_cm` must be supplied; other polynomial terms default to zero. Distances and offset use cm. Constrain offset so all shifted distances remain positive. These curves are a deliberately explicit alternative to the legacy parameterization, not an exact detector solid-angle calculation. Include terms only when constrained; singles alone can leave peak/total/source scale degenerate. Sum peaks, multiple distances, known activities or independent total-efficiency constraints help resolve it.

Outputs contain parameters, local covariance/rank warnings, predicted observations, standardized residuals and plots. The helper currently uses independent Gaussian observation errors; correlated activities should be source-scale nuisance parameters with priors. Correlated peak-area covariance would require extending the residual to whiten with the full covariance. It is not silently supported.

## Using a detector simulation as an efficiency input

Define the denominator first: emitted gamma, source decay, specified reaction, or incident projectile. Preserve all generated events or the generated count in separate metadata. Match detector/source geometry, attenuation, thresholds and gate to the measured calibration. For a cascade, sum-in/out can already be included in a simulated gated spectrum; do not apply the analytic correction again to the same observable.

A photopeak curve cannot be relabeled as total efficiency. Obtain both with explicitly defined scores and validate them with suitable measurements/limits. If cross-section or source sampling was biased, follow the simulation's history-weight convention and uncertainty calculation; raw accepted/generated counts are then not generally valid. Compare geometry variants as a systematic study with physical dimensional uncertainties. When combining a simulated response with calibrated points, retain common geometry/model uncertainties and identify which model parameters the data actually constrain.
