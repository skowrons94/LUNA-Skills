# Setting up and running KSHELL

## Build

KSHELL (Shimizu, Mizusaki, Utsuno, Tsunoda, Comput. Phys. Commun. 244, 372 (2019)) is Fortran with LAPACK/BLAS.
- On macOS: gfortran from Homebrew/conda, linked against Accelerate. Use `make` in `src/` with `FC = gfortran` and `LIBS = -framework Accelerate`, and add `-fopenmp` for threads.
- Binaries: `kshell.exe` (Lanczos) and `transit.exe` (transitions). The interactions (`.snt`) go next to the run.
- Set `export GFORTRAN_UNBUFFERED_PRECONNECTED=y` so the logs are written as the run proceeds.

## Model spaces and interactions

| interaction | space | core | use |
|---|---|---|---|
| YSOX | p + sd (0p, 0d, 1s) | ⁴He | cross-shell; normal parity 0–2ħω, non-normal 1–3ħω |
| Cohen–Kurath (ckpot) | p | ⁴He | p-shell benchmark of the normal-parity spectrum |
| PSDMK, WBP/WBT | p-sd | ⁴He | alternatives for the cross-shell band |

- Partitions (`.ptn`) are made by `kshell_ui.py`, which asks for the interaction, nucleus, parity and truncation (`hw` truncation for cross-shell).
- The same script writes a namelist and a run script. `write_input` here reproduces the namelist with the Lawson term explicit.
- `mtot` is 2M: use the lowest value of the nucleus (1 for odd A, 0 for even A) to get all J.
- `n_eigen` must be large enough to reach the states you need after spurious ones are removed. In a 1–3ħω space the lowest few states can all be spurious.

## The log

Each eigenstate prints:
- `<H>`, `<JJ>`, J and parity;
- `<Hcm>` and T;
- orbit occupancies `<p Nj>` and `<n Nj>`, in the orbit order of the header line `n orbit …`;
- the ħω decomposition `hw: 0:0.94 2:0.06`.

`parse_log` reads all of them.

## Calibrating an intruder band (the 7Be recipe)

1. Calibration nuclei: neighbours where the same non-normal-parity states are known. For 7Be these were the lowest 1/2⁺ and 5/2⁺ in ⁹Be, ¹¹Be and ¹³C.
2. Core runs: the A−1 cores (⁸Be, ¹⁰Be, ¹²C; ⁶Li for 7Be) in the normal-parity space, for the core+nucleon thresholds.
3. Residual per calibration state: (E_exp − E_threshold,exp) − (E_SM − E_threshold,SM).
4. Offset = mean residual, uncertainty = rms about it (`calibrate`). Referred to thresholds, the 7Be study had scatter 0.38 MeV and offset +0.54 MeV. Referred to ground states the scatter was 1.04 MeV, which is why the threshold reference is the right one.
5. Prediction: E_x = threshold_exp + (E_SM − E_threshold,SM) + offset ± scatter.

## Reading the structure

- sd occupancy (`sd_occupancy`): 1.00 means one nucleon in the sd shell on a p-shell core. For 7Be, the 1/2⁺, 3/2⁺ and 5/2⁺ all had 1.00, i.e. ⁶Li ⊗ (2s, 1d) nucleon states.
- ħω content: the fraction in the lowest allowed space against admixtures. Large higher-ħω admixtures make a truncation comparison necessary.
- Spectroscopic factors for one-nucleon removal need overlaps (`transit.exe` or KSHELL's sf scripts). Quote them with the radius convention of the reaction model that uses them.
