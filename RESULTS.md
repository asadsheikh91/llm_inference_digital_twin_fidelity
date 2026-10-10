# Phase 1 (Tier A): Vidur baseline reproduction, CPU only

Branch `phase1-tier-a`, worktree `~/fidelity-phase1`. Every number below is copied from a file under
`results/` or `logs/`; the source is named next to it. Times are wall clock on the machine below.

## Status

| Task | Status | Main output |
|---|---|---|
| 1.1 README example | Passed on attempt 3 (attempt 1 OOM-killed, attempt 2 lost plot/CDF outputs, see Issues) | `results/runs/readme_warm_llama3-8b_qps6.45_seed42/`, `logs/phase1_1.1_readme.log` |
| 1.2 Sweep, 2 models x 4 QPS x 3 seeds | Passed, 24/24 runs rc=0, 512/512 requests completed in each | `results/runs/sweep_*`, `logs/phase1_1.2_sweep.log` |
| 1.3 collect.py | Done | `scripts/collect.py`, `results/baseline.csv`, `results/baseline_agg.csv` |
| 1.4 Paper numbers | Partial: text statements and LLaMA2-7B bar labels extracted; per-trace mapping and bar heights TODO | `results/paper_reported.csv`, `data/paper_2405.05465/paper.txt` |
| 1.5 This file | Done | `RESULTS.md`, `results/tables.md` |
| 1.6 Llama-2-7b rerun, trace max_tokens 4096 | Passed, 12/12 runs rc=0, 512/512 requests completed in each, max request 4095 tokens | `results/baseline_llama2_capped4096.csv`, `results/baseline_llama2_capped4096_agg.csv`, `logs/phase1_1.6_capped.log` |
| 1.6 Predictor cache artifacts | Copied to `~/fidelity-artifacts/` (outside git), 132/132 files verified with `sha256sum -c` | `results/predictor_cache_manifest.csv`, `results/predictor_cache.sha256`, `logs/phase1_1.6_artifacts.log` |
| 1.6 Cleanup | `cache_oomkilled_run1/` deleted after checking it is not cited as evidence | `logs/phase1_1.6_cleanup.log` |

## Reproduction status

What Tier A shows:

- Vidur at commit `abae7f63aa857300f5cdc6f5e0d27860cd24721b` installs (as a source tree on `PYTHONPATH`) and runs on this CPU-only machine with the README configuration, after the two workarounds listed under Deviations (training thread cap, plots off).
- Every simulation completed all requests: 512 of 512 in each of the 24 sweep runs, the 12 capped Llama-2-7b runs and the README run (`num_requests_completed` in `results/baseline.csv` and `results/baseline_llama2_capped4096.csv`).
- For a fixed predictor cache and seed, the simulator output is deterministic: the README run and the sweep run with the same model, QPS and seed produce byte-identical `request_metrics.csv`.
- The simulated TTFT, TPOT and request E2E distributions for Llama-2-7b and Meta-Llama-3-8B on a100 at QPS 2, 4, 6.45 and 8 are recorded below as a baseline for later phases.

What Tier A does not show:

- It does not reproduce the paper's fidelity numbers. Those are percentage errors between Vidur's prediction and real A100 GPU runs; this phase has no real-GPU measurements, so no error was computed. Real-GPU ground truth is planned for Phase 2.
- It does not use the paper's fidelity setup (Chat-1M, Arxiv-4K and BWB-4K traces, default vLLM scheduler, arrival rates set relative to measured capacity), so even the simulated numbers are not the paper's simulated numbers.
- It does not show that the trained predictors are reproducible from scratch: predictor training is not seeded (Differences item 5), so the results depend on the archived cache in `~/fidelity-artifacts/`.

## What CPU contention can and cannot affect

The machine was shared with another agent's GPU and RAM workload during all runs.

- Can be affected: every wall-clock time and memory figure in this file (`/usr/bin/time -v` elapsed and max RSS, `results/sweep_walltimes.txt`, `results/capped_walltimes.txt`, the memory samples, and the sweep estimate built from them). These describe this machine under this load, not Vidur in general.
- Cannot be affected: the simulated metrics (TTFT, TPOT, request E2E and every other column of `request_metrics.csv`). They are computed from simulated time, which comes from the request generator and the trained predictors, not from host time. Supporting evidence: the README configuration run at different times under different load (1.1 attempt 2, 1.1 attempt 3, and the sweep) gave byte-identical `request_metrics.csv`.
- Indirect case: predictor training. Contention does not change the simulated metrics directly, but training is unseeded, so a retrained cache (for example after a crash) can give different predictors and therefore different simulated metrics. That is a reproducibility issue, not a contention effect, and is why the cache is archived.

## Environment

Source: `logs/phase1_env.log` (includes full `pip freeze` of `~/.venv-vidur`).

