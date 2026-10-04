# Adapting the simulation to a different reaction

A new reaction is a coupled change to material, incident particles, reaction probability, final states and output interpretation. A changed macro title or GPS ion does not supply these components.

## Prepare a reaction record

Record `a+A -> products`, target isotope fractions, incident lab-energy range and spread, target density/thickness/profile/backing, total versus channel cross section and energy frame, final levels and branch convention, angular law, source of masses/Q values, lifetimes, enabled competing processes and what one generated event represents. Mark unknown inputs rather than deriving them from filenames. Compare the planned observable with measured calibration or a numerical benchmark where available.

## Select the implementation route

| Requested physics | Candidate route | What must be established |
|---|---|---|
| Radiative capture `(p,gamma)` or `(alpha,gamma)` | Local custom capture if registered for that projectile/isotope | Physical XS table, compound-state populations, primary anisotropy, level/decay data, recoil behavior |
| Narrow resonant capture | Reviewed resonant model or a validated externally sampled reaction | Energy-dependent resonance yield, beam/target energy spread, actual level match, cascade and lifetime |
| `(p,alpha)`, `(alpha,n)`, `(p,n)`, other particle channels | An applicable inelastic model/data library or a custom final state | Thresholds, channel/level branching, product correlations and angular distributions; capture population files cannot describe these |
| Elastic/inelastic scattering | Applicable registered process and model | Differential law, recoil/excitation, competing transport and cut sensitivity |
| Detector response for a specified channel | Correlated reaction-product generator | Reaction-depth/energy distribution and external normalization per beam ion |
| Calibration decay | Stationary parent and decay processes/data | Parent state, holder/geometry, daughters, gamma probabilities and counting-time convention |

These are routes to inspect, not promises of built-in support. The local physics list contains projectile-specific inelastic branches and custom capture registrations; verify the one your selected particle actually uses. Do not assume a generic-ion selection activates the special local carbon-ion path. Cross-section library coverage and model validity must include the entire slowing-down range and all relevant target/backing constituents.

## Worked migration: 19F(p,gamma)20Ne to 14N(p,gamma)15O

This is an identifier/configuration example, not a supplied evaluated simulation:

- Change the active target isotope to Z=7,A=14 and its real chemical host/density/profile. Natural nitrogen and pure 14N are distinct choices; update stopping and unwanted reactions as needed.
- Keep proton beam identity but establish the new entrance energies, beam distribution and reaction-energy coverage.
- Inspect the reader's selection of target cross-section files `proton/cap7` or `cap7_14`, rather than carrying over `cap9`/`cap9_19`. Verify supported isotope indexing and fallback.
- The compound population/level identity becomes Z=8,A=15, such as the local custom population path `proton/z8.a15`; it is not the target identity. Rebuild the population-to-level correspondence and gamma anisotropy from the intended channel data.
- Review masses, primary energies, cascade branching/lifetimes, detector windows and gamma ancestry filters. Hard-coded parent-nuclide selections in tracking or stacking can make a physically generated new channel invisible to old diagnostics.
- Validate generated products before detector smearing, then compare measured/benchmark response. Normalization belongs to the new reaction and its actual target.

For 13C(alpha,n)16O, merely substituting alpha GPS and a capture file would instead describe the wrong final state. The neutron and oxygen recoil require the appropriate two-body/level channel (or a more complete final state), cross section and neutron transport. For 12C+12C with proton/alpha channels, preserve distinct residual levels and branch fractions and audit the special projectile registration; one generic capture cascade is insufficient.

## Thick targets and gas profiles

Use reaction-vertex energy after stopping. The thin-reaction-probability baseline is `Y = integral n_active(x)*sigma(E(x)) dx`, with stopping from the full mixture. When attenuation or competing processes matter, include survival/transport explicitly. An externally generated reaction sample needs the joint depth/energy/channel distribution; uniform depth is not generally correct near a narrow resonance. For a gas target, define pressure/temperature/density and beam-heating profiles with their uncertainties. For a compound, distinguish atom ratios, mass fractions and reactive-isotope fraction.

## Minimal channel checks before production

Test just below/above a physical threshold, fixed-energy kinematics, inaccessible levels, branch normalization, missing files and a zero/disabled channel. Verify reaction tags identify actual interactions, not individual photons or every track step. Check at least one unchanged calibration baseline after adding a process. Record the actual selected model and input files in output; a complete event count is not evidence that the requested channel occurred.

Use [bias-and-weights.md](bias-and-weights.md) for rare-event strategy and [kinematics-and-doppler.md](kinematics-and-doppler.md) for product and line-shape validation. Keep unverified reaction recipes labeled as configuration plans until executable and physics checks pass.
