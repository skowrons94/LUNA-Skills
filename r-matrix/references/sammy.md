# SAMMY (ORNL): practical guide

Source of every keyword and format: the local manual `~/Research/60_Codes/SAMMY/doc/SAMMY8.pdf`
(N. M. Larson, ORNL/TM-9179/R8, ENDF-364/R2, 2008). Pages cited are the **printed** numbers ("p. 313").
The PDF page index differs (printed p. 598 is PDF page 521): run `pdftotext -layout SAMMY8.pdf s.txt`
and grep `Page 313`. The installed code is newer (`Version.cmake`: 08.01, CMake build). Items marked
**[not in R8]** were seen only in the source or the test cases.

## 1. When to use SAMMY instead of AZURE2

- **Built for** neutron-induced resonance analysis (resolved and unresolved regions): transmission,
  total, elastic, capture, fission, η, self-indication, angular distributions (card 8, p. 322), with
  corrections for the experiment: Doppler broadening (free gas, Leal–Hwang, high-energy Gaussian,
  crystal lattice; pp. 125–137), resolution broadening (Gaussian+exponential, ORR, RPI/GELINA/nTOF,
  user-defined; pp. 139–175), self-shielding and multiple scattering (p. 177), normalization and
  background (p. 193), sample thickness and abundances.
- **Formalisms** (p. 335): Reich–Moore (default), MLBW, SLBW. No full R-matrix: it is mimicked by
  Reich–Moore with a tiny eliminated Γγ and an explicit capture exit channel (II.B.2, p. 43).
  Logarithmic external R-function (p. 41; PAR card set 3).
- **Fitting**: Bayes (generalized least squares with a prior parameter covariance), with explicit,
  implicit or PUP (propagated-uncertainty parameter) data covariance and an output parameter
  covariance (Section IV, pp. 211–277).
- **ENDF**: reads File 2 as the parameter file (p. 467); writes File 2 `SAMMY.NDF`, File 32
  `SAMMY.N32`, File 3, File 33 and File 4 Legendre coefficients (pp. 358, 461–466).
- **Charged particles**: "not limited to incident neutrons but can also be used for incident protons,
  alpha particles, or other charged particles; likewise, Coulomb exit channels can be included"
  (abstract, p. xvii). Coulomb functions from COULFG (II.C.4, p. 75); `USE ALTERNATIVE COULomb
  functions` for low ρ / high η (pp. 76, 364). With a charged incident particle "only the
  angle-differential cross sections are calculable" (p. 75).
- **Limits stated in the manual**: one incident particle; reciprocal data cannot share the same
  parameters in one evaluation, convert them by detailed balance (II.C.5, p. 79). Capture is the
  eliminated Reich–Moore Γγ, plus an optional `ADD DIRECT CAPTURE Component` read from a file
  (p. 51, p. 364), not AZURE2-style γ-ray channels with multipolarities. Energies are lab eV.
- **Rule of thumb**: neutron resonance data with broadening and sample corrections, delivered as
  ENDF File 2/32 → SAMMY. A charged-particle compound system fitted in all partitions at once, with
  capture to bound states, S-factor extrapolation and Brune parameters (e.g. ⁷Be) → AZURE2. The local
  test set does contain a ⁷Be (³He+α, p+⁶Li) example using `NEW INCIDENT PAIR =`
  (`samtry/convertToInverse/`; keyword in `src/blk/Zzzzz_common.f90`) **[not in R8]**.

## 2. Files and run sequence

SAMMY reads file names from stdin (Table VI E.1, p. 451; full list Table VI E.2, pp. 452–454; names
≤ 70 characters). The bundled tests use a here-document:

```sh
sammy <<EOF
case.inp
case.par
case.dat 150000.,167852.

EOF
```

INPut file, PARameter file (or the ENDF file, §6), DATa file followed by EMIN, EMAX in eV with
decimal points (these override card 2), then a blank line to stop (p. 451). Further files are asked
for afterwards, in the order of Table VI E.2: ndf file (ENDF output), WY files, direct capture,
**parameter COVariance file**, edge effects, IDC, AVG, MXW, ...

- **DATa** (pp. 437–438, 341). Default MULTI style: three points per line, `3(2F15.5,F7.3)`, with
  **fractional** uncertainty (Table VI C1.1). `CSISRS` (= `USE CSISRS FORMAT FOr data`): one point
  per line (3G11.8), absolute uncertainty. `TWENTY` (= `USE TWENTY SIGNIFICAnt digits`): one point per
  line (3F20.10), absolute uncertainty. Energies monotonic, either direction. Angular distributions:
  `DIFFERENTIAL DATA ARe in ascii file`, (8F10.1), an energy line then an uncertainty line (p. 438).
