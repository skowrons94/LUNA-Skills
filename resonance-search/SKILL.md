---
name: resonance-search
description: Automated, gated search for missing, surplus or misassigned resonances in a multichannel R-matrix evaluation (AZURE2/pyazr) fitted to many excitation functions — data audit, pattern map of unreproduced structure, window searches that add/delete/re-assign/move levels, structure-aware acceptance gates, merges, an unattended driver loop, and the final consolidation. Use when a level scheme must be extended or repaired against dense angular/excitation-function data (elastic scattering, (p,α), (α,α), THM), when χ² stalls far above 1, or when the user asks for "automatic resonance fits". For single AZURE2 runs, fits or extrapolations use the azure2 skill.
---

# Automated resonance search in R-matrix evaluations

The aim is a level scheme that reproduces the **resonance structure** of every data set with
physically admissible parameters, not the lowest χ². A model can lower χ² by smoothing real
resonances away or by oscillating between data points; neither is a better evaluation. Every
accepted change must improve χ² **and** keep the structure, the physics limits and the other data
sets intact.

## Route the task
- Single calculation, fit, decomposition, extrapolation or rate: `azure2` skill.
- Project layout, logs, reports: `nuclear-research-project` skill.
- Adding, deleting, re-assigning or moving levels against many data sets: this skill.

## Non-negotiable boundaries

- **Data are evidence.** Never edit published files. Masked, cut or re-extracted data are new files
  in `data/processed/` with the reason recorded. A point is excluded only for a documented
  experimental reason (transcription error, contaminating reaction, energy range disowned by the
  authors), never because the model misses it.
- **Published uncertainties.** Quote χ² against them. If the point-to-point scatter exceeds them,
  say so and give the implied χ²/N floor; do not inflate errors to reach a target.
- **Frames.** AZURE2 reads LAB energies and angles and compares the model with the data in the
  CENTRE OF MASS, as model/n − d_cm. Plot and audit in the same frame, with the data multiplied by
  n.
- **Parametrisation.** State it. With the Brune alternative parametrisation, energies and widths are
  observed values.
- **Physics limits.** θ² ≤ 1 in every channel for levels inside the data range. Background poles
  above it may exceed 1 up to a stated cap. Say which form the bound uses:
  - formal: γ²/(ħ²/μa²), the natural fit bound;
  - observed: Γ_c/Γ_W, with Γ_W = 2P_l(E_r)ħ²/(μa²).

  The two forms differ by the level-shift factor, which is 70+ for distant poles. Bound the poles
  formally and audit them on the observed θ².
- **Resolution.** No level narrower than the data can resolve: compare the c.m. total width with
  max(experimental resolution [beam spread ⊕ target thickness], energy step) at that energy.
- **Allowed J^π.** Two 0⁺ particles in their ground states (α₀+²⁰Ne, ¹²C+¹²C g.s.) → natural parity
  only. Exits to excited states (α₁, p₁) and channels with non-zero spin (p+²³Na 3/2⁺) also allow
  unnatural parity. Identical 0⁺ bosons in the same state → even L, so even J⁺. Their cross sections
  carry 1 + δ₁₂ = 2: check which channels your build applies it to (some builds apply it to elastic
  only).
- **Normalisations** float only with a prior equal to the stated systematic uncertainty, and are
  written to the segment line (they do not survive a generic write-back). When you fit through
  the pyazr residual API, add the prior term ((n−1)/σ_sys)² explicitly. Arbitrary-scale data
  (THM, unpublished yields) get an unconstrained or profiled norm and are plotted scaled.
- **No hidden degrees of freedom**: no per-segment energy shifts or extra error terms unless the user
  asks; any that are used are reported with the result.
- **Channel radii** are stated per partition, scanned (χ² against a) and kept the same in
  evaluations that will be combined. Reduced widths are comparable only at the same radius.

## Workflow

### 0. Data audit (before any fit)
- Cross-check repeated angles/energies between files: identical values at the same energy in two
  angles are transcription copies.
- Read the paper of every data set for energy ranges with overlapping reactions or contamination,
  resolution (beam spread, target thickness, step size) and the energy definition (effective
  E₀ − ΔE/2 data must not be target-integrated again).
- Re-extract digitised data from vector graphics when possible (exact calibration from tick marks);
  compare scale and error bars with the paper.
- Compare overlapping data sets after smoothing the sharper one to the coarser resolution; flag runs
  of consecutive points that disagree in one direction.