| Item | Value |
|---|---|
| OS | Ubuntu 22.04.5 LTS on WSL2, kernel 6.18.33.2-microsoft-standard-WSL2 |
| CPU | 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, 16 logical CPUs |
| RAM | MemTotal 10182304 kB (shared with another agent's vLLM process during these runs) |
| Python | 3.10.12 (`~/.venv-vidur`) |
| Vidur | `~/vidur`, branch main, commit `abae7f63aa857300f5cdc6f5e0d27860cd24721b`, remote https://github.com/microsoft/vidur.git, working tree clean (empty `git status --porcelain`) |
| Libraries | numpy 2.2.6, pandas 2.3.3, scikit-learn 1.7.2, scipy 1.15.3, joblib 1.6.0, plotly 7.1.0, plotly-express 0.4.1, kaleido 1.5.0, wandb 0.30.0, ddsketch 3.0.1, fasteners 0.20, matplotlib 3.10.9, seaborn 0.13.2 |
| Vidur install | Not pip-installed into `~/.venv-vidur`; run with `PYTHONPATH=~/vidur` |
| Env vars | `WANDB_MODE=disabled`, `PYTHONPATH=~/vidur` |

No package in `~/.venv-vidur` was changed. A separate throwaway venv in the session scratchpad was
created only to hold `pypdf==4.3.1` for reading the paper PDF (task 1.4).

## Exact commands

All runs go through `scripts/run_vidur.sh <model> <qps> <seed> <run_name> <logname>`, which runs from
`~/fidelity-phase1` with absolute input paths so nothing is written into `~/vidur`. The full expanded
command line of every run is logged on its `CMD:` line in `logs/phase1_1.1_readme.log` or
`logs/phase1_1.2_sweep.log`. Template:

```sh
WANDB_MODE=disabled PYTHONPATH=~/vidur nice -n 10 /usr/bin/time -v ~/.venv-vidur/bin/python -m vidur.main \
  --seed $SEED \
  --replica_config_device a100 \
  --replica_config_model_name $MODEL \
  --cluster_config_num_replicas 1 \
  --replica_config_tensor_parallel_size 1 \
  --replica_config_num_pipeline_stages 1 \
  --request_generator_config_type synthetic \
  --synthetic_request_generator_config_seed $SEED \
  --synthetic_request_generator_config_num_requests 512 \
  --length_generator_config_type trace \
  --trace_request_length_generator_config_seed $SEED \
  --trace_request_length_generator_config_max_tokens $MAX_TOKENS \
  --trace_request_length_generator_config_trace_file ~/vidur/data/processed_traces/splitwise_conv.csv \
  --interval_generator_config_type poisson \
  --poisson_request_interval_generator_config_seed $SEED \
  --poisson_request_interval_generator_config_qps $QPS \
  --replica_scheduler_config_type sarathi \
  --sarathi_scheduler_config_batch_size_cap 512 \
  --sarathi_scheduler_config_chunk_size 512 \
  --random_forrest_execution_time_predictor_config_prediction_max_prefill_chunk_size 16384 \
  --random_forrest_execution_time_predictor_config_prediction_max_batch_size 512 \
  --random_forrest_execution_time_predictor_config_prediction_max_tokens_per_request 16384 \
  --random_forrest_execution_time_predictor_config_{compute,attention,all_reduce,send_recv,cpu_overhead}_input_file <absolute ~/vidur/data/profiling/... path, same pattern as the default> \
  --random_forrest_execution_time_predictor_config_num_training_job_threads $THREADS \
  --no-metrics_config_store_plots \
  --metrics_config_output_dir ~/fidelity-phase1/results/runs/$RUN \
  --metrics_config_cache_dir ~/fidelity-phase1/cache
```

- 1.1: `scripts/run_vidur.sh meta-llama/Meta-Llama-3-8B 6.45 42 readme_warm_llama3-8b_qps6.45_seed42 1.1_readme`
- 1.2: `scripts/sweep.sh "42 43 44"` (models meta-llama/Llama-2-7b-hf and meta-llama/Meta-Llama-3-8B, QPS 2 4 6.45 8, seeds 42 43 44, sequential; THREADS=2 for Llama-2-7b, 4 for Llama-3-8B)
- 1.3: `~/.venv-vidur/bin/python scripts/collect.py` then `~/.venv-vidur/bin/python scripts/make_tables.py`
- 1.6: `scripts/sweep_capped.sh "42 43 44"` (Llama-2-7b, MAX_TOKENS=4096 via `VIDUR_MAX_TOKENS`, THREADS=2, QPS 2 4 6.45 8, seeds 42 43 44), then `~/.venv-vidur/bin/python scripts/collect.py --runs-glob 'results/runs/capped4096_*' --out results/baseline_llama2_capped4096.csv --agg-out results/baseline_llama2_capped4096_agg.csv`, `scripts/make_tables.py`, `scripts/update_results_md.py`

MAX_TOKENS is 16384 (README value) for 1.1 and 1.2 and 4096 for 1.6. Vidur's trace length generator
does not drop requests above the cap: it shrinks prefill and decode tokens proportionally so that their
sum fits (`vidur/request_generator/trace_request_length_generator.py`), so every run still has 512
requests. The predictor range flags (16384 / 512 / 16384) were kept at README values in 1.6 so the
trained Llama-2-7b cache from 1.2 was reused; `logs/phase1_1.6_capped.log` contains no `Trained model`
line.

Seeds: 42 is Vidur's default for every seed flag. Seed handling (found by reading the code, see Issues
item 5): `--seed` seeds `random`/`numpy` in `main.py`, but `SyntheticRequestGenerator.generate_requests`
re-seeds them with `--synthetic_request_generator_config_seed`, and the Poisson interval generator draws
from the global `random` module, so arrivals are controlled by the synthetic generator seed. Request
lengths are shuffled with `--trace_request_length_generator_config_seed`. The Poisson generator's own
seed field is not read by its code. The wrapper sets all four to the same value.

## 1.1 README example: time and memory

Sources: `logs/phase1_1.1_readme.log` (`/usr/bin/time -v`), `logs/phase1_1.1_readme_mem.csv`
(2 s samples of summed RSS of all `~/.venv-vidur` python processes plus MemAvailable).

| Attempt | Cache | Train threads | Plots | Result | Wall clock | Max RSS (largest single process, kB) | Peak summed RSS of process tree (kB) |
|---|---|---|---|---|---|---|---|
| 1 | cold | -1 (default, 16 workers) | on | Killed by kernel OOM killer, rc=137 | 13:45.45 | 3422572 | not sampled |
| 2 | cold | 4 | on | Simulation finished (`Simulation ended at: 85.97724680244782s`), `request_metrics.csv` written, then output crashed (Kaleido needs Chrome), exit status 0 | 17:26.43 | 4733720 | 8096212 (MemAvailable fell to 534240 kB) |
| 3 | warm | 4 | off | Completed, all outputs written | 0:30.30 | 4616580 | see `logs/phase1_1.1_readme_warm_mem.csv` |

The summed RSS double-counts shared pages, so it is an upper bound. Attempt 2 and attempt 3 produce
byte-identical `request_metrics.csv` (checked with `cmp`), and the sweep run
`sweep_Meta-Llama-3-8B_qps6.45_seed42` is byte-identical to attempt 3.

README example result (source: `results/baseline.csv`, row `sweep_Meta-Llama-3-8B_qps6.45_seed42`, whose
`request_metrics.csv` is byte-identical to `results/runs/readme_warm_llama3-8b_qps6.45_seed42/*/request_metrics.csv`):
512 of 512 requests completed;
TTFT P50 0.7861352998217725 s, P90 1.716575563624261 s, P99 2.6410766802431835 s;
TPOT P50 0.04637149310064115 s, P90 0.05216500848783811 s, P99 0.05299763417227775 s;
E2E P50 7.394115577664113 s, P90 21.242942110056227 s, P99 29.818169802845507 s.

## 1.2 Sweep time: estimate vs actual

Source: `logs/phase1_1.2_estimate.log`, `results/sweep_walltimes.txt`.

- Estimate given before starting: 1 cold run (1046.443398360 s, 1.1 attempt 2) + 23 warm runs (30.315123610 s each, 1.1 attempt 3) = 1743.691241390 s (29.06152068983333333333 min). Under 2 hours, so 3 seeds were run.
- Actual: sum of per-run wall times 1900.49 s (`logs/phase1_1.6_sums.log`); `SWEEP START` 18:23:56, `SWEEP DONE` 18:55:37. The Llama-2-7b cold run took 1197.043152332 s (19:57.02), longer than the estimate's cold term, because it trained with 2 threads instead of 4. Warm runs took between 22.396957739 s and 43.581230164 s.
- Largest single-process max RSS in the sweep: 5618496 kB (`sweep_Llama-2-7b-hf_qps4_seed44`). Peak summed RSS sample: 6070656 kB at 18:43:33, when MemAvailable was 2674900 kB (`logs/phase1_1.2_sweep_mem.csv`).

