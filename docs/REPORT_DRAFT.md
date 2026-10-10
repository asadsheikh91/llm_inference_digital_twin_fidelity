# Report draft: reproducing Vidur (MLSys 2024)

Status: draft. Filled only from verified material: `RESULTS.md` (this worktree), `FEASIBILITY.md`
(at `~/llm_inference_digital_twin_fidelity/FEASIBILITY.md`), logs, and the paper text extracted to
`data/paper_2405.05465/paper.txt`. Every number has its source file next to it. Items that need the
author's own reading of the paper are marked **TODO (ME)**.

Path conventions: paths without a prefix are relative to `~/fidelity-phase1` (branch `phase1-tier-a`).
Paths starting with `main:` are relative to `~/llm_inference_digital_twin_fidelity` (Phase 0 and
Phase 2 material; these logs are not committed on `phase1-tier-a`). Paper page numbers are PDF page
indices of `data/paper_2405.05465/paper.pdf` as extracted by pypdf.

## Title

Vidur: A Large-Scale Simulation Framework For LLM Inference (`data/paper_2405.05465/paper.txt` line 3;
arXiv abstract page title in `data/paper_2405.05465/abs.html`).

## Authors

**TODO (ME)**

## Venue

MLSys 2024. The PDF header reads "Proceedings of the 7th MLSys Conference, Santa Clara, CA, USA, 2024"
(`data/paper_2405.05465/paper.txt` lines 45 and 46, logged in `logs/phase1_report_facts.log`).

## Year

2024. arXiv v1 Wed, 8 May 2024; v2 Tue, 21 May 2024 (`logs/phase1_report_facts.log`, from
`data/paper_2405.05465/abs.html`). PDF: "Copyright 2024 by the author(s)" (`paper.txt` line 46).

## Paper link

https://arxiv.org/abs/2405.05465 (PDF fetched from https://arxiv.org/pdf/2405.05465, HTTP 200,
723168 bytes, `logs/phase1_1.4_paper.log`).

## Code link

https://github.com/microsoft/vidur, commit `abae7f63aa857300f5cdc6f5e0d27860cd24721b`, branch main,
working tree clean (`logs/phase1_env.log`; also `main:FEASIBILITY.md` section 0.5).

## Problem addressed

From the paper's own words (abstract, p1, `paper.txt` lines 7 to 13): optimizing LLM deployment "is
expensive today since it requires experimentally running an application workload against an LLM
implementation while exploring large configuration space formed by system knobs such as
parallelization strategies, batching techniques, and scheduling policies."

Section 3 lists challenges in simulating LLM inference: time scale, varying iteration times, and
cascading errors (`paper.txt` lines 280 to 319, p4).

Own summary and assessment of the problem: **TODO (ME)**

## Proposed approach

From the paper (p1 abstract, p5 Section 4.2, `paper.txt` lines 9 to 19 and 409 to 434):

- Vidur models the performance of LLM operators "using a combination of experimental profiling and
  predictive modeling" and evaluates end-to-end inference performance for different workloads.
- Two phases: model onboarding (profile a set of compute operators, then train small machine-learning
  models that produce operation-wise runtime lookup tables) and simulation (an event-driven simulator
  with a pluggable hierarchical scheduler).
- Vidur-Search uses Vidur to search deployment configurations for the best throughput per cost.

What the code does in the configuration we ran (verified in code, `RESULTS.md`): the runtime estimator
is a random forest per operator (`RandomForestRegressor()`, trained with `GridSearchCV`), trained from
the CSV files in `~/vidur/data/profiling/compute/<device>/<model>/` and cached.

Own explanation of why the approach works and its key insights (Section 4.1): **TODO (ME)**

## System architecture

From the paper (p4 Figure 2 "Vidur Simulator High Level Architecture", p5 to p6 Sections 4.3 to 4.5,
`paper.txt` lines 353, 409 to 560):

| Component (paper section) | What the paper text says |
|---|---|
| Profiler (4.3) | Triages operators into token-level, sequence-level and communication operators and profiles them |
| Runtime Estimator (4.4) | Trains small ML models on the profiled data to predict operator runtimes over a large parameter range |
| Hierarchical Scheduler (4.5) | Three tiers: global scheduler (request routing), replica scheduler (batching and memory management), and a third tier **TODO (ME)** |
| Vidur-Bench (5) | Workloads, scheduling/batching/routing policies, serving frameworks, metrics |
| Vidur-Search (6) | Configuration search over deployments |

