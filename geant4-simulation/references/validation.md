# Validation ladder

Each rung proves something specific and leaves the rest unproven. State the highest rung reached next to every simulated number.

| Rung | What it shows | What it does not show |
|---|---|---|
| 1. The run completes cleanly | the code, macro and environment run for this configuration; no fatal exceptions, overlaps, refused commands; requested events generated; outputs present and parseable | that the geometry, materials, physics or source are right |
| 2. Geometry and bookkeeping | dimensions, masses and densities printed equal the drawing and hand values (ideal-gas density, moderator mass); no overlaps over the scanned range; event and weight totals add up; energy conservation per event where testable | that the physics models and data reproduce nature |
| 3. Analytic and reference checks | the physics behaves as expected in limits that can be computed by hand | detector-level accuracy in the real geometry |
| 4. Calibration sources | the full model (geometry, materials, physics, response) for one source and position, with an absolute normalisation | the transfer to other energies, positions or reactions, which still rests on the model |
| 5. Measured data for the observable | the simulated observable for that configuration, with a quantified residual | other observables or configurations |

## Rung 3 examples

- **Thermal diffusion length.** Thermal point source in a large block of moderator, no detectors: in one-group diffusion theory the capture points satisfy ⟨r²⟩ = 6L². Compare L with a textbook value (water about 2.7–2.9 cm, polyethylene about 2.1 cm at room temperature); rerun without thermal scattering to see the bias. The template's `macros/diffusion.mac` does this.
- **Capture time in an infinite medium.** For thermal neutrons the mean capture time is 1/(vΣ_a) with v Σ_a independent of energy for a 1/v absorber (about 0.2 ms in water); the template's `diffusion.mac` writes it as `absorption_time_mean_us`.
- **Narrow-beam attenuation** exp(−Σx) of monoenergetic neutrons or gammas through a slab, scoring only unscattered particles, against tabulated cross sections or attenuation coefficients.
- **Kinematic endpoints and source moments**: maximum neutron energy at 0° from `kinematics.py`; sampled Watt mean 3a/2 + a²b/4; histogram means.
- **Physics-list and data variation**: two HP lists, thermal scattering on and off, a ±density change. These bound model sensitivity; agreement between two lists is not validation.

## Reproducibility

- Seeds explicit on the command line or in the macro (`/random/setSeeds a b`) and written into every output, together with the engine name. Same seeds and same build must give identical summaries; different seeds a different sample with consistent results within statistics. `scripts/test_template.py` checks both for the template.
- The same seeds reproduce only with the same executable, datasets and macro; record all of them. In multi-threaded mode the master pre-draws per-event seeds, so merged totals do not depend on the thread count but the event order does: compare merged quantities, not event order.
- Batches: distinct seeds per batch, recorded in the manifest; never reuse seeds across batches that will be merged.
- Statistical convergence: a result whose uncertainty does not fall as 1/√N, or which moves by more than its uncertainty when N is quadrupled, has a problem (rare large weights, a bug in accumulation, a time cut).

## Run manifests and checks beyond the return code

`scripts/run_checked.py --out RUN --expect FILE --json-min FILE:key=min -- EXE ARGS` runs the job in a new directory and writes `manifest.json` with: command, executable hash, copied input files and their hashes, source revision (`--source`), Geant4-related environment variables (dataset paths), host, load, wall time, return code, number of G4Exception warnings, outputs and their hashes, and a verdict. A run fails when:

- the return code is non-zero or the job timed out;
- the log contains a fatal G4Exception, "Overlap is detected", a refused or unknown command, an illegal application state, a parameter out of range, a segmentation fault or an abort;
- an expected output is missing, empty or not valid JSON;
- a numeric threshold fails (e.g. `gas_captures` ≥ 1, or the generated events equal to the request).

Read the warnings it counts; a run with thousands of warnings is not clean. Keep the manifest with the summary in git; the log can be compressed or dropped once the manifest and summary exist.

## Reporting

In `REPORT.md` and `results.json`: the highest rung reached for each number, the checks behind it with their run directories, the events and seeds, the statistical uncertainty and the model variations. Say plainly when a number rests only on rungs 1–3.