## 1.6 Capped rerun time: estimate vs actual

Source: `logs/phase1_1.6_capped_estimate.log`, `results/capped_walltimes.txt`, `logs/phase1_1.6_capped.log`.

- Estimate given before starting: 12 x 32.992442277 s (mean of the 11 warm Llama-2-7b sweep runs) = 395.909307321 s, assuming the predictor cache is reused.
- Actual: sum of per-run wall times 387.167 s (`logs/phase1_1.6_sums.log`); `CAPPED START` 19:08:29, `CAPPED DONE` 19:14:57. Per-run wall times from 28.574061841 s to 43.396065624 s. Largest single-process max RSS 5618344 kB (`capped4096_Llama-2-7b-hf_qps8_seed44`). No new OOM event in `dmesg`.

## Results

Metric definitions (from `~/vidur/docs/metrics.md` and `vidur/metrics/constants.py`; percentiles with
pandas `quantile`, the same call Vidur uses in `DataSeries.print_distribution_stats`):

- TTFT: `prefill_e2e_time`, f_r - a_r (docs name `prefill_time_e2e_cdf`)
- TPOT: `decode_time_execution_plus_preemption_normalized`, (c_r - f_r) / decode tokens, per request (docs item 16)
- E2E: `request_e2e_time`, c_r - a_r (docs name `request_e2e_time_cdf`)

Per-token inter-token delay (`decode_token_execution_plus_preemption_time`) is not reported:
`metrics_config_store_token_completion_metrics` defaults to False and the README command does not set it.

Full tables with all values: `results/tables.md` (generated from the CSVs by `scripts/make_tables.py`,
values copied as stored, no rounding). The tables below are inserted by `scripts/update_results_md.py`.
Mean and sample std (ddof=1) over seeds 42, 43, 44.

`range_note` is computed by `collect.py`: "outside profiled range" when the run's trace max_tokens is
larger than the max `prefill_chunk_size` in the model's a100 `attention.csv` (4096 for Llama-2-7b,
16384 for Meta-Llama-3-8B).

### Original sweep (trace max_tokens 16384; Llama-2-7b rows are outside profiled range)

Source files: `results/baseline.csv`, `results/baseline_agg.csv`. Kept unchanged except for the added
`max_tokens`, `profiled_max_prefill_chunk_size`, `range_note` and `max_request_num_tokens` columns
(metric values checked identical before and after). Llama-2-7b max request length 7037, 7207, 7052
tokens for seeds 42, 43, 44.

<!-- BEGIN TABLES_ORIGINAL -->
#### TTFT, seconds (source: results/baseline_agg.csv)

| model | max_tokens | range_note | qps | P50 mean | P50 std | P90 mean | P90 std | P99 mean | P99 std |
|---|---|---|---|---|---|---|---|---|---|
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 2.0 | 0.1052840762000002 | 0.0008269959752084195 | 0.37542574256716477 | 0.004545360509863857 | 0.5857987898398783 | 0.029429801936674285 |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 4.0 | 0.20127110929299497 | 0.048324657550082466 | 0.6874855780308016 | 0.10664801137620628 | 1.198852183409546 | 0.02255506665912669 |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 6.45 | 8.034868006638545 | 1.371182844914874 | 17.01922830826542 | 3.068252212329785 | 19.199816525875487 | 2.177705386550713 |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 8.0 | 14.318728488568269 | 1.169287472558086 | 28.622409667615496 | 2.3567971129917193 | 32.024877697708924 | 1.9711803319844885 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 2.0 | 0.10708588307347083 | 0.000541281295210577 | 0.38883540641130226 | 0.004060247450034512 | 0.6346112695376396 | 0.025066815452123775 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 4.0 | 0.1457384732984833 | 0.002941647468322682 | 0.5111175321771052 | 0.02792372089842099 | 0.9674723806525982 | 0.06632965704127748 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 6.45 | 1.92251422435518 | 1.420841554043027 | 4.0308703150016365 | 3.4362240073524695 | 4.762620626218518 | 3.3297943358516138 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 8.0 | 6.795849932493485 | 1.1881259385858525 | 13.160118181603385 | 2.816197502005593 | 14.767997546687019 | 2.0237243088264236 |

#### TPOT, seconds (source: results/baseline_agg.csv)

| model | max_tokens | range_note | qps | P50 mean | P50 std | P90 mean | P90 std | P99 mean | P99 std |
|---|---|---|---|---|---|---|---|---|---|
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 2.0 | 0.015236755412458418 | 0.00017724617427756738 | 0.019181062803586207 | 0.0005391447999946524 | 0.026152697466552643 | 0.0017017658670931703 |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 4.0 | 0.03183293051188674 | 0.005240049915263451 | 0.041801632990505454 | 0.007644180257085738 | 0.05190190945332454 | 0.004327836090631989 |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 6.45 | 0.0641196542930596 | 0.00038417266072525127 | 0.06692831411293866 | 0.0006724798506025668 | 0.06794329670457393 | 0.000601896881422636 |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 8.0 | 0.0647607896167632 | 0.0004995224823556635 | 0.0668483155546978 | 0.0003601578196160171 | 0.06769582372554318 | 0.00015409721031222023 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 2.0 | 0.013393246448426066 | 0.00011415450787014789 | 0.01649732893356973 | 0.00035763476862018276 | 0.024171215455255118 | 0.0017826247483070214 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 4.0 | 0.020070664968511367 | 0.000675779941955486 | 0.027048680603478852 | 0.00327454320774514 | 0.04059427813790495 | 0.004294696721712909 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 6.45 | 0.04888987758138305 | 0.0022477982013592826 | 0.051993642157547676 | 0.00020631242137631622 | 0.05256683946808927 | 0.0004911737216971688 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 8.0 | 0.0511695246485557 | 0.00020240440836123187 | 0.052650157803987775 | 0.0006172935216967411 | 0.05302553436743854 | 0.00046565064180657166 |

#### Request E2E, seconds (source: results/baseline_agg.csv)

| model | max_tokens | range_note | qps | P50 mean | P50 std | P90 mean | P90 std | P99 mean | P99 std |
|---|---|---|---|---|---|---|---|---|---|
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 2.0 | 2.2662150101637106 | 0.09017779199892308 | 7.112884657437952 | 0.12245430215036715 | 10.366714395009604 | 0.5634014900325387 |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 4.0 | 4.692430284066731 | 0.7221614088759627 | 15.120723226431858 | 2.1823195104173236 | 21.800618990593843 | 2.6081379172781434 |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 6.45 | 20.54428605706245 | 1.7984816986046304 | 36.95596229790825 | 2.4921110415253795 | 45.631173484082346 | 2.3633400101844892 |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 8.0 | 27.960698349381577 | 0.8965891502528494 | 45.79091065995855 | 2.4764714441867155 | 52.6913629454503 | 2.5225875027439955 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 2.0 | 2.0316902505409087 | 0.06466185654769156 | 6.1916405429384715 | 0.017546573715441282 | 8.974623251451519 | 0.47693037365499263 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 4.0 | 3.1427753043006192 | 0.2616297910785832 | 9.56078008520633 | 0.8526660134312348 | 14.078268471290022 | 0.987665472508234 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 6.45 | 8.57602672401838 | 2.0627700215891185 | 22.91378620600902 | 1.9959888979881835 | 30.908265918774703 | 1.134589959375186 |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 8.0 | 16.345026062684596 | 1.8435903212330742 | 29.05046858966483 | 2.0651356995081622 | 36.454585799754405 | 1.8072392262916195 |
<!-- END TABLES_ORIGINAL -->

