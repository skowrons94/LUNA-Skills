---
name: measurement-project
description: Set up, migrate or audit the folder of a nuclear-astrophysics measurement (LUNA, MV, Felsenkeller) so every number traces back to a run: raw data, per-run ROOT files, a generated logbook.csv, stages from audit, beam, calibration, background, efficiency and target to yield, S factor, R-matrix and rate, report, slides, docs and the HANDOFF, PROBLEMS, LITERATURE, DECISIONS registers. Use when starting a campaign's analysis, importing DAQ or server data, or checking a project's reproducibility; feasibility studies without data use `nuclear-research-project`.
---
# Measurement project

An analysis of a measurement is reproducible only if a reader can go from any quoted S factor back to the runs, the
calibrations and the decisions that produced it. Most LUNA-type analyses follow the same path, from the run list through
beam and detector calibration, background, efficiency and target characterisation to yields, S factors and an R-matrix
fit, so one layout serves all of them and makes two analyses of the same reaction comparable. This skill creates that
layout, explains what belongs in each folder and checks an existing project against it. You need the campaign (reaction,
setup, targets, years) and the location of the original data; you get the folder, the registers and the scripts that
keep it consistent. The tree and the placement rules are in [layout.md](references/layout.md); the data model (raw
files, ROOT conversion, logbook.csv) in [data-and-logbook.md](references/data-and-logbook.md); what each stage does,
checks and hands on in [stages.md](references/stages.md).

## Where this fits
- Comes from: the DAQ files and logbooks of a campaign, copied read-only from the server or the acquisition PC.
- Goes to: the stage skills, each working inside one `analysis/NN_<stage>/` folder (`yield-analysis`,
  `efficiency-analysis`, `peak-shape-analysis`, `target-analysis`, `underground-gamma-simulation`, `r-matrix`,
  `reaction-network`), `analysis-chain` for gated multi-stage runs, `research-slides` and the writing skills.
- Checked by: `scripts/check_measurement_project.py`, the `data-auditor` and `physics-referee` subagents, and a
  fresh-context review at every stage gate.

## Method
The project is built in the order the information arrives, so that nothing downstream is computed before its inputs
are fixed and recorded.
1. Create the folder with `scripts/create_measurement_project.py`, named `<reaction>_<setup>_<target>_<years>`
   (e.g. `14npg_bgo_solid_2023-2025`). The script never overwrites a file.
2. Copy the original data into `data/raw/` read-only and verify checksums against the source; record every file in
   `data/file_map.csv` (source path, local path, sha256). This is the only copy of the measurement the analysis may use.
3. Convert every run into one ROOT file in `data/root/` with a validated converter in `tools/`, and build
   `data/logbook.csv` with `tools/build_logbook.py` from the file headers and the original logbooks, one row per run,
   with a source column for every quantity that can come from more than one place.
4. Put papers, theses, manuals, ELOG exports, shift reports, drawings, photographs and correspondence in `docs/`, and
   list every reference used in `LITERATURE.md` with its DOI and what it is used for.
5. Run the stages in `analysis/` in their numbered order. Each stage has a README with its inputs, outputs, checks and
   gate result; a stage's outputs are read by the next stage from its `results/` only.
6. Write problems with runs or inputs into `PROBLEMS.md` when they are found, decisions into `DECISIONS.md` when they
   are taken, and the state of the work into `HANDOFF.md` at the end of every session.
7. Generate the report tables from the results (`tools/make_report_tables.py`), build `report/` into `report/build/`,
   and look at the PDF before quoting a number from it.

## Rules and their reasons
1. Original files are never edited, renamed in place or deleted; converted, calibrated or summed data are new files
   elsewhere. A wrong conversion can then always be redone from the original, and the checksums in `file_map.csv` prove
   that the analysis used the data that were taken.
2. `logbook.csv` is generated, not edited by hand. Hand-corrected logbooks drift from the files they describe; a
   script that reads the spectrum headers (live and real time, start time) and the shift logbooks, and records which
   source each value came from, can be rerun and audited. Spectrum headers win for times; a logbook value that
   disagrees is kept in its own column and flagged.
3. A run belongs to exactly one purpose class (scan, long run, background, source, calibration, test, excluded) and
   the class is a column of the logbook. Several errors in the 2001–2002 14N(p,γ) re-analysis came from summed or
   partial spectra counted twice and from "plateau checks" that were on the edge of the resonance profile.
4. Every excluded run or input is in `PROBLEMS.md` with its evidence and a link to the decision in `DECISIONS.md`.
   Exclusions are human decisions, so the record must let the researcher reverse them.
5. Stages read only from the `results/` of earlier stages and from `data/`, never from another stage's scratch or
   figures. This keeps the dependency graph explicit, which is what lets a stage be rerun after a change upstream.
6. Every generated file has a script that regenerates it, named in the stage README. Results that only exist because
   of an interactive session cannot be checked by a referee or by the next student.
7. Exploratory work goes to `_claude/<date>_<topic>/` (ignored by git) and is promoted into a stage only when it
   reproduces from its own script and its numbers are checked; the promotion is written into `CHANGELOG.md`.
8. Comparison data (published S factors, collaborators' sheets, EXFOR) live in `data/external/` with their source and
   date, and are used for comparison only. A result that silently depends on the number it is compared with is not
   a measurement of it.

## Pitfalls
- A logbook that gives the terminal voltage instead of the calibrated beam energy shifts every effective energy; in the
  2001–2002 data the nominal and calibrated energies differ by 1.2–1.6 keV, which is a few percent in S at 140 keV.
- Resonance checks taken at one energy are only plateau checks if the target is thick and uniform at that depth; three
  of eleven targets in the same data set had a surface layer, a thin layer or a nitrogen depth gradient. The target
  stage must model the profile from all checks before they are used as normalisation (stages.md, 05_target).
- Effective energies of thick targets depend on the definition (median, mean, self-consistent); quote the one used,
  and compare with published points in units of a common model shape (stages.md, 07_sfactor).
- Large raw data (hundreds of GB) are not copied whole; choose targets and runs with the researcher, and record the
  selection and what was left on the server in the README.

## Scripts
```bash
# Replace SKILL_DIR with this skill's directory.
python3 SKILL_DIR/scripts/create_measurement_project.py PATH --reaction 14npg --setup bgo --target solid --years 2023-2025
python3 SKILL_DIR/scripts/check_measurement_project.py PATH          # layout, registers, logbook schema, checksums, stray files
python3 SKILL_DIR/scripts/check_measurement_project.py PATH --strict  # also fail on warnings (before a review or a release)
```

## What to deliver
- The project folder with the registers filled in: README.md (campaign, setup, targets, people, data sources and what
  was not copied), CLAUDE.md, HANDOFF.md, PROBLEMS.md, LITERATURE.md, DECISIONS.md, ASSUMPTIONS.md, CHANGELOG.md.
- `data/file_map.csv`, `data/MANIFEST.sha256` and `data/logbook.csv` consistent with `data/raw/` and `data/root/`.
- One README per stage with its gate result, and `report/build/main.pdf` built from generated tables.
- A clean `check_measurement_project.py` run.
