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
- Restart from a photo with changed settings: `run.py restart spec.json [--photo x8100] --set inlist_file:controls:key=value`. The overrides are checked against MESA's defaults, and each restart gets its own `re_*.log` and a manifest entry. Photos are written every `photo_interval` models; a restart repeats the steps since the last photo.
- `write_profile_when_terminate = .true.` with `filename_for_profile_when_terminate = 'final.profile'` (both in `&star_job`) guarantees a profile at the stopping point. `mesa.py set` and `run.py` refuse keys that are not in the namelist's defaults file.

- A model created with `create_pre_main_sequence_model = .true.` first takes `pre_ms_relax_num_steps` (default 300) steps at a fixed tiny timestep (the terminal shows `dt_limit max_dt`, lg_dt ≈ −5). With `pre_ms_relax_to_start_radiative_core` it then relaxes until a radiative core appears. `LOGS/` appears only afterwards. Several minutes of this is normal, not a stuck run.

## Making grids fast

In order of payoff:

1. **Do not oversubscribe.** MESA scales poorly beyond 2–4 threads per run, so a grid runs fastest with one thread per run and no more concurrent runs than fast cores. Apple-silicon machines mix performance and efficiency cores (an M1 has 4 + 4, the efficiency cores roughly 3× slower). Nine single-thread runs on an 8-core M1 ran at about half speed each. Check the load before launching (`uptime`, `ps`) and stop runaway system daemons (Spotlight indexing of the MESA tree: put an empty `.metadata_never_index` in it).
2. **Compute shared phases once.** Variants that differ only in a late-acting ingredient (thermohaline or other extra mixing above the RGB bump, AGB mass loss) share the evolution before it. Run one base model per rate set to a branch point (e.g. `he_core_mass_limit` after first dredge-up), save it, and start each variant from it. In the branch spec, `load_saved_model`, `load_model_filename` and the model copied in through `files`. Set `set_initial_age`, `set_initial_model_number` and `set_initial_cumulative_energy_error` to `.false.` (many test cases reset them). Keep one run that includes the ingredient from the start, to show the branch approximation is good enough.
3. **Inherited timestep limiters.** Test cases switch on limiters for their own purposes. `1M_thermohaline` sets `dX_div_X_limit(1) = 3d-2` for all metals above X = 3×10⁻⁴; on the upper RGB this throttles every step at the CN-burning shell (`dt_limit` column shows `c12`, `o16`), and the core grew 13× slower per model than with the limiter off. Look at the `dt_limit` column of a slow run before changing tolerances, and check any relaxation against a strict reference over the phase that matters.
4. **Resolution is a speed knob only after a check.** Test-case settings such as `varcontrol_target = 1d-4` with gold tolerances can be stricter than the question needs. Run one model at both settings and adopt the looser one only if the observable changes much less than the effect under study (validation rung 2). Record the check.
5. **Smallest adequate network.** Explicit isotopes only where the question needs them.
6. **Memory caps the grid as well as cores.** Measure one run once it is stepping (`ps -C star -o rss`, or `RssAnon` in `/proc/PID/status`), never assume a figure from another machine. Memory grows in steps during a run: MESA r26 loads FreeEOS tables (134 MB each, plus 454 MB HELM) the first time the star's composition reaches that table, and keeps them. On Linux x86_64 a 1 Msun run with `pp_and_cno_extras.net` went 1.7 → 2.5 → 3.9 GB within its first ~150 models, and a 5 Msun AGB run held 4.4 GB, so one early reading underestimates. Log RSS against model number for a few hundred models before sizing a grid. A 20-core, 15 GB machine therefore runs 3, not 18, at once, and there is no swap on most cloud images: an overcommitted grid is killed by the OOM killer, not slowed. Start runs through `scripts/memgate.sh GB -- command` inside `xargs -P CORES`. It starts a run only when GB is free and holds the next start for a few minutes while the new run grows.
7. **Warm the caches first.** A fresh MESA has empty EOS/opacity/rate caches under `$MESA_DIR/data/*/cache` (~6 GB once filled). The first run builds them, slowly. Several first runs build the same files at once, and a run killed mid-write leaves a truncated cache file (compare sizes within a table family; delete the odd one, MESA rebuilds it). Run one model alone first.
8. **Keep long jobs out of the agent's session.** On systemd machines with `DefaultOOMPolicy=stop` (check `systemctl show -p DefaultOOMPolicy`), one OOM kill stops the whole unit the process belongs to. Jobs started from a terminal or agent shell share the session's scope (`setsid` and `nohup` do not change the cgroup), so a single overgrown run takes down the session and every other run. Start drivers with `scripts/detach.sh NAME --env ENVFILE -- command` (own unit, `OOMPolicy=continue`, memory-capped `mesa.slice`) after `loginctl enable-linger $USER`. Check `/proc/self/cgroup` if in doubt. On a VM without swap, add compressed swap (zram, zstd) and a swap file: MESA's loaded EOS tables are mostly idle and compress, which is what macOS does by default. Log memory with `scripts/memlog.sh` (RSS, swapped share, zram ratio).
9. **Clusters for grids.** One single-thread run per core; the specs and `run.py` only need the environment-file path changed.

Never rename or move a run directory while MESA runs in it. MESA continues (it holds the directory open), but the driver loses track and cannot record the final check.

## Judge a run on its log and outputs

`python3 SKILL_DIR/scripts/mesa.py check-run RUN_DIR` reads `rn.log`:

- The termination code must be the physical stopping condition of the case (`max_age`, `xa_central_lower_limit`, `log_center_temp_upper_limit`, ...). `max_model_number`, `min_timestep_limit` or retries exhausted mean the run did not reach its goal.
- `log_rel_run_E_err` (cumulative relative energy error) must stay small (≲ 10⁻³ for structure; much smaller is typical with gold tolerances).
- Look at retries and backups. Many retries around a phase transition mean the result there is resolution-sensitive.

## Reproducibility

One run directory per configuration (`runs/<name>/`), created from a spec by `run.py`, which writes `manifest.json` (template, edits, versions, hashes, wall time, check result). Keep the spec in git and the run directory out of it. Copy the final `history.data`, `final.profile` and `manifest.json` into the project's results if they are evidence for a claim.
