# AlterBBN reference (v2.2)

Code: https://alterbbn.hepforge.org (tarball `downloads/?f=alterbbn_v2.2.tgz`, manual `manuals/alterbbn2.2.pdf`). Papers: Arbey 2012, CPC 183, 1822 (arXiv:1106.1363); Arbey, Auffinger, Hickerson, Jenssen 2020, CPC 248, 106982 (arXiv:1806.11095). Its Sec. 5.1 lists the default output at η = 6.10e-10 (Y_p 0.2473, D/H 2.463e-5, ³He/H 1.034e-5, ⁷Li/H 5.376e-10, ⁶Li/H 1.085e-14), reproduced with `failsafe 3`.

## Reaction numbers and default rates (src/bbnrate.c)

| # | Reaction | Default source in v2.2 |
|---|---|---|
| 12 | p(n,γ)d | Ando 2006 |
| 20 | d(p,γ)³He | Coc et al. 2015 table, coded as a step function (bins with edges midway between the tabulated T9) |
| 22 | ⁶Li(p,γ)⁷Be | NACRE 1999 |
| 23 | ⁶Li(p,α)³He | Serpico 2004 |
| 24 | ⁷Li(p,α)⁴He | Serpico 2004 |
| 25 | d(α,γ)⁶Li | NACRE 1999 |
| 26 | t(α,γ)⁷Li | Serpico 2004 |
| 27 | ³He(α,γ)⁷Be | Cyburt et al. 2008 |
| 28 | d(d,n)³He | Coc et al. 2015 |
| 29 | d(d,p)t | Coc et al. 2015 |
| 32 | ³He(³He,2p)⁴He | NACRE 1999 |

Grep `/\* .* -> .*\*/` in `bbnrate.c` for the full list (100 reactions in the default network). Units: forward rates N_A⟨σv⟩ in cm³ mol⁻¹ s⁻¹ (two-body); reverse rates from detailed balance inside the code. Uncertainties: `ferrhigh`/`ferrlow` relative; the patch sets them from a factor uncertainty fu as fu − 1 and 1/fu − 1.

## Output

`ratioH[6]` = Y_p (⁴He mass fraction), `ratioH[3]` D/H, `[5]` ³He/H, `[8]` ⁷Li/H **including ⁷Be decay**, `[7]` ⁶Li/H, `[9]` ⁷Be/H. Defaults: N_ν = 3 (with the code's neutrino decoupling treatment), τ_n = 880.2 s (PDG 2018), η = 6.10e-10 (attributed to PDG 2018 by Arbey et al. 2020) — set η from the current CMB value.

## The patch (scripts/patch/)

- `rate_override.c`, included at the top of `bbnrate.c` and called just before the code clips rates and applies uncertainties: `ALTERBBN_RATES=FILE` with lines `INDEX PATH`; table columns T9, rate, fu = high/central and optional fl = central/low; `#` comments; log–log interpolation; outside a table the code's rate is used and counted.
- `bbn_driver.c`: `central ETA [FAILSAFE]` and `mc ETA N SEED [FAILSAFE]`, JSON lines. The Monte Carlo uses AlterBBN's `err=4` sampling (every rate, including weak rates and the neutron lifetime: linear in the relative error, low side capped at −20 %, high side at +100 %) with reproducible normal deviates; failed samples are retried at failsafe 2 (mode `mc_retry_fs2`).
- `dump_rates.c`: `dump_rates.x INDEX [NPTS]` writes the built-in forward rate and fu = high/central on T9 = 1e-3–10.
- `ALTERBBN_TRACE=FILE`: one line per step of the stiff integrator (failsafe < 5): t (s), T9, molar abundances Y of all 26 nuclides (mass fraction = Y·A); results unchanged. For evolution plots and animations; mark events from the trace itself (e.g. n/p leaving equilibrium, X(⁴He) rising), not from textbook values.
- `ALTERBBN_PREC`: overrides the relative precision of the adaptive RK methods (failsafe 10–32).

## Solver settings (measured with v2.2, built-in rates, η = 6.10e-10)

D/H relative to Cash-Karp with `ALTERBBN_PREC=1e-7` (failsafe 32, 135 s per run):

| failsafe | D/H | note |
|---|---|---|
| 1 (alter_eta default) | −1.1 % | 0.04 s per run |
| 2 | −0.1 % | |
| 3 (stiff, tight; adopted) | −0.06 % (built-in rates), +0.01 % (rates as tables) | ~0.2 s per run |
| 32 (Cash-Karp, built-in 1e-5) | +0.4 % | 6 s |
| 32 with ALTERBBN_PREC=1e-6 | +0.04 % | 20 s |

The higher-order methods at their built-in precisions are not better than `failsafe 3`; check with `ALTERBBN_PREC` when the effect under study is below ~0.1 %. Rate ratios (new/default at the same setting) cancel most of the solver error.

## Conversions and inputs to source

- η₁₀ = 273.78 Ω_b h² (Cooke et al. 2018, after Steigman 2006, whose Eq. 12 gives 273.9 ± 0.3 + 1.95(Y_p − 0.25)); conventions differ at the 0.05–0.3 % level, state the one used.
- Planck 2018 Ω_b h² (paper VI, Table 2): 0.02236 ± 0.00015 (TT,TE,EE+lowE), 0.02237 ± 0.00015 (+lensing), 0.02242 ± 0.00014 (+BAO).
- Observations: D/H = (2.527 ± 0.030)e-5 (Cooke et al. 2018, Eq. 10); Y_p (Aver et al. 2021); ⁷Li/H = (1.6 ± 0.3)e-10 (Fields et al. 2020, Eq. 6; Sbordone et al. 2010 give A(Li) = 2.199 ± 0.086); ⁶Li has no confirmed detection.

## Known defects

- `bbn_constraints.c` line 80: correlated χ² uses `translate[ie]` instead of `translate[je]` — the "compatible with BBN constraints (including correlations)" flag is wrong; do not use it.
- `nucl_err` with `err=4` seeds `rand()` with the PID and calls it from OpenMP threads: not reproducible, not thread-safe.
- The d(p,γ) step function: interpolating its tabulated points instead changes D/H by 2e-4 (negligible, but use tables for both sets anyway).
