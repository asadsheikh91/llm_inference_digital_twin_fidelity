#!/usr/bin/env python3
"""Render results/baseline_agg.csv, results/baseline.csv and results/paper_reported.csv as markdown
tables (results/tables.md). Values are copied as the exact strings stored in the CSVs (no rounding)."""
import csv

def read(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def md(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)

parts = []
cols = ["ttft_p50_s", "ttft_p90_s", "ttft_p99_s", "tpot_p50_s", "tpot_p90_s", "tpot_p99_s", "e2e_p50_s", "e2e_p90_s", "e2e_p99_s"]
for agg_path, per_path, title in [
    ("results/baseline_agg.csv", "results/baseline.csv", "Original sweep (trace max_tokens 16384)"),
    ("results/baseline_llama2_capped4096_agg.csv", "results/baseline_llama2_capped4096.csv", "Llama-2-7b rerun with trace max_tokens 4096"),
]:
    agg = read(agg_path)
    parts.append(f"### {title}")
    for short, name in [("ttft", "TTFT (prefill_e2e_time)"), ("tpot", "TPOT (decode_time_execution_plus_preemption_normalized)"), ("e2e", "Request E2E (request_e2e_time)")]:
        header = ["model", "max_tokens", "range_note", "qps", "seeds"] + [f"{p} {s}" for p in ("P50", "P90", "P99") for s in ("mean", "std")]
        rows = [[r["model"], r["max_tokens"], r["range_note"], r["qps"], r["seeds"]] + [r[f"{short}_{p}_s_{s}"] for p in ("p50", "p90", "p99") for s in ("mean", "std")] for r in agg]
        parts.append(f"#### {name}, seconds, mean and sample std (ddof=1) across seeds\n\nSource: {agg_path}\n\n" + md(header, rows))
    per = read(per_path)
    parts.append(f"#### Per-run values, seconds\n\nSource: {per_path}\n\n" + md(["model", "max_tokens", "range_note", "qps", "seed", "max_request_num_tokens"] + cols, [[r["model"], r["max_tokens"], r["range_note"], r["qps"], r["seed"], r["max_request_num_tokens"]] + [r[c] for c in cols] for r in per]))

pap = read("results/paper_reported.csv")
parts.append("#### Paper-reported values\n\nSource: results/paper_reported.csv\n\n" + md(["id", "pdf page", "location", "model", "metric", "condition", "value as printed", "trace mapping"], [[r["id"], r["source_page_pdf"], r["location"], r["model"], r["metric"], r["condition"], r["value_as_printed"].replace("|", "/"), r["trace_assignment"]] for r in pap]))

open("results/tables.md", "w").write("\n\n".join(parts) + "\n")
print("wrote results/tables.md")
