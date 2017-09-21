kernel void float_add(__global const float* restrict x, __global const float* restrict y, __global float* restrict z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i] + y[i];
	}
}

kernel void float_mult(__global const float* restrict x, __global const float* restrict y, __global float* restrict z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i]*y[i];
	}
}