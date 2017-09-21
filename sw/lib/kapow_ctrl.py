#!/usr/bin/env python

# KAPow controller module class
# James Davis, 2016

import lib.module as module
import lib.lfsr as lfsr
import math

class kapow_ctrl(module.module):

	regs = {
		'stamp': 4*0,
		'kernel_hash': 4*1,
		'N': 4*2,
		'W': 4*3,
		'go': 4*4,
		'read': 4*5
	}
	
	def __init__(self, axi, addr):
		module.module.__init__(self, axi, addr)
		if self.read(self.regs['stamp']) != 0x7f323e2e:
			raise RuntimeError('Module at address ' + hex(self.addr) + ' did not return KAPow ID stamp')
		self.kernel_hash = self.read(self.regs['kernel_hash'])								# Read kernel hash, N and W from hardware
		self.N = self.read(self.regs['N'])
		self.W = self.read(self.regs['W'])
		self.fifo_depth = int(2**math.ceil(math.log(self.N*self.W, 2))/32)					# Number of 4-byte words needed to read out scan chain
		self.lfsr = lfsr.lfsr(self.W)														# LFSR decoder
	
	def measure(self):
		'Take new activity measurement. Returns array of activity counts'
		self.write(self.regs['go'], 1)														# Write anything to start measurement
																							# Read raw data. Scan chain enters FIFO MSB of least-active counter first, which is the LSB of the first word read out
		raw = ''.join(bin(self.read(self.regs['read']))[2:].zfill(32)[::-1] for _ in xrange(self.fifo_depth))
																							# Split into counts and decode, returning most-active first
		return [self.lfsr.decode(int(raw[self.W*(self.N - 1 - i):self.W*(self.N - i)], 2)) for i in xrange(self.N)]
		