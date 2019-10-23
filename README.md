# KOCL (KAPow for OpenCL)

### Licence

This code is distributed under the terms of the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html). See the [licence file](LICENCE.txt) for more information.

If you make use of this code, please acknowledge us by citing [our article](http://ieeexplore.ieee.org/document/8031047/):

	@article{KOCL,
		author={J. J. Davis and J. M. Levine and E. A. Stott and E. Hung and P. Y. K. Cheung and G. A. Constantinides},
		journal={IEEE Design \& Test},
		title={{KOCL: Power Self-awareness for Arbitrary FPGA-SoC-accelerated OpenCL Applications}},
		year={2017},
		volume={34},
		number={6}
	}

### Disclaimer

This is an academic tool. It was developed and has been tested with a single vendor toolchain and development board, and makes extensive use of undocumented, unsupported and hidden features. It is highly likely that this tool will not work properly with other software or hardware.

### Prerequesites

On your Linux development machine, you will need:

* [Quartus II](http://dl.altera.com/opencl/15.0/?platform=linux&download_manager=direct) (we developed using 15.0.0.145)
* [Cyclone V support](http://dl.altera.com/opencl/15.0/?platform=linux&download_manager=direct)
* [OpenCL SDK](http://dl.altera.com/opencl/15.0/?platform=linux&download_manager=direct)
* [Python 2.7](https://www.python.org/downloads/release/python-2711/)

Your [Cyclone V Soc Development Kit](https://www.altera.com/products/boards_and_kits/dev-kits/altera/kit-cyclone-v-soc.html) needs to be running Linux. You can download a fully functional image based on Ubuntu Core 16.04.2 [here](https://imperialcollegelondon.app.box.com/s/2tj5vwxnfrpprtgjg2ns1expl8ipfv9q). Use `root` and `root` to log in.

### Kernel Code

The KOCL Offline Compiler (KOC) requires kernel code to exist in a separate `.cl` file. Ensure that your kernel and host code are suitably split before continuing. There are a few sample applications available in `apps` that conform to this standard; you can use one of these as-is, modify one of them or make your own that is similarly structured.

Make sure that at least the `hw` and your application directories are on your development machine before continuing. Let's assume everything's inside directory `KOCL`.

If your Altera install directory is not the default `/mnt/applications/altera/15.0`, modify `hw/koc_env.sh` as needed before continuing.

Set up your environment for KOC by executing:

	source KOCL/hw/koc_env.sh

Run the complete flow, from `.cl` to instrumented bitstream, by executing:

	python KOCL/hw/koc.py <path to .cl file>
	
There are several optional flags: `-k`, `-b`, `-n` and `-w`.

`-k` allows you to choose which kernels to instrument. You can supply `all`, `none` or a space-separated list of kernel names. The default is `all`. `none` will instrument none of your kernels: your build will have the same result as running `aoc` instead. A subset might look like:

	python KOCL/hw/koc.py KOCL/apps/int_add_mult/int_add_mult.cl -k "int_add int_mult"
	
`-b` allows you to choose the board you wish to target. We only support the Cyclone V at the moment, so leave this set to its default of `c5soc`.

`-n` allows you to choose how many activity counters are added to each kernel. A higher value normally results in higher model accuracy but always results in extra area overhead. The default is `8`.

`-w` allows you to choose the width (in bits) of each activity counter. We only support 9-bit counters at the moment, so leave this set to its default of `9`.

Depending on the complexity of the required hardware, this could take several hours to complete.

### Incorporating KOCL in Host Code

This section is optional. If you don't want to add power monitoring functionality to your host code, skip this section. The (non-"vanilla") sample applications already have this code inserted.

Include KOCL's header file in your host code to expose its functions:

	#include "KOCL.h"
	
Initialise KOCL by passing in how frequently you want measurements to be taken (in s):

	KOCL_t* KOCL = KOCL_init(<update period>);

`KOCL_init` returns a pointer to a `KOCL_t` structure. Pass this to all subsequent KOCL function calls.

KN + 1, where K is the number of instrumented kernels and N is the number of counters per module (specified with `-n`), updates must occur to KOCL's model before its estimates are meaningful. To establish whether or not the required number of updates have occurred, use:

	int built = KOCL_built(KOCL);
	
We offer two 'get' functions at the moment: you can either print the breakdown (to your terminal) or request kernel-level values (for use by your host code). To print, use:

	KOCL_print(KOCL);
	
To get a value for a specific kernel's power, use:

	float kernel_power = KOCL_get(KOCL, <kernel name>);
	
You can also get a value for the static power using:

	float static_power = KOCL_get(KOCL, "static");

When you've finished, clean up:

	KOCL_del(KOCL);
	
### Execution

Make sure that at least the `sw` directory is on your Cyclone V board before continuing. The makefile we use expects it to be at `/root/KOCL/sw`.

Copy your application to the board. You will need the `.aocx` file produced by KOCL, but nothing else: don't copy all of the build files (the subdirectory within the application directory)!

Configure the Altera OpenCL runtime:

	source ./init_opencl.sh

Build your application:

	cd <application directory>
	make

Ensure that the MSEL switches on the board are set, left to right, up-down-up-down-up-up.

Run your application:	
	
	make run

### Support
	
Please contact [James Davis](mailto:james.davis@imperial.ac.uk) if you have any problems with this tool or would like to offer any suggestions for its improvement.
	
