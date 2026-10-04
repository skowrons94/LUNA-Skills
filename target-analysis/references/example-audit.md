# Example audit and validation

The audited example (not distributed with this skill) contained exploratory notebooks, SRIM tables, an AZURE wrapper, model outputs and yield tables. This skill extracts the workflow rather than treating every notebook as a working implementation.

## Findings that change decisions

- `Yields.csv`: 78 measurements, with 38 for IMP_LFE#2, 23 for IMP_LTA#2 and 17 for SUDF#4. Energy ranges differ substantially and include separate resonance regions. Several files have copied target labels.
- The supplied low-energy `.extrap` table has 6000 rows and **302 adjacent repeated energy coordinates with differing cross sections**. The strict loader rejects it. Regenerate a higher-precision table from the actual calculation; do not silently drop/average values near narrow resonances. Apparent output rounding is a hypothesis, not verified original grid provenance.
- Cross-section coverage is 0.18992–0.24689 in its first column; units/frame must be verified from the producer. The notebooks treat it as CM MeV. `np.interp` outside this range silently clamps endpoints, contaminating broad integrations and other resonance regions.
- Notebook SRIM interpolation expects keV, but `Calculation.ipynb` passes values multiplied by 1000 for an eV calculation. It also clamps outside the table. The helper rejects this mistake.
- Electronic stopping is used in the notebook; a method named `eval_total_straggle` actually adds electronic/nuclear stopping. This is not a straggling model.
- Some notebooks mix `SRIM/SRIM` with the supplied lowercase `srim/srim`; several paths refer to data absent at the assumed location.
- The Gaussian profile returns before the square branch; `width` then has no effect. n_fe and n_f enter only as a ratio, so varying both is redundant.
- Several chi-square functions refer to undefined obs/err and convert named parameters to a list while their model expects named keys. Their plots are not evidence of completed optimization.
- Simpson integration uses an interval divided by N for a grid with N endpoints; the actual interval spacing is divided by N-1. New code passes coordinates explicitly.
- The thermal-width expression mixes unit conventions; see inputs-and-units.md.
- Some uncertainty bands use arbitrary independent parameter perturbations with no fitted covariance and permit negative widths. They are sensitivity plots, not statistical confidence bands.
- `pg.dat` starts with a numeric data row although one notebook skips it as a header. Inspect actual files, not copied loader assumptions.

## Tests performed

Environment: NumPy 2.1.3 and SciPy 1.15.2. All seven SRIM files parsed to 79 ordered points over 10–10000 lab keV. The electronic Fe first value converts from 10.85 eV/(1e15 atoms/cm²) to 1.085e-17 keV cm²/atom.

Five independent checks passed: constant-cross-section uniform analytic integral; truncated-Gaussian analytic integral and convolution normalization; strict coverage and charge-unit conversion; real SRIM parsing; and synthetic parameter recovery. The known Gaussian loss parameters (mean 7 keV, sigma 3 keV, amplitude 1.4) were recovered. Doubling integration resolution changed predictions by about 2.21e-6 of the synthetic peak. The forward CLI also produced the expected constant-cross-section result.

The fit CLI adds repeated starts, explicit absolute-error residuals, optional priors, local covariance/rank checks, fit/profile plots, HTML report and machine-readable outputs. Development tests and artifacts remain under `temp/target-analysis`. No measured target thickness, composition or calibrated experimental yield was inferred: measurement metadata and the duplicate-energy table must first be resolved. No legacy AZURE server was started.