- **Outputs** (Table VII.1, pp. 473–476) have fixed names in the working directory, so give each case
  its own directory. `SAMMY.LPT` (full listing: commands, flagged unknown commands, parameters, χ²,
  errors at the end), `SAMMY.IO` (initial/final varied parameters), `SAMMY.PAR` (updated parameters),
  `SAMMY.COV` (binary covariance + values), `SAMMY.ODF`/`SAMMY.LST` (ASCII)/`SAMMY.PLT` (columns:
  energy, data, uncertainty, initial theory, final theory; pp. 483–484), `SAMMY.RED` (reduced-width
  amplitudes, p. 383), `SAMMY.NDF`/`.N32`, `SAMMY.PUB` (p. 599), `SAMNDF.INP`/`.PAR`, `SAMQUA.PAR`.
- **Iterating** (VII.B, p. 479; test `tr004`): the output `SAMMY.PAR` ends with "Last A"
  (`COVARiance matrix is in binary form in another file`). Copy `SAMMY.PAR` and `SAMMY.COV` away and
  rerun with `case.inp / prev.par / case.dat EMIN,EMAX / prev.cov / (blank)`. **With a COV file,
  parameter values come from the COV file, not the PAR file** (p. 479). To drop the prior covariance:
  `IGNORE INPUT BINARY covariance file` (p. 338) or answer `IGNORE` (p. 606).

## 3. The INPut file

Card sets (Table VI A.1, pp. 311–330). `I` = right-justified integer, `F` = real with decimal point.

| Card | Content (columns) | Page |
|---|---|---|
| 1 | title | 313 |
| 2 | element 1–10, AW (amu) 11–20, EMIN 21–30, EMAX 31–40 (eV), NEPNTS 41–45, ITMAX 46–50 (default 2; negative for > 9), ICORR 51–52, NXTRA 53–55, ... | 313–315 |
| 3 | commands, one per line, then a blank line | 315 |
| 4 / 4a | key-word / fixed-format particle pairs, then a blank line | 316–318 |
| 5 | TEMP (K) 1–10, flight path (m) 11–20, DELTAL 21–30, DELTAE 31–40, DELTAG 41–50, ...; **omit with `BROADENING IS NOT WAnted`** or SAMMY aborts | 320 |
| 6 | only if DELTAG < 0 | 321 |
| 7 | CRFN radius (fm) 1–10, THICK (atoms/b) 11–20, DCOVA 21–30, DCOVB 31–40, VMIN 41–50 | 321 |
| 8 | data type from column 1: `TRANSmission`, `TOTAL cross section`, `ELASTic`, `DIFFErential elastic`, `DIFFErentiAL REaction`, `REACTion`, `FISSion`, `CAPTUre`, `FINAL state pairs = <names>`, ... | 322–323 |
| 10.1 / 10.2 | spin groups (10.2 with particle pairs is recommended), then a blank line | 324–327 |
| 11 | multiple-scattering geometry, only when requested | 328 |
| P4–P16 | PAR card sets moved into the INP: not variable there (flag 3 = PUP works) | 312, 330 |

**Commands** (p. 331): only the first 20 characters count (lowercase in the table is optional); case
free; the last of contradictory commands wins; unknown commands are only flagged in the LPT; `#` in
column 1 comments a command out. For a first run (Table VI A1.2; D = default):
formalism `REICH-MOORE FORMALISm is wanted` (D), `MLBW FORMALISM IS WAnted`, `SLBW FORMALISM IS
WAnted`, `REDUCED WIDTH AMPLITudes are used for input` (p. 335); quantum numbers `KEY-WORD
PARTICLE-PAir definitions are given` (preferred), `QUANTUM NUMBERS ARE in parameter file`
(p. 336), `FLAG ALL RESONANCE Parameters` (p. 337); data `TWENTY`, `CSISRS`, `IMPLICIT DATA
COVARIance is wanted` (pp. 341–343); broadening `BROADENING IS WANTED` (D) / `BROADENING IS NOT
WAnted` (p. 346), Doppler `USE FREE GAS MODEL Of doppler broadening` (D, `FGM`), `USE LEAL-HWANG
DOPPLer broadening`, `HEGA`, `CLM` (p. 347); fitting `SOLVE BAYES EQUATIONs` (D) / `DO NOT SOLVE
BAYES Equations` (p. 353); output `PRINT ALL INPUT PARAmeters`, `PRINT WEIGHTED RESIDuals`,
`CHI SQUARED IS WANTEd` (D), `PRINT REDUCED WIDTHS`, `GENERATE PLOT FILE Automatically`, `INCLUDE
THEORETICAL uncertainties in Plot file`, `EV`/`KEV`/`MEV` (pp. 354–360); charged particles `CM
COULOMB EXCITATIOn energies` (thresholds in c.m.; default lab, p. 364).

