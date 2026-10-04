# Validation record — 2026-09-25

## Provenance and scope

The upstream repository redirected to sign-in and cloning returned authentication denied. No upstream commit was fetched. This skill was developed against the user's existing local split-BGO source checkout. There was no `.git` identity in that code directory.

Source and test outputs are preserved separately in the development workspace (`temp/simulation-validation`). The original project and data were not edited. Source-file hashes and selected nuclear-data hashes are in `preflight.json`; each run contains its executed macro, executable hash, dataset paths, log and manifest. The tested executable SHA-256 is `602e9fef90cab881ec957a396b52d3e17bc810f2640638a3e8d74995e3299010`.

## Reproducing this local test

The build used the active `main` Conda environment: Geant4 11.2.2, ROOT 6.34.04, CMake 4.0 and the system Apple Clang compiler. See `configure-conda.log`, `build-conda.log`, subsequent rebuild logs and `environment.sh` in the validation directory. `environment.sh` only overrides project nuclear-data locations; the active Conda environment must already provide standard Geant4 datasets and libraries.

The reusable [stationary Cs macro](../assets/cs137-smoke.mac) targets this variant. The [source patch](local-split-bgo.patch) records the fixes applied **only to the isolated test copy**:

- Attach the sensitive detector to the actual split-crystal logical volume, with a checked lookup.
- Allocate deposited/smeared energy storage for 12 channels; apply event filtering and noise logic consistently across all 12.
- In reaction mode place the thin target in the world just upstream of the backing, with transformed coordinates; omit the reaction layer in source mode to avoid source-holder overlap.

Do not apply this patch blindly to six-crystal BGO, HPGe or upstream versions. Inspect context and use `git apply --check /path/to/local-split-bgo.patch` (or a patch dry run) against a separate matching source copy before applying. It does not implement the missing reaction branches or validate cross sections.

## Results

| Check | Result |
|---|---|
| Build patched local source | Passed |
| Stationary Cs-137, seeds 12345/67890 | 1000 completed events, 1000 Tree1 entries |
| Cs detector response | 792 events with nonzero deposit; all 12 channels populated; no negative/nonfinite deposit values |
| Diagnostic addback window 655–668 keV | 571 events; not a calibrated efficiency |
| Exact repeat of Cs seeds | Identical event-by-event Edep vectors |
| Seeds 98765/43210 | Different Edep vectors; 794 events with nonzero deposit |
| Source geometry, 1000 surface samples per volume | No overlap warnings after fixes |
| Reaction geometry, 1000 surface samples per volume | No overlap warnings after fixes |
| Supplied 19F(p,gamma), 250 keV | 10000 completed events and Tree1 entries; 9980 events with deposits |
| Reaction output sanity | Finite nonnegative deposits, maximum addback 13087.60 keV; Zint populated in 9991 events |
| Real invalid-command test | The application returned zero; checked runner rejected the interrupted batch and missing output |
| Helper regression tests | Three tests pass: explicit seeds/output, rejection of hidden/multiple runs, false-success detection |

Final outputs are in `verified-cs137`, `verified-cs137-repeat`, `verified-cs137-independent`, `verified-source-geometry`, `verified-reaction-geometry`, and `verified-f19`. `root-inspection.json`, `reproducibility.json`, and `reaction-check.json` preserve checks. Earlier failed/intermediate runs remain labeled separately for diagnosis.

## Scientific limits and observed warnings

These are execution and response smoke tests, not experimental validation. The local 19F test produces reaction-tagged positions almost entirely at the target front surface (about -0.0001 mm) and nearly every primary yields a signal. A subsequent reader/unit audit found raw `proton/cap9` values of 5.3e-6 consumed without a barn conversion (5.3e16 barns in internal units before isotope fallback scaling); their intended bias or units remain unverified. See [data-files.md](data-files.md). The cross-section normalization/bias and interaction-depth distribution need investigation before using it for yields or efficiencies. No absolute yield, validated efficiency, branching accuracy or uncertainty budget is claimed.

Geant4 prints repeated non-critical `G4Cache` mutex-destruction errors at shutdown in this environment. Runs complete and ROOT files reopen, but this remains a compatibility/lifetime warning to investigate before production; it is preserved in logs and manifests. The helper does not automatically classify every Geant4 warning as fatal.

The local source declares but never fills `EgammaDC`/`EgammaRes`, and never sets `fFusionEvent` true. Fusion-only output is therefore not usable here. Source position, source kinetic energy, material geometry and output units were checked from implementation and output rather than trusting example comments. Geometry sampling is not a mathematical proof of overlap absence.

No HPGe, inverse-kinematics, neutron, resonant-capture, high-statistics production or cluster execution was tested. Nuclear datasets were read, not changed. Obtain authenticated upstream access if current upstream compatibility is required.

Workspace organization: validation artifacts were subsequently moved into `temp/simulation-validation`. Historical manifests/logs retain their original execution paths as provenance; CMake caches may need regeneration before rebuilding in the new location.

## Expansion checks — 2026-09-26

Re-inspected the preserved local capture/final-state source. The kinematics guide now records the excited-final-state primary-gamma approximation, the existing CM-to-lab boost, and the active resonant path's level matching/geantino fallback; these are code-audit findings, not new transport-validation results. Source hashes for this audit are preserved in `temp/simulation-expansion-2026-09-26/source-audit.json` in the development workspace.

The standalone physics helper passes seven analytic regression tests: equal-mass elastic energy sharing, capture recoil/excitation, lab four-momentum and mass shells, thresholds/invalid inputs, Doppler limits and inverse boost, thin/unity bias limits, and weighted slab reaction-plus-survival normalization. The equal-mass JSON example uses synthetic masses. No new reaction, bias operator, lifetime transport or geometry scan was implemented in the user's checkout as part of this skill expansion. Validate any such implementation against the guide before production.