### Llama-2-7b rerun with trace max_tokens 4096 (within profiled range)

Source files: `results/baseline_llama2_capped4096.csv`, `results/baseline_llama2_capped4096_agg.csv`.
Max request length 4095 tokens in every run.

<!-- BEGIN TABLES_CAPPED -->
#### TTFT, seconds (source: results/baseline_llama2_capped4096_agg.csv)

| model | max_tokens | range_note | qps | P50 mean | P50 std | P90 mean | P90 std | P99 mean | P99 std |
|---|---|---|---|---|---|---|---|---|---|
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 2.0 | 0.1062514197146257 | 0.0009973471269493386 | 0.35319256694401324 | 0.0040935495489645675 | 0.5309991700977983 | 0.052878852823452706 |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 4.0 | 0.19077161721013758 | 0.0391026158277659 | 0.599467400712312 | 0.05549735851468667 | 1.0970147347769086 | 0.021567086315089145 |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 6.45 | 7.258150944504012 | 1.3344164723602796 | 15.736253936505898 | 3.1458333699906733 | 17.845736963483784 | 2.022213269313624 |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 8.0 | 13.486046549686158 | 1.225588743267588 | 27.259862712823615 | 2.3996819655293042 | 30.62982616038907 | 1.7260041076515007 |

#### TPOT, seconds (source: results/baseline_llama2_capped4096_agg.csv)

| model | max_tokens | range_note | qps | P50 mean | P50 std | P90 mean | P90 std | P99 mean | P99 std |
|---|---|---|---|---|---|---|---|---|---|
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 2.0 | 0.015137048903025333 | 0.00022722359084906553 | 0.01877683834854552 | 0.0006382318081714381 | 0.026210648944640532 | 0.0016271963049389732 |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 4.0 | 0.03093978577842065 | 0.004554283184055128 | 0.03945120770927469 | 0.007389157469498477 | 0.05060526696743881 | 0.0040124113120860085 |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 6.45 | 0.06411579322144993 | 0.00037062856472725456 | 0.06749502973087872 | 0.001275998625876449 | 0.06856074387180734 | 0.0009058382994977143 |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 8.0 | 0.06473588134505388 | 0.00031504871884415706 | 0.06768602199125127 | 0.0013271690032555113 | 0.06855674918356275 | 0.0009074327012870662 |

#### Request E2E, seconds (source: results/baseline_llama2_capped4096_agg.csv)

| model | max_tokens | range_note | qps | P50 mean | P50 std | P90 mean | P90 std | P99 mean | P99 std |
|---|---|---|---|---|---|---|---|---|---|
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 2.0 | 2.2189862909971736 | 0.10934854508481989 | 7.035025878483647 | 0.10783605812700699 | 10.255205047767378 | 0.6716841243689412 |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 4.0 | 4.489779015825743 | 0.6105782871253066 | 14.49509074186449 | 2.1021630770586657 | 20.8113444518759 | 2.8912648372112275 |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 6.45 | 19.545994976553086 | 1.9340790277974549 | 35.948709587703114 | 2.4269235027335965 | 44.672110572304234 | 2.3996494561282344 |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 8.0 | 27.34627248678619 | 0.6224410701861635 | 44.52333874560395 | 2.400102674186566 | 51.68664638040423 | 2.3154592943462817 |
<!-- END TABLES_CAPPED -->

## Paper vs reproduced

Paper: arXiv 2405.05465 (downloaded PDF, `data/paper_2405.05465/paper.pdf`, text layer extracted with
pypdf to `paper.txt`; page numbers are PDF page indices). Paper fidelity is defined as the percentage
error between Vidur's prediction and measurements on real A100 80GB GPUs running a vLLM fork with the
default vLLM scheduler, on Chat-1M, Arxiv-4K and BWB-4K traces (Section 7.1 and 7.2, pages 8 and 9).

| Paper item (source) | Paper value as printed | Reproduced | Comparable? |
|---|---|---|---|
| Abstract (p1): latency error across LLMs | less than 9% error | TODO | No: needs real-GPU measurements, which this CPU-only phase does not have |
| Static P95 execution latency error (p9 text, Fig 3) | upto 3.33% error | TODO | No: same reason; also different traces and scheduler |
| Dynamic, 85% capacity (p9 text, Fig 4) | <5% error in almost all scenarios | TODO | No |
| LLaMA2-7B dynamic, 95% capacity (p15 text, Fig 7) | up to 12.65% maximum error | TODO | No |
| LLaMA2-7B Fig 4(a) median normalized E2E error, 85% capacity (p9) | -2.88% / -8.50% / -6.99% (trace mapping TODO) | TODO | No |
| LLaMA2-7B Fig 4(b) P95 normalized E2E error, 85% capacity (p9) | -4.55% / -7.30% / -7.47% (trace mapping TODO; panel assumed LLaMA2-7B by order) | TODO | No |
| Absolute latencies (bar heights, Figs 3, 4, 7) | TODO (user to read from the figures; not in the text layer) | n/a | n/a |
| Any Meta-Llama-3-8B number | TODO (Llama-3 does not appear in the extracted text) | n/a | n/a |

All extracted paper values, including Figure 3 and Figure 7 bar labels for LLaMA2-7B, are in
`results/paper_reported.csv`.

## Differences and likely causes

1. Not a fidelity reproduction. The paper's fidelity numbers are errors against real GPU runs. This
   phase only runs the simulator, so it reproduces that Vidur runs and produces these outputs, not
   the error numbers. A real-hardware baseline is needed for any paper-vs-reproduced error comparison.
2. Workload and scheduler differ from the paper's fidelity setup. Our runs use the README config
   (splitwise_conv trace, Sarathi scheduler with chunk 512, Poisson QPS 2/4/6.45/8). The paper's
   fidelity runs use Chat-1M/Arxiv-4K/BWB-4K, the default vLLM scheduler, and arrival rates set relative
   to each system's measured capacity (75%, 85%, 95%), not fixed QPS.
