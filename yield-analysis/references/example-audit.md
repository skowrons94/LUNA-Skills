# Migration findings and evidence

The supplied ROI pickles and notebooks are preserved in `temp/yield-analysis/example`. Referenced external spectra and logbook files were absent, so no experimental yield reproduction is claimed. Do not deserialize unknown pickles as a data interchange format; extract trusted legacy selections into reviewed JSON if needed.

The original integration mixed inclusive ROOT integrals with a width calculated as `bin_high-bin_low`; this produces an off-by-one normalization. It also blurred energy, channel and bin-index conventions, omitted finite-sideband uncertainty, and applied inconsistent step-background treatment. The replacement operates on explicit bin edges and propagates the variance of every contributing bin.

Resolve the meaning of the legacy `deadTime`, charge units, 0.89 normalization and state-dependent summing factors from acquisition records. None is a universal constant. The old output-folder clearing step is not reproduced.

The portable demo tests an area of 100 counts and variance 260 for constant and step sidebands, rejects fractional-bin windows, and checks charge/live/efficiency normalization. It generates a complete report. This validates arithmetic, not experimental peak selection or calibration.
