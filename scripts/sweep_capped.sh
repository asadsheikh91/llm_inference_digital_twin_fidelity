#!/usr/bin/env bash
# Llama-2-7b rerun with request length capped at 4096 tokens (its max_position_embeddings and the
# max prefill/kv size in its a100 profiling data). Prediction-range flags stay at README values so the
# trained predictor cache from the original sweep is reused; only the workload changes.
# Usage: sweep_capped.sh "<seeds>"
set -uo pipefail
SEEDS="${1:-42 43 44}"
P1=~/fidelity-phase1
LOG="$P1/logs/phase1_1.6_capped.log"
export VIDUR_MAX_TOKENS=4096
export VIDUR_TRAIN_THREADS=2
MODEL=meta-llama/Llama-2-7b-hf
for QPS in 2 4 6.45 8; do
  for SEED in $SEEDS; do
    RUN="capped4096_Llama-2-7b-hf_qps${QPS}_seed${SEED}"
    echo "[$(date -Is)] capped launching $RUN (VIDUR_MAX_TOKENS=$VIDUR_MAX_TOKENS VIDUR_TRAIN_THREADS=$VIDUR_TRAIN_THREADS)" >> "$LOG"
    "$P1/scripts/run_vidur.sh" "$MODEL" "$QPS" "$SEED" "$RUN" 1.6_capped
    echo "[$(date -Is)] capped finished $RUN rc=$?" >> "$LOG"
  done
done
echo "[$(date -Is)] CAPPED DONE" >> "$LOG"
