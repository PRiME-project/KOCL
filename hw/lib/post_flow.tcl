# PRiME KOCL post-flow script
# Replaces post_flow.tcl in AOC flow to do everything original post_flow.tcl did plus determine and set TTL for KAPow controllers
# James Davis, 2016

load_package flow

# Run PLL adjustment script
source $::env(ALTERAOCLSDKROOT)/ip/board/bsp/adjust_plls.tcl

# START KOCL TTL REQUIREMENTS

# Get kernel frequency from PLL adjustment script-generated file

set handle [open "acl_quartus_report.txt" "r"]
set lines [split [read $handle] "\n"]
close $handle
set line [lsearch -inline $lines "Actual clock freq*"]
set f_kernel [string range $line [expr [string first ":" $line] + 2] [expr [string length $line] - 1]]

# Calculate optimal TTL. Bus frequency is fixed at 50MHz. KAPOW_W gets replaced during copy
set f_bus 50.0
set ttl [expr int(floor(2*(pow(2, %%KAPOW_W%%) - 2)*$f_bus/$f_kernel))]

# Write to MIF
set handle [open "kapow_ttl.mif" "r"]
set lines [split [read $handle] "\n"]
close $handle
set handle [open "kapow_ttl.mif" "w"]
foreach line $lines {
	if {$line == "0: 0;"} {
		set line "0: ${ttl};"
	}
	puts $handle $line
}
close $handle

# Update MIF in database
execute_module -tool cdb -args "-update_mif"

# Generate SOF
execute_module -tool asm

# END KOCL TTL REQUIREMENTS

# Generate RBF from SOF
execute_module -tool cpf -args "-c -o bitstream_compression=on top.sof top.rbf"

# Generate BIN from RBF
set argv [list top.rbf]
source "scripts/create_fpga_bin.tcl"
