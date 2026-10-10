#!/usr/bin/env bash
# Sample total RSS (kB) of all ~/.venv-vidur python processes and system MemAvailable every 2 s.
# Usage: mem_sampler.sh <outfile>   (runs until killed)
OUT="$1"
echo "iso_time,vidur_total_rss_kb,vidur_nproc,mem_available_kb" > "$OUT"
while true; do
  read -r RSS N < <(ps -eo rss=,args= | awk '/\.venv-vidur\/bin\/python/ && !/awk/ {s+=$1; n++} END{print s+0, n+0}')
  AV=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
  echo "$(date -Is),$RSS,$N,$AV" >> "$OUT"
  sleep 2
done
