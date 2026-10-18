# Reaction kinematics

Generate reaction products outside Geant4 when the reaction is rare, the library cross sections are unreliable at the energies of interest, or the energy–angle correlation must be controlled. `scripts/kinematics.py` implements the formulas below with the standard library only.

## Two-body relativistic kinematics

Reaction 1 + 2 → 3 + 4, projectile 1 with laboratory kinetic energy T₁ on target 2 at rest, particle 3 detected at laboratory angle θ, residual 4 possibly excited (m₄ → m₄ + E_x). With E = T₁ + m₁ + m₂, P = √(T₁(T₁ + 2m₁)), s = E² − P² and K = (s + m₃² − m₄²)/2, energy–momentum conservation gives E·E₃ − P·p₃ cos θ = K, so

p₃ = [K P cos θ ± E √(K² − m₃²(E² − P² cos²θ))] / (E² − P² cos²θ),

keeping the non-negative roots that satisfy the unsquared equation. Two roots exist when the centre-of-mass velocity exceeds the ejectile's CM velocity (endothermic reactions near threshold, heavy projectiles on light targets): both are physical and populate the same lab angle with different energies, up to a maximum angle.

- Threshold (Q < 0): T_thr = [(m₃ + m₄)² − (m₁ + m₂)²] / (2m₂). For ⁷Li(p,n)⁷Be, Q = −1.644 MeV and T_thr = 1.880 MeV; just above it the neutrons are confined to a forward cone with two energies per angle.
- CM to lab: from cos θ_cm, E₃* = (s + m₃² − m₄²)/(2√s), p₃* = √(E₃*² − m₃²); boost along the beam with β = P/E, γ = E/√s. Use this to sample events with a CM angular distribution.
- Excited final states: replace m₄ by m₄ + E_x and close the channel when √s < m₃ + m₄ + E_x. Each state gives its own neutron (or proton) group; the residual then decays (gamma, pair or particle emission). For ¹³C(α,n)¹⁶O the first excited states lie near 6 MeV, so they open only for alpha energies of a few MeV.
- Capture reactions (p,γ), (α,γ): m₃ = 0. E_γ(θ) ≈ Q + E_cm − recoil, Doppler-shifted by the CM motion; the same formula applies with m₃ = 0 (no maximum angle, one root).
- Use nuclear masses (atomic mass minus Z electrons) consistently; Q values from atomic mass excesses are the same because Z is conserved. Non-relativistic formulas differ by fractions of a per cent at MeV energies for light ejectiles; use the relativistic ones and check against the non-relativistic limit as a test.

## Thick targets

- A beam stopping in a thick target produces products at every energy from T₀ down to threshold (or to where the cross section vanishes). The yield per incident projectile at energy E in dE is n σ(E) dE / ε(E) with ε the stopping cross section per active nucleus (include stoichiometry and inactive constituents; `target-analysis` for stopping powers, `proposal-analysis` for yields).
- Fold kinematics over the energy loss: for each slice [E, E + dE] weight w = σ(E)/ε(E) dE and add the product energies at the angle of interest, or the full CM angular distribution. `thick_target_spectrum(m1, m2, m3, m4, T0, sigma, stopping, theta_deg=None)` returns (T₃, weight) pairs; `histogram()` bins them into the `hist` format of the template.
- Include beam energy spread and straggling when they are comparable to the structure of σ(E) (narrow resonances); the folding above assumes a sharp beam energy at each depth.
- Resonances: a narrow resonance in a thick target gives a narrow group of products at the resonance energy plus the non-resonant continuum; sample both with their relative yields.
- Angular distributions of the products in the CM frame (Legendre coefficients from data or R-matrix, `azure2`) are applied as weights or by rejection before the boost.

## From kinematics to the simulation

```bash
python3 kinematics.py "13C(a,n)16O" --T1 5.0 --theta 0 30 60 90           # E(theta) table, both roots
python3 kinematics.py "7Li(p,n)7Be" --T1 2.5 --theta 0 --Ex 0.429          # excited residual
python3 kinematics.py "13C(a,n)16O" --T1 5.0 --spectrum n_spec.csv --bins 50   # angle-integrated, isotropic CM
python3 kinematics.py "13C(a,n)16O" --T1 5.0 --events 10000 --seed 1 --out n_events.csv   # keeps E-direction correlation
```

- The angle-integrated spectrum with an isotropic source loses the correlation between energy and direction; it is acceptable only for a detector that surrounds the source symmetrically. Otherwise use the event list.
- `kinematics.py` holds a small mass table of light nuclides (AME2020 mass excesses); for other nuclides pass masses through the Python functions. Check every new reaction against a published Q value and threshold.
- Tests: `python3 test_kinematics.py` (conservation, thresholds, Q values, two-root region, non-relativistic limit, CM↔lab round trip, thick-target weights).
