# Comparing models with observed stars

These rules hold for any surface ratio or abundance, not only 12C/13C. They come from the referee rounds of the Astrophysics project (`docs/VALIDATION.md`, 2026-10-24). The case-02 data and numbers at the end are the example.

## Matching rules

1. One point per star. A star measured in several papers or lines is still one star: take the median of its independent values, and let N count stars. Drop values that one paper copied from another. Normalise star names before cross-matching.
2. Stage before value. Use the stage the paper gives (CMD position, asteroseismology), never a stage inferred from the abundance itself. A star in a later, quieter phase is compared with the model value at the end of the phase that set it: clump stars with the RGB tip, post-AGB objects with the end of the pulses. Thermohaline mixing can continue in the clump if 3He remains (C&L Sect. 1, citing Cantiello & Langer), so the tip value is a starting point, not a bound.
3. RGB stars per cluster. Compare below or above the bump as far as the paper's CMD position allows. The spectroscopic log g of a single star (±0.2 dex in Szigeti et al. 2018, ±0.3 dex in Drazdauskas et al. 2016) does not place it on a track.
4. Mass and [Fe/H] matched. Run the model at the mass and metallicity of the cluster. Mass usually moves a dredge-up value more than a rate does (levers in [burning-and-mixing.md](burning-and-mixing.md)). A giant's initial mass is slightly above the turn-off mass, and mass loss on the RGB lowers the clump mass. Convert the model's Z and mixture to [Fe/H] and state the offset. Field stars without masses test trends only.
5. Population. In globular clusters the second-population stars (O-poor, Na-rich) were born from processed matter. Scaled-solar models give orientation there, not a test.
6. Name the mixing: prescription and coefficient. "No extra mixing" means coefficient 0.
7. Separate bars by kind. Show model systematics (rate uncertainty, mass, [Fe/H], code spread) apart from observational errors (per star or typical). An observed range is not an error bar.
8. Keep the message within what the test can show. Say which lever the sample constrains; often it is the mixing efficiency, not the rate.

## Surface gravity and luminosity of a model

log g = 4.438 + log(M/Msun) − 2 log(R/Rsun), in cgs with the current mass. For a star of assumed mass, log(L/Lsun) = log(M/Msun) + 4 log(Teff/5772 K) − (log g − 4.438). The solar values 4.438 and 5772 K are the ones adopted in the project's `data/external/shetrone1996_m13/PROVENANCE.md` and in the case-02 dredge-up animation (`lecture/animations/dredgeup_scenes.py`).

## Where an observable is measured, and typical systematics

| Measured in | Proxy for | Systematics seen in the project's sources |
|---|---|---|
| Photosphere (atomic and molecular lines: CN, CO, C2) | current surface | per-star errors of different kinds (atmospheric parameters only, one typical value for all stars, or line-to-line σ); method offsets up to a factor ~2 between studies of the same stars |
| Circumstellar envelope (mm CO lines) | envelope averaged over the mass loss | photodissociation and fractionation; scatter against photospheric values rms 0.49 dex (factor ~3), up to ~8 for one star (project statistics, below) |
| Presolar grains | time-integrated ejecta that formed dust | contamination toward solar; database group classes ([grains.md](grains.md)) |
| Neutrinos, primordial abundances | the burning region itself | see `stellar-evolution/references/solar.md` and `big-bang-nucleosynthesis` |

Do not merge sources without a cross-calibration. When papers disagree on a star's class, take the majority over its rows.

## Example: case 02, 2026-10-24 (12C/13C; `cases/02_carbon-pg-12c13c/obs/`)

- Open clusters (`giant_12c13c.csv`, parsed from the papers' tables): M67 (Tautvaišienė et al. 2000; 9 stars, 1.25 Msun, [Fe/H] −0.03); Cr 261 (Mikolaitis et al. 2012, ELPLU579, and Drazdauskas et al. 2016; 1.1 Msun, −0.03 or +0.13; the two papers' stars are not cross-matched); NGC 6253 (ELPLU579; 1.4 Msun, +0.43 to +0.47 in Table 1, +0.36 to +0.46 in the literature); Mel 66 (Drazdauskas; 1.2 Msun, −0.33); NGC 6791 (Szigeti et al. 2018, PHB7U488; +0.39; no turn-off mass quoted, models at 1.10–1.15 Msun; errors +1–2 / −1–4 from atmospheric parameters only).
- M67 (1.25 Msun) and Cr 261 (1.1 Msun) are the clusters near solar [Fe/H]. The 1 Msun model (Z = 0.02, GS98, X = 0.70, [Fe/H] ≈ +0.10) matches neither, and the 1.25 Msun runs are for M67. Clump medians are 16.5 for M67 (6 stars) and 12 for Cr 261 (6 rows from two papers, not cross-matched). Both lie above the 1 Msun C_t = 1000 tip (7.87, LUNA). The 1.25 Msun pair (partial on 2026-10-24; re-read `mesa_rgb/results/rgb_summary.json`) will tell whether mass or mixing explains the gap.
- M13 (Shetrone 1996, AJ 112, 2639; 4ZCTJ8LT, Table 2; ±1 per star, Sect. 3.4): six C-depleted giants near the RGB tip. Four of them (I-48, II-67, IV-25, L-835) are O-poor and Na-rich, that is second population; L598 and L-629 have field-like O and Na.
- AGB stars (`agb_12c13c.csv`, 13 sources). Schöier & Olofsson 2000 find 12CO/13CO = (1.0 ± 0.2) times the photospheric ratio of Lambert et al. 1986 (their Eq. 4). Our own statistics for the stars in common with Lambert 1986 (computed in `obs/README.md`, not taken from the papers): Ramstedt & Olofsson 2014 are lower by a median 0.24 dex (rms 0.49, factor ~3), and by up to a factor ~8 for UX Dra. The two photospheric studies tabulated by Schöier & Olofsson 2000 (Table 1: Lambert 1986 against Ohnaka & Tsuji) differ by a factor 1.75–1.9 for J stars. We found no confirmed hot-bottom-burning star with a photospheric 12C/13C.
- The referee findings behind rules 2–7: clump stars had been drawn on the RGB track; a 1 Msun model stood in for clusters of 1.1–1.25 Msun; a weak-mixing branch was labelled "no extra mixing"; and the bars mixed model shifts with observed ranges.
