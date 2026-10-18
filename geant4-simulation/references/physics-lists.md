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
- **Thermal scattering.** Either register `G4ThermalNeutrons` on an `_HP` list (`phys->RegisterPhysics(new G4ThermalNeutrons(verbose))`), or use an `_HPT` list of Geant4 11 (`QGSP_BIC_HPT`, `FTFP_BERT_HPT`, `Shielding_HPT`, `ShieldingM_HPT`), which already contains it through `G4HadronElasticPhysicsHPT`; never both. In either case use the matching hydrogen element or material name ([geometry.md](geometry.md)). Below 4 eV (default), and only for the registered elements or materials, it replaces free-gas HP elastic scattering by the S(α,β) tables; every other element (C in PE, O in water, the 3He gas, steel) keeps free-gas HP elastic.
- `G4ThermalNeutrons` needs an HP list. On a non-HP list (`FTFP_BERT`, `QGSP_BIC`) the run completes without a warning, but low-energy neutron transport is not the evaluated-data one and a moderated-counter efficiency can be wrong by a large factor. The template refuses such lists.
- **Without thermal-scattering data the bias is large.** Free-gas hydrogen gives a wrong thermal spectrum, diffusion length and die-away time. In the template, a thermal point source in water gave a diffusion length of about 2.7 cm with thermal scattering (consistent with textbook values) and about 3.7 cm without, almost a factor two in ⟨r²⟩. In the template counter (3 × 10⁴ events per case) free-gas hydrogen raised the capture efficiency by about 20 % relative (some 12 standard deviations) and shortened the mean capture time by about 6 %. The size is geometry-dependent and not predictable by a rule: run both once, use only the thermal-scattering result.
- Verify registration in the log. At initialisation Geant4 prints "Neutron HP Thermal Scattering Data: Following material-element pairs and/or elements are registered." followed by one line per element (e.g. "Element TS_H_of_Polyethylene"), also with verbose level 0. Your moderator's element or material must be there, otherwise hydrogen is a free gas; a misspelled element name fails silently. `run_checked.py --require-log` can enforce it. `/process/had/verbose 1` additionally shows the thermal-scattering model and data below 4 eV in the neutron model list.
- Energy deposits from 3He(n,p)t, ¹⁰B(n,α)⁷Li and ⁶Li(n,t)α depend on how the HP models build the two-body final state and on `/process/had/particle_hp/do_not_adjust_final_state`, which has given non-conserving kinematics in some versions. Check the deposit spectrum ([scoring-and-output.md](scoring-and-output.md)) and record any `particle_hp` option you set.
- HP final states for capture gamma cascades are sampled without full correlations; use them for neutron counting and energy deposits, not for gamma multiplicity or angular correlations without a check. Options under `/process/had/particle_hp/` (photo-evaporation, final-state adjustment, missing isotopes) change this; list them with `help` in your version and record any you set.
- 3He(n,p)t, ¹⁰B(n,α)⁷Li and ⁶Li(n,t)α are in G4NDL; identify them in scoring by their products, not by process name (names differ between versions and lists: the 3He reaction is not "nCapture").
- Above 20 MeV the cascade models of the list take over; cosmic or high-energy sources need a list whose models cover the range (`FTFP_BERT_HP`, `Shielding`).

## Charged particles

- Protons and alphas slowing in targets: option 4 or option 3 EM, with step limits in thin layers (`G4StepLimiterPhysics` plus `G4UserLimits` on the volume) and production cuts small compared with the layer thickness. ICRU90 stopping for water, air and graphite: `/process/eLoss/UseICRU90 true` before `/run/initialize`. It applies only to the NIST materials `G4_WATER`, `G4_AIR` and `G4_GRAPHITE`, not to user-built materials (such as the template's `Water_TS`). Check simulated ranges against SRIM or PSTAR/ASTAR tables (`target-analysis`).
- Charged-particle-induced reactions ((α,n), (p,n), (p,γ)) at low energy are rare per projectile and their cross sections in general-purpose libraries (TENDL via `G4PARTICLEHPDATA` and `_AllHP` lists) are not reliable near astrophysical energies. Generate the reaction products from evaluated or measured cross sections and kinematics ([kinematics.md](kinematics.md)) and transport only the products, unless the study is about the library itself.
- Ions as primaries need `G4IonPhysics` (in all reference lists) and, for decays, radioactive-decay physics.

## Recording

Put in every output: list name, constructors added (thermal scattering on or off), EM option, cuts, any `/process/...` command used, Geant4 version and dataset versions.
