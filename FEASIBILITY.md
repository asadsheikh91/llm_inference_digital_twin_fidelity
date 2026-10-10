# Feasibility Log (Phase 0 and Phase 2)

Last updated: 2026-10-10

Every number in this file comes from a log in `logs/`. The log is named next to each item.

| Step | Verdict |
|------|---------|
| 0.1 GPU visible in WSL | GO |
| 0.2 vLLM serves TinyLlama-1.1B | GO (with deviation D1) |
| 0.3 sarathi-serve installs and imports | GO for install and import (with deviation D2, fix 2a); serving tested in 2.C |
| 0.4 vLLM serves LLaVA-OneVision-0.5B with an image | GO (with deviation D1) |
| 0.5 Vidur cloned and installed | GO |
| 2.1 sarathi venv pins (transformers, numpy) | DONE |
| 2.2 Vidur MLP profiling smoke test (TinyLlama) | GO (with deviations D3, D4) |
| 2.A Profiling CSV compatibility with shipped A100 data | Format compatible; timing method differs (see 2.A) |
| 2.B Vidur attention profiling smoke test (TinyLlama) | GO (with deviations D3, D4, D5) |
| 2.C sarathi-serve serves TinyLlama, one request | GO (with deviation D6) |

## Deviations

### D1: FlashInfer sampler disabled for vLLM (0.2)

- Setting: `VLLM_USE_FLASHINFER_SAMPLER=0`, set on the command line for the run only. It is not in any config file.
- Reason: on the first attempt, vLLM's sampler warmup called FlashInfer's top-k/top-p sampling kernel. FlashInfer compiles that kernel on first use, which needs `nvcc`. No CUDA toolkit is installed in WSL: `CUDA_HOME` is unset, `nvcc` is not on PATH, and `/usr/local/cuda` does not exist. The engine failed with `RuntimeError: Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist` (`logs/phase0_tinyllama_server.log` line 119, 17:17:20; analysis in `logs/phase0_tinyllama_diagnosis.log`).
- Effect: top-k/top-p sampling ran through vLLM's PyTorch implementation instead of FlashInfer. The server log confirms this: `FlashInfer top-p/top-k sampling disabled via VLLM_USE_FLASHINFER_SAMPLER=0.` (`logs/phase0_tinyllama_retry_server.log` line 28).
- Related: pip installed an `nvcc` inside the venv at `~/.venv-vllm/lib/python3.10/site-packages/nvidia/cu13/bin/nvcc`, release 13.4 (V13.4.92). The driver supports CUDA 13.0. FlashInfer does not search that path. Pointing `CUDA_HOME` at it, or installing a CUDA 13.0 toolkit in WSL, has not been tried (`logs/phase0_tinyllama_diagnosis.log`).

### D2: sarathi-serve built against a conda CUDA 12.1 toolchain (0.3)

- Setting: `CUDA_HOME=~/micromamba/envs/cuda-12.1` on the pip command line, for the build only. Not exported, not in any file.
- Reason: sarathi-serve's `setup.py` compiles CUDA extensions and needs `nvcc`. WSL has no CUDA toolkit, and PyPI's `nvidia-cuda-nvcc-cu12` wheels (12.1 to 12.9) ship no `nvcc` binary (fix 1).
- Effect: the kernels were compiled with nvcc 12.1.105, which matches torch 2.3.0's CUDA 12.1 build. The README's mamba env was replaced by `~/.venv-sarathi` per the project setup notes; micromamba is used only to provide the toolchain.

### D3: Vidur profilers run as modules from the worktree root (2.2, 2.B)

- Setting: `python -m vidur.profiling.mlp.main` and `python -m vidur.profiling.attention.main`, run from `~/vidur-phase2`.
- Reason: `docs/profiling.md` says `python vidur/profiling/mlp/main.py`. That fails with `ModuleNotFoundError: No module named 'vidur'` because `vidur/` has no `__init__.py`, so `find_packages` returns `[]` and the editable install maps nothing (`MAPPING = {}`) (`logs/phase2_vidur_install.log`). Vidur's README runs its simulator the same way (`python -m vidur.main`).

### D4: `cuda_event` timing instead of trace-based timing (2.2, 2.B)

