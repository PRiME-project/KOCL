SOURCES = float_add_mult_host.c
TARGET = float_add_mult_host
KOCL_ROOT = /root/KOCL/sw

COMPILE_CONFIG = $(shell aocl compile-config) $(shell python2.7-config --cflags) -I$(KOCL_ROOT)
LDFLAGS = $(shell aocl ldflags) $(shell aocl ldlibs) $(shell python2.7-config --ldflags)

host:
	$(CC) $(SOURCES) $(KOCL_ROOT)/KOCL.c -o $(TARGET) $(COMPILE_CONFIG) $(LDFLAGS)

run:
	./$(TARGET)
	
clean:
	rm -f $(TARGET)
	