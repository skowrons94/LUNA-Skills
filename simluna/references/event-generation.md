# Changing event generation

First distinguish the **primary-event generator** from the **reaction final-state model**. Changing the beam/source distribution is normally a GPS or `PrimaryGeneratorAction` change. Changing capture cascades, reaction branches, resonance behavior or angular coefficients usually belongs to the selected physics model and its data; see [data-files.md](data-files.md). Do not generate reaction products manually while also letting the same beam induce that reaction unless the combination is intentionally designed and normalized.

## Existing local generator

`SimLUNA.cc` creates `PrimaryGeneratorAction` and registers it with the serial run manager. The implementation is `shared/src/actions/PrimaryGeneratorAction.cc`; it owns `G4GeneralParticleSource`.

- `GeneratePrimaries()` dispatches on `DetectorConstruction::GetPhysics()` values `S` and `R`.
- Reaction mode calls GPS and records its primary position, energy and direction.
- Source mode resets `/gps/pos/centre` from `DetectorConstruction::GetSourcePos()` every event before generating the GPS primary. A GPS-only position edit is therefore overwritten.
- `PrimaryGeneratorMessenger` creates `/PrimaryGeneratorAction/` but currently implements no generator control commands. Do not invent mode commands without adding and wiring them.
- The `S/R` setting also affects constructed geometry. A new generator mode must have an explicit geometry choice; simply adding a third character can leave generation or geometry unconfigured.

## Use GPS when it represents the source

For supported changes, modify the macro: particle/ion, energy distribution, direction/angular distribution, point/beam/volume source, position and multiplicity. Check exact GPS command syntax and availability in the installed runtime. Make energy units, source shape and direction explicit. Stationary radioactive ions need `/gps/ene/mono 0 keV`; the supplied Cs example otherwise produced 1 MeV ions. In source mode use the implemented source-position control or deliberately revise the override.

Before a large run, store the actual generated primary distribution and check its position bounds, energy/frame, angular distribution and number of primaries. A target or detector position is not the same as a source vertex. Confirm decay lifetimes/time thresholds and daughter handling for radioactive sources.

The current bookkeeping queries GPS values once after generation. Do not assume it captures every vertex/particle for multiple GPS sources or multiplicities; inspect the actual `G4Event` primary vertices/particles or record each generated primary explicitly. Keep per-primary vectors aligned and distinguish event count from primary count.

## Implement a custom primary generator

Use this when GPS cannot express the needed correlations, external events, beam phase space or controlled reaction-product generation.

1. Define the input contract: species, energy/momentum, position, time, multiplicity, correlations, coordinate frame, units and weights. For a phase-space/event file, define grouping, ordering, malformed-record handling and end-of-file behavior. Do not silently cycle a short file and call the repeated sample independent.
2. Add an explicit mode/member and messenger interface, or a separate `G4VUserPrimaryGeneratorAction` selected in `SimLUNA.cc`. Preserve the baseline path. If keeping the existing class, dispatch to a new generation method and reject unknown modes. Decide how geometry source/reaction selection remains compatible.
3. Use an appropriate Geant4 primary interface, such as `G4ParticleGun` for simple single-particle generation or explicit primary vertices/particles for correlated multiparticle events. Set every required quantity, ownership and particle definition. Sample correlated quantities jointly and transform from CM to lab when needed; do not independently sample daughters that must conserve four-momentum.
4. Use the application's Geant4/CLHEP random engine for reproducible sampling. If an external library has a separate generator, seed and record it explicitly. Keep source sampling, event weights and file provenance in metadata. Do not use wall-clock reseeding for each event.
5. Save the actual generated primaries, event/source identity and relevant weights to analysis storage. Review the primary-buffer lifecycle described in [root-output.md](root-output.md). Ensure new tracks remain compatible with `TrackingAction`, `StackingAction` and any `TrackInformation` assumptions in sensitive detectors.
6. Handle missing files, invalid species, nonfinite/negative energies, impossible kinematics and exhausted input explicitly. Propagate failures into a nonzero process status or a clearly detected aborted run; do not emit empty events unnoticed.
7. Rebuild and test small controlled samples before connecting to complex reaction transport or production batches.

For a generator of reaction products rather than incident beam particles, state what one event means (one reaction, one decay, one incident projectile, or a weighted sample). Supply externally justified reaction probability/normalization if converting per-reaction detector response into yield per beam particle. A product generator alone does not simulate beam energy loss, reaction-depth probability or competing channels.

## Acceptance checks

For deterministic input, compare generated vertices/particles to the input exactly within serialization precision. For sampled distributions, compare energy/position moments and ranges, isotropic angular behavior where intended, correlations and multiplicities with the specified law using sufficient statistics. Check event-level energy/momentum conservation when the source model requires it, including recoil and unobserved products rather than checking gammas alone.

Verify same-seed repeatability, changed-seed differences, file boundaries, zero/one/multiple-primary cases, ROOT records and detector-hit behavior. Compare the unchanged generator mode against the baseline. These are implementation checks; validate the source's physical model separately against its experimental/evaluated inputs.

For exact two-body reference calculations and recoil/lifetime tests, read [kinematics-and-doppler.md](kinematics-and-doppler.md). For per-reaction versus per-beam normalization and weights, read [bias-and-weights.md](bias-and-weights.md).
