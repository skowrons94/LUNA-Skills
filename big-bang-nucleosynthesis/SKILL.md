---
name: big-bang-nucleosynthesis
description: Compute primordial abundances (Y_p, D/H, 3He/H, 7Li/H, 6Li/H) with the public BBN code AlterBBN — build it reproducibly from the unmodified tarball, replace any of its nuclear rates by a table (e.g. a measured LUNA rate with its uncertainty), run central values, baryon-density scans and a reproducible Monte Carlo over the rate uncertainties, infer Omega_b h^2 from an observed D/H, and check the numbers (patch identity, table round trip, solver convergence). Use whenever a task asks how a reaction rate changes the primordial abundances or the baryon density from BBN, for comparing a new rate with a BBN code's default, or for the starting composition of zero-metallicity (Population III) stars; these must be computed, not estimated from memory.
---
# Big Bang nucleosynthesis

A rate measured in the laboratory changes a primordial abundance only through a BBN calculation at a stated baryon density, neutron lifetime and number of neutrino species. Make that calculation from an unmodified, checksummed code with the rate swapped by a table, show that the swap changes nothing else, and use a solver setting whose numerical error is far below the effect.

## Route the task

- **The rate itself** (S factor, R-matrix, rate integration): `azure2`, `reaction-network` (`rates.py from-sfactor`). This skill starts from a rate table (T9, N_A⟨σv⟩, factor uncertainty).
- **Burning in stars** (including zero-metallicity stars that start from the BBN composition): `stellar-evolution`.
- Everything else here: build, run and check AlterBBN — [alterbbn.md](references/alterbbn.md) (reaction numbers, units, the patch, run modes, conversions, observational inputs to source).

## Non-negotiable boundaries

1. **The code is unmodified except for the documented patch.** Build from the downloaded tarball (record URL and sha256) with `scripts/build_alterbbn.sh`, which also builds an unpatched copy; the patched build without tables must reproduce the unpatched one exactly.
2. **Baseline and new rate use the same machinery.** Compare a measured rate with the code's own rate written as a table (`dump_rates.x`, or the code's tabulated points), not with the built-in function: interpolation and step functions then cancel. A round trip (built-in rates fed back as tables) must reproduce the built-in run (measured: 3e-6).
3. **Converged numbers only.** AlterBBN's `alter_eta` default (`failsafe = 1`) is 1.1 % low in D/H. Check the adopted setting against Cash-Karp with `ALTERBBN_PREC=1e-7` (measured: `failsafe 3` within 0.06 %, ~0.2 s per run).
4. **Tables are dense: build them as ratio × the code's own rate.** A published rate table (steps of a factor 2–5 in T9) interpolated log–log misses the curvature of a charged-particle rate: Mossa 2020's 17-point D(p,γ) table came out up to 15 % low at T9 = 0.2–0.3 and tripled the D/H effect (+1.7 % instead of +0.5 %). Interpolate the ratio new/default (smooth) onto the default's dense grid, or integrate the S factor on a fine grid; check one way against the other.
5. **Rates are bare and cover the BBN range.** BBN needs T9 ≈ 0.01–3 (tables to 10 are safer). A table that stops early must be joined to a stated shape; the patch counts calls outside each table (`ALTERBBN_RATES_VERBOSE=1`).
6. **Every input is sourced.** Omega_b h^2 (Planck), the η–Omega_b h^2 conversion, the observed D/H, Y_p, Li — quote them from the papers (with table/equation) and keep them in the results file, not in code comments only.
7. **Code systematics are stated.** BBN codes differ by more than a 1 % rate effect in D/H with the same D(p,γ) rate (PRIMAT vs PArthENoPE, mainly the d+d rates). Quote rate effects as ratios LUNA/default within one code; an absolute Omega_b h^2 carries the code's systematics.
8. **Monte Carlo is reproducible and its caps are stated.** AlterBBN's own `err=4` uses `rand()` in OpenMP threads seeded by the PID; use `bbn_driver.x mc ETA N SEED` (independent `erand48` state per sample; a sample whose solver fails — AlterBBN does not always flag it, all abundances come out ~0 — is rerun at failsafe 2 and tagged). AlterBBN caps a 1σ step at −20 % / +100 % (`LOWERR`, `UPPERR`): for rates with factor uncertainties above ~1.25 (NACRE ²H(α,γ)) the MC width reflects the caps, say so. Give tables both errors (fu = high/central, fl = central/low) so asymmetric bands survive.

## Quick start

```bash
bash scripts/build_alterbbn.sh alterbbn_v2.2.tgz build/           # patched + unpatched
build/alterbbn_v2.2/bbn_driver.x central 6.1245e-10 3              # one JSON line
build/alterbbn_v2.2/dump_rates.x 20 2001 > dpg_default.dat         # built-in rate as a table
echo "20 dpg_new.dat" > rates.list
ALTERBBN_RATES=rates.list ALTERBBN_RATES_VERBOSE=1 build/alterbbn_v2.2/bbn_driver.x central 6.1245e-10 3
ALTERBBN_RATES=rates.list build/alterbbn_v2.2/bbn_driver.x mc 6.1245e-10 1000 12345 3 > mc.jsonl
```

A worked project (LUNA D(p,γ), ²H(α,γ), ⁶Li(p,γ), ³He(α,γ), ³He(³He,2p); verification and Omega_b h^2 from D/H): `Astrophysics` repository, `cases/07_primordial-chain/bbn/`.