**Particle pairs** (card 4, pp. 316–317): `Name=` (unique, 8 characters), `PA`/`PB` (types
`NEUtron`, `PROtron` (sic), `DEUteron`, `ALPha`, `HE3`, `TRIton` set mass, charge, spin), `MA`, `MB`,
`ZA`, `ZB`, `SA`, `SB` (sign = parity), `PEnetrability`, `Shift`, `Q-value` (c.m.) or `THreshold`
(lab unless a `CM ... EXCITation` command), `EFfective radius`/`RE`, `TRue radius`/`RT`.

**Spin groups**, card 10.2 (pp. 326–327). Group line: JJ 1–3, `X` in 5 to exclude, NENT 8–10,
NEXT 13–15, J 16–20 (sign = parity), abundance 21–30. Channel lines: number 3–5, pair name 8–15,
IFEXCL 18, l 19–20, channel spin 21–30 (sign = parity), boundary ENBND 31–40 (default B = −l),
radii 41–50 / 51–60.

**Channel radii**: PAR card 7/7a overrides card-10 / particle-pair radii, which override INP card 7
CRFN (pp. 317, 321, 325, 327). CRFN = 0 gives 1.45·(1.008665+AW)^(1/3) fm (p. 321). The effective
radius sets the potential phase; the true radius sets penetrability and shift (p. 400).

### Minimal skeleton (first, no-Bayes run)

Adapted from bundled test `samtry/tr001` (`t001ap.inp`, `t001a.par`; column positions checked against
the tables above). The numbers are that test's values; the data type was changed from ELASTIC to
TRANSMISSION. **Not executed here** (§7). The files take no comments; annotations follow.

```
n+60Ni transmission: first no-Bayes run
      60NI    59.927  150000.0  167852.0
REICH-MOORE FORMALISM IS WANTED
KEY-WORD PARTICLE-PAIR DEFINITIONS ARE GIVEN
BROADENING IS WANTED
USE FREE GAS MODEL OF DOPPLER BROADENING
TWENTY
DO NOT SOLVE BAYES EQUATIONS
GENERATE PLOT FILE AUTOMATICALLY
PRINT ALL INPUT PARAMETERS
PRINT WEIGHTED RESIDUALS
CHI SQUARED IS WANTED

Name=n+60Ni  Pa=n  Pb=60Ni  Mb=59.927  Sb=0.0

      300.   78.2030    0.0200    0.0000    0.0100
    6.0000  0.074400
TRANSMISSION
  1      1    0  0.5  1.000
    1  n+60Ni      0  0.5
  2      1    0 -0.5  1.000
    1  n+60Ni      1  0.5

```
The lines are, in order: card 1; card 2; card 3 + blank; card 4 + blank; card 5 (300 K, 78.203 m);
card 7 (6.0 fm, 0.0744 atoms/b); card 8; card 10.2 with group 1 = 1/2⁺ (s wave) and group 2 = 1/2⁻
(p wave); a final blank line.

PAR file (E_λ 1–11 eV, Γγ 12–22 meV, Γc1 23–33 meV, flags 56–65, group 66–67):
```
 .15140E+06 .20000E+04 .18000E+05                       0 0 1 0 0 2
 .16200E+06 .20000E+04 .13000E+07                       1 0 1 0 0 1

0.1
Channel RADIUS PARAMETERS FOLLOW
 Radius=   6.000   6.000  Flags=0 -1
   PP=n+60Ni    L=all

```
Not verified: the meaning of the second `Flags=` value in card 7a. The manual lists the allowed
values (Yes, 1, No, 0, 2, −1; p. 385) and gives the `tr059` example (p. 402) without explaining them.
By analogy with card 7, −1 makes the true radius equal to the effective one (p. 400). If in doubt,
use the fixed-column card 7 `RADIUs parameters follow`.

## 4. Parameters, priors and the Bayes fit

