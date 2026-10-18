# Physics-list choice

Start from a reference list (`G4PhysListFactory().GetReferencePhysList(name)`), add constructors for what it lacks, and record the name and additions in every output. Check what is active rather than assuming: `/process/list`, `/process/had/verbose 1` (models and energy ranges per particle at initialisation), `/run/particle/dumpCutValues`.

## Gamma and electromagnetic

- Reference lists use the standard EM option 0, adequate for MeV gammas in thick detectors (efficiency, shielding).
- For low-energy gammas and X-rays, thin layers, dead layers, fluorescence or precise electron transport use option 4 (`_EMZ` suffix, e.g. `QGSP_BIC_HP_EMZ`), or Livermore (`_LIV`) / Penelope (`_PEN`); option 3 (`_EMY`) is an alternative. These need `G4LEDATA`.
- Production cuts (`/run/setCut`, per region) control secondary production, not energy conservation; check that the observable is stable when the cut is halved.
- Radioactive sources defined as ions need `G4RadioactiveDecayPhysics` (not in every list); check that the decay actually happens (secondaries, time) before trusting a source spectrum from it.
- For high-resolution gamma spectroscopy in-beam (summing, Doppler, angular correlations) use `underground-gamma-simulation` or `agata-simulation`.

## Neutrons

- Below 20 MeV use a high-precision list: `QGSP_BIC_HP`, `FTFP_BERT_HP`, or `Shielding` (HP below 20 MeV). They read evaluated data from `G4NEUTRONHPDATA`. Compare two lists as a model systematic when the result depends on fast-neutron reactions.
- **Thermal scattering.** Register `G4ThermalNeutrons` on the modular list (`phys->RegisterPhysics(new G4ThermalNeutrons(verbose))`) and use the matching hydrogen element or material name ([geometry.md](geometry.md)). Below 4 eV it replaces free-gas elastic scattering on hydrogen by the S(α,β) tables of bound hydrogen in polyethylene or water.
- **Without thermal-scattering data the bias is large.** Free-gas hydrogen gives a wrong thermal spectrum, diffusion length and die-away time. In the template, a thermal point source in water gave a diffusion length of about 2.7 cm with thermal scattering (consistent with textbook values) and about 3.7 cm without, almost a factor two in ⟨r²⟩. In the template counter (3 × 10⁴ events per case) free-gas hydrogen raised the capture efficiency by about 20 % relative (some 12 standard deviations) and shortened the mean capture time by about 6 %. The size is geometry-dependent and not predictable by a rule: run both once, use only the thermal-scattering result.
- Verify registration in the log (verbose constructor): your element or material must appear among the registered thermal-scattering elements, and the neutron model list must show the thermal-scattering model below 4 eV. A misspelled element name fails silently.
- HP final states for capture gamma cascades are sampled without full correlations; use them for neutron counting and energy deposits, not for gamma multiplicity or angular correlations without a check. Options under `/process/had/particle_hp/` (photo-evaporation, final-state adjustment, missing isotopes) change this; list them with `help` in your version and record any you set.
- 3He(n,p)t, ¹⁰B(n,α)⁷Li and ⁶Li(n,t)α are in G4NDL; identify them in scoring by their products, not by process name (names differ between versions and lists: the 3He reaction is not "nCapture").
- Above 20 MeV the cascade models of the list take over; cosmic or high-energy sources need a list whose models cover the range (`FTFP_BERT_HP`, `Shielding`).

## Charged particles

- Protons and alphas slowing in targets: option 4 or option 3 EM, with step limits in thin layers (`G4StepLimiterPhysics` plus `G4UserLimits` on the volume) and production cuts small compared with the layer thickness. ICRU90 stopping for water, air and graphite: `/process/em/UseICRU90Data true`. Check simulated ranges against SRIM or PSTAR/ASTAR tables (`target-analysis`).
- Charged-particle-induced reactions ((α,n), (p,n), (p,γ)) at low energy are rare per projectile and their cross sections in general-purpose libraries (TENDL via `G4PARTICLEHPDATA` and `_AllHP` lists) are not reliable near astrophysical energies. Generate the reaction products from evaluated or measured cross sections and kinematics ([kinematics.md](kinematics.md)) and transport only the products, unless the study is about the library itself.
- Ions as primaries need `G4IonPhysics` (in all reference lists) and, for decays, radioactive-decay physics.

## Recording

Put in every output: list name, constructors added (thermal scattering on or off), EM option, cuts, any `/process/...` command used, Geant4 version and dataset versions.
