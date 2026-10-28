# Mixing: the other half of every surface-abundance question

A surface abundance changed by a nuclear rate is always also changed by mixing, and in the literature mixing is usually the larger and less certain lever. Study rates *across* mixing prescriptions: a rate effect is meaningful only if it is distinguishable within the spread of plausible mixing, or if it changes what mixing is needed to match observations (the usual case for ¹²C/¹³C, Li, ³He, Na, Al).

## Where mixing enters

| Phase | Process | MESA controls (`&controls`) | Literature anchor |
|---|---|---|---|
| Main sequence, convective cores | overshoot | `overshoot_scheme/f/f0(i)`, zone and boundary selectors | Herwig 2000-style exponential overshoot |
| First dredge-up | convective envelope deepening (standard) | `mixing_length_alpha`, `MLT_option` | standard models; the baseline to beat |
| RGB above the bump | thermohaline (³He-driven μ inversion) | `use_Ledoux_criterion = .true.`, `thermohaline_option`, `thermohaline_coeff` | Charbonnel & Zahn 2007; Charbonnel & Lagarde 2010 |
| RGB/AGB | rotation-induced mixing | rotation flags in `&star_job`, `D_*_factor`, `am_*` | Charbonnel & Lagarde 2010 (with rotation) |
| RGB/AGB | magnetic buoyancy, "deep mixing" | no built-in prescription: `other_D_mix` hook in `run_star_extras` | Busso et al. 2007; Palmerini et al. 2011; Vescovi et al. 2020 |
| TP-AGB | third dredge-up (needs boundary mixing at the convective envelope and pulse-driven zone) | exponential overshoot `f` at those boundaries | Herwig 2005 (review) |
| TP-AGB | hot-bottom burning (envelope base hot enough for CN, Ne–Na, Mg–Al) | `mixing_length_alpha` (strongly), mass, metallicity; mass loss sets its duration | Karakas 2014 (review) |
| TP-AGB | ¹³C pocket (partial proton mixing) | overshoot `f` below the envelope after TDU, or `other_D_mix` | Herwig 2005; Straniero et al.; `c13_pocket` test case |

## Thermohaline efficiency: MESA vs the literature

MESA's Kippenhahn option (`turb/private/thermohaline.f90`, r26.04.1) uses

D = α_th · (3/2) · K/(ρ c_p) · (−∇_μ term)/(∇_ad − ∇),

while Charbonnel & Lagarde (2010, Eq. 3) write D = C_t · K_th · (φ/δ)(−∇_μ)/(∇_ad − ∇), with K_th the thermal diffusivity. Hence **C_t = 1.5 α_th**: the C_t = 1000 of Charbonnel & Zahn (2007) and Charbonnel & Lagarde (2010) is `thermohaline_coeff = 667`, and Kippenhahn's original α_th ≈ 2 is C_t ≈ 3. C&L's Eq. 4 relates C_t to the finger aspect ratio α: C_t = (8/3)π²α² (α = 5 gives 658). `'Brown_Garaud_Stellmach_13'` (coefficient 1) is the simulation-calibrated prescription, much less efficient than C_t = 1000. Bracket the plausible range by running all three, not one.

Thermohaline mixing needs `use_Ledoux_criterion = .true.` and a net with ³He (pp chains explicit).

## Thermohaline runs and the mesh: refine the smoothing with the mesh

A cell mixes by thermohaline only where `gradL_composition_term < 0` (`star/private/turb_support.f90`). That term is the composition part of `brunt_B`: the EOS is evaluated at fixed ρ and T with the neighbouring cell's composition, and the result is smoothed over `num_cells_for_smooth_gradL_composition_term` cells on each side (default 3; `hydro_vars.f90`, `threshold_smoothing` in `star_utils.f90`). Above the bump the μ inversion is tiny away from the ³He-burning layer. When the mesh is refined, the μ difference per cell falls with the cell size, and the smoothing width (a fixed number of cells) falls too. The sign of the term then follows numerical noise, and cells with zero mixing appear between the shell and the envelope. A single non-mixing cell blocks the transport.

What this looks like (1.25 Msun, Z = 0.02, C_t = 1000, NACRE, r26.04.1; LUNA project, 2026-10-28):

| Run | Surface drop starts at log L | Tip ¹²C/¹³C |
|---|---|---|
| Standard (`mesh_delta_coeff` 1.5 from `1M_thermohaline`) | 1.56 (the bump) | 8.20 |
| `time_delta_coeff` 0.25 only | bump | 8.04 |
| `mesh_delta_coeff` 0.5 only | 3.14 | 13.72 |
| `mesh_delta_coeff` 0.25 + `time_delta_coeff` 0.25 | none before the tip | 26.88 (dredge-up value) |
| `mesh_delta_coeff` 0.5 + smoothing over 9 cells | 1.53 | the ratio runs 5–10 % below the standard run at equal log L |

In the profiles, the standard run has one thermohaline region from just above the shell to the envelope base. The mesh-0.5 run has the same region only up to r ≈ 0.12 R☉, then a non-mixing gap of about 260 cells (μ still rises outward there, by about 2×10⁻⁷ per cell against 6×10⁻⁶ per cell in the standard run), then a few short thermohaline patches.

How to test thermohaline results for resolution:
- Scale `num_cells_for_smooth_gradL_composition_term` with the number of cells, so that the smoothing keeps its width in mass. Count the cells between the H shell and the envelope base in the profiles of both runs: 3 cells at the standard mesh became 9 at `mesh_delta_coeff` 0.5.
- Do not read a later onset on a finer mesh as convergence. First check the profiles: plot `mix_type` between the shell and the envelope, and look for gaps. Add `gradL_composition_term`, `brunt_B` and `log_D_thrm` to the profile columns of resolution runs.
- Vary the time step separately (`time_delta_coeff`). MESA refuses `varcontrol_target` below `min_allowed_varcontrol_target` (1d-4). Lattanzio et al. (2015, MNRAS 446, 2673) found the time step the critical parameter in the four codes they compared (Li, 1.25 Msun). Their tests did not include MESA's resolution, and in MESA the smoothing effect above dominates.
- Quote a rate shift only from pairs with identical numerics. The setup moves the absolute tip ratio by about as much as a 5–10 % rate shift.

## Doing it

- One mixing change per comparison, crossed with the rate change: a 2 × N grid (rates × mixing prescriptions) is the minimum for a rate claim about surface abundances.
- Start from the pre-main sequence with the final network. Changing the network on a loaded model leaves new isotopes at zero (e.g. ¹³C), which biases first-dredge-up ratios.
- Compare at the same phase: after first dredge-up (e.g. when the convective envelope reaches maximum depth), at the bump, at the tip, and after a given number of thermal pulses. Not at the same age.
- Report the mixing parameters with the result, and the observational sample used for comparison (cluster, mass range, metallicity).
