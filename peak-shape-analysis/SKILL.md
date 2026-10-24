---
name: peak-shape-analysis
description: Fit asymmetric nuclear-reaction gamma peaks and target energy-loss shapes in ROOT or CSV spectra with a bin-integrated detector response, explicit backgrounds, Poisson or Gaussian likelihoods and optional physics templates. Use when simple sideband windows cannot isolate a peak, when a peak shape carries target or lifetime information, or when tracking target degradation across runs.
---
# Peak-shape analysis

Some peaks cannot be separated from their background by sideband windows, and some carry information in their shape, such as the energy loss in the target. This skill fits such spectra with a forward model of the detector response, integrated over the actual bin edges. You need the spectrum, its energy calibration with uncertainty, the resolution and the fit region. You get the fitted area, shape parameters with their covariance, residuals and convergence checks. A detected peak area is not yet a target profile, a reaction yield or an S factor: those also need independently defined efficiency, kinematics, stopping and cross-section normalisation.

## Where this fits

- Comes from: the same spectrum contract as `yield-analysis` (`spectrum-csv`); calibration and resolution from the experiment.
- Goes to: `yield-analysis` (areas where sidebands fail), `target-analysis` (target-edge profiles and degradation across runs).
- Checked by: `scripts/demo.py`, the convergence and calibration variations of steps 5 and 6, and `uncertainty-audit` for weakly identified tails.

## Method

1. Identify the reaction and transition, the detector, the run history, the energy calibration and its uncertainty, whether the spectrum holds raw counts or corrected values, the resolution, the fit region and any interfering peaks. List or export ROOT histograms with `scripts/prepare_spectrum.py`.
2. Read [models-and-config.md](references/models-and-config.md) and select a Gaussian reference line or a phenomenological target-edge profile. Where a physics weighting template is required, use a validated one; the reaction constants of the example are not to be reused silently for another reaction.
3. Generate a starting configuration with `python scripts/demo.py --out NEW_DEMO`, adapt it to the measured spectrum, and run `python scripts/fit_peak.py CONFIG --out NEW_DIRECTORY`.
4. Inspect residuals, edges, tails, area, parameter bounds and correlations. Raw integer spectra with a Poisson deviance are preferred. A Gaussian fit is justified only when the supplied variances and the data treatment support it. A Poisson likelihood is never applied to live-time-divided counts, because those are no longer Poisson distributed.
5. Test convergence by refining the source grid and enlarging its domain, and vary calibration and resolution within their independent uncertainties. When counts are low, parameters reach their bounds or tails are weakly identified, the local covariance is not sufficient; supplement it with a profile likelihood or a coverage check on simulated data.
6. Compare runs against a reference scan with a consistent calibration and response, keep the target and accumulated-charge labels, and plot how the parameters evolve. Detector parameters shared between spectra may require a joint fit, which the bundled fitter does not do: it fits one spectrum at a time.

## Scripts

[example-audit.md](references/example-audit.md) records the migration of the legacy analysis, and [agent-code.md](references/agent-code.md) is to be read before extending the code. The scripts need NumPy, SciPy, Matplotlib, and uproot for ROOT input; the offline demo needs no ROOT installation.

## What to deliver

- The fitted spectrum, background and residuals.
- Parameter definitions and covariance, and the area convention.
- Data and configuration hashes, and the convergence checks.
- The assumptions needed for any physical inference from the shape.

Fit outputs go to the user's project, never into the skill directory.
