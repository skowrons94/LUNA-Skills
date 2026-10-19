# Pitfalls and checks

## Before calling a difference "library spread"
- **Shared evaluations.** Libraries adopt each other's files (e.g. in the fast range JEFF-3.3 coincides with ENDF/B-VIII.1 to 1e-4 for many light-element channels; ENDF/B-VIII.1 ¹⁷O(n,α) is numerically the TENDL-2019 file). Check whether values are bit-identical; report "n independent evaluations", not "n libraries".
- **Build substitutions.** OpenMC JEFF-3.3: C13 and O17 are TENDL-2019; C is natural `C0`. Subset/partial installs: missing nuclides silently fall back if your code searches several libraries — print which file was used.
- **Redundant sums.** MT4, MT103–107 and MT1 may be absent from processed files; sum the partials (MT51–91, 600–849) yourself, and compare partials with partials (an R-matrix fit with only α₀ must be compared with MT800, not MT107).
- **Temperature.** Compare at the same temperature; resonance-region window averages change with Doppler broadening. 0 K curves have no reference in HDF5 builds.

## Window quantities (definitions used in `xs.py`)
- Thermal value: σ(0.0253 eV), lab.
- Resonance integral: $I=\int_{0.5\,\text{eV}}^{E_2} \sigma\,dE/E$ (0.5 eV is the Cd cut-off convention; state $E_2$).
- MACS: $\frac{2}{\sqrt\pi}\int\sigma E e^{-E/kT}dE/(kT)^2$. For a 1/v cross section MACS(kT) = σ(kT); for a constant σ it equals $(2/\sqrt\pi)\sigma$. Written with the lab energy; for light targets convert to c.m. first ($E_\text{cm}=E\,A/(A+1)$) or state the convention.
- Fission-spectrum average: Watt spectrum, default U-235 thermal (a = 0.988 MeV, b = 2.249 MeV⁻¹); for threshold reactions quote the threshold too.
- Grid: the evaluation grid plus a dense logarithmic grid; sharp resonances need the evaluation points, not only a coarse grid.

## Resonance reconstruction checks
- **SAMMY** reads ENDF File 2 directly (`INPUT IS ENDF/B FILE`, with `MAT=` and the file). The MF3 *background* is not in File 2: add it before comparing with NJOY, otherwise capture between resonances can be off by tens of percent (²⁰⁸Pb: 0.63 without background).
- Reich–Moore (Pb206/207/208) and MLBW (Pb204, Bi209) agreed with NJOY to 1e-3 in the median; MLBW ²³Na showed 6–20% local differences between codes. A disagreement between two processing codes is a formalism-implementation question, not a library difference.
- **Ferdinand** converts MF2 LRF=7 (R-matrix limited) to AZURE2/GNDS and back. It fails on files without a resolved range ("NoneType … domainMin"): check `xs.py info` first.

## Charged particles and (α,n)
- Few evaluations exist; for many targets the only sources are EXFOR and R-matrix fits. Say "no evaluation available" rather than silently substituting.
- An AZURE2 `.extrap` file computed with an active `<targetInt>` block is a thick-target/folded quantity, not σ. Disable target integration to get thin-target σ.
- Thick-target yields need stopping powers of the actual matrix; see the `target-analysis` skill for SRIM/ASTAR tables.

## Units and frames
- ENDF: lab energy (eV), barns. R-matrix and S factors: usually c.m. Never mix without an explicit conversion.
- Detailed balance between a(b,c)d and d(c,b)a: σ_rev = σ_fwd · g_fwd/g_rev · (μ_fwd E_fwd)/(μ_rev E_rev) in c.m., with g = (2j₁+1)(2j₂+1) and E_rev = E_fwd + Q.
