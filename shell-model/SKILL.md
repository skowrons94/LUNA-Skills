---
name: shell-model
description: Run and interpret configuration-interaction shell-model calculations with KSHELL for light nuclei — p and p-sd (cross-shell) interactions such as YSOX, Cohen-Kurath or PSDMK, hbar-omega truncations, the Lawson term against spurious centre-of-mass states, energies, J^pi, isospin, orbit occupancies and hbar-omega content, calibration of a non-normal-parity (intruder) band on neighbouring nuclei referred to core+nucleon thresholds, and predictions of unobserved states (1/2+, 5/2+ intruders, mirror states) with an uncertainty. Use whenever a task asks where a state of a light nucleus should lie, what it is made of (one nucleon in the sd shell, a cluster, a mixture), whether an R-matrix level has a shell-model counterpart, or how to set up, run or parse KSHELL; these must be computed, not estimated from memory.
---
# Shell model (KSHELL)

The shell model says where states lie and what they are made of. It does not say how wide they are: every state lives in a square-integrable basis. Use it to identify a level, not to fix a width.

## Route the task

- **Widths, phase shifts, ANCs, the continuum**: `cluster-potential` (two-body) or `microscopic-cluster` (antisymmetrized).
- **The R-matrix level being identified**: `azure2`.
- **Mirror states** (Thomas–Ehrman shifts, charge-symmetry tests): `mirror-nucleus`. The shell model gives the charge-symmetric part.
- **Evaluated level data** to calibrate against: ENSDF/TUNL through `evaluated-nuclear-data`.
- Everything else: setup and runs in [running.md](references/running.md); checks and lessons in [validation.md](references/validation.md).

## Non-negotiable boundaries

1. **No widths from the shell model.** Energies, J^π, isospin, occupancies, ħω content and, with care, spectroscopic factors. A width needs a continuum calculation.
2. **Spurious states are removed, and shown removed.** In any space with more than one ħω, run with the Lawson term (β_cm = 10) and check ⟨H_cm⟩ per state. Physical states carry ~0.0–0.1 MeV. A state with several MeV is a centre-of-mass excitation. Keep the β_cm = 0 run that shows the difference.
3. **Use the interaction in the space it was fitted for.** YSOX: p-sd, 0–2ħω for normal and 1–3ħω for non-normal parity. A smaller truncation is a sensitivity check (7Be: 0.3–0.6 MeV), not the result.
4. **Calibrate an intruder band before predicting with it.** Take the same kind of state (1/2⁺, 5/2⁺) in neighbouring nuclei where it is known. Refer every energy to the same reference, preferably the core+nucleon threshold. The offset corrects the prediction and the scatter is its uncertainty. In the 7Be study the scatter was 1.04 MeV referred to the ground state and 0.38 MeV referred to the threshold.
5. **Say what the state is made of.** sd occupancy 1.00 is one promoted nucleon on a core, not a cluster state. Quote the occupancy with the identification.
6. **Match the mirror conventions.** The same interaction gives identical spectra for mirrors without Coulomb. Thomas–Ehrman shifts come from the continuum, not from here.

## Working method

1. Choose the interaction and space; build partitions per parity and truncation with KSHELL's `kshell_ui.py`. Name them `<nuc>_n02` (normal 0–2ħω), `<nuc>_p13` (non-normal 1–3ħω), and `_n`/`_a` for the minimal 0ħω/1ħω pair.
2. Write inputs with `write_input` (Lawson term on), run `kshell.exe in_x.input > log_x.txt`, and keep the logs.
3. Parse with `parse_log`. Separate spurious states (`flag_spurious`) and record E, J^π, T, ⟨H_cm⟩, sd occupancy and ħω content.
4. Calibrate: compute residuals (experiment − model, referred to threshold) for the known analog states; `calibrate` gives offset and scatter. Apply them to the prediction.
5. Compare with the R-matrix level and quote the distance in combined standard deviations, the occupancy and the truncation sensitivity.

## Scripts (Python with numpy; KSHELL itself for the runs)

```bash
python3 SKILL_DIR/scripts/selftest.py       # must print PASS (parser on a real log fragment, Lawson flag, calibration)
```
```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts"); import kshell_tools as kt
kt.write_input("in_Be7_p13.input", "ysox.snt", "Be7_p13.ptn", n_eigen=25)
st = kt.parse_log(open("log_Be7_p13.txt").read()); phys, spur = kt.flag_spurious(st)
off, unc = kt.calibrate([exp - sm for exp, sm in calibration_pairs])
```
