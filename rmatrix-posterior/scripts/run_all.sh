#!/bin/sh
# NUTS (4 chains) and emcee (4 workers) side by side on the same posterior, one thread each.
#   sh run_all.sh "--azr fit.azr --sav output/param.sav --cwd . --bg-energy 25" runs/nominal [warmup] [draws] [emcee steps]
# Needs <out>/map.npz (find_map.py).  Stop: kill $(cat <out>/logs/*.pid)   Resume: run this again.
SKILL=$(cd "$(dirname "$0")" && pwd)
FIT=$1; OUT=$2
WARM=${3:-500}; DRAWS=${4:-1000}; STEPS=${5:-4000}
[ -f "$OUT/map.npz" ] || { echo "$OUT/map.npz missing: run find_map.py first"; exit 1; }
mkdir -p "$OUT/logs"
export OMP_NUM_THREADS=1
for k in 0 1 2 3; do
  nohup python3 "$SKILL/run_chain.py" $FIT --out "$OUT" --chain $k --warmup $WARM --draws $DRAWS \
        --max-depth 8 >> "$OUT/logs/nuts_$k.log" 2>&1 &
  echo $! > "$OUT/logs/nuts_$k.pid"
done
nohup python3 "$SKILL/run_emcee.py" $FIT --out "$OUT" --walkers 416 --steps $STEPS --procs 4 --thin 5 \
      >> "$OUT/logs/emcee.log" 2>&1 &
echo $! > "$OUT/logs/emcee.pid"
echo "started: logs in $OUT/logs"