3. Llama-2-7b runs exceed the profiled range. Profiling data for Llama-2-7b on a100
   (`~/vidur/data/profiling/compute/a100/meta-llama/Llama-2-7b-hf/attention.csv`) has max
   prefill_chunk_size 4096, kv_cache_size 4032, batch_size 128, and `mlp.csv` max num_tokens 4096.
   The README flags ask for predictions up to 16384 tokens and batch 512, so the random forest
   extrapolates for long requests. Vidur also does not enforce `max_position_embeddings` (4096 in
   `Llama2_7BModelConfig`): in the Llama-2-7b QPS 2 runs, 50, 47 and 41 requests (seeds 42, 43, 44)
   have more than 4096 tokens, max 7037, 7207, 7052. A real Llama-2-7b vLLM server would reject these.
   For Meta-Llama-3-8B, profiling covers prefill_chunk_size up to 16384 and batch_size up to 512.
   Vidur's `Llama3_8BModelConfig` sets `max_position_embeddings` to 4096.
   Follow-up (1.6): with trace max_tokens 4096 the Llama-2-7b runs stay inside the profiled range
   (max request 4095 tokens). Latencies change only moderately (compare the two Llama-2-7b tables), for
   example TTFT P50 mean at QPS 6.45 is 8.034868006638545 s uncapped and 7.258150944504012 s capped.
4. Llama-2-7b saturates earlier than Llama-3-8B in the simulator: TTFT P50 mean jumps between QPS 4 and
   6.45 for Llama-2-7b (0.20127110929299497 s to 8.034868006638545 s). A likely cause, not verified
   here, is that Llama-2-7b has 32 KV heads versus 8 for Llama-3-8B, with both at 32 layers, 32 query
   heads and embedding_dim 4096 (`vidur/config/model_config.py`), so
   each token uses 4 times the KV cache memory and fewer requests fit in a batch. The capped rerun
   shows the same jump (TTFT P50 mean 0.19077161721013758 s at QPS 4 to 7.258150944504012 s at QPS
   6.45, `results/baseline_llama2_capped4096_agg.csv`), so the saturation is not caused by the
   over-length requests.
5. Execution-time predictor training is not seeded. `RandomForestRegressor()` is built without
   `random_state` (`vidur/execution_time_predictor/random_forrest_execution_time_predictor.py:38`).
   Two cold trainings on identical data picked different hyperparameters (for example, model `add`:
   n_estimators 750 in attempt 1, 250 in attempt 2, `logs/phase1_1.1_readme.log`). Results are
   reproducible only while the same `cache/` directory is reused. All sweep runs for a given model used
   one trained cache, so seed-to-seed differences come only from the request generator.
6. `attn_kv_cache_save` predictor fits poorly for Llama-3-8B: training MEAP 101.13621381971042% (attempt
   1) and 101.12785992327893% (attempt 2), versus 0.0% for Llama-2-7b (`logs/phase1_1.2_sweep.log`). Not
   investigated further.

## Installation problems and code issues

1. `vidur` is not installed in `~/.venv-vidur` (`ModuleNotFoundError: No module named 'vidur'`). Used `PYTHONPATH=~/vidur` instead of installing, to leave the venv unchanged.
2. Relative default paths. Profiling inputs default to `./data/profiling/...`, outputs to `simulator_output/`, cache to `cache/`. Running from `~/vidur` would write into it, so all paths were passed explicitly (absolute inputs, outputs and cache under `~/fidelity-phase1`).
3. OOM kill (1.1 attempt 1). `num_training_job_threads` defaults to -1, so GridSearchCV started 16 loky workers. The kernel log shows `Out of memory: Killed process 24480 (python) total-vm:6743700kB, anon-rss:3421396kB` (triggered from a `pt_nccl_watchdg` thread of another process). The 16 workers were orphaned (parent init) with total RSS 4463576 kB and were terminated with SIGTERM. Their semaphore names (`loky-23542-...`) match our python PID 23542. The truncated cache file `attn_prefill_f48e63f6_predictions.pkl` failed to load (`EOFError: Ran out of input`), so that cache was moved to `cache_oomkilled_run1/` and not reused. That directory (989M, 65 files) was deleted in 1.6 after confirming nothing in this file uses it as evidence; the evidence above is in `logs/phase1_1.1_readme.log` lines 56 and 63 (`logs/phase1_1.6_cleanup.log`).
4. Silent output failure (1.1 attempt 2). `fig.write_image` raised `RuntimeError: Kaleido requires Google Chrome to be installed.` inside an atexit callback (`Simulator._write_output`). Python reported `Exception ignored in atexit callback` and the process still exited 0, so only `config.json` and `request_metrics.csv` were written. Cause: Vidur's requirements are unpinned, and kaleido 1.5.0 no longer bundles Chromium. Not fixed by downloading Chrome. Worked around with `--no-metrics_config_store_plots`, which only skips PNG export (`data_series.py`), so CSVs are still written.
5. Seed flags. `--seed` alone does not change the workload, because the synthetic generator re-seeds with its own seed (default 42). See "Exact commands".
6. Docs vs code metric names: `docs/metrics.md` uses `prefill_time_e2e_cdf` and `request_e2e_time_cdf`, while the CSV columns are `prefill_e2e_time` and `request_e2e_time`.
7. The PDF could not be rendered by the Read tool (`pdftoppm is not installed`), so figure bar heights were not read.

## Deviations from the original setup

1. `--random_forrest_execution_time_predictor_config_num_training_job_threads 4` (2 for the Llama-2-7b sweep). Changes only training parallelism, to avoid OOM on a 10 GB machine shared with another agent.
2. `--no-metrics_config_store_plots` (PNG export needs Chrome).
3. Explicit absolute paths for the profiling inputs, trace file, output and cache dirs (same files as the defaults).
4. Seeds set on four flags (`--seed`, synthetic, trace length, Poisson) instead of the defaults, all equal per run.
5. All runs executed with `nice -n 10`, `WANDB_MODE=disabled`, under `/usr/bin/time -v`.
6. Results across runs depend on the shared trained-predictor cache (`cache/`), which was trained in 1.1 attempt 2 (Llama-3-8B) and in `sweep_Llama-2-7b-hf_qps2_seed42` (Llama-2-7b). Archived copy: see "Predictor cache artifacts".
7. 1.6 only: trace max_tokens 4096 instead of the README's 16384, for Llama-2-7b.

## Predictor cache artifacts

The predictor cache that produced `results/baseline.csv` (and, read-only, the capped results) was
copied with `cp -a ~/fidelity-phase1/cache ~/fidelity-artifacts/phase1_vidur_predictor_cache`
(outside git). Source: `logs/phase1_1.6_artifacts.log`.

