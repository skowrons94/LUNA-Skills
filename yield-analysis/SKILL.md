---
name: yield-analysis
description: Extract nuclear-reaction gamma-ray yields from ROOT or CSV spectra using reviewed ROIs, finite-sideband uncertainties, charge and live-time normalization, and correlated systematic errors. Use when turning measured spectra into net peak areas, photon or reaction yields, or excitation-curve points, or when auditing an existing yield analysis.
---
# Yield analysis

Turn raw spectrum counts into reproducible excitation-curve points. Keep raw data intact; preserve run, detector, transition and target identity. Use the scripts with explicit configuration rather than notebook state or executable pickle inputs.

## Workflow

1. Establish energy calibration, histogram identity, bin convention, charge units/charge state, live fraction, peak identity and which efficiency, branching and summing corrections have already been applied. A variable named `deadTime` may actually contain a live fraction; resolve its definition.
2. Inspect candidate peaks and sidebands. `prepare_spectrum.py` lists ROOT histograms, exports calibrated bins, and suggests candidate windows. Suggestions require review for interfering lines and sloping/stepped backgrounds. Use peak-shape fitting when simple sidebands cannot isolate the signal.
3. Read [configuration.md](references/configuration.md), prepare a JSON file and run `scripts/analyze_yield.py CONFIG --out NEW_DIRECTORY`. Paths are relative to the configuration. Use bin edges, not ROOT bin numbers, for windows. The tool rejects partial-bin ROIs.
4. Check each saved ROI overlay, net area, background, uncertainty and normalized point. Retain negative background-subtracted areas; do not replace them with zero. Low-count inference may require a joint Poisson signal/background model beyond the supplied Gaussian propagation.
5. Keep statistical, independent normalization, and shared uncertainties distinguishable. Use the covariance matrix for downstream inference rather than treating a shared calibration error as independent at each energy.

## Helpers and validation

Run `python scripts/demo.py --out PATH_TO_NEW_DEMO` for a complete offline example with data, configuration, plots, CSV and HTML report. It checks an analytic net area and finite-sideband variance. NumPy, SciPy and Matplotlib are needed; ROOT input additionally needs uproot, not a ROOT installation.

Read [example-audit.md](references/example-audit.md) when migrating the original PhD scripts, and [agent-code.md](references/agent-code.md) before changing the implementation. Write analysis outputs to the user's project (e.g. `results/`), never into the skill directory.

## Deliver

Provide the excitation curve, ROI diagnostics, per-run counts and correction factors, uncertainty/covariance ordering, input hashes and reproducible configuration. State whether the result is detected counts, a photon yield, or a reaction yield; dividing by a branch probability is only appropriate for the intended observable.
