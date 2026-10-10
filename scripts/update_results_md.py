#!/usr/bin/env python3
"""Regenerate the data-driven blocks of RESULTS.md from the CSVs in results/ (values copied as stored).
Blocks are delimited by <!-- BEGIN name --> / <!-- END name --> markers."""
import csv
import re

import pandas as pd


def md(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def agg_tables(path):
    rows = list(csv.DictReader(open(path)))
    parts = []
    for short, name in [("ttft", "TTFT"), ("tpot", "TPOT"), ("e2e", "Request E2E")]:
        header = ["model", "max_tokens", "range_note", "qps"] + [f"{p} {s}" for p in ("P50", "P90", "P99") for s in ("mean", "std")]
        body = [[r["model"], r["max_tokens"], r["range_note"], r["qps"]] + [r[f"{short}_{p}_s_{s}"] for p in ("p50", "p90", "p99") for s in ("mean", "std")] for r in rows]
        parts.append(f"#### {name}, seconds (source: {path})\n\n" + md(header, body))
    return "\n\n".join(parts)


def cache_table():
    m = pd.read_csv("results/predictor_cache_manifest.csv")
    return md(["path", "size_bytes", "trained_in", "sha256"], m[["path", "size_bytes", "trained_in", "sha256"]].values.tolist())


blocks = {
    "TABLES_ORIGINAL": agg_tables("results/baseline_agg.csv"),
    "TABLES_CAPPED": agg_tables("results/baseline_llama2_capped4096_agg.csv"),
    "CACHE_MANIFEST": cache_table(),
}
text = open("RESULTS.md").read()
for name, content in blocks.items():
    pat = re.compile(rf"(<!-- BEGIN {name} -->\n).*?(<!-- END {name} -->)", re.S)
    if not pat.search(text):
        raise SystemExit(f"marker {name} missing")
    text = pat.sub(lambda mo: mo.group(1) + content + "\n" + mo.group(2), text)
open("RESULTS.md", "w").write(text)
print("updated RESULTS.md blocks:", ", ".join(blocks))
