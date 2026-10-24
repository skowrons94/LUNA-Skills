---
name: efficiency-analysis
description: Calibrate gamma-detector photopeak efficiency, retrieve evaluated nuclear data directly from IAEA NDS, and calculate or fit prompt-cascade coincidence summing with explicit peak/total efficiencies and geometry. Use for HPGe or scintillator efficiency curves from calibration sources or reaction lines, summing-in/summing-out corrections, and decay or level data needed for them, including how large a summing or efficiency correction is for a given line and geometry, which must be computed rather than estimated from memory.
---
# Efficiency analysis

The efficiency curve converts a peak area into a number of emitted gamma rays, and the summing correction accounts for cascade photons that are detected together. This skill builds both reproducibly, without `nudel`. You need calibration-source spectra or reaction lines with their net areas, the source certificates, and the detector geometry. You get a correlated efficiency curve with its validity range, summing corrections where they matter, and the nuclear-data snapshots behind them. Each calibration belongs to one detector, source position, source extent, absorber arrangement and set of acquisition conditions, and it is not transferred to another without a reason. The full-energy peak efficiency and the total interaction efficiency are different quantities and are kept apart.

## Where this fits

- Comes from: net areas of calibration lines (`yield-analysis`, `peak-shape-analysis`); evaluated decay and level data from IAEA NDS (this skill's `nds.py`, or `evaluated-nuclear-data` for cross sections); a validated detector model (`geant4-simulation`, `underground-gamma-simulation`) where the total efficiency is not measured.
- Goes to: `yield-analysis` (contract `efficiency-curve`, evaluated with the `efficiency-at` adapter of `analysis-chain`).
- Checked by: `scripts/demo.py` and `scripts/demo_cascade.py`, the direct limits listed under the rules, and `uncertainty-audit`.

## Choose the workflow

- Known source activity and peak areas: read [calibration.md](references/calibration.md), build the points with `build_points.py` and fit a correlated log-polynomial curve over the measured range with `fit_efficiency.py`.
- Evaluated line and level data: read [direct-nds.md](references/direct-nds.md). `nds.py` fetches and caches the official data, selects the parent state and decay mode, and keeps the provenance. Network access is needed only to fetch new data.
- Coincidence summing or a simultaneous peak/total fit: read [cascades.md](references/cascades.md), review a complete prompt scheme, then use `cascade.py` or `fit_cascade_efficiency.py`. A normalised adopted-level graph is conditional on its initial population, so it is not automatically a complete model of a radioactive decay.

`python scripts/demo.py --out NEW_DEMO` runs an offline calibration and analytic summing checks, and `python scripts/demo_cascade.py --out NEW_DEMO` a joint single- and sum-peak fit at several distances. Both generate editable configurations and reports. The scripts need Python with NumPy, SciPy and Matplotlib; the NDS retrieval uses the standard library only.

## Rules and their reasons

1. Resolve the activity reference date, half-life, measurement duration, live-time convention, emission probability, net-area errors and any correction already applied, because each one scales the efficiency directly. The correlations of source activities and emission probabilities are carried through the calibration.
2. Metastable and ground-state ambiguities are resolved before a decay line is used, and transitions are identified from the level scheme, not matched to the nearest energy.
3. Inspect the fit residuals, rank, bounds and the degeneracy between source scale and efficiency. A total efficiency must be constrained by the data or come from an independently validated model; renaming the photopeak curve does not produce one.
4. Before a summing correction is applied to measured yields, test its direct limits (zero efficiency, an isolated photon, two-photon sum-in and sum-out) and the neglected effects that are relevant for the geometry.

[example-audit.md](references/example-audit.md) records the migration decisions and the validation limits, and [agent-code.md](references/agent-code.md) is to be read before extending the scripts. Original data are preserved; working products go to the user's project, never into the skill directory.

## What to deliver

- Calibration coefficients with covariance, and the validity range.
- The geometry and the nuclear-data snapshots with their hashes.
- Where used, the reviewed cascade and its assumptions.
- Fit plots with residuals, and a reproducible report.

The statistical and local-fit uncertainty is reported separately from the systematics of incomplete nuclear data, geometry, angular correlation and timing. When the curve feeds yields, its uncertainty is a shared systematic across runs, not a per-run error, which is why it is evaluated with `adapters.py efficiency-at`.
