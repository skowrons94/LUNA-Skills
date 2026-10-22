# Installing MESA

MESA is two downloads: the MESA SDK (compilers and libraries, ~250 MB) and the MESA source (~2.3 GB zip, ~20 GB after installation with its data). Releases are on Zenodo: the MESA concept record `10.5281/zenodo.2602941` (the latest version is listed there), and the SDK records linked from the SDK page (Rich Townsend, University of Wisconsin). Record URL, version and MD5/SHA-256 of both downloads in `docs/ENVIRONMENT.md` of the project, or in a `SOURCE.txt` next to them.

Put MESA, its SDK and its caches outside the skill and outside synced folders, on a disk with ≥ 30 GB free. One installation serves every project; projects record which one they used.

## macOS on Apple silicon, without administrator rights

The SDK ships as a `.pkg` that installs to `/Applications/mesasdk`. The package is relocatable, so it can be expanded into a user directory instead:

```bash
cd /path/to/MESA
pkgutil --expand-full downloads/mesasdk-aarch64-macos-<ver>.pkg sdk-expanded
mv sdk-expanded/mesasdk.pkg/Payload/mesasdk ./mesasdk && rm -rf sdk-expanded
unzip -q downloads/mesa-<ver>.zip            # gives mesa-<ver>/
```

Then write an environment file (`mesa_env.sh`) and source it only in shells that build or run MESA:

```bash
export MESASDK_ROOT=/path/to/MESA/mesasdk
export MESA_DIR=/path/to/MESA/mesa-<ver>
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-4}
unset SDKROOT                      # see below
source $MESASDK_ROOT/bin/mesasdk_init.sh
export PATH=$PATH:$MESA_DIR/scripts/shmesa
```

Check the compilers before the long build. A Fortran program with `-fopenmp` and a C program including `<stdio.h>` must both compile and run with the SDK's `gfortran` and `gcc`.

Build in the background at low priority, and keep the log:

```bash
bash -c 'source mesa_env.sh && cd $MESA_DIR && nice -n 10 ./install' > build.log 2>&1
grep -n "MESA installation was successful" build.log
```

It takes roughly 30–60 minutes on an 8-core laptop.

### Known failure: `unknown type name 'FILE'` while compiling `utils_c_system`

**Cause.** `SDKROOT` points to an Xcode SDK newer than the one the MESA SDK was built against (e.g. Xcode 27 with SDK 26.x). GCC's fixed headers then clash with Apple's.

**Fix.** The SDK carries its own `sysroot`, so `unset SDKROOT` (do not set it to an Xcode SDK). The MESA documentation suggests `export SDKROOT=$(xcrun --show-sdk-path)` for a `library 'z' not found` error on macOS 15. Apply that only if that error appears, and only with an Xcode SDK matching the MESA SDK's macOS version. After changing the environment, run `./clean` before `./install`.

Linker warnings `building for macOS-11.0, but linking with dylib ... built for newer version 26.0` are harmless.

## Linux

Install the Linux SDK tarball in the same way (`tar xf` into a user directory, same environment file without the `SDKROOT` line). On shared machines, set `OMP_NUM_THREADS` from the current load and run with `nice`.

## Check the installation

1. `grep "MESA installation was successful" build.log`.
2. Run a short test-suite case from a copy (never inside `$MESA_DIR`), e.g. `custom_rates` with `MESA_SKIP_OPTIONAL=t` (~15 min). `mesa.py check-run` must report its physical termination code and an energy error well below 10⁻³.
3. Record in `docs/ENVIRONMENT.md`: MESA version (`$MESA_DIR/data/version_number`), SDK version (`$MESASDK_VERSION`), paths, compiler, and the test case run.

## Caches

MESA caches rates, EOS and opacity tables under `$MESA_DIR/data/*/cache`. A rate cache built with one rate is silently reused with another. Every run that changes a rate sets `rates_cache_dir = './rates_cache'` in `&star_job` (run-local cache), or the shared cache is cleared with `$MESA_DIR/empty_caches`.
