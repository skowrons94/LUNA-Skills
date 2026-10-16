# Shared systematics and covariances

## Fitting scale uncertainties

- A covariance matrix built from the measured values for a multiplicative (normalization) uncertainty biases a least-squares fit low (Peelle's pertinent puzzle; d'Agostini, Nucl. Instrum. Methods A 346, 306 (1994)). Remedies: build the covariance from the model prediction and iterate, or fit an explicit multiplicative factor per dataset, applied to the model, with a prior of the quoted width. Prefer a lognormal prior (or marginalise the factor): the maximum-a-posteriori estimate with a Gaussian prior on a multiplicative factor is biased high at order f² (about +3% for a 20% normalization in the demonstration).
- With explicit factors, state the convention (does the factor multiply the data or the model?) before interpreting fitted values; a factor below one on the data means the data lie above the model.
- Shape-type systematics (stopping powers, screening, the energy dependence of an efficiency) are not normalizations; give them their own nuisance parameters acting on energy or shape.
- For low-count points use a Poisson likelihood or model-based variances; variances taken from the observed counts bias fits low as well.
- Per-dataset excess variance can absorb a shared parameter if both are free; show they are identifiable (each shared parameter constrained by at least two datasets).

## Correlations between results

- A component shared by several measurements (same laboratory, detector, efficiency reference, calibration source, stopping-power table, charge integration) correlates their results. Ratios of such results lose that component; sums gain it.
- Dilution: a shared component s carried by one experiment contributes about s/N_eff to the standard deviation (s²/N_eff² to the variance) of a rate built from N_eff comparably weighted experiments. A correlation coefficient computed as if one experiment dominated both rates overstates the effect by about N_eff.
- Correlations within one compound system (several channels fitted together in one multichannel R-matrix analysis) are already handled by the joint fit; the new step is correlation across different compound systems through shared experimental components.
- Cap a shared component at the total quoted uncertainty of each quantity it enters; never add uncertainty that is not in the published budget.

`scripts/peelle_demo.py` shows, on synthetic data, the low bias of the data-based covariance and its absence for the model-based and lognormal-factor treatments, and the O(f²) bias of a Gaussian factor prior.
