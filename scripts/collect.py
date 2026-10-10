#!/usr/bin/env python3
"""Collect Vidur sweep metrics into results/baseline.csv and results/baseline_agg.csv.

Metric names follow ~/vidur/docs/metrics.md and vidur/metrics/constants.py; the per-request
values are read from <run>/<timestamp>/request_metrics.csv:

  TTFT  = prefill_e2e_time                                  (docs: prefill_time_e2e_cdf, f_r - a_r)
  TPOT  = decode_time_execution_plus_preemption_normalized  (docs item 16, (c_r - f_r) / decode tokens)
  E2E   = request_e2e_time                                  (docs: request_e2e_time_cdf, c_r - a_r)

All values are seconds as written by Vidur. Percentiles use pandas Series.quantile (linear
interpolation), the same call Vidur uses in DataSeries.print_distribution_stats.
Model, QPS, seed and max_tokens are read from each run's config.json, not from the directory name.
range_note is "outside profiled range" when the run's trace max_tokens exceeds the max
prefill_chunk_size in ~/vidur/data/profiling/compute/<device>/<model>/attention.csv.

Usage: python scripts/collect.py [--runs-glob 'results/runs/sweep_*'] [--out results/baseline.csv]
"""
import argparse
import glob
import json
import os

import pandas as pd

METRICS = {
    "ttft": "prefill_e2e_time",
    "tpot": "decode_time_execution_plus_preemption_normalized",
    "e2e": "request_e2e_time",
}
PERCENTILES = {"p50": 0.50, "p90": 0.90, "p99": 0.99}
VIDUR_DIR = os.path.expanduser("~/vidur")
_profiled_max_cache = {}


def profiled_max_prefill(device, model):
    """Max prefill_chunk_size in Vidur's attention profiling data for this device/model."""
    key = (device, model)
    if key not in _profiled_max_cache:
        path = os.path.join(VIDUR_DIR, "data/profiling/compute", device, model, "attention.csv")
        _profiled_max_cache[key] = int(pd.read_csv(path, usecols=["prefill_chunk_size"])["prefill_chunk_size"].max())
    return _profiled_max_cache[key]


def load_run(run_dir):
    subdirs = sorted(d for d in glob.glob(os.path.join(run_dir, "*")) if os.path.isdir(d))
    if len(subdirs) != 1:
        raise RuntimeError(f"{run_dir}: expected exactly 1 timestamp subdir, found {len(subdirs)}")
    out_dir = subdirs[0]
    cfg = json.load(open(os.path.join(out_dir, "config.json")))
    rg = cfg["request_generator_config"]
    df = pd.read_csv(os.path.join(out_dir, "request_metrics.csv"))
    model = cfg["cluster_config"]["replica_config"]["model_name"]
    device = cfg["cluster_config"]["replica_config"]["device"]
    max_tokens = rg["length_generator_config"]["max_tokens"]
    profiled_max = profiled_max_prefill(device, model)
    row = {
        "run": os.path.basename(run_dir),
        "model": model,
        "device": device,
        "max_tokens": max_tokens,
        "profiled_max_prefill_chunk_size": profiled_max,
        "range_note": "outside profiled range" if max_tokens > profiled_max else "within profiled range",
        "max_request_num_tokens": int(df["request_num_tokens"].max()),
        "qps": rg["interval_generator_config"]["qps"],
        "seed": cfg["seed"],
        "synthetic_seed": rg["seed"],
        "length_seed": rg["length_generator_config"]["seed"],
        "num_requests_config": rg["num_requests"],
        "num_requests_completed": len(df),
        "source_file": os.path.relpath(os.path.join(out_dir, "request_metrics.csv")),
    }
    for short, col in METRICS.items():
        s = df[col].dropna()
        row[f"{short}_n"] = len(s)
        for pname, q in PERCENTILES.items():
            row[f"{short}_{pname}_s"] = s.quantile(q)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-glob", default="results/runs/sweep_*")
    ap.add_argument("--out", default="results/baseline.csv")
    ap.add_argument("--agg-out", default="results/baseline_agg.csv")
    args = ap.parse_args()

    run_dirs = sorted(glob.glob(args.runs_glob))
    if not run_dirs:
        raise SystemExit(f"no runs match {args.runs_glob}")
    per_run = pd.DataFrame([load_run(d) for d in run_dirs])
    per_run = per_run.sort_values(["model", "max_tokens", "qps", "seed"]).reset_index(drop=True)
    per_run.to_csv(args.out, index=False)

    value_cols = [c for c in per_run.columns if c.endswith("_s")]
    g = per_run.groupby(["model", "device", "max_tokens", "range_note", "qps"])
    agg = g[value_cols].agg(["mean", "std"])  # std: pandas sample std (ddof=1)
    agg.columns = [f"{c}_{stat}" for c, stat in agg.columns]
    agg.insert(0, "seeds", g["seed"].apply(lambda s: " ".join(str(x) for x in sorted(s))))
    agg.insert(0, "n_seeds", g["seed"].nunique())
    agg = agg.reset_index()
    agg.to_csv(args.agg_out, index=False)
    print(f"wrote {args.out} ({len(per_run)} runs) and {args.agg_out} ({len(agg)} groups)")


if __name__ == "__main__":
    main()
