#!/usr/bin/env python

# KOC: The KOCL Offline Compiler
# Builds KAPow-instrumentated OpenCL kernel systems
# James Davis, 2015

# Usage: ./KOC.py <OPENCL_KERNEL_FILE (.cl)> [-k <KERNELS {"kernel_1 kernel_2 ..."|none|all}>] [-b <BOARD_TO_TARGET>] [-n <KAPOW_N>] [-w <KAPOW_W>]
# Prerequesites: python, aoc, quartus_sh and qsys-script paths must be in PATH

import argparse
import os
import subprocess
import shutil
import hashlib

# Parse arguments
# TODO: support W != 9

parser = argparse.ArgumentParser(description = 'KOC: The KOCL Offline Compiler')
parser.add_argument('cl_file', help = 'path to kernel code (.cl) file')
parser.add_argument('-k', '--kernels', default = 'all', help = 'space-separated list of kernels to instrument OR none OR all, default: all')
parser.add_argument('-b', '--board', default = 'c5soc', help = 'target board name, default: c5soc')
parser.add_argument('-n', '--kapow_n', type = int, default = 8, help = 'counters per kernel (N), default: 8')
parser.add_argument('-w', '--kapow_w', type = int, choices = [9], default = 9, help = 'counter width (W), default: 9')
args = parser.parse_args()
print 'KOC: The KOCL Offline Compiler'
print 'KOC: Starting'
	
# Establish project name from CL file

if os.path.isfile(args.cl_file) and os.path.splitext(args.cl_file)[1] == '.cl':
	proj = os.path.splitext(os.path.basename(args.cl_file))[0]
else:
	raise RuntimeError('KOC: ERROR: Unrecognised file type')
print 'KOC: Working on project "{}"'.format(proj)
	
# Establish directories of project and this script

proj_dir = os.path.dirname(os.path.realpath(args.cl_file))
self_dir = os.path.dirname(os.path.realpath(__file__))
	
# Execute OpenCL flow until QSys system generation
# This will break if aoc is not called from project directory

os.chdir(proj_dir)
subprocess.call('aoc -s -v ' + os.path.join(proj_dir, proj + '.cl --board ' + args.board), shell = True)
os.chdir(self_dir)
print 'KOC: First-stage AOC generation complete'
		
# Gather names of kernels present in kernel RTL file. Verify kernel name arguments against these, if necessary

with open(os.path.join(proj_dir, proj, proj + '.v'), 'r') as handle:
	lines = handle.readlines()
	
kernels = {'all': []}
for line in lines:
	if line.startswith('module') and line.rstrip().endswith('_sys_cycle_time'):
		kernels['all'].append(line[line.index(' ') + 1:line.index('_sys_cycle_time')])
if args.kernels == 'none':
	kernels['inst'] = []
elif args.kernels == 'all':
	kernels['inst'] = kernels['all']
else:
	kernels['inst'] = args.kernels.strip('"').split(' ')
	for kernel in kernels['inst']:
		if kernel not in kernels['all']:
			raise RuntimeError('KOC: ERROR: Unable to locate kernel with name "' + kernel + '"')
print 'KOC: Kernels verified'
		
# Split kernel RTL file by kernel. Create a new directory for, and put its source into, each

out_content = ''
kernel = None
for line in lines:
	out_content += line
	if line.startswith('module') and line.rstrip().endswith('_sys_cycle_time'):
		kernel = line[line.index(' ') + 1:line.index('_sys_cycle_time')]
		os.mkdir(os.path.join(proj_dir, proj, kernel))
	if kernel and line.rstrip().endswith('endmodule'):
		with open(os.path.join(proj_dir, proj, kernel, kernel + '.v'), 'w') as handle:
			handle.write(out_content)
		out_content = ''
		kernel = None
print 'KOC: Kernels split'
			
# Extract AOC includes from kernel QSys component Tcl script as list of (type, file) tuples
# QSys and Quartus II use different type conventions, so they must be converted

aoc_includes = []
with open(os.path.join(proj_dir, proj, proj + '_system_hw.tcl'), 'r') as handle:
	for line in handle:
		if line.startswith('add_fileset_file'):
			parts = line.split(' ')
			(type, file) = (parts[2].replace('_', '') + '_FILE', parts[4])
			if file.startswith('$::env(ALTERAOCLSDKROOT)') and (type, file) not in aoc_includes:
				aoc_includes.append((type, file))
print 'KOC: AOC includes extracted'
				