Code directories in `~/vidur/vidur/` (`logs/phase1_report_facts.log`) include `execution_time_predictor`,
`scheduler`, `request_generator`, `metrics`, `profiling` and `config_optimizer`. Which directory
implements which paper component: **TODO (ME)**. Architecture
diagram description and own reading of Figure 2: **TODO (ME)**

## Cloud computing component

Facts from the paper:

- The paper's evaluation hardware is cloud VMs: "Azure Standard NC96ads A100 v4VMs, each equipped with
  4 NVIDIA 80GB A100 GPUs, connected with pairwise NVLink" (as extracted, p8, `paper.txt` lines 748 to 750).
- Vidur-Search found the best configuration for LLaMA2-70B in "about one hour on a 96-core CPU cores
  that costs $9.93 per hour on Microsoft Azure", versus "42K GPU hours, costing approximately $218K"
  (p2, `paper.txt` lines 159 to 164).

Facts from our setup: everything ran on a local WSL2 laptop, no cloud resources (`logs/phase1_env.log`,
`main:FEASIBILITY.md` Host).

How the project's cloud component relates to the course brief: **TODO (ME)**

## Multimodal component

- Vidur has no vision models. The README "Supported Models" table lists seven text LLMs:
  `meta-llama/Meta-Llama-3-8B`, `meta-llama/Meta-Llama-3-70B`, `meta-llama/Llama-2-7b-hf`,
  `codellama/CodeLlama-34b-Instruct-hf`, `meta-llama/Llama-2-70b-hf`, `internlm/internlm-20b`,
  `Qwen/Qwen-72B` (`logs/phase1_report_facts.log`, copied from `~/vidur/README.md`).
- The paper's evaluated models are LLaMA2 7/70B, InternLM-20B and Qwen-72B (p8, `paper.txt` section 7.1).
- The planned multimodal extension is future work. Feasibility evidence only: vLLM 0.31.0 served
  `llava-hf/llava-onevision-qwen2-0.5b-ov-hf` on the laptop GPU and answered one image request with
  HTTP 200 (`main:FEASIBILITY.md` section 0.4). This is a smoke test, not a result.

## Datasets

Only one trace from `~/vidur/data/processed_traces/` was used in our runs.

| Field | `splitwise_conv.csv` |
|---|---|
| Path | `~/vidur/data/processed_traces/splitwise_conv.csv` (382729 bytes; size, rows and columns in `logs/phase1_report_facts.log`) |
| Source | Added to the Vidur repo in commit `8e54dd5` on 2024-08-16 with message "[Trace][Core] Add traces from Splitwise, make CLI params more intuitive (#29)" (`logs/phase1_report_facts.log`). Original upstream dataset and its licence: **TODO (ME)** |
| Rows | 19366 (`logs/phase1_report_facts.log`) |
| Columns | `arrived_at`, `num_prefill_tokens`, `num_decode_tokens` (`logs/phase1_report_facts.log`) |
| Ranges | `arrived_at` 0.0 to 3501.721937; `num_prefill_tokens` 2 to 14050; `num_decode_tokens` 7 to 1000 (`logs/phase1_report_facts.log`) |
| How it is used | Only `num_prefill_tokens` and `num_decode_tokens` are read, by the trace length generator (`logs/phase1_report_facts.log`). Rows are shuffled with `--trace_request_length_generator_config_seed`. Arrivals come from the Poisson interval generator, so `arrived_at` is not used. Requests longer than `max_tokens` are shrunk proportionally, not dropped (`RESULTS.md`, Exact commands). 512 requests per run (`results/baseline.csv`). |
| Used by the paper? | Not in the paper's Table 1 workloads (Chat-1M, Arxiv-4K, BWB-4K, p7, `paper.txt` lines 593 to 601). The commit date (2024-08-16) is after arXiv v2 (2024-05-21) (`logs/phase1_report_facts.log`). |
| What it represents (conversation workload, units of `arrived_at`) | **TODO (ME)** |

Not used: `arxiv_summarization_stats_llama2_tokenizer_filtered_v2.csv` and `splitwise_code.csv` in the
same directory. Whether the arxiv file corresponds to the paper's Arxiv-4K: **TODO (ME)**.

## Hardware, OS, Python and library versions, important configuration settings

Simulator runs (`RESULTS.md` Environment, `logs/phase1_env.log`):

