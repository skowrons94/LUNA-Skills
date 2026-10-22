# Running MESA

## Start from a test-suite case

Never edit `$MESA_DIR`. Copy a case (the run driver does this) and change the copy. Test-suite cases are maintained, run with every release, and document their physics choices, so they are better starting points than an empty `star/work`.

| Question | Template in `$MESA_DIR/star/test_suite` | Notes |
|---|---|---|
| Solar model, neutrino fluxes, S-factor sensitivity | `simplex_solar_calibration` | single run at calibrated values with `just_do_first_values = .true.`; GS98 opacities; diffusion on |
| Low-mass evolution to the WD, RGB mixing, ¹²C/¹³C | `1M_pre_ms_to_wd`, `1M_thermohaline` | thermohaline mixing case for extra mixing on the RGB |
| AGB, thermal pulses, hot-bottom burning | `7M_prems_to_AGB` | long run; network choice decides Na/Mg/Al output |
| ¹³C pocket, s-process neutron source | `c13_pocket` | pocket set up by a parametrised mixing profile |
| Massive stars to core collapse, C/Ne/O burning | `12M_pre_ms_to_core_collapse`, `20M_pre_ms_to_core_collapse` | hours; `approx21` by default, larger nets for yields |
| Carbon ignition, flames | `carbon_kh`, `cburn_inward`, `wd_c_core_ignition` | ¹²C+¹²C sensitivity |
| Pair-instability, black-hole mass gap | `pisn`, `ppisn` | ¹²C(α,γ) studies (Farmer et al. 2020, ApJL 902, L36) |
| Custom rates mechanism | `custom_rates` | rate tables via `rate_list.txt` |
| Novae, accreting WDs | `wd_acc_small_dm`, `ns_h` (accreting NS) | burning on accretion; check the net |

Run times on an 8-core laptop range from minutes (`custom_rates` final part: 15 min) to hours (solar: ~2 h, massive stars to collapse: several hours) to a day or more (AGB with pulses). Pilot first: run with `max_model_number` small and time a few hundred steps.

## Mechanics

- A case has `inlist` (pointing to `inlist_*_header` files), `inlist_project`-style files with `&star_job`, `&eos`, `&kap`, `&controls`, `&pgstar`, `src/run_star_extras.f90`, `mk`, `rn` (runs the parts in order), `re` (restart from `photos/`).
- `MESA_SKIP_OPTIONAL=t` makes multi-part cases start from the saved models they ship (e.g. a pre-ZAMS model). Use it for pilots and reruns with changed rates *after* the shipped model's phase. If the rate acts earlier (pre-MS ⁷Li or D burning), run all parts.
- Edit inlists with `mesa.py set FILE NAMELIST key=value` (or `run.py` from a spec), not with `sed`. Repeated keys and inline comments are common, and a silently unmatched edit is the usual failure.
- Threads: `OMP_NUM_THREADS` (2–4 is efficient for 1D models; several runs in parallel beat one run with many threads). Always `nice` long runs on a shared machine.
- Output: `LOGS/history.data` (one row per `history_interval` steps), `LOGS/profileN.data` (every `profile_interval` steps, indexed in `LOGS/profiles.index`), `photos/` for restarts. Add columns in `history_columns.list` and `profile_columns.list`. `add_screened_rates` and `add_raw_rates` add per-cell rates for every reaction in the net.
- `write_profile_when_terminate = .true.` with `filename_for_profile_when_terminate = 'final.profile'` guarantees a profile at the stopping point.

## Judge a run on its log and outputs

`python3 SKILL_DIR/scripts/mesa.py check-run RUN_DIR` reads `rn.log`:

- The termination code must be the physical stopping condition of the case (`max_age`, `xa_central_lower_limit`, `log_center_temp_upper_limit`, ...). `max_model_number`, `min_timestep_limit` or retries exhausted mean the run did not reach its goal.
- `log_rel_run_E_err` (cumulative relative energy error) must stay small (≲ 10⁻³ for structure; much smaller is typical with gold tolerances).
- Look at retries and backups. Many retries around a phase transition mean the result there is resolution-sensitive.

## Reproducibility

One run directory per configuration (`runs/<name>/`), created from a spec by `run.py`, which writes `manifest.json` (template, edits, versions, hashes, wall time, check result). Keep the spec in git and the run directory out of it. Copy the final `history.data`, `final.profile` and `manifest.json` into the project's results if they are evidence for a claim.
