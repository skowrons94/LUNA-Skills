---
name: azure2
description: Run AZURE2 R-matrix evaluations of reaction and scattering data from the CLI or from Python via pyazr: calculate cross sections and chi-squared, fit levels and widths, add or remove levels, decompose a cross section into level, interference and external contributions, extrapolate S-factors, compute reaction rates. Use whenever a task involves an .azr project file, AZURE2 levels, channels or segments, R-matrix fitting, resonance significance tests or the o17_guardo (THM) example; automated, gated searches for missing or misassigned levels are `resonance-search`.
---

# Running AZURE2 evaluations

An R-matrix evaluation turns measured cross sections, scattering data and S factors into a level scheme of the compound nucleus, and through it into an S factor at stellar energies and a reaction rate. AZURE2 is a multi-channel, multi-level R-matrix code that does this; this skill explains how to run it headless, how to fit, edit and decompose a model, and what goes wrong. You need AZURE2 with its pyazr package and an evaluation driven by a single `.azr` project file, which describes the compound nucleus, the particle pairs, the levels and channels, and the data segments. You get χ² per segment, fitted parameters, extrapolated cross sections or S factors, decompositions and reaction rates, all in the centre-of-mass frame.

## Where this fits

- Comes from: `yield-analysis` and cross-section tables through the `to-azure` adapter of `analysis-chain` (contract `azure-dat`); effective energies and target thickness from `target-analysis`; lifetimes and widths from `delta-beta-dsam`; the structure behind a level or width from `shell-model`, `cluster-potential`, `microscopic-cluster` and `mirror-nucleus`, and scattering lengths from `effective-range`; repaired level schemes from `resonance-search`; evaluated data to compare with from `evaluated-nuclear-data`; the reactions that matter most, from the sensitivity runs of `reaction-network`.
- Goes to: `reaction-network` (contract `rate-table`, converted with `rates.py from-azure`) and `stellar-evolution`; cross sections for `target-analysis`; phase-shift grids for `effective-range`; fits to compare with in `cluster-potential`, `microscopic-cluster` and `mirror-nucleus`; repairs of the level scheme against many data sets in `resonance-search`.
- Checked by: the run checks in "Verifying a run", and `uncertainty-audit` or `physics-referee` before a fit, S factor or rate is quoted.

## Two ways to run it

AZURE2 runs headless in two ways, the interactive CLI (`--no-gui`) and the pyazr Python API. The CLI suits a one-shot calculate, fit, extrapolate or rate run that writes the standard output files. We use pyazr for all evaluation work: χ², parameter scans, level add/remove tests, cross-section decomposition, custom fitters and samplers.

The binary is on `$PATH` as `AZURE2`, and also at `build/src/AZURE2` in the source repo. pyazr resolves it via `$AZURE2_BINARY` → `<repo>/build/src/AZURE2` → `$PATH`, so `binary=` is usually unnecessary. The two copies can drift, because `/usr/local/bin/AZURE2` is a copy, not a symlink, and a `make AZURE2` in the source repo does not reach it. After every rebuild, therefore, run `sudo cp build/src/AZURE2 /usr/local/bin/` or export `$AZURE2_BINARY`. AZURE2 must be installed with its `pyazr/` package, v2.3.0 or later, at the source repo root. pyazr is often mirrored into evaluation directories, so `from pyazr import ...` works when cwd is either.

The full reference documentation is in `docs/_build/html/_sources/`: `reference/` covers command_line, data_formats and output_files, and `user_guide/` covers levels_channels, segments, particle_pairs, fitting and mcmc. The worked example is `examples/o17_guardo/`.

## Rules and their reasons

1. The input is in the LAB frame with forward kinematics, the light particle being the projectile, while all output files and API results are in the CENTER-OF-MASS frame. The two are never mixed. A c.m. energy given where a lab energy is expected is wrong by the mass factor, and the extrapolation grids of the older 7Be scripts predate this finding ([scripts-and-examples.md](references/scripts-and-examples.md)). The rule includes `add_extrapolation(e_min, e_max, e_step)`, whose arguments are lab energies (multiply c.m. by `(m_beam + m_target)/m_target`), while the energies that come back from `calculate_energies` are c.m.
2. Always run from the directory that contains the `.azr` file, because the `.azr` stores `output/`, `checks/` and data paths relative to itself. pyazr does this for you via `cwd=`, which defaults to the directory of the `.azr`.
3. The `output/` directory must exist, since AZURE2 writes its results there.
4. Delete `output/intEC.extrap` whenever the `<segmentsTest>` grid changes. AZURE2 caches the external-capture integrals in that file and silently reuses them on a different grid. Because the integrals for data and test segments are built together at INITIALIZE, a stale cache corrupts both the capture cross sections and the data-mode χ². `intEC.dat` is the equivalent for the data segments and is safe while `<segmentsData>` is untouched. Both files are safe to delete; they only cost time to rebuild.
5. Open one AZURE2 session per process, because a second `azure2()` in the same interpreter desyncs `GET_PARAMS_INFO`. Variants are therefore swept from a shell loop, or one temporary `.azr` is built that carries everything the run needs.
6. CLI mode does not read the Runtime Options from the `.azr`, so they must be passed as flags every time (`--use-brune`, `--gsl-coul`, …).

