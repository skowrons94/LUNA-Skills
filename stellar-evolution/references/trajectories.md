# From a stellar model to a network calculation

A stellar model gives the conditions; `reaction-network` gives cheap rate variations under those conditions. The handoff is the `thermo-trajectory` contract (`time_s,T_K,rho_cgs`) plus an initial composition.

## Centre of the star (core burning)

```bash
python3 SKILL_DIR/scripts/mesa.py trajectory LOGS/history.data --center --from-age AGE0 --to-age AGE1 --out traj.csv
python3 SKILL_DIR/scripts/mesa.py composition LOGS/profileK.data --mass 0.0 --out X0.json    # profile at AGE0
python3 REACTION_NETWORK/scripts/trajectory.py check traj.csv
```

`history.data` needs `log_center_T`, `log_center_Rho` and `star_age` (default columns). Backups and restarts repeat model numbers; `mesa.py` keeps the last occurrence. Increase history output (`history_interval = 1`) when the burning phase is short, and check the trajectory for temperature steps above 10 %.

**What the centre trajectory ignores.** A convective core mixes fresh fuel in and products out. The centre's composition evolves by burning *and* mixing over the convective mass, so a one-zone network along the central (T, ρ) burns too fast. Use it for radiative cores and for the rate *ranking*, and for convective cores compare with the model's own central abundances. The mismatch measures how much mixing matters.

## A mass shell (shell burning, envelopes, explosions)

There is no built-in per-shell history. Either save profiles densely (`profile_interval` small, `max_num_profile_models` large) and interpolate T and ρ at fixed mass coordinate (or fixed fraction of a moving shell) from successive profiles, or add the shell's values as extra history columns in `run_star_extras.f90` (`how_many_extra_history_columns`, `data_for_extra_history_columns`). The second is exact and cheap. Document which mass coordinate (Lagrangian or relative to a boundary) the trajectory follows.

## Composition

`mesa.py composition` returns mass fractions with pynucastro names (`h1` → `p`, `neut` → `n`). Isotopes absent from the MESA net are absent from the profile. The network then starts them at zero, which is wrong for trace seeds (e.g. ²⁵Mg if the MESA net has only ²⁴Mg). Fill them from the initial mixture of the model (same metallicity scaling and solar reference) and state it.

## Consistency

Post-processing is consistent only if the network rates match those that made the trajectory, or differ in reactions that do not feed back on the structure (trace isotopes, low energy generation). A rate that changes the energy generation needs a new stellar model. Compare the network's energy generation along the trajectory with the model's `eps_nuc` at the centre; a large mismatch means the networks differ.
