# Recording new observables in ROOT

Choose the scientific quantity and its sampling level before changing branches. A file can contain a branch that is never populated: the local `EgammaDC` and `EgammaRes` branches demonstrate this. Trace producer → event buffer → selection → `TTree::Fill()` → file write, and test the stored values.

## Decide what a row means

For each requested quantity, specify name/type, units/frame, definition, event/track/hit scope, source callback, empty-value convention and selection. Examples:

| Observable | Appropriate producer | Definition to settle |
|---|---|---|
| Total deposited energy per detector | SD hits aggregated in `EventAction` | Raw or smeared; channel/addback grouping; threshold |
| First-arrival time | SD/stepping information | Global or relative time; first entry versus first deposit |
| Reaction vertex and incident energy | Reaction-producing step/process | Which process; pre-step energy; one row per reaction |
| Generated primary kinematics | Primary generator / actual event vertices | Per primary, lab/CM frame, weight and source index |
| Emitted gamma energy/angle | Selected secondary creation or generator | Reaction gammas versus later transport secondaries; parent/process |
| Track entry or exit | `SteppingAction` with boundary selection | First crossing or all crossings; volume pair and direction |

For an event tree, keep one row per selected event and vectors for variable multiplicities. For a separate hit/track/reaction tree, save run and event IDs plus track/parent/channel identifiers as appropriate. Track IDs are event-local, and event IDs can repeat across runs: do not join by track ID alone. Keep a run/batch identifier when merging files. Specify a validity flag or documented sentinel for absent scalars; zero may be a physical value.

## Change the local output pipeline

1. Add persistent typed storage to `include/AnalysisManager.hh`, plus the setter/append method needed by the producer. ROOT branch addresses must refer to storage that lives through every fill; do not bind a branch to a temporary or a local stack variable that goes out of scope. Prefer ordinary scalar/STL types with existing ROOT support, or supply dictionaries for custom classes.
2. In `AnalysisManager::BeginOfRun()`, create branches after the file/tree is created. This variant writes `Tree1` directly with ROOT rather than the Geant4 analysis ntuple API. Include units in new names or record an explicit schema; preserve established branch meanings unless a versioned schema change is intended.
3. Add initialization/reset at the correct lifecycle point. Existing `ClearVariables()` runs from `BeginOfEventAction`; `ClearPrimaries()` runs at event end. Primary generation can happen before `BeginOfEventAction`, so clearing newly written primary data there can erase it. Reset primary buffers before producing primaries or in another verified lifecycle location; test first, second and zero-hit events for stale or lost values.
4. Populate data at the chosen callback. In `EventAction`, convert units explicitly and aggregate detector hits. In `SteppingAction`, filter process/volume/particle and boundary state so the same physical occurrence is not recorded on every step. Guard null process and volume pointers, particularly at world boundaries. Record IDs if multiple secondaries must be grouped into one interaction.
5. Call `tree1->Fill()` once for each accepted event after its buffers are complete. For extra hit/reaction trees, fill at their defined granularity. Review `AllEventFlag`, `AllFusionEventFlag` and detected-event selection when new detectors or triggers are added. Preserve total generated-primary/event counts separately from selected-tree length.
6. Add a messenger flag only if users need to enable/disable expensive output. Wire it to an initialized member and actual branch creation/filling; merely adding a command is insufficient. Establish schema before the run and avoid toggling branches halfway through a tree.
7. Preserve `EndOfRun()` writing/closing, check file creation failures and reopen the file for validation. The local file is opened with `RECREATE`; use distinct filenames. Add run metadata such as geometry/configuration ID, generator mode, units/schema version, event count, seeds and data provenance, in ROOT or a clearly linked manifest.

Raw energy, reconstructed energy and weights should have distinct fields. If weights are introduced, document whether each is a primary, track, event or selection weight and how downstream estimators combine them. Do not silently report an unweighted histogram as a normalized physical yield.

The local `Multiplicity` is a vector appended during secondary analysis despite representing an event-level count. Inspect its actual cardinality before consuming it. The hard-coded O-16 selection used to populate `Ep` is not a generic incident-energy definition. Implement the intended producer instead of relying on a convenient branch name.

## Verify the new schema and values

Rebuild, run a small deterministic case, then reopen ROOT and check branch types, lengths, units and representative values. Verify no-hit/absent-value behavior, per-channel sums, aligned parallel vectors, reset between events, and selection denominators. Compare at least one quantity with an independently calculated expectation or a diagnostic from the producer. Repeat with changed geometry/source so the new field responds as expected; test a disabled-output flag if provided.

`scripts/inspect_root.py` currently checks the existing BGO `Tree1/Edep` schema only. Extend it or write a focused check for new branches and other detectors; its success does not validate fields it never reads. Update downstream notebooks and merged-output assumptions with the schema change. Estimate per-event storage from a pilot before enabling all step/track data in production.

The tested executable uses serial `G4RunManager`. Shared ROOT buffers/files are not a valid multithreading design by default. If converting the application to MT, explicitly design worker-local state and supported output merging; do not share this serial `AnalysisManager` unchanged.

For biased or Doppler-sensitive work, use the per-history scoring contract in [bias-and-weights.md](bias-and-weights.md) and the per-photon truth fields in [kinematics-and-doppler.md](kinematics-and-doppler.md). Record weights without changing the energy-axis values; a declared but unfilled truth branch cannot validate either effect.
