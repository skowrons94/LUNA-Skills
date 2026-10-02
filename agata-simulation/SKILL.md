---
name: agata-simulation
description: Run and analyse the official AGATA Geant4 simulation (gitlab.com/malabi-agata/agata) for gamma-ray feasibility studies — custom array geometries (e.g. one triple cluster in close geometry), external event files with user-generated gamma cascades, list-mode output parsing, PSA/energy-resolution emulation, summing and gamma-ray tracking (OFT/MGT) analysis. Use for any AGATA efficiency, summing, Doppler, tracking or count-rate simulation, or when debugging the Agata executable, its macros, geometry lists or GammaEvents output.
---
# AGATA simulation

Simulate what AGATA would record, and keep every number traceable to a run, a geometry and a seed.
Known-good build, worked examples and validated pitfalls come from two projects:
`~/Desktop/28Si` (inverse kinematics with SAURON, `-TargetEx` generator) and `~/Desktop/LUAGATA`
(14N(p,γ)15O cascades, one triplet at 20 mm, external events, summing-in tag, OFT).

## Route the task

- Build, environment, how to launch: [references/build-and-run.md](references/build-and-run.md).
- Geometry (array lists, one cluster at a chosen distance and angle): [references/geometry.md](references/geometry.md).
- Event generation (external event files, `-TargetEx` reaction generator): [references/events.md](references/events.md).
- Output format, offline packing, detector response, analysis and tracking: [references/output-and-analysis.md](references/output-and-analysis.md).
- `scripts/agata_lm.py`: parse `GammaEvents.NNNN` into a compact npz with one point per (event, crystal, segment) and the emitted gammas; `scripts/check_energy.py`: energy-conservation test of a converted run.

## Non-negotiable checks

1. Run the binary outside the Claude Code sandbox (`dangerouslyDisableSandbox: true`): it cannot map the dyld shared cache inside it.
2. Do NOT use `/Agata/file/packingDistance` > 0: it roughly doubles the energy written per crystal (packed/unpacked 2.0–2.15 for 7 MeV γ). Write all steps (default packing 0) and pack offline.
3. After every production, test energy conservation per event (deposited ≤ emitted). This is the check that caught the packing bug.
4. With `-Ext`, `/run/beamOn N` counts emitted particles, not cascades: set N ≫ particles in the file; the run ends at end of file.
5. The event-file path is resolved relative to the `-Path` geometry directory (absolute paths fail: `substr(0)=="/"` bug under G4V11). Use a relative path such as `../../runs/<run>/events.txt`.
6. `-seed` takes no value (seeds from the clock). For reproducibility put `/random/setSeeds a b` in the macro.
7. Verify the geometry before production: hit positions (x, y, z of interaction points) must land where you placed the crystals; print the minimum distance of hits from the target.
8. With `-TargetEx` the stock code is broken (products at rest, α at one azimuth, inverted theta veto, SAURON overlap): apply the 28Si patches and check the light-product φ and θ distributions before production ([references/events.md](references/events.md)).
9. Vacuum world (`G4AGATAVACUUMINWORLD=1`), ancillary enabled before `/run/initialize`, and the recoil's radioactive decay suppressed (`/process/had/rdm/thresholdForVeryLongDecayTime 1 us`); lifetimes are set in G4ENSDFSTATE, branchings in PhotonEvaporation ([references/build-and-run.md](references/build-and-run.md)).

## Working method

- Generate physics outside Geant4 when it matters (kinematics, recoil, lifetimes/DSAM, angular correlations) and pass lab-frame γ rays (FORMAT 2 0). Store all emitted directions so that angular distributions can be applied later as event weights instead of re-running.
- Emulate PSA offline (one point per hit segment, energy-dependent position smearing), core and segment resolution and thresholds; vary these as systematics.
- Validate against something measured (a literature summing ratio, a source efficiency, a resonance branching) before drawing conclusions.
- Keep geometry dirs (`simulation/geometry/<name>/` with symlinks + generated `aeuler`), runs (`simulation/runs/<config>/<run>/` with macro, compressed log, `hits.npz`) and a manifest with seeds and executable hash.