| Item | Value |
|---|---|
| OS | Ubuntu 22.04.5 LTS on WSL2, kernel 6.18.33.2-microsoft-standard-WSL2 |
| CPU | 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, 16 logical CPUs |
| RAM | MemTotal 10182304 kB (`logs/phase1_env.log`); 9.7 GiB visible to WSL, swap 8.0 GiB (`main:FEASIBILITY.md` Host) |
| GPU (not used by the simulator) | NVIDIA GeForce RTX 3060 Laptop GPU, 6144 MiB, driver 581.83, max CUDA 13.0 (`main:FEASIBILITY.md` 0.1) |
| Python | 3.10.12 (`~/.venv-vidur`) |
| Libraries | numpy 2.2.6, pandas 2.3.3, scikit-learn 1.7.2, scipy 1.15.3, joblib 1.6.0, plotly 7.1.0, plotly-express 0.4.1, kaleido 1.5.0, wandb 0.30.0, ddsketch 3.0.1, fasteners 0.20, matplotlib 3.10.9, seaborn 0.13.2 (`logs/phase1_env.log`) |
| Vidur | commit `abae7f63aa857300f5cdc6f5e0d27860cd24721b`, run from source with `PYTHONPATH=~/vidur` |

Important configuration (README example, `RESULTS.md` Exact commands): device a100, 1 replica, TP 1,
PP 1, synthetic request generator with 512 requests, trace length generator on `splitwise_conv.csv`,
Poisson arrivals at QPS 2, 4, 6.45, 8, Sarathi scheduler with batch size cap 512 and chunk size 512,
random forest predictor with prediction ranges 16384 / 512 / 16384, seeds 42, 43, 44. Trace
`max_tokens` 16384 (README) or 4096 (Llama-2-7b capped rerun).

Other environments used for Phase 0 and Phase 2 smoke tests: `~/.venv-vllm` (vllm 0.31.0, torch
2.13.0+cu130) and `~/.venv-sarathi` (sarathi 0.1.7, torch 2.3.0+cu121, flashinfer 0.1.1+cu121torch2.3,
transformers 4.42.4, numpy 1.26.4) (`main:FEASIBILITY.md` Environment versions).

## Original results

Fidelity in the paper is the percentage error between Vidur's prediction and real GPU runs (A100,
vLLM fork with the default vLLM scheduler, Chat-1M, Arxiv-4K, BWB-4K) (p8 to p9, `paper.txt` lines 740
to 830). Values below are as printed; full list in `results/paper_reported.csv`.

| Item (page) | Value as printed |
|---|---|
| Abstract (p1) | "less than 9% error across the range" |
| Static workloads, P95 (p9, Fig 3) | "upto 3.33% error across the four models and three datasets" |
| Dynamic workloads at 85% of capacity (p9, Fig 4) | "high fidelity ( <5% error) in almost all scenarios" (as extracted) |
| LLaMA2-7B at 95% of capacity (p15, Fig 7) | "up to 12.65% maximum error" |
| LLaMA2-7B Fig 4(a) median normalized E2E error, 85% capacity (p9) | -2.88% / -8.50% / -6.99% (assignment to traces **TODO (ME)**) |
| LLaMA2-7B Fig 4(b) P95 normalized E2E error, 85% capacity (p9) | -4.55% / -7.30% / -7.47% (assignment to traces **TODO (ME)**) |
| Absolute latencies (bar heights, Figs 3, 4, 7) | **TODO (ME)** |

## Reproduced results

**Tier A does not test accuracy against real GPUs.** These are simulator outputs only. They show that
Vidur runs on CPU and completes every request (512 of 512 in every run, `results/baseline.csv`,
`results/baseline_llama2_capped4096.csv`); they cannot confirm or refute the paper's error figures.
Wall-clock times can be affected by CPU contention; the simulated metrics below cannot (`RESULTS.md`,
"What CPU contention can and cannot affect").

Values in seconds, mean and sample std (ddof=1) over seeds 42, 43, 44. Uncapped Llama-2-7b rows are
labelled "outside profiled range" (trace max_tokens 16384 above the 4096 max `prefill_chunk_size` in
its a100 profiling data). Sources: `results/baseline_agg.csv`, `results/baseline_llama2_capped4096_agg.csv`.

<!-- BEGIN REPORT_TABLES -->
#### TTFT (`prefill_e2e_time`), seconds

