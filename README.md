# Nuclear physics skills

Agent skills (Claude Code / Agent Skills format) for experimental nuclear physics and nuclear astrophysics. Together they cover the path of a low-energy reaction measurement, from the raw spectra through the cross section and the reaction rate to its consequences in stars and in the early Universe, and finally to the paper and the talk. Each folder is one self-contained skill (`SKILL.md` plus optional `references/`, `scripts/`, `assets/`). Around them are review subagents that check results with a fresh context (`subagents/`), a hook that enforces project boundaries (`settings/`), and evaluations of how well an agent uses the skills (`evals/`).

## The path

The skills are grouped in seven sections that follow the order in which a thesis or a measurement campaign usually proceeds. Each `SKILL.md` opens with the question it answers and a short "Where this fits" block that names the skill its inputs come from, the skill its results go to, and what checks them. Handoffs between stages are files with a checked format (the contracts of `analysis-chain`: `spectrum-csv`, `yield-table`, `efficiency-curve`, `excitation-curve`, `azure-dat`, `rate-table`, `thermo-trajectory`), so that units, frames and shared uncertainties survive the step from one skill to the next.

```
0 Running a project ─ layout, claims register, staged chains with gates, uncertainty audit, reviewers
        │ (applies to every stage below)
1 In the lab ──────────► 3 From cross section to rate ──────────► 5 In the cosmos ──────► 6 Telling people
  spectra → yields,         R-matrix fits, resonance search,        networks, BBN, MESA,     figures, papers,
  efficiency, target,       extrapolation, rate tables              stellar observables      talks, proposals
  lifetimes                       ▲
        ▲                          │
2 Simulating the experiment      4 The nucleus behind the rate
  Geant4, AGATA, evaluated data    shell model, cluster models, mirror nuclei
```

