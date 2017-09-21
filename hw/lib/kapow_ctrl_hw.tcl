# PRiME KAPow control QSys component
# Controls KAPow instrumentation
# James Davis, 2015

package require -exact qsys 15.0

set_module_property NAME kapow_ctrl

add_interface clk clock sink
add_interface_port clk clk clk Input 1

add_interface rstn reset sink
add_interface_port rstn rstn reset_n Input 1
set_interface_property rstn associatedClock clk

add_interface bus avalon slave
add_interface_port bus bus_address address Input 3
add_interface_port bus bus_read read Input 1
add_interface_port bus bus_readdata readdata Output 32
add_interface_port bus bus_waitrequest waitrequest Output 1
add_interface_port bus bus_write write Input 1
add_interface_port bus bus_writedata writedata Input 32
set_interface_property bus associatedClock clk
set_interface_property bus associatedReset rstn

add_interface kapow_clk clock sink
add_interface_port kapow_clk kapow_clk clk Input 1

add_interface kapow conduit end
add_interface_port kapow kapow_cnten cnten Output 1
add_interface_port kapow kapow_scanin scanin Output 1
add_interface_port kapow kapow_scanout scanout Input 1

add_parameter kernel_hash NATURAL 0 ""
set_parameter_property kernel_hash DEFAULT_VALUE 0
set_parameter_property kernel_hash DISPLAY_NAME kernel_hash
set_parameter_property kernel_hash TYPE NATURAL
set_parameter_property kernel_hash UNITS None
set_parameter_property kernel_hash ALLOWED_RANGES 0:2147483647
set_parameter_property kernel_hash DESCRIPTION "KAPow associated-kernel name hash"
set_parameter_property kernel_hash HDL_PARAMETER true

add_parameter n NATURAL 8 ""
set_parameter_property n DEFAULT_VALUE 8
set_parameter_property n DISPLAY_NAME n
set_parameter_property n TYPE NATURAL
set_parameter_property n UNITS None
set_parameter_property n ALLOWED_RANGES 0:2147483647
set_parameter_property n DESCRIPTION "KAPow number of counters (N)"
set_parameter_property n HDL_PARAMETER true

add_parameter w NATURAL 9 ""
set_parameter_property w DEFAULT_VALUE 9
set_parameter_property w DISPLAY_NAME w
set_parameter_property w TYPE NATURAL
set_parameter_property w UNITS None
set_parameter_property w ALLOWED_RANGES 0:2147483647
set_parameter_property w DESCRIPTION "KAPow counter width (W)"
set_parameter_property w HDL_PARAMETER true

add_fileset QUARTUS_SYNTH QUARTUS_SYNTH "" ""
set_fileset_property QUARTUS_SYNTH TOP_LEVEL kapow_ctrl
set_fileset_property QUARTUS_SYNTH ENABLE_RELATIVE_INCLUDE_PATHS false
set_fileset_property QUARTUS_SYNTH ENABLE_FILE_OVERWRITE_MODE false
add_fileset_file kapow_ctrl.vhd VHDL PATH kapow_ctrl.vhd TOP_LEVEL_FILE

add_fileset SIM_VHDL SIM_VHDL "" ""
set_fileset_property SIM_VHDL TOP_LEVEL kapow_ctrl
set_fileset_property SIM_VHDL ENABLE_RELATIVE_INCLUDE_PATHS false
set_fileset_property SIM_VHDL ENABLE_FILE_OVERWRITE_MODE false
add_fileset_file kapow_ctrl.vhd VHDL PATH kapow_ctrl.vhd TOP_LEVEL_FILE