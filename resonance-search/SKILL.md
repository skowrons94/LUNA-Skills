---
name: resonance-search
description: Run an automated, gated search for missing, surplus or misassigned resonances in a multichannel R-matrix evaluation (AZURE2/pyazr) fitted to many excitation functions: data audit, pattern map, window searches that add, delete, re-assign or move levels, acceptance gates, merges and an unattended driver loop. Use when a level scheme must be extended or repaired against dense angular or excitation-function data (elastic scattering, (p,α), (α,α), THM), when χ² stalls far above 1, or when the user asks for "automatic resonance fits"; single AZURE2 runs, fits or extrapolations use `azure2`.
---

# Automated resonance search in R-matrix evaluations

A multichannel R-matrix evaluation fitted to many excitation functions often stalls with χ² far above 1, because levels are missing, surplus or assigned the wrong J^π. This skill searches for those levels automatically and with gates. The aim is a level scheme that reproduces the resonance structure of every data set with physically admissible parameters, not the lowest χ². A model can lower χ² by smoothing real resonances away or by oscillating between data points, and neither is a better evaluation. Every accepted change must therefore improve χ² and also keep the structure, the physics limits and the other data sets intact. You need an AZURE2 evaluation driven through pyazr, the data sets with their papers, and the published uncertainties. You get the best evaluation file and its folded version, a hypothesis ledger of every tested change, a campaign log, figures and a status report.

## Where this fits

- Comes from: an evaluation built and run with `azure2`, on data in the `azure-dat` contract; the `data-auditor` subagent for the first data audit.
- Goes to: `azure2` for single calculations, fits, decompositions, extrapolations and rates of the consolidated model; project layout, logs and reports follow `nuclear-research-project`.
- Checked by: the acceptance gate and the hypothesis ledger of step 3, the reload test of the written file, and `physics-referee` or `uncertainty-audit` before a level scheme is quoted.

## Rules and their reasons

1. Data are evidence. Published files are never edited; masked, cut or re-extracted data are new files in `data/processed/`, with the reason recorded. A point is excluded only for a documented experimental reason, such as a transcription error, a contaminating reaction or an energy range disowned by the authors, and never because the model misses it.
2. χ² is quoted against the published uncertainties. If the point-to-point scatter exceeds them, the report says so and gives the implied χ²/N floor. Errors are not inflated to reach a target, because the χ² would then no longer measure the model against the experiment.
3. AZURE2 reads LAB energies and angles and compares the model with the data in the CENTRE OF MASS, as model/n − d_cm. Plots and audits are made in the same frame, with the data multiplied by n, so that the residuals seen are those the fit minimises.
4. The parametrisation is stated with every result. With the Brune alternative parametrisation, energies and widths are observed values.
5. Levels inside the data range must have θ² ≤ 1 in every channel. Background poles above the data range may exceed 1, up to a cap that is stated with the result. The reduced width can be expressed in two forms, and the report says which one a bound uses. The formal form, γ²/(ħ²/μa²), is the natural bound for the fit. The observed form is Γ_c/Γ_W, with Γ_W = 2P_l(E_r)ħ²/(μa²). The two differ by the level-shift factor, which is 70+ for distant poles, so a pole within the bound in one form can be far outside it in the other. We therefore bound the poles in the formal form and audit them on the observed θ².
6. No level may be narrower than the data can resolve. The c.m. total width is compared with max(experimental resolution [beam spread ⊕ target thickness], energy step) at that energy.
7. The allowed J^π follow from the channels. Two 0⁺ particles in their ground states (α₀+²⁰Ne, ¹²C+¹²C g.s.) allow natural parity only. Exits to excited states (α₁, p₁) and channels with non-zero spin (p+²³Na 3/2⁺) also allow unnatural parity. Identical 0⁺ bosons in the same state allow even L only, so even J⁺. Their cross sections carry 1 + δ₁₂ = 2, and the build in use must be checked for which channels it applies this factor to, because some builds apply it to elastic only.
8. The normalisation of a data set may float only with a prior whose width equals the stated systematic uncertainty of that data set. The fitted normalisation is written to the segment line, because a generic write-back does not keep it. A fit through the pyazr residual API does not include the prior, so the term ((n−1)/σ_sys)² is added explicitly. Data on an arbitrary scale (THM, unpublished yields) get an unconstrained or profiled normalisation and are plotted scaled.
9. There are no hidden degrees of freedom: no per-segment energy shifts or extra error terms unless the user asks for them. Any that are used are reported with the result.
10. Channel radii are stated per partition, scanned (χ² against a) and kept the same in evaluations that will be combined, because reduced widths are comparable only at the same radius.

