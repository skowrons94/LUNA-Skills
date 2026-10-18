# Scoring and output

## Choose a scoring route

- **Stepping action** (`G4UserSteppingAction`): test the pre-step volume and accumulate into per-event buffers. Short and transparent for a few volumes; the template uses it.
- **Sensitive detectors** (`G4VSensitiveDetector` + hits collection, attached with `SetSensitiveDetector` or `G4SDManager`): the standard route for many channels, readout geometry and per-hit information; hits are processed in the event action.
- **Primitive scorers** (`G4MultiFunctionalDetector` with `G4PSEnergyDeposit`, `G4PSCellFlux`, `G4PSNofSecondary`, ...) and **command-based mesh scoring** (`/score/create/boxMesh`, `/score/quantity/...`) for flux or dose maps without code.

Whatever the route: reset per-event buffers at the start of each event, accumulate per run, and write at the end of the run. Keep the generated-event count and summed weights next to every tally.

## Captures

- Identify a reaction by its products in the step where the neutron interacts: 3He(n,p)t → proton + triton; ¹⁰B(n,α)⁷Li → alpha + ⁷Li; ⁶Li(n,t)α → triton + alpha; H(n,γ)d → deuteron + gamma. Loop over `step->GetSecondaryInCurrentStep()`.
- Process names (`nCapture`, `neutronInelastic`, ...) depend on the version and the list; print the name once for each reaction you score, and do not rely on it for reactions that are not radiative capture. The template counts gas captures by products and "captures anywhere" by the `nCapture` process.
- Count the first capture per event for efficiency and time; count all captures if multiplicity matters (sources emitting several neutrons per event, cosmic showers).
- Store the capture position when spatial information is needed (diffusion checks, tube-by-tube rates).

## Energy deposits

- Sum `step->GetTotalEnergyDeposit()` per sensitive volume and event. In a 3He tube, a full-energy capture deposits 764 keV (proton 573 keV + triton 191 keV); wall effects give a continuum down to the triton or proton energy, so a counting threshold (often 100–200 keV) trades gamma rejection against efficiency. Report efficiency both for captures and above the threshold.
- Electronic noise, gas gain and quenching are not in the transport; apply resolution and thresholds in the analysis and vary them as systematics.
- For scintillators and semiconductors, apply light yield (Birks quenching for heavy ions) or energy resolution offline, from a calibration.

## Timing (die-away)

- Use the global time of the post-step point of the capture step, measured from the primary emission at t = 0 (Geant4 time units are ns; write µs with the unit in the key).
- Histogram capture times on a logarithmic axis for the overview and on a linear axis for gate studies; keep enough range to see the late tail (moderated systems: several hundred µs and beyond).
- For pulsed sources, apply the pulse structure in the analysis (convolution with the pulse shape) rather than in the generator, unless pile-up between pulses is the question.

## Weights

- Event weights from the generator (`G4PrimaryVertex::SetWeight`) propagate to tracks (`track->GetWeight()`). Accumulate Σw and Σw² for every tally; the uncertainty of a weighted count is √Σw².
- Biasing (importance, forced interactions, cross-section scaling) changes weights; keep the unbiased denominator and validate the biased result against an unbiased run on a small case.

## Output

- One small machine-readable summary per run (JSON): configuration (geometry, source, physics list, thermal scattering, cuts), Geant4 version, seeds, engine, events generated and summed weights, tallies with units in the key names, histograms with their bin definitions. This file is what `results.json` and the proposal consume.
- Optional per-event or per-hit output (CSV with a header row and units; ROOT or HDF5 through `G4AnalysisManager`, chosen by file extension, when volume demands it). Per-event files are large: git-ignore them and keep the summaries.
- Write outputs into the run directory given by the macro or command line, never into the source tree; one directory per run, with its log and manifest (`run_checked.py`).
- Multi-threaded runs: one file per thread or merged accumulables; check that merged totals equal the sum over threads.