- MLP: `--profile_method cuda_event`. The default `record_function` run exited 0, but its CSV had no `time_stats.*` columns. Its profiler trace has 201 `vidur_*` annotations and 362 `cuda_runtime` events but 0 GPU kernel events, so every operation's time came out as 0 and was dropped (`logs/phase2_mlp_profiling_outputs.log`, `logs/phase2_mlp_record_function_trace_sample.json`).
- Attention: the method is hard-coded to `kineto` in `attention_wrapper.py`. Changed to `cuda_event` in the worktree, on instruction (commit `6a45295` on `ext-profiling`).
- Effect: CUDA-event timing spans everything between two events, which can include gaps between kernel launches. Trace-based timing sums kernel durations only. The shipped A100 data appears to be trace-based (see 2.A). So profiles from this machine are not directly comparable with the shipped profiles. This is a methodology confound.

### D5: Vidur attention profiling changes and FlashInfer pin (2.B)

- `get_max_num_blocks` asserted `num_layers % 8 == 0`. TinyLlama has 22 layers. Changed to use the largest pipeline degree <= 8 that divides `num_layers`. Unchanged for every shipped model (32, 48 and 80 layers) (commit `6a45295` on `ext-profiling`).
- Attention runs set `PATH=~/.venv-sarathi/bin:$PATH` (what activating the venv does) and `CUDA_HOME=~/micromamba/envs/cuda-12.1` on the command line only.
- flashinfer pinned to 0.1.1+cu121torch2.3 in `~/.venv-sarathi`, replacing 0.2.0.post1, which has an incompatible `append_paged_kv_cache` signature (see 2.B).

### D6: sarathi-serve `step_async` fix on a local branch (2.C)

- Branch `local-fixes` in `~/sarathi-serve`, made from `vidur`. Commit `03233cb`. The `vidur` branch is unchanged (`vidur` and `origin/vidur` both at `c94dbf4`).
- Change: `step_async` passes `block=False` to `engine.step` only when the engine is a `PipelineParallelLLMEngine` (`logs/phase2_sarathi_fix1.log`).
- Reason: commit `c94dbf4` (2024-07-23) made `step_async` always pass `False`. `BaseLLMEngine.step(self)`, used when pipeline parallel size is 1, takes no arguments, so the OpenAI server failed every request with `TypeError: BaseLLMEngine.step() takes 1 positional argument but 2 were given` (`logs/phase2_sarathi_serve_server.log`).

## Host (`logs/phase0_host_gpu.log`, `logs/phase0_vllm_env.log`)

- WSL2, kernel 6.18.33.2-microsoft-standard-WSL2
- RAM visible to WSL: 9.7 GiB, swap 8.0 GiB (after the WSL restart)
- Disk: 938 GB free on `/`
- System Python: 3.10.12
- No CUDA toolkit in WSL: `nvcc` not on PATH, no `/usr/local/cuda*`. The CUDA driver libraries come from Windows through `/usr/lib/wsl/lib` (`libcuda.so*`, `libnvidia-ml.so.1`).

## 0.1 GPU visible in WSL: GO

Evidence: `logs/phase0_host_gpu.log`, `logs/phase0_vllm_env.log`

- `nvidia-smi` inside WSL: NVIDIA GeForce RTX 3060 Laptop GPU, bus 00000000:01:00.0
- VRAM: 6144 MiB total. 430 MiB in use at idle with no CUDA process running, which is the Windows display's share.
- Driver 581.83 (Windows host), NVIDIA-SMI 580.108, max supported CUDA version 13.0
- Power cap 115 W
- torch in `~/.venv-vllm`: `torch.cuda.is_available()` is True, device capability (8, 6)

## 0.2 vLLM serves TinyLlama-1.1B: GO (with deviation D1)

### Environment (`logs/phase0_vllm_env.log`)

| Package | Version |
|---------|---------|
| Python | 3.10.12 |
| vllm | 0.31.0 |
| torch | 2.13.0+cu130 (CUDA build 13.0) |
| transformers | 5.17.0 |
| flashinfer-python | 0.7.0.post1 |
| triton | 3.7.1 |
| torchvision | 0.28.0 |
| torchaudio | 2.11.0 (version number differs from torch 2.13.0; not used in Phase 0) |

`torch.cuda.is_available()`: True.

### Model download (`logs/phase0_modelsize_TinyLlama_TinyLlama-1.1B-Chat-v1.0.log`, `logs/phase0_tinyllama_server.log`)

- Repo total 2,202,470,207 bytes, of which `model.safetensors` is 2,200,119,864 bytes
- vLLM reported `Time spent downloading weights ...: 543.267830 seconds` (line 21)
- The server log showed nothing during the download, which looked like a stall. Diagnosis showed the `.incomplete` blob still growing (`logs/phase0_tinyllama_diagnosis.log`).

### Attempt 1: failed (`logs/phase0_tinyllama_server.log`)

