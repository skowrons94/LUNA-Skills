# Uncertainty assessment checklist

Work from the code, configurations and result files. For every item, note where it is implemented (file:line) or that it is missing.

## 1. Sources by stage

| Stage | Sources to look for |
|---|---|
| Counting | Poisson statistics, low-count regime (Gaussian propagation invalid), background model choice, ROI and sideband choice, peak-shape model, interfering lines |
| Normalisation | charge integration (calibration, secondary electrons, charge state), live time (definition), target stoichiometry and thickness, target degradation over the irradiation |
| Detection | photopeak efficiency (curve covariance, extrapolation outside the calibrated range, geometry transfer), summing, angular distribution, branching ratios |
| Energy | beam energy calibration and spread, energy loss and straggling, effective energy definition, lab ↔ centre-of-mass conversion |
| Physics model | R-matrix channel radius, background poles, level assignments (J^π, number of levels), parametrisation, external capture, electron screening correction |
| Simulation | Monte Carlo statistics, physics list, geometry tolerances, event generator, validation residuals |
| Literature inputs | quoted errors (stat/sys split known?), normalisation uncertainty, digitisation error, evaluated-data uncertainties |

## 2. Correlation structure

For each source decide:
- **point-to-point independent**;
- **common to one data set** (normalisation, efficiency at one energy, target);
- **common to several data sets** (shared calibration source, shared stopping table, same detector);
- **energy-dependent correlated** (efficiency curve across line energies, stopping power across energies).

Check that the implementation matches the decision. Two errors are common:
- A common error added in quadrature to every point. It then shrinks with the number of points in a fit.
- A shared error omitted because each data set "has its own normalisation".

## 3. Propagation

- Is the covariance used in the fit, or only the diagonal?
- Floated normalisations: is there a prior equal to the quoted systematic, and is Peelle-type bias avoided? Fitting with a multiplicative-error covariance built from the data, rather than from the model, biases the result low.
- Model-dependent quantities (S(0), resonance strengths from fits, rates): is the model uncertainty from alternative models (radius scan, level-scheme variants) quoted, or only the fit covariance at one model?
- Monte Carlo propagation: enough samples, seeds recorded, and checked for convergence?
- Asymmetric or bounded quantities (upper limits, widths near zero): is a profile or posterior used instead of a symmetric error?

## 4. Calibration evidence

What evidence shows the uncertainties are the right size?
- Pull distributions per data set and region.
- Repeat measurements (reproducibility vs quoted error).
- Agreement of independent methods (sideband vs peak fit, two efficiency sources).
- Prediction of data not used in the fit.
- Agreement with later measurements (back-test).

No such evidence is itself a finding.

## 5. Reported vs implemented

Compare the methods text, captions and error-budget tables with what the code does. Typical mismatches:
- A budget lists a source the code never applies.
- The code applies a correction the text does not mention.
- "Statistical" errors that already include a systematic part.
- A different χ² definition in the text than in the fit.

## 6. Conclusion check

Write the conclusion the analysis draws, then ask:
- Which sources dominate the uncertainty of that conclusion?
- Are those the ones best characterised?
- Would a plausible alternative treatment of the dominant source change the conclusion?

If yes, the result needs that alternative quoted, or the conclusion needs weakening.
