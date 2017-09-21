kernel void float_add(global float *x, global float *y, global float *z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i] + y[i];
	}
}

kernel void float_mult(global float *x, global float *y, global float *z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i]*y[i];
	}
}