- 132 files, 2339608995 bytes in total (sum of file sizes in the manifest), 36 of them zero-byte lock files (both from `logs/phase1_1.6_sums.log`). `du -sb` of the copy: 2339621283.
- Manifest in `sha256sum` format: `~/fidelity-artifacts/phase1_vidur_predictor_cache.sha256` (copy in `results/predictor_cache.sha256`, byte-identical by `cmp`); sha256 of that manifest file: `7362c11f124e5eba30ed1d46be1c59819857c4337f1b15c96e69363c36e48a19`.
- Verification: `sha256sum -c` of the manifest against the original `cache/` gave 132 OK, 0 not OK. No cache file was modified by the 1.6 capped runs (none newer than the end of the 1.2 sweep).
- Per-file manifest with size and training origin: `results/predictor_cache_manifest.csv` (copy in `~/fidelity-artifacts/`). `trained_in` is assigned from file mtime: 66 files fall in the 1.1 attempt 2 window (18:04:45 to 18:22:08, Meta-Llama-3-8B) and 66 in the `sweep_Llama-2-7b-hf_qps2_seed42` window (18:23:56 to 18:43:54, Llama-2-7b); none fall outside both.
- To reuse: copy the directory back and pass it as `--metrics_config_cache_dir`.

<details><summary>All 132 files (path, size in bytes, training origin, sha256)</summary>

