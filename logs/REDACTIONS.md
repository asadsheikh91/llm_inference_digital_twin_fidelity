# Redactions applied to logs/ before commit

Date: 2026-10-10T20:25:00+05:00

Scan: email addresses, token-shaped strings (hf_, sk-, ghp_, gho_, github_pat_, AKIA, xox, JWT), keywords (api key, token, secret, password, bearer, authorization, credential, WANDB_API, HF_TOKEN), IP addresses, URLs, hostname, user and home-path strings.

Found: no secrets, tokens, API keys or email addresses. Keyword hits were token-count wording only (for example MAX_TOKENS, TOKENS_PER_REQUEST).

Redacted: local home directory path `/home/<user>` replaced by `~` (sed s|/home/<user>|~|g):

- phase1_1.1_readme.log: 73 occurrences
- phase1_1.6_artifacts.log: 4 occurrences
- phase1_1.6_capped.log: 252 occurrences
- phase1_1.2_sweep.log: 504 occurrences

Left unchanged (judged not private): kernel version, kernel OOM line with UID:1000, public URLs (arxiv.org, github.com/microsoft/vidur), ISO timestamps with +05:00 offset (timing evidence).
- RESULTS.md (already committed in 9e0bfa0): 1 occurrence in the Environment table, redacted the same way in this commit.
