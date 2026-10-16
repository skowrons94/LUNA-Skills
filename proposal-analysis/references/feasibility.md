# Feasibility

## Count rates and beam time

- Start from the observable the decision needs (a cross section at an energy, a yield over a window, an asymmetry, a resonance strength) and its target uncertainty; derive counts, then beam time. Do not start from the beam time available.
- Use the facility's own beam specification (species, charge states, energy range, current at the relevant beamline, time structure such as pulsing) and record its source and date. Currents on beamlines at large deflection angles or with small beam spots can be several times lower than nominal.
- Thick-target yield: Y(E) = ∫ σ(E')/ε(E') dE' over the energy loss in the target, with ε the stopping cross section per active nucleus (include stoichiometry and enrichment). For a narrow resonance in an infinitely thick target, Y_max = (λ_r²/2) ωγ (m_p + m_t)/m_t / ε_r, with λ_r = h/p_cm (not ħ/p_cm) the centre-of-mass de Broglie wavelength at the resonance and ε_r the laboratory effective stopping cross section per active nucleus there, ε_r = ε_active + Σ_i (N_i/N_active) ε_i over the other target constituents i. Multiply by efficiency, branching ratio and angular-distribution factor to obtain detected counts, and fold beam energy spread and straggling into the yield integral when they are not negligible compared with the window. Stopping powers and target profiles: `target-analysis`; detection efficiency and summing: `efficiency-analysis`.
- Non-resonant yields scale with target thickness (while σ/ε is roughly constant over it): recompute hours when moving from thick to thin targets. For a narrow resonance the plateau yield does not depend on thickness while ΔE ≫ Γ and the beam spread; below that the maximum yield is Y_max (2/π) arctan(ΔE/Γ) (neglecting beam spread and straggling). A thinner target then costs scan points, not counts per coulomb at the plateau.
- Include dead time and pile-up (detector count-rate limits can cap the current), radiation-protection limits on neutron or γ production, and the beam-time overheads (calibration, background, target changes, resonance scans).

## Backgrounds

- List beam-induced backgrounds by threshold and target contaminant (e.g. light-element (α,n) or (p,γ) channels on backings, slits and collimators) and room or cosmic background for the detector; use measured background rates for the specific detector when available.
- Plan blanks on identical backings and separate time windows (pulsed beams, time of flight, coincidence windows) where they remove a background class.

## Uncertainty budget

- Tabulate statistical, independent systematic and shared (correlated) components separately: charge or beam current, target areal density and stoichiometry, stopping powers, detection efficiency (and its energy dependence), angular distribution, summing, screening, analysing power or other calibration scales.
- Mark which components are shared across energies, runs, datasets or reactions; these determine covariances downstream (see covariances.md).
- A scale uncertainty that cancels in a ratio or asymmetry is one of the strongest arguments for a measurement; say so explicitly and show which terms cancel.
- Check every component against a source or a validation measurement; a budget made of round numbers is a red flag for a specialist.