Command: `vllm serve TinyLlama/TinyLlama-1.1B-Chat-v1.0 --max-model-len 2048 --gpu-memory-utilization 0.8 --port 8000`

- Got through weight loading (5.82 s, 2.05 GiB), torch.compile (14.32 s), CUDA graph capture, and KV cache allocation (2.16 GiB, 103,088 tokens)
- Failed at 17:17:20 during sampler warmup, 45 s after the download finished at 17:16:35. Root cause: FlashInfer could not find `nvcc` (see D1).
- Peak device-wide GPU memory: 5286 MiB at 17:17:19.667 (`logs/phase0_tinyllama_gpumem.csv`)
- No out-of-memory events in `dmesg` (`logs/phase0_tinyllama_diagnosis.log`)

### Attempt 2: succeeded (`logs/phase0_tinyllama_retry_server.log`)

Command: `VLLM_USE_FLASHINFER_SAMPLER=0 vllm serve TinyLlama/TinyLlama-1.1B-Chat-v1.0 --max-model-len 2048 --gpu-memory-utilization 0.8 --port 8000`

Not eager mode (`--enforce-eager` was not used). torch.compile and CUDA graphs were active.

- Pre-run checks (`logs/phase0_tinyllama_retry_prep.log`): no leftover server or sampler, port 8000 free, GPU at 430 MiB in 5 samples
- Weights served from cache. No download line appears in the log.
- Warm startup: launched 17:34:37, `Starting vLLM server on http://0.0.0.0:8000` at 17:35:49, so 72 s. Breakdown from the log:
  - weights load 1.83 s
  - model loading 5.846600 s
  - torch.compile 11.68 s
  - engine init (profile, KV cache, warmup) 43.42 s
- KV cache: 2.16 GiB available, 103,088 tokens, maximum concurrency 50.34x at 2,048 tokens per request

Request (`logs/phase0_tinyllama_request.log`):

- `POST /v1/completions`, prompt `"The capital of France is"`, `max_tokens` 32, `temperature` 0.8, `top_p` 0.95, `top_k` 50
- HTTP 200 in 0.673328 s, 6 prompt tokens, 32 completion tokens, `finish_reason` `length`
- Response text: `" located on the banks of the Seine River in the northern part of the country.\n\n4. Los Angeles, California The capital of California is located in the"`

GPU memory (`logs/phase0_tinyllama_retry_gpumem.csv`, summary in `logs/phase0_tinyllama_retry_summary.log`):

- Idle baseline: 430 MiB (8 samples before launch, min = max = 430)
- Peak: 5349 MiB at 17:35:43.226
- Peak minus baseline: 4919 MiB
- Measured device-wide with `nvidia-smi` every 0.5 s. WSL does not report per-process GPU memory.

Shutdown: SIGINT to the API server. vLLM logged `force killing remaining process EngineCore pid 20730` (lines 103 and 104). GPU memory returned to 430 MiB.

## 0.3 sarathi-serve installs and imports: GO for install and import (with deviation D2)

Evidence: `logs/phase0_sarathi_size.log`, `logs/phase0_sarathi_install.log`

- `df -h ~` before starting: 938G available
- Download sizes, checked before starting:
  - repo 2,877 KiB (GitHub API)
  - torch 2.3.0 plus its pinned CUDA 12.1 wheels: 2,802,693,816 bytes (PyPI)
  - flashinfer 0.2.0.post1+cu121torch2.3 wheel: 405,796,554 bytes
  - unpinned dependencies not sized
- Clone: `~/sarathi-serve`, branch `vidur`, commit `c94dbf438711a4670dbf7477175062e87748999d` (2024-07-23)
- Venv: `~/.venv-sarathi`, Python 3.10.12. The README uses a mamba env; a venv is used here per the project's setup notes.
- README install command: `pip install -e . --extra-index-url https://flashinfer.ai/whl/cu121/torch2.3/`
  - Started 17:38:06. Build dependencies (torch 2.3) were downloaded.
  - Failed at 17:53:20 in "Getting requirements to build editable" with `RuntimeError: Cannot find CUDA_HOME. CUDA must be available to build the package.` (log line 52)
  - Cause: `setup.py` builds three CUDA extensions (`sarathi.pos_encoding_ops`, `sarathi.layernorm_ops`, `sarathi.activation_ops`) and stops at line 23 when torch's `CUDA_HOME` lookup finds no toolkit. WSL has no CUDA toolkit (see Host).
