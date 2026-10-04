# Reaction kinematics and Doppler effects

## Define the vertex before defining a peak

Use consistent masses, energy frame and excitation conventions. Geant4 transport uses nuclear/particle masses; atomic mass tables require electron accounting before combination with bare nuclei. Record mass source and uncertainty. For a stationary target, compute the compound four-vector from the projectile at the reaction vertex, after its energy loss, plus the target four-vector. Do not use entrance energy for every depth.

For `a+A -> b+B`, use c=1, rest energies m in MeV, projectile lab kinetic energy T, and `s=(ma+mA)^2+2*mA*T`. In the CM frame, the two products have equal opposite momentum. Generate one direction using the specified differential cross section, construct both products, and boost them with the same CM velocity. A detector's lab angle is not the sampled CM angle. Differential cross sections need the appropriate transformation if their angular frame changes; transforming events avoids an accidental Jacobian omission.

For capture into a residual level with mass `mB=m_ground+Ex`, the primary gamma CM energy is `(s-mB²)/(2*sqrt(s))`. Its recoil partner must have this excited mass. For subsequent transitions use the current emitter and daughter masses and update recoil at every emission. Ground-state capture and a cascade through excited states do not share the same first photon energy.

The general four-vector/two-body conventions can be checked against the [PDG kinematics review](https://pdg.lbl.gov/2025/web/viewer.html?file=..%2Freviews%2Frpp2025-rev-kinematics.pdf). Use the bundled `physics_checks.py two-body CONFIG.json` as an independent reference. Required JSON keys are `projectile_mass_MeV,target_mass_MeV,beam_kinetic_MeV,product_mass_MeV,residual_mass_MeV,theta_cm_deg`; `phi_cm_deg` defaults to zero. Supply product mass zero for a gamma and include excitation in residual mass. The helper returns lab four-vectors and conservation residuals. It does not choose nuclear masses, channel probabilities or angular distributions.

## Source-specific findings to verify before precision work

In the inspected local `ParticleRadCapture::ApplyYourself`:

- The target begins at rest and the projectile's four-vector is added. Primary gamma directions are sampled in the CM calculation and `lv2.boost(bst)` already converts to lab. Confirm the hadronic framework's rotation convention for a beam not aligned with +z.
- The primary formula is `(M²-m_ground²)/(2*M)-Ex`. This differs from the exact `(M²-(m_ground+Ex)²)/(2*M)`. Compare the difference at your excitation and precision, then test any code correction with the residual on-shell condition and total four-momentum. A subtracted gamma four-vector alone does not guarantee that a subsequently constructed dynamic ion retains an inconsistent four-vector unchanged.
- The recoil is created as an excited ion. That does not by itself establish that the required lifetime, decay and stopping sequence is handled correctly; inspect registered processes and emitted secondaries.

In local `ParticleResRadCapture`, the active A>4 branch uses a 0.01 internal-energy level-matching test (10 keV under the inspected MeV convention). It creates an excited ion near a level and a geantino otherwise; the alternative direct PhotonEvaporation breakup block is commented out. Below-threshold correction code also changes the initial four-vector. Audit these branches before using this model for arbitrary resonances or claiming conservation. A geantino is a diagnostic particle, not a physical missing cascade. These are local findings, not statements about current upstream.

## Doppler shift, lifetime and resolution are separate effects

For a photon with energy E0 in the emitting nucleus rest frame and recoil speed beta at emission,

`E_lab = gamma*E0*(1+beta*cos(theta_rest))`

or, using the angle measured in the lab relative to the recoil velocity,

`E_lab = E0/[gamma*(1-beta*cos(theta_lab))]`.

Do not mix the two angle definitions. At small beta, the leading shift is E0*beta*cos(theta). Use the actual emission position and direction: a finite crystal subtends a range of angles, and recoil can deviate from the beam after preceding emissions/scattering.

```
python SKILL_DIR/scripts/physics_checks.py doppler --rest-energy-keV 1000 --beta 0.01 --lab-angle-deg 0
```

The illustrative forward shift is about +10.05 keV; backward emission is redshifted. The helper assumes a fixed emitter velocity, not a slowing target recoil.

For lifetime effects, sample proper decay time with the correct mean lifetime (half-life/ln 2 when the input is a half-life). Transport the excited recoil through the target/backing before emission, including stopping and straggling where relevant. Decay at the creation point with a delayed timestamp cannot reproduce slowing-dependent Doppler attenuation. Do not simulate recoil transport twice when the existing excited-ion decay process already does it. Level-data availability alone is insufficient; verify process assignment, lifetime treatment and step/time behavior.

Beam energy spread, target thermal motion, reaction-depth loss, recoil slowing, detector angular acceptance and detector energy resolution affect different stages. Detector resolution acts on deposited/reconstructed energy after transport; it is not a Doppler correction. Preserve raw deposit, emitted gamma truth and reconstructed energy separately. Do not add an empirical Doppler Gaussian on top of a complete event-level boost and recoil history unless it represents a specifically missing effect.

## Validation sequence and saved truth

1. Use fixed-energy two-body vertices in vacuum: verify total energy/momentum, product mass shells and thresholds at forward, transverse and backward CM angles.
2. Set recoil beta=0: rest and lab photon energies agree. At fixed beta test forward/backward extrema and invert the lab formula to recover E0.
3. For isotropic emission, sample uniform cos(theta), not uniform theta; validate the chosen anisotropy before applying detector acceptance.
4. Compare prompt, fully stopped and intermediate-lifetime cases with suitable controlled benchmarks. Refine recoil transport steps until centroid and width converge. Finite-angle acceptance should broaden a moving-source line even before energy smearing.
5. Compare angular spectra and centroids, not just an angle-integrated peak that can hide a wrong sign or frame. A good Gaussian fit alone does not validate kinematics.

Save reaction energy/depth, emitting parent and daughter identity/excitation, emission position/time, emitter momentum before decay, photon lab four-vector, transition/cascade/history IDs and any weight needed for scoring. Use aligned per-photon records. Name a gamma rest-energy branch only if its producer actually computes that quantity. Existing `EgammaDC`/`EgammaRes` declarations are not sufficient.
