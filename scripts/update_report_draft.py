#!/usr/bin/env python3
"""Fill the REPORT_TABLES block of docs/REPORT_DRAFT.md from results/baseline_agg.csv and
results/baseline_llama2_capped4096_agg.csv. Values are copied as stored (no rounding)."""
import csv
import re

SOURCES = ["results/baseline_agg.csv", "results/baseline_llama2_capped4096_agg.csv"]


def md(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


rows = []
for src in SOURCES:
    for r in csv.DictReader(open(src)):
        r["_src"] = src.split("/")[-1]
        rows.append(r)

parts = []
for short, name in [("ttft", "TTFT (`prefill_e2e_time`)"), ("tpot", "TPOT (`decode_time_execution_plus_preemption_normalized`)"), ("e2e", "Request E2E (`request_e2e_time`)")]:
    header = ["model", "max_tokens", "range_note", "qps", "P50 mean", "P50 std", "P90 mean", "P90 std", "P99 mean", "P99 std", "source"]
    body = [[r["model"], r["max_tokens"], r["range_note"], r["qps"]] + [r[f"{short}_{p}_s_{s}"] for p in ("p50", "p90", "p99") for s in ("mean", "std")] + [r["_src"]] for r in rows]
    parts.append(f"#### {name}, seconds\n\n" + md(header, body))

p = "docs/REPORT_DRAFT.md"
text = open(p).read()
pat = re.compile(r"(<!-- BEGIN REPORT_TABLES -->\n).*?(<!-- END REPORT_TABLES -->)", re.S)
if not pat.search(text):
    raise SystemExit("REPORT_TABLES marker missing")
text = pat.sub(lambda mo: mo.group(1) + "\n\n".join(parts) + "\n" + mo.group(2), text)
open(p, "w").write(text)
print(f"filled REPORT_TABLES with {len(rows)} rows per metric")
