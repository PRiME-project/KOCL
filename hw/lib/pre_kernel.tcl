# PRiME pre-KAPow kernel flow
# Performs pre-KAPow run steps for instrumenting arbitrary Verilog for power monitoring
# James Davis, 2015

set dir [lindex $::argv 0]
set kernel [lindex $::argv 1]

load_package flow

cd $dir

project_new $kernel
set_global_assignment -name FAMILY "Cyclone V"
set_global_assignment -name SYSTEMVERILOG_FILE ${kernel}.v
source aoc_includes.tcl
set_global_assignment -name TOP_LEVEL_ENTITY ${kernel}_function_wrapper
set_global_assignment -name SDC_FILE kernel_clocks.sdc
set_global_assignment -name INI_VARS "qatm_force_vqm=on;"
set_instance_assignment -name VIRTUAL_PIN ON -to *

execute_module -tool map

execute_module -tool fit

execute_module -tool cdb -args --vqm=${kernel}.vqm

set_global_assignment -name POWER_OUTPUT_SAF_NAME ${kernel}.asf
set_global_assignment -name POWER_DEFAULT_INPUT_IO_TOGGLE_RATE "12.5 %"
set_global_assignment -name POWER_REPORT_SIGNAL_ACTIVITY ON
set_global_assignment -name POWER_REPORT_POWER_DISSIPATION ON
execute_module -tool pow

project_close