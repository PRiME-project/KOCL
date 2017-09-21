#!/usr/bin/env python

# Generic AXI module class. Intended to be inherited by specific module classes
# James Davis, 2016

class module:

	def __init__(self, axi, addr):
		self.axi = axi
		self.addr = addr
		
	def read(self, addr):
		'Read 4 bytes from register at addr'
		return self.axi.read(self.addr + addr)
		
	def write(self, addr, data):
		'Write data as 4 bytes to register at addr'
		self.axi.write(self.addr + addr, data)
		