# Nuclear physics skills

Agent skills (Claude Code / Agent Skills format) for experimental nuclear physics and nuclear astrophysics, covering low-energy reaction measurements and gamma-ray spectroscopy: from raw spectra to a published paper and a talk. Each folder is one self-contained skill (`SKILL.md` plus optional `references/`, `scripts/`, `assets/`). Around them: review subagents that check results with a fresh context (`subagents/`), a hook that enforces project boundaries (`settings/`), and evaluations of how well an agent uses the skills (`evals/`).

## The chain

```
spectra ──► yield-analysis ──► peak-shape-analysis ──► target-analysis ──► azure2 (R-matrix, S-factor, rate) ──► resonance-search (level-scheme campaigns)
                                                                                      │
                                                                                      └──► reaction-network (pynucastro burns, trajectories, rate sensitivity, measurement impact)
               ▲                                                ▲
      efficiency-analysis        evaluated-nuclear-data     geant4-simulation (general Geant4: neutron counters, sources, kinematics, validation)
                                                            underground-gamma-simulation (Geant4 detector response, kinematics)
                                                            agata-simulation (AGATA Geant4, PSA emulation, summing, tracking)
                                                            delta-beta-dsam (fs lifetimes from Δβ = β_reac − β_ems)
                                                                 │
nuclear-research-project  (project layout, provenance, claims register, LaTeX report, handoff) ◄──┘
                                                                 │
     proposals: proposal-project (layout, registers, tool studies) · proposal-analysis (feasibility, design, back-tests, review cycle)
     across stages: analysis-chain (stages, gates, handoff contracts, adapters, state) · uncertainty-audit (are the errors right?)
     writing: clear-experimental-writing · methods-paper-style · proposal-style · unslop
     figures: prc-figures (PRC / ROOT-like matplotlib style, stacked spectra, heatmaps, render check)
     talks:   research-slides (built-in house layout or your own template, Manim animations, render + audit)
```

| Skill | Use it for |
|---|---|
| `yield-analysis` | Net areas, charge/live-time normalization and correlated uncertainties → excitation-curve points |
| `peak-shape-analysis` | Bin-integrated fits of asymmetric γ peaks and target energy-loss shapes |
| `efficiency-analysis` | Photopeak efficiency, IAEA NDS decay data, cascade summing corrections |
| `target-analysis` | Target profiles, stoichiometry and degradation from excitation curves; SRIM tables |
| `geant4-simulation` | General Geant4 applications: environment and datasets, simple geometries and materials, physics lists (neutron HP with thermal scattering), sources, two-body kinematics, scoring, efficiency and die-away analyses, validation ladder, tested neutron-counter template |
| `underground-gamma-simulation` | Building, extending and validating Geant4/ROOT simulations of gamma-detection setups at underground accelerator laboratories |
| `agata-simulation` | AGATA Geant4 code: custom geometries (e.g. one triplet in close geometry), external cascade events, list-mode conversion, PSA/resolution emulation, summing-in tags and OFT tracking |
| `delta-beta-dsam` | Femtosecond lifetimes with the Doppler-velocity (Δβ) DSAM method: centroids, nuisance fit, Δβ–τ calibration, sensitivity |
| `evaluated-nuclear-data` | Evaluated cross sections (ENDF/B-VIII, JEFF, JENDL, TENDL): OpenMC HDF5 or raw ENDF-6, NJOY at temperature, thermal/RI/MACS/fission-spectrum averages, library spread, MF/MT lookup, SAMMY and Ferdinand checks |
| `azure2` | AZURE2/pyazr R-matrix calculations, fits, decompositions, extrapolations, rates |
| `reaction-network` | pynucastro networks: one-zone burns at constant conditions or along trajectories, REACLIB/STARLIB/table rates (AZURE2 output), detailed-balance reverses, ²⁶Al isomer branches, Monte Carlo and OAT rate sensitivity with noise thresholds, what a measurement's precision buys, REACLIB-form fits |
| `resonance-search` | Automated, gated search for missing or misassigned resonances in a multichannel R-matrix evaluation: data audit, pattern map, window searches, structure-aware gates, merges, unattended driver |
| `analysis-chain` | Analyses that span several skills: fixed stages with gates, handoff contracts, unit/frame/correlation-preserving adapters (efficiency → yields, yields → target, tables → AZURE2), provenance sidecars, decision briefs, bounded retries, parallel independent attempts |
| `uncertainty-audit` | Whether uncertainties support the conclusion: source and correlation assessment against the code; pulls, χ², localised residual structure, held-out coverage, parameter identifiability |
| `nuclear-research-project` | Scaffolding and auditing reproducible feasibility-study projects and reports; claims register with staleness checks |
| `proposal-project` | Scaffolding and tidying grant-proposal projects: versioned drafts, number provenance, PI placeholders, decision and objection registers, and the layout and size policy of tool studies (R-matrix, Geant4, transport, MCMC) |
| `proposal-analysis` | The quantitative case of a proposal: feasibility, Bayesian design, pre-registered decision rules, power simulations, back-tests, covariances, sampling checks, simulated review |
| `clear-experimental-writing` | Experimental manuscripts, abstracts, captions, referee replies |
| `methods-paper-style` | Formalism, methods and R-matrix sections in a plain, reusable technical register |
| `proposal-style` | Proposals, grants, fellowships, beam-time requests |
| `unslop` | De-formulaic editing of any prose (explicit invocation only) |
| `prc-figures` | PRC / ROOT-like matplotlib figures: spectra, stacked components, S factors with data, heatmaps, method comparisons, annotated Geant4 renders, overlap checks |
| `research-slides` | Talks in a consistent house style, Manim animations, rendering and deck audit |

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

If a folder of the same name already exists in `~/.claude/skills`, move it aside first. Skills that drive external codes (AZURE2, Geant4, AGATA, ROOT) assume those codes are installed; point the agent at your own installation.

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
python3 analysis-chain/scripts/selftest.py
python3 uncertainty-audit/scripts/selftest.py
python3 nuclear-research-project/scripts/test_check_claims.py
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
- The writing skills contain original, general guidance; they do not reproduce text from books, papers or proposals.
- Numerical examples in the skills are synthetic or published values; they are not results to cite.

## License

MIT (see [LICENSE](LICENSE)) for the code and documentation.