<!-- BEGIN CACHE_MANIFEST -->
| path | size_bytes | trained_in | sha256 |
|---|---|---|---|
| 06bc2760_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 1317b83a_prediction_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 252f66c5_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 345ffb5f_prediction_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 3f6dd157_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 48772d3b_prediction_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 51400a4e_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 53661595_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 5de27470_prediction_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 684f46d6_prediction_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 697e5910_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 6d170439_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 70d5abf5_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 70f1716d_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 79581cda_prediction_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 7ec512eb_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 855a6010_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 8c27eeb2_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 8f57dc1c_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 91e106f6_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 9a045ad3_prediction_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| 9d5f659b_prediction_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| a738bc87_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| a827eb3f_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| aa4a5d0e_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| add_70d5abf5.pkl | 4752583 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | d8997f64b998b26f8914b7fe95136ecc9538bf312fe346396c617ddf062d9f7f |
| add_70d5abf5_training_predictions.csv | 8184 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 66c2eef384540ae24c7d281dadb105c02ff1d4fec15667acb6223b489df668ca |
| add_9a045ad3_predictions.csv | 429436 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 6d36f09879f87ff72f8acf2ae33d24dba9902fc3daf19ffbf6651a9c358422c8 |
| add_9a045ad3_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 46e8fbe2caf8240e3dabbdcd003301ea1efcea3fcd40ec3e1a8e7d56fc3026aa |
| add_9d5f659b_predictions.csv | 411132 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 698ea3f4afdceb6042f58060c9a62877c7d666172ac0fb8ad473dc9ecde000c7 |
| add_9d5f659b_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | f539bdc00eabc76c34ddb519bda24bf4a6043680591ef1cf717e04a6614d7957 |
| add_fccb9d87.pkl | 6818484 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 4fa5d53232478cd204bcc7b2aeea5999bbffa974320b86068c9c82ab2463905e |
| add_fccb9d87_training_predictions.csv | 14246 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 063c7d14ca8901710148785880b76e8fcf2aad7dbd560cff5f254630969932fe |
| attn_decode_345ffb5f_predictions.csv | 3607292 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 70a8ac1073ca5517380679e8e5e44dbab4b655ac35b1779dc414c63b55c32364 |
| attn_decode_345ffb5f_predictions.pkl | 7764916 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | f8d99d8abee77589c42daccafab737517c7fce4d235204519ac2d75a4b8a92ee |
| attn_decode_6d170439.pkl | 675049033 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | d3468ac7dc77ed328a8ac764d508572a0c60e91883dd1199d52d973f23d77882 |
| attn_decode_6d170439_training_predictions.csv | 339482 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | f2127d035bf6f0111bea061d52368400bef59e0ccb676c6f45bf4e8522ea0c6b |
| attn_decode_9d5f659b_predictions.csv | 3686443 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 6563e1cbf1cf186a1db5327c2a35418cf7a9c40a57ea00b64308478eacaeba49 |
| attn_decode_9d5f659b_predictions.pkl | 7764916 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 2f62f4b4d007cde875a6f929a02a0f41ce52a65088b64e98b76409d0a0138309 |
| attn_decode_f437ed3f.pkl | 324360542 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 47299e34a7fb69093f0be4319db9873ab9899cd00b89800c44fe27891d1a4487 |
| attn_decode_f437ed3f_training_predictions.csv | 533217 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 5a0ed330b36395f3fdbfbc272d32eda260b798ccbcbe13bbae476594a9ba2134 |
| attn_kv_cache_save_1317b83a_predictions.csv | 152756 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 9114e2946071e98a5d225bf285339774d64153370e664217764231492796d95e |
| attn_kv_cache_save_1317b83a_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | c5966d30fc64e6a0ef7e74bec3885922cdcf25239f15e6e77c9bea0f51be6af4 |
| attn_kv_cache_save_697e5910.pkl | 7891716 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 425687f1ea212c520a3b705f8fad0928dd0316c335e6d35d6cfd2db6effa9d29 |
| attn_kv_cache_save_697e5910_training_predictions.csv | 567327 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 17c396af7c12676721833a2866d8328e4c2a8063eccfca93ecb75b2802d9569b |
| attn_kv_cache_save_bc3599c9_predictions.csv | 388498 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | bbb7a85bcabbab044707bd45060d94d1f461d1f5c260f0e7fb11b6197e2db884 |
| attn_kv_cache_save_bc3599c9_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | b5ee23f9929fb6cf319f22df23573cc2a86100d73d4a362ab1001a691b5b6722 |
| attn_kv_cache_save_e6015fe1.pkl | 74916 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e1c97b1fe75542ee54f72e2d4ba8ab1798e228eb5d0a526ad58cf32c65fc30b8 |
| attn_kv_cache_save_e6015fe1_training_predictions.csv | 139651 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 9e34d2fb5b14ffc43a9efc50ada3716d7f597201500cc85c965047418174cb0d |
| attn_post_proj_9d5f659b_predictions.csv | 393971 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 3af7407ba26b2bc9348136c869e8531b36161e751a14dfd40ac83a190652e60f |
| attn_post_proj_9d5f659b_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | f50f2915397fea4aeb12a229d5d05d3a2b3c2763784868a41140a7ad29f2d89b |
| attn_post_proj_a738bc87.pkl | 2293524 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 3ec17a57ae400da1a688b073c8444a024cad5423be292de1171dd93e5662bf86 |
| attn_post_proj_a738bc87_training_predictions.csv | 7958 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 575cb9d79adea14d061bd73d2457c4b561872042bf8651cc458c60b64df36175 |
| attn_post_proj_d2ed5d7d.pkl | 9652782 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 4a42e248a775eac33163def715bbd525dd4b25b87278a8220a5feb3bac8b8bdd |
| attn_post_proj_d2ed5d7d_training_predictions.csv | 14175 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 7680b0c1f505e97c3d7dec6148850aee3563d5d6f18ea66649e25e4d0cd0e1b4 |
| attn_post_proj_e0fd08c2_predictions.csv | 400394 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | a8e6d4d75c76ded3409b69bfee77094ae0eb20af496ecf14e65838e7b0c2af25 |
| attn_post_proj_e0fd08c2_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 9200593f38da14b46fcfaa53c587f442ee2aaab0720cc8de72c4dbb93a468e09 |
| attn_pre_proj_684f46d6_predictions.csv | 386239 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 04f8dd7f01f02d1d2624638b1283c0e7b275f41f7b00954b5d0cc2a7ccf8c5af |
| attn_pre_proj_684f46d6_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 5364baa93ee87802f3cab32ca8bc3b2b38915472c6419a9842cd9c58aa789958 |
| attn_pre_proj_855a6010.pkl | 9875550 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 18f881108f413c048b7831f47ced42a3db2c2e0b39c85a4bdbe44e1be56ec22b |
| attn_pre_proj_855a6010_training_predictions.csv | 14130 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 10bc54b89ad586f4a58a16199112d4251990ae24abf4d39c606a5811f21ac368 |
| attn_pre_proj_9d5f659b_predictions.csv | 392297 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | ff81e5ecbab4ac3c08f5930879ead833e048f2e8010a2901a1da899298a890e4 |
| attn_pre_proj_9d5f659b_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | b652c7307dcc04af1d8ab5156bafc885f03a380502b71c887ebc73c72b4b4efd |
| attn_pre_proj_ca3673f6.pkl | 11246161 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 119fe71f54534356de995e2003496ff5fba706650c286bef212d8f992bd6a7e2 |
| attn_pre_proj_ca3673f6_training_predictions.csv | 7855 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 7b52f286298b72296ed380418a2d3fa7462d7717c068c61afc3288453d9184dc |
| attn_prefill_345ffb5f_predictions.csv | 140520148 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | f54f09130cc152652fdbaf9633f6d4b5060c90d3fbab1908f3604333064e2204 |
| attn_prefill_345ffb5f_predictions.pkl | 248473258 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 3685e6bad4888fb6fb4475c9afa992d469ce28ceb922b5f8945b1318c454b62b |
| attn_prefill_70f1716d.pkl | 46074420 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 398adc88b9b660c4974ca7281d9577154e69c8b0d39d80c3352d05744f161a96 |
| attn_prefill_70f1716d_training_predictions.csv | 97847 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 7df6638f3b562a1b99540cc079f0389c4db6bc178d4e10c45f8b9630732fc732 |
| attn_prefill_aa4a5d0e.pkl | 280751005 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | ed7f79d0305ddf777ec70722ddd0f69bd9c546db809ac0496fe0af69d336b747 |
| attn_prefill_aa4a5d0e_training_predictions.csv | 163743 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 49b676201703f41526c352482280383a7154330fbbbd25cbfbbbbd369796ed26 |
| attn_prefill_fad4c843_predictions.csv | 137152446 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 5a59c9be5954506adbd720ec9a1eeeeaf8b0a1cddf9a6aa164fa0c131b67bef0 |
| attn_prefill_fad4c843_predictions.pkl | 248473258 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 73b86ee02136e82a0d4c4c64176d74df66b417a5165d3b0301e839ddb0f8c02c |
| attn_rope_06bc2760.pkl | 7552492 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 907b008e9a2a2b9bb8d2eaf4f35b8c0664935a3535119fdbe08ae7f2ce0dd392 |
| attn_rope_06bc2760_training_predictions.csv | 8031 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 394291c40164095bd69c21b2eefaf807a424df06866aab7167e3b84f03a5556b |
| attn_rope_5de27470_predictions.csv | 409804 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 5ff209f87795264bf2f38eb667dbc72b4ad2305671cad8be88ea478d31e5e1de |
| attn_rope_5de27470_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 599c4dbae3efb56f5e6f9bb1839c33621e75e95e1fc54655c3b10836a22772af |
| attn_rope_684f46d6_predictions.csv | 415029 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e9b897deed87e675ac9865bc4dcac6715b01943b7be7c186f1898f3e38f7f8a3 |
| attn_rope_684f46d6_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | c4cc0f351befb8b8586cd26b541f86780ade21edc055a166cca0648b7e73aef0 |
| attn_rope_a827eb3f.pkl | 21778168 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 3af5c1b65090c0abe2cc70c9b3697581e85c16f37fec819c229d09b317d139d8 |
| attn_rope_a827eb3f_training_predictions.csv | 14323 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 336cc4bbd49388aab0ce2e040336d70c0c520ebbdb1d9d0d7f8ab0629ec13afb |
| bc3599c9_prediction_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| ca3673f6_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| d2ed5d7d_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| d7eea2ea_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| e0fd08c2_prediction_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| e6015fe1_model_lock.file | 0 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| e67c02c6_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| f437ed3f_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| f48e63f6_prediction_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| fad4c843_prediction_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| fccb9d87_model_lock.file | 0 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| input_layernorm_345ffb5f_predictions.csv | 415644 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 5bf0cb98efc0d4d8a561e6cf20ccce9fc2df1bf918f149caee3567b038cdd0cb |
| input_layernorm_345ffb5f_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | affc867c78340d29b81f489e22d72e313f4bd7abac5e9270893a633cb8a9f495 |
| input_layernorm_8c27eeb2.pkl | 15489040 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | cbdc296e89c95302ffcce5e5b11154340dd31f855f7588aee0abe8b8ed30b107 |
| input_layernorm_8c27eeb2_training_predictions.csv | 14357 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 3baa00d329c49d4bd02a6e0e2578822e1823cde69798bea38c0082c06ff77968 |
| input_layernorm_d7eea2ea.pkl | 10778458 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 2bbc914d4364a068bee34b1656c224dcfb77979f3757a1e63d6e206f4798087d |
| input_layernorm_d7eea2ea_training_predictions.csv | 8111 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 6171da312f687980d810bd7a8749c6229339f1119dfa82572fd746c4f9f24007 |
| input_layernorm_f48e63f6_predictions.csv | 408775 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 34a410f8633faa236f5970e6e5066b577ff8f911c14d3e99a63380d2ed608100 |
| input_layernorm_f48e63f6_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 79a32de5642cdd060496a9231997c530af4fa89bd1769ab302f438f26b7ea563 |
| mlp_act_252f66c5.pkl | 13826530 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 1732b47fe15b21b44c51f5ae41eae17261f13f74b0ca59b7ab71570e4d183b1b |
| mlp_act_252f66c5_training_predictions.csv | 8002 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 469011a43156741882d940e4c9f4bf364a02dfa86bfe55f5b5accf0186550d54 |
| mlp_act_345ffb5f_predictions.csv | 414377 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | fedcf0ea2bceaec365a5060918383a4de844927d4e2e85c8dc349ac5abcb7a95 |
| mlp_act_345ffb5f_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | ca1a685d1585453ed49f98d57924a0591502318202e4d64e1e7bb7414e5fd7e3 |
| mlp_act_9d5f659b_predictions.csv | 397456 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 12474768b38fcb1ccf20d1924640fe16b53bc013b1af02dfac62956f51e75cb8 |
| mlp_act_9d5f659b_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 801270c476be8e91ba31be29dcaaee65bae36ebf3d401cd481ebc228b317207b |
| mlp_act_e67c02c6.pkl | 9109758 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | a9b629403213b4557a4fa0187b05122a152631acd3abbb635242af246c188721 |
| mlp_act_e67c02c6_training_predictions.csv | 14107 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 6a1d81da75cdc3256cc98895d3e22e0e5cf60fdc1cd2e5a501ab166c6f8e993d |
| mlp_down_proj_345ffb5f_predictions.csv | 398389 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 35577db516259eda0b1d331ec35349b2bc9769a6c376d1e74ffa1b5df76d8af8 |
| mlp_down_proj_345ffb5f_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 57f66c6b8f042783e6a287e2a6455ecf8956ed5d5959cc9414dd1e0ba394ee26 |
| mlp_down_proj_53661595.pkl | 5575611 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 8590451461fa1e14ab2c1a8dd7cbd8e17bd03523882fad3fb4278deb03b974f3 |
| mlp_down_proj_53661595_training_predictions.csv | 14276 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 49c92a559b9597b047a96dde129ffa3dd730482e4eec0eb9be124020e88da4a7 |
| mlp_down_proj_79581cda_predictions.csv | 387286 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 9d380958afb64b05157b2853fc9fc9ae3938ca7e998045b69065457b044e3d55 |
| mlp_down_proj_79581cda_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 6b75a5f10e3ea093b5efed0dba947d5530104e510496fe1c5787c102860efd6d |
| mlp_down_proj_7ec512eb.pkl | 16501450 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 141c6a64a68c84ae03377809f2cf294e07f44a5b21cc8afb4a6532a268c5e6b5 |
| mlp_down_proj_7ec512eb_training_predictions.csv | 7863 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 40afb3a95808f3c0a60e1f59f54da17beff925afadcb90d3dec1f41e627f6122 |
| mlp_up_proj_48772d3b_predictions.csv | 384752 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 3e44c9089d5472e4c726daf34f52ffc5ea9c2ca89159897c83ef880d0f14fabc |
| mlp_up_proj_48772d3b_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 5fd4c21749161facefb8f604e2baf88d74408851baec4dc8916abe89e4ee1379 |
| mlp_up_proj_8f57dc1c.pkl | 20555374 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 79c86d7eff1362689c116854a7e7a02848b662ee6cf23db4b4dae6978e6d633a |
| mlp_up_proj_8f57dc1c_training_predictions.csv | 14167 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 5e55255b9ee5305de02ef8d5a47e7e063c6522d2f78e0aae3710c902636d4cab |
| mlp_up_proj_91e106f6.pkl | 5845476 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 4cfdb19572ecacc3628ed31b9886e3fbb307c50c20f740d875e3aa1ceea30bd9 |
| mlp_up_proj_91e106f6_training_predictions.csv | 8133 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 0982b326d2909ef73b32dbf81bb1a665819348fd2f3bd00770132e2896f6b914 |
| mlp_up_proj_f48e63f6_predictions.csv | 388876 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | a52fa3256b4526b3b57723edd6e122b688f72abe97746d5665f028cf3329a9f9 |
| mlp_up_proj_f48e63f6_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 8adae8f810cdf33e0140f05befe533653da1dfdd2f8f22a448020f0b2528c7bf |
| post_attention_layernorm_3f6dd157.pkl | 7263012 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | d746be25d9eb08afe8c2baa6a6569045f61ff85701c8b61191fcd46feb31d4e3 |
| post_attention_layernorm_3f6dd157_training_predictions.csv | 14292 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | f6b8f8cc450d301789d5e26c6d1a2446aa192bf791e8458668b56b46095226fe |
| post_attention_layernorm_51400a4e.pkl | 6098083 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 1b5625e4c53f5a904c2ccae34c5d7185237aec369510ae366457ec5691331209 |
| post_attention_layernorm_51400a4e_training_predictions.csv | 8121 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 33d8f96b0a5f727e1aa5f84e5dc42db604d46f4a606e6aa94add4539d5c01e3e |
| post_attention_layernorm_9a045ad3_predictions.csv | 415604 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | b8a1097c85962c520856bf449aa85b5a899ab7e36b60b080423791852bdc9578 |
| post_attention_layernorm_9a045ad3_predictions.pkl | 655618 | sweep_Llama-2-7b-hf_qps2_seed42 (meta-llama/Llama-2-7b-hf) | 069a3e332546f3898201520c41d04c7b72e2be561743354bdb1e706cf7180de0 |
| post_attention_layernorm_9d5f659b_predictions.csv | 407477 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 81b78183edd42c81230fb79f60e2a61ee84597e8efc642518ce23bcc82a0192e |
| post_attention_layernorm_9d5f659b_predictions.pkl | 655618 | 1.1 attempt 2 (meta-llama/Meta-Llama-3-8B) | 455ae2d6cfadcd5cf8c71dd715a895cc0de861a6d3e7cb5f0e202124e91028e5 |
<!-- END CACHE_MANIFEST -->

