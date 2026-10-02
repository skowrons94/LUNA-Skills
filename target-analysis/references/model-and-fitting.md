# Forward model and inference

## What the supplied helper computes

Let E0 and u be incident laboratory energy and mean energy loss, both in keV. The helper computes

Y(E0)=A integral_0^U P(u) <sigma(E0-u+delta)/epsilon_eff(E0-u+delta)>_delta du,

where delta has a zero-mean Gaussian with variance

s(u)^2 = s_beam^2 + s_Doppler^2 + a_strag^2 u.

Cross section is cm², effective stopping is keV cm² per active atom, so the result is dimensionless per incident ion under the chosen target model. The straggling coefficient has units keV/sqrt(keV). All widths supplied are standard deviations; FWHM=2 sqrt(2 ln 2) sigma.

`P(u)` is a **dimensionless profile modifier**, either a uniform support from 0 to width or a Gaussian exp[-(u-mean)^2/(2 sigma²)] restricted to u>=0 and the chosen integration extent. It is not a normalized probability density. `amplitude` scales it. Changing to a unit-area Gaussian changes both units and parameter interpretation and must be reflected in the model. The example's Gaussian and square branches were mutually exclusive despite both sets of parameters being declared.

This preserves the example's energy-loss-coordinate approximation: the profile is evaluated at the nominal loss u while the ratio sigma/epsilon is broadened. It is not an exact coupled simulation of variable concentration, energy loss and depth-dependent straggling. For a physical concentration model use depth x, local densities n_i(x), stopping dE/dx=-sum_i n_i(x)epsilon_i(E), and yield integral n_active(x)sigma(E(x))dx, with the appropriate energy distribution and detection acceptance. Do not interpret a free profile modifier and free stopping-composition ratio as independent measurements of the same density without a consistent derivation.

If a dimensionless profile represents the active-atom measure in energy coordinates, an areal-density estimate involves integral P(u)/epsilon_eff du (and any physically defined amplitude). For a uniform mixture this reduces to integrating 1/epsilon_eff over the energy loss. This relation requires a defined reference/energy dependence and consistent composition; it is not a universal conversion from fitted Gaussian area to atoms/cm². Converting to nm additionally needs a number/mass density and geometry. Report energy-loss widths when these inputs are absent.

## Helper contract

Produce two numeric CSV files with one header and two columns:

- cross section: `energy_lab_keV,cross_section_cm2`;
- effective stopping: `energy_lab_keV,stopping_keV_cm2_per_active_atom`.

The numeric loader checks shape, ordering and finite/nonnegative values, but cannot infer units or scientific meaning from values. Build effective stopping from the explicit active/inactive ratio, not directly from the elemental export unless the target is pure active material. Use input grids with enough coverage and resolution; do not extrapolate them silently.

A configuration example (illustrative settings, not measured target parameters):

```json
{
  "cross_section_csv": "cross_section.csv",
  "effective_stopping_csv": "effective_stopping.csv",
  "energy_lab_keV": [235, 240, 245],
  "model": {
    "profile_kind": "gaussian",
    "mean_keV": 7,
    "sigma_keV": 4,
    "max_loss_keV": 30,
    "beam_sigma_keV": 0.1,
    "doppler_sigma_keV": 0,
    "straggling_keV_per_sqrt_keV": 0.5,
    "amplitude": 1,
    "depth_points": 401,
    "kernel_points": 101,
    "kernel_sigmas": 5
  }
}
```

Paths resolve relative to the JSON file. Run `python SKILL_DIR/scripts/target_model.py config.json --out temp/new-prediction`. The output directory must be new. Import `response()` for parameter fitting and `counts_per_microcoulomb()` for an explicit scalar efficiency/charge-state conversion. The forward CLI deliberately produces yield per incident ion, not an automatically efficiency-corrected fit.

Uniform profiles use `profile_kind="uniform"` and `width_keV`; mean/sigma are irrelevant and should not be fit. The helper integrates exactly to the uniform edge. Gaussian profiles use a finite `max_loss_keV`, whose omitted tail must be checked. The numerical Gaussian broadening is truncated and renormalized over `kernel_sigmas`; extend it and refine both grids to test convergence. A zero-width kernel is supported. Positive broadened-energy coverage is required; low-energy truncation needs a separately derived model rather than renormalizing away an unmodeled boundary.

## Fitting and identifiability

Build residuals in the **same units as the observations**. For independent Gaussian errors use (prediction-observation)/sigma; for covariance C whiten residuals using its factorization. For counts, use a likelihood that matches count and background acquisition. Keep parameter access by name; the original code sometimes changes dictionaries into positional lists while the model still uses named keys.

Parameterize `inactive_to_active`, not both n_inactive and n_active if only their ratio enters epsilon_eff. Inspect dependencies before optimization: no unused Gaussian/square parameters, no declared resonance parameters disconnected from the cross-section generator. Keep nuclear and target parameters separate initially; joint fits require enough independent information to avoid absorbing wrong resonance physics into a target tail.

Amplitude, stoichiometry, efficiency and absolute cross-section normalization can compensate for one another. Beam spread, straggling and profile width can be strongly correlated; energy calibration/offset and mean implantation loss can shift the same feature. Use independent constraints and report remaining degeneracy. Estimate Jacobian rank/correlations, inspect bound hits and repeat from multiple starts. Do not derive precise composition from a curve whose normalization is freely adjustable.

For an implementation test, create synthetic observations with known parameters and recover them; also validate against an analytic limit so passing a self-generated fit does not merely prove internal consistency. Check the measured curve/model with residuals, not visual agreement alone. Compare alternate profiles or time-evolution models when justified.

Propagate fitted covariance or joint posterior/bootstrap samples while respecting constraints. Shared calibration/efficiency/stopping uncertainties need correlated treatment. Independently perturbing each parameter by an arbitrary 20–50% and plotting a standard deviation is a sensitivity envelope, not a measured confidence band. Use positive/log transforms or bounded priors for widths, composition and straggling; negative Gaussian samples become misleading when squared in the model. Record random seeds.

## Acceptance and reporting

Demonstrate stability against integration extent, grid density and kernel cutoff at a level small compared with the requested physical precision. Preserve cross-section grid resolution near resonances. Include raw and transformed energy/yield conventions, fit range, exclusions, free/fixed parameters, optimizer outcome, fit statistic and degrees of freedom where meaningful, covariance/rank diagnostics and systematic assumptions.

Plot observations and model in identical units with residuals. Show profile against **energy loss** unless a validated stopping/density mapping supports depth; include uncertainty only with its statistical meaning. Keep run/scan comparisons to show potential depletion or target evolution. Neither a synthetic recovery nor a finite optimizer result validates the experimental normalization or a particular target's physical thickness.

## Connecting a fitted target to transport

To use a target result in SimLUNA, first define a physical layer model: composition/isotope fractions, number density, thickness, backing and any depth dependence. The helper's fitted energy-loss profile is not directly a spatial density profile. Derive and document the stopping-based mapping, or transfer the validated joint reaction-energy/depth distribution to a prescribed-product generator with explicit normalization. Verify the simulation reproduces the intended energy-loss and reaction-depth distributions before comparing detector spectra. Keep target/stopping uncertainty separate from detector and cascade uncertainty. Do not tune physical thickness merely to compensate for an enhanced or incorrectly scaled simulation cross section.
