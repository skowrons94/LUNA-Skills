# Decomposition and evaluation recipes

## Decomposing a cross section

Everything below is done at the **fitted point, without refitting**, so each
number is that component's raw contribution.

```python
m.extrap_mode()
ex   = m.calculate_excitation_energy(best)     # common Ex axis
full = m.calculate_rwa(best)
off  = m.calculate_rwa(m.without_level(best, jpi="5/2-", energy=6.588))
only = m.calculate_rwa(m.only_level(best,    jpi="5/2-", energy=6.588))
bg   = m.calculate_rwa(zero_all_widths(best))  # non-resonant / hard-sphere / external
interference = (full - off) - (only - bg)
```

- `full − off` = everything the level does (resonant + its interference).
- `only − bg` = the bare resonance on the non-resonant background.
- The difference is pure interference. It is **block-diagonal in J^π** — only
  same-J^π levels interfere; that is a correctness check on any decomposition.
- Pairwise, level T against level L:
  `cross = only{T,L} − only{T} − only{L} + bg = 2 Re(A_T A_L*)`. Integrate
  `|cross|` over Ex to rank which partners a level interferes with.

**Capture-specific.** Zeroing only the **γ-channel** widths
(`p.radiation_type in ("E","M")`) leaves every particle channel — and therefore
the whole scattering solution — untouched, so it decomposes the capture
amplitude cleanly. Zero *all* γ widths at once and what remains is the
**external (direct) capture**.

**S-factor.** `calculate_sfactor_rwa` = cross section × an energy-only
conversion factor, so linear combinations of cross sections may be converted
after the fact: `conv = sfactor_full / xs_full` (guard the zeros) and multiply
each curve by it. Units: MeV b — ×10³ for keV b, ×10⁶ for eV b.

## Evaluation recipes

**Is a level needed?** Frozen Δχ² ranking — recompute χ² with each level in turn
switched off (`without_level`) at fixed parameters. Then, for the candidates,
refit with the level removed (`AzrModel.remove_level` / `deactivate_level` +
`least_squares`) — the frozen Δχ² is an upper bound on the level's importance,
the refit Δχ² is the honest one. Report both, plus which experiments' χ² move
(per-dataset χ² partition in [pyazr.md](pyazr.md)): a level justified by one dataset is a different
claim from one justified by all of them.

**Changing the channel radius.** `m.set_channel_radius(pair, r)` on a live
instance, or `AzrModel.set_channel_radius(pair, r)` + `write()` to persist one.
The radius is the matching surface, so AZURE2 rebuilds the compound nucleus and
data, redoes penetrabilities / shift functions / boundary conditions / Wigner
limits, and recomputes **every external-capture integral** (the API clears
`USE_PREVIOUS_INTEGRALS` for the rebuild, so `output/intEC*` is not reused).
A reduced width means something different at a different radius — **the model is
no longer fitted, so refit before reading anything off it.** For a scan, give
each radius its own directory (own `output/`, `data` symlinked) and walk the
ladder outward, warm-starting each radius from its converged neighbour rather
than from the original fit; starting them all from one point biases the ends.

**Is a new level/channel warranted?** Add it (`add_level`, or free one more
channel of an existing level), refit the subset it can affect, and weigh Δχ²
against the parameters spent and against physical bounds: θ² ≤ 1 for particle
channels, a few W.u. for γ channels. Sweep candidates from a shell loop — one
session per process.

**Dimensionless widths.** `m.dimensionless_widths(x)` (pyazr ≥ 2.4) does the
whole job — θ² for every particle channel, W.u. for every γ channel, at any
parameter vector:

```python
t = m.dimensionless_widths(best)          # -> WidthTable of ChannelWidth rows
print(t.photons.nonzero.table())          # .particles / .photons / .free / .nonzero
[c for c in t.particles if c.theta2 and c.theta2 > 1]
```

Each row carries `theta2` (= Γ/Γ_W), `theta2_formal` (= γ²/γ²_W),
`wigner_width` (Γ_W, eV), `wigner_gamma2` (γ²_W, MeV), and for photons
`e_gamma`, `weisskopf`, `wu`. Closed (sub-threshold) channels have `is_open =
False`, no Γ_W — AZURE2 reports an ANC there, not a width. `m.wigner_widths(x)`
returns just `{free_index: Γ_W}`; `weisskopf_width(rad, L, E_γ, A)` and
`m.mass_number` are exposed separately. Example:
`pyazr/examples/dimensionless_widths.py <azr> [--params output/param.sav]`.

The reason there are two answers: AZURE2 exposes the Wigner limit in two
non-interchangeable forms.

1. **GUI / width form**, in eV next to each channel: `Γ_W = 2 P_l(E_r) γ²_W`,
   energy-dependent. **θ² = Γ/Γ_W** — prefer this; it is checkable one channel
   at a time in the GUI.
2. **API form**, `Parameter.wigner_limit`: `γ²_W = ħ²/(μ a²)` in **MeV**,
   already squared and energy-independent. Then θ² = γ²_formal/γ²_W with the
   formal reduced width (`g_int` in `parameters.out`, squared).

Never divide by `wigner_limit` twice. The two differ by the level-shift factor
`1/(1 + Σ_c γ_c² dS_c/dE)`, negligible for narrow levels but a factor 70+ for
the 30 MeV background poles. AZURE2 reports **observed** partial widths,
`Γ_c = 2 P_c γ_c²/(1 + Σ γ² dS/dE)`. Some references use the Teichmann–Wigner
sum-rule unit `3ħ²/(2μa²)`, 1.5× larger (`teichmann_wigner()`).

`Γ_W` needs `P_l(E_r)`, which the API does not expose; `wigner_widths` gets it
out of AZURE2 itself by transforming a probe vector with every rwa set to a tiny
`eps`, so the shift denominator is 1 and `Γ_c(eps) = 2 P_c eps²`. One extra
`TRANSFORM_RWA`, at AZURE2's own radii and Coulomb functions — it reproduces the
GUI's Γ_W (7/2⁻ 4.57 ³He+α: 3.487e5 eV, θ² = 0.494).

**γ-ray strengths.** W.u. against the Weisskopf estimates E1 `6.8e-2 A^{2/3}
E³`, E2 `4.9e-8 A^{4/3} E⁵`, M1 `2.1e-2 E³` eV with E in MeV (E1–E4/M1–M4 in
`pyazr/widths.py`). Note Γ is **not** ∝ rwa² for a capture channel — the
external-capture term is linear in the amplitude — so convert with
`transform_rwa`, never by squaring.