| model | max_tokens | range_note | qps | P50 mean | P50 std | P90 mean | P90 std | P99 mean | P99 std | source |
|---|---|---|---|---|---|---|---|---|---|---|
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 2.0 | 0.1052840762000002 | 0.0008269959752084195 | 0.37542574256716477 | 0.004545360509863857 | 0.5857987898398783 | 0.029429801936674285 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 4.0 | 0.20127110929299497 | 0.048324657550082466 | 0.6874855780308016 | 0.10664801137620628 | 1.198852183409546 | 0.02255506665912669 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 6.45 | 8.034868006638545 | 1.371182844914874 | 17.01922830826542 | 3.068252212329785 | 19.199816525875487 | 2.177705386550713 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 8.0 | 14.318728488568269 | 1.169287472558086 | 28.622409667615496 | 2.3567971129917193 | 32.024877697708924 | 1.9711803319844885 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 2.0 | 0.10708588307347083 | 0.000541281295210577 | 0.38883540641130226 | 0.004060247450034512 | 0.6346112695376396 | 0.025066815452123775 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 4.0 | 0.1457384732984833 | 0.002941647468322682 | 0.5111175321771052 | 0.02792372089842099 | 0.9674723806525982 | 0.06632965704127748 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 6.45 | 1.92251422435518 | 1.420841554043027 | 4.0308703150016365 | 3.4362240073524695 | 4.762620626218518 | 3.3297943358516138 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 8.0 | 6.795849932493485 | 1.1881259385858525 | 13.160118181603385 | 2.816197502005593 | 14.767997546687019 | 2.0237243088264236 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 2.0 | 0.1062514197146257 | 0.0009973471269493386 | 0.35319256694401324 | 0.0040935495489645675 | 0.5309991700977983 | 0.052878852823452706 | baseline_llama2_capped4096_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 4.0 | 0.19077161721013758 | 0.0391026158277659 | 0.599467400712312 | 0.05549735851468667 | 1.0970147347769086 | 0.021567086315089145 | baseline_llama2_capped4096_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 6.45 | 7.258150944504012 | 1.3344164723602796 | 15.736253936505898 | 3.1458333699906733 | 17.845736963483784 | 2.022213269313624 | baseline_llama2_capped4096_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 8.0 | 13.486046549686158 | 1.225588743267588 | 27.259862712823615 | 2.3996819655293042 | 30.62982616038907 | 1.7260041076515007 | baseline_llama2_capped4096_agg.csv |

#### TPOT (`decode_time_execution_plus_preemption_normalized`), seconds

| model | max_tokens | range_note | qps | P50 mean | P50 std | P90 mean | P90 std | P99 mean | P99 std | source |
|---|---|---|---|---|---|---|---|---|---|---|
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 2.0 | 0.015236755412458418 | 0.00017724617427756738 | 0.019181062803586207 | 0.0005391447999946524 | 0.026152697466552643 | 0.0017017658670931703 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 4.0 | 0.03183293051188674 | 0.005240049915263451 | 0.041801632990505454 | 0.007644180257085738 | 0.05190190945332454 | 0.004327836090631989 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 6.45 | 0.0641196542930596 | 0.00038417266072525127 | 0.06692831411293866 | 0.0006724798506025668 | 0.06794329670457393 | 0.000601896881422636 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 8.0 | 0.0647607896167632 | 0.0004995224823556635 | 0.0668483155546978 | 0.0003601578196160171 | 0.06769582372554318 | 0.00015409721031222023 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 2.0 | 0.013393246448426066 | 0.00011415450787014789 | 0.01649732893356973 | 0.00035763476862018276 | 0.024171215455255118 | 0.0017826247483070214 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 4.0 | 0.020070664968511367 | 0.000675779941955486 | 0.027048680603478852 | 0.00327454320774514 | 0.04059427813790495 | 0.004294696721712909 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 6.45 | 0.04888987758138305 | 0.0022477982013592826 | 0.051993642157547676 | 0.00020631242137631622 | 0.05256683946808927 | 0.0004911737216971688 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 8.0 | 0.0511695246485557 | 0.00020240440836123187 | 0.052650157803987775 | 0.0006172935216967411 | 0.05302553436743854 | 0.00046565064180657166 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 2.0 | 0.015137048903025333 | 0.00022722359084906553 | 0.01877683834854552 | 0.0006382318081714381 | 0.026210648944640532 | 0.0016271963049389732 | baseline_llama2_capped4096_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 4.0 | 0.03093978577842065 | 0.004554283184055128 | 0.03945120770927469 | 0.007389157469498477 | 0.05060526696743881 | 0.0040124113120860085 | baseline_llama2_capped4096_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 6.45 | 0.06411579322144993 | 0.00037062856472725456 | 0.06749502973087872 | 0.001275998625876449 | 0.06856074387180734 | 0.0009058382994977143 | baseline_llama2_capped4096_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 8.0 | 0.06473588134505388 | 0.00031504871884415706 | 0.06768602199125127 | 0.0013271690032555113 | 0.06855674918356275 | 0.0009074327012870662 | baseline_llama2_capped4096_agg.csv |

