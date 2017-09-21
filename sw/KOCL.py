#!/usr/bin/env python

# KAPow for OpenCL (KOCL) interface
# James Davis, 2016

import sys
import os
import hashlib
import multiprocessing
import time

found = False																					# Add the directory this script resides in to the search path. Since this script is wrapped in an interpreter, find it dynamically
depth = 0
while not found:
	for root, dirs, files in os.walk('/'):
		if root.count(os.sep) >= depth:
			del dirs[:]
		if __file__ in files:
			sys.path.append(root)
			found = True
			break
	depth += 1

import lib.axi as axi
import lib.kapow_ctrl as kapow_ctrl
import lib.rls as rls
					
class KOCL_model(multiprocessing.Process):

	def __init__(self, pipe, kernels, update_period):
		multiprocessing.Process.__init__(self)
		self.daemon = True
		self.pipe = pipe
		self.update_period = update_period
		bus = axi.axi()
		kapow_ctrls = {}																		# Controller discovery
		addr = 0
		while addr < bus.size:
			if bus.read(addr) == 0x7f323e2e:
				for kernel in kernels:
					if bus.read(addr + 4) == int(hashlib.md5(kernel).hexdigest()[-8:], 16) % 2**31:
						kapow_ctrls[kernel] = kapow_ctrl.kapow_ctrl(bus, addr)
				addr += 28
			else:
				addr += 4
		self.model = rls.rls(kapow_ctrls)
		
	def run(self):
		last_update_time = time.time() - self.update_period
		while True:
			if time.time() - last_update_time >= self.update_period:
				last_update_time += self.update_period
				self.model.update()
				self.pipe.send(self.model.split())
				
class KOCL_pool(multiprocessing.Process):

	def __init__(self, pipes):
		multiprocessing.Process.__init__(self)
		self.daemon = True
		self.pipes = pipes
		self.breakdown = {}
		self.model_built = False
		
	def run(self):
		while True:
			if self.pipes['iface'].poll():
				command, kernel = self.pipes['iface'].recv()
				if command == 'split':															# Send power breakdown
					if kernel:																	# If a kernel name has been received, send only that element. If the name given is invalid, send None
						try:
							self.pipes['iface'].send(self.breakdown[kernel])
						except KeyError:
							self.pipes['iface'].send(None)
					else:																		# If no kernel name has been received, send all elements
						self.pipes['iface'].send(self.breakdown)
				else:																			# Send model built True/False flag
					self.pipes['iface'].send(self.model_built)
			if self.pipes['updater'].poll():
				self.breakdown, self.model_built = self.pipes['updater'].recv()
			
class KOCL_iface:

	def __init__(self, update_period):
		kernels = []																			# Read kernel names from .aocx. This will return ALL kernel names, but discovery will eliminate those that aren't instrumented
		for file in os.listdir('.'):
			if os.path.splitext(file)[1] == '.aocx':
				with open(file, 'r') as handle:
					for line in handle:
						if line.startswith('	<kernel name="'):
							kernels.append(line.split('"')[1])
				break
		lander_pipes = {}
		lander_pipes['iface'], self.pipe = multiprocessing.Pipe()
		updater_pipe, lander_pipes['updater'] = multiprocessing.Pipe()
		daemons = (																				# Spawn daemons
			KOCL_pool(lander_pipes),
			KOCL_model(updater_pipe, kernels, update_period)
		)
		for daemon in daemons:
			daemon.start()
	
	def split_get(self, kernel):
		self.pipe.send(('split', kernel))
		return self.pipe.recv()
			
	def split_print(self):
		self.pipe.send(('split', None))
		breakdown = self.pipe.recv()
		for kernel, power in breakdown.iteritems():
			print '{}: {:.2f} mW'.format(kernel, power)
		
	def built(self):
		self.pipe.send(('built', None))
		return self.pipe.recv()
		