- **PAR card set 1** (pp. 389–390): E_λ, Γγ, Γc1–Γc3 (meV; a negative width gives a negative
  amplitude), flags (0 = fixed, 1 = vary, 3 = PUP), group (negative or > 50 omits the resonance), X in
  68–80 (< 0 means a continuation line with Γc4–Γc8). A blank line ends the set. Card set 2 is one line,
  FUDGE, the default relative prior (0.1); for E_λ the default prior is instead 2× the sum of all
  widths, Doppler and resolution included (p. 393). Card set 2 is required if any later card set is
  present (p. 383).
- **Headers** (Table VI B.1, pp. 385–387): `EXTERnal R-function parameters follow` (3),
  `BROADening parameters may be varied` (4), `NORMAlization and background are next` (6; flags
  −1/0/1/3, optional uncertainty line, p. 398), `RADIUs parameters follow` (7) / `Channel RADIUS
  PARAMETERS FOLLOW` (7a), `ISOTOpic abundances and masses` (10), `BACKGround functions` (13).
- **Priors** (pp. 427–432): `EXPLIcit uncertainties and correlations follow` (absolute; NN = resonance
  line number with MM = parameter index; radius 4000+n, normalization 3000+n; correlations through KK,
  LL), `RELATive uncertainties follow`, `PRIOR uncertainties follow in key word format` (`RELAtive=`,
  `ABSOlute=`, `GRoup=`, `CHannel=`, `PP=`, `L=`, `EMIN=`, `EMAX=`). Uncertainty on E_λ alone: `ENERGY
  UNCERTAINTIES are at end of line in par file` + columns 68–80 (pp. 338, 390).
- **Method** (pp. 213–226): a linearized Bayes update; ITMAX iterations re-expand around the current
  values. The LPT prints "CUSTOMARY CHI SQUARED" (χ²_LS) and "BAYESIAN CHI SQUARED", each also per
  NDAT. χ²_LS is always larger, and falls towards χ²_Bayes in a good fit. A large χ²_Bayes points to the
  model or the data (spins, background, multiple scattering), not to more iterations (p. 221).
- **Pitfalls stated in the manual**:
  - Results depend on the priors (p. 606, footnote). The default E_λ prior can be far too large; large
    E_λ priors let resonances swap places (pp. 267, 603, 606).
  - True least squares (infinite prior) needs the M+W scheme: `USE LEAST SQUARES TO define prior
    parameter covariance matrix`, `REMEMBER ORIGINAL PArameter values`, `READ Y AND W MATRICEs`, and
    possibly `TAKE BABY STEPS WITH least-squares method` (pp. 267–268, test `tr163`).
  - Sequential fits (the PAR+COV of one run fed into the next) depend on the order of the data sets.
    Repeating the sequence N times shrinks the covariance by N, so multiply uncertainties by √N
    (p. 598). Using the same data twice has the same effect (p. 605).
  - `DIVIDE DATA INTO REGions` can cut through a resonance (p. 342).
  - The output covariance is "widely regarded as too small"; enlarge it deliberately (IV.E.6,
    p. 599). Enter systematic uncertainties as PUPs (flag 3 on normalization, background, thickness)
    or as an implicit data covariance (p. 597).
  - Posterior/prior uncertainty ≈ 1: the data do not constrain the parameter. < 0.1: well constrained.
    > 1: a numerical problem (p. 606).
  - Outside levels must be represented, by dummy resonances or the external R-function, or the data
    cannot be fitted (p. 594).

## 5. Checks after a run (XI.A–B, pp. 593–603)

1. Read `SAMMY.LPT` every time. Check that every command was recognized and that parameter values
   are as intended (factors of 10; eV and meV). Error messages are at the end (pp. 477, 601).
2. Start with no-Bayes runs (`DO NOT SOLVE BAYES Equations`, `GENERATE PLOT FILE AUtomatically`,
   `PRINT ALL INPUT PARAmeters`) until theory and data roughly agree. Plot `SAMMY.LST` (p. 595).
3. Weighted residuals far above the rest mean unrealistically small uncertainties; jumps mean format
   errors (p. 595). Zero uncertainties are never allowed; VMIN (INP card 7) sets a floor (p. 603).
4. Broadening: start at 300 K with a Gaussian resolution (p. 596). Test the auxiliary grid with
   NXTRA = 1 (card 2): the broadened values must not change (p. 597). The grid is the analyst's
   responsibility (p. 115). Fit transmission rather than total cross section (p. 593).
5. Compare χ²_LS and χ²_Bayes per point, and follow the parameter path with the default
   `DO NOT SUPPRESS ANY intermediate printout` (p. 596).