#### Request E2E (`request_e2e_time`), seconds

| model | max_tokens | range_note | qps | P50 mean | P50 std | P90 mean | P90 std | P99 mean | P99 std | source |
|---|---|---|---|---|---|---|---|---|---|---|
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 2.0 | 2.2662150101637106 | 0.09017779199892308 | 7.112884657437952 | 0.12245430215036715 | 10.366714395009604 | 0.5634014900325387 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 4.0 | 4.692430284066731 | 0.7221614088759627 | 15.120723226431858 | 2.1823195104173236 | 21.800618990593843 | 2.6081379172781434 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 6.45 | 20.54428605706245 | 1.7984816986046304 | 36.95596229790825 | 2.4921110415253795 | 45.631173484082346 | 2.3633400101844892 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 16384 | outside profiled range | 8.0 | 27.960698349381577 | 0.8965891502528494 | 45.79091065995855 | 2.4764714441867155 | 52.6913629454503 | 2.5225875027439955 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 2.0 | 2.0316902505409087 | 0.06466185654769156 | 6.1916405429384715 | 0.017546573715441282 | 8.974623251451519 | 0.47693037365499263 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 4.0 | 3.1427753043006192 | 0.2616297910785832 | 9.56078008520633 | 0.8526660134312348 | 14.078268471290022 | 0.987665472508234 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 6.45 | 8.57602672401838 | 2.0627700215891185 | 22.91378620600902 | 1.9959888979881835 | 30.908265918774703 | 1.134589959375186 | baseline_agg.csv |
| meta-llama/Meta-Llama-3-8B | 16384 | within profiled range | 8.0 | 16.345026062684596 | 1.8435903212330742 | 29.05046858966483 | 2.0651356995081622 | 36.454585799754405 | 1.8072392262916195 | baseline_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 2.0 | 2.2189862909971736 | 0.10934854508481989 | 7.035025878483647 | 0.10783605812700699 | 10.255205047767378 | 0.6716841243689412 | baseline_llama2_capped4096_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 4.0 | 4.489779015825743 | 0.6105782871253066 | 14.49509074186449 | 2.1021630770586657 | 20.8113444518759 | 2.8912648372112275 | baseline_llama2_capped4096_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 6.45 | 19.545994976553086 | 1.9340790277974549 | 35.948709587703114 | 2.4269235027335965 | 44.672110572304234 | 2.3996494561282344 | baseline_llama2_capped4096_agg.csv |
| meta-llama/Llama-2-7b-hf | 4096 | within profiled range | 8.0 | 27.34627248678619 | 0.6224410701861635 | 44.52333874560395 | 2.400102674186566 | 51.68664638040423 | 2.3154592943462817 | baseline_llama2_capped4096_agg.csv |
<!-- END REPORT_TABLES -->

## Differences and possible explanations

From `RESULTS.md` "Differences and likely causes":

1. No error numbers can be compared: the paper reports error against real GPUs; Tier A has no
   real-GPU measurements. Real-GPU ground truth is planned for Phase 2.
2. Different setup from the paper's fidelity experiments: splitwise_conv trace, Sarathi scheduler,
   fixed QPS, versus Chat-1M/Arxiv-4K/BWB-4K, default vLLM scheduler, and load set relative to
   capacity.
3. The uncapped Llama-2-7b runs exceed its profiled range (max request lengths 7037, 7207, 7052 tokens
   for seeds 42, 43, 44, `results/baseline.csv` column `max_request_num_tokens`), so the predictor
   extrapolates. The capped rerun (max 4095, `results/baseline_llama2_capped4096.csv`) changes latencies
   only moderately.
4. Llama-2-7b saturates between QPS 4 and 6.45 in both the uncapped and capped runs. Possible
   explanation, not verified: 32 KV heads versus 8 for Llama-3-8B at equal layers and hidden size
   (`RESULTS.md` item 4).
