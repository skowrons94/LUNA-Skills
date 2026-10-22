# Physics of the network, and where it misleads

Read this before quoting a network number. Most wrong results here do not come from the solver. They come from a rate that means something other than what the network assumes, or a one-zone model asked a question it cannot answer.

## Rates the network expects

- **Units and convention.** Tables hold N_A⟨σv⟩ in cm³ mol⁻¹ s⁻¹ (two-body) or s⁻¹ (decays), on a T9 grid. The network multiplies by ρ^(n−1), the molar abundances and pynucastro's identical-particle factor 1/n! (for ¹²C+¹²C, 3α, p+p). Tables must therefore **not** already contain 1/(1+δ_ij). REACLIB and STARLIB follow this convention. Check any literature table, and AZURE2 output for identical particles, before use.
- **Bare rates only.** The network applies plasma screening (`network.screening`). A rate entering it must be the bare-nucleus rate. An R-matrix fit to laboratory data that were not corrected for laboratory electron screening contains that enhancement. Plasma screening on top of it double counts. Correct the data (state the potential U_e and its source) before the fit, or state that the rate is lab-screened and run with `screening: none` only for comparison.
- **Detailed balance.** Replacing a forward rate without its reverse breaks equilibrium wherever the reverse matters (photodisintegration above T9 ≈ 0.3–0.5, (p,α)/(α,p) pairs). The builder derives the reverse by default with pynucastro partition functions and Q from the mass table. REACLIB's own reverse fits omit partition functions and use older Q values, so they differ from derived reverses by up to ~10 % above T9 ≈ 1 and by exp(−ΔQ/kT) at low T. That difference is a library inconsistency, not an uncertainty.
- **Validity range.** REACLIB fits are meant for T9 = 0.01–10. A table is exact only on its grid. `outside: error` is the default because a silently extrapolated rate is the commonest hidden assumption. REACLIB-form fits of a table (`rates.py fit`) are unconstrained outside the fitted range.
- **Q values.** Energy generation uses pynucastro's nuclear masses. Rates carry their library Q only for reverse-rate construction.

## Weak rates

- REACLIB weak rates are laboratory decay rates: no temperature or density dependence. For T9 ≳ 0.5, or densities where electron captures matter (ρYe ≳ 10⁶ g/cm³), use tabulated stellar weak rates. pynucastro provides `TabularLibrary` (Suzuki, Langanke, FFN); the engine evaluates them with ρ and composition.
- Energy generation `E` counts the mass change of every reaction. For REACLIB β decays the neutrino energy is not removed (pynucastro removes it only for tabulated weak rates). For CNO burning this overstates the energy by ~6 %. Do not quote `E` as a luminosity without that correction.

## Isomers: ²⁶Al and others

pynucastro's REACLIB contains only total `al26`, which decays with the ground-state half-life (0.717 Myr). Below roughly 0.15 GK the ground state and the 228-keV isomer (6.3 s) do not communicate thermally. Between ~0.15 and ~0.4 GK the coupling is partial, and above ~0.4 GK they are in equilibrium (Gupta & Meyer 2001; Iliadis et al. 2011). Consequences at hydrostatic temperatures:

- A total ²⁵Mg(p,γ)²⁶Al rate puts the isomer's share into long-lived ²⁶Al. The ground-state yield is then overestimated by 1/f_gs.
- The effective fix below ~0.15 GK is `branch`: fraction 1−f_gs of ²⁵Mg(p,γ) goes directly to ²⁶Mg (the isomer decays before it can capture). Take f_gs(T) from the measured branchings to the ground state and isomer (it is temperature dependent: use the value at the burning temperature, or split into separate table rates). Record its source in `why`.
- In the partial-coupling range neither one species nor two isolated species is right. That needs explicit ground and isomer species with the coupling transitions, which this engine does not build automatically.

## What a one-zone network cannot tell you

- **No mixing, no feedback.** T and ρ are prescribed. Convective envelopes (hot-bottom burning), shell mergers, the AGB ¹³C pocket and the i-process are set by mixing at least as much as by the rates. A one-zone ranking for such a site screens candidate reactions. Confirm it with a stellar model (MESA, via the stellar-evolution workflow) before stating the impact.
- **Self-heating.** If the burning changes T (thermonuclear runaways, ignition), a prescribed trajectory is a post-processing approximation that is valid only if the trajectory came from a model with the same nuclear physics. Changing a rate that powers the trajectory makes the trajectory inconsistent.
- **Site dependence.** A sensitivity coefficient belongs to one (T, ρ, time, initial composition). Scan the condition range of the site (`T_scale`, several trajectories) before calling a rate important. A rate that matters only at the edge of the range is a weak case.
- **Equilibria.** When a cycle is in steady flow (CNO, Mg–Al at high T) the abundance of an intermediate depends on its own destruction rate, not on its production rate. A small sensitivity for a production rate is often physics, not a bug.

## Hydrostatic reference points (for sanity checks)

| Site | T (GK) | ρ (g/cm³) | Time | Typical question |
|---|---|---|---|---|
| Solar core, H burning | 0.015 | 150 | Gyr | pp/CNO, neutrino fluxes |
| CNO in massive MS stars | 0.03–0.04 | 5–10 | Myr | ¹⁴N(p,γ) bottleneck |
| Hot-bottom burning (AGB) | 0.07–0.1 | 1–10 | short pulses, diluted | Mg–Al, Na–O |
| Core He burning | 0.1–0.3 | 10³–10⁴ | 10⁵–10⁶ yr | ¹²C(α,γ), C/O |
| Core C burning | 0.6–1.0 | 10⁵–10⁶ | 10²–10³ yr | ¹²C+¹²C |
| Classical novae | 0.1–0.4 peak | 10²–10⁴ | 100–1000 s | (p,γ) on ¹⁷,¹⁸F, ²⁶Al, ²²Na |

These are orders of magnitude for checks, not inputs. Take the conditions of a study from a model or a cited parametrisation.
