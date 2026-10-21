# Handoff contracts

`scripts/contracts.py list` prints the machine-checked part. This file states the physics each handoff must preserve, which a column check cannot.

## spectrum-csv → yield-analysis, peak-shape-analysis

`low,high,counts[,variance]`, contiguous increasing bins in keV, raw counts. Not live-time corrected, not efficiency corrected. A calibrated ROOT export must say which calibration it used. A weighted (simulated) spectrum needs its real variance column.

## yield-table: yield-analysis → target-analysis, cross-section extraction, R-matrix

`yields.csv` with `covariance.csv` and `result.json` beside it. Three uncertainty classes travel separately:

- `stat_error`: counting statistics of this point, independent between points.
- `independent_normalization_error`: per-point normalisation errors that are independent between points (e.g. a per-run charge reading).
- `shared_systematics` in `result.json`: fully correlated over the rows they apply to (charge integrator calibration, efficiency curve, target stoichiometry). They are a common normalisation downstream, not a per-point error. In an R-matrix fit they become a normalisation factor with a prior equal to the quoted value.

State whether `yield_per_ion` is a detected-photon yield, a photon yield (efficiency-corrected) or a reaction yield (divided by a branching). Dividing by a branching is correct only for the intended observable.

`yields-to-excitation` writes the statistical (or statistical ⊕ independent) error only and says so in the sidecar. The shared part must be carried by the consumer.

## efficiency-curve: efficiency-analysis → yield-analysis

`ln ε = Σ cᵢ [ln(E/E_ref)]ⁱ` with the coefficient covariance, validity range, geometry and `quantity = full_energy_peak`. Use `efficiency-at` to get ε, its relative uncertainty and the correlation between line energies:

- Each run's `efficiency` is ε at the line energy.
- The relative uncertainty goes into `shared_systematics`. It is fully correlated over all runs at the same line energy. Across different line energies, use the printed correlation. It is not an independent per-run error.
- Outside the validity range the value is an extrapolation. Use a validated simulation or extend the calibration instead.
- Summing corrections belong to the geometry and the cascade. A curve measured far away does not apply in close geometry without a summing treatment.

## excitation-curve → target-analysis

`energy_lab_keV,yield,error`, strictly increasing energies, one detector and transition per file. Say what `error` contains. Stopping powers and composition are inputs with their own provenance. The effective energy returned for each point is in the lab frame unless stated otherwise.

## azure-dat → AZURE2

Four columns: E_lab (MeV), angle (deg), cross section (b, or b/sr for differential), uncertainty in the same unit. Lab frame, forward kinematics. Angle-integrated data use a dummy angle. Analysing-power data use a centre-of-mass angle (see `azure2`). Conversions with `to-azure`:

- `--frame cm`: E_lab = E_cm (m₁+m₂)/m₂, non-relativistic. Differential data in the centre of mass are refused; convert angles and cross sections first.
- `--value-kind sfactor`: σ = S/E_cm · exp(−2πη), with 2πη = 2π Z₁Z₂ α √(μc²/2E_cm). Any electron-screening correction must be removed or applied explicitly before conversion, and recorded.
- The uncertainty column should be the point-to-point part. Put the common normalisation of the data set into the segment's normalisation prior, not into each point.

The contract check warns when energies exceed 50 MeV, which usually means keV were written. It is a heuristic: data entirely below 50 keV written in keV are not caught, so look at the first lines.

## Into the claims register

A number leaving stage 5 or 7 is a claim with `kind`, `evidence`, `produced_by` and `depends_on` pointing at the upstream claims (yield normalisation, efficiency, target). This lets a rerun upstream mark it stale.
