#!/usr/bin/env python

import sys
from itertools import imap
import re
import os

def parse_asf(asf, regex):
	act = []
	with open(asf) as f:
		hier = []
		for line in f:
			if any( [ 
				not line.strip(),
				line.startswith('#'),
				line.startswith('FORMAT_VERSION'),
				line.startswith('DEFINE_FLAG'),
				line.startswith('BEGIN_OUTPUT_SIGNAL_INFO')
				] ):
				continue
			depth = re.search(r'[^ ]', line).start()
			hier = hier[:depth-1]
			line = line.strip()
			assert line[-1] == ';'
			line = line.rstrip(';')
			line = line.split()
			hier.append(line[0])
			if len(line) == 1:
				continue
			if len(line) == 4:
				signal = '|'.join(hier)
				if re.match(regex, signal):
					act.append((float(line[2]),'|'.join(hier)))
				continue
			raise RuntimeError
	return act

def write_vqm(vqm, vqm_inst, act):
	num = len(act)

	re_mod = re.compile(r'^(module.*) \(')
	re_io = re.compile(r'^((in|out)put\s+(\[\d+:\d+\]\s+)?[^ ]+;)')
	re_axy = re.compile(r'[a-z]+_unconnected_wire_\d+,')
	re_dff = re.compile(r'^dffeas ([^ ]+ )\(')
	re_end = re.compile(r'^endmodule')
	i = 0
	last_dffeas = None
	with open(vqm) as fi, open(vqm_inst, 'w') as fo:
		for line in fi:
			# Add prime signals
			line = re_mod.sub(
r'''\1 (
\tkapow_clk,
\tkapow_cnten,
\tkapow_scanin,
\tkapow_scanout,'''
			, line, count=1)
			# Add our prime ports before the first port
			if re_io:
				new_line = re_io.sub(
r'''input   kapow_clk;
input   kapow_cnten;
input   kapow_scanin;
output  kapow_scanout;
parameter kapow_nbits = 9;
\1'''
				, line)
				if new_line != line:
					re_io = None
					line = new_line

			# Fix VQM breakage with cyclonev_mac (DSP) blocks
			# by removing all these "unconnected" wires
			line = re_axy.sub('', line)

			# At the end of the VQM, add KAPow instrumentation
			if re_end.match(line):
				fo.write(
r'''
localparam num_counters = %d;

wire [num_counters:0] kapow_scan;
assign kapow_scan[0] = kapow_scanin;

wire [num_counters-1:0] kapow_activity;

// Create as many kapow_scan_counter instances as the number 
// signals to be instrumented
genvar i;
generate for (i = 0; i < num_counters; i=i+1) begin : g
		kapow_scan_counter #(
			.nbits(kapow_nbits)
		)
		c(
			.clk(kapow_clk), 
			.en(kapow_cnten),
			.in(kapow_activity[i]), 
			.si(kapow_scan[i]),
			.so(kapow_scan[i+1])
		);
end
endgenerate

// Attach the last counter's scan output as the
// input to the FIFO
assign kapow_scanout = kapow_scan[num_counters];
''' % num
				)

				fo.write('// Attach counters to signals with highest activity\n')
				for j,a in enumerate(act):
					fo.write('assign kapow_activity[%d] = \\%s ; // %.2e\n' % (j,a[1],a[0]))
			
			fo.write(line)

def write_signals(signals, act):
	with open(signals, 'w') as f:
		for _,a in act:
			f.write(a + '\n')
			
# Parse VQM to establish which signals to monitor. Signals connected to the following primitives' ports are OK:
# FFs: q
# LUTs: combout, sumout
# RAMs: portadataout, portbdataout
# MACs: resulta, resultb
def legal_signals(vqm):
	legal = []
	with open(vqm, 'r') as handle:
		for line in handle:
			if line.strip().startswith('.'):
				(port, signal) = line.lstrip().split('(')
				signal = signal.split(')')[0].lstrip('\\').rstrip()
				if port in ['.q', '.combout', '.sumout', '.portadataout', '.portbdataout', '.resulta', '.resultb'] and signal not in legal:
					legal.append(signal)
	return legal

def main(argv):
	try:
		# Input VQM
		vqm_in = argv.pop(0)
		# Output VQM
		vqm_out = argv.pop(0)
		# ASF
		asf = argv.pop(0)
		# Regular expression for filtering signals
		regex = argv.pop(0)
		# Number of top-most activity signals to instrument
		num = int(argv.pop(0))
	except IndexError:
		print 'Usage: ./kapow.py <vqm_in> <vqm_out> <asf> <regex> <num>'
		print 'Output: <vqm_out>'
		return

	act = parse_asf(asf, regex)
	act.sort(reverse=True)
	
	# Remove illegal signals from head of list until there are enough legal signals to use
	legal = legal_signals(vqm_in)
	no_legal = 0
	while no_legal < num:
		try:
			if act[no_legal][1] in legal:
				no_legal += 1
			else:
				del act[no_legal]
		except IndexError:
			break
	
	del act[num:]

	write_vqm(vqm_in, vqm_out, act)

if __name__=='__main__':
	main(sys.argv[1:])
