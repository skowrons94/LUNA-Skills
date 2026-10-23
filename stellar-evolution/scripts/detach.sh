#!/usr/bin/env bash
# Run a long job (a MESA grid driver, a single run) in its own systemd user unit, outside the shell
# or agent session that starts it.
#
#   detach.sh UNIT_NAME [--env FILE]... -- command [args...]
#   systemctl --user status UNIT_NAME ; journalctl --user -u UNIT_NAME ; systemctl --user stop UNIT_NAME
#
# Why: processes started from a terminal or agent live in that session's cgroup scope, and setsid or
# nohup do not move them out. Many distributions set DefaultOOMPolicy=stop, so a single OOM kill of
# one MESA run stops the whole scope: the session, the driver and every other run. Here the job gets
# its own unit with OOMPolicy=continue, inside mesa.slice, whose MemoryMax (total RAM minus
# MESA_RESERVE_GB, default 2.5) keeps out-of-memory events inside the slice. The working directory
# is kept; each --env FILE is sourced first (environment files, conda activate scripts).
# Needs systemd and `loginctl enable-linger $USER` for jobs to survive logout.
#
# MESA_KSM=1 (needs sudo): the job runs as a system unit for $USER with MemoryKSM=yes, and ksmd is
# switched on. Every MESA run loads its own copy of the same EOS tables (FreeEOS cache files, ~134 MB
# each, up to several GB per run); kernel samepage merging keeps one copy of identical pages across
# all runs of the unit. Results are unchanged (same bytes); ksmd costs some CPU. User units cannot
# use MemoryKSM (needs CAP_SYS_RESOURCE). The system mesa.slice has its own MemoryMax.
set -euo pipefail
unit=${1:?usage: detach.sh UNIT_NAME [--env FILE]... -- command}; shift
envs=()
while [ "${1:-}" = "--env" ]; do envs+=("$2"); shift 2; done
[ "${1:-}" = "--" ] && shift
[ $# -gt 0 ] || { echo "no command" >&2; exit 2; }
total_kb=$(awk '/MemTotal/{print $2}' /proc/meminfo)
reserve_kb=$(awk -v g="${MESA_RESERVE_GB:-2.5}" 'BEGIN{print int(g*1048576)}')
max_mb=$(( (total_kb - reserve_kb) / 1024 ))
pre=""
for f in "${envs[@]}"; do pre+="source $(printf %q "$f"); "; done
cmd=$(printf '%q ' "$@")
if [ "${MESA_KSM:-0}" = 1 ]; then
  sudo sh -c 'echo 1 > /sys/kernel/mm/ksm/run; echo 1000 > /sys/kernel/mm/ksm/pages_to_scan'
  sudo systemd-run --unit="$unit" --slice=mesa.slice --collect -p User="$(id -un)" \
    -p WorkingDirectory="$PWD" -p MemoryKSM=yes -p OOMPolicy=continue -p "MemoryMax=${max_mb}M" \
    -E HOME="$HOME" -E USER="$(id -un)" -E PATH="$PATH" \
    bash -c "${pre}exec $cmd"
  sudo systemctl set-property --runtime mesa.slice "MemoryMax=${max_mb}M"
  echo "started system unit $unit (KSM) in mesa.slice (MemoryMax ${max_mb} MB); logs: journalctl -u $unit"
  exit 0
fi
systemd-run --user --unit="$unit" --slice=mesa.slice --same-dir --collect \
  -p OOMPolicy=continue -p "MemoryMax=${max_mb}M" \
  -E HOME="$HOME" -E USER="${USER:-$(id -un)}" -E PATH="$PATH" \
  bash -c "${pre}exec $cmd"
systemctl --user set-property --runtime mesa.slice "MemoryMax=${max_mb}M" OOMPolicy=continue 2>/dev/null || \
  systemctl --user set-property --runtime mesa.slice "MemoryMax=${max_mb}M"
echo "started $unit in mesa.slice (MemoryMax ${max_mb} MB); logs: journalctl --user -u $unit"
