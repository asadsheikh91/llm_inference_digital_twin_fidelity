# Redactions applied to Phase 0 and Phase 2 logs before push

Date: 2026-10-10T21:04:49+05:00

Scan of everything that would be pushed (trees of phase0-feasibility and phase1-tier-a, and git log -p main..branch for both) for API keys, tokens, passwords, email addresses, /home/<user>, private IPs and files over 50 MB.

Found: no API keys, tokens or passwords. `auth_token` appears only as a file name and path in Ray output; the token value itself is in neither tree nor history (checked with grep -F). `HF_TOKEN` appears only in Hugging Face's unauthenticated-request warning. No file or blob over 50 MB (largest pushed blob 321536 bytes). Email addresses appear only in commit metadata (author and Co-Authored-By lines) and in `git@github.com:microsoft/sarathi-serve.git`.

Redacted: `/home/<user>` replaced by `~` (sed s|/home/<user>|~|g), line counts unchanged:

- logs/phase0_llava_prep.log: 3 occurrences
- logs/phase0_llava_server.log: 2 occurrences
- logs/phase0_sarathi_fix1.log: 5 occurrences
- logs/phase0_sarathi_fix2.log: 50 occurrences
- logs/phase0_sarathi_import.log: 3 occurrences
- logs/phase0_sarathi_install.log: 7 occurrences
- logs/phase0_tinyllama_diagnosis.log: 22 occurrences
- logs/phase0_tinyllama_retry_server.log: 2 occurrences
- logs/phase0_tinyllama_server.log: 89 occurrences
- logs/phase1_sarathi_import_after_pins.log: 3 occurrences
- logs/phase1_sarathi_pins.log: 2 occurrences
- logs/phase2_attn_profiling_prep.log: 4 occurrences
- logs/phase2_attn_profiling_run0.log: 5 occurrences
- logs/phase2_attn_profiling_run1.log: 21 occurrences
- logs/phase2_attn_profiling_run2.log: 24 occurrences
- logs/phase2_attn_profiling_run3.log: 1 occurrences
- logs/phase2_attn_profiling_run3_outputs.log: 6 occurrences
- logs/phase2_attn_profiling_run3_prep.log: 1 occurrences
- logs/phase2_compat_check.log: 3 occurrences
- logs/phase2_mlp_profiling_outputs.log: 11 occurrences
- logs/phase2_mlp_profiling_outputs_cuda_event.log: 9 occurrences
- logs/phase2_mlp_profiling_run.log: 2 occurrences
- logs/phase2_mlp_profiling_run_cuda_event.log: 1 occurrences
- logs/phase2_sarathi_benchmark_runner_static.log: 3 occurrences
- logs/phase2_sarathi_fix1.log: 1 occurrences
- logs/phase2_sarathi_import_after_flashinfer011.log: 1 occurrences
- logs/phase2_sarathi_serve_server.log: 45 occurrences
- logs/phase2_tinyllama_model_config.log: 1 occurrences
- logs/phase2_vidur_install.log: 5 occurrences
- logs/phase2_vidur_worktree.log: 7 occurrences

Not redacted (reported to the user for a decision): `-home-<user>-` inside session scratchpad paths, `<user> <user>` owner columns in `ls -l` output, the WSL private address 192.168.152.45 in Ray and sarathi-serve logs. History is not rewritten, so earlier commits on this branch still contain the unredacted paths.