5. Predictor training is unseeded, so results depend on the archived cache
   (`results/predictor_cache_manifest.csv`, `~/fidelity-artifacts/`).
6. The `attn_kv_cache_save` predictor: training MEAP 101.13621381971042% and 101.12785992327893% for
   Llama-3-8B, 0.0% for Llama-2-7b (`logs/phase1_1.1_readme.log`, `logs/phase1_1.2_sweep.log`). The
   shipped Llama-2-7b a100 `attention.csv` has 0 `attn_kv_cache_save` columns while Meta-Llama-3-8B has
   5 (`logs/phase1_report_facts.log`). Whether this explains the 0.0%: not verified.

Own interpretation: **TODO (ME)**

## Installation problems

| Problem | Evidence | Resolution |
|---|---|---|
| `vidur` not installed in `~/.venv-vidur` (`ModuleNotFoundError: No module named 'vidur'`) | `RESULTS.md` Issues 1 | Ran from source with `PYTHONPATH=~/vidur` |
| Unpinned requirements: kaleido 1.5.0 needs Chrome; PNG export crashed silently (`RuntimeError: Kaleido requires Google Chrome to be installed.`, exit status 0) | `RESULTS.md` Issues 4, `logs/phase1_1.1_readme.log` | `--no-metrics_config_store_plots` |
| numpy resolved to 2.2.6 for a pre-numpy-2 code base | `main:FEASIBILITY.md` 0.5 | No numpy-related line appears in the Phase 1 run logs (checked with grep in this session); no change made |
| No CUDA toolkit in WSL; vLLM FlashInfer sampler needs `nvcc` | `main:FEASIBILITY.md` D1 | `VLLM_USE_FLASHINFER_SAMPLER=0` |
| sarathi-serve build needs `CUDA_HOME`; PyPI `nvidia-cuda-nvcc-cu12` wheels 12.1 to 12.9 contain no `nvcc` | `main:FEASIBILITY.md` 0.3 fix 1 | CUDA 12.1 toolchain from conda via micromamba (D2) |
| sarathi-serve requirements unpinned: transformers resolved to 5.19.0 | `main:FEASIBILITY.md` 0.3 caveats | Pinned transformers 4.42.4 and numpy 1.26.4 |
| Running `python vidur/profiling/mlp/main.py` as in `docs/profiling.md` fails with `ModuleNotFoundError: No module named 'vidur'`; running from `~` makes `~/vidur` shadow the installed package | `main:logs/phase2_vidur_install.log` | Used `python -m vidur.profiling...` from `~/vidur-phase2` |
| Attention profiling: `RuntimeError: Ninja is required to load C++ extensions` | `main:logs/phase2_attn_profiling_run1.log` line 75 | venv `bin` on PATH and `CUDA_HOME` on the command line (`main:logs/phase2_attn_profiling_run2.log`) |
| flashinfer 0.2.0.post1 API differs from sarathi-serve's call: `TypeError: append_paged_kv_cache() missing 1 required positional argument: 'kv_last_page_len'` | `main:logs/phase2_attn_profiling_run2.log` line 50 | Installed flashinfer 0.1.1+cu121torch2.3 (`main:logs/phase2_flashinfer011_install.log`) |

## Missing resources

- Real-GPU ground truth on the paper's hardware (A100 80GB). Only a 6144 MiB RTX 3060 Laptop GPU is
  available (`main:FEASIBILITY.md` 0.1).
- Profiling data for the local GPU: `data/profiling/compute/` contains only `a100`, `a40`, `h100`
  (`main:logs/phase2_compat_check.log`).
- The paper's workloads (Chat-1M, Arxiv-4K, BWB-4K) are not present under those names in
  `~/vidur/data/processed_traces/` (files: `arxiv_summarization_stats_llama2_tokenizer_filtered_v2.csv`,
  `splitwise_code.csv`, `splitwise_conv.csv`, `logs/phase1_report_facts.log`). **TODO (ME)** check whether the
  arxiv file is the paper's Arxiv-4K.
- `docs/profiling.md` is out of date (checked against commit `abae7f6`, `logs/phase1_report_facts.log`):
  - It says to add a YAML model config in `data/model_configs`; that directory does not exist. The
    Phase 2 smoke test added the model in `vidur/config/model_config.py` instead
    (`main:logs/phase2_vidur_install.log`, diff stat).
  - Its directory listing names `network/a100_pair_nvlink/allreduce.csv`; the repo has
    `a100_pairwise_nvlink`, `a40_pairwise_nvlink`, `h100_pairwise_nvlink`, `a100_dgx`, `h100_dgx`, and
    the simulator default file name is `all_reduce.csv`.
  - Its commands `python vidur/profiling/mlp/main.py ...` fail with `ModuleNotFoundError`
    (`main:logs/phase2_vidur_install.log`).
  - It says CPU overhead profiling scripts are "not documented yet" (`~/vidur/docs/profiling.md`).
