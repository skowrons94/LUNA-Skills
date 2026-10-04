# Geometry changes and controlled scans

Use [geometry-and-detectors.md](geometry-and-detectors.md) for the implementation chain. This guide covers parameter choices, scans and reproducible comparisons.

## Make the requested dimension unambiguous

“Detector distance” can mean source-to-endcap, source-to-active front face or source-to-crystal center. Store the requested reference surfaces and the derived center coordinates. For a detector facing an interaction point r0, define its active-axis direction from r0 to its center, then derive the placement rotation using that component's local axis. Check the sign with a directed gamma test; changing a rotation without moving the center does not perform an angular scan around the target.

A useful scan record includes case ID, nominal controls, actual placements, active/passive dimensions, material densities and isotope abundances, source/reaction profile, channel map, seeds, generated primaries and scored observable. Record the world transform `r_world = R*r_local + t`; nested transforms compose in order. Geant4 solid arguments often use half lengths; keep full physical thickness in user-facing configuration and convert once.

When changing target thickness, keep the intended surface anchored: if the beam-facing surface is fixed, shift the layer center by half the thickness change. Move the backing/contact consistently and keep source vertices in the intended material. A tilted flat layer increases beam path length approximately by `1/abs(cos(theta))` only while lateral escape and finite extent can be neglected. Distinguish physical thickness, areal density and beam energy loss.

## Scans that produce interpretable results

- **Distance/angle:** recompute center/rotation relative to the reaction position; preserve or explicitly vary absorbers, endcap and source holder. Monitor solid angle, attenuation and Doppler acceptance.
- **Dead layer or endcap:** change the passive region and active dimensions consistently. Do not keep both active and passive volumes occupying the same space. Validate low-energy response and material density.
- **Segmentation:** update physical placements, SD attachment, touchable/copy mapping, buffer size, threshold/noise, addback and event selection together. Give channels stable identities.
- **Target/backing:** record isotope/composition and density as well as dimensions; rerun stopping/reaction-depth diagnostics and unintended backing-channel checks.

Prefer a new process for each case. Generate macros from a reviewed template, ensure each changed command is wired to construction, and use separate outputs. Compare printed actual dimensions/materials, not only macro text. The local target/backing code includes hard-coded dimensions; an advertised parameter may have no effect.

If interactive rebuilding is necessary, use the installed Geant4 geometry lifecycle and notify the run manager when dimensions, placement or material change. Recreating a construction can invalidate logical-volume pointers, SD attachments and collection assumptions; test successive rebuilds for duplicate detectors/volumes and stale mappings. The official [dynamic-geometry guide](https://geant4.web.cern.ch/documentation/dev/bfad_html/ForApplicationDevelopers/Detector/Geometry/geomDynamic.html) describes opening/closing geometry and run-manager notification. It does not make arbitrary local setters effective.

## Geometry and response acceptance

Run overlap checks after initialization and inspect the relevant cross-sections visually. Surface sampling is useful evidence but not a mathematical proof of no overlap. Inspect containment, touching boundaries and active/passive interfaces separately. Test a source at the expected location and rays that hit/miss the intended detector; inspect channel occupancy and truth positions.

For a small detector facing a distant point source, detection efficiency should approach a solid-angle trend near inverse distance squared only when attenuation and interaction response are otherwise stable. Do not impose that trend at close geometry, for an extended target or for addback/summing-dominated peaks. Compare absolute scores with the correct generated denominator and interval; use weighted estimators if biasing is enabled.

For a systematic uncertainty scan, vary dimensions using their measurement uncertainty and correlations. A wide design scan is not a one-sigma uncertainty band. Keep a nominal case, summarize changes in efficiency/centroid/width, and retain case-specific geometry and response files so a selected design can be reproduced.
