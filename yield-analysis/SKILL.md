---
name: yield-analysis
description: Extract nuclear-reaction gamma-ray yields from ROOT or CSV spectra with reviewed ROIs, finite-sideband uncertainties, charge and live-time normalization, and correlated systematic errors. Use when turning measured spectra into net peak areas, photon or reaction yields, or excitation-curve points, or when auditing an existing yield analysis.
---
# Yield analysis

A yield analysis turns the counts of a gamma-ray spectrum into excitation-curve points that another analysis can trust. You need the spectra (ROOT or CSV), the energy calibration, the accumulated charge and the live time of each run. You get net areas, normalised yields and their covariance, together with the configuration that reproduces them. The raw data are not changed at any point, and run, detector, transition and target keep their identity through the analysis, because the later stages need to know which point came from which run.

## Where this fits

- Comes from: raw spectra (contract `spectrum-csv`); the efficiency curve from `efficiency-analysis` (contract `efficiency-curve`).
- Goes to: `target-analysis` and cross-section extraction (contract `excitation-curve`, through the `yields-to-excitation` adapter of `analysis-chain`), and `azure2` (contract `azure-dat`, adapter `to-azure`). When sidebands cannot isolate a peak, the fit moves to `peak-shape-analysis`.
- Checked by: `scripts/demo.py` (must print PASS), the `data-auditor` subagent before the analysis, `uncertainty-audit` and `physics-referee` before the yields are quoted.

## Method

The scripts are driven by an explicit configuration file, not by notebook state or pickled inputs, so that every number can be regenerated from the configuration.

1. Establish what the inputs mean before using them: energy calibration, histogram identity, bin convention, charge units and charge state, live fraction, peak identity, and which efficiency, branching and summing corrections have already been applied. A variable named `deadTime` may in fact hold a live fraction, so resolve its definition from the acquisition code or its author.
2. Inspect the candidate peaks and sidebands. `prepare_spectrum.py` lists the ROOT histograms, exports calibrated bins and suggests candidate windows. The suggestions do not see interfering lines or sloping and stepped backgrounds, so review each one. Use `peak-shape-analysis` when simple sidebands cannot isolate the signal.
3. Read [configuration.md](references/configuration.md), prepare a JSON configuration and run `scripts/analyze_yield.py CONFIG --out NEW_DIRECTORY`. Paths are relative to the configuration. Windows are given as bin edges, not ROOT bin numbers, and the tool rejects ROIs that cut a bin.
4. Check each saved ROI overlay, net area, background, uncertainty and normalised point. A negative background-subtracted area is kept as it is and not replaced by zero, because clipping biases the mean of low-count points upward. For low counts the supplied Gaussian propagation may not be enough, and a joint Poisson model of signal and background is then needed.
5. Keep the statistical, the independent normalisation and the shared uncertainties apart. Downstream inference uses the covariance matrix, because a shared calibration error treated as independent at each energy would average down as if it were statistical.

## Scripts and validation

`python scripts/demo.py --out PATH_TO_NEW_DEMO` runs a complete offline example with data, configuration, plots, CSV and an HTML report. It checks an analytic net area and the finite-sideband variance. The scripts need NumPy, SciPy and Matplotlib; ROOT input also needs uproot, but not a ROOT installation.

[example-audit.md](references/example-audit.md) records the migration of the original PhD scripts, and [agent-code.md](references/agent-code.md) is to be read before changing the implementation. Analysis outputs go to the user's project (for example `results/`), never into the skill directory.

## What to deliver

- The excitation curve with ROI diagnostics, per-run counts and correction factors.
- The uncertainty components and the covariance, with their ordering.
- Input hashes and the configuration that reproduces the result.

The output is the `yield-table` contract of `analysis-chain`. When the yields feed another stage (`target-analysis`, a cross section, AZURE2), convert them with its adapters, so that shared systematics stay shared. State whether the result is detected counts, a photon yield or a reaction yield: dividing by a branch probability is appropriate only for the observable that is actually intended.