for kernel in kernels['inst']:
	print 'KOC: Working on kernel "{}"'.format(kernel)
	
	# Copy SDC file containing clock constraints
	
	shutil.copyfile(os.path.join('lib', 'kernel_clocks.sdc'), os.path.join(proj_dir, proj, kernel, 'kernel_clocks.sdc'))
				
	# Make AOC includes Tcl script
	
	with open(os.path.join(proj_dir, proj, kernel, 'aoc_includes.tcl'), 'w') as handle:
		for type, file in aoc_includes:
			handle.write('set_global_assignment -name ' + type + ' ' + file + '\n')
				
	# Execute kernel pre-instrumentation Tcl script

	subprocess.call('quartus_sh -t ' + os.path.join('lib', 'pre_kernel.tcl') + ' "' + os.path.join(proj_dir, proj, kernel) + '" ' + kernel, shell = True)
	print 'KOC: Pre-instrumentation steps complete'
	
	# Execute kernel instrumentation Python script
	# TODO: regex
	
	subprocess.call('python ' + os.path.join('lib', 'kapow.py') + ' "' + os.path.join(proj_dir, proj, kernel, kernel + '.vqm') + '" "' + os.path.join(proj_dir, proj, kernel, kernel + '_kapow.sv') + '" "' + os.path.join(proj_dir, proj, kernel, kernel + '.asf') + '" "" ' + str(args.kapow_n), shell = True)
	print 'KOC: Instrumentation complete'
				
if kernels['inst']:

	# Execute QSys interface system Tcl script
	# This will break if (1) qsys-script is not called from directory script is in or (2) objects are referenced that are outside either qsys-script or the script's directory structures
	
	shutil.copyfile(os.path.join('lib', 'iface.tcl'), os.path.join(proj_dir, proj, 'iface', 'iface.tcl'))
	os.chdir(os.path.join(proj_dir, proj, 'iface'))
	subprocess.call('qsys-script --script=iface.tcl', shell = True)
	os.chdir(self_dir)
	print 'KOC: Modified interface system'
	
	# Copy controller RTL, component and port declaration and memory initialisation files
	
	for file in ('kapow_ctrl.vhd', 'kapow_scan_counter.sv', 'kapow_ctrl_hw.tcl', 'kapow_ports.tcl', 'kapow_ttl.mif'):
		shutil.copyfile(os.path.join('lib', file), os.path.join(proj_dir, proj, file))

	# Modify kernel QSys component RTL file to add the needed connections to and between kernel modules

	with open(os.path.join(proj_dir, proj, proj + '_system.v'), 'r') as handle:
		lines = handle.readlines()
	
	with open(os.path.join(proj_dir, proj, proj + '_system.v'), 'w') as handle:
		target = (None, None)
		for line in lines:
			if line.startswith('module ' + proj + '_system'):
				target = ('module_system', None)
			else:
				for kernel in kernels['inst']:
					if line.lstrip().startswith(kernel + '_top_wrapper'):
						target = ('inst_wrapper', kernel)
						break
					elif line.startswith('module ' + kernel + '_top_wrapper'):
						target = ('module_kernel', kernel)
						break
					elif line.lstrip().startswith(kernel + '_function_wrapper'):
						target = ('inst_kernel', kernel)
						break
			if target[0] == 'module_system' and line.lstrip().startswith('input logic clock,'):
				for kernel in kernels['inst']:
					handle.write('	input logic ' + kernel + '''_kapow_clk,
	input logic ''' + kernel + '''_kapow_cnten,
	input logic ''' + kernel + '''_kapow_scanin,
	output logic ''' + kernel + '''_kapow_scanout,
''')
				target = (None, None)
			elif target[0] == 'inst_wrapper' and line.lstrip().startswith('.clock(clock),'):
				if target[1] in kernels['inst']:
					handle.write('		.kapow_clk(' + target[1] + '''_kapow_clk),
		.kapow_cnten(''' + target[1] + '''_kapow_cnten),
		.kapow_scanin(''' + target[1] + '''_kapow_scanin),
		.kapow_scanout(''' + target[1] + '''_kapow_scanout),
''')
				target = (None, None)
			elif target[0] == 'module_kernel' and line.lstrip().startswith('input logic clock,'):
				if target[1] in kernels['inst']:
					handle.write('''	input logic kapow_clk,
	input logic kapow_cnten,
	input logic kapow_scanin,
	output logic kapow_scanout,
''')
				target = (None, None)
			elif target[0] == 'inst_kernel' and line.lstrip().startswith('.local_router_hang(lmem_invalid_single_bit),'):
				if target[1] in kernels['inst']:
					handle.write('''		.kapow_clk(kapow_clk),
		.kapow_cnten(kapow_cnten),
		.kapow_scanin(kapow_scanin),
		.kapow_scanout(kapow_scanout),
''')
				target = (None, None)
			handle.write(line)
	print 'KOC: Modified kernel QSys component RTL'

