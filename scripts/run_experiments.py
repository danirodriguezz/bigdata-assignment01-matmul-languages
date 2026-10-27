#!/usr/bin/env python3
"""Experiment driver for Assignment 1 (reads configs/experiment.json).

For every size n of an experiment (ascending) and every language (order shuffled per n with a
fixed seed, to avoid a systematic drift favouring one language), it calls
.claude/skills/benchmark-protocol/scripts/run_measured.py, which
  * takes the machine-wide benchmark lock (shared with the other assignments),
  * launches the program P times (process_runs), records process wall time and peak RSS
    (GNU time %M) and converts the JSON lines printed by the program into raw CSV rows,
  * records timeouts / out-of-memory / errors as rows with an empty time (never invented).
Inside each process the program performs W warm-up and R measured kernel repetitions.

Stopping rule: if a configuration fails (exit code 3 from run_measured.py), larger sizes of that
language are not attempted; they are written to <output>_skipped.csv with the reason.

Usage
    .venv/bin/python scripts/run_experiments.py --experiment size_sweep
    .venv/bin/python scripts/run_experiments.py --experiment pilot
    .venv/bin/python scripts/run_experiments.py --experiment size_sweep --languages c --sizes 512
"""
import argparse
import csv
import json
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_MEASURED = ROOT / ".claude" / "skills" / "benchmark-protocol" / "scripts" / "run_measured.py"


def rule_for(exp, lang, n):
    rules = exp.get("language_rules", {}).get(lang, exp["rules"])
    for rule in rules:
        if n <= rule["max_n"]:
            return rule
    raise ValueError(f"no rule for {lang} n={n}")


def log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(ROOT / "configs" / "experiment.json"))
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--languages", nargs="*", help="subset of languages (default: from config)")
    ap.add_argument("--sizes", nargs="*", type=int, help="subset of sizes (default: from config)")
    ap.add_argument("--dry-run", action="store_true", help="print the commands without running them")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    exp = cfg["experiments"][args.experiment]
    langs = args.languages or exp["languages"]
    sizes = sorted(args.sizes or exp["sizes"])
    out = ROOT / exp["output"]
    skipped_path = out.with_name(out.stem + "_skipped.csv")
    seed = cfg["inputs"]["seed"]
    timeout = cfg["budgets"]["timeout_s"]
    env = [f"{k}={v}" for k, v in cfg["env"].items()]
    min_sample = cfg["common_args"]["min_sample_time_s"]
    rng = random.Random(seed)
    stopped = {}   # language -> n at which it failed
    t_start = time.monotonic()

    for n in sizes:
        a = ROOT / "data" / "inputs" / f"A_n{n}_s{seed}.bin"
        b = ROOT / "data" / "inputs" / f"B_n{n}_s{seed}.bin"
        if not (a.exists() and b.exists()):
            sys.exit(f"missing inputs for n={n}: run scripts/gen_inputs.py --config {args.config}")
        order = list(langs)
        rng.shuffle(order)
        for lang in order:
            if lang in stopped:
                reason = f"not attempted: {lang} failed at n={stopped[lang]} (stopping rule)"
                log(f"skip {lang} n={n}: {reason}")
                new = not skipped_path.exists()
                with open(skipped_path, "a", newline="") as fh:
                    w = csv.writer(fh)
                    if new:
                        w.writerow(["timestamp", "experiment", "language", "n", "reason"])
                    w.writerow([datetime.now().isoformat(timespec="seconds"), args.experiment, lang, n, reason])
                continue
            rule = rule_for(exp, lang, n)
            prog = cfg["languages"][lang]["cmd"] + [
                "--a", str(a.relative_to(ROOT)), "--b", str(b.relative_to(ROOT)), "--n", str(n),
                "--warmup", str(rule["warmup"]), "--reps", str(rule["reps"]),
                "--min-sample-time", str(min_sample)]
            spec = cfg["languages"][lang]
            labels = [f"assignment={cfg['assignment']}", f"experiment={args.experiment}",
                      f"method={spec.get('method', 'naive_ijk')}",
                      f"language={spec.get('language_label', lang)}", f"n={n}", "dtype=float64",
                      "representation=dense", "threads=1", f"seed={seed}"]
            # split_processes: one run_measured call (and one lock acquisition) per process run, so
            # that very long configurations do not hold the shared lock for many minutes
            split = rule.get("split_processes", False)
            calls = rule["process_runs"] if split else 1
            per_call = 1 if split else rule["process_runs"]
            cmd = [sys.executable, str(RUN_MEASURED), "--out", str(out), "--warmup", "0",
                   "--reps", str(per_call), "--timeout", str(timeout),
                   "--label", *labels, "--env", *env, "--", *prog]
            log(f"run {lang} n={n} W={rule['warmup']} R={rule['reps']} P={rule['process_runs']}"
                f"{' (lock released between processes)' if split else ''}")
            if args.dry_run:
                print("   ", " ".join(cmd))
                continue
            t0 = time.monotonic()
            for _ in range(calls):
                rc = subprocess.run(cmd, cwd=ROOT).returncode
                if rc != 0:
                    break
            log(f"done {lang} n={n} rc={rc} in {time.monotonic() - t0:.1f}s "
                f"(elapsed {(time.monotonic() - t_start) / 60:.1f} min)")
            if rc == 3:
                stopped[lang] = n
            elif rc != 0:
                sys.exit(f"run_measured.py failed with rc={rc}")
    log(f"experiment {args.experiment} finished in {(time.monotonic() - t_start) / 60:.1f} min")


if __name__ == "__main__":
    main()