## Method

The search alternates between finding unreproduced structure and testing local changes of the level scheme against it. Each change is tested in a window, accepted only through a gate, merged with the others and refitted, and the loop repeats until it stops gaining.

### 0. Data audit (before any fit)

Delegate a first pass to the `data-auditor` subagent if it is installed, since it is read-only and starts from a fresh context, then resolve its findings. The following items are the minimum.

- Cross-check repeated angles and energies between files; identical values at the same energy in two angles are transcription copies.
- Read the paper of every data set for energy ranges with overlapping reactions or contamination, for the resolution (beam spread, target thickness, step size) and for the energy definition; effective E₀ − ΔE/2 data must not be target-integrated again.
- Re-extract digitised data from vector graphics when possible, with the exact calibration from the tick marks, and compare scale and error bars with the paper.
- Compare overlapping data sets after smoothing the sharper one to the coarser resolution, and flag runs of consecutive points that disagree in one direction.

### 1. Baseline and gate metrics

Score each data set by χ²/N. For each angle, also compute R = rms(Δ²model / y_data) / rms(Δ²data / y_data) and the correlation of the two second differences. Both terms are divided by the data value y_data, with the model rescaled to the data per angle. Never divide by the model's own value, because one interference zero then dominates the angle. Record θ²_max for levels and poles, the count of unresolvable levels and the normalisations.

### 2. Pattern map

For each angle, find the significant extrema of ln(data), with prominence > max(0.1, 3σ/y), and of ln(model) on the same grid, and match them within two grid steps. Cluster the unmatched data features across angles. A feature seen at ≥ 5 angles (≥ 2 for sparse data) is a missing or misassigned level, and unmatched model features across angles are surplus structure. Rank the clusters by the local χ².

### 3. Window search

Each target gets a window of ±50–70 keV; the windows do not overlap and run in parallel.

The candidates are: add a level (each allowed J^π on a grid), delete, re-assign J^π, move, or revive a dormant level. All candidates are screened with one Jacobian (linearised gain), the best few are kept, each is refitted locally (window ± 150 keV), and the best that passes the gate is taken. The screen targets the data family that shows the feature and allows the parities that family permits.

The gate requires that the total χ² decreases, that no data set worsens beyond a small tolerance, that the structure amplitude does not move away from its target and the correlation does not drop, that the θ² limits hold, and that the count of unresolvable levels does not grow. An added level must also beat its parameter cost, Δχ² > 2k for k new parameters (AIC), or pass an F-test. Δχ² is logged for every level, and each window gets two rounds.

Every tested change, accepted or not, is appended to the hypothesis ledger `hypotheses.csv`, with the columns `pass, window_MeV, operation (add/delete/reassign/move), J^π, channel, E_x, k, Δχ²_total, Δχ² per data set (worst), AIC or F, gate failed, reason, status (accepted/rejected/deferred), fit files`. A rejection without the failed gate and the numbers is not recorded.

### 4. Merge

Apply all accepted window operations to the current best, transplant the fitted widths of the windows, and refit the union of the windows jointly in chunks. The gate is scored after each chunk and the best passing state is kept. Before merging, drop any added level narrower than the resolution limit and any duplicate of a level that a neighbouring window added at the shared edge.

