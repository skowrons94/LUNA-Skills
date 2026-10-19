# Where to get evaluated data

## OpenMC HDF5 builds (fastest route for neutrons)

Index: https://openmc.org/data (source page: github.com/openmc-dev/openmc.org, `data.md`). Each library is one `.tar.xz` on `anl.box.com`; read the current links from that page, they change. Builds available in 2026: ENDF/B-VII.1, ENDF/B-VIII.0, **ENDF/B-VIII.1**, **JEFF-3.3**, **JEFF-4.0**, **JENDL-5**, FENDL-3.2, plus LANL ACE conversions (endf70, endf71x, lib80x).

What the builds contain and where they differ from the original library:
- Incident-neutron data at several temperatures (typically 250–2500 K), thermal scattering (`c_*.h5`), photon data, sometimes windowed multipole.
- **JEFF-3.3 build: C13 and O17 are TENDL-2019** (NJOY could not process the JEFF files); natural carbon is stored as `C0`. Label these explicitly.
- JEFF-4.0 / JENDL-5 builds: photon and atomic relaxation data are taken from ENDF/B-VIII.1.
- NJOY version is stated on the page (e.g. 2016.78); it can matter for edge cases.

Size: the archives are 2–10 GB compressed; **ENDF/B-VIII.1 unpacks to more than 40 GB** (thermal scattering alone is about 31 GB). If disk is tight, extract only what you need; `xz` still decompresses the whole stream but tar writes only the selected members:

```bash
pats=('*cross_sections.xml'); for n in O16 O17 F19 Na23 Pb208 Bi209; do pats+=("*/neutron/$n.h5"); done
xz -T0 -dc LIB-hdf5.tar.xz | tar -xf - -C LIB "${pats[@]}"      # BSD and GNU tar accept these wildcards
```

A partial library is fine for cross-section lookups and for transport, as long as the materials use only extracted nuclides (OpenMC loads nuclides lazily). Keep the full `cross_sections.xml`.

## Raw ENDF-6 files

| Library | Primary distributor | Notes |
|---|---|---|
| ENDF/B-VIII.1, VIII.0 | NNDC, https://www.nndc.bnl.gov/endf-b8.1/ (sublibrary zips) | worked for scripted download in 2026 |
| JEFF-4.0, JEFF-3.3 | OECD NEA, https://www.oecd-nea.org/dbdata/jeff/ | returned HTTP 403 to scripts; download in a browser |
| JENDL-5 | JAEA, https://wwwndc.jaea.go.jp/jendl/j5/j5.html | bot-challenge page for scripts; browser download |
| TENDL-2023 | PSI, https://tendl.web.psi.ch/ (mirrors exist) | host intermittently unreachable |
| CENDL-3.2 | CNDC (via IAEA NDS) | |
| All of the above | IAEA NDS, https://www-nds.iaea.org/public/download-endf/ | Cloudflare challenge for scripts in 2026 |

Do not try to defeat bot protection or spoof user agents. Ask the user to download the file in a browser, then treat it as an immutable input with a recorded checksum.

Charged-particle sublibraries are much sparser than neutron ones: ENDF/B-VIII.1 has protons for few light targets and alphas for a handful (e.g. 9Be, 17O, 18O); JENDL-5 and TENDL have broad p, d, α coverage. For many (α,n) reactions there is **no evaluation**; use EXFOR data or an R-matrix fit and say so.

## Experimental data next to evaluations

EXFOR: the IAEA web retrieval may refuse scripts; the official master files are on GitHub (`IAEA-NDS/exfor_master`, a shallow clone is about 1.4 GB) and can be scanned locally. Record the commit hash; entries newer than the snapshot are missing.

## Decay and structure data

ENSDF and decay data: NNDC NuDat 3 (https://www.nndc.bnl.gov/nudat3/) or IAEA LiveChart; for gamma-ray lines and efficiency work use the `efficiency-analysis` skill.