## Workflow A: interactive CLI (one-shot runs)

The CLI prompts in a fixed order: the menu choice, then the external parameter file, then the prompts of the chosen mode. Piping stdin runs it non-interactively.

| # | Mode |
|---|------|
| 1 | Calculate Segments From Data (`AZUREOut_*.out`, `chiSquared.out`) |
| 2 | Fit Segments From Data (Minuit2 → `param.sav`, `parameters.out`) |
| 3 | Calculate Segments Without Data / extrapolate (`AZUREOut_*.extrap`) |
| 4 | MINOS Error Analysis (`param.errors`, `covariance_matrix.out`) |
| 5 | Calculate Reaction Rate (needs temps → `reactionrates.dat`) |
| 6 | MCMC Bayesian Sampling (`samples.mcmc`) |
| 7 | Exit |

At the external parameter file prompt, a saved `output/param.sav` starts the run from those best-fit formal parameters, and a blank answer builds the parameters fresh from the `.azr` levels.

```bash
# Calculate with saved best-fit params; writes chiSquared.out + AZUREOut_*.out
printf '1\noutput/param.sav\n' | AZURE2 --no-gui 7Be.azr

# Fit fresh from the .azr levels. Mode 2 then asks about the cross-section
# uncertainty band (y/n) and, if yes, reduced-chi2 scaling (y/n):
printf '2\n\nn\n' | AZURE2 --no-gui 7Be.azr

# Extrapolate (no data) using saved params:
printf '3\noutput/param.sav\nn\n' | AZURE2 --no-gui 7Be.azr
```

The flag `--covariance-band`, with `--scale-covariance`, controls the band without the y/n prompts. Other flags are `--use-brune`, `--gsl-coul`, `--ignore-externals`, `--use-rmc` and `--no-transform`; `--help` lists all.

## Workflow B: pyazr

pyazr spawns headless `AZURE2 --no-gui --use-api` processes and talks to them over a socket. A session is a context manager and is always closed. The package is not on PyPI and is installed from the repository root.

```bash
pip install -e .                # core: numpy, mpmath, scipy
pip install -e ".[examples]"    # + matplotlib, emcee, multiprocess
pip install -e ".[all]"         # + zeus-mcmc
```

The `-e` form is the useful one, since the package lives in the checkout. AZURE2 itself is C++ and is not installed by pip, so it is built separately. pyazr locates the binary via `$AZURE2_BINARY`, then `build/src/AZURE2`, then `$PATH`, and the binary must be built with `USE_API=ON`, which is the default. Installing also puts `pyazr-cleanup` on the path; it reaps API instances orphaned by an interpreter that died before it could close them.

```python
import os
os.environ.setdefault("OMP_NUM_THREADS", "4")   # set BEFORE importing numpy
import numpy as np
from pyazr import azure2, AzrModel

with azure2("7Be.azr", nprocs=1, cwd=HERE) as m:
    best = np.asarray(m.params_rwa, float)      # free parameter vector
    chi2 = np.sum(m.calculate_chi2_rwa(best))
```

`nprocs=N` spawns N independent instances, and `proc=i` selects one; this gives one χ² per walker in emcee/zeus. Ports are OS-assigned, so parallel sessions never collide. The rest of the pyazr API, namely the two parameter conventions, data and extrapolation mode, inspecting a model, χ² per data set, observables and analysing power, and fitting from Python, is described in [references/pyazr.md](references/pyazr.md).

## Where to read next

| Task | Read |
|---|---|
| Parameter conventions, χ² per dataset, observables, analysing power, least-squares fits | [references/pyazr.md](references/pyazr.md) |
| Adding/removing/moving levels, `AzrModel`, extrapolation grids | [references/model-editing.md](references/model-editing.md) |
| Level/interference/external decomposition, S factor, significance tests, radius changes, evaluation recipes | [references/decomposition-and-recipes.md](references/decomposition-and-recipes.md) |
| Trojan Horse (THM/HOES) segments | [references/thm.md](references/thm.md) |
| `.azr` anatomy, `.dat` data format, output files | [references/files.md](references/files.md) |
| Ready-made 7Be scripts, pyazr examples | [references/scripts-and-examples.md](references/scripts-and-examples.md) |

The relevant file is read before editing a model, writing a fitter or interpreting a decomposition. The rules above apply throughout.

## Verifying a run

The quickest check is `cat output/chiSquared.out`, which must show a finite total χ² and the expected N per segment. From pyazr, `np.sum(m.calculate_chi2_rwa(m.params_rwa))` must reproduce the known total of the model. We record that total whenever the `.azr` changes, because a jump concentrated in the capture datasets almost always means a stale `intEC.extrap`. After a fit, check that `param.sav` was updated, and compare the widths in `parameters.out`, and their θ², against expectations.

## What to deliver

- The `.azr` file and the `param.sav` of the reported model, with the total χ² recorded for it.
- `chiSquared.out` and `parameters.out` of the final run, with the frame of every quoted energy stated.
- Extrapolated S factors or rates, with the AZURE2 build and the flags used.
