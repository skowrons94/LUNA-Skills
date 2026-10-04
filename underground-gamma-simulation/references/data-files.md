# Selecting and changing nuclear data

Read this before changing reaction cross sections, gamma branching, level schemes, angular distributions or radioactive decay. Data edits are part of configuring SimLUNA: available library values may be absent, incomplete, deliberately biased or inappropriate for the specific measurement. Do not treat installed data as automatically correct, or alter them merely to make a spectrum look plausible.

## Identify the input that controls the requested change

| Intended change | Relevant input in the examined local version | Important distinction |
|---|---|---|
| Capture probability versus incident energy | `G4PARTICLEXSDATA/<projectile>/capZ` and applicable `capZ_A` | Z/A identify the target |
| Resonant-capture cross section | Same root, `rescapZ` and applicable isotope files | Verify `PartCapType` actually selects the resonant model |
| Custom inelastic cross section | Same root, `inelZ` and applicable isotope files | Particle HP may use a different database/model |
| Direct-capture population of final states and primary-gamma anisotropy | `G4RADIATIVECAPTURE/<projectile>/zZ.aA` | Z/A identify the compound nucleus |
| Excited-state energies, lifetimes, decay branches and transition information | `G4LEVELGAMMADATA/zZ.aA` | Changing level order can invalidate capture-population row alignment |
| Parent half-life and radioactive-decay branches | `G4RADIOACTIVEDATA/zZ.aA` | Coordinate daughter excitations with level data |
| Particle HP reaction channels and final states | `G4PARTICLEHPDATA` / projectile-specific settings actually used by the reader | Preserve the HP directory/file structure; these are not `capZ_A` tables |
| LEND reaction data | `G4LENDDATA` | Follow the selected LEND reader's format and library organization |

For example, 19F(p,gamma)20Ne uses target Z=9, A=19 for cross sections, but compound Z=10, A=20 for the custom capture-population and level files. A `cap9_19` filename is only useful if this source's isotope range and selection code load it; adding a file does not register an unsupported isotope. Read `Initialise`, `IsoCrossSection`, and process registration.

A cross-section edit controls interaction probability; it does not by itself define gamma-cascade branching. Conversely, modifying a population file does not supply a missing cross section. Target isotope fractions and density generally belong to material definitions, not to these nuclear-data files.

## Make a reproducible override

1. Establish the desired change and its evidence: evaluated nuclear data, a cited measurement, the user's explicit model, or a labeled sensitivity test. Record uncertainty, energy frame/range, units, normalization, and any bias factor. If these materially affect the result and are unknown, resolve them before claiming a physical calculation.
2. Trace the selected process to the precise path and file it loads. Record the original SHA-256 and inspect the existing format. Check element/isotope fallback and energy applicability; initialization may require files for other elements in the geometry too.
3. Make a project-local, complete dataset override or a versioned copy of the required dataset family. Preserve the original. If using a symlink overlay for a large library, replace each edited symlink with a regular private copy **before writing**; otherwise edits will modify the shared original. Avoid hard links for editable files too. A directory containing only one replacement file usually cannot replace an entire dataset root.
4. Edit the minimum set of coupled files, retain a diff, and record old/new hashes plus the scientific reason. Point only the relevant environment variables at the override in the run launcher. Record their resolved absolute paths in the manifest. Do not globally repoint another project's environment.
5. Validate structure and physics as below, then launch a **new SimLUNA process**. These models cache data; changing a file while the application remains alive may not change the loaded tables. Data-only changes normally need a restart, not recompilation; changes to reader logic, supported isotopes or model registration need a rebuild.
6. Demonstrate that the overridden data were read. Prefer reader diagnostics showing the resolved file and effective cross sections/populations, or temporary instrumentation in the isolated build. A nonempty output file alone does not prove the override was used.

## Cross-section format and unit checks

The local `ParticleCaptureXS`, `ParticleResonantCaptureXS` and `ParticleInelasticXS` use `G4PhysicsVector::Retrieve(stream, true)`. The inspected Geant4 reader expects:

```text
E_min E_max N
N
E_0 sigma_0
E_1 sigma_1
...
E_(N-1) sigma_(N-1)
```

