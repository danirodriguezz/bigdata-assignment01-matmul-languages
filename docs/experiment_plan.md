# Experiment plan — Assignment 01 (written before the full benchmark, 2026-10-27)

## Research question
**RQ.** On one Intel Core i7-9750H laptop, how do the runtime and the memory use of the same naive
(ijk triple-loop) dense float64 matrix multiplication grow with the matrix size n when it is implemented in
C (gcc -O2), Java (OpenJDK 21, HotSpot JIT) and Python (CPython 3.12), and how large are the differences
between the three implementations at equal n?

- **Factor varied:** matrix side length n (n × n square matrices); implementation language (3 levels).
- **Outcomes:** kernel runtime [s] (median, IQR, k), time per multiply–add T/n³ [ns], growth exponent b of
  T ≈ c·n^b, peak RSS [MiB] and one language-internal memory metric per language, largest feasible n.

## Hypotheses (predictions, not results)
- **H1** Runtime grows approximately as n³ for all three implementations (fitted exponent b ≈ 3); deviations
  above 3 are expected at large n when B no longer fits in the caches.
- **H2** At equal n, C < Java < Python in runtime; after JIT warm-up Java is within a small factor of C, Python is
  one to two orders of magnitude slower.
- **H3** Python needs several times more memory per matrix element than C and Java (boxed floats: ≈ 32 B vs 8 B).

## Methods (controlled comparison)
| Method | Language | Layout | Settings |
|---|---|---|---|
| naive_ijk | C | contiguous row-major `double*` | gcc 13.3 `-O2 -std=c11 -Wall -Wextra`, default x86-64 target, no FMA (ISO mode ⇒ `-ffp-contract=off`) |
| naive_ijk | Java | `double[][]` | OpenJDK 21.0.12, `-Xms1g -Xmx4g -XX:+UseG1GC`, tiered JIT, in-process warm-up |
| naive_ijk | Python | list of lists of `float` | CPython 3.12.3, pure Python, standard library only |

Fairness: same algorithm, same loop order and scalar accumulator (bit-identical results), same numeric type,
same input files, same timing boundary (`kernel`), same machine, one thread, runs serialised by a lock.

## Inputs
`scripts/gen_inputs.py`: NumPy `default_rng(42)` (PCG64), A then B, uniform [-1, 1), float64, little-endian row-major
binary files + JSON sidecar + SHA-256 checksums. |c_ij| ≤ n ⇒ no overflow.

## Sizes, budgets, stopping rule
- Correctness: n ∈ {1, 2, 3, 7, 64, 100}.
- Benchmark: n ∈ {64, 128, 256, 384, 512, 768, 1024, 1536, 2048}, all three languages (RSS baseline at n = 1).
- Budgets (Daniel): **600 s per process run**, **8 GB memory**, **≤ 90 min total benchmark time**.
  Dense storage 3·8n² = 96 MiB at n = 2048 ⇒ memory budget is not limiting.
- Stopping rule: after a timeout/OOM/error of a language, larger n for that language are not attempted
  (logged in `results/raw/size_sweep_skipped.csv`).

## Protocol
- Timer: C `clock_gettime(CLOCK_MONOTONIC)`, Java `System.nanoTime()`, Python `time.perf_counter_ns()`.
- Boundary `kernel`: only the triple loop. Loading, allocation of C and checksum are outside the timed region.
- Each configuration = P separate process runs; inside each process W warm-ups + R = 1 measured repetition.
  Short kernels: one measured sample = batch of ceil(0.2 s / t_last_warmup) calls; time per call is reported.
- Pilot results (`results/raw/pilot_size_sweep.csv`, 1 process): C 2.0 s and Java 5.3 s at n = 1024; Python 9 s at
  n = 512 (65–80 ns per multiply–add). Extrapolated (model, not result): Python ≈ 5–6 min at n = 1536 and
  > 600 s at n = 2048.
- Resulting plan (fits ≈ 60–70 min of machine time):

| Language | n ≤ 512 | 768 | 1024 | 1536 | 2048 |
|---|---|---|---|---|---|
| C | W=2, P=5 | W=1, P=5 | W=0, P=5 | W=0, P=5 | W=0, P=5 |
| Java | W=5, P=5 | W=2, P=5 | W=2, P=5 | W=1, P=5 | W=1, P=5 |
| Python | W=1, P=5 | W=0, P=5 | W=0, P=5 | W=0, **P=3** | W=0, **P=1 (attempt)** |

  Justification for fewer warm-ups/repetitions: pilot shows no warm-up effect for C at n = 1024 (1.981 s vs 1.984 s)
  or for Python at n = 512; Java shows a JIT effect (first iteration 7× slower at n = 64), so Java always keeps ≥ 1
  warm-up. Python n = 1536 uses k = 3 (≈ 6 min per run) and n = 2048 a single attempt to document the timeout.
- Language order shuffled per n (seed 42). Each configuration holds the machine-wide lock; long configurations
  release it between processes.
- Memory: peak RSS (GNU time) for every run + language metric (C `matrix_storage_bytes`, Java
  `jvm_heap_peak_used_bytes`, Python `pyobj_deep_size_bytes`); RSS baseline at n = 1 (5 runs per language).
- Statistic: median and IQR over k measured samples; all raw rows kept. No exclusion rule planned; loadavg recorded.

## Optional, separate experiment
C optimisation flags (-O0, -O2, -O3, -O3 -march=native), same source, n ∈ {256, 512, 1024}, W=1, P=5.
Not part of the controlled language comparison.
