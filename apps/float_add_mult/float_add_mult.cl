kernel void float_add(__global const float* x, __global const float* y, __global float* z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i] + y[i];
	}
}

kernel void float_mult(__global const float* x, __global const float* y, __global float* z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i]*y[i];
	}
}