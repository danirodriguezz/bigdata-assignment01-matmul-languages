#!/usr/bin/env bash
# Assignment-1-specific additions to results/environment.md (appended by `make env`).
set -u
cd "$(dirname "$0")/.."
echo
echo "## Assignment 1 build and runtime settings"
echo
echo '```'
echo "C compiler:      $(gcc --version | head -1)"
echo "C flags:         -O2 -std=c11 -Wall -Wextra (default x86-64 target, no -march, no -ffast-math, single thread)"
echo "gcc -O2 target:  $(gcc -O2 -Q --help=target 2>/dev/null | grep -E '^\s+-march=' | tr -s ' ')"
echo "JDK:             $(java -version 2>&1 | sed -n 2p)"
echo "JVM:             $(java -version 2>&1 | sed -n 3p)"
echo "JVM flags:       -Xms1g -Xmx4g -XX:+UseG1GC (default tiered JIT compilation)"
echo "Java GC/JIT threads: JVM default (background threads; the kernel itself runs on the main thread)"
echo "Python (bench):  $(.venv/bin/python -c 'import sys,platform;print(platform.python_implementation(), sys.version.split()[0], "-", sys.executable)')"
echo "Python packages (venv): $(.venv/bin/python -m pip freeze 2>/dev/null | tr '\n' ' ')"
echo "perf_event_paranoid: $(cat /proc/sys/kernel/perf_event_paranoid) (hardware counters not available)"
echo "GNU time:        $(/usr/bin/time --version 2>&1 | head -1)"
echo "Thread env for runs: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1"
echo '```'