A student new to the field can read the sections in this order. The first exercise in each analysis skill is its offline demo or selftest (see [Test](#test)), and the graded tasks in `evals/` are worked problems with a known answer and a built-in trap. How the skills are written is described in [STYLE.md](STYLE.md).

### 0. Running a project

How is the work kept reproducible, staged and checked? Read this first; every other section uses it.

| Skill | Use it for |
|---|---|
| `measurement-project` | Layout and audit of a measurement analysis: raw data and per-run ROOT files, generated `logbook.csv`, stage folders from audit, beam, calibration, background, efficiency and target to yield, S factor, R-matrix and rate (mapped onto the `analysis-chain` stages and contracts), registers (HANDOFF, PROBLEMS, LITERATURE, DECISIONS), report and slides |
| `nuclear-research-project` | Scaffolding and auditing reproducible feasibility-study projects and reports; claims register with staleness checks |
| `analysis-chain` | Analyses that span several skills: fixed stages with gates, handoff contracts, unit/frame/correlation-preserving adapters (efficiency → yields, yields → target, tables → AZURE2), provenance sidecars, decision briefs, bounded retries, parallel independent attempts |
| `uncertainty-audit` | Whether uncertainties support the conclusion: source and correlation assessment against the code; pulls, χ², localised residual structure, held-out coverage, parameter identifiability |

### 1. In the lab

What did the detector record, and what yield, efficiency, target and lifetime follow from it?

| Skill | Use it for |
|---|---|
| `yield-analysis` | Net areas, charge/live-time normalization and correlated uncertainties → excitation-curve points |
| `peak-shape-analysis` | Bin-integrated fits of asymmetric γ peaks and target energy-loss shapes |
| `efficiency-analysis` | Photopeak efficiency, IAEA NDS decay data, cascade summing corrections |
| `target-analysis` | Target profiles, stoichiometry and degradation from excitation curves; SRIM tables |
| `delta-beta-dsam` | Femtosecond lifetimes with the Doppler-velocity (Δβ) DSAM method: centroids, nuisance fit, Δβ–τ calibration, sensitivity |

### 2. Simulating the experiment

What should the detector record, and which evaluated data describe the reaction?

| Skill | Use it for |
|---|---|
| `geant4-simulation` | General Geant4 applications: environment and datasets, simple geometries and materials, physics lists (neutron HP with thermal scattering), sources, two-body kinematics, scoring, efficiency and die-away analyses, validation ladder, tested neutron-counter template |
| `underground-gamma-simulation` | Building, extending and validating Geant4/ROOT simulations of gamma-detection setups at underground accelerator laboratories |
| `agata-simulation` | AGATA Geant4 code: custom geometries (e.g. one triplet in close geometry), external cascade events, list-mode conversion, PSA/resolution emulation, summing-in tags and OFT tracking |
| `evaluated-nuclear-data` | Evaluated cross sections (ENDF/B-VIII, JEFF, JENDL, TENDL): OpenMC HDF5 or raw ENDF-6, NJOY at temperature, thermal/RI/MACS/fission-spectrum averages, library spread, MF/MT lookup, SAMMY and Ferdinand checks |

### 3. From cross section to rate

Which level scheme describes the data, and what is the rate at stellar energies?

| Skill | Use it for |
|---|---|
| `r-matrix` | R-matrix evaluations with AZURE2/pyazr (charged particles, capture, rates) or SAMMY (neutron resonances, broadening, Bayes, ENDF): choice of code, fits, decompositions, extrapolations, conversions through ENDF, and whether a fit is physical (Park norm and saturated levels, transformability, covariance against profile scans) |
| `rmatrix-posterior` | Posterior sampling of AZURE2 fits: width, transformability and Park-norm priors that make the fit physical, exact-Hessian whitening at the MAP, Laplace and importance-sampling checks, checkpointed NUTS against an emcee baseline, derived S(0) |
| `resonance-search` | Automated, gated search for missing or misassigned resonances in a multichannel R-matrix evaluation: data audit, pattern map, window searches, structure-aware gates, merges, unattended driver |
| `effective-range` | Coulomb-modified effective-range analysis of phase shifts (data, R-matrix eigenphases, models), fit-window systematics, the charged-hard-sphere reference for a large a0 and the equivalent core radius, the θ² one R-matrix level needs for a given scattering length |

### 4. The nucleus behind the rate

What structure explains a level, a width or an ANC, and is it physical?

| Skill | Use it for |
|---|---|
| `shell-model` | KSHELL for light nuclei: p and p-sd interactions, ħω truncations, Lawson term and spurious states, occupancies, intruder-band calibration on neighbours referred to thresholds, identification of R-matrix levels; spectroscopic amplitudes from a CI calculation with cluster channels turned into R-matrix widths (as-built SF, μ_Q renormalization, sum rule) |
| `cluster-potential` | Two-body cluster models with Pauli-forbidden states: depths on known levels, bound states, ANCs, phase shifts, resonances, penetrabilities and θ² of a width, norm-kernel μ_N (a normalization, not a force), parity-dependent potentials, the orthogonality-condition (Pauli-only) test |
| `microscopic-cluster` | Antisymmetrized GCM/RGM of 0s clusters with the Minnesota force and the microscopic R-matrix: one exchange parameter on the other parity, oscillator-width scan, parameter-free phase shifts and scattering lengths |
| `mirror-nucleus` | Charge-symmetry tests: mirror spectra with one potential, ANC ratios over geometries, widths at a common radius, Thomas–Ehrman shifts, free-versus-constrained mirror refits |

### 5. In the cosmos

What does the rate change in the Big Bang, in a star, and in what astronomers observe?

| Skill | Use it for |
|---|---|
| `reaction-network` | pynucastro networks: one-zone burns at constant conditions or along trajectories, REACLIB/STARLIB/table rates (AZURE2 output), detailed-balance reverses, ²⁶Al isomer branches, Monte Carlo and OAT rate sensitivity with noise thresholds, what a measurement's precision buys, REACLIB-form fits |
| `big-bang-nucleosynthesis` | AlterBBN built reproducibly from the unmodified tarball with a small patch: any nuclear rate replaced by a table (rate + factor uncertainty), JSON driver, reproducible Monte Carlo, precision override for convergence tests; checks (patch identity, table round trip, solver convergence), Omega_b h^2 from D/H, known code defects |
| `stellar-evolution` | MESA without admin rights (SDK relocation, macOS SDKROOT pitfall), test-suite templates, rate factors and dense rate tables with run-local caches, run driver with manifests, run checks, solar neutrino fluxes from per-cell rates, centre trajectories and compositions for networks, resolution and physics-degeneracy checks |
| `stellar-observables` | Physics of surface, wind and grain observables a rate can change (12C/13C, 14N/15N, O, Mg and Al isotopes, Li, Na, s-process): which burning sets each, which phase exposes it (dredge-ups, extra mixing, HBB, winds), which levers are larger than the rate, how to match models with observed stars and presolar grains; a general method plus a worked 12C/13C example |

### 6. Telling people

How are the results shown and written: figures, papers, talks and proposals?

| Skill | Use it for |
|---|---|
| `prc-figures` | PRC / ROOT-like matplotlib figures: spectra, stacked components, S factors with data, heatmaps, method comparisons, annotated Geant4 renders, overlap checks |
| `research-slides` | Talks in a consistent house style, Manim animations, rendering and deck audit |
| `clear-experimental-writing` | Experimental manuscripts, abstracts, captions, referee replies |
| `methods-paper-style` | Formalism, methods and R-matrix sections in a plain, reusable technical register |
| `proposal-style` | Proposals, grants, fellowships, beam-time requests |
| `unslop` | De-formulaic editing of any prose (explicit invocation only) |
| `proposal-project` | Scaffolding and tidying grant-proposal projects: versioned drafts, number provenance, PI placeholders, decision and objection registers, and the layout and size policy of tool studies (R-matrix, Geant4, transport, MCMC) |
| `proposal-analysis` | The quantitative case of a proposal: feasibility, Bayesian design, pre-registered decision rules, power simulations, back-tests, covariances, sampling checks, simulated review |

## Install

Claude Code loads personal skills from `~/.claude/skills/<name>/`. Clone the repository and link the skills you want:

```bash
git clone https://github.com/skowrons94/LUNA-Skills.git && cd LUNA-Skills
for s in */; do [ -f "$s/SKILL.md" ] && ln -sfn "$PWD/${s%/}" ~/.claude/skills/"${s%/}"; done
```

Subagents and the project guard:

```bash
mkdir -p ~/.claude/agents
for a in subagents/*.md; do [ "$(basename "$a")" = README.md ] || ln -sfn "$PWD/$a" ~/.claude/agents/; done
python3 settings/install_guard.py /path/to/analysis-project
```

Codex and OpenCode read the same `SKILL.md` format from `.agents/skills/` (Codex also `.codex/skills/`; OpenCode also `.claude/skills/`); link the folders there in the same way and check your tool's documentation for its user-level location. Each skill's `agents/openai.yaml` holds its Codex display metadata.

If a folder of the same name already exists in `~/.claude/skills`, move it aside first. Skills that drive external codes (AZURE2, Geant4, AGATA, ROOT, MESA, pynucastro) assume those codes are installed; point the agent at your own installation.

## Test

Each analysis skill ships an offline demo that must print `PASS`:

```bash
python3 yield-analysis/scripts/demo.py --out /tmp/demo-yield
python3 peak-shape-analysis/scripts/demo.py --out /tmp/demo-peak
python3 target-analysis/scripts/demo.py --out /tmp/demo-target
python3 efficiency-analysis/scripts/demo.py --out /tmp/demo-eff
python3 efficiency-analysis/scripts/demo_cascade.py --out /tmp/demo-cascade
python3 evaluated-nuclear-data/scripts/selftest.py
python3 underground-gamma-simulation/scripts/test_physics_checks.py && python3 underground-gamma-simulation/scripts/test_helpers.py
python3 agata-simulation/scripts/test_agata_lm.py
python3 geant4-simulation/scripts/selftest.py
python3 delta-beta-dsam/scripts/selftest.py
python3 reaction-network/scripts/selftest.py     # needs pynucastro; uses $NUCLEAR_DATA_DIR/STARLIB if present
python3 stellar-evolution/scripts/selftest.py    # no MESA needed
python3 shell-model/scripts/selftest.py          # no KSHELL needed
python3 cluster-potential/scripts/selftest.py
python3 effective-range/scripts/selftest.py
python3 microscopic-cluster/scripts/selftest.py  # --full adds the end-to-end 7Be check (~1 min)
python3 mirror-nucleus/scripts/selftest.py       # needs cluster-potential next to it
python3 analysis-chain/scripts/selftest.py
python3 uncertainty-audit/scripts/selftest.py
python3 nuclear-research-project/scripts/test_check_claims.py
python3 measurement-project/scripts/selftest.py
python3 settings/test_guard.py
python3 evals/run_evals.py selftest
python3 proposal-project/scripts/test_create_proposal_project.py
python3 proposal-analysis/scripts/selftest.py
python3 prc-figures/scripts/demo.py --out /tmp/demo-prc
python3 research-slides/scripts/demo_deck.py --out /tmp/demo-deck
```

`python3 geant4-simulation/scripts/test_template.py --build-dir DIR --jobs N` additionally builds and smoke-tests the Geant4 template (needs a Geant4 installation).

The tests above check the scripts. `evals/` checks the agent: whether a request loads the right skill, and whether graded tasks with known answers and built-in traps (live fraction stored as `deadTime`, charge in µC, a doublet, a negative net area, undecayed source activities, raw data edited in place) are solved. These runs call Claude Code headless and cost money; see [evals/README.md](evals/README.md).

## Working with agents

- **Separate producing from judging.** `physics-referee`, `data-auditor` and `citation-checker` run read-only with a fresh context. Give them files and the claim, not the reasoning.
- **Fixed stages, checked handoffs.** `analysis-chain` runs multi-stage work as a resumable state machine with gates; agents choose methods inside a stage, not the order of stages or what counts as done.
- **Numbers trace to files.** The claims register flags quoted values whose evidence changed or that depend on a challenged claim.
- **Boundaries are enforced, not only stated.** The project guard denies edits to raw data and asks before anything leaves the machine.
- **Skill edits are method changes.** Run the evaluations before relying on an edited skill; grow them from real failures.

Python 3 (tested with 3.12) with NumPy, SciPy, Matplotlib; `uproot` for ROOT input; `python-pptx` for decks; `manim`, `ffmpeg` and `pdftoppm` for animations and rendering. See each skill's `requirements.txt`.

## Notes

- `research-slides` ships no logos or institutional templates. It draws its own house layout; pass your own template or logo files only where you are entitled to use them.
- The writing skills contain original, general guidance; they do not reproduce text from books, papers or proposals. `STYLE.md` quotes single sentences from the owner's papers and three methods papers as evidence for its measurements, with their references.
- Numerical examples in the skills are synthetic or published values; they are not results to cite.

## License

MIT (see [LICENSE](LICENSE)) for the code and documentation.
