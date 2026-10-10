# Local patches to upstream repositories

These code changes live in local clones outside this repository. They are exported here with
`git format-patch -1` so the Phase 2 smoke tests can be reproduced. Apply with `git am <file>` (keeps
the commit) or `git apply <file>` from the root of the upstream checkout.

| Patch file | Upstream repo | Base commit (parent) | Local source | What it changes |
|---|---|---|---|---|
| `0001-Attention-profiling-use-cuda_event-timer-support-lay.patch` | https://github.com/microsoft/vidur | `c9b473bcf078804c16ecfc99eb4324078fc81c82` (local, not upstream; see note) | `~/vidur-phase2` branch `ext-profiling`, commit `6a452955c195296882ef8f1436a44efcd2648b78` | `vidur/profiling/attention/attention_wrapper.py`: timer `profile_method` kineto to cuda_event. `vidur/profiling/utils/__init__.py`: `get_max_num_blocks` uses the largest pipeline degree that divides `num_layers` instead of asserting (needed for TinyLlama, 22 layers) |
| `0001-Fix-step_async-for-pipeline_parallel_size-1.patch` | https://github.com/microsoft/sarathi-serve | `c94dbf438711a4670dbf7477175062e87748999d` (upstream branch `vidur`) | `~/sarathi-serve` branch `local-fixes`, commit `03233cb062b35238b10f6d50604f7afd2a348c69` | `sarathi/engine/async_llm_engine.py`: `step_async` passes `block=False` only to `PipelineParallelLLMEngine.step`; `BaseLLMEngine.step` takes no argument (pipeline_parallel_size 1 failed with `TypeError: BaseLLMEngine.step() takes 1 positional argument but 2 were given`) |

Note on the vidur patch base: its parent `c9b473b` is a local commit ("Add TinyLlama-1.1B-Chat-v1.0
model config for profiling", 15 lines in `vidur/config/model_config.py`) on top of upstream
`abae7f63aa857300f5cdc6f5e0d27860cd24721b`. That commit is not exported here. The patch touches
different files and was checked to apply cleanly to upstream `abae7f6` with `git apply --check`
(rc 0); the sarathi-serve patch was checked the same way against `c94dbf4` (rc 0). Profiling
TinyLlama also needs the model config from `c9b473b`.

Evidence for why each change was made: `logs/phase2_attn_profiling_run0.log`,
`logs/phase2_attn_profiling_run1.log`, `logs/phase2_sarathi_serve_summary.log`,
`logs/phase2_sarathi_fix1.log`.