# Modify kernel QSys component Tcl script to instantiate the appropriate file in each /<kernel> directory in place of <proj>.v. If controller(s) are present, also reference kapow_scan_counter.sv
	
with open(os.path.join(proj_dir, proj, proj + '_system_hw.tcl'), 'r') as handle:
	lines = handle.readlines()

kapow_scan_counter_added = False
with open(os.path.join(proj_dir, proj, proj + '_system_hw.tcl'), 'w') as handle:
	for line in lines:
		if line.startswith('add_fileset_file ' + proj + '.v SYSTEM_VERILOG PATH ' + proj + '.v TOP_LEVEL_FILE'):
			for kernel in kernels['all']:
				if kernel in kernels['inst']:
					file = kernel + '_kapow.sv'
					if not kapow_scan_counter_added:
						handle.write('add_fileset_file kapow_scan_counter.sv SYSTEM_VERILOG PATH kapow_scan_counter.sv TOP_LEVEL_FILE\n')
						kapow_scan_counter_added = True
				else:
					file = kernel + '.v'
				handle.write('add_fileset_file ' + file + ' SYSTEM_VERILOG PATH ' + kernel + '/' + file + ' TOP_LEVEL_FILE\n')
		else:
			if line.startswith('add_fileset QUARTUS_SYNTH QUARTUS_SYNTH "" ""'):
				for kernel in kernels['inst']:
					handle.write('set kernel ' + kernel + '''
source kapow_ports.tcl
''')
			handle.write(line)
print 'KOC: Modified kernel QSys component Tcl'

if kernels['inst']:

	# Keep track of used hashes to detect collisions. Controllers use their own hash to identify themselves, so start with that

	hashes = [0x7f323e2e]
	
	# Copy controller QSys Tcl script
	
	shutil.copyfile(os.path.join('lib', 'kapow_ctrl.tcl'), os.path.join(proj_dir, proj, 'kapow_ctrl.tcl'))
	
for kernel in kernels['inst']:
	print 'KOC: Working on kernel "{}"'.format(kernel)

	# ID of kernels is done with MD5 hashes of their names. Bottom 31 bits of hash are taken to suit range of natural generic kernel_hash in kapow_ctrl.vhd
	
	hash = int(hashlib.md5(kernel).hexdigest()[-8:], 16) % 2**31
	if hash in hashes:
		raise RuntimeError('KOC: ERROR: Hash collision for kernel "{}"'.format(kernel))
	hashes.append(hash)
	
	# Execute controller QSys Tcl script
	# This will break if (1) qsys-script is not called from directory script is in or (2) objects are referenced that are outside either qsys-script or the script's directory structures
	
	os.chdir(os.path.join(proj_dir, proj))
	subprocess.call('qsys-script --script=kapow_ctrl.tcl ' + proj + ' ' + kernel + ' ' + ' '.join((str(hash), str(args.kapow_n), str(args.kapow_w))), shell = True)
	os.chdir(self_dir)
	print 'KOC: Instantiated instrumentation controller'
	
# Delete previously generated interface system partition file so it's regenerated

os.remove(os.path.join(proj_dir, proj, 'acl_iface_partition.qxp'))
	
# Remove add_* commands from system.tcl so that QSys isn't told to add components or wires that already exist

with open(os.path.join(proj_dir, proj, 'system.tcl'), 'r') as handle:
	lines = handle.readlines()

with open(os.path.join(proj_dir, proj, 'system.tcl'), 'w') as handle:
	for line in lines:
		if not line.startswith('add_'):
			handle.write(line)
			
# Replace post_flow.tcl with customised version to initialise kapow_ctrl.vhd with TTL, if necessary. This script needs to know W but it can't be passed in as an argument, so set it during copy
			
if kernels['inst']:
			
	with open(os.path.join('lib', 'post_flow.tcl'), 'r') as handle:
		lines = handle.readlines()
	
	with open(os.path.join(proj_dir, proj, 'scripts', 'post_flow.tcl'), 'w') as handle:
		for line in lines:
			handle.write(line.replace('%%KAPOW_W%%', str(args.kapow_w)))
			
# Execute full OpenCL flow
# This will break if aoc is not called from project directory

os.chdir(proj_dir)
subprocess.call('aoc -v ' + os.path.join(proj_dir, proj + '.aoco --board ' + args.board), shell = True)
os.chdir(self_dir)
print 'KOC: Second-stage AOC generation complete'

print 'KOC: Complete'
