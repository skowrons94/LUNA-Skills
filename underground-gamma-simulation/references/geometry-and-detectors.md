# Changing geometry and adding detectors

Use the actual checkout's component, messenger, hit and action classes as the interface contract. These paths refer to the local source examined for this skill, relative to `code/`.

## Modify an existing setup

Start at `src/DetectorConstruction.cc`. Trace the component's `Construct()` and its placement in the mother volume. Existing implementations are under `shared/src/detectors/` and `shared/src/setup/`; materials are built by `shared/src/setup/auxiliary/Materials.cc`. Corresponding headers and messenger implementations define public setters, macro commands and units.

For a position, dimension, material or thickness change:

1. Establish dimensions and coordinate conventions from the user's drawing or model: full length versus half-length, units, rotation order, mother coordinates and beam direction. Check isotope fractions/density separately from the material name.
2. Prefer an existing macro parameter **only if it is wired to the geometry actually constructed**. The examined target backing ignores its advertised thickness parameter and uses a hard-coded thickness. Document such discrepancies rather than reporting a scan that changes nothing.
3. If no working parameter exists, add a component member/default, setter and messenger command, with dimensional units, bounds and supported application states. Read the value during construction. Restrict it to pre-initialization unless geometry rebuilding is explicitly implemented and tested.
4. Update the solid/logical volume and its placement together. A daughter must fit the mother's actual solid; putting it in a visually empty hole of a union solid is not valid containment. Transform positions when changing mothers. Attach a named rotation with understood lifetime and convention.
5. Rebuild for C++ edits and start a fresh process. For parameter scans use separate processes initially. A setter that changes a member after `/run/initialize` does not necessarily change the already constructed solid; use a verified geometry-reinitialization implementation for interactive changes.
6. Inspect the resulting placements/materials and run `/geometry/test/run` after initialization. Check target/backing contacts, crystal gaps, dead layers and nested assemblies. The local BGO component's internal overlap flag creates extra placements, so use the external diagnostic instead until that code is corrected.

Keep a parameter/geometry summary with the output so detector positions, materials and copy-number mapping remain interpretable. Refer to [validation-record.md](validation-record.md) for the local split-BGO fixes; those fixes are not generic geometry templates.

## Add a new detector end to end

Adding a solid does not make it sensitive, and making it sensitive does not automatically save its hits. Follow this complete chain:

| Layer | Local example | Required work |
|---|---|---|
| Detector geometry | `shared/src/detectors/BGO/BGO14Np.cc` | Define active and passive volumes/materials; expose the active logical volume or a reliable attachment interface |
| Placement | `src/DetectorConstruction.cc` | Construct and position it; choose unique copy-number/hierarchy conventions |
| Sensitive detector | `BGO14NpSD.cc` | Register with `G4SDManager`; attach to the intended active logical volume |
| Hit representation | `BGO14NpHit.hh/.cc` | Define the per-step or aggregated quantities and ownership |
| Hit collection | SD `Initialize()` | Create a collection for each event and attach it to the event hit container |
| Response accumulation | SD `ProcessHits()` | Populate fields from steps using explicit pre/post-step semantics |
| Event readout | `src/EventAction.cc` | Resolve the collection, handle absent collections and aggregate hits |
| Persistent output | `src/AnalysisManager.cc` | Own buffers, reset them, define branches, fill and write them |

Reuse a suitable existing Ge/Si/BGO implementation when its assumptions fit. Give a new SD and collection distinct names; prefer unambiguous SD/collection identifiers for lookup. If instances share a logical volume, an attached SD applies to every placement: distinguish instances with the touchable hierarchy, not just an assumed top-level copy number. Keep channel IDs stable and document them.

The local BGO SD creates **one hit per nonzero-energy-deposit step**. Its `ProcessHits()` returns early when deposit is zero. This is suitable for calorimetric response but misses zero-deposit crossings, incident flux, some neutral-particle entries and track-length tallies. Choose the hit condition for the observable; do not copy this condition unquestioningly. Define whether position/time refers to entry, exit, a step or the first hit. Sum deposits once per event/channel; avoid counting both hit totals and their constituent steps.

The local SD casts `TrackInformation` without a null check. A new generator/tracking action may not supply it. Preserve the tracking-information contract or check safely and define what missing ancestry means. Do not silently manufacture ancestry or original gamma energy.

`EventAction::EndOfEventAction` currently returns immediately when the BGO collection ID is invalid. A new-detector-only configuration would therefore lose its readout unless that early return is refactored. Read each enabled collection independently and fill the event according to the requested selection even when BGO is absent. Update detection/trigger selection to include the new detector explicitly; otherwise the ROOT tree may discard precisely the new events of interest.

Allocate/reset buffers for all possible channel IDs and check bounds at the producer. Changing segmentation requires updating channel storage, noise/threshold handling, multiplicity and event filtering, not just geometry. The local source also has fixed secondary arrays; review capacity when adding high-multiplicity detectors or generators.

## Validation for a new detector

Use a simple controlled source aimed at the active volume. Check expected hit presence, correct copy IDs and units, aggregation and events with no hit. Test a miss, a passive-volume interaction and each detector instance. If crossing counts are required, test zero-deposit entries and distinguish re-entry from first entry. For energy response, compare against a suitable known source or analytic limit before a complex reaction.

Check overlap diagnostics, finite energies, channel bounds, ROOT schema, event selection and independent-seed behavior. Re-run an existing baseline to identify unintended changes. Document any unsupported optical transport, charge collection, dead layer, resolution, threshold, pileup or electronics model that matters to the intended observable; do not imply these effects exist just because the detector material was added.

Connect the implementation to [root-output.md](root-output.md) and, when source assumptions change, [event-generation.md](event-generation.md).

For controlled distance/angle, target/backing and dead-layer scans, read [geometry-scans.md](geometry-scans.md).
