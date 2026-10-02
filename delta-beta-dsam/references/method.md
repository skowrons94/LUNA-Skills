# Δβ method: formulas, systematics and uncertainty budget

## Formulas (c = 1)

Recoil at the reaction point (beam b along z, ejectile e measured, target at rest):

    |p_R|² = p_b² + p_e² − 2 p_b p_e cos θ_e
    β_reac = |p_R| / √(|p_R|² + (m_R + E_x)²)
    E_x    = √(E_R² − |p_R|²) − m_R,   E_R = T_b + m_b + m_t − (T_e + m_e)

Doppler shift and inversion (θ: angle between γ and recoil, R = E_obs/E0):

    E_obs = E0 √(1 − β²) / (1 − β cos θ)
    β_ems = [R² cos θ ± √(1 + R² cos² θ − R²)] / (1 + R² cos² θ)

The positive root applies above ≈85°, the negative below (choose the root closest to β_reac).
∂β_ems/∂E ∝ 1/cos θ: windows near 90° carry little information and large tails.

Slowing down (constant stopping over the decay time):

    dβ/dt = β c · m² / (β E_tot³) · dE/dx = c m² / E_tot³ · dE/dx,   Δβ ≈ (dβ/dt) τ

c = 0.2998 µm/fs. Example: 27Si at 110 MeV in Au, dE/dx = 10.8 MeV/µm → 1.24×10⁻⁴ fs⁻¹;
15O at β = 0.065 in Au–3He: 9.7(3)×10⁻⁵ fs⁻¹ (SRIM), fitted 9.4(2)×10⁻⁵ fs⁻¹ (15O paper).

## Systematic distortions of Δβ(θ)

- γ-energy offset ΔE (E0 or calibration): distortion largest near the root-exchange angle and with a
  residual at the most forward/backward angles; fitted per transition.
- Emission-angle offset Δθ (array position, target position, PSA): similar shape near 90°, degenerate
  with ΔE over limited ranges; fixed to the average over all transitions.
- β_reac bias from the ejectile energy scale or energy-loss correction: constant offset of Δβ at all
  angles (recoil in a narrow forward cone); absorbed by the calibration intercept, bounded by E_x.
- Effective beam energy (reaction depth): common to all channels → intercept.
- Single-event resolution (energy, PSA, ejectile straggling, ring pitch): broadens the distribution,
  does not move the centroid — except at acceptance edges (drop edge windows).

## Uncertainty budget (structure)

| Source | Effect on Δβ | Treatment |
|---|---|---|
| centroid statistics | usually dominant | posterior |
| γ-energy offset ΔE | included in the centroid fit | nuisance, fitted |
| β_reac energy gain and angle | small; bound it with the known E_x | bounded by E_x |
| effective beam energy | common to all channels | intercept |
| calibration intercept | from the ejectile energy-calibration prior | posterior |
| calibration slope (stopping power) | the stopping-power uncertainty (a few %) | posterior |

Single-event Δβ resolution is of order 10⁻² in the 27Si simulation (β = 0.095, main-interaction-point
direction, 1 mm SAURON); measure it from the data for each campaign. Precision scales as σ/√N.

## Calibration and fit choices

- Linear calibration Δβ = a τ + b fitted to transitions of known τ (e.g. 18F in a 15O run, scaled by the
  stopping-power ratio between the recoils) and/or to simulations analysed with
  exactly the same estimator.
- Bayesian fit (emcee): Gaussian priors on slope (stopping-power uncertainty) and intercept; literature
  priors on the unknown lifetimes (asymmetric Gaussians, half-Gaussians for upper limits); report also
  the flat-prior result.
- Linearity: verify with the simulation up to the largest τ used (27Si with 1 µm Au: saturation above
  ≈30 fs because the recoil exits the backing).
