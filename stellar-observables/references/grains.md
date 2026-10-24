# Presolar grains as tests of reaction rates

A presolar grain is dust that condensed in the ejecta of a single star. Its isotopes are measured one by one (SIMS, NanoSIMS) with errors per grain. A grain records the time-integrated composition of the wind or ejecta in which the dust formed, not a snapshot of the photosphere, and contamination can pull it toward solar values. Grain groups are classes in a database, not always the labels of the original authors. For SiC the database is the Presolar Grain Database (PGD; Stephan et al. 2024, ApJS 270, 27), which classifies grains probabilistically.

## What each group can constrain

| Group | Isotopic signature | Parent stars (as read in the papers) | What it tests | Anchor |
|---|---|---|---|---|
| SiC mainstream (MS) and Y | 12C/13C from ≥ 13.5 to 100 in the PGD (Stephan et al. 2024, Sect. 3.1), 10–100 in the classical scheme (Liu et al. 2021, MTNT3TTZ, introduction); Y above 100; s-process enriched | low-mass C-rich AGB stars; 14N-rich MS and Y grains linked to N-type carbon stars of 1.5–3 Msun with near-solar Z (Liu Sect. 3.2); MS and Y together are over 90 % of SiC (Liu Sect. 3.1.1) | first and third dredge-up, the 13C pocket, the C-star phase | MTNT3TTZ; Vescovi et al. 2020 (2LXMPCGS, introduction) |
| SiC AB | 12C/13C ≲ 10 (Liu introduction, Sect. 3.1.2); the PGD's AB class reaches 13.5, and 25 where N or Al rule out other types (Stephan et al. 2024, Sect. 3.5) | AB2: J and SC carbon stars; AB1: supernovae (Liu Sect. 3.1.2); born-again AGB stars and novae have also been proposed (not checked here) | CN burning below the equilibrium value; hot or ingestion burning | MTNT3TTZ |
| SiC Z | 12C/13C 14.7–96.5 (case-02 `obs/README.md`) | AGB stars of lower Z | AGB at low Z | PGD (project PROVENANCE) |
| SiC X, C, D; N | supernovae; nova candidates | | not AGB tests; not tested here | PGD |
| O-rich (oxide) grains | 17O, 18O, 26Al/27Al | AGB stars of ≲ 1.5–1.7 Msun with extra mixing (Palmerini et al. 2011, NRLFHW6Q, abstract); with the LUNA 25Mg(p,γ) rates, AGB extra mixing does not reach 26Al/27Al > 1e-2 (Straniero et al. 2013, AEGNXTUH, abstract) | 17O(p,α), 25Mg(p,γ), extra mixing | not tested here |

Liu et al. (end of Sect. 3.1.1) infer H burning at ≳ 1e8 K for the 15N-rich MS grains and for SC stars, but not for AB grains.

## Method

1. Compute the envelope (or ejecta) composition of the candidate parent star with both rates, at the mass and Z the grain group points to.
2. Weight by the mass lost while the star can make that kind of dust (for SiC, while C/O > 1), not by time.
3. Compare distributions, not single grains. A few extreme grains test the lower limit of the burning, not the bulk.
4. A grain below the transient minimum of a burning (`reaction-network`, with the rate uncertainty propagated) needs another site or process. Mixing or dilution cannot produce it, since a mixed ratio cannot fall below its lowest component.

## Example: case 02, 2026-10-24 (`cases/02_carbon-pg-12c13c/`; plan in its README, not run)

PGD-SiC, version 2026-05-19 (`data/external/pgd_sic_stephan2024/PROVENANCE.md`), has 20088 grains with 12C/13C, of which 11546 are unpublished. Mainstream: 16956 grains, median 55.3. AB: 1332 grains, median 6.4, 244 above 10 (`obs/obs_vs_predictions_stats.json`).

- AB grains below the CN transient minimum. 40 AB grains lie below 2.548, 37 of them by more than 2σ of the grain errors alone. 168 lie below 3.37, the lower edge of the LUNA equilibrium band 3.37–3.78 (68 %, with the systematics of the two LUNA rates taken as fully shared). The LUNA minimum 2.548 is for central rates, reached at 20 MK on a coarse 20/25 MK grid; the NACRE minimum is 2.951 at 25 MK. A finer grid (2.545–2.607) is recorded only in `docs/VALIDATION.md`. What we can say: at the central LUNA rates, no constant-temperature CN burn at 20–25 MK reaches these grains. The rate uncertainty on the minimum is not yet propagated. Next step: a one-zone scan over T, ρ and time, and hot or ingestion trajectories.
- Mainstream grains. These need a C-rich TP-AGB pair of 2–3 Msun; the case's 5 Msun model burns at the envelope base. We expect the rate effect to be small next to the efficiency of the first and third dredge-up (an expectation, not tested).
