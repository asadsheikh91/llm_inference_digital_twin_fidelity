#!/usr/bin/env bash
# Log RAM every 30 s to $1. If MemAvailable < 1 GiB, log ALERT, kill the process matching $2, and exit.
out="$1"; pattern="$2"
echo "timestamp,mem_free_kib,mem_available_kib,swap_free_kib" > "$out"
while true; do
  f=$(awk '/^MemFree:/{print $2}' /proc/meminfo); a=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo); s=$(awk '/^SwapFree:/{print $2}' /proc/meminfo)
  echo "$(date -Is),$f,$a,$s" >> "$out"
  if [ "$a" -lt 1048576 ]; then echo "ALERT $(date -Is) MemAvailable ${a} KiB < 1 GiB; killing '$pattern'" | tee -a "$out"; pkill -f "$pattern"; exit 0; fi
  sleep 30
done
