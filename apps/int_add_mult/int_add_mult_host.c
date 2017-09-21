#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "CL/opencl.h"
#include "KOCL.h"

#undef NDEBUG
#include "assert.h"

#define N 1000000

int main(int argc, char* argv[]) {
	
	int ret;

	// Create platform
	cl_uint num_platforms;
	ret = clGetPlatformIDs(0, NULL, &num_platforms);
	assert(ret == CL_SUCCESS);

	cl_platform_id* platform_id = (cl_platform_id *)malloc(sizeof(cl_platform_id)*num_platforms);
	cl_platform_id platform = NULL;
	clGetPlatformIDs(num_platforms, platform_id, &num_platforms);
	int i;
	for(i = 0; i < num_platforms; i++){
		char buffer[100];
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
	cl_device_id *devices = (cl_device_id *)malloc(dev_list_size);
	clGetContextInfo(context, CL_CONTEXT_DEVICES, dev_list_size, devices, NULL);
	cl_device_id device = devices[0];

	// Create program
	FILE *handle = fopen("int_add_mult.aocx", "r");
	char *buffer = (char *)malloc(100000000);
	size_t size = fread(buffer, 1, 100000000, handle);
	fclose(handle);
	cl_program program = clCreateProgramWithBinary(context, 1, &device, (const size_t *)&size, (const unsigned char **)&buffer, NULL, &ret);
	assert(ret == CL_SUCCESS);	
	ret = clBuildProgram(program, 1, &device, NULL, NULL, NULL);
	assert(ret == CL_SUCCESS);
	
	// Create command queues
	cl_command_queue queue_add = clCreateCommandQueue(context, device, 0, &ret);
	assert(ret == CL_SUCCESS);
	cl_command_queue queue_mult = clCreateCommandQueue(context, device, 0, &ret);
	assert(ret == CL_SUCCESS);
	
	// Create kernels
	cl_kernel kernel_add = clCreateKernel(program, "int_add", &ret);
	assert(ret == CL_SUCCESS);
	cl_kernel kernel_mult = clCreateKernel(program, "int_mult", &ret);
	assert(ret == CL_SUCCESS);
	
	// Create memory objects
	int *x_add = (int *)malloc(N*sizeof(int));
	cl_mem x_buffer_add = clCreateBuffer(context, CL_MEM_READ_ONLY, N*sizeof(int), NULL, &ret);
	assert(ret == CL_SUCCESS);
	int *y_add = (int *)malloc(N*sizeof(int));
	cl_mem y_buffer_add = clCreateBuffer(context, CL_MEM_READ_ONLY, N*sizeof(int), NULL, &ret);
	assert(ret == CL_SUCCESS);
	int *z_add = (int *)malloc(N*sizeof(int));
	cl_mem z_buffer_add = clCreateBuffer(context, CL_MEM_WRITE_ONLY, N*sizeof(int), NULL, &ret);
	assert(ret == CL_SUCCESS);
	int *x_mult = (int *)malloc(N*sizeof(int));
	cl_mem x_buffer_mult = clCreateBuffer(context, CL_MEM_READ_ONLY, N*sizeof(int), NULL, &ret);
	assert(ret == CL_SUCCESS);
	int *y_mult = (int *)malloc(N*sizeof(int));
	cl_mem y_buffer_mult = clCreateBuffer(context, CL_MEM_READ_ONLY, N*sizeof(int), NULL, &ret);
	assert(ret == CL_SUCCESS);
	int *z_mult = (int *)malloc(N*sizeof(int));
	cl_mem z_buffer_mult = clCreateBuffer(context, CL_MEM_WRITE_ONLY, N*sizeof(int), NULL, &ret);
	assert(ret == CL_SUCCESS);
	
	// Set kernel arguments
	ret = clSetKernelArg(kernel_add, 0, sizeof(cl_mem), (void *)&x_buffer_add);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_add, 1, sizeof(cl_mem), (void *)&y_buffer_add);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_add, 2, sizeof(cl_mem), (void *)&z_buffer_add);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_mult, 0, sizeof(cl_mem), (void *)&x_buffer_mult);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_mult, 1, sizeof(cl_mem), (void *)&y_buffer_mult);
	assert(ret == CL_SUCCESS);
	ret = clSetKernelArg(kernel_mult, 2, sizeof(cl_mem), (void *)&z_buffer_mult);
	assert(ret == CL_SUCCESS);
	
	// Seed random number generator
	srand(time(NULL));
	
	// Create input data
	for(i = 0; i < N; i++) {
		x_add[i] = rand();
		y_add[i] = rand();
		x_mult[i] = rand();
		y_mult[i] = rand();
	}
	
	// Initialise KOCL
	KOCL_t *KOCL = KOCL_init(1.0);
	
	// TEST 1: INT_ADD ONLY
	
	// Write to memory objects
	ret = clEnqueueWriteBuffer(queue_add, x_buffer_add, CL_TRUE, 0, N*sizeof(int), x_add, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	ret = clEnqueueWriteBuffer(queue_add, y_buffer_add, CL_TRUE, 0, N*sizeof(int), y_add, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueWriteBuffer returned\n");

	// Run kernel
	const size_t global_work_size = N;
	const size_t local_work_size = 1;
	cl_event event_add;
	ret = clEnqueueNDRangeKernel(queue_add, kernel_add, (cl_uint)1, 0, &global_work_size, &local_work_size, 0, NULL, &event_add);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueNDRangeKernel returned\n");
	
	// Wait for kernel execution to finish. While it's running, print power breakdowns
	cl_int status;
	do {
		KOCL_print(KOCL);
		sleep(1);
		clGetEventInfo(event_add, CL_EVENT_COMMAND_EXECUTION_STATUS, sizeof(cl_int), &status, NULL);
	} while(status != CL_COMPLETE);
	printf("clGetEventInfo returned\n");
	
	// Read from memory objects
	ret = clEnqueueReadBuffer(queue_add, z_buffer_add, CL_TRUE, 0, N*sizeof(int), z_add, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueReadBuffer returned\n");

	// Test results
	for(i = 0; i < N; i++) {
		if(i < 10) {
			printf("%i + %i = %i\n", x_add[i], y_add[i], z_add[i]);
		}
		assert(z_add[i] == x_add[i] + y_add[i]);
	}

	printf("Test 1 passed succesfully!\n");
	
	// TEST 2: INT_MULT ONLY
	
	// Write to memory objects
	ret = clEnqueueWriteBuffer(queue_mult, x_buffer_mult, CL_TRUE, 0, N*sizeof(int), x_mult, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	ret = clEnqueueWriteBuffer(queue_mult, y_buffer_mult, CL_TRUE, 0, N*sizeof(int), y_mult, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueWriteBuffer returned\n");

	// Run kernel	
	cl_event event_mult;
	ret = clEnqueueNDRangeKernel(queue_mult, kernel_mult, (cl_uint)1, 0, &global_work_size, &local_work_size, 0, NULL, &event_mult);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueNDRangeKernel returned\n");
	
	// Wait for kernel execution to finish. While it's running, print power breakdowns
	do {
		KOCL_print(KOCL);
		sleep(1);
		clGetEventInfo(event_mult, CL_EVENT_COMMAND_EXECUTION_STATUS, sizeof(cl_int), &status, NULL);
	} while(status != CL_COMPLETE);
	printf("clGetEventInfo returned\n");
	
	// Read from memory objects
	ret = clEnqueueReadBuffer(queue_mult, z_buffer_mult, CL_TRUE, 0, N*sizeof(int), z_mult, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueReadBuffer returned\n");

	// Test results
	for(i = 0; i < N; i++) {
		if(i < 10) {
			printf("%i*%i = %i\n", x_mult[i], y_mult[i], z_mult[i]);
		}
		assert(z_mult[i] == x_mult[i]*y_mult[i]);
	}
	
	printf("Test 2 passed succesfully!\n");
	
	// TEST 3: INT_ADD + INT_MULT
	
	// Write to memory objects
	ret = clEnqueueWriteBuffer(queue_add, x_buffer_add, CL_TRUE, 0, N*sizeof(int), x_add, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	ret = clEnqueueWriteBuffer(queue_add, y_buffer_add, CL_TRUE, 0, N*sizeof(int), y_add, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueWriteBuffer returned\n");
	ret = clEnqueueWriteBuffer(queue_mult, x_buffer_mult, CL_TRUE, 0, N*sizeof(int), x_mult, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	ret = clEnqueueWriteBuffer(queue_mult, y_buffer_mult, CL_TRUE, 0, N*sizeof(int), y_mult, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueWriteBuffer returned\n");
	
	// Run kernels
	ret = clEnqueueNDRangeKernel(queue_add, kernel_add, (cl_uint)1, 0, &global_work_size, &local_work_size, 0, NULL, &event_add);
	assert(ret == CL_SUCCESS);
	ret = clEnqueueNDRangeKernel(queue_mult, kernel_mult, (cl_uint)1, 0, &global_work_size, &local_work_size, 0, NULL, &event_mult);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueNDRangeKernel returned\n");
	
	// Wait for kernel executions to finish. While they're running, print power breakdowns
	cl_int statuses[2];
	do {
		KOCL_print(KOCL);
		sleep(1);
		clGetEventInfo(event_add, CL_EVENT_COMMAND_EXECUTION_STATUS, sizeof(cl_int), &statuses[0], NULL);
		clGetEventInfo(event_mult, CL_EVENT_COMMAND_EXECUTION_STATUS, sizeof(cl_int), &statuses[1], NULL);
	} while(statuses[0] != CL_COMPLETE || statuses[1] != CL_COMPLETE);
	printf("clGetEventInfo returned\n");
	
	// Read from memory objects
	ret = clEnqueueReadBuffer(queue_add, z_buffer_add, CL_TRUE, 0, N*sizeof(int), z_add, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	ret = clEnqueueReadBuffer(queue_mult, z_buffer_mult, CL_TRUE, 0, N*sizeof(int), z_mult, 0, NULL, NULL);
	assert(ret == CL_SUCCESS);
	printf("clEnqueueReadBuffer returned\n");

	// Test results
	for(i = 0; i < N; i++) {
		if(i < 10) {
			printf("%i + %i = %i\n", x_add[i], y_add[i], z_add[i]);
			printf("%i*%i = %i\n", x_mult[i], y_mult[i], z_mult[i]);
		}
		assert(z_add[i] == x_add[i] + y_add[i]);
		assert(z_mult[i] == x_mult[i]*y_mult[i]);
	}
	
	printf("Test 3 passed succesfully!\n");

	// Clean up
	ret = clReleaseKernel(kernel_add);
	assert(ret == CL_SUCCESS);
	ret = clReleaseKernel(kernel_mult);
	assert(ret == CL_SUCCESS);
	ret = clReleaseCommandQueue(queue_add);
	assert(ret == CL_SUCCESS);
	ret = clReleaseCommandQueue(queue_mult);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(x_buffer_add);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(y_buffer_add);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(z_buffer_add);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(x_buffer_mult);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(y_buffer_mult);
	assert(ret == CL_SUCCESS);
	ret = clReleaseMemObject(z_buffer_mult);
	assert(ret == CL_SUCCESS);
	ret = clReleaseProgram(program);
	assert(ret == CL_SUCCESS);
	ret = clReleaseContext(context);
	assert(ret == CL_SUCCESS);
	
	// KOCL clean-up
	KOCL_del(KOCL);
	
	return 0;
}	