</details>

## Files

- `scripts/run_vidur.sh`, `scripts/sweep.sh`, `scripts/sweep_capped.sh`, `scripts/mem_sampler.sh`, `scripts/collect.py`, `scripts/make_tables.py`, `scripts/update_results_md.py`
- `results/baseline.csv` (per run), `results/baseline_agg.csv` (mean/std over seeds), `results/baseline_llama2_capped4096.csv`, `results/baseline_llama2_capped4096_agg.csv`, `results/tables.md`, `results/sweep_walltimes.txt`, `results/capped_walltimes.txt`, `results/paper_reported.csv`, `results/predictor_cache_manifest.csv`, `results/predictor_cache.sha256`, `results/runs/*` (simulator output, not committed)
- `logs/phase1_1.1_readme.log`, `logs/phase1_1.1_readme_mem.csv`, `logs/phase1_1.1_readme_warm_mem.csv`, `logs/phase1_1.2_estimate.log`, `logs/phase1_1.2_sweep.log`, `logs/phase1_1.2_sweep_mem.csv`, `logs/phase1_1.3_collect.log`, `logs/phase1_1.4_paper.log`, `logs/phase1_1.6_capped_estimate.log`, `logs/phase1_1.6_capped.log`, `logs/phase1_1.6_artifacts.log`, `logs/phase1_1.6_cleanup.log`, `logs/phase1_1.6_sums.log`, `logs/phase1_env.log`, `logs/phase1_vidur_help.txt`
- `cache/` (2.2G per `du -sh`, trained predictors for both models): not committed; archived in `~/fidelity-artifacts/`.