### 1. Baseline and gate metrics
Score each data set by χ²/N. For each angle, also compute
R = rms(Δ²model / y_data) / rms(Δ²data / y_data) and the correlation of the two second differences.
Divide by the data value y_data in both terms, with the model rescaled to the data per angle. Never
divide by the model's own value: one interference zero then dominates the angle. Record θ²_max (levels, poles), the count of unresolvable levels and the
normalisations.

### 2. Pattern map
For each angle, find significant extrema of ln(data) (prominence > max(0.1, 3σ/y)) and of ln(model)
on the same grid; match within two grid steps. Cluster unmatched data features across angles: a
feature seen at ≥ 5 angles (≥ 2 for sparse data) is a missing or misassigned level; unmatched model
features across angles are surplus structure. Rank clusters by the local χ².

### 3. Window search
Around each target (±50–70 keV, non-overlapping windows, run in parallel):
- **Candidates**: add (each allowed J^π on a grid), delete, re-assign J^π, move, revive a dormant
  level. Screen all candidates with one Jacobian (linearised gain), keep the best few, refit each
  locally (window ± 150 keV) and take the best that passes the gate.
- **Gate**: total χ² decreases; no data set worsens beyond a small tolerance; structure amplitude
  does not move away from its target and correlation does not drop; θ² limits hold; the count of
  unresolvable levels does not grow. An added level must beat its parameter cost (Δχ² > 2k for k
  new parameters, AIC; or an F-test); log Δχ² for every level. Two rounds per window.
- Target the screen at the data family that shows the feature; allow the parities that family
  permits.

### 4. Merge
Apply all accepted window operations to the current best, transplant the windows' fitted widths,
and refit the union of the windows jointly **in chunks**, scoring the gate after each chunk and
keeping the best passing state. Before merging, drop any added level narrower than the resolution
limit and any duplicate of a level a neighbouring window added at the shared edge.

### 5. Loop
Repeat 2–4 automatically, skipping regions rejected in the last passes and a documented blacklist
of regions where every change has cost another data set. Stop after two passes gaining less than a
set threshold. Alternate passes between the data families so the weaker data are not swamped.

### 6. Consolidation and report
Gaussian convolution (beam spread, data at an effective energy) and target integration (thick
targets with stopping powers, `<targetInt>`) are different corrections. Never apply both to the same
data. If either changes χ² little (measure it on/off at fixed parameters), switch it on only for
the final fit, because it multiplies the cost of every evaluation.

Report:
- χ²/N per data set against the published errors;
- normalisations, and the excluded data with the reason for each;
- per level: E_x, J^π, observed partial widths Γ_c and θ²_c (ANCs for sub-threshold levels);
- uncertainties from the Hessian/MINOS, with MCMC for the reported model;
- comparison with ENSDF and other compilations, flagging every J^π that differs from previous
  assignments and the data that drive it;
- the census of states per J^π constrained by each data set.

## Pitfalls that cost days

- Fit energies only with bounds that keep ≥ 1 keV from every same-J^π level, live or dormant:
  AZURE2 merges coincident same-J^π levels on reload and the saved file no longer reproduces the
  fit. Always reload the written file and compare χ².
- The fit library's pole threshold must match where the background poles are; otherwise poles are
  bounded as ordinary levels (θ² ≤ 1) and the approved cap never applies.
- Segments that cut a data file in the middle: take energies and data from the engine
  (`m.energies`, `m.cross`), never from the first n rows of the file.
- Keep one grouping function for data families shared by gates, screens and pattern maps; a copy
  elsewhere silently classifies new data sets wrongly.
- Operation journals per window must start fresh each run; reused window tags otherwise re-apply
  old operations at the next merge.
- Two merges writing the same scratch model corrupt each other; one merge at a time.
- Memory of folded fits grows with points × threads × parameters: reduce threads, not points.
- Logs: filter AZURE2's repeated warnings at the source; a full disk stops every tool.
- `pgrep -f pattern` inside a shell whose command line contains the pattern matches itself; use
  `[p]attern`.
- Check the AZURE2 build: identical-particle factors and THM options differ between branches; plot
  with the same build that fitted.

## Deliverables
- The evaluation file of the best model and its folded (reported) version.
- A campaign log: every pass, every accepted and rejected change, every data decision.
- Figures: data and fit on a common E_x axis (PRC style), proton/alpha excitation functions, census of
  constrained states per J^π, states shared between evaluations.
- A status report with per-data-set χ²/N, physics checks and limitations.
