#ifndef JACOBI_H
#define JACOBI_H

#define N 4096
#define UNROLL_LEVEL 8						// Factor by which to unroll kernel loop. Must be an exact divisor of N
#define ROUNDS 1000
#define SOLVES_PER_ROUND 10
#define ITERATIONS_PER_SOLVE 10

int main(int argc, char* argv[]);
double rand_in_range(double min, double max);
double l2norm_sq(double* A, double* b, double* x);

#endif
