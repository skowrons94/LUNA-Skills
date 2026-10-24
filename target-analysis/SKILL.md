---
name: target-analysis
description: Infer solid-target energy-loss profiles, effective stopping, composition ratios and target evolution from nuclear-reaction excitation curves. Use for implanted or compound targets, SRIM stopping data and cross-section folding, and for stopping powers or effective stopping of compound targets (Bragg's rule, composition dependence), which must come from stopping tables rather than memory; peak extraction and detector-efficiency calibration stay explicit upstream inputs.
---

# Target analysis

A measured excitation curve contains the target: how the active nuclei are distributed in depth, how much the beam loses on the way, and how this changes during irradiation. This skill builds a reproducible target-response model from such a curve and, where the data allow it, constraints on the target properties. You need the excitation curve with its yield definition, the beam-energy calibration, stopping tables and the cross section of the channel. You get a fitted profile with uncertainties and correlations, the forward-model checks, and the target quantities the data can actually identify. A phenomenological profile in energy loss is distinguished from a physical reconstruction of concentration against depth. The skill derives from the user's fluorine-in-Fe/Ta and CaF2 notebooks; their hard-coded values are examples, not defaults for new targets.

## Where this fits

- Comes from: `yield-analysis` through the `yields-to-excitation` adapter of `analysis-chain` (contract `excitation-curve`); peak shapes from `peak-shape-analysis`; cross sections from `azure2`; stopping from SRIM tables (`scripts/srim_table.py`).
- Goes to: effective energies and target thickness for the cross section or S factor, and on to `azure2`.
- Checked by: the forward-model tests of step 5, `scripts/demo.py`, and `uncertainty-audit` or `physics-referee` before thickness or stoichiometry is quoted.

## Establish the measurement

Read [inputs-and-units.md](references/inputs-and-units.md) before modelling. Identify the reaction and channel, the target and scan, the projectile charge state, the beam-energy calibration and its frame, the definition of the measured yield, the uncertainty convention, the efficiency, branching and solid-angle corrections, the stopping inputs and the provenance of the cross section. Run IDs and acquisition order are kept, so that deterioration during irradiation is not averaged into a false static profile. The error column of the `excitation-curve` contract excludes the shared systematics, which act as a common normalisation.

Existing project metadata are used to resolve the inputs. If units, energy frame or error definitions remain ambiguous, ask for those specific facts before reporting fitted physical quantities, and meanwhile continue to audit the files and test the model independently. A column called `Y_error` is not assumed to be an absolute standard deviation, nor an AZURE output column to be a total cross section.

Calculations, logs and tests are written to the user's project or a scratch directory, never into the skill directory. In an analysis project its source data are preserved and its output layout is used. Input hashes and the model configuration are recorded with the results.

## Model and fit

1. Inspect the data coverage and group physically distinct scans. Flag duplicate measurements, non-finite values, non-positive errors and inconsistent target labels. Low-energy points are not dropped silently, and different resonances or efficiencies are not combined.
2. Construct the stopping per active isotope from the chosen elemental or compound data and composition convention. Fit an identifiable inactive/active ratio rather than two abundances that enter only through their ratio. Check electronic against total stopping and any compound correction.
3. Obtain a sufficiently resolved cross section for the intended channel and angular acceptance, over the full integration and broadening domain. A validated table can be reused. New AZURE2 results are generated with the `azure2` skill, if installed, and their output definition verified; the old server wrapper of the example is not run automatically.
4. Choose a uniform layer, a truncated Gaussian or another justified profile, state its normalisation and support, and fold cross section and stopping with the beam spread and the depth-dependent straggling, following [model-and-fitting.md](references/model-and-fitting.md). Start with a transparent model and add complexity only when the measurements can constrain it.
5. Test the forward model before optimising it: the analytic limit of a constant cross section, the behaviour without broadening, unit and frame consistency, input coverage, numerical convergence and the recovery of synthetic parameters.
6. Fit only parameters the model uses, with physical constraints and an appropriate likelihood or covariance. Test multiple starts and inspect residuals, parameter correlations, bounds and rank. Statistical uncertainty is kept separate from the efficiency, stopping, calibration and nuclear-model systematics. A forward plot with hand-picked parameters is not a fit.
7. Report only identifiable quantities. An energy-loss width is converted to an areal or physical thickness only with a consistent model of stopping, composition and density. A target that changed during the measurement is fitted jointly or per scan, as its acquisition history requires.

## Scripts

[usability.md](references/usability.md) describes the complete fit configuration and outputs. The helpers need Python, NumPy and SciPy, and Matplotlib for fit reports; they do not require ROOT, lmfit or a running AZURE server.

- `scripts/fit_target.py CONFIG.json --out NEW_DIRECTORY` fits named, bounded parameters with repeated starts, checks the rank, and saves fit, residual and profile plots, the covariance and an HTML report.
- `scripts/srim_table.py INPUT.stop OUTPUT.csv --component total` parses the supplied SRIM format, accepts decimal commas, and converts to lab keV and keV cm²/atom. Choose `electronic`, `nuclear` or `total` explicitly. It refuses to overwrite its output.
- `scripts/target_model.py CONFIG.json --out NEW_DIRECTORY` evaluates the energy-loss-coordinate approximation and saves the predictions with input hashes. The JSON and table contract and the API are in [model-and-fitting.md](references/model-and-fitting.md). It rejects queries outside the table coverage instead of silently holding the endpoint values. It is a forward model, not an automatic fit nor a complete depth-transport solver.

[example-audit.md](references/example-audit.md) is the record to read when reusing the original notebooks: it lists the traps demonstrated, the behaviour tested and the measurement metadata still unresolved. The skill itself does not depend on the original notebooks. `python scripts/demo.py --out NEW_DEMO` produces editable synthetic inputs and a complete fit and report. [agent-code.md](references/agent-code.md) is to be read before extending the helpers; dependencies are listed in `requirements.txt`.

## What to deliver

- The model definition and assumptions, the data selection and the normalisation.
- Fitted or fixed parameters with units, uncertainties and correlations.
- Data-model plot with residuals, and a profile plot whose coordinate is labelled explicitly.
- The numerical checks and the reproducible inputs and results.

A claim on physical thickness or stoichiometry explains how the inferred quantity maps onto the target and which external inputs constrain it. Manually chosen curves and sensitivity envelopes are labelled as what they are.
