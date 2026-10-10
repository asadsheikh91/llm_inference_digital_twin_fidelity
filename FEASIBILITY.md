# Phase 0 Feasibility Log

Last updated: 2026-10-10

Every number in this file comes from a log in `logs/`. The log is named next to each item.

| Step | Verdict |
|------|---------|
| 0.1 GPU visible in WSL | GO |
| 0.2 vLLM serves TinyLlama-1.1B | GO (with deviation D1) |
| 0.3 sarathi-serve installs and imports | NO-GO as of now: README install fails, fixes not yet tried (awaiting decision) |
| 0.4 vLLM serves LLaVA-OneVision-0.5B with an image | GO (with deviation D1) |
| 0.5 Vidur cloned and installed | GO |

## Deviations

### D1: FlashInfer sampler disabled for vLLM (0.2)

- Setting: `VLLM_USE_FLASHINFER_SAMPLER=0`, set on the command line for the run only. It is not in any config file.
- Reason: on the first attempt, vLLM's sampler warmup called FlashInfer's top-k/top-p sampling kernel. FlashInfer compiles that kernel on first use, which needs `nvcc`. No CUDA toolkit is installed in WSL: `CUDA_HOME` is unset, `nvcc` is not on PATH, and `/usr/local/cuda` does not exist. The engine failed with `RuntimeError: Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist` (`logs/phase0_tinyllama_server.log` line 119, 17:17:20; analysis in `logs/phase0_tinyllama_diagnosis.log`).
- Effect: top-k/top-p sampling ran through vLLM's PyTorch implementation instead of FlashInfer. The server log confirms this: `FlashInfer top-p/top-k sampling disabled via VLLM_USE_FLASHINFER_SAMPLER=0.` (`logs/phase0_tinyllama_retry_server.log` line 28).
- Related: pip installed an `nvcc` inside the venv at `~/.venv-vllm/lib/python3.10/site-packages/nvidia/cu13/bin/nvcc`, release 13.4 (V13.4.92). The driver supports CUDA 13.0. FlashInfer does not search that path. Pointing `CUDA_HOME` at it, or installing a CUDA 13.0 toolkit in WSL, has not been tried (`logs/phase0_tinyllama_diagnosis.log`).

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

## 0.3 sarathi-serve installs and imports: NO-GO as of now (0 of 2 allowed fixes tried)

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
- Fixes: none tried yet. Both candidate fixes provide a CUDA 12.x `nvcc`, which needs approval first:
  1. Install a pip `nvcc` 12.1 into `~/.venv-sarathi` and point `CUDA_HOME` at it, for this build only.
  2. Install a CUDA 12.x toolkit in WSL. Needs sudo.
- Not yet answered: whether sarathi-serve's CUDA kernels and its pinned flashinfer support this GPU (compute capability 8.6). The README says it was tested with CUDA 12.1 on A100 and A40 GPUs.

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

## Environment versions

| Venv | Python | Key packages |
|------|--------|--------------|
| `~/.venv-vidur` | 3.10.12 | see `docs/environment/vidur-freeze.txt` |
| `~/.venv-vllm` | 3.10.12 | vllm 0.31.0, torch 2.13.0+cu130, transformers 5.17.0 (`logs/phase0_vllm_env.log`); py-spy 0.4.2 added for diagnosis |
| `~/.venv-sarathi` | 3.10.12 | empty apart from pip; README install failed (`logs/phase0_sarathi_install.log`) |
