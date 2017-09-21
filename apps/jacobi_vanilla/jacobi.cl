#include "jacobi.h"

/* Kernel jacobi_float()
Computes Jacobi solution of Ax = b in single-precision floating point
A: pointer to (N x N) matrix A
b: pointer to (N x 1) vector b
x: pointer to (N x 1) vector x */

__attribute__((reqd_work_group_size(N, 1, 1)))
__attribute__((max_work_group_size(N)))
__kernel void jacobi_float(__global const float* restrict A, __global const float* restrict b, __global float* restrict x) {
	
	int i = get_global_id(0);
	int j;
	float temp = 0.0;
	
	#pragma unroll UNROLL_LEVEL
	for(j = 0; j < N; j++)						// temp = sum over i != j of A[i,j]*x[j]
		if(i != j)
			temp += A[i*N + j]*x[j];
	
	x[i] = (b[i] - temp)/A[i*N + i];			// x[i] = (b[i] - temp)/A[i,i]
	
	//barrier(CLK_GLOBAL_MEM_FENCE);

}

/* Kernel jacobi_double()
Computes Jacobi solution of Ax = b in double-precision floating point
A: pointer to (N x N) matrix A
b: pointer to (N x 1) vector b
x: pointer to (N x 1) vector x */

__attribute__((reqd_work_group_size(N, 1, 1)))
__attribute__((max_work_group_size(N)))
__kernel void jacobi_double(__global const double* restrict A, __global const double* restrict b, __global double* restrict x) {
	
	int i = get_global_id(0);
	int j;
	double temp = 0.0;
	
	#pragma unroll UNROLL_LEVEL
	for(j = 0; j < N; j++)						// temp = sum over i != j of A[i,j]*x[j]
		if(i != j)
			temp += A[i*N + j]*x[j];
	
	x[i] = (b[i] - temp)/A[i*N + i];			// x[i] = (b[i] - temp)/A[i,i]
	
	//barrier(CLK_GLOBAL_MEM_FENCE);

}
