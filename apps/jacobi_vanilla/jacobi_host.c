#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <assert.h>
#include "CL/opencl.h"
#include "jacobi.h"

int main(int argc, char* argv[]) {

	// Create platform
	cl_uint num_platforms;
	int ret = clGetPlatformIDs(0, NULL, &num_platforms);
	assert(ret == CL_SUCCESS);

	cl_platform_id* platform_id = (cl_platform_id*)malloc(sizeof(cl_platform_id)*num_platforms);
	cl_platform_id platform = NULL;
	clGetPlatformIDs(num_platforms, platform_id, &num_platforms);
	int i;
	char buffer[100];
	for(i = 0; i < num_platforms; i++){
		clGetPlatformInfo(platform_id[i], CL_PLATFORM_VENDOR, sizeof(buffer), buffer, NULL);
		platform = platform_id[i];
		if(!strcmp(buffer, "Altera Corporation")) break;
	}

	// Create context
	cl_context_properties props[3] = {CL_CONTEXT_PLATFORM, (cl_context_properties)platform, 0};
	cl_context context = clCreateContextFromType(props, CL_DEVICE_TYPE_ACCELERATOR, NULL, NULL, &ret);
	assert(ret == CL_SUCCESS);

	// Create device
	size_t dev_list_size;
	ret = clGetContextInfo(context, CL_CONTEXT_DEVICES, 0, NULL, &dev_list_size);
	assert(ret == CL_SUCCESS);
	cl_device_id* devices = (cl_device_id*)malloc(dev_list_size);
	clGetContextInfo(context, CL_CONTEXT_DEVICES, dev_list_size, devices, NULL);
	cl_device_id device = devices[0];

	// Create program
	FILE* handle = fopen("jacobi.aocx", "r");
	char* bin = (char*)malloc(100000000);
	size_t size = fread(bin, 1, 100000000, handle);
	fclose(handle);
	cl_program program = clCreateProgramWithBinary(context, 1, &device, (const size_t*)&size, (const unsigned char**)&bin, NULL, &ret);
	assert(ret == CL_SUCCESS);	
	ret = clBuildProgram(program, 1, &device, NULL, NULL, NULL);
	assert(ret == CL_SUCCESS);
	
	// Create command queue
	cl_command_queue queue = clCreateCommandQueue(context, device, 0, &ret);
	assert(ret == CL_SUCCESS);
	
	// Create kernels
	cl_kernel kernel_float = clCreateKernel(program, "jacobi_float", &ret);
	assert(ret == CL_SUCCESS);
	cl_kernel kernel_double = clCreateKernel(program, "jacobi_double", &ret);
	assert(ret == CL_SUCCESS);
	
	// Create memory objects
	float* A_float = (float*)malloc(N*N*sizeof(float));
	cl_mem A_buffer_float = clCreateBuffer(context, CL_MEM_READ_ONLY, N*N*sizeof(float), NULL, &ret);
	assert(ret == CL_SUCCESS);
	float* b_float = (float*)malloc(N*sizeof(float));
	cl_mem b_buffer_float = clCreateBuffer(context, CL_MEM_READ_ONLY, N*sizeof(float), NULL, &ret);
	assert(ret == CL_SUCCESS);
	float* x_float = (float*)malloc(N*sizeof(float));
	cl_mem x_buffer_float = clCreateBuffer(context, CL_MEM_READ_WRITE, N*sizeof(float), NULL, &ret);
	assert(ret == CL_SUCCESS);
	double* A_double = (double*)malloc(N*N*sizeof(double));
	cl_mem A_buffer_double = clCreateBuffer(context, CL_MEM_READ_ONLY, N*N*sizeof(double), NULL, &ret);
	assert(ret == CL_SUCCESS);
	double* b_double = (double*)malloc(N*sizeof(double));
	cl_mem b_buffer_double = clCreateBuffer(context, CL_MEM_READ_ONLY, N*sizeof(double), NULL, &ret);
	assert(ret == CL_SUCCESS);
	double* x_double = (double*)malloc(N*sizeof(double));
	cl_mem x_buffer_double = clCreateBuffer(context, CL_MEM_READ_WRITE, N*sizeof(double), NULL, &ret);
	assert(ret == CL_SUCCESS);
	
	// Set kernel arguments
	ret = clSetKernelArg(kernel_float, 0, sizeof(cl_mem), (void*)&A_buffer_float);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_float, 1, sizeof(cl_mem), (void*)&b_buffer_float);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_float, 2, sizeof(cl_mem), (void*)&x_buffer_float);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_double, 0, sizeof(cl_mem), (void*)&A_buffer_double);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_double, 1, sizeof(cl_mem), (void*)&b_buffer_double);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_double, 2, sizeof(cl_mem), (void*)&x_buffer_double);
	assert(ret == CL_SUCCESS);
	
	// Seed random number generator
	srand(time(NULL));
	
	int j, k, l;
	clock_t start, end;
	const size_t global_work_size = N;
	const size_t local_work_size = N;
	cl_event event;
	
	for(k = 0; k < ROUNDS; k++) {
	
		// Create initial input data. Make A diagonally dominant by keeping non-diagonal elements of A in range [0, 1] and diagonal elements in range [N, N^2]
		for(i = 0; i < N; i++) {
			for(j = 0; j < N; j++)
				if(i != j)
					A_double[i*N + j] = rand_in_range(0.0, 1.0);
				else
					A_double[i*N + j] = rand_in_range((double)N, (double)(N*N));
			b_double[i] = rand_in_range(0.0, (double)N);
		}
		
		for(l = 0; l < SOLVES_PER_ROUND; l++) {
			
			if(k % 2 == 0)
				printf("Precision: float\n");
			else
				printf("Precision: double\n");
			
			// Perturb input data. Keep A diagonally dominant. Reset x
			for(i = 0; i < N; i++) {
				for(j = 0; j < N; j++)
					if(i != j)
						A_double[i*N + j] += rand_in_range(0.0, 1.0/(double)N);
					else
						A_double[i*N + j] += rand_in_range(1.0, (double)N);
				b_double[i] += rand_in_range(0.0, 1.0);
				x_double[i] = 0.0;
			}
			
			// Capture start time
			start = clock();
			
			// If operating on floats, cast from doubles
			if(k % 2 == 0) {
				for(i = 0; i < N; i++) {
					for(j = 0; j < N; j++)
						A_float[i*N + j] = (float)A_double[i*N + j];
					b_float[i] = (float)b_double[i];
					x_float[i] = (float)x_double[i];
				}
			}
			
			// Write to memory objects
			if(k % 2 == 0) {
				ret = clEnqueueWriteBuffer(queue, A_buffer_float, CL_TRUE, 0, N*N*sizeof(float), A_float, 0, NULL, NULL);
				ret = clEnqueueWriteBuffer(queue, b_buffer_float, CL_TRUE, 0, N*sizeof(float), b_float, 0, NULL, NULL);
				ret = clEnqueueWriteBuffer(queue, x_buffer_float, CL_TRUE, 0, N*sizeof(float), x_float, 0, NULL, NULL);
				assert(ret == CL_SUCCESS);
			}
			else {
				ret = clEnqueueWriteBuffer(queue, A_buffer_double, CL_TRUE, 0, N*N*sizeof(double), A_double, 0, NULL, NULL);
				ret = clEnqueueWriteBuffer(queue, b_buffer_double, CL_TRUE, 0, N*sizeof(double), b_double, 0, NULL, NULL);
				ret = clEnqueueWriteBuffer(queue, x_buffer_double, CL_TRUE, 0, N*sizeof(double), x_double, 0, NULL, NULL);
				assert(ret == CL_SUCCESS);
			}
			
			// Run kernel
			for(i = 0; i < ITERATIONS_PER_SOLVE; i++) {
				if(k % 2 == 0)
					ret = clEnqueueNDRangeKernel(queue, kernel_float, (cl_uint)1, 0, &global_work_size, &local_work_size, 0, NULL, &event);
				else
					ret = clEnqueueNDRangeKernel(queue, kernel_double, (cl_uint)1, 0, &global_work_size, &local_work_size, 0, NULL, &event);
				assert(ret == CL_SUCCESS);
			}
			
			// Read from memory objects
			if(k % 2 == 0)
				ret = clEnqueueReadBuffer(queue, x_buffer_float, CL_TRUE, 0, N*sizeof(float), x_float, 1, &event, NULL);
			else
				ret = clEnqueueReadBuffer(queue, x_buffer_double, CL_TRUE, 0, N*sizeof(double), x_double, 1, &event, NULL);
			assert(ret == CL_SUCCESS);
			
			// If operating on floats, cast back to doubles
			if(k % 2 == 0)
				for(i = 0; i < N; i++)
					x_double[i] = (double)x_float[i];
			
			// Capture end time and calculate throughput
			end = clock();
			printf("Throughput: %.2f solves/sec\n", (float)CLOCKS_PER_SEC/(end - start));
			
			// Calculate error
			printf("Error: %.2e\n", l2norm_sq(A_double, b_double, x_double));
		
		}
	
	}
	
	// Clean up
	ret = clReleaseKernel(kernel_float);
	assert(ret == CL_SUCCESS);
	ret = clReleaseKernel(kernel_double);
	assert(ret == CL_SUCCESS);
	ret = clReleaseCommandQueue(queue);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(A_buffer_float);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(b_buffer_float);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(x_buffer_float);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(A_buffer_double);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(b_buffer_double);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(x_buffer_double);
	assert(ret == CL_SUCCESS);
	ret = clReleaseProgram(program);
	assert(ret == CL_SUCCESS);
	ret = clReleaseContext(context);
	assert(ret == CL_SUCCESS);
	
	return 0;
	
}

double rand_in_range(double min, double max) {
	
	return min + (max - min)*(double)rand()/RAND_MAX;
	
}

double l2norm_sq(double* A, double* b, double* x) {

	int i, j;
	double norm = 0.0;
	double temp;

	for(i = 0; i < N; i++) {
		temp = 0.0;
		for(j = 0; j < N; j++)
			temp += A[i*N + j]*x[j];
		norm += (temp - b[i])*(temp - b[i]);
	}

	return norm;

}
