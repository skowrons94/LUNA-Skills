# Migration and validation

Original inputs are retained under `temp/efficiency-analysis/example`. The replacement avoids a dependency on `nudel`; no claim about that library's maintenance status is required. Live requests successfully retrieved Co-60 decay radiation, Ni-60 adopted gammas and Cs-137 decay radiation from IAEA NDS. The client cached the latter with URL, time and checksum. A Ni-60 conditional level-4 cascade converted successfully with strict ICC handling.

Legacy risks addressed: nearest-energy association within 50 keV can select the wrong transition; missing branch intensities must not default to one; cyclic/incomplete graphs and branch truncation require explicit handling. Sum-out is a product of no-interaction probabilities, not a sum of subset products with all positive signs. Source-ratio priors belong once in the objective. The old chi-square error definition of 4 and loose fitting settings are not carried over.

The old multi-distance calibration contains reaction/source-specific constants and data columns whose activity, uncertainty and position conventions need confirmation. No fully calibrated reproduction of those experimental efficiencies is claimed. The supplied joint fitter offers named parameters, explicit distances/exposure, bounded peak/total curves and source nuisance scales, rather than copying undocumented constants.

Offline tests cover exact two-photon sum-in/out, conversion-path normalization, cycle rejection, decay integration, source-area normalization and polynomial coefficient recovery. A second demo recovers joint total and peak efficiency from single/sum peaks at three distances. Synthetic success validates the implementation under its stated model, not the neglected detector/nuclear effects.
