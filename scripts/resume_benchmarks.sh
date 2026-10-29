#!/usr/bin/env bash
# Resume the Assignment 1 benchmark after the interruption of 2026-10-29 11:01.
# Runs only the configurations that are still missing in results/raw/size_sweep.csv:
#   * Python n=1536: 2 more process runs (1 of 3 done)
#   * C and Java n=1536 (5 process runs each)
#   * C, Java and Python n=2048 (Python: single attempt, 600 s limit)
#   * the separate C flags study (results/raw/c_flags.csv)
# then captures the environment again. Every timed run goes through run_measured.py (machine-wide lock).
# Usage (from the folder root):  bash scripts/resume_benchmarks.sh 2>&1 | tee -a results/logs/resume_benchmark.log
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[$(date -Is)] RESUME start; uptime: $(uptime)"

for i in 1 2; do
  .venv/bin/python .claude/skills/benchmark-protocol/scripts/run_measured.py --out results/raw/size_sweep.csv \
    --warmup 0 --reps 1 --timeout 600 --label assignment=A1 experiment=size_sweep method=naive_ijk language=python \
    n=1536 dtype=float64 representation=dense threads=1 seed=42 \
    --env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    -- .venv/bin/python src/python/matmul_naive.py --a data/inputs/A_n1536_s42.bin --b data/inputs/B_n1536_s42.bin \
    --n 1536 --warmup 0 --reps 1 --min-sample-time 0.2
done

.venv/bin/python scripts/run_experiments.py --experiment size_sweep --sizes 1536 --languages c java
.venv/bin/python scripts/run_experiments.py --experiment size_sweep --sizes 2048
.venv/bin/python scripts/run_experiments.py --experiment c_flags
PATH="$PWD/.venv/bin:$PATH" bash .claude/skills/benchmark-protocol/scripts/capture_env.sh results/environment_after.md

echo "[$(date -Is)] RESUME done"
