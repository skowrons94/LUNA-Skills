# Data model: raw files, ROOT files and the run logbook

The analysis reads the data through two generated products, one ROOT file per run and one table with a row per run,
both made by scripts in `tools/` from the original files, which stay untouched in `data/raw/`. This keeps every format
quirk (ORTEC headers, MPA list mode, CoMPASS folders) in one validated converter instead of in every analysis script,
and lets the analysis be rerun from the originals at any time.

## Raw data

`data/raw/YYYY-MM[_campaign]/` holds the files as received, with the folder structure of the source where it carries
meaning (one folder per run in CoMPASS, per target in older campaigns). Files are copied read-only and their checksums
compared with the source (SHA-256 or MD5 on both sides, both lists sorted with `LC_ALL=C`); `data/file_map.csv` has
one row per file with `source_path, local_path, sha256, note`. Large campaigns are not copied whole: the README says
which targets and runs were taken and what stayed on the server, so that a later analysis can extend the selection.

## ROOT files

`data/root/YYYY-MM/<run>.root`, one file per run, keeps the original run name so that logbooks and spreadsheets still
refer to it. Each file contains:

- a TTree `events` for list-mode data, one entry per hit, with the branches `channel` (int), `timestamp_ns` (double or
  long), `energy_adc` (the raw energy value), `flags` (DAQ flags, pile-up, saturation) and, where the DAQ gives it,
  `energy_short` for pulse-shape data. Calibrated energies are not stored here, because the calibration is a result of
  02_calibration and changes; they are computed when the tree is read.
- a TH1D `h_ch<N>` per channel with the raw spectrum, in ADC channels, exactly as the DAQ wrote it when it wrote one
  (histogram-mode data have only these).
- metadata as TNamed or a TTree `meta`: run name, source file(s) and their sha256, start and stop time, real time and
  live time per channel, DAQ settings (thresholds, gains) when available, converter name and version.

A converter is accepted only after its validation script compares, for at least one run of every format and period,
the counts channel by channel, the live and real times and the start time with an independent copy or reader of the
same measurement (an `.Spe` exported next to an `.Spc`, the CoMPASS histogram next to the list mode). The format is
detected from the file content, not from the extension, because old files are often misnamed.

## logbook.csv

`data/logbook.csv` is built by `tools/build_logbook.py` from the ROOT metadata and the original logbooks in
`data/logbook_sources/`. One row per run; the columns below are required, others may be added.

| Column | Content |
|---|---|
| `run` | run name as in the DAQ |
| `file` | path of the ROOT file, relative to the project |
| `start`, `stop` | ISO times from the file header |
| `real_s`, `live_s` | from the file header (per main detector channel if they differ; the others in extra columns) |
| `charge_C`, `charge_source` | integrated charge and where it came from (integrator log, logbook, DAQ scaler) |
| `current_uA` | mean current |
| `Ep_keV`, `Ep_source` | calibrated beam energy (01_beam formula) and its inputs (`TV_kV`, `PV_kV` or `EV_kV`) |
| `target` | target name as in the target list |
| `purpose` | one of `scan`, `long_run`, `background`, `source`, `calibration`, `test`, `excluded` |
| `geometry` | detector configuration (distance, angle, shielding) |
| `source_id` | calibration source and certificate, for source runs |
| `flags` | semicolon-separated flags from the audit (`charge_suspect`, `duplicate`, `partial`, ...) |
| `notes` | operator remarks, copied verbatim |

Where two sources give a quantity (live time from the header and from the logbook, charge from the integrator and from
the shift report), both are kept: the adopted value in the column above, the other in `<quantity>_<source>`, and a flag
when they disagree beyond tolerance. The spectrum header is authoritative for times; logbook descriptions are often
stale and are copied, not interpreted.

## Integrity

`data/MANIFEST.sha256` holds the checksums of `data/raw/` and `data/root/` and is regenerated after every conversion;
`check_measurement_project.py` verifies it. A ROOT file that no longer matches its converter output is a sign that
someone edited derived data by hand.
