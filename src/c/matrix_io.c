#include "matrix_io.h"
#include <stdio.h>
#include <stdlib.h>

double *matrix_read_bin(const char *path, size_t n)
{
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); return NULL; }
    double *M = malloc(n * n * sizeof(double));
    if (!M) { fprintf(stderr, "Cannot allocate memory for %s\n", path); fclose(f); return NULL; }
    size_t got = fread(M, sizeof(double), n * n, f);
    /* the file must contain exactly n*n values */
    int extra = fgetc(f);
    fclose(f);
    if (got != n * n || extra != EOF) {
        fprintf(stderr, "%s: expected exactly %zu float64 values\n", path, n * n);
        free(M);
        return NULL;
    }
    return M;
}

int matrix_write_bin(const char *path, const double *M, size_t n)
{
    FILE *f = fopen(path, "wb");
    if (!f) { perror(path); return 1; }
    size_t put = fwrite(M, sizeof(double), n * n, f);
    fclose(f);
    return put == n * n ? 0 : 1;
}
