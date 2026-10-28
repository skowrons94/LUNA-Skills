# From spectroscopic amplitudes to R-matrix reduced widths

Worked case: ⁷Be, FSU interaction (s-p-sd-pf, Lubna et al. PRC 100, 034308 (2019); PRR 2, 043342 (2020)) with
cluster channels built as in Kravvaris & Volya (PRL 119, 062501 (2017); PRC 100, 034321 (2019)), compared with a
multichannel AZURE2 fit at a = 4.70 fm (³He+α) and 4.40 fm (p+⁶Li). The collaborator's files: a structure
yaml (levels and amplitudes), potentials, widths, and an R-matrix template.

## Rules

1. **Use the amplitudes, not the energies.** Phenomenological CI energies of intruders can be off by MeV
   (FSU 1/2⁺ at 6.52 MeV against 7.79 fitted). Evaluate every width at the fitted energy.
2. **Cluster SF as built.** Codes may also offer a channel "normalized to 1". Check what it divides by: the
   correct factor for two 0s clusters is the projected norm-kernel eigenvalue μ_Q of the Q oscillator quanta
   (α+³He: μ3 = 1.191, μ4 = 0.5955, μ5 = 1.1992; Horiuchi Eq. 4·1·12 gives 343/288, 343/576 exactly). The
   ⁷Be files' "new" SF used an unprojected norm (old/new = 6.95 at Q = 4 instead of 1/0.5955): it included
   spurious centre-of-mass states (Volya, 2026). Only the as-built SF is well defined; renormalize, if at all,
   as SF/μ_Q. The analytic limit fails where the space is truncated (3ħω without the g shell: 0.770 against
   0.806) and for core calculations with mixed ħω (YSOX).
3. **Sum-rule check.** Σ over states of SF/μ_Q for one (L, Q) channel approaches the number of J values when the
   space is complete (1 for L = 0 with channel spin 1/2, else 2). ⁷Be: 2.000 (L = 1, 3; Q = 3), 0.970 (L = 0,
   Q = 4), 2.078 (L = 4); Q = 5 (2ħω) incomplete, 0.29–0.38. A normalization that gives 0.083 is wrong.
4. **Recouple j-j to channel spin.** A nucleon channel amplitude is Σ_j U A_j with
   U = (−1)^(l+½+I+J) √((2j+1)(2s+1)) {l ½ j; I J s} (`amplitudes.recouple`; unitary over j for each s).
   Check that the recoupled amplitudes reproduce the collaborator's own channel amplitudes exactly.
5. **Single-particle width in the R-matrix convention.** For each channel: a Woods–Saxon (nucleons: e.g. the
   Seminole parameterization, Schwierz, Wiedenhöver, Volya, arXiv:0709.3525) or cluster potential with the Pauli
   node count; adjust the depth so that the interior solution has a·u'/u = S_l(E) at the fitted energy and
   channel radius; γ²_sp from the interior norm, Thomas-corrected (θ²_obs = θ²_formal/(1 + γ² dS/dE)). Then
   θ² = SF · θ²_sp in the same units as the fit (state TW = 3ħ²/(2μa²) or ħ²/μa²; pyazr's theta2 is TW).
   Flux or phase widths of a broad non-resonant s wave do not compare with an R-matrix γ (⁷Be 1/2⁺: R-matrix
   Γ_sp 8.0 MeV against a flux width of 1.74 MeV).
6. **Reconstruct the geometries from the collaborator's numbers** when the potential files are missing:
   fit R, a (and R_c, spin-orbit) to their depth/energy/ANC triples (⁷Be: 11 p+⁶Li bound states to ≤ 16 keV).
7. **Bound states compare through ANCs**, not widths, and widths ∝ ANC² (quote ratios of ANC² when you
   say "widths").

## What the comparison found in ⁷Be (what to expect)

- α-cluster states (g.s., 1/2⁻, 7/2⁻₁, 5/2⁻₁): SF ≈ 1 (as built), predicted widths 1.4–2.1× the fitted ones.
- The 1/2⁺ (fitted at 7.79 MeV): a proton in 1s₁/₂ on ⁶Li, SF 0.32 → θ²_p 0.23 TW against 0.16 fitted;
  α SF 0.076 → θ²_α 0.07 TW (0.12 renormalized) against 0.71 fitted: the α width is not spectroscopic; the
  renormalized s-wave strength (0.97) lies at 13.7 MeV.
- A channel the fit lacked: the second 7/2⁻ decays by p wave to ⁶Li(3⁺) (SF 1.21). Adding it improved χ² by
  319 (−270 with a Park-norm bound; `r-matrix` physicality.md).
- Widths the model cannot give: a d-wave proton width of the 1/2⁺ (fit 0.15 TW against 0.0003; a factor ~600)
  and f-wave proton widths of 5/2⁻ levels (0f enters only at 2ħω). Report them as open, not as agreement.
- Bound-state ANCs: FSU α ANCs ~1.6× the fit's, but their ratio (0.83 vs 0.89) is closer.
