kernel void int_add(__global const int* x, __global const int* y, __global int* z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i] + y[i];
	}
}

kernel void int_mult(__global const int* x, __global const int* y, __global int* z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i]*y[i];
	}
}