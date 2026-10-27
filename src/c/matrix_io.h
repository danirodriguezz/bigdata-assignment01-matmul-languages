/* Reading/writing the shared input format: raw little-endian float64, row-major, no header. */
#ifndef MATRIX_IO_H
#define MATRIX_IO_H
#include <stddef.h>

/* Allocates an n*n double block and fills it from `path`. Returns NULL on error (message on stderr).
 * Assumes a little-endian host (x86-64), which matches the file format. */
double *matrix_read_bin(const char *path, size_t n);

/* Writes n*n doubles to `path`. Returns 0 on success. */
int matrix_write_bin(const char *path, const double *M, size_t n);

#endif
