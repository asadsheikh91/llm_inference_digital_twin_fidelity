#!/usr/bin/env bash
# Run one Vidur simulation with the README example flags (a100, sarathi, RF predictor, 16k context).
# Usage: run_vidur.sh <model> <qps> <seed> <run_name> <logname>
# Seed is applied to --seed, --synthetic_request_generator_config_seed and
# --trace_request_length_generator_config_seed (see RESULTS.md: the Poisson interval generator
# draws from the global `random` module, which the synthetic generator re-seeds with its own seed).
set -euo pipefail
MODEL="$1"; QPS="$2"; SEED="$3"; RUN="$4"; LOGNAME="$5"
P1=~/fidelity-phase1
VD=~/vidur
LOG="$P1/logs/phase1_${LOGNAME}.log"
OUT="$P1/results/runs/$RUN"
mkdir -p "$OUT"
export WANDB_MODE=disabled
export PYTHONPATH="$VD"
PY=~/.venv-vidur/bin/python
CMD=(nice -n 10 /usr/bin/time -v "$PY" -m vidur.main
  --seed "$SEED"
  --replica_config_device a100
  --replica_config_model_name "$MODEL"
  --cluster_config_num_replicas 1
  --replica_config_tensor_parallel_size 1
  --replica_config_num_pipeline_stages 1
  --request_generator_config_type synthetic
  --synthetic_request_generator_config_seed "$SEED"
  --synthetic_request_generator_config_num_requests 512
  --length_generator_config_type trace
  --trace_request_length_generator_config_seed "$SEED"
  --trace_request_length_generator_config_max_tokens "${VIDUR_MAX_TOKENS:-16384}"
  --trace_request_length_generator_config_trace_file "$VD/data/processed_traces/splitwise_conv.csv"
  --interval_generator_config_type poisson
  --poisson_request_interval_generator_config_seed "$SEED"
  --poisson_request_interval_generator_config_qps "$QPS"
  --replica_scheduler_config_type sarathi
  --sarathi_scheduler_config_batch_size_cap 512
  --sarathi_scheduler_config_chunk_size 512
  --random_forrest_execution_time_predictor_config_prediction_max_prefill_chunk_size 16384
  --random_forrest_execution_time_predictor_config_prediction_max_batch_size 512
  --random_forrest_execution_time_predictor_config_prediction_max_tokens_per_request 16384
  --random_forrest_execution_time_predictor_config_compute_input_file "$VD/data/profiling/compute/{DEVICE}/{MODEL}/mlp.csv"
  --random_forrest_execution_time_predictor_config_attention_input_file "$VD/data/profiling/compute/{DEVICE}/{MODEL}/attention.csv"
  --random_forrest_execution_time_predictor_config_all_reduce_input_file "$VD/data/profiling/network/{NETWORK_DEVICE}/all_reduce.csv"
  --random_forrest_execution_time_predictor_config_send_recv_input_file "$VD/data/profiling/network/{NETWORK_DEVICE}/send_recv.csv"
  --random_forrest_execution_time_predictor_config_cpu_overhead_input_file "$VD/data/profiling/cpu_overhead/{NETWORK_DEVICE}/{MODEL}/cpu_overheads.csv"
  --random_forrest_execution_time_predictor_config_num_training_job_threads "${VIDUR_TRAIN_THREADS:-4}"
  --no-metrics_config_store_plots
  --metrics_config_output_dir "$OUT"
  --metrics_config_cache_dir "$P1/cache"
)
cd "$P1"
{
  echo "=== [$(date -Is)] START run=$RUN model=$MODEL qps=$QPS seed=$SEED"
  echo "cwd=$(pwd) WANDB_MODE=$WANDB_MODE PYTHONPATH=$PYTHONPATH"
  printf 'CMD:'; printf ' %q' "${CMD[@]}"; echo
} >> "$LOG"
START=$(date +%s.%N)
set +e
"${CMD[@]}" >> "$LOG" 2>&1
RC=$?
set -e
END=$(date +%s.%N)
echo "=== [$(date -Is)] END run=$RUN rc=$RC wall_seconds_date=$(echo "$END - $START" | bc)" >> "$LOG"
exit $RC
