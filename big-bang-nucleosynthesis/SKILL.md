---
name: big-bang-nucleosynthesis
description: Compute primordial abundances (Y_p, D/H, 3He/H, 7Li/H, 6Li/H) with the public BBN code AlterBBN: reproducible build from the unmodified tarball, any nuclear rate replaced by a table (e.g. a measured LUNA rate with its uncertainty), central values, baryon-density scans, Monte Carlo, and Omega_b h^2 from an observed D/H. Use whenever a task asks how a reaction rate changes the primordial abundances or the baryon density from BBN, for comparing a new rate with a BBN code's default, or for the starting composition of zero-metallicity (Population III) stars; these must be computed, not estimated from memory.
---
# Big Bang nucleosynthesis

A rate measured in the laboratory changes a primordial abundance only through a BBN calculation at a stated baryon density, neutron lifetime and number of neutrino species. This skill makes that calculation with AlterBBN, built from the unmodified, checksummed code with a documented patch that swaps any rate for a table. You need the rate as a table (T9, N_A⟨σv⟩, factor uncertainty), the baryon density and the observed abundances to compare with, each from a cited source. You get Y_p, D/H, ³He/H, ⁷Li/H and ⁶Li/H for the central rates, for baryon-density scans and for a reproducible Monte Carlo over the rate uncertainties, and Omega_b h^2 inferred from an observed D/H. Three checks make these numbers trustworthy: the patch identity, which shows that the swap changes nothing else; the table round trip; and solver convergence, with a setting whose numerical error is far below the effect.

## Where this fits

- Comes from: a rate table (T9, N_A⟨σv⟩, factor uncertainty) made by `azure2` or by `reaction-network` (`rates.py from-sfactor`); the observational inputs from the papers listed in [alterbbn.md](references/alterbbn.md).
- Goes to: `stellar-evolution`, for zero-metallicity (Population III) stars that start from the BBN composition.
- Checked by: the patch identity, the round trip and the solver-convergence check of rules 1–3; `physics-referee` before a number is quoted.

The rate itself, from an S factor, an R-matrix fit or a rate integration, belongs to `azure2` and `reaction-network`. Burning in stars, including zero-metallicity stars, belongs to `stellar-evolution`. Building, running and checking AlterBBN is documented in [alterbbn.md](references/alterbbn.md): reaction numbers, units, the patch, run modes, conversions and the observational inputs to source.

## Rules and their reasons

1. The code is unmodified except for the documented patch. Build it from the downloaded tarball, recording the URL and sha256, with `scripts/build_alterbbn.sh`, which also builds an unpatched copy. The patched build without tables must reproduce the unpatched one exactly, which shows that the patch alone changes nothing.
2. Baseline and new rate use the same machinery. A measured rate is compared with the code's own rate written as a table (`dump_rates.x`, or the code's tabulated points), not with the built-in function, so that interpolation and step functions cancel in the ratio. A round trip, in which the built-in rates are fed back as tables, must reproduce the built-in run (measured: 3e-6).
3. Only converged numbers are quoted. AlterBBN's `alter_eta` default (`failsafe = 1`) is 1.1 % low in D/H. The adopted setting is therefore checked against Cash-Karp with `ALTERBBN_PREC=1e-7` (measured: `failsafe 3` within 0.06 %, ~0.2 s per run).
4. Tables are dense, and are built as ratio × the code's own rate. A published rate table, with steps of a factor 2–5 in T9, interpolated log–log misses the curvature of a charged-particle rate. Mossa 2020's 17-point D(p,γ) table came out up to 15 % low at T9 = 0.2–0.3 and tripled the D/H effect (+1.7 % instead of +0.5 %). Interpolate the ratio new/default, which is smooth, onto the default's dense grid, or integrate the S factor on a fine grid, and check one way against the other.
5. Rates are bare and cover the BBN range. BBN needs T9 ≈ 0.01–3, and tables to 10 are safer. A table that stops early must be joined to a stated shape. The patch counts the calls outside each table (`ALTERBBN_RATES_VERBOSE=1`), so a gap in coverage shows in the log.
6. Every input is sourced. Omega_b h^2 (Planck), the η–Omega_b h^2 conversion, the observed D/H, Y_p and Li are quoted from the papers, with table or equation, and kept in the results file, not in code comments only.
7. Code systematics are stated. BBN codes differ by more than a 1 % rate effect in D/H with the same D(p,γ) rate (PRIMAT vs PArthENoPE, mainly through the d+d rates). Rate effects are therefore quoted as ratios LUNA/default within one code, and an absolute Omega_b h^2 carries the code's systematics.
8. The Monte Carlo is reproducible and its caps are stated. AlterBBN's own `err=4` uses `rand()` in OpenMP threads seeded by the PID, so it is neither reproducible nor thread-safe. Use `bbn_driver.x mc ETA N SEED` instead, which keeps an independent `erand48` state per sample. A sample whose solver fails is rerun at failsafe 2 and tagged; AlterBBN does not always flag such a sample, whose abundances all come out ~0. AlterBBN caps a 1σ step at −20 % / +100 % (`LOWERR`, `UPPERR`), so for rates with factor uncertainties above ~1.25 (NACRE ²H(α,γ)) the MC width reflects the caps, and the result says so. Tables get both errors (fu = high/central, fl = central/low), so that asymmetric bands survive.

## Scripts

```bash
bash scripts/build_alterbbn.sh alterbbn_v2.2.tgz build/           # patched + unpatched
build/alterbbn_v2.2/bbn_driver.x central 6.1245e-10 3              # one JSON line
build/alterbbn_v2.2/dump_rates.x 20 2001 > dpg_default.dat         # built-in rate as a table
echo "20 dpg_new.dat" > rates.list
ALTERBBN_RATES=rates.list ALTERBBN_RATES_VERBOSE=1 build/alterbbn_v2.2/bbn_driver.x central 6.1245e-10 3
ALTERBBN_RATES=rates.list build/alterbbn_v2.2/bbn_driver.x mc 6.1245e-10 1000 12345 3 > mc.jsonl
```

A worked project, with LUNA D(p,γ), ²H(α,γ), ⁶Li(p,γ), ³He(α,γ) and ³He(³He,2p), the verification and Omega_b h^2 from D/H, is in the `Astrophysics` repository, `cases/07_primordial-chain/bbn/`.

## What to deliver

- The build record: tarball URL and sha256, and the patched-against-unpatched identity.
- The round-trip check and the solver setting with its convergence check.
- Abundances as ratios new/default within one code, with the baryon density, τ_n and N_ν used.
- For a Monte Carlo, N, the seed, the retried samples and whether the caps bind.
- Every observational input with its paper, table or equation, in the results file.
