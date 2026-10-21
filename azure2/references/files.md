# AZURE2 files

## `.azr` file anatomy

Plain-text, section-tagged; prefer the GUI or `AzrModel` over hand edits.

- `<config>` — A-matrix flag, `output/` and `checks/` dirs, check toggles.
- `<levels>` — one line **per channel of each level**, 31 fields matching
  `NucLine` (`include/NucLine.h`); the file stores `2J`, `2S`, `2L` as integers.
  Blank line between levels; `levelID` groups them.
- `<segmentsData>` — one line per data segment: `isActive entranceKey exitKey
  minE maxE minA maxA isDiff [phaseJ phaseL] dataNorm varyNorm dataNormError
  [energyShift …] dataFile`. A `+10` on `isDiff` marks a THM/HOES segment.
- `<segmentsTest>` — extrapolation grids (see [model-editing.md](model-editing.md)).
- `<targetInt>` — target/experimental effects (integration, convolution).
- `<parameterSettings>` — free/fixed, limits, nuisance, category, Minuit index.
- `<mcmc>` — walkers, steps, threads.

## Data file format (`.dat`)

Convert tables with `analysis-chain`'s `adapters.py to-azure` (frame, units, S factor → cross section) and check them with `contracts.py check azure-dat`.

Four whitespace-delimited columns, **lab frame, forward kinematics**:
energy (MeV) · angle (deg) · cross section (b, or b/sr if differential) ·
uncertainty. The angle column is required even for angle-integrated data (dummy
value). Phase-shift data uses the same layout with the phase (deg) in column 3.
Analyzing-power data uses it with `A_y` (dimensionless, signed) in column 3 —
and its **angle column is centre-of-mass**, not lab.

## Output files (all center-of-mass)

- `AZUREOut_aa=<in>_R=<out>.out` — 9 cols: cm E, excitation E, cm angle, **fit**
  σ, fit S, **data** σ, data σ err, data S, data S err. For an analyzing-power
  segment, cols 4 and 6 hold `A_y` instead of σ (dimensionless, may be negative). `TOTAL_CAPTURE` in place
  of `R=<out>` for summed capture. `.band` files carry the covariance band.
- `AZUREOut_*.extrap` — 5 cols: cm E, excitation E, cm angle, σ, S (mode 3).
- `chiSquared.out` — per-segment χ²/N and norms; last line total χ². **The
  quickest scalar check that a run succeeded.**
- `param.par` initial / `param.sav` best-fit formal params (reload as the
  external parameter file); `parameters.out` physical/observable params.
- `normalizations.out` — fitted segment norms (auto-loaded with `param.sav`).
- `param.errors`, `covariance_matrix.out` — MINOS (mode 4).
- `reactionrates.dat` (mode 5); `samples.mcmc` (mode 6).
- `intEC.dat` / `intEC.extrap` — external-capture integral caches; see the
  golden rules in SKILL.md.