- `import sarathi`: fails with `ModuleNotFoundError: No module named 'sarathi'`, because nothing was installed. torch is not installed in the venv either.
- Fix 1, approved: install a pip `nvcc` 12.x into `~/.venv-sarathi` and point `CUDA_HOME` at it (`logs/phase0_sarathi_fix1.log`)
  - Prerequisite present: gcc/g++ 11.4.0 on Ubuntu 22.04.5
  - Installed `nvidia-cuda-nvcc-cu12==12.1.105` (19,996,355-byte wheel) and `nvidia-cuda-runtime-cu12==12.1.105` (823,596-byte wheel). `nvidia/cuda_nvcc/bin/` contains only `ptxas`. There is no `nvcc` binary.
  - Downloaded, but did not install, the newest wheel of every later cu12 minor: 12.2.140, 12.3.107, 12.4.131, 12.5.82, 12.6.85, 12.8.93, 12.9.86. Listed each wheel's `bin/` entries: every one has only `ptxas`.
  - Result: PyPI has no CUDA 12 `nvcc`, so fix 1 cannot be executed as a pip install. No sarathi-serve build was run.
  - The two nvidia packages above are still installed in `~/.venv-sarathi`. `import sarathi` still fails with `ModuleNotFoundError`.
- Fix 2a, approved: a CUDA 12.1 toolchain from NVIDIA's conda channel, installed with micromamba (no sudo), with `CUDA_HOME` set for the build only (`logs/phase0_sarathi_fix2.log`)
  - micromamba 2.9.0-0 static binary at `~/micromamba/bin/micromamba` (18,292,808 bytes). sha256 `366cd9cd...fafb3e3` matches the published checksum.
  - Dry run first:
    - nvcc plus cudart only: 56,762,248 bytes. Not enough, because torch's `ATen/cuda/CUDAContextLight.h` includes `cusparse.h`, `cublas_v2.h`, `cublasLt.h` and `cusolverDn.h`.
    - Full set: 894,307,537 bytes
  - Installed into `~/micromamba/envs/cuda-12.1` (1.2G on disk) from `nvidia/label/cuda-12.1.1`:
    - cuda-nvcc 12.1.105, cuda-cudart(-dev) 12.1.105, cuda-cccl 12.1.109
    - libcublas(-dev) 12.1.3.1, libcusparse(-dev) 12.1.0.106, libcusolver(-dev) 11.4.5.107
    - These versions match the CUDA 12.1 wheels torch 2.3.0 depends on.
  - `nvcc --version` reports release 12.1, V12.1.105. The env has no `lib64`; torch 2.3 falls back to `CUDA_HOME/lib` (`torch/utils/cpp_extension.py` lines 1203 to 1209).
  - Build command, the README's unchanged except for the env var: `CUDA_HOME=~/micromamba/envs/cuda-12.1 pip install -e . --extra-index-url https://flashinfer.ai/whl/cu121/torch2.3/`
  - Result: exit 0, 18:23:17 to 18:35:13. `Building editable for sarathi` finished with status `done`. Built `sarathi/activation_ops`, `layernorm_ops` and `pos_encoding_ops` `.so` files.
- Import test, run from `~` (`logs/phase0_sarathi_import.log`):
  - torch 2.3.0+cu121, CUDA build 12.1, `torch.cuda.is_available()` True, device capability (8, 6)
  - `import sarathi` OK (version 0.1.7). The three extension modules load. `from sarathi import LLMEngine` OK. `sarathi.model_executor.model_loader` imports OK.
  - Kernel check: `layernorm_ops.rms_norm` ran on the GPU on a 4x2048 fp16 tensor. Max abs diff vs a PyTorch reference: 0.0.
  - flashinfer 0.2.0.post1+cu121torch2.3 imports.
- Follow-up after Phase 0 (`logs/phase1_sarathi_pins.log`, `logs/phase1_sarathi_import_after_pins.log`):
  - Pinned transformers 4.42.4 and numpy 1.26.4, the newest 4.x and 1.x releases uploaded before the `vidur` branch commit date (2024-07-23). The repo itself has no version pins.
  - The pins also changed huggingface_hub (2.2.0 to 0.36.2) and tokenizers (0.23.3 to 0.19.1). `pip check`: no broken requirements.
  - Freezes before and after: `logs/phase1_sarathi_freeze_before_pins.txt`, `logs/phase1_sarathi_freeze_after_pins.txt`
  - Rerun checks pass: transformers now sees torch, and `rms_norm` max abs diff is 0.0.
