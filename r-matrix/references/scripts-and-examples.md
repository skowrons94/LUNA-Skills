# Ready-made scripts and examples

## Ready-made scripts (7Be evaluation directory)

In `IAEA/evaluations/7Be/AZURE2/claude/scripts/`, reusable as templates. They
anchor their paths one level up, so run them from the evaluation directory as
`python scripts/<name>.py`:

- `fetch_exfor_web.py` → `make_capture_data.py` → `update_capture_segments.py` —
  the EXFOR-to-`.azr` data pipeline for ³He(α,γ)⁷Be (see
  `docs/CAPTURE_DATA_REVISION.md`).
- `fit.py` — least-squares fit in rwa space with the analytic Jacobian;
  `--only-norms`, `--only-rmatrix`, `--start`, `--out`.
- `report_chi2.py` — per-dataset χ², χ²/N and fitted normalizations.
- `sfactor.py` — S(E), S(0) and the γ₁/γ₀ branching by extrapolation.
- `resonance_probe.py "5/2-@6.588"` — one level: Δχ² ranking of all levels,
  per-dataset degradation, full/off/only/background curves per channel,
  interference partners. `--list`, `--index N`, `--all-rank`.
- `resonance_probe_all.py` — the same sweep over every level, plus
  level×dataset and level×level matrices and heatmaps.
- `capture_decomp.py` — capture decomposition (per-level γ off/only, external
  capture) for both entrance channels.
- `gamma_candidates.py` / `second_e1_test.py` — free one more γ channel, refit,
  report Δχ² and the strength in W.u.
- `gamma_fit_physical.py` — refit γ widths with the fit variables in eV.
- `width_rank.py`, `audit_parameters.py`, `weisskopf.py`, `plabels.py`.

Their extrapolation grids predate the lab-vs-c.m. finding — check the `cm2lab`
handling before trusting absolute energies in older ones
(`capture_decomp.py`/`second_e1_test.py` are correct).

## Examples shipped with pyazr

In `pyazr/examples/`: `angular_distribution.py`, `print_scheme.py`,
`edit_scheme.py`, `deactivate_level.py`, `transform_widths.py`,
`dimensionless_widths.py`, `save_fit_to_azr.py`, `uncertainty_band.py`,
`fit_emcee.py`, `fit_zeus.py`.
