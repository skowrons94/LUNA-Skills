# Reproducibility, validation, and handoff

## Minimum reproducibility record

For every reported result, retain:

- source file and citation or collaborator provenance;
- checksum or stable external identifier when practical;
- input units and the normalized internal units;
- reaction, channel, energy frame, charge-state convention, and beam normalization;
- code revision and named configuration;
- software or solver version;
- random seed policy and number of events for Monte Carlo work;
- output table and plot generated from it;
- validation status and known limitations.

Store stable project-wide settings in `project.yaml` and analysis-specific variants in `configs/`. Do not bury a decisive constant only in a notebook cell, figure script, or slide.

## Validation ladder

Use the strongest available checks:

1. Dimensional and unit tests.
2. Conservation laws, sum rules, thresholds, and analytical limits.
3. Numerical regression against a small trusted case.
4. Comparison with independent code or calculation.
5. Comparison with calibration or measured data.
6. Sensitivity to model choices, binning, integration limits, detector resolution, and background assumptions.

For R-matrix work, report datasets included, normalizations, channel radii, fit status, chi-squared definition, residuals, saved parameters, extrapolation limits, and alternative solutions that materially affect the conclusion.

For detector simulation, validate geometry and response with known dimensions, monoenergetic tests, calibration peaks, efficiency curves, or measured spectra. Separate physics-model uncertainty from finite Monte Carlo statistics.

For thick-target yields, test integration convergence, stopping-power units, energy-frame conversion, target composition, and branching normalization. Preserve at least one calculation that can be checked independently by hand.

## Assumptions and decisions

`docs/ASSUMPTIONS.md` is a live register of uncertain inputs. Each entry states the adopted value or scenario, evidence, effect on the result, and what measurement could replace it.

`docs/DECISIONS.md` records choices that change the analysis, such as adopting a cross-section envelope, promoting an R-matrix fit to master, excluding a dataset, choosing a detector window, or changing a target model. Include the date, decision, evidence, alternatives, and consequence.

Do not rewrite history after a correction. Add the new decision, mark the earlier one superseded, and note which results were regenerated.

## Handoff

Update `docs/HANDOFF.md` at the end of a work cycle with:

- the question and current conclusion;
- authoritative inputs and master model;
- exact workflow order or one-command entry point;
- headline results and uncertainty scenarios;
- validation completed;
- corrections that must not be reintroduced;
- open scientific and technical items;
- deliverables and their build locations.

A handoff is a state description, not a second report. Keep it compact, operational, and honest about what remains soft.
