/* Naive dense matrix multiplication C = A * B (ijk loop order, scalar accumulator).
 * Matrices are n x n, float64, stored row-major in one contiguous block: element (i, j) is M[i*n + j].
 * Reused by later assignments as the validated sequential baseline. */
#ifndef MATMUL_NAIVE_H
#define MATMUL_NAIVE_H
#include <stddef.h>

/* Computes C[i][j] = sum_{k=0}^{n-1} A[i][k] * B[k][j], accumulating in increasing k.
 * C is fully overwritten (it does not need to be zeroed). */
void matmul_naive_ijk(const double *A, const double *B, double *C, size_t n);

#endif
