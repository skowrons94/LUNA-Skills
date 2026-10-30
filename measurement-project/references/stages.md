# Analysis stages of a measurement

The stages run in the order of the physics: a quantity is used only after the stage that determines it has passed its
gate. Each folder corresponds to a stage of `analysis-chain`, is worked by one or two stage skills, and writes its
results in the format of the contract the next stage reads, so that the chain's checks (`contracts.py`) and adapters
(`adapters.py`) work on the project without changes. The state of all stages is kept in `CHAIN.md` at the project root
(template in `analysis-chain/assets/CHAIN.md`); decisions taken at a gate go to `DECISIONS.md`.

| Folder | analysis-chain stage | Skills | Results read downstream | Contract |
|---|---|---|---|---|
| `00_audit` | 0 Data audit | `data-auditor` subagent, `yield-analysis` (run checks) | `results/run_table.csv` (logbook.csv plus flags) | — |
| `01_beam` | 0–1 (normalisation inputs) | `yield-analysis` (charge, live time), `target-analysis` (resonance energies) | `results/beam_energy.json`, `results/charge_checks.csv` | — |
| `02_calibration` | 1 (energy scale) | `peak-shape-analysis`, `yield-analysis` | `results/calibration_<period>.json` per channel | `spectrum-csv` for exported spectra |
| `03_background` | 1 (backgrounds) | `yield-analysis`, `peak-shape-analysis`, `underground-gamma-simulation` | `results/room_rates.csv`, `results/contaminant_lines.csv` | — |
| `04_efficiency` | 2 Efficiency | `efficiency-analysis`, `underground-gamma-simulation`, `agata-simulation` | `results/result.json` | `efficiency-curve` |
| `05_target` | 3 Target, effective energy | `target-analysis`, `peak-shape-analysis` | `results/target_profiles.json`, `results/run_normalisation.csv` | `excitation-curve` in |
| `06_yield` | 1 Yields | `yield-analysis`, `peak-shape-analysis` | `results/yields.csv`, `covariance.csv`, `result.json` | `yield-table` |
| `07_sfactor` | 4 Cross section, S factor | `yield-analysis` (normalisation), `uncertainty-audit` | `results/sfactor.csv`, `results/azure/*.dat` | `azure-dat` |
| `08_rmatrix` | 4–5 R-matrix, extrapolation | `r-matrix`, `resonance-search`, `rmatrix-posterior` | `results/extrap.dat`, `results/rate.csv` | `rate-table` out |
| `09_rate` | 5b–5c Astrophysical impact | `reaction-network`, `stellar-evolution`, `big-bang-nucleosynthesis` | network and model outputs with manifests | `rate-table`, `thermo-trajectory` in |
| `report/`, `slides/` | 6 Review, 7 Write-up | `physics-referee`, `clear-experimental-writing`, `prc-figures`, `research-slides` | — | claims register |

The folder numbers follow the order in which the quantities are needed, which differs from the numbering of
`analysis-chain` in one place: yields (chain stage 1) are computed after efficiency and target (folders 04, 05),
because the normalisation of a long run depends on both. Each stage README records its gate, the gate of the
corresponding chain stage, judged by a reviewer other than the agent that produced the result.

## 00_audit

The audit classifies every run (purpose, target, geometry, beam), checks that times and charges are consistent between
the file headers and the logbooks, finds duplicated, summed or partial spectra, and lists runs that cannot be used.
It produces `run_table.csv`, the logbook with flags, and its gate is that every blocking issue is resolved or written
into ASSUMPTIONS.md. Summed spectra counted next to their parts, a dead-time field that holds the live fraction and a
charge integrator that read double in one period were all found at this stage in past analyses.

## 01_beam

Beam energy comes from the accelerator calibration (resonances, (p,γ) thresholds) and is written as a formula with
its validity range and uncertainty; nominal terminal voltages are never used as beam energies. Charge integration is
checked for its unit, its offset and its stability (current against time, yield per coulomb on a reference), and the
dead-time or live-time convention of the DAQ is fixed here. A run whose current is far below its neighbours with a
yield per coulomb far above is an under-recorded charge.

## 02_calibration

Energy calibration per channel and period from lines in the data (room background, beam-induced lines, resonance
gammas), validated on lines not used in the fit, and the resolution as a function of energy. A drifting calibration
is calibrated per run or per group with the anchors that are present in every run; a single global calibration
smears summed peaks.

## 03_background

Two kinds of background are separated because they scale differently. Room background (natural radioactivity, cosmic
muons, intrinsic activity) scales with live time and is measured with beam off; beam-induced lines (11B, 18O, 19F,
13C, 15N contaminants) scale with charge and with the contaminant content, which can change in time. Expressed per
reaction, room background varies with the beam current, so long runs at different currents have different
signal-to-background ratios. The stage delivers line lists with their origin and the room rates per channel.

## 04_efficiency

Full-energy and total efficiency for the real geometry, with summing-in and summing-out and the angular correlations
of the cascades, from sources and from a resonance with known branchings, or from a validated simulation. The curve is
written as an `efficiency-curve` with its covariance and validity range. A simulated efficiency (SimLUNA, Geant4) is
validated against at least one measured quantity of the same setup before it is used.

## 05_target

Target profiles from the resonance scans and checks, for every target and in time: front-edge position (a surface
layer shifts it), plateau height (stoichiometry and loss of the active nucleus), back edge (thickness and thinning),
and a depth gradient where the plateau is not flat. Checks taken at one energy are plateau checks only if the profile
shows that the energy is on the plateau at that time. The stage delivers, for every long run, the expected
resonance-equivalent reactions per coulomb with its uncertainty and the layer the run actually saw, which the yield
and S-factor stages use. The scatter of the checks about the profile model is the per-point normalisation
uncertainty; in the 2001–2002 14N(p,γ) data it did not average down over the runs of a point.

## 06_yield

Net areas with reviewed ROI overlays or line-shape fits, normalised to charge and live time, and the run normalisation
from 05. Negative net areas are kept, window stability is tested, and every shared systematic (charge, efficiency,
stoichiometry) is named and kept out of the per-point errors. The result is a `yield-table`.

## 07_sfactor

Cross sections or S factors from the yields and the target layer, with an effective energy whose definition is stated.
For thick targets measured relative to a model shape, the yield-weighted mean energy is exact to first order in a
shape error and independent of the layer's back part; the self-consistent energy of Filippone (Lemut, EPJA 36 (2008)
233) suits thin targets. The uncertainty budget keeps statistical, independent normalisation and shared systematic
parts separate, and comparisons with published data are made in units of a common model shape, matching points from
the same runs by beam energy. Output in `azure-dat` format for 08.

## 08_rmatrix and 09_rate

The R-matrix stage reads 07 and external data with their provenance and normalisation priors equal to the quoted
systematics; the rate and impact stages read the rate table. Both follow their skills; this layout only fixes where
their inputs and results live.

## Review and write-up

The report in `report/` takes every number from a generated table (`tools/make_report_tables.py`), and the claims
register (`CLAIMS.toml`, checked with `nuclear-research-project/scripts/check_claims.py`) ties quoted numbers to result
files, so that a rerun upstream marks the report as stale. Slides in `slides/` are built by a script from the same
figures.
