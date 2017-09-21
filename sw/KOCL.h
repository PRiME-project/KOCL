// KAPow for OpenCL (KOCL) interface
// James Davis, 2016

typedef struct KOCL_t KOCL_t;

KOCL_t* KOCL_init(float update_period);
float KOCL_get(KOCL_t* KOCL, char* kernel_name);
void KOCL_print(KOCL_t* KOCL);
int KOCL_built(KOCL_t* KOCL);
void KOCL_del(KOCL_t* KOCL);
