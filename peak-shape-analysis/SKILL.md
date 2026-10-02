---
name: peak-shape-analysis
description: Fit asymmetric nuclear-reaction gamma peaks and target energy-loss shapes in ROOT or CSV spectra with bin-integrated detector response, explicit backgrounds, Poisson or Gaussian likelihoods, and optional physics templates. Use when simple sideband windows cannot isolate a peak, when a peak shape carries target or lifetime information, or when tracking target degradation across runs.
---
# Peak-shape analysis

Fit spectra using the actual bin edges and a forward response model. Distinguish the detected peak area from a target profile, reaction yield or S factor: the latter require independently defined efficiency, kinematics, stopping and cross-section normalization.

## Workflow

1. Identify reaction/transition, detector, run history, energy calibration and its uncertainty, raw counts versus corrected spectra, resolution, fit region and interfering peaks. List/export ROOT histograms with `scripts/prepare_spectrum.py`; use the same spectrum contract as yield extraction.
2. Read [models-and-config.md](references/models-and-config.md). Select a Gaussian reference line or a phenomenological target-edge profile. Use a validated physics weighting template where required; do not silently reproduce reaction constants from the example.
3. Generate a starting configuration with `python scripts/demo.py --out NEW_DEMO`, then adapt it to the measured spectrum. Run `python scripts/fit_peak.py CONFIG --out NEW_DIRECTORY`.
4. Inspect residuals, edges, tails, area, parameter bounds and correlations. Prefer raw integer spectra with Poisson deviance. Use Gaussian fitting only when supplied variances and data treatment justify it. Never apply a Poisson likelihood to live-time-divided counts.
5. Refine the source grid and enlarge its domain to test convergence. Vary calibration and resolution within their independent uncertainties. If counts are low, parameters hit bounds or tails are weakly identified, supplement local covariance with profile likelihood or simulated-data coverage checks.
6. Compare runs against a reference scan using consistent calibration/response, retain target and accumulated-charge labels, and plot parameter evolution. Shared detector parameters may require a joint fit; the bundled fitter handles one spectrum at a time.

## Resources and deliverables

Read [example-audit.md](references/example-audit.md) when migrating the legacy analysis, and [agent-code.md](references/agent-code.md) before extending the code. Scripts need NumPy, SciPy, Matplotlib and uproot for ROOT input; the offline demo requires no ROOT installation.

Deliver the fitted spectrum/background/residuals, parameter definitions and covariance, area convention, data/configuration hashes, convergence checks and the assumptions needed for any physical inference. Write fit outputs to the user's project, never into the skill directory.