6. Common failures (Table XI B.1, p. 603): "matrix nearly singular" (start values far off, priors
   too large, too few points); divide check or overflow (a zero where none is allowed); cryptic crash
   (too many points, mistyped file name); parameters run away (missing background R-matrix or dummy
   levels, wrong spins, unrealistic uncertainties, region split in a resonance, E_λ priors too
   large). To isolate a problem: smaller energy range, fewer varied parameters, no normalization,
   background or broadening (p. 601).

## 6. ENDF, AZURE2 and Ferdinand

- **ENDF File 2 in** (VI.F.3, pp. 467–468): keep INP card sets 1–8 only and put `INPUT IS ENDF/B
  FILE  MAT=abcd` in card set 3. Give the ENDF file where the PAR file is asked for. Without `MAT=`, the
  file must contain only File 2 of that material. The first 20 characters, `INPUT IS ENDF/B FILE`,
  select the command, so the form in `evaluated-nuclear-data/references/pitfalls.md` is valid; the
  command table writes `INPUT IS ENDF/B FILE 2` (pp. 337, 357). `USE ENERGY RANGE FROm endf/b
  file 2` takes the ENDF energy range. The run writes `SAMNDF.INP` (card 10.1), `SAMNDF.PAR` and
  `SAMQUA.PAR` for reuse. Only isotopic files work. Delete SLBW/MLBW commands from `SAMNDF.INP` before
  a new evaluation (pp. 468, 594); spins and parities from formats other than LRF=7 are not reliable
  (p. 594). The MF3 background is not in File 2: add it before comparing with NJOY (`pitfalls.md`).
- **ENDF out** (pp. 461–466): `ENDF/B-VI FILE 2 IS wanted` (or `ENDF`), with an ndf file given
  where the data file name is asked for. Prefer `NDF FILE IS IN KEY-Word Format` (keys `Z`, `A`,
  `Mat`, `LRF` = 1/2/3/7, `LCOmp`, ...). Output: `SAMMY.NDF`. For File 32, `PUT COVARIANCE MATRIx into
  endf file 32` (key-word ndf only) writes `SAMMY.N32`. An empty spin group needs LRF=7 (p. 607).
- **AZURE2 ↔ SAMMY**: there is no direct converter. Ferdinand (`~/Research/60_Codes/ferdinand`,
  README v0.50) reads `fresco, sfresco, eda, amur, rac, endf, azure, gnd=gnds=xml` and writes `fresco,
  sfresco, eda, hyrma, endf, azure, gnd=gnds=xml, tex`. SAMMY is not a format there, so the route is
  ENDF File 2 LRF=7: SAMMY (ndf `LRF=7`) → ENDF → Ferdinand → AZURE2, and back. Check boundary
  conditions (Ferdinand `-b Brune|L|X`; SAMMY default B = −l, p. 327) and widths vs amplitudes
  (`-a`, `-G`). Ferdinand fails on files without a resolved range (`pitfalls.md`). Untested here,
  because SAMMY does not run (§7).

## 7. Local installation (checked 2026-10-28)

- Executable: `~/Research/60_Codes/SAMMY/build/bin/sammy`, with auxiliary codes (`samrml`, `samqua`,
  `suggel`, `samamx`, ...) in the same folder. It is not on `PATH`. `build-release/` holds only a
  CMake cache. Tests: `samtry/trNNN/testNNN` (csh) with reference `answers/`.
- **It does not run.**
  1. The rpaths point to the deleted `~/Desktop/R-Matrix/IAEA/codes/SAMMY/sammy/build/...`, so dyld
     aborts with "Library not loaded: @rpath/libsammyLib.dylib". The libraries exist in `build/lib`,
     `build/external/openScale/repo/lib` and `.../external/gnds/src`.
  2. With `DYLD_LIBRARY_PATH` set to those folders (no relinking), the libraries load, but they come
     from a Debug build linked against AddressSanitizer (`libclang_rt.asan_osx_dynamic.dylib`). The
     process hangs in `__asan::InitializeShadowMemory` before `main`, also with the ASan runtime
     preloaded. Test `tr001a` wrote nothing in > 7 min.
  3. `CMakeLists.txt` already has ASan commented out ("ASan deadlocks in its initializer on macOS
     15+"), but the libraries (Nov 2025) were not rebuilt; only `sammy` was relinked (9 Sep).
- Fix (not done): a clean non-ASan Release rebuild. Then run `samtry/tr001/test001` in a scratch copy
  and compare with `answers/raa.lpt`.
- Consequence: everything above comes from the manual and the test inputs. No keyword has been
  exercised on this machine.
