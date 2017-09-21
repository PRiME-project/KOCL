# PRiME KAPow QSys flow
# Adds and wires up a KAPow control IP block
# James Davis, 2015

package require -exact qsys 15.0

set proj [lindex $::argv 0]
set kernel [lindex $::argv 1]
set kernel_hash [lindex $::argv 2]
set n [lindex $::argv 3]
set w [lindex $::argv 4]

load_system system.qsys

add_instance ${kernel}_kapow_ctrl kapow_ctrl
set_instance_parameter_value ${kernel}_kapow_ctrl kernel_hash $kernel_hash
set_instance_parameter_value ${kernel}_kapow_ctrl n $n
set_instance_parameter_value ${kernel}_kapow_ctrl w $w
add_connection acl_iface.prime_clk ${kernel}_kapow_ctrl.clk
add_connection acl_iface.prime_rstn ${kernel}_kapow_ctrl.rstn
add_connection acl_iface.prime_bus ${kernel}_kapow_ctrl.bus
add_connection acl_iface.kernel_clk ${kernel}_kapow_ctrl.kapow_clk
auto_assign_base_addresses ${kernel}_kapow_ctrl

add_connection acl_iface.kernel_clk ${proj}_system.${kernel}_kapow_clk
add_connection ${kernel}_kapow_ctrl.kapow ${proj}_system.${kernel}_kapow

save_system