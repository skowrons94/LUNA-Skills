# Build and run

## Known-good build (macOS arm64)
- Source: https://gitlab.com/malabi-agata/agata, commit b1335fd (2026-07-31), in `~/Desktop/28Si/environment/agata`; executable `build/Agata`.
- Geant4 11.2.2 (MT) and ROOT 6.34 from the conda env `main`; compile with Apple clang (`/usr/bin/clang++`); conda clang 18 fails on `<complex>` with the macOS 26 SDK.
- Local patches (`~/Desktop/28Si/environment/agata_local_patches.diff`): custom target `AGATA` renamed `AGATA_all` (collides with `Agata` on case-insensitive FS); `-Wl,--no-as-needed` only if not Apple; configure with `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` (CMake 4). Reaction generator fixes for `-TargetEx` (virtual `ReactionProduct()`, inverted theta window veto, uninitialised `PLEx/TLEx`) — see 28Si `docs/DECISIONS.md` D-006.
```bash
cd environment/agata && mkdir -p build && cd build
cmake .. -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_COMPILER=/usr/bin/clang++ -DCMAKE_C_COMPILER=/usr/bin/clang
make -j8
```

## Launch
```bash
G4AGATAVACUUMINWORLD=1 Agata -Ext -noQT -Path <geometry_dir>/ -b run.mac      # external events
G4AGATAVACUUMINWORLD=1 Agata -TargetEx -a 1 41 -noQT -Path <geo>/ -b run.mac   # reaction generator + SAURON
```
- `-Path` needs the trailing slash. Run from the run directory: output `GammaEvents.0000` is written to the cwd.
- `G4AGATAVACUUMINWORLD=1`: vacuum world (no air).
- Useful macro commands: `/Agata/detector/enableCapsules`, `/Agata/detector/targetMaterial G4_Ti`, `/Agata/detector/targetSize 20 20 <mg/cm2>`, `/Agata/detector/backingMaterial G4_Ta`, `/Agata/detector/backingThickness <mg/cm2>`, `/Agata/detector/rotateArray th ph`, `/Agata/detector/traslateArray x y z`, `/Agata/detector/update`, `/run/initialize`, `/Agata/generator/emitter/eventFile <rel path>`, `/Agata/file/enableLM`, `/random/setSeeds a b`, `/run/beamOn N`.
- List commands: a macro with `/control/manual /Agata/generator/` and `/control/manual /Agata/file/`.
- Speed: ~1500 two-γ cascades/s per thread for one triplet; parallelise with a process pool (Python threads serialise event generation on the GIL).
- Run logs are long (material tables); grep for `COMMAND NOT FOUND`, `abort`, `Could not open`, `Regular end of run`.

## Runtime pitfalls (validated in 28Si)
- Missing geometry files at start-up: build a geometry dir with symlinks to the array files and pass it with `-Path <dir>/`.
- World material defaults to air: always set `G4AGATAVACUUMINWORLD=1` (air distorts charged-particle energies and DSAM).
- Ancillary detectors are not built unless `/Agata/detector/enableAncillary` comes before `/run/initialize` (and `-a 1 <id>` on the command line; SAURON = 41).
- `/Agata/run/beamOn` does not exist: use `/run/beamOn`.
- Radioactive decay of the recoil (e.g. 27Si β+, s-scale) is emitted in the prompt event and adds 511 keV and β+ energy: set `/process/had/rdm/thresholdForVeryLongDecayTime 1 us`.
- One process per run with distinct `/random/setSeeds` (e.g. from a hash of the run name); record seeds and executable hash in a manifest.
- Convert `GammaEvents.NNNN` to npz right after the run and delete the text file (GB per 10^6 events); gzip the log.

## Rendering the geometry (validated in LUAGATA)
- GDML export (`AGATAWRITEGDML=1`, written in `UpdateGeometry` after `/run/initialize` + `/Agata/detector/update`) FAILS for the array: crystals are `CConvexPolyhedron`, unknown to GDML.
- The terminal-mode `AgataVisManager` does not provide a usable RayTracer viewer ("No valid current viewer", then segfault on trace). In `~/Desktop/LUAGATA/environment/agata_luagata`, `Agata.cc` uses `G4VisExecutive` when `AGATAG4VISEXECUTIVE=1`; then `TSG_OFFSCREEN` works (RayTracer still does not):
```
/vis/open TSG_OFFSCREEN 1800x1200-0+0
/vis/viewer/set/autoRefresh false
/vis/drawVolume
/vis/geometry/set/colour geDetCapsL00 0 0.20 0.45 0.80 1   # capsules follow the crystal shape: colour them, hide wlDetL00 (cryostat)
/vis/geometry/set/visibility wlDetL00 0 false
/vis/viewer/set/style surface
/vis/viewer/set/viewpointVector -1 0.55 -0.45
/vis/viewer/zoomTo 1.35
/vis/tsg/offscreen/set/file setup.png
/vis/viewer/rebuild
```
- Logical volumes of one ATC: `geDetCapsL0k` (capsule), `cryPolyL0k` (crystal), `gePassC0k`/`gePassBL0k` (passivated core/back layers), `wlDetL00` (18 cryostat walls). Hiding a capsule hides its crystal; stacked transparent walls wash out colours.
- Extra passive geometry (e.g. a target holder) can be added in `AgataDetectorConstruction` right after `theConstructed->Placement()` (both in `Construct` and `UpdateGeometry`) into `hallPhys`; see the `PlaceLunaHolder` patch (the 14N(p,γ) target holder ported from the underground-laboratory simulation), switched by `AGATALUNAHOLDER=1`. These two identifiers are the names used in the user's patched AGATA code; keep them unless that code is renamed too. When the holder carries the backing, do not also set `/Agata/detector/backingMaterial`.
