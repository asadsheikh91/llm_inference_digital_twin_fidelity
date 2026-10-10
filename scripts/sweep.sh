#!/usr/bin/env bash
# Task 1.2 sweep: a100, sarathi, splitwise_conv, README flags; 2 models x 4 QPS x seeds.
# Usage: sweep.sh "<seeds>"   e.g. sweep.sh "42 43 44"
set -uo pipefail
SEEDS="${1:-42 43 44}"
P1=~/fidelity-phase1
LOG="$P1/logs/phase1_1.2_sweep.log"
for MODEL in meta-llama/Llama-2-7b-hf meta-llama/Meta-Llama-3-8B; do
  SHORT=$(basename "$MODEL")
  # first run of a model with a cold predictor cache trains RF models: use 2 threads to limit RAM
  if [ "$MODEL" = "meta-llama/Llama-2-7b-hf" ]; then export VIDUR_TRAIN_THREADS=2; else export VIDUR_TRAIN_THREADS=4; fi
  for QPS in 2 4 6.45 8; do
    for SEED in $SEEDS; do
      RUN="sweep_${SHORT}_qps${QPS}_seed${SEED}"
      echo "[$(date -Is)] sweep launching $RUN (VIDUR_TRAIN_THREADS=$VIDUR_TRAIN_THREADS)" >> "$LOG"
      "$P1/scripts/run_vidur.sh" "$MODEL" "$QPS" "$SEED" "$RUN" 1.2_sweep
      echo "[$(date -Is)] sweep finished $RUN rc=$?" >> "$LOG"
    done
  done
done
echo "[$(date -Is)] SWEEP DONE" >> "$LOG"
