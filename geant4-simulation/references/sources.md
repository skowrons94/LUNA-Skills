# Sources

## Gun or GPS

- `G4ParticleGun` in `GeneratePrimaries`: one particle per call, energy, position and direction set in code for every event. Best when the source is computed (spectra, kinematics, event lists) and must be recorded per event.
- `G4GeneralParticleSource` (GPS): configured from macros (`/gps/particle`, `/gps/pos/type Point|Plane|Volume`, `/gps/ene/type Mono|Gauss|Exp|Arb|User|...`, `/gps/ang/type iso|beam1d|...`, `/gps/hist/...`). Good for standard shapes and calibration-source geometries. With `iso`, GPS emits along the negative of the sampled direction: restricted `mintheta`/`maxtheta` select a cone about −z. Histogram the generated directions once before trusting a restricted cone.
- Start the source inside a vacuum or air volume, or sample positions inside the source volume (extended sources), never exactly on a boundary.
- Store the generated energy (and direction when it matters) per event; the denominator of every efficiency is the number (or summed weight) of generated events.

## Energy spectra

- **Monoenergetic**: response functions and efficiency against energy; fold with a spectrum afterwards, and compare with a direct simulation of that spectrum once.
- **Watt fission spectrum** f(E) ∝ exp(−E/a) sinh(√(bE)), mean 3a/2 + a²b/4. Sample as E = w + a²b/4 + (2u − 1)√(a²bw) with w drawn from a Maxwellian of temperature a (w = −a [ln u₁ + ln u₂ cos²(πu₃/2)]). Parameter sets for spontaneous fission of ²⁵²Cf differ between evaluations and codes; ISO 8529-1 recommends a Maxwellian with T = 1.42 MeV (mean 2.13 MeV) for ²⁵²Cf. Check the mean of your parameters against the reference you cite, and treat the spectrum shape as a systematic.
- **Maxwellian** (thermal or fission approximation): flux spectrum E exp(−E/kT) is sampled as −kT ln(u₁u₂); kT = 25.3 meV at 293.6 K.
- **AmBe and other (α,n) sources**: use the tabulated ISO 8529-1 reference spectrum (mean about 4.2 MeV) or the supplier's spectrum, converted to a histogram file of bin edges and weights. Check whether the table gives fractions per bin or values per unit energy (multiply by the bin width) or per unit lethargy. AmBe also emits a 4.44 MeV gamma with part of the neutrons and 59.5 keV gammas from ²⁴¹Am; include them if the detector sees gammas.
- **Reaction neutrons from a beam on target**: compute the energy–angle distribution from kinematics and the cross section ([kinematics.md](kinematics.md)); feed either an angle-integrated spectrum (loses the energy–angle correlation) or an event list of (E, direction) (keeps it).
- Histogram sampling uniform within bins is adequate for fine bins; for steep spectra on coarse bins sample uniformly in log E within the bin, or refine the bins.

## Angular distributions

- Isotropic: cos θ uniform in [−1, 1] and φ uniform in [0, 2π). Sampling θ uniformly is a common error that crowds the poles.
- Weighted distributions, e.g. W(θ) = 1 + a₂P₂(cos θ) + a₄P₄(cos θ) about the beam axis:
  - **rejection**: sample isotropically and accept with probability W/W_max (W_max ≤ 1 + |a₂| + |a₄|); every event has weight 1;
  - **event weights**: sample isotropically, store cos θ, and apply W as a weight in the analysis; one run serves many W, at the cost of larger variance for strongly anisotropic W. Normalise so that the mean weight over the sphere is 1.
- An angular distribution given in the centre-of-mass frame is applied before the boost to the laboratory ([kinematics.md](kinematics.md)); applying CM coefficients to lab angles is wrong except for capture gammas at low recoil velocity, where the difference is a small aberration.

## External fields and normalisation

- An isotropic external flux on a convex detector: start points uniform on a sphere of radius R enclosing it, inward directions with a cosine-law distribution (cos α = √u relative to the inward normal). N generated particles correspond to a fluence N/(πR²).
- Convert per-source-particle results to rates with the emission rate (activity × yield, beam current × neutron yield per projectile) and live time; keep the emission-rate uncertainty separate from the simulation.
- Record the source definition in every output: spectrum and its parameters or file hash, position, angular distribution, weights.