- Caveats as originally recorded (the first two are resolved by the pins above):
  - transformers resolved to 5.19.0, because `requirements.txt` says only `>= 4.37.0`. It prints `Disabling PyTorch because PyTorch >= 2.5 is required but found 2.3.0`. sarathi only imports config and tokenizer classes from transformers, and those import fine. Whether transformers 5.x configs behave the way this 2024 code expects will only show when a model is served.
  - numpy resolved to 2.2.6 alongside torch 2.3.0
  - The README says sarathi-serve was tested with CUDA 12.1 on A100 and A40 GPUs. Serving a model on this RTX 3060 (sm_86, 6 GB) was tried in Phase 2 (see 2.C).

## 0.4 vLLM serves LLaVA-OneVision-0.5B with an image: GO (with deviation D1)

Evidence: `logs/phase0_modelsize_llava-hf_llava-onevision-qwen2-0.5b-ov-hf.log`, `logs/phase0_llava_prep.log`, `logs/phase0_llava_server.log`, `logs/phase0_llava_request.log`, `logs/phase0_llava_gpumem.csv`, `logs/phase0_llava_summary.log`

Command: `VLLM_USE_FLASHINFER_SAMPLER=0 vllm serve llava-hf/llava-onevision-qwen2-0.5b-ov-hf --max-model-len 4096 --gpu-memory-utilization 0.8 --port 8000`

D1 was applied on the command line for this run too. No other FlashInfer path asked for `nvcc`: the server log has no `nvcc` or ERROR lines.

- Support: vLLM 0.31.0 resolved `LlavaOnevisionForConditionalGeneration` (log line 10)
- Download: repo top-level files total 1,799,151,227 bytes. vLLM reported 276.493459 s spent downloading weights.
- Startup:
  - launched 17:54:20, `Starting vLLM server` at 18:03:59, download included
  - weights load 2.48 s; model loading 1.68 GiB
  - torch.compile 84.28 s
  - engine init 123.05 s
- KV cache: 2.29 GiB available, 200,000 tokens, maximum concurrency 48.83x at 4,096 tokens per request
- Request:
  - one chat completion with one image: `data/phase0/test_shapes.png`, a 336x336 PNG made by `scripts/make_test_image.py`, sha256 `34b7567b...c8bdcd9`
  - prompt "Describe the shapes and colors in this image.", temperature 0.0, `max_tokens` 48
  - HTTP 200 in 1.240 s, 1502 prompt tokens, 33 completion tokens, `finish_reason` `stop`
- Response: "The image features two primary shapes: a red circle and a blue square. The red circle is positioned above the blue square, both set against a white background." The shapes and colors are correct. The layout is only partly right: the circle is top-left and the square bottom-right.
- GPU memory, device-wide `nvidia-smi` every 0.5 s:
  - idle baseline 0 MiB (5 samples before launch, min = max = 0)
  - peak 4969 MiB at 18:04:33.838, during the request
  - peak minus baseline: 4969 MiB
  - The baseline differs from the 430 MiB seen in 0.2. The Windows display was no longer using the NVIDIA GPU at this time.
- Shutdown: SIGINT. vLLM force-killed EngineCore pid 25016 (lines 108 and 109). GPU memory returned to 0 MiB.

## 0.5 Vidur cloned and installed: GO

Evidence: `logs/phase0_vidur.log`, `logs/phase0_vidur_unshallow.log`, `logs/phase0_tinyllama_retry_prep.log`, `docs/environment/vidur-freeze.txt`

- Location: `~/vidur` (outside this repo). Source: https://github.com/microsoft/vidur
- Commit: `abae7f63aa857300f5cdc6f5e0d27860cd24721b` (2026-08-24)
- First cloned shallow (`--depth 1`) after a full clone failed on a dropped connection. Then `git fetch --unshallow` ran with exit 0. `git rev-parse --is-shallow-repository` now prints `false`, and the history has 26 commits.
- Venv: `~/.venv-vidur`, Python 3.10.12
- Installed with `pip install -r ~/vidur/requirements.txt`, which does not list torch. Resolved versions:
  - numpy 2.2.6, pandas 2.3.3, scikit-learn 1.7.2
  - wandb 0.30.0, kaleido 1.5.0, ddsketch 3.0.1, fasteners 0.20
  - plotly 7.1.0, plotly-express 0.4.1, matplotlib 3.10.9, seaborn 0.13.2
- Smoke test: `python -m vidur.main --help` (from `~/vidur`) exits 0. No simulation has been run yet.
- Vidur's `environment.yml` also lists ray, randomname, paretoset and streamlit, which are not in requirements.txt. They are not installed because the simulator imports without them.
- Caveat: numpy resolved to 2.x. Vidur predates numpy 2. If the simulator hits numpy-2 incompatibilities, pin `numpy<2`.

## Phase 2

