# Decisions log — Assignment 01

Record every design decision with date, the options considered and Daniel's answer.
Sibling assignments read this file to stay consistent.

| Date | Decision | Choice | Rationale / who decided |
|---|---|---|---|
| 2026-10-27 | Existing A1 material | None — start from scratch | Daniel |
| 2026-10-27 | Benchmark budget | ≤ 90 min machine time for this assignment; 600 s max per process run; 8 GB memory | Daniel |
| 2026-10-27 | Hardware counters (perf) | Not available (perf_event_paranoid=4) — state as limitation | Daniel |
| 2026-10-27 | Other open choices (sizes, optional experiments, repo name) | Recommended defaults from CLAUDE.md, delegated to the agent | Daniel delegated |
| 2026-10-27 | Algorithm / loop order | ijk triple loop with scalar accumulator in C, Java and Python; rows of A (and C) hoisted in Java/Python, flat index in C | Agent (skill `multilang-naive-matmul`) |
| 2026-10-27 | Numeric type | IEEE-754 float64 everywhere (`double` / Python `float`) | Agent (default) |
| 2026-10-27 | Storage layouts | C: one contiguous row-major `double*` (malloc/calloc); Java: `double[][]`; Python: list of lists of float | Agent (idiomatic layouts; described as unavoidable differences) |
| 2026-10-27 | Inputs | Shared binary files: `scripts/gen_inputs.py`, NumPy `default_rng(42)` (PCG64), A then B, uniform [-1, 1), little-endian float64 row-major + JSON sidecar + `data/inputs/checksums.sha256` | Agent |
| 2026-10-27 | Program interface (reusable in A2–A4) | `<prog> --a A.bin --b B.bin --n N --warmup W --reps R --min-sample-time T [--out-c C.bin]`, one JSON line per repetition | Agent |
| 2026-10-27 | Timer boundary | `kernel`: only the triple loop; loading, allocation of C and checksum outside the timed region | Agent |
| 2026-10-27 | Short kernels | Batch calibration: after the warm-ups, batch = ceil(0.2 s / t_last_warmup) kernel calls per sample; time reported per multiplication; batch stored in `extra_json` | Agent |
| 2026-10-27 | C flags (controlled comparison) | `gcc 13.3 -O2 -std=c11 -Wall -Wextra`, default x86-64 target; ISO mode ⇒ `-ffp-contract=off` (no FMA). Assembly checked: scalar `mulsd`/`addsd` | Agent |
| 2026-10-27 | JVM settings | OpenJDK 21.0.12, `javac --release 21`, `java -Xms1g -Xmx4g -XX:+UseG1GC`, default tiered JIT | Agent |
| 2026-10-27 | Python | CPython 3.12.3 (venv), pure Python loops, standard library only in the kernel | Agent |
| 2026-10-27 | Correctness tolerance | Exact equality for known/identity/zero cases and across the three own implementations; vs NumPy: abs(c−c_ref) ≤ 2·n·u·(abs(A)·abs(B)), u = 2^-53 (Higham dot-product bound) | Agent |
| 2026-10-27 | Size sequence | n ∈ {64, 128, 256, 384, 512, 768, 1024, 1536, 2048} (powers of two + 384/768/1536); RSS baseline n = 1 | Agent (CLAUDE.md default) |
| 2026-10-27 | Repetitions / warm-ups (after pilot) | k = P process runs × R = 1 measured rep, P = 5 (Python n = 1536: P = 3; Python n = 2048: single attempt). In-process warm-ups: C W=2 (n≤512), 1 (768), 0 (≥1024); Java W=5 (n≤512), 2 (≤1024), 1 (≥1536); Python W=1 (n≤512), 0 (≥768). Justified by the pilot (no warm-up effect for C at n=1024 or Python at n=512; JIT effect visible for Java) and by the 90-min budget | Agent |
| 2026-10-27 | Lock policy | Each configuration takes the machine-wide lock; Java n≥1536 and Python n≥768 release it between process runs (`split_processes`) | Agent |
| 2026-10-27 | Memory metrics | Peak RSS (GNU time %M) for all; plus C `matrix_storage_bytes` (exact allocation 3·8n²), Java `jvm_heap_peak_used_bytes` (MemoryPoolMXBean peak, heap pools), Python `pyobj_deep_size_bytes` (sys.getsizeof of lists + floats). tracemalloc not used (too slow inside the kernel) | Agent |
| 2026-10-27 | Optional experiment | Separate C flags study: -O0, -O2, -O3, -O3 -march=native at n ∈ {256, 512, 1024}; not part of the controlled comparison | Agent (CLAUDE.md default "if time allows") |
| 2026-10-27 | Repository name | `bigdata-assignment01-matmul-languages` (GitHub user to be confirmed by Daniel) | Agent (CLAUDE.md default) |
| 2026-10-27 | Report style | IEEE conference two-column, impersonal voice, figures with Okabe–Ito palette | Agent |
