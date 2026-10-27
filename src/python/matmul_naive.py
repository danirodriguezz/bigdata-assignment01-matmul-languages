#!/usr/bin/env python3
"""Naive dense matrix multiplication in pure Python (Assignment 1).

Storage layout: idiomatic list of row lists of Python float objects (each element is a boxed
PyFloat; a list stores pointers to them). Loop order ijk with a scalar accumulator, identical to
the C and Java versions, so the floating-point evaluation order is the same in the three languages.
Only the standard library is used (no NumPy in the kernel).

Usage:
    python3 matmul_naive.py --a A.bin --b B.bin --n N [--warmup W] [--reps R]
                            [--min-sample-time T] [--out-c C.bin]

Protocol (same as the C and Java drivers): inputs are loaded and C is allocated outside the timed
region; W warm-up repetitions are followed by R measured repetitions; each repetition times a batch
of kernel calls with time.perf_counter_ns() (monotonic) and reports time per call; sum(C) is
printed after every repetition. One JSON line per repetition on stdout.
"""
import argparse
import json
import math
import os
import platform
import sys
import time
from array import array


def multiply(a, b, c, n):
    """C[i][j] = sum_k A[i][k] * B[k][j], k increasing. C is fully overwritten."""
    for i in range(n):
        ai = a[i]          # row of A (same row hoisting as in the Java version)
        ci = c[i]
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += ai[k] * b[k][j]   # B is walked down a column: one row list per k
            ci[j] = s


def read_matrix(path, n):
    """Read an n x n little-endian float64 row-major file into a list of row lists."""
    if os.path.getsize(path) != 8 * n * n:
        raise ValueError(f"{path}: expected exactly {n * n} float64 values")
    if sys.byteorder != "little":
        raise RuntimeError("this reader assumes a little-endian host")
    rows = []
    with open(path, "rb") as fh:
        for _ in range(n):
            buf = array("d")
            buf.fromfile(fh, n)        # one row at a time: small temporary buffer
            rows.append(buf.tolist())  # list of n Python floats
    return rows


def write_matrix(path, m):
    with open(path, "wb") as fh:
        for row in m:
            array("d", row).tofile(fh)


def checksum(c):
    s = 0.0
    for row in c:          # row-major order, same as C and Java
        for v in row:
            s += v
    return s


def deep_size_bytes(*matrices):
    """Bytes of the Python objects holding the matrices: sys.getsizeof of each outer list, each row
    list and each element float. Metric name: pyobj_deep_size_bytes. No de-duplication is done (a
    set of ids would itself inflate the process memory); this is exact here because every element is
    a distinct float object (checked by tests/test_correctness.py)."""
    total = 0
    for m in matrices:
        total += sys.getsizeof(m)
        for row in m:
            total += sys.getsizeof(row) + sum(map(sys.getsizeof, row))
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--warmup", type=int, default=0)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--min-sample-time", type=float, default=0.0)
    ap.add_argument("--out-c")
    args = ap.parse_args()
    n = args.n

    a = read_matrix(args.a, n)
    b = read_matrix(args.b, n)
    c = [[0.0] * n for _ in range(n)]   # allocated outside the timed region
    impl = f"{platform.python_implementation()} {platform.python_version()}"

    batch = 1
    for r in range(args.warmup + args.reps):
        is_warm = r < args.warmup
        calls = 1 if is_warm else batch
        t0 = time.perf_counter_ns()
        for _ in range(calls):
            multiply(a, b, c, n)
        t = (time.perf_counter_ns() - t0) * 1e-9 / calls
        # deep size is measured after the kernel (C then holds n*n distinct floats); not timed
        mem = deep_size_bytes(a, b, c) if not is_warm and r == args.warmup else None
        rec = {"time_s": t, "timer_boundary": "kernel", "repetition": r, "is_warmup": is_warm,
               "checksum": checksum(c), "batch": calls, "language_impl": impl}
        if mem is not None:
            rec.update({"memory_metric": "pyobj_deep_size_bytes", "memory_bytes": mem})
        print(json.dumps(rec), flush=True)
        if r == args.warmup - 1 and args.min_sample_time > 0 and t > 0:
            batch = max(1, min(100000, math.ceil(args.min_sample_time / t)))
    if args.reps == 0 and args.warmup == 0:
        multiply(a, b, c, n)   # --out-c only
    if args.out_c:
        write_matrix(args.out_c, c)


if __name__ == "__main__":
    main()