- Figure bar heights in the paper could not be read from the text layer; rendering tools were not
  available (`RESULTS.md` Issues 7).

## Code problems

From `RESULTS.md` and the Phase 2 logs:

1. `--seed` alone does not change the workload; the synthetic generator re-seeds with its own seed
   (`RESULTS.md` Issues 5).
2. `RandomForestRegressor()` has no `random_state`; two cold trainings chose different
   hyperparameters (`RESULTS.md` Differences 5).
3. Output writing runs in an atexit callback, so an exception there is ignored and the process exits
   0 with missing outputs (`RESULTS.md` Issues 4).
4. Default relative paths (`./data/...`, `simulator_output`, `cache`) write into the current directory
   (`RESULTS.md` Issues 2).
5. Default `num_training_job_threads=-1` started 16 workers and contributed to an OOM kill on a
   10 GB machine (`RESULTS.md` Issues 3).
6. Vidur does not enforce `max_position_embeddings`; Llama-2-7b received requests over 4096 tokens
   (`RESULTS.md` Differences 3).
7. MLP profiler default `--profile_method record_function` produced an `mlp.csv` with only the 8
   configuration columns and no `time_stats` columns; `--profile_method cuda_event` produced 58 columns
   (`main:logs/phase2_mlp_profiling_outputs.log`, `main:logs/phase2_mlp_profiling_outputs_cuda_event.log`).
8. Attention profiler asserts `model_config.num_layers % max_pipeline_parallel_size == 0`, which fails
   for TinyLlama (22 layers) (`main:logs/phase2_attn_profiling_run0.log` lines 30 and 31).
9. sarathi-serve `vidur` branch: `TypeError: BaseLLMEngine.step() takes 1 positional argument but 2
   were given` on the first request with pipeline parallel size 1 (HTTP 500)
   (`main:logs/phase2_sarathi_serve_summary.log`).

## Dataset problems

- `splitwise_conv.csv` contains requests longer than Llama-2-7b's 4096-token context (`num_prefill_tokens`
  max 14050, `logs/phase1_report_facts.log`); Vidur shrinks them to `max_tokens` instead of rejecting
  them.
- `arrived_at` timestamps in the trace are not used in the README configuration (Poisson arrivals).
- Provenance and licence of the Splitwise-derived traces are not documented in the files we read:
  **TODO (ME)**.
- Shipped profiling data for Llama-2-7b on a100 covers at most `prefill_chunk_size` 4096,
  `kv_cache_size` 4032 and `batch_size` 128 (`RESULTS.md` Differences 3), less than the README's
  prediction ranges.

## Computational limitations

- GPU: NVIDIA GeForce RTX 3060 Laptop GPU with 6144 MiB VRAM (`main:FEASIBILITY.md` 0.1), versus
  80GB A100s in the paper (p8).
- RAM: 9.7 GiB visible to WSL, swap 8.0 GiB (`main:FEASIBILITY.md` Host); MemTotal 10182304 kB
  (`logs/phase1_env.log`). One simulator run was OOM-killed (`RESULTS.md` Issues 3).
- The machine was shared with another agent's GPU and RAM workload during Phase 1; wall-clock times
  are affected (`RESULTS.md`).
- WSL does not report per-process GPU memory; GPU memory is measured device-wide
  (`main:FEASIBILITY.md` 0.2).

## Deviations from the original experiment

From `main:FEASIBILITY.md` (it defines D1 and D2 only):

- **D1**: `VLLM_USE_FLASHINFER_SAMPLER=0` for vLLM, because FlashInfer's sampler needs `nvcc` and WSL
  has no CUDA toolkit. Effect: top-k/top-p sampling uses vLLM's PyTorch implementation.
- **D2**: sarathi-serve built with `CUDA_HOME=~/micromamba/envs/cuda-12.1` (nvcc 12.1.105) instead of
  the README's mamba environment; `~/.venv-sarathi` replaces the mamba env.

From `RESULTS.md` (Phase 1 simulator runs):

