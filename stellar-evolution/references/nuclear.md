# Nuclear physics in MESA

Checked against MESA r26.04.1 (`star/defaults/star_job.defaults`, `controls.defaults`, `rates/private/raw_rates.f90`). Recheck the defaults files when the MESA version changes.

## Networks and reaction names

- The network is chosen by `change_initial_net = .true.` / `new_net_name = '<file>.net'` in `&star_job`. Net files are in `$MESA_DIR/data/net_data/nets` and can `include` each other.
- `basic.net` uses compound reactions (`rc12_to_n14` = ¹²C(p,γ)¹³N(e⁺ν)¹³C(p,γ)¹⁴N), which is fast but has no individual intermediates. To change one step, use a net in which that step is explicit: `pp_and_cno_extras.net` (explicit pp chains, ¹³N, ¹⁵O, ¹⁷F), `cno_extras_o18_to_mg26.net`, `sagb_NeNa_MgAl.net` (Ne–Na and Mg–Al cycles), `mesa_49.net` and larger. A rate factor on a reaction the net does not contain does nothing. Check the reaction list printed at the start of the run (or `show_net_reactions_info = .true.`).
- Names: `r_<target>_<projectile+ejectile>_<product>`, e.g. `r_n14_pg_o15`, `r_c12_ag_o16`, `r_mg25_pg_al26`, `r_he4_he4_he4_to_c12`, `r1212`. The list is `$MESA_DIR/data/rates_data/reactions.list`. A new name needs a local copy of that file (`net_reaction_filename`).

## MESA's default rates are not all REACLIB

`rates/private/raw_rates.f90` hard-codes many charged-particle rates to old compilations instead of REACLIB. In r26.04.1, 16 reactions (45 forward and reverse network entries) go to NACRE (1999) fits: pp, d(p,γ), ³He+³He, ³He(α,γ), ⁷Be(p,γ), ⁷Li(p,α), ¹²C(p,γ), ¹³C(p,γ), ¹³N(p,γ), ¹⁴N(p,γ), ¹⁶O(p,γ), ¹⁸O(p,α), ¹⁹F(p,α), ²⁰Ne(p,γ), **¹²C(α,γ)** and ¹⁶O(α,γ). A further 17 entries use Caughlan–Fowler-era fits (`_fxt`). ¹⁵N(p,α) is REACLIB. Count them yourself in your version: `grep -o 'call do1\(_reverse\)\?(rate_[a-z0-9]*_nacre' raw_rates.f90 | sort -u`. Example: `ir_n14_pg_o15 → rate_n14pg_nacre` is 1.68× the LUNA-based REACLIB `im05` at solar-core temperature, which doubles the solar CNO neutrino fluxes (see [solar.md](solar.md)). Before using MESA for any of these reactions, look up the dispatch in `raw_rates.f90` (`case(ir_<reaction>)`), and supply the modern rate as a table (below) for every rate the conclusion depends on. In a paper, state which rates were replaced.

## Changing a rate

**Constant factor**, in `&star_job`:

```fortran
num_special_rate_factors = 1
reaction_for_special_factor(1) = 'r_n14_pg_o15'
special_rate_factor(1) = 1.10d0
rates_cache_dir = './rates_cache'
```

**Replace by a table** (e.g. from AZURE2 via `reaction-network`'s rate-table contract):

```bash
python3 SKILL_DIR/scripts/mesa.py rate-table rates/mg25pg.csv --out r_mg25_pg_al26_lu.dat --reaction r_mg25_pg_al26
```

and in `&star_job`: `filename_of_special_rate(1) = 'r_mg25_pg_al26_lu.dat'` with `special_rate_factor(1) = 1`. The table format is comment lines, then a line holding the number of points, then `T8 rate` pairs (N_A⟨σv⟩ in cm³ mol⁻¹ s⁻¹).

- MESA interpolates tables piecewise-monotonically in **linear** rate vs T8. `mesa.py rate-table` therefore resamples onto 2000 log-spaced points, interpolating the source in (ln T, ln rate), from T8 = 0.01 up to the table's end. Below the source table the rate is set to zero (`--below zero`, recorded in the file header). Choose `--below error` if the star burns there.
- For a tabulated forward rate MESA builds the reverse as table × REACLIB's detailed-balance factor (`eval_table_reverse`), so forward and reverse stay consistent.
- The older mechanism `rate_tables_dir` + `rate_list.txt` replaces rates for every reaction named in the list (see the `custom_rates` test case).

**Run-local rate cache.** Always set `rates_cache_dir = './rates_cache'` when a rate changes. The shared cache does not know the rate changed.

## Screening and weak rates

- `screening_mode = 'chugunov'` (default) in `&controls`. To compare with `reaction-network`, use the same prescription there (`chugunov_2007`). The rates given to MESA must be bare, exactly as for the network.
- Weak rates blend tabulated weak rates and REACLIB (`T9_weaklib_full_off/on`); `use_suzuki_weak_rates`, `use_special_weak_rates` for sd-shell captures. Above T9 ≈ 0.5 or at high density, state which weak-rate set was used.

## ²⁶Al ground state and isomer

MESA knows separate species `al26-1` (ground state) and `al26-2` (isomer) (`data/chem_data/isotopes.data`) and their thermal transition rates `r_al26-1_to_al26-2` / `r_al26-2_to_al26-1` (`reactions.list`, tables in `data/rates_data/rate_tables`). No shipped net contains them (r26.04.1): `sagb_NeNa_MgAl.net` has total `al26` and `r_mg25_pg_al26`. A ground/isomer study therefore needs a custom net (`add_isos(al26-1, al26-2)` plus the feeding and destruction reactions of each state). Before trusting it, confirm in the run's reaction list that ²⁵Mg(p,γ) feeds both states with the intended branchings (not checked in this skill). Without that, ²⁶Al from MESA is a total, like pynucastro's REACLIB (see `reaction-network/references/physics.md`).

`r1212` is a compound rate: ¹²C+¹²C → ²⁰Ne + α with the ²³Na + p channel folded in (its description in `reactions.list`). For carbon-burning branching studies use a net with the separate channels (`r_c12_c12_to_he4_ne20`, `r_c12_c12_to_h1_na23`; check their presence in the chosen net).

## What a rate change does in a star

A changed rate changes the structure (energy generation, convective boundaries, lifetimes), not only the yields. That is the difference from post-processing. Report the structural changes (core masses, lifetimes, central abundances at fixed phase) next to the abundance changes. Compare models at the same evolutionary phase (e.g. central H = 10⁻⁴, or core-He exhaustion), not at the same age.
