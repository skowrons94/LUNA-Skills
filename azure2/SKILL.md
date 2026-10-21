---
name: azure2
description: Run AZURE2 R-matrix evaluations of nuclear reaction/scattering data — calculate cross sections & chi-squared, fit levels/widths, add/remove levels, decompose a cross section into level/interference/external contributions, extrapolate, compute reaction rates, or drive AZURE2 from Python via pyazr. Use whenever the task involves an .azr project file, AZURE2 levels/channels/segments, R-matrix fitting, S-factors, resonance significance tests, or the o17_guardo (THM) example in this repo.
---

# Running AZURE2 evaluations

AZURE2 is a multi-channel, multi-level R-matrix code. An evaluation is driven by
a single `.azr` project file that describes the compound nucleus, particle
pairs, levels/channels, and data segments. Two headless ways to run it: the
**interactive CLI** (`--no-gui`) and the **pyazr** Python API. Use the CLI for a
one-shot calculate/fit/extrapolate/rate that writes the standard output files;
use **pyazr for all evaluation work** — χ², parameter scans, level add/remove
tests, cross-section decomposition, custom fitters and samplers.

The binary is on `$PATH` as `AZURE2` (also `build/src/AZURE2` in the source
repo); pyazr resolves it via `$AZURE2_BINARY` → `<repo>/build/src/AZURE2` →
`$PATH`, so `binary=` is usually unnecessary. **The two can drift**:
`/usr/local/bin/AZURE2` is a copy, not a symlink, so a `make AZURE2` in the
source repo does not reach it — `sudo cp build/src/AZURE2 /usr/local/bin/` after
every rebuild, or export `$AZURE2_BINARY`. AZURE2 must be installed (with its `pyazr/`
package, v2.3.0 or later, at the source repo root); pyazr is often mirrored into
evaluation directories, so `from pyazr import ...` works when cwd is either.

Full reference docs: `docs/_build/html/_sources/` — `reference/` covers
command_line, data_formats, output_files; `user_guide/` covers levels_channels,
segments, particle_pairs, fitting, mcmc. Worked example: `examples/o17_guardo/`.

## Golden rules

- **Input is LAB frame, forward kinematics** (light particle = projectile).
  **All output files and API results are CENTER-OF-MASS.** Never mix them.
  This includes `add_extrapolation(e_min, e_max, e_step)` — those are **lab**
  energies (multiply c.m. by `(m_beam + m_target)/m_target`), while the energies
  that come *back* from `calculate_energies` are c.m.
