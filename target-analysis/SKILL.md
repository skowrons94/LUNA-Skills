---
name: target-analysis
description: Infer solid-target energy-loss profiles, effective stopping, composition ratios and target evolution from nuclear-reaction excitation curves. Use for implanted or compound targets, SRIM stopping data and cross-section folding; keep peak extraction and detector-efficiency calibration as explicit upstream inputs.
---

# Target analysis

Turn a measured excitation curve into a reproducible target-response model and, where identifiable, constraints on target properties. Distinguish a phenomenological profile in energy loss from a physical concentration-versus-depth reconstruction. This skill is derived from the user's fluorine-in-Fe/Ta and CaF2 notebooks; their hard-coded values are examples, not defaults for new targets.

## Establish the measurement

Read [inputs-and-units.md](references/inputs-and-units.md) before modeling. Identify reaction/channel, target/scan, projectile charge state, beam-energy calibration and frame, measured-yield definition, uncertainty convention, efficiency/branching/solid-angle corrections, stopping inputs and cross-section provenance. Preserve run IDs and acquisition order so deterioration during irradiation is not averaged into a false static profile.

Use existing project metadata to resolve inputs. If units, energy frame or error definitions remain ambiguous, ask for those specific facts before reporting fitted physical quantities. Continue auditing files and testing the model independently. Do not guess that a column called `Y_error` is an absolute standard deviation or that an AZURE output column is a total cross section.

Write calculations, logs and tests to the user's project or a scratch directory, never into the skill directory. For an analysis project, preserve its source data and use its requested output layout. Record input hashes and model/configuration with results.

## Model and fit

1. Inspect data coverage and group physically distinct scans. Flag duplicate measurements, nonfinite values, nonpositive errors and target-label inconsistencies. Do not silently drop low-energy points or combine different resonances/efficiencies.
2. Construct stopping per active isotope from the chosen elemental/compound data and composition convention. Fit an identifiable inactive/active ratio rather than two abundances that enter only through their ratio. Check electronic versus total stopping and any compound correction.
3. Obtain a sufficiently resolved cross section for the intended channel and angular acceptance over the full integration and broadening domain. Reuse a validated table when appropriate. If generating new AZURE2 results, use the AZURE2 skill (`azure2`, if installed) and verify its output definition; do not automatically execute the example's old server wrapper.
4. Choose a uniform layer, truncated Gaussian or another justified profile, state normalization and support, then fold cross section/stopping with beam spread and depth-dependent straggling. Follow [model-and-fitting.md](references/model-and-fitting.md). Start with a transparent model, then add complexity only when measurements can constrain it.
5. Test the forward model before optimizing: constant-cross-section analytic limit, zero-broadening behavior, unit/frame consistency, input coverage, numerical convergence and synthetic parameter recovery.
6. Fit only parameters used by the model, with physical constraints and an appropriate likelihood/covariance. Test multiple starts and inspect residuals, parameter correlations, bounds and rank. Separate statistical uncertainty from efficiency, stopping, calibration and nuclear-model systematics. A forward plot with hand-picked parameters is not a fit.
7. Report only identifiable quantities. Convert energy-loss widths to areal/physical thickness only with a consistent stopping/composition/density model. Fit changing target state jointly or per scan where the acquisition history demands it.

## Tested helpers

Read [usability.md](references/usability.md) for complete fit configuration and outputs. These helpers need Python, NumPy and SciPy (Matplotlib for fit reports). They do not require ROOT, lmfit or a running AZURE server.

- `scripts/fit_target.py CONFIG.json --out NEW_DIRECTORY` fits named, bounded parameters with repeated starts, checks rank, and saves fit/residual/profile plots, covariance and an HTML report.
- `scripts/srim_table.py INPUT.stop OUTPUT.csv --component total` parses the supplied SRIM format, supports decimal commas and converts to lab-keV and keV cm²/atom. Choose `electronic`, `nuclear` or `total` explicitly. It refuses to overwrite its output.
- `scripts/target_model.py CONFIG.json --out NEW_DIRECTORY` evaluates the energy-loss-coordinate approximation and saves predictions plus input hashes. The JSON/table contract and API are in [model-and-fitting.md](references/model-and-fitting.md). It rejects queries outside table coverage instead of silently holding endpoint values. It is a forward model, not an automatic fit or a complete depth-transport solver.

Read [example-audit.md](references/example-audit.md) when reusing the original notebooks. It records demonstrated traps, tested behavior and unresolved measurement metadata. The operational skill does not depend on the original notebooks.

## Deliverables

Provide the model definition/assumptions, data selection and normalization, fitted or fixed parameters with units, uncertainty/correlation information, data-model plot and residuals, profile visualization with an explicitly labeled coordinate, numerical checks and reproducible inputs/results. For physical thickness or stoichiometry claims, explain how the inferred quantity maps to the target and what external inputs constrain it. Label manually chosen curves and sensitivity envelopes accurately.

Run `python scripts/demo.py --out NEW_DEMO` for editable synthetic inputs and a complete fit/report. Read [agent-code.md](references/agent-code.md) before extending the helpers. Dependencies are listed in `requirements.txt`.
