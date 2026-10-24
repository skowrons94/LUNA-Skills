# Worked example: 12C(p,γ), 13C(p,γ) and 12C/13C in giants (case 02, 2026-10-24)

This is how the method of SKILL.md went for one rate pair. The files are in `cases/02_carbon-pg-12c13c/` of the Astrophysics project, and model values are from `mesa_rgb/results/rgb_summary.json` unless another file is named. LUNA means the new tables, NACRE the built-in rates of MESA r26.04.1. All ratios are number ratios. Values marked "partial" come from unfinished or unrefereed runs; re-read the file before quoting them.

## Local effect (one-zone)

At 25–80 MK and central rates, the CN-equilibrium 12C/13C is 3.53–3.61 with LUNA and 3.82–3.91 with NACRE. The 68 % bands are 3.37–3.78 and 3.05–4.89 (σ_ln 4.7 % for LUNA, with its shared systematics taken as fully common, and 22 % for NACRE). The transient minimum at central rates is 2.548 at 20 MK for LUNA and 2.951 at 25 MK for NACRE (`one_zone/results/exposure_ratio.json`, on a coarse 20/25 MK grid). A finer grid gives 2.545–2.607; that result is recorded only in `docs/VALIDATION.md`.

## Exposure, levers and model pairs at the same phase

| Phase (read point) | 1 Msun, Z = 0.02 | 0.8 Msun, Z = 5e-4 |
|---|---|---|
| Main sequence (model 500, X_c(H) = 0.67) | 13C-rich layer: X(13C) peaks at 6.5e-4 at m = 0.14 Msun | — |
| End of the main sequence (model 1000: X_c(H) = 0, He core 0.11 Msun, before the dredge-up) | X(13C) peaks at 6.6e-4 at m = 0.35 Msun, 16 times the surface value (`mesa_rgb/runs/rgb_base_luna/LOGS/profile1,2.data`, not versioned) | — |
| First dredge-up, 0.01 Msun of core growth before the bump | 30.637 NACRE → 28.691 LUNA (factor 1.068); at He core 0.17 Msun 30.67 → 28.73 (−6.3 %) | 36.82 → 35.38 (−3.9 %) |
| RGB tip (L_He = 100 Lsun), no extra mixing | `rgb_1M_luna_std` running (partial) | 36.82 / 35.38 (−3.9 %) |
| Tip, weak thermohaline mixing (MESA `Brown_Garaud_Stellmach_13`) | 29.56 / 27.68 (−6.4 %) | — |
| Tip, C_t = 150 (`thermohaline_coeff` 100) | — | 5.99 / 5.34 (−10.9 %) |
| Tip, C_t = 1000 (`thermohaline_coeff` 667) | 8.21 / 7.87 (factor 1.043); 7.87 recomputed by the animation referee, 8.21 not yet refereed | 4.04 / 3.69 (−8.7 %) |

C_t = 1.5 × `thermohaline_coeff`; the conversion is derived in `stellar-evolution/references/mixing.md` from MESA's `turb/private/thermohaline.f90` and C&L Eq. 3.

Literature values at the same phases: after the first dredge-up of 1 Msun, 28.26 (K&L Table 1, Z = 0.02) and 28.8 (C&L Table 2); at the C_t = 1000 tip, 8.1 for 1.0 Msun, 8.9 for 1.1 and 10.4 for 1.25 (C&L Table 2).

Mass against rate, within one code each. After the first dredge-up, going from 1.0 to 1.25–1.3 Msun lowers the ratio by a factor 1.12 (C&L, 28.8 → 25.74) or 1.17 (K&L, 28.26 → 24.07). The LUNA/NACRE factor is 1.068, so the mass effect is about twice the rate shift in log. At the C_t = 1000 tip the mass factor is 1.28 (C&L, 8.1 → 10.4), about six times the rate factor of 1.043 at the 1 Msun tip. The rate shift at the tip is 4–11 %. It does not change monotonically with the mixing efficiency, and it has not yet been tested for resolution over the thermohaline drop.

The 5 Msun, Z = 0.014 TP-AGB model (`mesa_agb/results/agb_summary_partial.json`; LUNA only, 6 pulses to model 19440, partial) has a convective-envelope ratio of 18.84 over models 1000–3000 and 18.8–19.2 over pulses 1–4, with the envelope base at 24.2–46.4 MK. Hot-bottom burning then sets in: the base heats from 53 to 65 MK and the envelope ratio falls from 19.08 (model 7000) to 10.21 (model 19000). The NACRE partner branched at photo 6000, 110 models before pulse 4 starts at model 6110 (base 46.4 MK, envelope 18.91; `mesa_agb/branch_nacre.sh`). It measures the rate effect from that point on only, and there is no pair result yet. The summary's `al26al27_before` values are total-al26 values, not a test of the branching.

## What the comparison could say

The clump medians of M67 (1.25 Msun) and Cr 261 (1.1 Msun), 16.5 and 12, lie above the 1 Msun C_t = 1000 tip (7.87), a model that matches neither mass. The 1.25 Msun pair (partial) will tell whether mass or mixing explains the gap ([observations.md](observations.md)). The rate shift is smaller than the per-star errors and the offsets between methods. Clusters of known mass therefore constrain the efficiency of the extra mixing, and the rates shift the efficiency inferred from them.

Checks done (`docs/VALIDATION.md`): the first-dredge-up value is stable under resolution (28.72 against 28.73); the branched run matches the full run at the branch point; the strict and relaxed time-step limiters differ by 0.7 %, and only over He core 0.2348–0.2353 Msun; the 0.8 Msun strict-limiter run tested nothing, because its limiter never acted.