This is a schematic, not a ready-to-run file. Require N >= 2, exactly N pairs, increasing finite energies, finite nonnegative cross sections, and header bounds consistent with the actual grid. Plain `operator>>` parsing does not accept arbitrary inline comments. Preserve adequate numeric precision and independently check interpolation around narrow resonances and thresholds. Coverage must include the energies sampled as the beam slows down, not just its entrance energy. Inspect below-grid and above-grid behavior rather than assuming extrapolation; the examined capture code returns zero above the vector's maximum energy.

**Units are crucial in this local reader.** It passes the projectile kinetic energy directly to `Value(ekin)` and returns the tabulated value without multiplying by `barn`. Geant4 internal units here are MeV and mm². Thus, for these specific raw tables:

- incident keV → stored energy: multiply by 1e-3;
- barns → stored cross section: multiply by 1e-22;
- millibarns → stored cross section: multiply by 1e-25.

Check the installed source before applying these conversions to another variant or dataset family. PhotonEvaporation, decay and HP formats have their own conventions. The local element fallback additionally scales cross section by A/aeff[Z]; check what the selected isotope actually receives.

The examined `proton/cap9` contains values such as `5.3E-6`. Under the reader above, that corresponds to 5.3e16 barns before isotope fallback scaling. This is not evidence for a physical fluorine capture cross section: it may encode extreme bias or a unit mistake. Do not silently correct the user's research data or assume a known bias factor. Establish its intent and normalization first. This observation is consistent with the earlier smoke test's nearly immediate interactions at the target surface.

## Capture populations and angular distributions

The examined `ParticleRadCapture` reads six whitespace-separated values per row: an integer, a population, and four Legendre coefficient ratios. It consumes rows in order through the highest accessible level, assigns energies from PhotonEvaporation by loop index, and does not use the read integer to look up a level. Reordering lines or merely changing their printed indices therefore does not remap populations correctly.

Verify a row exists for every accessed level, the row order agrees with the companion level file, all values are finite, populations are nonnegative, and the sum over accessible levels is positive. The code normalizes that accessible sum. A total across inaccessible levels cannot rescue a zero accessible sum. Check the correspondence again after adding, deleting or moving a level.

The four coefficients describe W(mu)=1+sum(a_l/a_0 P_l(mu)) for the selected primary transition in this model. Test the full mu range [-1,1]. The current rejection sampler assumes 0 <= W <= 2; a larger envelope requires changing the sampler, not silently truncating the distribution. Do not confuse these coefficients with the separate cascade gamma-correlation settings.

## Level, decay and evaluated-library edits

Read the reader/documentation for the exact dataset version before writing fields. PhotonEvaporation and RadioactiveDecay are structured nuclear-data formats, not arbitrary energy/branching tables. Preserve record counts, level/daughter references, allowed transition coding and required auxiliary information. Verify energies and lifetimes in the format's own units, branch normalization under its convention, accessible daughter states and gamma-energy differences including the model's recoil treatment. Keep population and level edits synchronized.

For HP/LEND, use the applicable library-generation/translation workflow or a validated existing replacement. Do not repurpose the simple capture-vector writer for evaluated final-state files. If the format or scientific inputs cannot be established, identify the exact missing information rather than generating plausible-looking values.

## Test the change and report its effect

- Compare original and modified data with otherwise identical source, geometry, physics list, seeds and event count. Record restart and selected dataset paths. Matching seeds help control the comparison, but changed interaction probabilities can change random-number consumption.
- First test parsing and effective values at representative energies, thresholds and resonances. For cascades, test primary populations, emitted energies, branching and angular distributions with suitable statistics.
- Compare generated primaries, reaction indicators, interaction-depth distributions, energy spectra and detector observables. In the examined local source, `EgammaDC`, `EgammaRes` and `fFusionEvent` are not implemented; do not use them as evidence of changed reaction rates. Add verified diagnostic output when needed.
- Separate model/data corrections from Monte Carlo biasing. For a bias change, check target attenuation and interaction depth, competition between channels, weights and denominator definitions; see [physics-and-analysis.md](physics-and-analysis.md).
- Deliver the edited private files, exact environment overrides, diff/hashes, source of the nuclear values, structural checks, before/after results and scientific limitations. Keep the baseline available for rollback.

Before using cross-section enhancement, read [bias-and-weights.md](bias-and-weights.md). The bias factor belongs to the sampling model and does not replace a physical cross-section/unit audit.
