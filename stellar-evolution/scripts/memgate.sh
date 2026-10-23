#!/usr/bin/env bash
# Start a command only when enough memory is free, one start at a time.
#
#   memgate.sh GB [SETTLE_S] -- command [args...]
#
# Waits until MemAvailable >= GB, starts the command, and keeps other memgate starts waiting for
# SETTLE_S seconds (default 180) while the new run grows to its working size (a MESA run loads its
# EOS/opacity tables during the first minutes). Then waits for the command and returns its status.
# Use it inside `xargs -P N` so N caps the cores and GB caps the memory:
#   ls specs/*.json | xargs -P 18 -I{} memgate.sh 3 -- python3 run.py run {}
# Without /proc/meminfo (macOS) the command just runs.
set -u
need=${1:?usage: memgate.sh GB [SETTLE_S] -- command}; shift
settle=180
if [ "${1:-}" != "--" ]; then settle=$1; shift; fi
[ "${1:-}" = "--" ] && shift
[ -r /proc/meminfo ] || exec "$@"
# if memory still runs out, the kernel kills a run (inherited by MESA's child processes), not the
# shell, the driver or the agent session that started it
echo "${MEMGATE_OOM_ADJ:-800}" > /proc/self/oom_score_adj 2>/dev/null || true
lock=${MEMGATE_LOCK:-/tmp/memgate.${USER:-$(id -u)}.lock}
exec 9>"$lock"
flock 9
while [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -lt "$need" ]; do sleep 30; done
"$@" 9>&- &
pid=$!
sleep "$settle"
flock -u 9
exec 9>&-
wait "$pid"
