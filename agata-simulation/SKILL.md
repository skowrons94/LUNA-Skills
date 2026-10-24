---
name: agata-simulation
description: Run and analyse the official AGATA Geant4 simulation (gitlab.com/malabi-agata/agata) for gamma-ray feasibility studies: custom array geometries (e.g. one triple cluster in close geometry), external event files with user-generated gamma cascades, list-mode output parsing, PSA/energy-resolution emulation, summing and gamma-ray tracking (OFT/MGT). Use for any AGATA efficiency, summing, Doppler, tracking or count-rate simulation, or when debugging the Agata executable, its macros, geometry lists or GammaEvents output; other Geant4 applications use `geant4-simulation` or `underground-gamma-simulation`.
---
# AGATA simulation

An AGATA feasibility study asks what the array, or part of it, would record for a given reaction: full-energy efficiency, summing, Doppler broadening, tracking performance or count rates. This skill runs the official AGATA simulation code (Geant4) for such a question and keeps every number traceable to a run, a geometry and a seed. The AGATA code must be installed. You need the array configuration, the gamma cascades or the reaction, and the detector response to be emulated. You get run directories with macros, compressed logs and `hits.npz` files, a manifest with seeds and executable hash, and the efficiencies, summing and tracking results derived from them. The known-good build, worked examples and validated pitfalls come from two studies: inverse kinematics with SAURON (`-TargetEx` generator), and 14N(p,γ)15O cascades (one triplet at 20 mm, external events, summing-in tag, OFT).

## Where this fits

- Comes from: gamma cascades and kinematics computed by the user's own generator, written as lab-frame external event files; c.m. angular distributions for `-TargetEx` (e.g. TALYS dσ/dΩ).
- Goes to: `delta-beta-dsam`, for the Δβ lifetime analysis of the output; `proposal-analysis`, for the detector response in a feasibility case.
- Checked by: `scripts/check_energy.py` after every production, the geometry check of rule 7, a comparison with something measured, and `physics-referee` before a number is quoted.

Other Geant4 applications are not run here: a new or general application belongs to `geant4-simulation`, and a LUNA-type underground gamma setup to `underground-gamma-simulation`.

## Guides and scripts

- Build, environment and how to launch: [references/build-and-run.md](references/build-and-run.md).
- Geometry, with array lists and one cluster at a chosen distance and angle: [references/geometry.md](references/geometry.md).
- Event generation, with external event files and the `-TargetEx` reaction generator: [references/events.md](references/events.md).
- Output format, offline packing, detector response, analysis and tracking: [references/output-and-analysis.md](references/output-and-analysis.md).
- `scripts/agata_lm.py` parses `GammaEvents.NNNN` into a compact npz with one point per (event, crystal, segment) and the emitted gammas.
- `scripts/check_energy.py` runs the energy-conservation test of a converted run.

## Rules and their reasons

1. The binary runs outside the Claude Code sandbox (`dangerouslyDisableSandbox: true`), because it cannot map the dyld shared cache inside it.
2. Never use `/Agata/file/packingDistance` > 0, because it roughly doubles the energy written per crystal: packed/unpacked was 2.0–2.15 for 7 MeV γ. Write all steps with the default packing 0 and pack offline.
3. After every production, test energy conservation per event, that is, deposited ≤ emitted. This is the check that caught the packing bug.
4. With `-Ext`, `/run/beamOn N` counts emitted particles, not cascades. Set N ≫ particles in the file, so that the run ends at the end of the file.
5. The event-file path is resolved relative to the `-Path` geometry directory, and absolute paths fail because of a `substr(0)=="/"` bug under G4V11. Use a relative path such as `../../runs/<run>/events.txt`.
6. `-seed` takes no value and seeds from the clock. For reproducibility, put `/random/setSeeds a b` in the macro.
7. Verify the geometry before production: the hit positions, that is, the x, y, z of the interaction points, must land where the crystals were placed. Print the minimum distance of the hits from the target.
8. With `-TargetEx` the stock code is broken, with products at rest, α at one azimuth, an inverted theta veto and a SAURON overlap. Apply the 28Si patches and check the light-product φ and θ distributions before production ([references/events.md](references/events.md)).
9. The world is vacuum (`G4AGATAVACUUMINWORLD=1`), because the default air distorts charged-particle energies and DSAM. The ancillary is enabled before `/run/initialize`, since otherwise it is not built. The recoil's radioactive decay is suppressed (`/process/had/rdm/thresholdForVeryLongDecayTime 1 us`), because it is otherwise emitted in the prompt event and adds 511 keV and β+ energy. Lifetimes are set in G4ENSDFSTATE and branchings in PhotonEvaporation ([references/build-and-run.md](references/build-and-run.md)).

## Method

The physics that matters is generated outside Geant4, and the detector response is applied offline, so that both can be varied without repeating the transport.

1. Generate the physics outside Geant4 when it matters, for kinematics, recoil, lifetimes/DSAM and angular correlations, and pass lab-frame γ rays (FORMAT 2 0). Store all emitted directions, so that angular distributions can be applied later as event weights instead of re-running.
2. Emulate PSA offline, with one point per hit segment and energy-dependent position smearing, together with the core and segment resolution and thresholds. Vary these as systematics.
3. Validate against something measured, such as a literature summing ratio, a source efficiency or a resonance branching, before drawing conclusions.
4. Keep geometry dirs (`simulation/geometry/<name>/` with symlinks + generated `aeuler`), runs (`simulation/runs/<config>/<run>/` with macro, compressed log, `hits.npz`) and a manifest with seeds and executable hash.

## What to deliver

- The geometry directory and the run directories with macros, compressed logs and `hits.npz`.
- The manifest with seeds and executable hash.
- The energy-conservation and geometry checks, and the measured quantity the simulation was validated against.
- The derived efficiencies, summing or tracking results, with the response parameters varied as systematics.
