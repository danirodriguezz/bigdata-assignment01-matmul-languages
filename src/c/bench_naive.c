/* Benchmark driver for the naive C kernel (Assignment 1).
 *
 * Usage: matmul_naive_c --a A.bin --b B.bin --n N [--warmup W] [--reps R]
 *                       [--min-sample-time T] [--out-c C.bin]
 *
 * Protocol (identical in the Java and Python drivers):
 *   1. Load A and B from the shared input files and allocate C  -> outside the timed region.
 *   2. Run W warm-up repetitions, then R measured repetitions. Each repetition times a batch of
 *      `batch` consecutive kernel calls with CLOCK_MONOTONIC and reports time per call.
 *      batch = 1 unless --min-sample-time T > 0 and W >= 1: then batch = ceil(T / t_last_warmup),
 *      so that very short kernels are timed over at least ~T seconds.
 *   3. After each repetition the checksum sum(C) (row-major order) is printed; this consumes the
 *      result (no dead-code elimination) and is a cross-language consistency check.
 * Output: one JSON line per repetition on stdout (parsed by run_measured.py).
 * Timer boundary "kernel": only the triple loop; loading, allocation and checksum are excluded. */
#define _POSIX_C_SOURCE 199309L
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "matmul_naive.h"
#include "matrix_io.h"

static double now_s(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

static double checksum(const double *C, size_t n)
{
    double s = 0.0;
    for (size_t idx = 0; idx < n * n; idx++) s += C[idx];
    return s;
}

static void usage(void)
{
    fprintf(stderr, "usage: matmul_naive_c --a A.bin --b B.bin --n N [--warmup W] [--reps R] "
                    "[--min-sample-time T] [--out-c C.bin]\n");
    exit(2);
}

int main(int argc, char **argv)
{
    const char *a_path = NULL, *b_path = NULL, *c_out = NULL;
    long n_arg = -1, warmup = 0, reps = 1;
    double min_sample = 0.0;
    for (int i = 1; i < argc; i++) {
        if (i + 1 >= argc) usage();
        if (!strcmp(argv[i], "--a")) a_path = argv[++i];
        else if (!strcmp(argv[i], "--b")) b_path = argv[++i];
        else if (!strcmp(argv[i], "--n")) n_arg = atol(argv[++i]);
        else if (!strcmp(argv[i], "--warmup")) warmup = atol(argv[++i]);
        else if (!strcmp(argv[i], "--reps")) reps = atol(argv[++i]);
        else if (!strcmp(argv[i], "--min-sample-time")) min_sample = atof(argv[++i]);
        else if (!strcmp(argv[i], "--out-c")) c_out = argv[++i];
        else usage();
    }
    if (!a_path || !b_path || n_arg < 1 || warmup < 0 || reps < 0) usage();
    size_t n = (size_t)n_arg;

    double *A = matrix_read_bin(a_path, n);
    double *B = matrix_read_bin(b_path, n);
    double *C = calloc(n * n, sizeof(double));
    if (!A || !B || !C) { fprintf(stderr, "Cannot allocate memory\n"); return 1; }
    const double storage_bytes = 3.0 * 8.0 * (double)n * (double)n; /* exactly what was allocated */

    long batch = 1;
    double last = 0.0;
    for (long r = 0; r < warmup + reps; r++) {
        int is_warm = r < warmup;
        long calls = is_warm ? 1 : batch;
        double t0 = now_s();
        for (long b = 0; b < calls; b++) matmul_naive_ijk(A, B, C, n);
        double t = (now_s() - t0) / (double)calls;
        last = t;
        printf("{\"time_s\": %.9e, \"timer_boundary\": \"kernel\", \"repetition\": %ld, "
               "\"is_warmup\": %s, \"checksum\": %.17g, \"memory_metric\": \"matrix_storage_bytes\", "
               "\"memory_bytes\": %.0f, \"batch\": %ld, \"language_impl\": \"C (gcc)\"}\n",
               t, r, is_warm ? "true" : "false", checksum(C, n), storage_bytes, calls);
        fflush(stdout);
        if (r == warmup - 1 && min_sample > 0.0 && last > 0.0) {
            batch = (long)ceil(min_sample / last);
            if (batch < 1) batch = 1;
            if (batch > 100000) batch = 100000;
        }
    }
    if (reps == 0 && warmup == 0) matmul_naive_ijk(A, B, C, n); /* --out-c only */
    if (c_out && matrix_write_bin(c_out, C, n)) { fprintf(stderr, "cannot write %s\n", c_out); return 1; }
    free(A); free(B); free(C);
    return 0;
}