Phase 2 logs are `logs/phase2_*`. The transformers and numpy pins (2.1) were logged as `logs/phase1_*`.

### 2.1 sarathi venv pins: DONE

Evidence: `logs/phase1_sarathi_pins.log`, `logs/phase1_sarathi_import_after_pins.log`. Details are under 0.3 (Follow-up after Phase 0).

- transformers 4.42.4 (uploaded 2024-07-11) and numpy 1.26.4 (uploaded 2024-02-05), the newest releases before the sarathi `vidur` branch commit date
- `rms_norm` check still passes, max abs diff 0.0

### 2.2 Vidur MLP profiling smoke test: GO (with deviations D3, D4)

Evidence: `logs/phase2_vidur_worktree.log`, `logs/phase2_tinyllama_model_config.log`, `logs/phase2_vidur_install.log`, `logs/phase2_mlp_profiling_prep.log`, `logs/phase2_mlp_profiling_run.log`, `logs/phase2_mlp_profiling_outputs.log`, `logs/phase2_mlp_profiling_run_cuda_event.log`, `logs/phase2_mlp_profiling_outputs_cuda_event.log`, `logs/phase2_mlp_tinyllama_cuda_event.csv`

- Worktree: `~/vidur-phase2`, branch `ext-profiling`, from `~/vidur` `main` at `abae7f6`. `~/vidur` itself stayed on `main` with a clean working tree.
- Model config: `docs/profiling.md` refers to `data/model_configs/*.yml`, which does not exist at this commit. The profiler reads Python classes from `vidur/config/model_config.py`, so `TinyLlama_1_1BModelConfig` was added there from the model's `config.json` (commit `c9b473b` on `ext-profiling`).
- Install: `pip install -e . --no-deps` into `~/.venv-sarathi`. No other packages were needed. The freeze diff shows only the added editable `vidur`. torch 2.3.0, transformers 4.42.4 and numpy 1.26.4 unchanged.
- GPU idle baseline: 317 MiB, no compute processes
- Default `record_function` run: exit 0 in 26.06 s, but no timing columns (see D4)
- `cuda_event` run: `--models TinyLlama/TinyLlama-1.1B-Chat-v1.0 --num_gpus 1 --num_tensor_parallel_workers 1 --max_tokens 8 --profile_method cuda_event`
  - exit 0 in 20.65 s, peak RSS 677,076 KB
  - `mlp.csv`: 5,712 bytes, 4 rows (8, 4, 2 and 1 tokens), 58 columns
  - `mlp_up_proj` mean in ms: 0.2178463988006115 (8 tokens), 0.16837440207600593 (1 token)

### 2.A Profiling CSV compatibility with shipped A100 data

Evidence: `logs/phase2_compat_check.log`

- Our `mlp.csv` and the shipped `data/profiling/compute/a100/meta-llama/Llama-2-7b-hf/mlp.csv` have the same 58 columns in the same order. The shipped file has 1,044 rows: 259 token counts (1 to 4,096) at TP 1, 2, 4 and 8.
- The execution time predictor (`vidur/execution_time_predictor/sklearn_execution_time_predictor.py`):
  - filters rows on `n_head`, `n_kv_head`, `n_embd`, `n_expanded_embd`, `use_gated_mlp`, `vocab_size` and `num_tensor_parallel_workers`
  - uses `num_tokens` as its only feature
  - trains on `time_stats.<op>.median` for 9 operations: `attn_pre_proj`, `attn_post_proj`, `mlp_up_proj`, `mlp_down_proj`, `mlp_act`, `input_layernorm`, `post_attention_layernorm`, `attn_rope`, `add`. `emb` and the min, max, mean and std columns are not used.
- Profile method of the shipped A100 data: no record in the docs or data folders.
  - `record_function` was the default when the data was committed (`bee57da`, 2024-05-14).
  - All 10,440 shipped median values lie on a 0.5 microsecond grid: 9,726 whole microseconds and 714 half-microseconds. All 40 of our `cuda_event` medians are off that grid.
  - So the shipped data is not from `cuda_event`. The data does not show whether it came from `record_function` or `kineto`.

### 2.B Vidur attention profiling smoke test: GO (with deviations D3, D4, D5)

