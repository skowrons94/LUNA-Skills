# Nuclear physics skills

Agent skills (Claude Code / Agent Skills format) for experimental nuclear physics and nuclear astrophysics, covering low-energy reaction measurements and gamma-ray spectroscopy: from raw spectra to a published paper and a talk. Each folder is one self-contained skill (`SKILL.md` plus optional `references/`, `scripts/`, `assets/`).

## The chain

```
spectra ──► yield-analysis ──► peak-shape-analysis ──► target-analysis ──► azure2 (R-matrix, S-factor, rate)
               ▲                                                ▲
      efficiency-analysis                                   underground-gamma-simulation (Geant4 detector response, kinematics)
                                                            agata-simulation (AGATA Geant4, PSA emulation, summing, tracking)
                                                            delta-beta-dsam (fs lifetimes from Δβ = β_reac − β_ems)
                                                                 │
nuclear-research-project  (project layout, provenance, LaTeX report, handoff) ◄──────────┘
                                                                 │
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
| `underground-gamma-simulation` | Building, extending and validating Geant4/ROOT simulations of gamma-detection setups at underground accelerator laboratories |
| `agata-simulation` | AGATA Geant4 code: custom geometries (e.g. one triplet in close geometry), external cascade events, list-mode conversion, PSA/resolution emulation, summing-in tags and OFT tracking |
| `delta-beta-dsam` | Femtosecond lifetimes with the Doppler-velocity (Δβ) DSAM method: centroids, nuisance fit, Δβ–τ calibration, sensitivity |
| `azure2` | AZURE2/pyazr R-matrix calculations, fits, decompositions, extrapolations, rates |
| `nuclear-research-project` | Scaffolding and auditing reproducible feasibility-study projects and reports |
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

If a folder of the same name already exists in `~/.claude/skills`, move it aside first. Some skills mention paths on the author's machine (`~/Desktop/...`); treat them as discovery hints and point the agent at your own installation.

## Test

Each analysis skill ships an offline demo that must print `PASS`:

```bash
python3 yield-analysis/scripts/demo.py --out /tmp/demo-yield
python3 peak-shape-analysis/scripts/demo.py --out /tmp/demo-peak
python3 target-analysis/scripts/demo.py --out /tmp/demo-target
python3 efficiency-analysis/scripts/demo.py --out /tmp/demo-eff
python3 efficiency-analysis/scripts/demo_cascade.py --out /tmp/demo-cascade
python3 underground-gamma-simulation/scripts/test_physics_checks.py && python3 underground-gamma-simulation/scripts/test_helpers.py
python3 agata-simulation/scripts/test_agata_lm.py
python3 delta-beta-dsam/scripts/selftest.py
python3 prc-figures/scripts/demo.py --out /tmp/demo-prc
python3 research-slides/scripts/demo_deck.py --out /tmp/demo-deck
```

Python 3 (tested with 3.12) with NumPy, SciPy, Matplotlib; `uproot` for ROOT input; `python-pptx` for decks; `manim`, `ffmpeg` and `pdftoppm` for animations and rendering. See each skill's `requirements.txt`.

## Notes

- `research-slides` ships no logos or institutional templates. It draws its own house layout; pass your own template or logo files only where you are entitled to use them.
- The writing skills contain original, general guidance; they do not reproduce text from books, papers or proposals.
- Numerical examples in the skills are synthetic or published values; they are not results to cite.

## License

MIT (see [LICENSE](LICENSE)) for the code and documentation.
