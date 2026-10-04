# Spectrum and configuration

Use the generated demo configuration as a complete editable example. `spectrum` contains either `spectrum_csv` (numeric `low,high,counts[,variance]`) or `root_file,histogram,calibration:{offset,slope}`. Paths are relative to the JSON file. `fit_window` must align with bin edges. Supply `source_domain:[low,high]`, `source_points` (at least 101), and independently justified `response_sigma_keV` (>0). This sigma is a Gaussian standard deviation, not FWHM.

Each entry of `parameters` has either `{"value":...,"min":...,"max":...}` or `{"value":...,"vary":false}`. Bounds must be finite. Optional `starts`, `seed` and `max_nfev` control optimization.

## Shapes

For `shape:"target_edge"`, parameters are:

- `area_counts`: integrated detected-signal expectation over the configured true-energy source domain before fit-window losses.
- `edge_keV`, `loss_width_keV`: high-energy edge and separation of the two profile edges.
- `low_edge_scale_keV`, `high_edge_scale_keV`: positive logistic edge scales, not Gaussian sigmas.
- `background_left`, `background_right`: nonnegative counts per keV at the observed fit-window ends.
- Optional `tail_amplitude`, `tail_start_keV`, `tail_low_scale_keV`, `tail_high_scale_keV` add a low-energy logistic tail. Inspect the `intrinsic` function before fitting this extra component; constrain it only with sufficient data.

The main shape is `expit((edge-E)/high_scale) * expit((E-edge+loss_width)/low_scale)`. A separately normalized Gaussian detector response is integrated over each observed bin. The source shape, optionally multiplied by a physics template, is normalized over the source domain before applying area.

For `shape:"gaussian"`, use `centroid_keV`, `intrinsic_sigma_keV` and the common area/background parameters. Check parameter names against the bundled example/API before extending a configuration. Intrinsic and detector widths can be strongly degenerate; do not freely fit both without information.

`template_csv` optionally supplies increasing `energy_keV,weight` covering the full source domain. The template must be finite and nonnegative. It can represent an externally validated cross-section/efficiency/kinematic weighting, but its normalization is absorbed into area. This alone cannot determine an absolute S factor. A physical replacement should evaluate reaction kinematics, Doppler/angular acceptance, stopping and energy-dependent detector response consistently; validate those components separately.

## Likelihood and numerical checks

Default `likelihood:"poisson"` requires raw nonnegative integer counts with Poisson variance. It includes empty bins through the Poisson deviance. `likelihood:"gaussian"` requires positive variances; it is useful for the noiseless expected-count recovery demo and appropriately processed observations.

Do not convolve a plotted curve and then sample bin centers: the code integrates the response into each observed bin. Do not shift a template with circular array rolling. Enlarge the source domain until tails and fit-window leakage are stable, halve the source spacing, and compare fitted area/shape changes against their errors. Resolution is fixed in this helper; repeat at plausible resolutions to assess its systematic effect.

Outputs include `fit.csv` with observed, predicted, signal, background and residual information, PNG/PDF fit diagnostics, `result.json` with covariance and input hashes, and `report.html`. A formally converged fit with structured residuals is not an adequate physical model.

## Simulation-informed Doppler shapes

For an angle-dependent peak or a lifetime-sensitive tail, construct the emission model using reaction kinematics, recoil velocity at emission, target/backing slowing, level lifetime and detector angular acceptance. If the `underground-gamma-simulation` skill is used, apply its kinematics/Doppler guide and validate generated truth separately from detector deposits. Do not add a second boost to already boosted photons. Detector resolution is applied after transport; a generic Gaussian width is not a substitute for recoil slowing.

The current `template_csv` multiplies the intrinsic source shape before Gaussian response. It is suitable for a nonnegative physical weighting function, not automatically for a complete already-convolved Monte Carlo histogram. Importing a detector-response spectrum as that template would apply the response twice. A direct Monte Carlo template fit needs a separate prediction path with explicit histogram normalization, bin integration, statistical uncertainty and any additional resolution convolution. Report calibration/resolution/target/lifetime degeneracies rather than assigning the entire fitted width to one effect.
