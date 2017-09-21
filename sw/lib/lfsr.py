#!/usr/bin/env python

# LFSR decoder class
# James Davis, 2016

class lfsr:

	def __init__(self, width):
		self.table = {}
		state = 0
		count = 0
		while state not in self.table:
			self.table[state] = count
			if width == 9:
				state = ((state & ((1 << 8) - 1)) << 1) | (1 - (((state & 1 << 8) >> 8) ^ ((state & 1 << 4) >> 4)))
			else:
				raise ValueError('Unknown LFSR width ' + str(width))
			count += 1
			
	def decode(self, state):
		'Decode LFSR state into count'
		return self.table[state]
			