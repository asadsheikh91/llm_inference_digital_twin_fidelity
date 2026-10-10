#!/usr/bin/env bash
# Sample total GPU memory used (MiB) every 0.5 s to the given CSV until killed.
# WSL does not expose per-process GPU memory, so this is device-wide (includes the Windows display).
out="$1"
echo "timestamp,memory_used_mib,memory_total_mib" > "$out"
while true; do
  echo "$(date +%Y-%m-%dT%H:%M:%S.%N | cut -c1-23),$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | tr -d ' ')" >> "$out"
  sleep 0.5
done
