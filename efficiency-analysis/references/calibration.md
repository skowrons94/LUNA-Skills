# From source spectra to an efficiency curve

Use a reviewed ROI/peak fit to obtain net counts and their uncertainty. `build_points.py INPUT.csv --out NEW_DIRECTORY` accepts numeric columns `energy_keV,net_counts,net_error,decays,emission_probability,live_fraction`, plus optional `summing_factor` (multiplicative; default 1). Probabilities are fractions, not percent. It computes `efficiency = net_counts*summing_factor/(decays*emission_probability*live_fraction)`. Avoid correcting live time or summing twice.

`integrated_decays(activity_Bq,elapsed_s,real_time_s,half_life_s)` in `build_points.py` integrates activity over the real exposure, including decay between the activity reference epoch and acquisition. Decide explicitly whether acquisition metadata already reports an integrated activity or live-time exposure. A nuclide's photon probability per decay differs from a conditional level-transition probability.

The point builder propagates net-count error only. Add activity, emission probabilities, live fraction and summing-model uncertainties with their correlations before making a total uncertainty claim. For independent sources or repeated source measurements, construct covariance from shared nuisance sensitivities, not repeated independent activity errors.

Run `fit_efficiency.py CONFIG.json --out NEW_DIRECTORY`. Example config:

```json
{"points_csv":"points.csv", "geometry":"Detector A, source center 10 cm from endcap", "degree":2, "reference_energy_keV":1000, "quantity":"full_energy_peak"}
```

Points have `energy_keV,efficiency,error`. Optional `covariance_csv` is a numeric square matrix without headers in point order, in absolute efficiency squared, replacing the diagonal errors. It must be positive definite. Use sufficient independent points and sensible degree (0–5); the fitter requires more points than coefficients.

The curve is `ln(efficiency) = sum c_k * ln(E/reference_energy_keV)^k`. Generalized least squares uses a first-order transformation of the covariance to log space; large relative errors may need a likelihood in the original observation space. The output coefficients use increasing powers, and their covariance is not rescaled by reduced chi-square. Local uncertainty bands are not full systematic bands.

The fit rejects efficiency above 1 over its sampled measured range and records the energy validity range. Do not extrapolate it into an unmeasured region. Calibrate different geometries separately or use the explicit joint distance model. The offline demo produces exact coefficient recovery and a complete example configuration.
