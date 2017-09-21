// KAPow for OpenCL (KOCL) interface
// James Davis, 2016

#include <Python.h>
#include "KOCL.h"

struct KOCL_t {
	PyObject* script_obj;
};

KOCL_t* KOCL_init(float update_period) {
	
	Py_Initialize();
	
	FILE* handle = popen("find / -name KOCL.py", "r");
	char path[100];
	fscanf(handle, "%s", path);
	pclose(handle);
	PyRun_SimpleFile(fopen(path, "r"), "KOCL.py");
	
	PyObject* script_main = PyImport_AddModule("__main__");
    PyObject* script_dict = PyModule_GetDict(script_main);
	PyObject* script_class = PyDict_GetItemString(script_dict, "KOCL_iface");
	
	KOCL_t* KOCL = malloc(sizeof(KOCL_t));
	PyObject* vars = Py_BuildValue("(f)", update_period);
	KOCL->script_obj = PyObject_CallObject(script_class, vars);
	
	Py_DECREF(vars);
	
	return KOCL;
	
}

float KOCL_get(KOCL_t* KOCL, char* kernel_name) {

	PyObject* rtn = PyObject_CallMethod(KOCL->script_obj, "split_get", "(s)", kernel_name);

	float power;
	if(rtn == Py_None) {
		power = NAN;																			// This should probably do something nicer when a non-kernel name is given
	}
	else {
		power = (float)PyFloat_AsDouble(rtn);
	}
	
	Py_DECREF(rtn);
	
	return power;

}

void KOCL_print(KOCL_t* KOCL) {

	PyObject* rtn = PyObject_CallMethod(KOCL->script_obj, "split_print", NULL);
	
	Py_DECREF(rtn);

}

int KOCL_built(KOCL_t* KOCL) {

	PyObject* rtn = PyObject_CallMethod(KOCL->script_obj, "built", NULL);
	
	int built = (rtn == Py_True);
	
	Py_DECREF(rtn);
	
	return built;

}

void KOCL_del(KOCL_t* KOCL) {

	Py_DECREF(KOCL->script_obj);
	Py_Finalize();
	
	free(KOCL);
	
}
