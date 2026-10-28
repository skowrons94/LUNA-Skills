---
name: shell-model
description: Run and interpret KSHELL shell-model calculations of light nuclei, and turn spectroscopic amplitudes from a CI calculation with cluster channels (e.g. FSU / Kravvaris–Volya) into R-matrix reduced widths, with p and p-sd (cross-shell) interactions such as YSOX, Cohen-Kurath or PSDMK, hbar-omega truncations and the Lawson term against spurious states, giving energies, J^pi, isospin, sd occupancies and calibrated intruder (1/2+, 5/2+) or mirror states; widths only through a single-particle continuum width. Use when a task asks where a state of a light nucleus should lie, what it is made of, whether an R-matrix level has a shell-model counterpart, or how to run or parse KSHELL; these must be computed, not estimated from memory.
---
# Shell model (KSHELL)

The shell model answers two questions about a level of a light nucleus: where it should lie and what it is made of, whether one nucleon in the sd shell, a cluster or a mixture. It does not say how wide the level is, because every state lives in a square-integrable basis without a continuum. The skill is therefore used to identify a level, for instance an R-matrix level that has no counterpart in the compilation, not to fix its width. You need an interaction suited to the model space, the KSHELL binaries and the known levels of neighbouring nuclei for calibration. You get energies, J^π, isospin, orbit occupancies and ħω content per state, the spurious states separated, and a calibrated prediction of unobserved states (1/2⁺, 5/2⁺ intruders, mirror states) with an uncertainty.

## Where this fits

- Comes from: known levels of the nucleus and its neighbours from the compilations (ENSDF, TUNL) for the calibration; the R-matrix level to identify from `r-matrix`; the structure questions raised by `cluster-potential`, `microscopic-cluster` and `mirror-nucleus` (intruder energies and configurations, mirror states).
- Goes to: the identification of that level in `r-matrix`, and the reduced widths implied by spectroscopic amplitudes, computed as described in [amplitudes-to-widths.md](references/amplitudes-to-widths.md) with `scripts/amplitudes.py` and the single-particle width of `cluster-potential`; the charge-symmetric part of mirror states for `mirror-nucleus`. Widths, phase shifts, ANCs and the continuum are left to `cluster-potential` (two-body) or `microscopic-cluster` (antisymmetrized).
- Checked by: `scripts/selftest.py` (must print PASS) and the validation ladder in [validation.md](references/validation.md); setup and runs are described in [running.md](references/running.md).

## Method

The interaction is used in the space it was fitted for, spurious centre-of-mass states are removed with the Lawson term, and an intruder band is calibrated on neighbouring nuclei before it predicts anything.

1. Choose the interaction and space, and build partitions per parity and truncation with KSHELL's `kshell_ui.py`. Name them `<nuc>_n02` (normal 0–2ħω), `<nuc>_p13` (non-normal 1–3ħω), and `_n`/`_a` for the minimal 0ħω/1ħω pair.
2. Write inputs with `write_input`, which sets the Lawson term on, run `kshell.exe in_x.input > log_x.txt`, and keep the logs.
3. Parse with `parse_log`. Separate the spurious states with `flag_spurious` and record E, J^π, T, ⟨H_cm⟩, sd occupancy and ħω content for the others.
4. Calibrate on the known analog states. The residuals are experiment − model, referred to the threshold, and `calibrate` gives the offset and the scatter, which are applied to the prediction.
5. Compare with the R-matrix level and quote the distance in combined standard deviations, the occupancy and the truncation sensitivity.

## Rules and their reasons

1. The shell model alone gives no widths. It gives energies, J^π, isospin, occupancies, ħω content and spectroscopic factors, and a width needs a continuum calculation, because a square-integrable basis has no decay channel. A spectroscopic factor becomes a reduced width only when it multiplies a single-particle R-matrix width computed at the fitted energy and channel radius. Cluster spectroscopic factors are used as built; a channel normalized to unity divides them by the projected eigenvalue mu_Q of the norm kernel, and the renormalized strength summed over states is checked against the number of J values of the channel, which is how an unphysical normalization was caught in 7Be.
2. Spurious states are removed, and shown to be removed. In any space with more than one ħω the run uses the Lawson term (β_cm = 10), and ⟨H_cm⟩ is checked per state. Physical states carry ~0.0–0.1 MeV, while a state with several MeV is a centre-of-mass excitation. The β_cm = 0 run that shows the difference is kept. In the 7Be study the three lowest positive-parity states of the full 1ħω space were spurious (validation.md).
3. The interaction is used in the space it was fitted for. YSOX is a p-sd interaction for 0–2ħω in normal and 1–3ħω in non-normal parity. A smaller truncation is a sensitivity check (7Be: 0.3–0.6 MeV), not the result.
4. An intruder band is calibrated before it predicts. The same kind of state (1/2⁺, 5/2⁺) is taken in neighbouring nuclei where it is known, and every energy is referred to the same reference, preferably the core+nucleon threshold. The offset corrects the prediction and the scatter is its uncertainty. The reference sets the error: in the 7Be study the scatter was 1.04 MeV referred to the ground state and 0.38 MeV referred to the threshold.
5. The identification says what the state is made of. An sd occupancy of 1.00 is one promoted nucleon on a core, not a cluster state, so the occupancy is quoted together with the identification.
6. Mirror conventions are matched. Without Coulomb the same interaction gives identical spectra for mirrors, so the Thomas–Ehrman shifts come from the continuum and not from this calculation.

## Scripts

The tools need Python with numpy; the runs need KSHELL itself. Replace SKILL_DIR with this skill's directory.

```bash
python3 SKILL_DIR/scripts/selftest.py       # must print PASS (parser on a real log fragment, Lawson flag, calibration)
```
```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts"); import kshell_tools as kt
kt.write_input("in_Be7_p13.input", "ysox.snt", "Be7_p13.ptn", n_eigen=25)
st = kt.parse_log(open("log_Be7_p13.txt").read()); phys, spur = kt.flag_spurious(st)
off, unc = kt.calibrate([exp - sm for exp, sm in calibration_pairs])
```

## What to deliver

- The KSHELL logs of every run used, including the β_cm = 0 comparison run.
- Per state: E, J^π, T, ⟨H_cm⟩, sd occupancy and ħω content, with the spurious states listed separately.
- The calibration nuclei, the offset and the scatter, and the calibrated prediction with its uncertainty.
- The comparison with the R-matrix level: distance in combined standard deviations, occupancy and truncation sensitivity.
