---
name: multilang-naive-matmul
description: Technical guide for Assignment 1 — implementing and fairly benchmarking the naive triple-loop dense matrix multiplication in Python, Java and C (shared inputs, identical loop order, storage layouts, JIT warm-up, compiler flags, memory metrics per language, numerical tolerance, size sequence, analysis of cubic growth). Use when designing, coding, testing or analysing Assignment 1.
---

# Naive matrix multiplication in Python, Java and C

## 1. One algorithm, three languages (the controlled comparison)
Identical **ijk** loop order with a scalar accumulator in all three:
```
for i in 0..n-1:
  for j in 0..n-1:
    s = 0.0
    for k in 0..n-1:
      s += A[i][k] * B[k][j]
    C[i][j] = s
```
- Numeric type: **IEEE-754 float64** everywhere (`double` in C/Java, `float` in Python).
- Same evaluation order ⇒ C, Java and Python should give **bit-identical** results (as long as C is not compiled
  with `-ffast-math` and does not use FMA contraction: keep the default x86-64 target, no `-march=native`, in the
  controlled comparison). Verifying bit-identity across languages is a strong, cheap correctness check — report it.
- No library matmul in the kernels (NumPy only as an external reference in the tests).

### Storage layouts (describe them in the report, they are "unavoidable differences")
| Language | Idiomatic layout used | Consequence |
|---|---|---|
| C | one contiguous `double*` of n² elements, row-major, index `i*n+k` (malloc) | unit-stride rows; B column walk has stride n·8 B |
| Java | `double[][]` (array of row arrays; rows are separate heap objects, each contiguous) | extra indirection per row, bounds checks (often hoisted by JIT) |
| Python | `list` of `list` of `float` objects (each element a boxed PyFloat, list stores pointers) | pointer chasing, ~24 B per float object + 8 B per pointer, interpreter dispatch per operation |
Optional *separate* experiment (clearly labelled, not part of the controlled comparison): C with `double**`, Java
with flat `double[]`, Python with `array('d')`, or `-O3 -march=native`.

## 2. Shared inputs
- `scripts/gen_inputs.py --n N --seed S` (NumPy `default_rng(seed).uniform(-1, 1, (n, n))`) writes
  `data/inputs/A_n{N}_s{S}.bin` and `B_...bin` as **little-endian float64 row-major** + a JSON sidecar
  (n, seed, generator, distribution, dtype, sha256). `data/inputs/checksums.sha256` is committed.
- Readers: C `fread` into `double*`; Java `FileChannel` + `ByteBuffer.order(LITTLE_ENDIAN).asDoubleBuffer()`;
  Python `array('d')` + `fromfile` then split into list of lists (conversion **outside** the timed region).
- Values in [-1, 1) keep sums well inside float64 range; no overflow concerns (document it).

## 3. Program interface (same for the three)
`<prog> --a FILE --b FILE --n N --warmup W --reps R [--out-c FILE]` → prints one JSON line per repetition:
`{"time_s":…, "timer_boundary":"kernel", "repetition":r, "is_warmup":bool, "checksum":sum(C), "memory_metric":…, "memory_bytes":…}`
- Timed region = the triple loop only (C already allocated and zeroed before timing → boundary `kernel`;
  say so). Allocation of C outside timing; state it.
- Timers: C `clock_gettime(CLOCK_MONOTONIC)`, Java `System.nanoTime()`, Python `time.perf_counter_ns()`.
- Consume the result: checksum printed (prevents dead-code elimination in C/JIT).
- `--out-c` writes C for the correctness tests.

## 4. Language settings (fixed, recorded)
- **C**: `gcc -O2 -std=c11 -Wall` (state why -O2: common default; optional separate -O0/-O3 experiment).
  Record `gcc --version`. No OpenMP, single thread.
- **Java**: OpenJDK 21, `javac --release 21`; run `java -Xms2g -Xmx<budget> -XX:+UseG1GC` (fixed, recorded).
  JIT warm-up **in-process**: e.g. W = 3 warm-ups for n ≤ 512, W = 1 for larger n (justify; show warm-up vs steady
  times in a small figure or table — it is a nice piece of evidence of JIT effects). Consider ≥ 3 separate JVM
  invocations for between-process variability (Georges et al., OOPSLA 2007 — verify before citing).
  JMH is optional (cross-check one size); the custom harness must be documented.
