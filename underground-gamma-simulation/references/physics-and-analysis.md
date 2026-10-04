# Physics and analysis checks

## Detector-response baseline

A calibration source tests decay generation, particle transport, detector attachment and event output without relying on a rare beam-induced capture. A monoenergetic gamma tests a different, simpler response. Do not equate counts per generated gamma with counts per source decay.

Specify the source material/holder, active location and shape, detector dimensions, dead layers, thresholds and resolution model. Check overlap diagnostics, expected spectral features, deposit-energy bounds and hit occupancy. Compare calibrated-source measurements at matching geometry before claiming efficiency accuracy. Account for gamma emission probability and cascade coincidence summing.

The tested split-BGO variant stores `Tree1` with `Edep` (12 raw energy deposits, keV), optional vectors `Zint`, `Ep`, `EgammaRes`, `EgammaDC`, `Pgx/Pgy/Pgz`, `BeamX/Y/Z`, `BeamKinE`, `BeamTheta`, and `Multiplicity`. Trace the producer for each unit: primary positions are mm, energy keV, theta degrees. Do not infer units or an event weight from branch names. In this examined source, `EgammaRes` and `EgammaDC` are declared and cleared but never filled, and `fFusionEvent` is never set true. Do not use these branches or fusion-only storage for reaction counting until the producer is implemented and tested. `Zint` is populated for selected parent-nuclide gammas and can have multiple entries per interaction; it is not automatically a unique reaction counter.

`AllEventFlag=true` stores all events. Otherwise `AllFusionEventFlag=true` selects fusion-tagged events; both false select detected events. Tree length is not necessarily the number of generated primaries. A selected tree cannot supply an absolute-efficiency denominator by itself. Local unpatched split-BGO code checked only the first six channels for detected-event selection.

`Edep` is unsmeared in this implementation even though `EventAction` computes Gaussian-smeared values separately. Setting `/EventAction/NoiseBGO14Np` does not make this branch a measured-resolution spectrum. Follow the actual stored quantity. Sum relevant segments for addback; distinguish per-crystal full-energy peaks, total detection and addback efficiencies. Do not sum duplicate channels or concatenate unlike geometries.

For unweighted independent events and a binary selection, efficiency is k/N and its binomial standard error is sqrt(efficiency*(1-efficiency)/N); use an interval suitable for small or zero k instead of claiming zero uncertainty. Weighted/bias-corrected events require a corresponding estimator and uncertainty treatment. For precision planning, use selected-event statistics, not just primary count.

## Reaction simulation

For file selection, format/units, private overrides and before/after testing, read [data-files.md](data-files.md).

Verify projectile species, target isotope fractions, density/stoichiometry, thickness, beam direction/profile, energy spread and lab versus center-of-mass energy. For a stationary target in the nonrelativistic limit, E_cm = E_lab*m_target/(m_projectile+m_target). For gas targets check measured pressure/temperature profiles and density; for solids check backing and stopping/straggling. Vary step limits and relevant transport cuts to demonstrate observable convergence.

Inspect `PhysicsList`, `HadronPhysicsList`, process registration and the selected final-state class. Avoid double counting overlapping models. In the local interface, `/HadronPhysicsList/PartCapFlag` and `PartCapType` choose charged-particle capture; projectile-specific inelastic flags are separate. A macro filename mentioning a reaction is not proof the implementation/data support it.

Local `ParticleCaptureXS` loads `$G4PARTICLEXSDATA/<particle-name>/capZ` and optional `capZ_A`; resonant capture uses `rescap`. Z/A here describe the target. Missing isotope files can trigger fallback behavior: trace the actual code and applicability ranges. Inspect serialization via `G4PhysicsVector::Retrieve`, energy units, normalization and interpolation in code before generating data files; do not assume a plain two-column keV/barn table.

Local non-resonant `ParticleRadCapture` reads `$G4RADIATIVECAPTURE/<particle-name>/zZ.aA`, where Z/A describe the compound nucleus. It reads rows containing an index, population and four Legendre coefficient ratios. Rows must correspond to the levels accessed in PhotonEvaporation at the selected excitation energy. Validate row count/order, finite nonnegative populations and a positive accessible population sum. This code lacks robust file-read checks before normalization. Missing/inconsistent data may therefore produce invalid physics without a clean error.

The angular rejection sampler in that source draws a uniform ordinate in [0,2] and accepts against W(cos(theta)) = 1 + sum(a_l/a_0 P_l). Check W over [-1,1]: if it is negative or exceeds 2, the implemented sampler is unsuitable without correction. Do not silently clip coefficients or renormalize away a physical mismatch.

Treat custom cross sections and level data as research inputs: record provenance and hashes, preserve originals, and verify reaction Q value, emitted energies, branching, recoil/boost behavior and angular distributions against an appropriate reference. A successful Cs run does not test these reaction models.

## Bias and normalization

A manually enhanced cross section can improve reaction statistics, but dividing event counts by a factor is not automatically valid: attenuation, interaction depth, competition and multiple reactions can change. Identify where bias is applied and whether event weights exist. Compare reduced-bias or unbiased pilots and interaction distributions; justify any thin-target approximation. Report absolute beam-normalized yields only with an established normalization. Do not infer nuclear-data scale factors from filenames.

## Production acceptance

Require completed counts, readable expected outputs, sensible channel occupancy, reproducible same-seed observables, changed-seed independence, overlap review, statistical precision and relevant calibration/physics comparisons. Keep a convergence check for step/cut choices and enough input provenance to reproduce the result. Report outstanding geometry or data-model limitations even when execution passes.

Background reading: [published detector and shielding study, Universe 10, 228 (2024)](https://www.mdpi.com/2218-1997/10/5/228). It describes the modular Geant4/ROOT framework and validation against source/reaction measurements. It does not validate arbitrary local changes or grant a universal accuracy to a new simulation.

For explicit bias estimators and bias scans, read [bias-and-weights.md](bias-and-weights.md). For a new channel, use [reaction-workflows.md](reaction-workflows.md); validate emitted kinematics and Doppler effects using [kinematics-and-doppler.md](kinematics-and-doppler.md).