Evidence: `logs/phase2_attn_profiling_prep.log`, `logs/phase2_attn_profiling_run0.log`, `logs/phase2_attn_profiling_run1.log`, `logs/phase2_attn_profiling_run2_prep.log`, `logs/phase2_attn_profiling_run2.log`, `logs/phase2_attn_profiling_run2_mem.csv`, `logs/phase2_flashinfer_version_choice.log`, `logs/phase2_flashinfer011_install.log`, `logs/phase2_sarathi_import_after_flashinfer011.log`, `logs/phase2_attn_profiling_run3_prep.log`, `logs/phase2_attn_profiling_run3.log`, `logs/phase2_attn_profiling_run3_mem.csv`, `logs/phase2_attn_profiling_run3_outputs.log`, `logs/phase2_attn_tinyllama_cuda_event.csv`

Command: `python -m vidur.profiling.attention.main --models TinyLlama/TinyLlama-1.1B-Chat-v1.0 --num_gpus 1 --num_tensor_parallel_workers 1 --max_seq_len 64 --max_model_len 64 --min_batch_size 1 --max_batch_size 1`

- Attempt 0, with the `cuda_event` change: `AssertionError` in `get_max_num_blocks` after 8.77 s (22 layers, see D5). Phase 1's Llama-2-7b rerun was using about 106% CPU during attempts 0 and 1.
- Fix 1 (layer-count change): failed after 32.99 s with `RuntimeError: Ninja is required to load C++ extensions`, because FlashInfer 0.2.0.post1 tried to compile a prefill kernel it does not ship precompiled
- Fix 2 (PATH and CUDA_HOME):
  - FlashInfer compiled the kernel (19:29:49.721 to 19:30:09.598)
  - then failed after 45.97 s with `TypeError: append_paged_kv_cache() missing 1 required positional argument: 'kv_last_page_len'`
  - lowest available RAM was 6,384,624 KiB
- Cause: sarathi requires only `flashinfer >= 0.0.5`. FlashInfer 0.2 changed `append_paged_kv_cache` from 7 to 8 arguments.
- Version research:
  - sarathi set `>= 0.0.5` on 2024-06-20, the day v0.0.5 was released, and last edited its wrapper on 2024-06-23
  - sarathi's call signatures match FlashInfer source at every tag checked from v0.0.5 to v0.1.1
  - v0.1.1 (2024-07-20) is the newest release before the branch commit
- Renewed fix: pinned `flashinfer==0.1.1+cu121torch2.3`, approved download 1,262,500,987 bytes, installed with `--no-deps`
  - the freeze diff shows only the flashinfer line changed
  - torch, transformers and numpy unchanged
  - `rms_norm` max abs diff 0.0
- Final run:
  - machine quiet, GPU baseline 430 MiB
  - exit 0 in 24.26 s, peak RSS 761,928 KB
  - no compile step, no kernel or architecture errors
  - lowest available RAM 8,533,120 KiB
- `attention.csv`: 2,682 bytes, 3 rows, 36 columns. Medians in ms:

| is_prefill | prefill_chunk_size | kv_cache_size | batch_size | attn_prefill | attn_decode | attn_kv_cache_save |
|---|---|---|---|---|---|---|
| True | 64 | 0 | 1 | 0.05939200147986412 | 0.008191999979317188 | 0.043007999658584595 |
| True | 32 | 0 | 1 | 0.0942080020904541 | 0.01929599978029728 | 0.03276799991726875 |
| False | 0 | 32 | 1 | 0.006912000011652708 | 0.062463998794555664 | 0.03155200183391571 |

- Caveats:
  - sarathi wraps each `if contains_prefill` / `if contains_decode` block in a timer, so the timer records even when the block does no work. With `cuda_event`, these empty regions measure 0.006912 to 0.019296 ms here. That floor needs filtering in real profiles.
  - Compared with the shipped A100 `attention.csv`, ours has 5 extra columns (`time_stats.attn_kv_cache_save.*`) and none missing. The predictor fills `attn_kv_cache_save.median` with 0 when absent.
  - The attention profiler runs only 5 active steps per input.

### 2.C sarathi-serve serves TinyLlama: GO (with deviation D6)

Evidence: `logs/phase2_sarathi_serve_prep.log`, `logs/phase2_sarathi_serve_server.log`, `logs/phase2_sarathi_serve_request.log`, `logs/phase2_sarathi_serve_summary.log`, `logs/phase2_sarathi_serve_gpumem.csv`, `logs/phase2_sarathi_serve_mem.csv`, `logs/phase2_sarathi_fix1.log`, `logs/phase2_sarathi_serve_run2_prep.log`, `logs/phase2_sarathi_serve_run2_server.log`, `logs/phase2_sarathi_serve_run2_request.log`, `logs/phase2_sarathi_serve_run2_summary.log`, `logs/phase2_sarathi_serve_run2_gpumem.csv`, `logs/phase2_sarathi_serve_run2_mem.csv`

