---
name: efficiency-analysis
description: Calibrate gamma-detector photopeak efficiency, retrieve evaluated nuclear data directly from IAEA NDS, and calculate or fit prompt-cascade coincidence summing with explicit peak/total efficiencies and geometry. Use for HPGe or scintillator efficiency curves from calibration sources or reaction lines, summing-in/summing-out corrections, and decay or level data needed for them.
---
# Efficiency analysis

Create reproducible efficiency calibrations and summing calculations without `nudel`. Match each calibration to detector, source position, source extent, absorber arrangement and acquisition conditions. Distinguish full-energy peak efficiency from total interaction efficiency.

## Choose the workflow

- **Known source activity and peak areas:** read [calibration.md](references/calibration.md); use `build_points.py` and `fit_efficiency.py` to build points and fit a correlated log-polynomial curve over the measured range.
- **Evaluated line and level data:** read [direct-nds.md](references/direct-nds.md); use `nds.py` to fetch/cache official data, select the parent state/decay mode, and preserve provenance. Network access is only needed for fetching new data.
- **Coincidence summing or simultaneous peak/total fits:** read [cascades.md](references/cascades.md). Review a complete prompt scheme, then use `cascade.py` or `fit_cascade_efficiency.py`. A normalized adopted-level graph is conditional on its initial population, not automatically a complete radioactive-decay model.

Run `python scripts/demo.py --out NEW_DEMO` for an offline calibration and analytic summing checks. Run `python scripts/demo_cascade.py --out NEW_DEMO` for a joint single/sum-peak fit at several distances. Both generate editable configurations and reports. Use Python with NumPy, SciPy and Matplotlib; NDS retrieval itself uses the standard library.

## Scientific checks

Resolve activity reference date, half-life, measurement duration, live-time convention, emission probability, net-area errors and any prior correction. Keep source activity and emission-probability correlations through the calibration. Resolve metastable/ground-state ambiguities before using decay lines. Do not match transitions merely to the nearest energy.

Inspect fit residuals, rank, bounds and source-scale/efficiency degeneracy. Data must constrain the requested total efficiency or it must come from an independently validated model. Never obtain it by renaming the photopeak curve. Test direct limits (zero efficiency, isolated photon, two-photon sum-in/out) and relevant neglected effects before applying a correction to measured yields.

Read [example-audit.md](references/example-audit.md) for migration decisions and validation limits, and [agent-code.md](references/agent-code.md) before extending scripts. Preserve original data; write working products to the user's project, never into the skill directory.

Deliver calibration coefficients/covariance and validity range, geometry, nuclear-data snapshots/hashes, a reviewed cascade and assumptions where used, fit plots/residuals and a reproducible report. Report statistical/local-fit uncertainty separately from incomplete nuclear-data, geometry, angular-correlation and timing systematics.