- Always run **from the directory that contains the `.azr` file** (pyazr does
  this for you via `cwd=`, defaulting to the `.azr`'s directory), because the
  `.azr` stores `output/`, `checks/` and data paths *relative to itself*.
- The `output/` directory must exist; AZURE2 writes results there.
- **Delete `output/intEC.extrap` whenever the `<segmentsTest>` grid changes.**
  AZURE2 caches external-capture integrals there and silently reuses them on a
  different grid — this corrupts capture cross sections *and* data-mode χ²
  (integrals for data and test segments are built together at INITIALIZE).
  `intEC.dat` is the data-segment equivalent and is safe while `<segmentsData>`
  is untouched. Both are safe to delete; they just cost time to rebuild.
- **One AZURE2 session per process.** Opening a second `azure2()` in the same
  interpreter desyncs `GET_PARAMS_INFO`. Sweep variants from a shell loop, or
  build one temp `.azr` that carries everything the run needs.
- CLI mode does **not** read Runtime Options from the `.azr` — pass them as
  flags every time (`--use-brune`, `--gsl-coul`, …).

## Workflow A — interactive CLI (one-shot runs)

Prompt order: **(1) menu choice → (2) external parameter file → (3) mode-specific
prompts**. Pipe stdin to run non-interactively.

| # | Mode |
|---|------|
| 1 | Calculate Segments From Data (`AZUREOut_*.out`, `chiSquared.out`) |
| 2 | Fit Segments From Data (Minuit2 → `param.sav`, `parameters.out`) |
| 3 | Calculate Segments Without Data / extrapolate (`AZUREOut_*.extrap`) |
| 4 | MINOS Error Analysis (`param.errors`, `covariance_matrix.out`) |
| 5 | Calculate Reaction Rate (needs temps → `reactionrates.dat`) |
| 6 | MCMC Bayesian Sampling (`samples.mcmc`) |
| 7 | Exit |

The **external parameter file** prompt: give a saved `output/param.sav` to start
from those best-fit formal parameters, or leave **blank** to build fresh from
the `.azr` levels.

```bash
# Calculate with saved best-fit params; writes chiSquared.out + AZUREOut_*.out
printf '1\noutput/param.sav\n' | AZURE2 --no-gui 7Be.azr

# Fit fresh from the .azr levels. Mode 2 then asks about the cross-section
# uncertainty band (y/n) and, if yes, reduced-chi2 scaling (y/n):
printf '2\n\nn\n' | AZURE2 --no-gui 7Be.azr

# Extrapolate (no data) using saved params:
printf '3\noutput/param.sav\nn\n' | AZURE2 --no-gui 7Be.azr
```

Non-interactive band control: `--covariance-band` (+ `--scale-covariance`) skips
the y/n prompts. Other flags: `--use-brune`, `--gsl-coul`, `--ignore-externals`,
`--use-rmc`, `--no-transform`; `--help` lists all.

## Workflow B — pyazr

pyazr spawns headless `AZURE2 --no-gui --use-api` processes and talks to them
over a socket. A session is a context manager; always close it.

Install it from the repository root (it is not on PyPI):

```bash
pip install -e .                # core: numpy, mpmath, scipy
pip install -e ".[examples]"    # + matplotlib, emcee, multiprocess
pip install -e ".[all]"         # + zeus-mcmc
```

`-e` is the useful form, since the package lives in the checkout. AZURE2 itself
is C++ and is **not** installed by pip — build it separately. pyazr locates the
binary via `$AZURE2_BINARY`, then `build/src/AZURE2`, then `$PATH`, and it must
be built with `USE_API=ON` (the default). Installing also puts `pyazr-cleanup`
on the path, which reaps API instances orphaned by an interpreter that died
before it could close them.

```python
import os
os.environ.setdefault("OMP_NUM_THREADS", "4")   # set BEFORE importing numpy
import numpy as np
from pyazr import azure2, AzrModel

with azure2("7Be.azr", nprocs=1, cwd=HERE) as m:
    best = np.asarray(m.params_rwa, float)      # free parameter vector
    chi2 = np.sum(m.calculate_chi2_rwa(best))
```

`nprocs=N` spawns N independent instances (`proc=i` selects one) — for one χ²
per walker in emcee/zeus. Ports are OS-assigned, so parallel sessions never
collide.


The rest of the pyazr API — the two parameter conventions, data vs extrapolation
mode, inspecting a model, per-dataset χ², observables and analysing power, fitting
from Python — is in [references/pyazr.md](references/pyazr.md).

## Where to read next

| Task | Read |
|---|---|
| Parameter conventions, χ² per dataset, observables, analysing power, least-squares fits | [references/pyazr.md](references/pyazr.md) |
| Adding/removing/moving levels, `AzrModel`, extrapolation grids | [references/model-editing.md](references/model-editing.md) |
| Level/interference/external decomposition, S factor, significance tests, radius changes, evaluation recipes | [references/decomposition-and-recipes.md](references/decomposition-and-recipes.md) |
| Trojan Horse (THM/HOES) segments | [references/thm.md](references/thm.md) |
| `.azr` anatomy, `.dat` data format, output files | [references/files.md](references/files.md) |
| Ready-made 7Be scripts, pyazr examples | [references/scripts-and-examples.md](references/scripts-and-examples.md) |

Read the relevant file before editing a model, writing a fitter or interpreting a
decomposition; the golden rules above apply throughout.

## Verifying a run

`cat output/chiSquared.out` — a finite total χ² and the expected N per segment.
From pyazr: `np.sum(m.calculate_chi2_rwa(m.params_rwa))` must reproduce the
model's known total (record it whenever the `.azr` changes; a jump concentrated
in the capture datasets almost always means a stale `intEC.extrap`). After a
fit, check `param.sav` updated and compare `parameters.out` widths — and their
θ² — against expectations.
