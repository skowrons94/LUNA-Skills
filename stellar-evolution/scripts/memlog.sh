#!/usr/bin/env bash
# Log the memory of running MESA processes against model number, to size a grid from measurements.
#
#   memlog.sh OUT.tsv [INTERVAL_S]
#
# Every INTERVAL_S (default 60) one row per running ./star: time, run directory, OpenMP threads,
# model number, resident memory (RSS) and swapped-out memory of the run (MB), MemAvailable and, if
# zram swap is active, the data it holds and their compressed size (MB). A large swapped share with a
# small compressed size means most of a run's memory is idle and compressible (EOS tables).
out=${1:?usage: memlog.sh OUT.tsv [INTERVAL_S]}; dt=${2:-60}
[ -s "$out" ] || printf "time\trun\tthreads\tmodel\trss_mb\tswap_mb\tavail_mb\tzram_data_mb\tzram_compr_mb\n" > "$out"
while true; do
  av=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
  zd=0; zc=0
  if [ -r /sys/block/zram0/mm_stat ]; then read -r zd zc _ < /sys/block/zram0/mm_stat; zd=$((zd/1048576)); zc=$((zc/1048576)); fi
  for p in $(pgrep -x star); do
    d=$(readlink "/proc/$p/cwd") || continue
    rss=$(awk '/VmRSS/{print int($2/1024)}' "/proc/$p/status" 2>/dev/null)
    sw=$(awk '/VmSwap/{print int($2/1024)}' "/proc/$p/status" 2>/dev/null)
    th=$(ls "/proc/$p/task" 2>/dev/null | wc -l)
    m=$(tail -1 "$d/LOGS/history.data" 2>/dev/null | awk '{print $1}')
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$(date +%FT%T)" "$(basename "$d")" "$th" "${m:-0}" \
      "${rss:-0}" "${sw:-0}" "$av" "$zd" "$zc" >> "$out"
  done
  sleep "$dt"
done
