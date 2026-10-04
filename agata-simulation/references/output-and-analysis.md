# Output and analysis

## GammaEvents.NNNN (OUTPUT_MASK 111001000)
Header ends with a line `$`. Per event:
```
-100  <evnum>
 -101  beta ux uy uz          # emitter velocity (one per emitted particle)
 -102  x y z                  # emitter position
   -1  E(keV) ux uy uz idx    # emitted gamma (lab)
    1  Edep(keV) x y z 04     # interaction: crystal, energy, position (mm), segment code
```
- Crystal id < 1000 (0,1,2 for one triplet); ancillaries use offsets (SAURON 41000).
- Segment code: two digits, sector (0–5) and slice (0–5) → index `(code//10)*6 + code%10` (0–35).
- With packing 0 every Geant4 step is a line (large files: convert to npz and delete the text immediately).
- There is no separate core line: the core energy is the sum over segments.

## Offline packing and response (validated choices)
- PSA: one point per hit segment at the energy-weighted position; Gaussian smearing FWHM(e) = 2.7 + 6.2·sqrt(0.1 MeV/e) mm (Söderström et al., NIM A 638 (2011) 96); vary ×0.5 and ×2 as systematics.
- Energy: core FWHM = sqrt(1.2² + 0.0030 E) keV (2.3 keV at 1.33 MeV), segment sqrt(1.8² + 0.0045 E); thresholds 20 keV (segment), 10 keV (core).
- Doppler-correct sums with the direction of the most energetic point.

## Tracking
- OFT and MGT source are in `environment/agata/analysis/oft/built-in/forward2018.c` and `analysis/mgt/` (with Ge cross-section tables `ge_{comp,phot,pair}.dat`: E keV, μ 1/cm).
- Python OFT figure of merit (Compton-angle term with position-error propagation, attenuation factors, (·)^(1/(2N−1)), single-hit isolation 4 cm + range test). For a single cluster, compute the Ge path from the triplet front plane, not from a 4π shell.
- For known cascades, an energy-partition test (a subset of ≤4 points whose energy equals a known primary) separates summing-in from single high-energy γ better than generic tracking: 94 % / 19 % (sum / true) vs OFT 77 % / 9 % at 7.4 MeV.

## Statistics for low counts
Split the ROI into categories (multiplicity × tag) and fit μ_c = s·G_c + θ·U_c + B_c with θ free (data-driven summing); evaluate systematics by fitting pseudo-data from varied templates.