- Predictor training threads 4 (2 for Llama-2-7b) instead of all cores.
- `--no-metrics_config_store_plots`.
- Explicit absolute input, output and cache paths.
- Seeds set on four flags, equal per run (42, 43, 44).
- `nice -n 10`, `WANDB_MODE=disabled`, `/usr/bin/time -v`.
- Results tied to the archived predictor cache.
- Capped rerun only: trace `max_tokens` 4096 for Llama-2-7b.

Not deviations of the reproduction but changes made for the Phase 2 smoke tests (in
`~/vidur-phase2` branch `ext-profiling` and `~/sarathi-serve` branch `local-fixes`): attention
`profile_method` kineto to cuda_event, `get_max_num_blocks` divisor fix, flashinfer 0.1.1 pin, and the
sarathi `step` call fix (`main:logs/phase2_attn_profiling_run0.log`, `run1.log`,
`main:logs/phase2_flashinfer011_install.log`, `main:logs/phase2_sarathi_fix1.log`).

The paper's own experimental settings not replicated (traces, scheduler, capacity-relative load,
real A100s): see Differences. Full list of what the original experiment did: **TODO (ME)**

## Phase 2 feasibility evidence (smoke tests, not results)

All on the RTX 3060 Laptop GPU with TinyLlama/TinyLlama-1.1B-Chat-v1.0 and the smallest settings.
These show that the tools run on this machine; the numbers are not measurements for the report.

**MLP profiling** (`~/vidur-phase2`, `main:logs/phase2_mlp_profiling_run.log`,
`main:logs/phase2_mlp_profiling_outputs.log`, `..._cuda_event.log`):

- Command: `python -m vidur.profiling.mlp.main --models TinyLlama/TinyLlama-1.1B-Chat-v1.0 --num_gpus 1 --num_tensor_parallel_workers 1 --max_tokens 8`; num_tokens profiled 8, 4, 2, 1.
- Default `record_function`: exit 0, wall 0:26.06, max RSS 677300 kB; `mlp.csv` has 5 lines (header plus 4 rows) and no timing columns.
- `--profile_method cuda_event`: exit 0, wall 0:20.65, max RSS 677076 kB; `mlp.csv` 5 lines with 58 columns.
- `main:logs/phase2_compat_check.log` reports "shipped columns: 58 ours: 58", same order, against the shipped a100 Llama-2-7b `mlp.csv`. The log does not name the compared TinyLlama file; the `cuda_event` output is the only one of the two with 58 columns.

**Attention profiling** (`main:logs/phase2_attn_profiling_run0.log` to `run3.log`,
`main:logs/phase2_attn_profiling_run3_outputs.log`):

- Command: `python -m vidur.profiling.attention.main --models TinyLlama/TinyLlama-1.1B-Chat-v1.0 --num_gpus 1 --num_tensor_parallel_workers 1 --max_seq_len 64 --max_model_len 64 --min_batch_size 1 --max_batch_size 1`.
- Attempts 0 to 2 failed (layer-count assert, Ninja missing, flashinfer API mismatch; see Code problems and Installation problems).
- Attempt 3 with flashinfer 0.1.1: exit 0, wall 0:24.26, max RSS 761928 kB. `attention.csv` 4 lines (header plus 3 rows). It has 36 columns versus 31 in the shipped a100 Llama-2-7b `attention.csv`; the extra 5 are the `attn_kv_cache_save` statistics.

**sarathi-serve** (`main:logs/phase2_sarathi_serve_summary.log`, `main:logs/phase2_sarathi_serve_run2_summary.log`, `main:logs/phase2_sarathi_serve_run2_request.log`):

- Run 1: server started (TinyLlama, fp16 after "Casting torch.bfloat16 to torch.float16", 7329 GPU blocks); the first `/v1/completions` request returned HTTP 500 with the `BaseLLMEngine.step()` TypeError. GPU peak 5235 MiB over a 0 MiB baseline.
- Run 2 after the one-line fix on branch `local-fixes`: request `"The capital of France is"`, `max_tokens` 32, HTTP 200 in 1.367453 s. First server log line 20:23:05, readiness 20:23:34. GPU peak 5271 MiB over a 0 MiB baseline (device-wide `nvidia-smi`).
- dtype differs from the Phase 0 vLLM run (vLLM bfloat16, sarathi float16; TinyLlama `config.json` `torch_dtype` bfloat16) (`main:logs/phase2_sarathi_serve_run2_summary.log`).
