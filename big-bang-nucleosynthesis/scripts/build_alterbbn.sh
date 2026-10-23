#!/usr/bin/env bash
# Build AlterBBN v2.x twice from the unmodified tarball: DEST/alterbbn_vX (patched: rate tables,
# JSON driver, reproducible Monte Carlo, precision override) and DEST/alterbbn_vX_orig (unpatched
# library + the same driver, for the identity check).
#   build_alterbbn.sh TARBALL DEST
# Patches (scripts/patch/): rate_override.c (forward rates from tables listed in $ALTERBBN_RATES),
# bbn_driver.c (central | mc), dump_rates.c (built-in rates as tables). ALTERBBN_PREC sets the
# relative precision of the adaptive Runge-Kutta methods (failsafe >= 10).
set -euo pipefail
tgz=$(realpath "${1:?usage: build_alterbbn.sh TARBALL DEST}"); dest=${2:?DEST}
P=$(cd "$(dirname "$0")" && pwd)/patch
rm -rf "$dest" && mkdir -p "$dest" && cd "$dest"
tar xzf "$tgz"
top=$(tar tzf "$tgz" | awk -F/ 'NR==1{t=$1} END{print t}')   # read the whole listing (no SIGPIPE)
cp -r "$top" "${top}_orig"
S=$top/src
cp "$P/rate_override.c" $S/
sed -i '1i #include "rate_override.c"' $S/bbnrate.c
n=$(grep -c 'for(ie=12;ie<=NNUCREAC;ie++) f\[ie\]=max(0.,f\[ie\]);' $S/bbnrate.c)
[ "$n" = 1 ] || { echo "rate patch anchor found $n times" >&2; exit 1; }
sed -i 's|    for(ie=12;ie<=NNUCREAC;ie++) f\[ie\]=max(0.,f\[ie\]);|    rate_override(f,ferrlow,ferrhigh,T9,paramrelic->err>0);\n&|' $S/bbnrate.c
n=$(grep -c 'double dt=1.e-10\*s_to_GeV; /\* initial time step \*/' $S/bbn.c)
[ "$n" = 2 ] || { echo "prec anchor found $n times (expected 2: RK4 and RK4-5 blocks)" >&2; exit 1; }
sed -i 's|\(\s*\)double dt=1.e-10\*s_to_GeV; /\* initial time step \*/|\1if(getenv("ALTERBBN_PREC")) prec=atof(getenv("ALTERBBN_PREC"));\n&|' $S/bbn.c
sed -i 's|^libbbn.a(bbnrate.o): bbnrate.c|& rate_override.c|' $S/Makefile
for d in "${top}_orig" "$top"; do
  (cd $d && make > make.log 2>&1 && make stand_cosmo alter_eta >> make.log 2>&1
   cp "$P/bbn_driver.c" "$P/dump_rates.c" .
   gcc -O3 -fopenmp -std=c99 -D_DEFAULT_SOURCE -o bbn_driver.x bbn_driver.c src/libbbn.a -lm
   gcc -O2 -fopenmp -std=c99 -D_DEFAULT_SOURCE -o dump_rates.x dump_rates.c src/libbbn.a -lm)
done
echo "built: $dest/$top (patched), $dest/${top}_orig"
