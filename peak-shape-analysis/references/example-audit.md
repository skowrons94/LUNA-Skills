# Legacy example and validation

The original scripts and ROOT data remain in `temp/peak-shape-analysis/example`. Actual ROOT histogram `CompleteSpectra/00212_Ch2` in `2019_Runs_5-469.root` was listed and exported successfully with uproot (16,383 bins). The illustrative legacy calibration was offset -1.99293 and slope 0.542642; its scientific accuracy was not independently established. Peak suggestions were tested as IO, not accepted as line identifications.

The old model divided counts by live fraction before Poisson fitting, used hard-coded bin-width assumptions, and had an adaptation path that rolled one theory array while evaluating another. Circular rolling also wraps endpoints. These behaviors are not retained. Reaction-specific masses/constants require review: the example's f13 setup used an M1 value of 12 alongside target mass number 13. No automatic correction to its physics is asserted.

The supplied fitter replaces the reusable spectral machinery: finite-bin response integration, positive backgrounds, named bounded parameters, explicit source support and uncertainty reports. It does not claim to reproduce the old absolute S-factor inference without its external physics inputs.

The portable offline demo recovers area 8,000, edge 105 keV and loss width 12 keV from an asymmetric synthetic spectrum, checks near-full-range signal normalization and the empty-bin deviance limit. It uses expected counts with Gaussian variance to isolate implementation accuracy; this is not a statistical coverage study or an experimental target fit.
