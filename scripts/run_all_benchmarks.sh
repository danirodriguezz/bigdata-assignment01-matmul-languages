#!/usr/bin/env bash
# Full Assignment 1 benchmark (~75 min of machine time on the i7-9750H laptop, plus waiting for the
# machine-wide lock if other benchmarks are running). Run from the folder root after `make test inputs`.
# Order: environment snapshot -> RSS baseline (n = 1) -> controlled size sweep -> optional C flags study.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
mkdir -p results/logs
PATH="$PWD/.venv/bin:$PATH" bash .claude/skills/benchmark-protocol/scripts/capture_env.sh results/environment.md
bash scripts/env_extra.sh >> results/environment.md
for exp in rss_baseline size_sweep c_flags; do
  $PY scripts/run_experiments.py --experiment "$exp" 2>&1 | tee "results/logs/${exp}.log"
done
PATH="$PWD/.venv/bin:$PATH" bash .claude/skills/benchmark-protocol/scripts/capture_env.sh results/environment_after.md
echo "all benchmarks finished"