- **Python**: CPython 3.12.x (record exact), plain loops, `python3 -I` style isolation optional. W = 1 warm-up.
  For the largest feasible sizes a single run may take minutes: justify fewer repetitions if needed and report it.

## 5. Memory (name metric + tool for each language)
1. **Peak RSS** of the whole process (GNU time `%M`, recorded automatically by `run_measured.py`) — the common,
   comparable metric. Also measure an **empty/minimal run** (e.g. n = 1) per language to show runtime baseline
   (Python interpreter ≈ 10 MB, JVM ≈ 40+ MB): report RSS − baseline as "data-dependent part".
2. Language-internal metric (separate, not mixed with RSS):
   Python `tracemalloc` peak in a separate run (it slows execution — never in timed runs);
   Java `MemoryMXBean` heap used / pool peak usage; C: analytical `3·8·n²` B (allocations are exactly that).
3. Compare with the analytical estimate: Python list-of-lists ≈ n²·(8 B pointer + 24 B PyFloat) per matrix
   (verify with `sys.getsizeof`) — a nice quantitative explanation of Python's memory footprint.

## 6. Correctness (before any benchmark)
- Identity (A·I = A, I·B = B), zero matrix, hand-computed 2×2 and 3×3 (also non-symmetric), small random (n = 7, 64)
  vs NumPy reference.
- Tolerance justified with the standard dot-product error bound (Higham, *Accuracy and Stability of Numerical
  Algorithms*, 2002 — verify): `|ĉ_ij − c_ij| ≤ γ_n (|A||B|)_ij`, `γ_n ≈ n·u`, `u = 2^-53`. Use
  `tol_ij = 2·n·u·(|A||B|)_ij` vs NumPy (different summation order), and **exact equality** across the three own
  implementations (same order). Report max abs/rel error observed.

## 7. Sizes and budgets (proposal to confirm with Daniel)
- Correctness: n ∈ {1, 2, 3, 7, 64}.
- Benchmark: n ∈ {64, 128, 256, 384, 512, 768, 1024, 1536, 2048} for C/Java (+ 3072 if within budget);
  Python stops at the first size exceeding the budget (expect around n ≈ 512–1024 for ~10 min runs; pilot first).
- Mixing powers of two with non-powers (384, 768, 1536) helps reveal cache-associativity effects of the strided
  B-column walk at power-of-two n — check the "time per inner iteration" `T/n³` curve.
- Budget suggestion: 600 s per process run, total benchmarking ≤ 3 h, memory ≤ 8 GB.
- Timeouts → record status, stop escalating that language, report "largest completed n" vs "attempted n".

## 8. Analysis checklist
- log-log runtime vs n per language with IQR bars; `growth_fit.py` exponent b with CI (expect ≈ 3; deviations at
  small n = constant overheads, at large n = cache/memory effects).
- `T/n³` (ns per multiply-add) vs n: flat ⇒ pure cubic; steps ⇒ cache levels (L1 32 KiB/L2 256 KiB/L3 12 MiB per
  `lscpu` on the i7-9750H — use the captured values).
- Ratios Java/C and Python/C at equal n (median ratio), with variability, scoped to this machine/settings.
- Memory: peak RSS vs n with analytical curves; baseline subtraction.
- JIT warm-up evidence (Java first-iteration vs steady-state).
- Limits table.

## 9. Hypotheses to state (predictions, to be checked — not results)
H1 runtime grows ≈ n³ for all three; H2 C < Java < Python in time with Java approaching C after warm-up;
H3 Python's memory per element is several times larger than C/Java due to boxed floats. Phrase them in the
report and give a verdict per hypothesis in the Discussion.

## 10. Key references to verify (candidates)
Higham 2002 (error bounds), Hennessy & Patterson 2017 or Drepper 2007 (memory hierarchy), Georges et al. 2007
(Java benchmarking), Hoefler & Belli 2015 (benchmark reporting), Golub & Van Loan 2013 (classical algorithm),
official docs: CPython `tracemalloc`/`time`, OpenJDK `MemoryMXBean`, GCC optimisation options.
