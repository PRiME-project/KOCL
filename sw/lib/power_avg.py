#!/usr/bin/env python

import sys
import os
import time
from subprocess import check_output

def measPower(n):
	p = []
	for _ in range(n):
		s = check_output(os.path.join(sys.path[-1], 'lib', 'volreg FPGA_1_1'), shell = True)
		p.append(float(s.split()[7]))
	return sum(p)/len(p)