### 5. Loop

Repeat steps 2–4 automatically. The loop skips hypotheses already in the ledger with the same parameters, regions rejected in the last passes, and a documented blacklist of regions where every change has cost another data set. It stops after two passes that gain less than a set threshold. Passes alternate between the data families, so that the weaker data are not swamped.

### 6. Consolidation and report

Gaussian convolution (beam spread, data at an effective energy) and target integration (thick targets with stopping powers, `<targetInt>`) are different corrections, and both are never applied to the same data. Measure each on and off at fixed parameters; if it changes χ² little, switch it on only for the final fit, because it multiplies the cost of every evaluation. The report gives:

- χ²/N per data set against the published errors;
- the normalisations, and the excluded data with the reason for each;
- per level: E_x, J^π, observed partial widths Γ_c and θ²_c (ANCs for sub-threshold levels);
- uncertainties from the Hessian/MINOS, with MCMC for the reported model;
- the comparison with ENSDF and other compilations, flagging every J^π that differs from previous assignments and the data that drive it;
- the census of states per J^π constrained by each data set.

## Pitfalls

Level energies are fitted only with bounds that keep ≥ 1 keV from every same-J^π level, live or dormant. AZURE2 merges coincident same-J^π levels on reload, and the saved file then no longer reproduces the fit. Always reload the written file and compare χ².

The pole threshold of the fit library must match where the background poles are. Otherwise the poles are bounded as ordinary levels (θ² ≤ 1) and the approved cap never applies.

When segments cut a data file in the middle, energies and data are taken from the engine (`m.energies`, `m.cross`), never from the first n rows of the file.

Gates, screens and pattern maps share one grouping function for the data families. A copy elsewhere silently classifies new data sets wrongly.

The operation journals of each window must start fresh each run, because reused window tags otherwise re-apply old operations at the next merge. Two merges that write the same scratch model corrupt each other, so only one merge runs at a time.

The memory of folded fits grows with points × threads × parameters; reduce the threads, not the points. AZURE2's repeated warnings are filtered at the source, because a full disk stops every tool.

`pgrep -f pattern` inside a shell whose command line contains the pattern matches itself; use `[p]attern`.

Identical-particle factors and THM options differ between AZURE2 branches, so the build is checked and the plots are made with the same build that fitted.

Local-data windows, with screening and trial fits on the data within the window +- ~0.25 MeV, are ~8x faster, but widths fitted locally damage far data. The accepted variant is therefore polished on ALL data, once more for near misses, and gated on all data; locally the gate uses only the total chi^2.

Normalisation priors must be centred on 1, the experimental value, never on the norm currently in the file. Re-centring at every refit lets the norms random-walk far outside their errors.

When two evaluations are merged, EVERY decay channel of the ported levels is carried over, including channels no data set measures. Dropping them changes the total widths of the levels and every observed channel. Prove that the port is lossless, with the same chi^2 at the radii of the source, before fitting.

Channel radii are changed in steps with a refit at each (radius continuation), because a jump leaves the fit far from any minimum.

It matters which Jacobian rows are analytic. Finite-differenced rows, e.g. THM/HOES observables in some AZURE2 versions, cost two evaluations per FREE parameter of the session, not per fitted column. Fix everything outside the fitted block in the file, or add the analytic adjoint.

Agents and long runs are launched detached with a PID file. Never kill a PID you did not write, and check for a live copy before starting another.

## What to deliver

- The evaluation file of the best model and its folded (reported) version.
- A campaign log with every pass, every accepted and rejected change and every data decision, and the hypothesis ledger, so that a later campaign or referee can see what was tried and why it failed.
- Figures: data and fit on a common E_x axis (PRC style), proton/alpha excitation functions, the census of constrained states per J^π, and the states shared between evaluations.
- A status report with per-data-set χ²/N, physics checks and limitations.