Command: `python -m sarathi.entrypoints.openai.api_server --model_config_model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --parallel_config_pipeline_parallel_size 1 --parallel_config_tensor_parallel_size 1 --log_level info --output_dir <scratch> --port 8000`. PATH and CUDA_HOME were set on the command line. Pipeline parallel size defaults to 2, so it is set to 1 explicitly.

- No download: sarathi loads `*.safetensors` first, and TinyLlama's `model.safetensors` was already cached
- Run 1, on the `vidur` branch:
  - startup 27 s (launched 20:16:04, first `/v1/models` 200 at 20:16:31)
  - peak 5235 MiB above a 0 MiB baseline, during startup
  - the request returned HTTP 500 with the `step_async` `TypeError` (see D6)
- Run 2, on `local-fixes` `03233cb`:
  - startup 34 s (launched 20:23:00, `# GPU blocks: 7329` at 20:23:33, first `/v1/models` 200 at 20:23:34)
  - request: same prompt and sampling settings as 0.2. HTTP 200, latency 1.367453 s (curl `time_total`), 6 prompt tokens, 32 completion tokens, `finish_reason` `length`.
  - response text: `" a city that holds a deep historical significance. The city was founded in 31 BCE by Julius Caesar, and it played a pivotal role"`
  - GPU memory: baseline 0 MiB (8 samples), peak 5271 MiB at 20:23:41.583 during the request, so peak minus baseline is 5271 MiB
  - lowest available RAM 5,930,080 KiB
  - shutdown: SIGINT did not stop the server within 30 s, so SIGTERM was sent. Afterwards no Ray processes were left and the GPU was back at 0 MiB.
- Differences from the vLLM run in 0.2:
  - dtype: vLLM served `torch.bfloat16`, the model's `torch_dtype`. sarathi logged `Casting torch.bfloat16 to torch.float16` and ran in `torch.float16` (its `--model_config_dtype` default).
  - latency for the same request: 1.367453 s on sarathi, 0.673328 s on vLLM. These are single requests on engines with different compile and CUDA-graph settings, so this is not a performance comparison.

### sarathi-serve benchmark runner (read from code, not run)

Evidence: `logs/phase2_sarathi_benchmark_runner_static.log`

- Entry point: `python -m sarathi.benchmark.main` (`BenchmarkRunnerLauncher` in `sarathi/benchmark/benchmark_runner.py`)
  - it builds `LLMEngine.from_system_config`, calls `add_request`, and drives the synchronous `step()`, with no HTTP client
  - it uses Ray for replicas
- Flags follow `sarathi/config/flat_dataclass.py`: a selectable config gets `--<field>_type`, and each subclass's fields get `--<snake_case(ClassName)>_<field>`. Examples:
  - `--request_generator_config_type SYNTHETIC|TRACE`
  - `--synthetic_request_generator_config_num_requests`
  - `--length_generator_config_type UNIFORM|ZIPF|TRACE|FIXED` and `--interval_generator_config_type POISSON|GAMMA|STATIC|TRACE`
  - `--trace_request_generator_config_trace_file`
  - plus the engine flags the server takes. Pipeline parallel size defaults to 2 here too.
- The default trace paths (`data/processed_traces/...`) are not in the sarathi clone. `sarathi/benchmark/README.md` describes an older YAML config.

## Environment versions

| Venv | Python | Key packages |
|------|--------|--------------|
| `~/.venv-vidur` | 3.10.12 | see `docs/environment/vidur-freeze.txt` |
| `~/.venv-vllm` | 3.10.12 | vllm 0.31.0, torch 2.13.0+cu130, transformers 5.17.0 (`logs/phase0_vllm_env.log`); py-spy 0.4.2 added for diagnosis |
| `~/.venv-sarathi` | 3.10.12 | sarathi 0.1.7 (editable, `~/sarathi-serve`, branch `local-fixes` `03233cb`), vidur 0.0.1 (editable, `~/vidur-phase2`, branch `ext-profiling`), torch 2.3.0+cu121, flashinfer 0.1.1+cu121torch2.3 (was 0.2.0.post1; pinned in Phase 2, `logs/phase2_flashinfer011_install.log`), triton 2.3.0, ray 2.59.0; pinned after Phase 0: transformers 4.42.4, numpy 1.26.4 (`logs/phase1_sarathi_pins.log`) |
| `~/micromamba/envs/cuda-12.1` | n/a | CUDA 12.1 build toolchain for sarathi-serve (nvcc 12.1.105), used only via `CUDA_HOME` (`logs/phase0_sarathi_fix2.log`) |
