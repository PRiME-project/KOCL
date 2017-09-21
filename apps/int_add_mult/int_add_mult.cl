kernel void int_add(global int *x, global int *y, global int *z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i] + y[i];
	}
}

kernel void int_mult(global int *x, global int *y, global int *z){
	int i = get_global_id(0);
	int t;
	for(t = 0; t < 1000; t++) {
		z[i] = x[i]*y[i];
	}
}