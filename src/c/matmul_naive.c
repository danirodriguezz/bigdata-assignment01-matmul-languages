/* Naive triple-loop matrix multiplication (the controlled kernel of Assignment 1). */
#include "matmul_naive.h"

void matmul_naive_ijk(const double *A, const double *B, double *C, size_t n)
{
    for (size_t i = 0; i < n; i++) {
        for (size_t j = 0; j < n; j++) {
            double s = 0.0;                      /* scalar accumulator, same as Java/Python */
            for (size_t k = 0; k < n; k++) {
                s += A[i * n + k] * B[k * n + j]; /* A walks a row (stride 1), B a column (stride n) */
            }
            C[i * n + j] = s;
        }
    }
}
